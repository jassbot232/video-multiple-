import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
TEMP_DIR = "temp_files"
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.aac', '.m4a']

# Create temp directory if not exists
os.makedirs(TEMP_DIR, exist_ok=True)
