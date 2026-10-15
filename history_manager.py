import os
import json
import time
from config import HISTORY_FILE

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
        print(f"[!] Warning: History file corrupted or unreadable ({e}). Initializing backup.")
        return {"posted_ids": [], "items": []}

def is_already_posted(post_id):
    """Checks if a post ID or URL has already been processed."""
    history = load_history()
    return post_id in history.get("posted_ids", [])

def mark_as_posted(post_id, media_type, source_url, file_path=""):
    """Records a post as successfully posted."""
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
    
    # Keep only the last 1000 items to avoid infinite file growth
    if len(history["items"]) > 1000:
        history["items"] = history["items"][-1000:]
        history["posted_ids"] = history["posted_ids"][-1000:]
        
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"[+] Saved to history: {post_id}")
    except Exception as e:
        print(f"[!] Failed to write history file: {e}")
