from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = browser.new_page()
    page.goto("https://web.snapchat.com", timeout=25000)
    page.wait_for_timeout(4000)
    print("Page URL:", page.url)
    print("Page Title:", page.title())
    page.screenshot(path="headful_test.png")
    browser.close()
