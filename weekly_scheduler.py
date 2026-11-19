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
    Guarantees at least 7 posts per run as strictly requested by user.
    Can also be overridden by CLI arg: python weekly_scheduler.py 7
    """
    if len(sys.argv) > 1:
        try:
            return max(7, int(sys.argv[1]))
        except ValueError:
            pass

    return 7

def check_recent_run_guard():
    """
    Prevents duplicate posting if another scheduled trigger already posted in the same window (last 45 mins).
    Can be bypassed if manual CLI arg is provided.
    """
    if len(sys.argv) > 1:
        return True

    if os.path.exists("history.json"):
        try:
            with open("history.json", "r", encoding="utf-8") as f:
                history = json.load(f)
                items = history.get("items", [])
                if items:
                    last_ts = items[-1].get("timestamp", 0)
                    diff = int(time.time()) - last_ts
                    if diff < 2700: # 45 minutes
                        print(f"[i] Slot already posted {diff}s ago (< 45 min). Skipping redundant fire.")
                        sys.exit(0)
        except Exception:
            pass
    return True

def run_pipeline():
    """
    Automated Daily Poster:
    1. Loads target Instagram accounts.
    2. Downloads posts (100% Live Direct Mobile Clips API).
    3. Guarantees 7+ uncropped posts with divine144empath pinned last.
    4. Auto-posts to Spotlight and Public Story ('BC Nation').
    5. Saves history and refreshes session state.
    """
    check_recent_run_guard()
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
