from playwright.sync_api import sync_playwright

SESSION_FILE = "state.json"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        storage_state=SESSION_FILE,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 850}
    )
    page = context.new_page()
    print("Navigating to https://my.snapchat.com/...")
    page.goto("https://my.snapchat.com/", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(6000)

    print("Current URL:", page.url)
    print("Page Title:", page.title())
    
    # Check for upload input or elements
    file_inputs = page.locator('input[type="file"]').count()
    print("File inputs count:", file_inputs)

    buttons = [b.inner_text().strip() for b in page.locator("button").all() if b.inner_text()]
    print("Buttons found:", buttons[:10])

    page.screenshot(path="posting_web_test.png")
    print("Screenshot saved to posting_web_test.png")
    browser.close()
