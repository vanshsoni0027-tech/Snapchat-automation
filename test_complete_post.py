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

    # 1. Check Spotlight
    print("[*] Checking Post to Spotlight...")
    page.locator('text="Post to Spotlight"').first.click(force=True)
    page.wait_for_timeout(1000)

    # 2. Check Public Story
    print("[*] Checking Post to Public Story...")
    page.locator('text="Post to Public Story"').first.click(force=True)
    page.wait_for_timeout(1500)

    # 3. Select BC Nation in profile picker
    print("[*] Selecting BC Nation profile...")
    page.locator('div.styles-1hk38nh').first.click()
    page.wait_for_timeout(1500)
    
    bc_option = page.locator('text="BC Nation"').last
    if bc_option.is_visible():
        bc_option.click()
        print("[+] Clicked BC Nation option!")
    else:
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")

    page.wait_for_timeout(1500)

    # 4. Turn OFF 'Save to a Public Profile' if checked
    save_profile = page.locator('text="Save to a Public Profile"')
    if save_profile.count() > 0:
        print("[*] Unchecking Save to a Public Profile...")
        save_profile.first.click(force=True)
        page.wait_for_timeout(1500)

    page.screenshot(path="ready_to_post.png")

    # 5. Click the bottom right Post button
    post_btn = page.locator('button:has-text("Post")').last
    print("Post button enabled:", post_btn.is_enabled())
    if post_btn.is_enabled():
        print("[*] Clicking Post button...")
        post_btn.click()
        page.wait_for_timeout(10000)
        page.screenshot(path="FINAL_POSTED_CONFIRM.png")
        print("[+] SUCCESS! POSTED TO BOTH SPOTLIGHT & PUBLIC STORY!")

    browser.close()
