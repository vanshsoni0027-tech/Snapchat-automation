import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        storage_state="state.json",
        viewport={"width": 1280, "height": 900}
    )
    page = context.new_page()
    page.goto("https://my.snapchat.com/", wait_until="domcontentloaded", timeout=45000)
    page.locator('input[type="file"]').wait_for(state="attached", timeout=35000)
    page.locator('input[type="file"]').set_input_files("sample.jpg")
    page.wait_for_timeout(6000)

    # Click Post to Public Story
    page.locator('text="Post to Public Story"').last.click(force=True)
    page.wait_for_timeout(2000)

    # Print all text content on the right side
    right_col = page.locator('div:has-text("Choose your posting destination")').last
    print("=== HTML of destination section ===")
    print(right_col.inner_html()[:2000])

    browser.close()
