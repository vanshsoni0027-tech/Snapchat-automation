import os
import sys
import time
from playwright.sync_api import sync_playwright
from config import SESSION_FILE, PROCESSED_DIR
from snapchat_uploader import schedule_single_snap
from history_manager import mark_as_posted

def main():
    print("=" * 65)
    print(" STEP 1: ONE-TIME SNAPCHAT AUTHENTICATION")
    print("=" * 65)
    print("[*] Opening browser window on your screen...")
    print("[*] Please log in to your Snapchat account in the window.")
    print("=" * 65)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 850}
        )
        page = context.new_page()
        page.goto("https://my.snapchat.com")

        print("[*] Waiting for you to log in in the opened browser window (10 min timeout)...")
        logged_in = False
        for sec in range(600):
            try:
                # Detect creator uploader screen
                if page.locator('input[type="file"]').count() > 0 or page.locator('text="Post to Spotlight"').count() > 0:
                    print("\n[+] LOGIN DETECTED SUCCESSFULLY!")
                    logged_in = True
                    page.wait_for_timeout(3000)
                    break
            except Exception:
                pass
            time.sleep(1)

        if not logged_in:
            print("[-] Login timed out (10 minutes). Please try again.")
            browser.close()
            return

        context.storage_state(path=SESSION_FILE)
        print(f"[+] Fresh session saved to: {SESSION_FILE}")

        print("\n" + "=" * 65)
        print(" STEP 2: POSTING / SCHEDULING READY MEDIA")
        print("=" * 65)

        media_path = os.path.join(PROCESSED_DIR, "Dft1gqDSyjm_story.mp4")
        if not os.path.exists(media_path):
            candidates = [os.path.join(PROCESSED_DIR, f) for f in os.listdir(PROCESSED_DIR) if f.endswith(".mp4")]
            if candidates:
                media_path = candidates[0]
            else:
                print("[-] No processed video found to upload.")
                browser.close()
                return

        print(f"[*] Posting media: {media_path}")
        success = schedule_single_snap(page, media_path)

        if success:
            mark_as_posted("Dft1gqDSyjm", "video", "https://www.instagram.com/reel/Dft1gqDSyjm/", media_path)
            print("\n🎉🎉🎉 SUCCESS! REEL HAS BEEN POSTED TO SNAPCHAT! 🎉🎉🎉")
        else:
            print("\n[-] Upload could not complete. Check screenshot/logs.")

        browser.close()

if __name__ == "__main__":
    main()
