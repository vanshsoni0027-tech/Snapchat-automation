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

    # Attach sample image
    page.locator('input[type="file"]').set_input_files("sample.jpg")
    page.wait_for_timeout(5000)

    # Check Spotlight
    print("[*] Checking Post to Spotlight...")
    page.locator('text="Post to Spotlight"').first.click(force=True)
    page.wait_for_timeout(1000)

    # Check Public Story
    print("[*] Checking Post to Public Story...")
    page.locator('text="Post to Public Story"').first.click(force=True)
    page.wait_for_timeout(2000)

    # Click Post button
    post_btn = page.locator('button:has-text("Post")').last
    print("Is Post button enabled?", post_btn.is_enabled())
    if post_btn.is_enabled():
        print("[*] Clicking Post button...")
        post_btn.click()
        page.wait_for_timeout(10000)
        page.screenshot(path="POST_SUBMITTED_LIVE.png")
        print("[+] POST SUBMITTED SUCCESSFULLY TO SNAPCHAT!")

    browser.close()
