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
    page.wait_for_timeout(6000)

    # Click Post to Public Story with force=True
    page.locator('text="Post to Public Story"').last.click(force=True)
    page.wait_for_timeout(2000)

    # Uncheck Save to Public Profile with force=True if checked
    save_profile_box = page.locator('text="Save to a Public Profile"')
    if save_profile_box.count() > 0:
        save_profile_box.first.click(force=True)
        page.wait_for_timeout(1000)

    page.screenshot(path="public_story_checked.png")
    
    # Click the red profile selection area
    # Use bounding box click or exact text click
    red_box = page.locator('text="Select 1 to 5 profiles to post to"')
    if red_box.count() > 0:
        box = red_box.first.bounding_box()
        if box:
            # Click slightly above the red text (inside the select box)
            page.mouse.click(box["x"] + 50, box["y"] - 25)
            page.wait_for_timeout(2000)
            page.screenshot(path="dropdown_clicked.png")
            
            # Press arrow down and enter
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
            page.screenshot(path="after_selection.png")

    # Check Post button status
    post_btn = page.locator('button:has-text("Post")').last
    print("Post enabled:", post_btn.is_enabled())
    if post_btn.is_enabled():
        post_btn.click()
        page.wait_for_timeout(8000)
        page.screenshot(path="REAL_POST_SUCCESS.png")
        print("[+] REALLY POSTED TO SNAPCHAT!")

    browser.close()
