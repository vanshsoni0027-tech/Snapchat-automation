import os
import json
from datetime import datetime, timedelta
from config import QUEUE_FILE, POSTS_PER_DAY, DAYS_TO_SCHEDULE, DAILY_TIME_SLOTS

def generate_weekly_schedule_slots(start_date=None):
    """
    Generates scheduling datetime objects for the upcoming week.
    Default: Starts from tomorrow so you have full daily coverage.
    """
    if start_date is None:
        start_date = datetime.now() + timedelta(days=1)
        # reset to beginning of day
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    slots = []
    for day_offset in range(DAYS_TO_SCHEDULE):
        current_day = start_date + timedelta(days=day_offset)
        for slot_time in DAILY_TIME_SLOTS:
            slot_dt = current_day.replace(
                hour=slot_time["hour"],
                minute=slot_time["minute"],
                second=0
            )
            slots.append(slot_dt)

    return slots

def save_schedule_queue(items):
    """Saves the scheduled items and their assigned slots to JSON."""
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"[+] Schedule queue saved: {len(items)} items in {QUEUE_FILE}")

def load_schedule_queue():
    """Loads the schedule queue."""
    if not os.path.exists(QUEUE_FILE):
        return []
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
