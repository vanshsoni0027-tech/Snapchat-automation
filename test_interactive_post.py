import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        storage_state="state.json",
        viewport={"width": 1280, "height": 900}
    )
    page = context.new_page()
    page.goto("https://my.snapchat.com/", wait_until="domcontentloaded", timeout=45000)
    page.locator('input[type="file"]').wait_for(state="attached", timeout=35000)

    # Attach sample image
    page.locator('input[type="file"]').set_input_files("sample.jpg")
    print("Attached sample.jpg. Waiting 5 seconds...")
    page.wait_for_timeout(5000)

    print("Browser is open on your screen!")
    print("Please observe the destination options on screen.")
    page.wait_for_timeout(25000)
    browser.close()
