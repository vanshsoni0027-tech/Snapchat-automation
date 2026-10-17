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
    page.wait_for_timeout(5000)

    # 1. Check Spotlight
    print("[*] Checking Post to Spotlight...")
    page.locator('text="Post to Spotlight"').first.click(force=True)
    page.wait_for_timeout(1000)

    # 2. Check Public Story
    print("[*] Checking Post to Public Story...")
    page.locator('text="Post to Public Story"').first.click(force=True)
    page.wait_for_timeout(1500)

    # 3. Uncheck Save to a Public Profile
    save_profile = page.locator('text="Save to a Public Profile"')
    if save_profile.count() > 0:
        save_profile.first.click(force=True)
        page.wait_for_timeout(1000)

    # 4. Fill all profile comboboxes
    combos = page.locator('.sds-dropdown-input-selection-search-input').all()
    print("Combobox inputs found:", len(combos))
    for i, c in enumerate(combos):
        print(f"Selecting option on combobox [{i}]...")
        c.focus()
        page.wait_for_timeout(500)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(500)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)

    page.screenshot(path="all_combos_filled.png")

    post_btn = page.locator('button:has-text("Post")').last
    print("Post enabled:", post_btn.is_enabled())
    if post_btn.is_enabled():
        print("[*] Clicking Post button...")
        post_btn.click()
        page.wait_for_timeout(12000)
        page.screenshot(path="SUCCESS_BOTH_POSTED.png")
        print("[+] SUCCESS! POST SUBMITTED TO SPOTLIGHT AND STORY!")

    browser.close()
