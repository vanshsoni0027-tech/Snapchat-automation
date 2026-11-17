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
    for _ in range(8):
        current_url = page.url.lower()
        if "accounts.snapchat.com" in current_url or "login" in current_url:
            break
        if page.locator('input[type="file"]').count() > 0:
            return
        page.wait_for_timeout(1000)

    current_url = page.url.lower()
    if "accounts.snapchat.com" in current_url or "login" in current_url:
        print("[*] Login page detected. Performing automated authentication...")
        try:
            user_input = page.locator('input#accountIdentifier, input[name="accountIdentifier"], input[autocomplete="username"]').first
            user_input.wait_for(state="visible", timeout=15000)
            user_input.fill(SNAPCHAT_USERNAME)
            page.wait_for_timeout(500)
            next_btn = page.locator('button:has-text("Next"), button[type="submit"]').first
            if next_btn.is_visible():
                next_btn.click()
                page.wait_for_timeout(3000)

            pw_input = page.locator('input#password, input[name="password"], input[type="password"]').first
            pw_input.wait_for(state="visible", timeout=15000)
            pw_input.fill(SNAPCHAT_PASSWORD)
            page.wait_for_timeout(500)
            sub_btn = page.locator('button:has-text("Log In"), button:has-text("Next"), button[type="submit"]').first
            if sub_btn.is_visible():
                sub_btn.click()
                page.wait_for_timeout(10000)

            if os.path.exists(SESSION_FILE):
                try:
                    context.storage_state(path=SESSION_FILE)
                except Exception:
                    pass
        except Exception as e:
            print(f"[!] Login automation exception: {e}")

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
    Automates uploading a single piece of media on my.snapchat.com.
    - If photo (.jpg, .jpeg, .png): posts ONLY to Public Story ('BC Nation'). Never touches Spotlight.
    - If video (.mp4): posts to BOTH Spotlight and Public Story ('BC Nation').
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

    # Determine media type
    is_photo = media_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))

    # 3. Destination:
    if is_photo:
        print("[*] Media is PHOTO: Selecting ONLY 'Post to Public Story' (leaving Spotlight untouched)...")
        story_box = page.locator('text="Post to Public Story"')
        if story_box.count() > 0 and story_box.first.is_visible():
            story_box.first.click(force=True)
            page.wait_for_timeout(1000)
    else:
        print("[*] Media is VIDEO: Selecting BOTH Spotlight and Public Story...")
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

    # 4. Select BC Nation in ALL visible profile dropdowns
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

    # 5. Fill caption/description if textarea exists (mainly for video)
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
        
        # Check for success confirmation modal
        confirmed = False
        for _ in range(15):
            page.wait_for_timeout(1000)
            success_modal = page.locator('text="Success! Your Snap is now live!", text="Your Snap is now live!"')
            if success_modal.count() > 0 and success_modal.first.is_visible():
                confirmed = True
                print("[+] Verified: 'Success! Your Snap is now live!' modal appeared!")
                break
            error_toast = page.locator('[role="alert"], .sds-toast--negative')
            if error_toast.count() > 0 and error_toast.first.is_visible():
                err_text = error_toast.first.text_content().strip()
                print(f"[!] Upload Error Toast: {err_text}")
                return False

        return True
    else:
        print("[-] Submit button remained disabled.")
        return False
