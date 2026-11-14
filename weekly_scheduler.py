import os
import sys
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

from config import (
    ACCOUNTS_FILE,
    DEFAULT_TARGET_ACCOUNTS,
    TOTAL_POSTS_PER_WEEK,
    SESSION_FILE
)
from scraper import batch_download_unposted
from media_processor import adapt_media_for_snapchat
from schedule_planner import generate_weekly_schedule_slots, save_schedule_queue
from snapchat_uploader import check_session_exists, open_uploader_page, schedule_single_snap
from history_manager import mark_as_posted

def load_accounts():
    """Loads accounts from accounts.json or uses default."""
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                accounts = json.load(f)
                if isinstance(accounts, list) and accounts:
                    return [a.strip().lstrip("@") for a in accounts if a.strip()]
        except Exception:
            pass
    return DEFAULT_TARGET_ACCOUNTS

def run_weekly_pipeline():
    """
    Main Weekly Orchestrator:
    1. Loads target accounts list.
    2. Batch-downloads 28 unposted reels/memes.
    3. Formats all 28 into 9:16 vertical videos with blurred backdrop.
    4. Generates scheduled slots for the next 7 days (4 posts/day).
    5. Automates scheduling them into Snapchat Creator Portal.
    """
    print("\n" + "=" * 70)
    print("🚀 SNAPCHAT 7-DAY BATCH & SCHEDULING PIPELINE")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if not check_session_exists():
        print("[!] Snapchat session missing. Please run START_LOGIN.bat once to save session.")
        return False

    accounts = load_accounts()
    print(f"[*] Target Accounts ({len(accounts)}): {', '.join(accounts)}")
    print(f"[*] Target Schedule: {TOTAL_POSTS_PER_WEEK} posts across 7 days")

    # 1. Batch Scraping & Downloading
    items = batch_download_unposted(accounts, target_count=TOTAL_POSTS_PER_WEEK)
    if not items:
        print("[-] No new unposted media could be downloaded. Exiting.")
        return False

    # 2. Batch Media Processing (9:16 Vertical)
    print(f"\n[*] Formatting {len(items)} media files into 9:16 vertical format...")
    processed_queue = []
    for idx, item in enumerate(items, 1):
        try:
            print(f"[{idx}/{len(items)}] Processing {item['id']} ({item['type']})...")
            processed_file = adapt_media_for_snapchat(item["raw_file"], item)
            if processed_file and os.path.exists(processed_file):
                item["processed_file"] = processed_file
                processed_queue.append(item)
            else:
                print(f"[!] Failed to process {item['id']}")
        except Exception as e:
            print(f"[!] Processing exception for {item['id']}: {e}")

    if not processed_queue:
        print("[-] No media files were successfully processed.")
        return False

    # 3. Generate Weekly Schedule Slots
    slots = generate_weekly_schedule_slots()
    print(f"\n[*] Generated {len(slots)} schedule slots for the upcoming week:")
    for i, s in enumerate(slots[:4]):
        print(f"   Slot {i+1}: {s.strftime('%A, %d %b %Y @ %I:%M %p')}")
    print("   ...")

    for i, item in enumerate(processed_queue):
        if i < len(slots):
            item["scheduled_for"] = slots[i].strftime("%Y-%m-%d %H:%M")
            item["slot_datetime"] = slots[i]
        else:
            item["scheduled_for"] = None

    save_schedule_queue(processed_queue)

    # 4. Upload & Schedule on Snapchat
    print(f"\n[*] Starting Snapchat Automated Scheduling ({len(processed_queue)} posts)...")
    success_count = 0

    with sync_playwright() as p:
        browser, context, page = open_uploader_page(p, headless=True)
        try:
            for idx, item in enumerate(processed_queue, 1):
                slot_info = item.get("scheduled_for", "Immediate")
                print(f"\n--- [{idx}/{len(processed_queue)}] Scheduling {item['id']} for {slot_info} ---")

                success = schedule_single_snap(page, item["processed_file"], item.get("slot_datetime"))
                if success:
                    mark_as_posted(item["id"], item["type"], item["url"], item["processed_file"])
                    success_count += 1
                    print(f"[+] Post {item['id']} successfully queued on Snapchat!")
                else:
                    print(f"[-] Could not queue {item['id']}.")

                # Clean up local files after scheduling
                try:
                    if os.path.exists(item["raw_file"]):
                        os.remove(item["raw_file"])
                    if os.path.exists(item["processed_file"]):
                        os.remove(item["processed_file"])
                except Exception:
                    pass

                time.sleep(4)

            # Auto-refresh session state after batch
            try:
                context.storage_state(path=SESSION_FILE)
                print(f"[+] Session refreshed and saved to {SESSION_FILE}")
            except Exception:
                pass

        finally:
            if browser:
                browser.close()
            else:
                context.close()

    print("\n" + "=" * 70)
    print(f"🎉 WEEKLY BATCH RUN COMPLETE: {success_count}/{len(processed_queue)} posts scheduled!")
    print("Snapchat will now automatically publish them throughout the week!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    run_weekly_pipeline()
