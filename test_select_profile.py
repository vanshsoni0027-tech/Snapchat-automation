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

    # Click Post to Public Story
    page.locator('text="Post to Public Story"').first.click()
    page.wait_for_timeout(2000)

    # Uncheck Save to your Public Profile if checked
    save_profile = page.locator('text="Save to a Public Profile"')
    if save_profile.count() > 0:
        save_profile.first.click()
        page.wait_for_timeout(1000)

    # Handle 'Select more Public Profiles' input
    inputs = page.locator('div:has-text("Select more Public Profiles") input, div:has-text("Select 1 to 5 profiles to post to") input, input[placeholder*="Public Profile" i]').all()
    print("Found profile inputs:", len(inputs))
    if len(inputs) > 0:
        inputs[0].click()
        page.wait_for_timeout(1000)
        # Select first option in dropdown
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)

    page.screenshot(path="after_profile_select.png")
    
    # Check if Post button is now enabled
    post_btn = page.locator('button:has-text("Post")').last
    is_enabled = post_btn.is_enabled()
    print("Is Post button enabled?", is_enabled)
    
    if is_enabled:
        print("[*] Clicking Post button...")
        post_btn.click()
        page.wait_for_timeout(8000)
        page.screenshot(path="final_post_result.png")
        print("[+] Clicked Post successfully!")

    browser.close()
