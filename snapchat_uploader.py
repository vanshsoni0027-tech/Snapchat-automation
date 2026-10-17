import os
import time
from playwright.sync_api import sync_playwright
from config import SESSION_FILE, USER_DATA_DIR

def check_session_exists():
    """Verifies if persistent profile or state.json is present."""
    if os.path.exists(USER_DATA_DIR) and os.listdir(USER_DATA_DIR):
        return True
    if os.path.exists(SESSION_FILE) and os.path.getsize(SESSION_FILE) > 100:
        return True
    print("[!] Error: Neither persistent snapchat_profile nor state.json found.")
    return False

def upload_story_to_snapchat(media_path, headless=True):
    """
    Automated Snapchat uploader for my.snapchat.com.
    Uploads media to Spotlight and Public Profile effortlessly.
    Supports persistent browser profile (VPS) or state.json.
    """
    if not check_session_exists():
        return False

    if not os.path.exists(media_path):
        print(f"[!] Error: Media file does not exist: {media_path}")
        return False

    print(f"[*] Starting Snapchat upload: {media_path}")

    try:
        with sync_playwright() as p:
            browser = None
            if os.path.exists(USER_DATA_DIR) and os.listdir(USER_DATA_DIR):
                print(f"[*] Launching Chromium with persistent profile: {USER_DATA_DIR}")
                context = p.chromium.launch_persistent_context(
                    user_data_dir=USER_DATA_DIR,
                    headless=headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox"
                    ],
                    ignore_default_args=["--enable-automation"],
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 900},
                    locale="en-US"
                )
                page = context.pages[0] if context.pages else context.new_page()
            else:
                browser = p.chromium.launch(
                    headless=headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox"
                    ],
                    ignore_default_args=["--enable-automation"]
                )
                context = browser.new_context(
                    storage_state=SESSION_FILE,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 900},
                    locale="en-US"
                )
                page = context.new_page()

            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            print("[*] Loading Snapchat Creator Portal (my.snapchat.com)...")
            page.goto("https://my.snapchat.com/", wait_until="domcontentloaded", timeout=50000)

            # Wait for file input (handles page spinner up to 35 seconds)
            print("[*] Waiting for creator uploader to load...")
            file_input = page.locator('input[type="file"]')
            file_input.wait_for(state="attached", timeout=35000)

            print("[+] Uploader loaded. Attaching media file...")
            file_input.set_input_files(media_path)

            # Wait for video/photo to render preview
            print("[*] Waiting for media processing...")
            page.wait_for_timeout(6000)

            # Select Destination: Post to Spotlight
            print("[*] Selecting destination: Spotlight...")
            page.locator('text="Post to Spotlight"').first.click(force=True)
            page.wait_for_timeout(1500)

            # Select Destination: Post to Public Story
            print("[*] Selecting destination: Public Story...")
            story_box = page.locator('text="Post to Public Story"')
            if story_box.count() > 0:
                story_box.first.click(force=True)
                page.wait_for_timeout(1500)

                # Select profile 'BC Nation' via keyboard dropdown
                rc_input = page.locator('#rc_select_1')
                if rc_input.count() > 0 and rc_input.is_visible():
                    print("[*] Selecting 'BC Nation' profile...")
                    rc_input.focus()
                    page.wait_for_timeout(500)
                    page.keyboard.press("ArrowDown")
                    page.wait_for_timeout(500)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(1500)

            # Uncheck 'Save to a Public Profile' if required to prevent validation lock
            save_profile = page.locator('text="Save to a Public Profile"')
            if save_profile.count() > 0 and save_profile.is_visible():
                save_profile.first.click(force=True)
                page.wait_for_timeout(1000)

            # Wait for Post button to enable and click it
            post_btn = page.locator('button:has-text("Post")').last
            print("[*] Waiting for Post button to activate...")
            for _ in range(15):
                if post_btn.is_enabled():
                    break
                page.wait_for_timeout(1000)

            if post_btn.is_enabled():
                print("[*] Clicking Post button...")
                post_btn.click()
                page.wait_for_timeout(10000)
                print("[+] STORY/SPOTLIGHT POSTED TO SNAPCHAT SUCCESSFULLY!")
                if browser:
                    browser.close()
                else:
                    context.close()
                return True
            else:
                print("[-] Post button was not enabled.")
                page.screenshot(path="post_disabled.png")
                if browser:
                    browser.close()
                else:
                    context.close()
                return False


    except Exception as e:
        print(f"[!] Upload exception: {e}")
        return False

