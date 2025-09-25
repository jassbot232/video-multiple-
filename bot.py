import os
import logging
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    InputFile
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes,
    filters
)
from config import BOT_TOKEN, MAX_FILE_SIZE, SUPPORTED_VIDEO_FORMATS, SUPPORTED_AUDIO_FORMATS
from user_manager import user_manager
from video_processor import VideoProcessor
import asyncio
import aiofiles

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Main menu buttons
MAIN_MENU = [
    [
        InlineKeyboardButton("Video Converter", callback_data="convert_menu"),
        InlineKeyboardButton("Video Merge", callback_data="merge_menu")
    ],
    [
        InlineKeyboardButton("Video Rename", callback_data="rename"),
        InlineKeyboardButton("Video and Audio Merge", callback_data="av_merge_menu")
    ],
    [
        InlineKeyboardButton("Video Split", callback_data="split_menu"),
        InlineKeyboardButton("Video to Audio Converter", callback_data="audio_menu")
    ]
]

# Format selection keyboards
VIDEO_FORMATS = [
    [InlineKeyboardButton("MP4", callback_data="format_mp4"),
     InlineKeyboardButton("AVI", callback_data="format_avi")],
    [InlineKeyboardButton("MOV", callback_data="format_mov"),
     InlineKeyboardButton("MKV", callback_data="format_mkv")],
    [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
]

AUDIO_FORMATS = [
    [InlineKeyboardButton("MP3", callback_data="audio_mp3"),
     InlineKeyboardButton("WAV", callback_data="audio_wav")],
    [InlineKeyboardButton("AAC", callback_data="audio_aac"),
     InlineKeyboardButton("M4A", callback_data="audio_m4a")],
    [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and main menu"""
    welcome_text = """
🎬 *Welcome to Video Processing Bot!*

I can help you with various video operations:
• Convert videos between formats
• Merge multiple videos
• Extract audio from videos
• Split videos
• Merge video with audio
• Rename files

Simply send me a video file or document to get started!
    """
    
    keyboard = InlineKeyboardMarkup(MAIN_MENU)
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=keyboard)

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming video files"""
    user_id = update.message.from_user.id
    
    # Download the file
    file = await update.message.video.get_file()
    file_path = f"temp_files/{user_id}_{update.message.video.file_id}.mp4"
    await file.download_to_drive(file_path)
    
    # Store file info in user context
    context.user_data['current_file'] = file_path
    context.user_data['file_type'] = 'video'
    
    # Show main menu
    keyboard = InlineKeyboardMarkup(MAIN_MENU)
    await update.message.reply_text(
        "✅ Video received! What would you like to do with it?",
        reply_markup=keyboard
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document files (videos/audio)"""
    user_id = update.message.from_user.id
    document = update.message.document
    
    # Check if it's a supported format
    file_ext = os.path.splitext(document.file_name)[1].lower()
    
    if file_ext in SUPPORTED_VIDEO_FORMATS:
        file_type = 'video'
    elif file_ext in SUPPORTED_AUDIO_FORMATS:
        file_type = 'audio'
    else:
        await update.message.reply_text("❌ Unsupported file format!")
        return
    
    # Download the file
    file = await document.get_file()
    file_path = f"temp_files/{user_id}_{document.file_id}{file_ext}"
    await file.download_to_drive(file_path)
    
    # Store file info
    context.user_data['current_file'] = file_path
    context.user_data['file_type'] = file_type
    
    keyboard = InlineKeyboardMarkup(MAIN_MENU)
    await update.message.reply_text(
        f"✅ {file_type.capitalize()} file received! What would you like to do?",
        reply_markup=keyboard
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "main_menu":
        keyboard = InlineKeyboardMarkup(MAIN_MENU)
        await query.edit_message_text("Choose an option:", reply_markup=keyboard)
    
    elif data == "convert_menu":
        keyboard = InlineKeyboardMarkup(VIDEO_FORMATS)
        await query.edit_message_text("Select output format:", reply_markup=keyboard)
    
    elif data == "audio_menu":
        keyboard = InlineKeyboardMarkup(AUDIO_FORMATS)
        await query.edit_message_text("Select audio format:", reply_markup=keyboard)
    
    elif data.startswith("format_"):
        format_type = data.replace("format_", "")
        await process_conversion(query, context, format_type)
    
    elif data.startswith("audio_"):
        audio_format = data.replace("audio_", "")
        await process_audio_extraction(query, context, audio_format)
    
    elif data == "merge_menu":
        await start_merge_process(query, context)
    
    elif data == "av_merge_menu":
        await start_av_merge_process(query, context)
    
    elif data == "split_menu":
        await start_split_process(query, context)
    
    elif data == "rename":
        await start_rename_process(query, context)

async def process_conversion(query, context, output_format):
    """Process video conversion"""
    user_id = query.from_user.id
    
    if 'current_file' not in context.user_data:
        await query.edit_message_text("❌ Please send a video file first!")
        return
    
    await query.edit_message_text("🔄 Starting conversion...")
    
    # Progress callback
    async def progress_callback(progress, status):
        try:
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=f"🔄 Converting... {progress}%\n{status}"
            )
        except:
            pass
    
    try:
        output_path = await VideoProcessor.convert_video(
            context.user_data['current_file'],
            output_format,
            progress_callback
        )
        
        # Send the converted file
        with open(output_path, 'rb') as file:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=InputFile(file, filename=f"converted.{output_format}"),
                caption="✅ Conversion completed!"
            )
        
        # Clean up
        os.unlink(output_path)
        
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        await query.edit_message_text("❌ Error during conversion!")

async def process_audio_extraction(query, context, audio_format):
    """Extract audio from video"""
    user_id = query.from_user.id
    
    if 'current_file' not in context.user_data:
        await query.edit_message_text("❌ Please send a video file first!")
        return
    
    await query.edit_message_text("🔄 Extracting audio...")
    
    async def progress_callback(progress, status):
        try:
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=f"🔄 Extracting audio... {progress}%\n{status}"
            )
        except:
            pass
    
    try:
        output_path = await VideoProcessor.video_to_audio(
            context.user_data['current_file'],
            audio_format,
            progress_callback
        )
        
        with open(output_path, 'rb') as file:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=InputFile(file, filename=f"audio.{audio_format}"),
                caption="✅ Audio extraction completed!"
            )
        
        os.unlink(output_path)
        
    except Exception as e:
        logger.error(f"Audio extraction error: {e}")
        await query.edit_message_text("❌ Error during audio extraction!")

async def start_merge_process(query, context):
    """Start video merge process"""
    user_manager.set_user_state(query.from_user.id, "awaiting_merge_files")
    user_manager.clear_queue(query.from_user.id)
    
    # Add current file to queue if exists
    if 'current_file' in context.user_data:
        user_manager.add_to_queue(query.from_user.id, {
            'path': context.user_data['current_file'],
            'type': context.user_data['file_type']
        })
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add More", callback_data="add_more_merge")],
        [InlineKeyboardButton("🚀 Process Merge", callback_data="process_merge")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    queue_count = len(user_manager.get_queue(query.from_user.id))
    await query.edit_message_text(
        f"📁 Merge Process\nFiles in queue: {queue_count}\n\n"
        "Send more video files or click 'Process Merge' when ready.",
        reply_markup=keyboard
    )

async def start_av_merge_process(query, context):
    """Start video-audio merge process"""
    await query.edit_message_text(
        "Please send the audio file you want to merge with the video."
    )
    user_manager.set_user_state(query.from_user.id, "awaiting_audio_merge")

async def start_split_process(query, context):
    """Start video split process"""
    await query.edit_message_text(
        "Please send the start and end times in format: start_seconds end_seconds\n"
        "Example: `10 30` - to split from 10s to 30s"
    )
    user_manager.set_user_state(query.from_user.id, "awaiting_split_times")

async def start_rename_process(query, context):
    """Start rename process"""
    await query.edit_message_text(
        "Please send the new filename with extension:\n"
        "Example: `my_video.mp4`"
    )
    user_manager.set_user_state(query.from_user.id, "awaiting_new_name")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for various states"""
    user_id = update.message.from_user.id
    text = update.message.text
    state = user_manager.get_user_state(user_id)
    
    if state == "awaiting_split_times":
        try:
            start_time, end_time = map(float, text.split())
            await process_video_split(update, context, start_time, end_time)
        except:
            await update.message.reply_text("❌ Invalid format! Use: start_seconds end_seconds")
    
    elif state == "awaiting_new_name":
        await process_rename(update, context, text)
    
    user_manager.set_user_state(user_id, "idle")

async def process_video_split(update, context, start_time, end_time):
    """Process video splitting"""
    message = await update.message.reply_text("🔄 Splitting video...")
    
    async def progress_callback(progress, status):
        try:
            await context.bot.edit_message_text(
                chat_id=message.chat_id,
                message_id=message.message_id,
                text=f"🔄 Splitting... {progress}%\n{status}"
            )
        except:
            pass
    
    try:
        output_path = await VideoProcessor.split_video(
            context.user_data['current_file'],
            start_time,
            end_time,
            progress_callback
        )
        
        with open(output_path, 'rb') as file:
            await context.bot.send_video(
                chat_id=update.message.chat_id,
                video=InputFile(file),
                caption=f"✅ Video split from {start_time}s to {end_time}s!"
            )
        
        os.unlink(output_path)
        await message.delete()
        
    except Exception as e:
        logger.error(f"Split error: {e}")
        await message.edit_text("❌ Error during video split!")

async def process_rename(update, context, new_name):
    """Process file renaming"""
    try:
        output_path = await VideoProcessor.rename_file(
            context.user_data['current_file'],
            new_name
        )
        
        file_type = context.user_data['file_type']
        
        if file_type == 'video':
            with open(output_path, 'rb') as file:
                await context.bot.send_video(
                    chat_id=update.message.chat_id,
                    video=InputFile(file, filename=new_name),
                    caption="✅ File renamed!"
                )
        else:
            with open(output_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=update.message.chat_id,
                    document=InputFile(file, filename=new_name),
                    caption="✅ File renamed!"
                )
        
        os.unlink(output_path)
        
    except Exception as e:
        logger.error(f"Rename error: {e}")
        await update.message.reply_text("❌ Error during renaming!")

def main():
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start bot
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
