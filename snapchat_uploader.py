import os
import time
from playwright.sync_api import sync_playwright
from config import SESSION_FILE

def check_session_exists():
    """Verifies if state.json is present."""
    if not os.path.exists(SESSION_FILE) or os.path.getsize(SESSION_FILE) < 10:
        print("[!] Error: Snapchat session file (state.json) not found!")
        print("[!] Please run 'python save_session.py' first to log in once.")
        return False
    return True

def upload_story_to_snapchat(media_path, headless=True):
    """
    Automates uploading an image or video to Snapchat Story via my.snapchat.com
    (Snapchat's official Web Story & Spotlight Posting Portal).
    """
    if not check_session_exists():
        return False

    if not os.path.exists(media_path):
        print(f"[!] Media file does not exist: {media_path}")
        return False

    print(f"[*] Preparing Snapchat upload for: {media_path}")

    try:
        with sync_playwright() as p:
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
                permissions=["camera", "microphone"],
                locale="en-US"
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            page = context.new_page()

            # Navigate to Snapchat's official Web Story Uploader
            print("[*] Navigating to Snapchat Web Story Portal (my.snapchat.com)...")
            page.goto("https://my.snapchat.com/", wait_until="domcontentloaded", timeout=35000)
            page.wait_for_timeout(6000)

            # Check if redirected to login
            if "login" in page.url or page.locator("input[name='accountIdentifier']").is_visible():
                print("[!] Error: Snapchat session expired or login required.")
                page.screenshot(path="login_required_debug.png")
                browser.close()
                return False

            print(f"[+] Loaded uploader portal: {page.url}")

            # Step 1: Upload file via file input
            file_input = page.locator('input[type="file"]')
            if file_input.count() > 0:
                print("[*] Found file input locator. Attaching media file...")
                file_input.first.set_input_files(media_path)
            else:
                upload_btn = page.locator('button:has-text("Choose"), button:has-text("Upload"), [role="button"]:has-text("Upload")')
                if upload_btn.is_visible(timeout=4000):
                    with page.expect_file_chooser() as fc_info:
                        upload_btn.first.click()
                    file_chooser = fc_info.value
                    file_chooser.set_files(media_path)
                else:
                    print("[!] Upload button/input not found on portal.")
                    page.screenshot(path="no_upload_input_debug.png")
                    browser.close()
                    return False

            print("[*] Waiting for file to process and preview to render...")
            page.wait_for_timeout(5000)

            # Step 2: Target 'My Story'
            story_selectors = [
                'text="My Story"',
                'label:has-text("My Story")',
                'input[type="checkbox"][value*="story" i]',
                'div[role="checkbox"]:has-text("Story")',
                'span:has-text("My Story")',
                'text="Story"'
            ]

            story_checked = False
            for sel in story_selectors:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible():
                    print(f"[*] Selecting Story target via: {sel}")
                    loc.first.click()
                    story_checked = True
                    break

            page.wait_for_timeout(2000)

            # Step 3: Click 'Post' / 'Post to Story'
            post_selectors = [
                'button:has-text("Post")',
                'button:has-text("Post to Story")',
                'button:has-text("Send")',
                'button[type="submit"]',
                'div[role="button"]:has-text("Post")'
            ]

            posted = False
            for sel in post_selectors:
                btn = page.locator(sel)
                if btn.count() > 0 and btn.first.is_visible():
                    print(f"[*] Clicking Post button via: {sel}")
                    btn.first.click()
                    posted = True
                    break

            if posted:
                print("[*] Waiting for post confirmation...")
                page.wait_for_timeout(8000)
                print("[+] SUCCESS: Media successfully posted to Snapchat Story!")
                browser.close()
                return True
            else:
                print("[!] Could not locate Post button. Saving debug screenshot...")
                page.screenshot(path="post_button_debug.png")
                browser.close()
                return False

    except Exception as e:
        print(f"[!] Error during Snapchat Web upload: {e}")
        return False
