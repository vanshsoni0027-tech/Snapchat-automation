import os
import sys
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

from config import (
    ACCOUNTS_FILE,
    DEFAULT_TARGET_ACCOUNTS,
    SESSION_FILE
)
from scraper import batch_download_unposted
from media_processor import adapt_media_for_snapchat
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

def get_target_count_for_current_run():
    """
    Determines post count based on IST hour:
    - 10:00 AM IST run (~04:30 UTC): 7 posts
    - 04:00 PM IST run (~10:30 UTC): 7 posts
    - 08:00 PM IST run (~14:30 UTC): 6 posts
    Total: 20 posts per day!
    Can also be overridden by CLI arg: python weekly_scheduler.py 7
    """
    if len(sys.argv) > 1:
        try:
            return int(sys.argv[1])
        except ValueError:
            pass

    # Check UTC hour to adjust (04 -> 7, 10 -> 7, 14 -> 6)
    utc_hour = datetime.utcnow().hour
    if 13 <= utc_hour <= 17:
        return 6 # Evening slot (8:00 PM IST)
    return 7 # Morning (10:00 AM IST) or Afternoon (4:00 PM IST)

def run_pipeline():
    """
    Automated Daily Poster:
    1. Loads target Instagram accounts.
    2. Downloads posts (allowing 40% repeat from posts >= 7 days old).
    3. Formats to 9:16 vertical (1080x1920) or clean high-res photo.
    4. Auto-posts to Spotlight and Public Story ('BC Nation').
    5. Saves history and refreshes session state.
    """
    target_count = get_target_count_for_current_run()

    print("\n" + "=" * 70)
    print(" SNAPCHAT AUTOMATED CLOUD POSTER")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Posts This Run: {target_count} (Daily Goal: 20 posts across 3 runs)")
    print("=" * 70)

    if not check_session_exists():
        print("[!] Warning: state.json session file not found or empty.")

    accounts = load_accounts()
    print(f"[*] Active Target Accounts ({len(accounts)}): {', '.join(accounts[:6])}... (+{len(accounts)-6} more)")

    # 1. Gather Media (100% Live Scraping from accounts.json, strict pinned last from divine144empath)
    items = batch_download_unposted(accounts, target_count=target_count)
    if not items:
        print("[-] Error: No media items could be gathered for this run.")
        sys.exit(1)

    # 2. Batch Media Processing
    print(f"\n[*] Formatting {len(items)} media files...")
    processed_queue = []
    for idx, item in enumerate(items, 1):
        try:
            label = "Recycled" if item.get("is_recycled") else "Fresh"
            print(f"[{idx}/{len(items)}] [{label}] Processing {item['id']} ({item['type']})...")
            processed_file = adapt_media_for_snapchat(item["raw_file"], item)
            if processed_file and os.path.exists(processed_file):
                item["processed_file"] = processed_file
                processed_queue.append(item)
            else:
                print(f"[!] Processing failed for {item['id']}")
        except Exception as e:
            print(f"[!] Processing exception for {item['id']}: {e}")

    if not processed_queue:
        print("[-] Error: No media files were successfully processed.")
        sys.exit(1)

    # 3. Post to Snapchat Spotlight & Public Story
    print(f"\n[*] Uploading {len(processed_queue)} posts to Snapchat...")
    success_count = 0

    with sync_playwright() as p:
        browser, context, page = open_uploader_page(p, headless=True)
        try:
            for idx, item in enumerate(processed_queue, 1):
                print(f"\n--- [{idx}/{len(processed_queue)}] Uploading {item['id']} ---")
                try:
                    success = schedule_single_snap(page, item["processed_file"])
                    if success:
                        mark_as_posted(item["id"], item["type"], item["url"], item["processed_file"])
                        success_count += 1
                        print(f"[+] Post {item['id']} successfully published on Snapchat!")
                    else:
                        print(f"[-] Could not publish {item['id']}.")
                except Exception as upload_err:
                    print(f"[!] Upload exception for {item['id']}: {upload_err}")

                # Clean up local temp files
                try:
                    if os.path.exists(item["raw_file"]):
                        os.remove(item["raw_file"])
                    if os.path.exists(item["processed_file"]):
                        os.remove(item["processed_file"])
                except Exception:
                    pass

                time.sleep(5)

            # Auto-save refreshed session state
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
    print(f" RUN COMPLETE: {success_count}/{len(processed_queue)} posts published!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    run_pipeline()
