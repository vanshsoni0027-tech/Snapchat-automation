import os
import time
from playwright.sync_api import sync_playwright
from config import SESSION_FILE, CHROME_USER_AGENT

def check_session_exists():
    """Verifies if state.json is present."""
    if not os.path.exists(SESSION_FILE) or os.path.getsize(SESSION_FILE) < 10:
        print("[!] Error: Snapchat session file (state.json) not found!")
        print("[!] Please run 'python save_session.py' first to log in once.")
        return False
    return True

def upload_story_to_snapchat(media_path, headless=True):
    """
    Automates uploading an image or video to Snapchat Story via Snapchat Web.
    Includes multi-layer fallback locators for file input, story target, and submit button.
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
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                storage_state=SESSION_FILE,
                user_agent=CHROME_USER_AGENT,
                viewport={"width": 1280, "height": 900}
            )
            page = context.new_page()

            print("[*] Navigating to Snapchat Web...")
            page.goto("https://web.snapchat.com", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(4000)

            # Check if session is expired or redirect to login occurred
            if "login" in page.url or page.locator("input[name='accountIdentifier']").is_visible():
                print("[!] Error: Snapchat Web session expired. Please re-run 'python save_session.py'.")
                browser.close()
                return False

            print("[+] Authenticated session active.")

            # Step 1: Upload File (Multi-locator fallback)
            uploaded = False
            file_input = page.locator('input[type="file"]')
            
            if file_input.count() > 0:
                print("[*] Found file input locator. Attaching media...")
                file_input.first.set_input_files(media_path)
                uploaded = True
            else:
                # Fallback: Look for upload button or drag-and-drop trigger
                upload_btn = page.locator('button[aria-label*="Upload"], svg[aria-label*="Upload"], div[role="button"]:has-text("Upload")')
                if upload_btn.is_visible(timeout=3000):
                    print("[*] Clicking upload button fallback...")
                    with page.expect_file_chooser() as fc_info:
                        upload_btn.first.click()
                    file_chooser = fc_info.value
                    file_chooser.set_files(media_path)
                    uploaded = True

            if not uploaded:
                print("[-] Could not find file upload target on Snapchat Web.")
                page.screenshot(path="upload_debug.png")
                browser.close()
                return False

            page.wait_for_timeout(4000)

            # Step 2: Target 'My Story' or 'Public Story' (Multi-locator fallback)
            story_selected = False
            story_selectors = [
                'text="My Story"',
                'span:has-text("My Story")',
                'div[role="checkbox"]:has-text("Story")',
                'div[aria-label*="My Story"]',
                'div[aria-label*="Story"]',
                'text="Story"'
            ]

            for sel in story_selectors:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible():
                    print(f"[*] Selecting story target via selector: {sel}")
                    loc.first.click()
                    story_selected = True
                    break

            page.wait_for_timeout(1500)

            # Step 3: Click Send Button (Multi-locator fallback)
            send_selectors = [
                'button:has-text("Send")',
                'button[aria-label*="Send"]',
                'div[role="button"]:has-text("Send")',
                'button:has-text("Post")',
                'svg[aria-label*="Send"]'
            ]

            sent = False
            for sel in send_selectors:
                btn = page.locator(sel)
                if btn.count() > 0 and btn.first.is_visible():
                    print(f"[*] Clicking send button via selector: {sel}")
                    btn.first.click()
                    sent = True
                    break

            if sent:
                print("[*] Waiting for upload completion...")
                page.wait_for_timeout(6000)
                print("[+] Successfully uploaded to Snapchat Story!")
                browser.close()
                return True
            else:
                print("[!] Could not locate Send button. Saving debug screenshot...")
                page.screenshot(path="send_debug.png")
                browser.close()
                return False

    except Exception as e:
        print(f"[!] Exception during Snapchat upload: {e}")
        return False
