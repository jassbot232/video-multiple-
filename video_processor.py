import os
import asyncio
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from pydub import AudioSegment
import ffmpeg
import aiofiles
from config import TEMP_DIR

class VideoProcessor:
    @staticmethod
    async def convert_video(input_path: str, output_format: str, progress_callback=None) -> str:
        """Convert video to different format"""
        output_path = os.path.join(TEMP_DIR, f"converted_{os.path.basename(input_path).split('.')[0]}.{output_format}")
        
        if progress_callback:
            await progress_callback(10, "Starting conversion...")
        
        clip = VideoFileClip(input_path)
        clip.write_videofile(output_path, verbose=False, logger=None)
        clip.close()
        
        if progress_callback:
            await progress_callback(100, "Conversion completed!")
        
        return output_path

    @staticmethod
    async def merge_videos(video_paths: list, progress_callback=None) -> str:
        """Merge multiple videos"""
        output_path = os.path.join(TEMP_DIR, "merged_video.mp4")
        
        if progress_callback:
            await progress_callback(10, "Loading videos...")
        
        clips = []
        for i, path in enumerate(video_paths):
            if progress_callback:
                await progress_callback(10 + (i * 30 // len(video_paths)), f"Loading video {i+1}...")
            clips.append(VideoFileClip(path))
        
        if progress_callback:
            await progress_callback(70, "Merging videos...")
        
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(output_path, verbose=False, logger=None)
        
        for clip in clips:
            clip.close()
        final_clip.close()
        
        if progress_callback:
            await progress_callback(100, "Merge completed!")
        
        return output_path

    @staticmethod
    async def video_to_audio(input_path: str, audio_format: str, progress_callback=None) -> str:
        """Extract audio from video"""
        output_path = os.path.join(TEMP_DIR, f"audio_{os.path.basename(input_path).split('.')[0]}.{audio_format}")
        
        if progress_callback:
            await progress_callback(20, "Extracting audio...")
        
        video = VideoFileClip(input_path)
        audio = video.audio
        
        if progress_callback:
            await progress_callback(60, "Saving audio file...")
        
        audio.write_audiofile(output_path, verbose=False, logger=None)
        video.close()
        audio.close()
        
        if progress_callback:
            await progress_callback(100, "Audio extraction completed!")
        
        return output_path

    @staticmethod
    async def split_video(input_path: str, start_time: float, end_time: float, progress_callback=None) -> str:
        """Split video by time range"""
        output_path = os.path.join(TEMP_DIR, f"split_{os.path.basename(input_path)}")
        
        if progress_callback:
            await progress_callback(20, "Loading video...")
        
        clip = VideoFileClip(input_path)
        
        if progress_callback:
            await progress_callback(50, "Cutting video...")
        
        subclip = clip.subclip(start_time, end_time)
        subclip.write_videofile(output_path, verbose=False, logger=None)
        
        clip.close()
        subclip.close()
        
        if progress_callback:
            await progress_callback(100, "Video split completed!")
        
        return output_path

    @staticmethod
    async def merge_video_audio(video_path: str, audio_path: str, progress_callback=None) -> str:
        """Merge video with external audio"""
        output_path = os.path.join(TEMP_DIR, f"merged_av_{os.path.basename(video_path)}")
        
        if progress_callback:
            await progress_callback(20, "Loading files...")
        
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)
        
        if progress_callback:
            await progress_callback(60, "Merging audio and video...")
        
        final_clip = video_clip.set_audio(audio_clip)
        final_clip.write_videofile(output_path, verbose=False, logger=None)
        
        video_clip.close()
        audio_clip.close()
        final_clip.close()
        
        if progress_callback:
            await progress_callback(100, "Merge completed!")
        
        return output_path

    @staticmethod
    async def rename_file(input_path: str, new_name: str) -> str:
        """Simple file rename"""
        import shutil
        output_path = os.path.join(TEMP_DIR, new_name)
        shutil.copy2(input_path, output_path)
        return output_path
