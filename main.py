import os
import sys
import time
from scraper import fetch_next_unposted_media
from media_processor import adapt_media_for_snapchat
from snapchat_uploader import upload_story_to_snapchat, check_session_exists
from history_manager import mark_as_posted

def cleanup_file(path):
    """Safely removes temporary media files."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

def run_single_cycle():
    """
    Executes one complete automation run:
    Scrape -> Format to 9:16 -> Upload to Snapchat Story -> Record state.
    """
    print("\n" + "=" * 65)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] STARTING SNAPCHAT STORY CYCLE")
    print("=" * 65)

    if not check_session_exists():
        print("[!] Setup Required: state.json is missing.")
        print("[!] Please run 'python save_session.py' to authenticate once.")
        return False

    # 1. Scrape & Download Next Unposted Post (Meme or Reel)
    raw_media_path, post_info = fetch_next_unposted_media()
    if not raw_media_path or not post_info:
        print("[*] No new media to post at this time. Cycle complete.")
        return True

    processed_media_path = None
    try:
        # 2. Format into clean 9:16 Vertical Story
        print(f"[*] Formatting {post_info['type']} for Snapchat...")
        processed_media_path = adapt_media_for_snapchat(raw_media_path, post_info)

        # 3. Upload to Snapchat Story
        print(f"[*] Uploading to Snapchat Story...")
        success = upload_story_to_snapchat(processed_media_path, headless=True)

        if success:
            mark_as_posted(post_info["id"], post_info["type"], post_info["url"], processed_media_path)
            print(f"[+] CYCLE FINISHED SUCCESSFULLY! Posted: {post_info['id']}")
            return True
        else:
            print(f"[-] Upload failed for post: {post_info['id']}.")
            return False

    except Exception as e:
        print(f"[!] Critical error in cycle: {e}")
        return False

    finally:
        # Clean up temporary storage
        cleanup_file(raw_media_path)
        cleanup_file(processed_media_path)

if __name__ == "__main__":
    success = run_single_cycle()
    sys.exit(0 if success else 1)
