from playwright.sync_api import sync_playwright

SESSION_FILE = "state.json"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox"
        ],
        ignore_default_args=["--enable-automation"]
    )
    context = browser.new_context(
        storage_state=SESSION_FILE,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 850},
        permissions=["camera", "microphone"],
        locale="en-US"
    )
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    page = context.new_page()
    
    # Listen to navigation
    page.on("framenavigated", lambda frame: print("Navigated to:", frame.url) if frame == page.main_frame else None)

    print("Navigating to https://web.snapchat.com/...")
    page.goto("https://web.snapchat.com/", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(8000)

    print("Final URL:", page.url)
    page.screenshot(path="snapchat_nav_test.png")
    browser.close()
