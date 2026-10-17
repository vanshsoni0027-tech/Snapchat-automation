import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        storage_state="state.json",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900}
    )
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    page = context.new_page()
    print("Navigating to https://my.snapchat.com/...")
    page.goto("https://my.snapchat.com/", wait_until="domcontentloaded", timeout=40000)

    # Wait up to 25 seconds for the spinner to finish
    print("Waiting for page elements to render...")
    for sec in range(1, 26):
        page.wait_for_timeout(1000)
        file_count = page.locator('input[type="file"]').count()
        buttons = [b.inner_text().strip() for b in page.locator("button").all() if b.inner_text()]
        if file_count > 0 or len(buttons) > 1:
            print(f"[+] Loaded at second {sec}! File inputs: {file_count}, Buttons: {buttons}")
            break
        print(f"Sec {sec}: still loading (buttons: {len(buttons)})...")

    page.screenshot(path="portal_rendered.png")
    print("Screenshot saved to portal_rendered.png")
    browser.close()
