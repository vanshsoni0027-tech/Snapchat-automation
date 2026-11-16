import os
import json
import time
from config import HISTORY_FILE

SEVEN_DAYS_SECONDS = 7 * 86400

def load_history():
    """Loads posted history from history.json with corruption recovery fallback."""
    if not os.path.exists(HISTORY_FILE):
        return {"posted_ids": [], "items": []}
    
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"posted_ids": [], "items": []}
            if "posted_ids" not in data:
                data["posted_ids"] = []
            if "items" not in data:
                data["items"] = []
            return data
    except Exception as e:
        print(f"[!] Warning: History file corrupted ({e}). Initializing backup.")
        return {"posted_ids": [], "items": []}

def is_already_posted(post_id, allow_repeat_after_days=7):
    """
    Checks if a post ID was posted recently.
    If posted > allow_repeat_after_days ago, allows it to be re-posted.
    """
    history = load_history()
    now = int(time.time())
    max_age = allow_repeat_after_days * 86400
    
    for item in reversed(history.get("items", [])):
        if item.get("id") == post_id:
            posted_at = item.get("timestamp", 0)
            if (now - posted_at) < max_age:
                return True # Posted within last 7 days -> do not re-post
            else:
                return False # Posted > 7 days ago -> eligible for repeat!
                
    return post_id in history.get("posted_ids", [])

def get_recyclable_items(max_count=3, min_days=7):
    """
    Returns up to max_count items that were posted more than min_days ago,
    ideal for 40% repeat quota.
    """
    history = load_history()
    now = int(time.time())
    threshold = min_days * 86400
    candidates = []

    for item in history.get("items", []):
        ts = item.get("timestamp", 0)
        if (now - ts) >= threshold and item.get("source_url"):
            candidates.append(item)

    # Sort oldest first
    candidates.sort(key=lambda x: x.get("timestamp", 0))
    return candidates[:max_count]

def mark_as_posted(post_id, media_type, source_url, file_path=""):
    """Records a post as successfully posted with current timestamp."""
    history = load_history()
    
    if post_id not in history["posted_ids"]:
        history["posted_ids"].append(post_id)
        
    history["items"].append({
        "id": post_id,
        "type": media_type,
        "source_url": source_url,
        "timestamp": int(time.time()),
        "file_name": os.path.basename(file_path) if file_path else ""
    })
    
    # Keep only the last 2000 items
    if len(history["items"]) > 2000:
        history["items"] = history["items"][-2000:]
        history["posted_ids"] = history["posted_ids"][-2000:]
        
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"[+] Saved to history: {post_id}")
    except Exception as e:
        print(f"[!] Failed to write history file: {e}")
