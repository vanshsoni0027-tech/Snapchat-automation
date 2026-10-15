from playwright.sync_api import sync_playwright
import os

PROFILE_DIR = os.path.abspath("chrome_profile")
os.makedirs(PROFILE_DIR, exist_ok=True)

with sync_playwright() as p:
    # Launch persistent context
    context = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR,
        channel="chrome",  # Uses the installed real Google Chrome on this machine!
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled"
        ],
        viewport={"width": 1280, "height": 850}
    )
    page = context.new_page()
    page.goto("https://web.snapchat.com", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(4000)
    
    print("Persistent Chrome URL:", page.url)
    print("Page Title:", page.title())
    page.screenshot(path="real_chrome_test.png")
    context.close()
