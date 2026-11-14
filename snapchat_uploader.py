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
    return False

def open_uploader_page(playwright_instance, headless=True):
    """Launches browser with saved session and navigates to Snapchat portal."""
    if os.path.exists(USER_DATA_DIR) and os.listdir(USER_DATA_DIR):
        context = playwright_instance.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            ignore_default_args=["--enable-automation"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            locale="en-US"
        )
        page = context.pages[0] if context.pages else context.new_page()
        browser = None
    else:
        browser = playwright_instance.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            ignore_default_args=["--enable-automation"]
        )
        context = browser.new_context(
            storage_state=SESSION_FILE,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            locale="en-US"
        )
        page = context.new_page()

    context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
    return browser, context, page

def schedule_single_snap(page, media_path, scheduled_dt=None):
    """
    Automates uploading and scheduling a single piece of media on my.snapchat.com.
    If scheduled_dt is provided, sets the future schedule date & time.
    Otherwise posts immediately.
    """
    print(f"[*] Loading Snapchat Creator Portal (my.snapchat.com)...")
    page.goto("https://my.snapchat.com/", wait_until="domcontentloaded", timeout=50000)

    # 1. Wait for file input and attach file
    file_input = page.locator('input[type="file"]')
    file_input.wait_for(state="attached", timeout=35000)
    print(f"[*] Attaching media file: {os.path.basename(media_path)}")
    file_input.set_input_files(media_path)

    # 2. Wait for media rendering preview
    page.wait_for_timeout(6000)

    # 3. Destination: Spotlight
    spotlight_opt = page.locator('text="Post to Spotlight"')
    if spotlight_opt.count() > 0:
        spotlight_opt.first.click(force=True)
        page.wait_for_timeout(1000)

    # 4. Destination: Public Story
    story_box = page.locator('text="Post to Public Story"')
    if story_box.count() > 0:
        story_box.first.click(force=True)
        page.wait_for_timeout(1000)

        # Select BC Nation profile dropdown
        rc_input = page.locator('#rc_select_1')
        if rc_input.count() > 0 and rc_input.is_visible():
            rc_input.focus()
            page.wait_for_timeout(400)
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(400)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000)

    # 5. Disable 'Save to a Public Profile' if present
    save_profile = page.locator('text="Save to a Public Profile"')
    if save_profile.count() > 0 and save_profile.is_visible():
        save_profile.first.click(force=True)
        page.wait_for_timeout(800)

    # 6. Apply Schedule if scheduled_dt is given
    if scheduled_dt:
        dt_str = scheduled_dt.strftime("%Y-%m-%d %H:%M")
        print(f"[*] Setting post schedule time for: {dt_str}...")

        # Search for Schedule toggle or checkbox
        schedule_btn = page.locator('text="Schedule", button:has-text("Schedule"), input[type="checkbox"]:has-text("Schedule")')
        if schedule_btn.count() > 0:
            schedule_btn.first.click(force=True)
            page.wait_for_timeout(1000)

            # Check for date/time picker inputs
            date_input = page.locator('input[placeholder*="Date"], input[type="date"]').first
            time_input = page.locator('input[placeholder*="Time"], input[type="time"]').first

            if date_input.count() > 0 and date_input.is_visible():
                date_input.fill(scheduled_dt.strftime("%Y-%m-%d"))
            if time_input.count() > 0 and time_input.is_visible():
                time_input.fill(scheduled_dt.strftime("%H:%M"))
        else:
            print("[i] Note: Direct web schedule toggle not found on current screen. Proceeding with standard queue submission.")

    # 7. Wait for Post/Schedule button to become active
    submit_btn = page.locator('button:has-text("Schedule"), button:has-text("Post")').last
    for _ in range(15):
        if submit_btn.is_enabled():
            break
        page.wait_for_timeout(1000)

    if submit_btn.is_enabled():
        btn_label = submit_btn.text_content().strip()
        print(f"[*] Clicking '{btn_label}' button...")
        submit_btn.click()
        page.wait_for_timeout(8000)
        print(f"[+] Successfully queued on Snapchat!")
        return True
    else:
        print("[-] Submit button was disabled. Capturing diagnostic screenshot...")
        page.screenshot(path="submit_disabled.png")
        return False
