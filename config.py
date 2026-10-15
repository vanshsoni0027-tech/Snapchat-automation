import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "downloads")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
SESSION_FILE = os.path.join(BASE_DIR, "state.json")

# Ensure required directories exist
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Instagram Target Configuration
INSTAGRAM_TARGET_USERNAME = "bakchod_nation"
INSTAGRAM_PROFILE_URL = f"https://www.instagram.com/{INSTAGRAM_TARGET_USERNAME}/"

# Automation Strategy Settings
ALLOWED_MEDIA_TYPES = ["video", "photo"]  # Supports both video reels and meme images
MAX_VIDEO_DURATION_SECONDS = 59            # Snapchat story limit is ~60s
TARGET_WIDTH = 1080                        # 9:16 vertical standard
TARGET_HEIGHT = 1920

# Scheduling (4 to 5 times per day -> approx every 4.8 to 5 hours)
CHECK_INTERVAL_HOURS = 5
RANDOM_JITTER_MINUTES = 15                 # Random variation to keep behavior authentic

# User Agent for web requests
CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
