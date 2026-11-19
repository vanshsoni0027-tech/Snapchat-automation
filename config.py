import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "downloads")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
SESSION_FILE = os.path.join(BASE_DIR, "state.json")
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
POOL_FILE = os.path.join(BASE_DIR, "discovered_pool.json")
QUEUE_FILE = os.path.join(BASE_DIR, "schedule_queue.json")
USER_DATA_DIR = os.getenv("USER_DATA_DIR", os.path.join(BASE_DIR, "snapchat_profile"))

# Ensure required directories exist
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Default Target Instagram Accounts (You can add more via accounts.json)
DEFAULT_TARGET_ACCOUNTS = [
    "bakchod_nation"
]

# Media Formatting Standards
ALLOWED_MEDIA_TYPES = ["video", "photo"]
MAX_VIDEO_DURATION_SECONDS = 59
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920

# Weekly Scheduling Settings
POSTS_PER_DAY = 4
DAYS_TO_SCHEDULE = 7
TOTAL_POSTS_PER_WEEK = POSTS_PER_DAY * DAYS_TO_SCHEDULE # 28 posts

# Daily Slot Timings (in 24-hr format: Hours, Minutes)
# e.g., Morning (11:00), Afternoon (15:00), Evening (19:30), Night (22:30)
DAILY_TIME_SLOTS = [
    {"hour": 11, "minute": 0},
    {"hour": 15, "minute": 0},
    {"hour": 19, "minute": 30},
    {"hour": 22, "minute": 30}
]

# Browser Configuration
CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
