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
    page.wait_for_timeout(5000)

    # 1. Check Spotlight
    print("Checking Post to Spotlight...")
    page.locator('text="Post to Spotlight"').first.click(force=True)
    page.wait_for_timeout(1000)

    # 2. Check Public Story
    print("Checking Post to Public Story...")
    page.locator('text="Post to Public Story"').first.click(force=True)
    page.wait_for_timeout(1500)

    # 3. Select Profile in 'Select more Public Profiles'
    print("Looking for profile dropdown...")
    profile_inputs = page.locator('input[placeholder*="Public Profile" i], input[type="text"]').all()
    print("Profile inputs count:", len(profile_inputs))
    
    # Try typing BC Nation into any visible text input
    for inp in profile_inputs:
        if inp.is_visible():
            print("Found visible text input. Typing 'BC Nation'...")
            inp.click()
            inp.fill("BC Nation")
            page.wait_for_timeout(1000)
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            break

    # If dropdown box was a div:
    selector_div = page.locator('div:has-text("Select more Public Profiles")').last
    if selector_div.is_visible():
        print("Clicking selector div...")
        selector_div.click()
        page.wait_for_timeout(1000)
        page.keyboard.type("BC Nation")
        page.wait_for_timeout(1000)
        page.keyboard.press("Enter")

    page.wait_for_timeout(2000)
    page.screenshot(path="both_selected.png")

    # Check Post button
    post_btns = page.locator('button:has-text("Post")').all()
    print("Post buttons found:", len(post_btns))
    for i, b in enumerate(post_btns):
        print(f"Button [{i}]: text='{b.inner_text().strip()}', enabled={b.is_enabled()}")
        if b.is_enabled() and b.inner_text().strip() == "Post":
            print("[+] Clicking active Post button!")
            b.click()
            page.wait_for_timeout(8000)
            page.screenshot(path="LIVE_POSTED.png")
            print("[+] Live Post succeeded!")
            break

    browser.close()
