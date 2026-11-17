import os
import sys
import time
from playwright.sync_api import sync_playwright
from config import SESSION_FILE, USER_DATA_DIR

SNAPCHAT_USERNAME = os.environ.get("SNAPCHAT_USERNAME", "bakchod_nationn")
SNAPCHAT_PASSWORD = os.environ.get("SNAPCHAT_PASSWORD", "8003402780")

def check_session_exists():
    """Verifies if state.json or persistent profile is present."""
    if os.path.exists(SESSION_FILE) and os.path.getsize(SESSION_FILE) > 100:
        return True
    if os.path.exists(USER_DATA_DIR) and os.listdir(USER_DATA_DIR):
        return True
    return False

def ensure_logged_in(page, context):
    """Checks if logged in; if at login screen, logs in automatically."""
    current_url = page.url.lower()
    if "accounts.snapchat.com" in current_url or "login" in current_url:
        print("[*] Login page detected. Performing automated authentication...")
        user_input = page.locator('input#accountIdentifier, input[name="accountIdentifier"], input[autocomplete="username"]').first
        if user_input.is_visible():
            user_input.fill(SNAPCHAT_USERNAME)
            next_btn = page.locator('button:has-text("Next"), button[type="submit"]').first
            if next_btn.is_visible():
                next_btn.click()
                page.wait_for_timeout(3000)

        pw_input = page.locator('input#password, input[name="password"], input[type="password"]').first
        if pw_input.is_visible():
            pw_input.fill(SNAPCHAT_PASSWORD)
            sub_btn = page.locator('button:has-text("Log In"), button:has-text("Next"), button[type="submit"]').first
            if sub_btn.is_visible():
                sub_btn.click()
                page.wait_for_timeout(8000)

        if os.path.exists(SESSION_FILE):
            try:
                context.storage_state(path=SESSION_FILE)
            except Exception:
                pass

def open_uploader_page(playwright_instance, headless=True):
    """Launches browser with saved session."""
    browser = playwright_instance.chromium.launch(
        headless=headless,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        ignore_default_args=["--enable-automation"]
    )
    context = browser.new_context(
        storage_state=SESSION_FILE if os.path.exists(SESSION_FILE) else None,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900},
        locale="en-US"
    )
    context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
    page = context.new_page()
    return browser, context, page

def schedule_single_snap(page, media_path, scheduled_dt=None, caption="🔥 #reels #viral #spotlight"):
    """
    Automates uploading and scheduling a single piece of media on my.snapchat.com.
    Posts to both Spotlight and Public Story ('BC Nation').
    """
    print(f"[*] Navigating to Creator Portal (my.snapchat.com)...")
    page.goto("https://my.snapchat.com/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)

    # Check for login redirection
    ensure_logged_in(page, page.context)

    # 1. Wait for file input and attach file
    file_input = page.locator('input[type="file"]')
    file_input.wait_for(state="attached", timeout=35000)
    print(f"[*] Attaching media: {os.path.basename(media_path)}")
    file_input.set_input_files(media_path)

    # 2. Wait for media rendering preview
    page.wait_for_timeout(6000)

    # 3. Destination: Check Spotlight and Public Story
    spotlight_opt = page.locator('text="Post to Spotlight"')
    if spotlight_opt.count() > 0 and spotlight_opt.first.is_visible():
        print("[*] Selecting Spotlight destination...")
        spotlight_opt.first.click(force=True)
        page.wait_for_timeout(1000)

    story_box = page.locator('text="Post to Public Story"')
    if story_box.count() > 0 and story_box.first.is_visible():
        print("[*] Selecting Public Story destination...")
        story_box.first.click(force=True)
        page.wait_for_timeout(1000)

    # 4. Select BC Nation in ALL visible dropdowns (whether 1 for photo or 2 for video)
    inputs = page.locator('.sds-dropdown-input-selection-search-input').all()
    for idx, inp in enumerate(inputs):
        if inp.is_visible():
            print(f"[*] Selecting BC Nation in profile input {idx + 1}...")
            inp.click(force=True)
            page.wait_for_timeout(400)
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(300)
            page.keyboard.press("Enter")
            page.wait_for_timeout(800)

    # 5. Fill caption/description if textarea exists
    try:
        desc = page.locator('textarea').first
        if desc.is_visible():
            desc.fill(caption)
            page.wait_for_timeout(400)
    except Exception:
        pass

    # 6. Disable 'Save to a Public Profile' if present
    save_profile = page.locator('text="Save to a Public Profile"')
    if save_profile.count() > 0 and save_profile.is_visible():
        save_profile.first.click(force=True)
        page.wait_for_timeout(600)

    # 7. Apply Schedule if scheduled_dt is provided
    if scheduled_dt:
        dt_str = scheduled_dt.strftime("%Y-%m-%d %H:%M")
        print(f"[*] Applying schedule time: {dt_str}...")
        schedule_btn = page.locator('button:has-text("Schedule for later"), text="Schedule for later", button:has-text("Schedule")')
        if schedule_btn.count() > 0 and schedule_btn.first.is_visible():
            schedule_btn.first.click(force=True)
            page.wait_for_timeout(1000)

    # 8. Wait for Post / Schedule button to become enabled
    submit_btn = page.locator('button:has-text("Schedule"), button:has-text("Post")').last
    for _ in range(15):
        if submit_btn.is_enabled():
            break
        page.wait_for_timeout(1000)

    if submit_btn.is_enabled():
        btn_label = submit_btn.text_content().strip()
        print(f"[*] Submitting via '{btn_label}' button...")
        submit_btn.click()
        page.wait_for_timeout(12000)
        print("[+] Snap successfully submitted and confirmed!")
        return True
    else:
        print("[-] Submit button remained disabled.")
        return False
