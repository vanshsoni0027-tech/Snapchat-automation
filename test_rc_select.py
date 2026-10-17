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

    # Click Post to Public Story
    page.locator('text="Post to Public Story"').last.click(force=True)
    page.wait_for_timeout(2000)

    # Click the rc_select input
    print("Clicking #rc_select_1...")
    page.locator('#rc_select_1').click(force=True)
    page.wait_for_timeout(1500)

    # Inspect all option elements
    options = page.locator('div[role="option"], .sds-dropdown-input-item-option').all()
    print("Found options count:", len(options))
    for i, opt in enumerate(options):
        print(f"Option [{i}]: '{opt.inner_text().strip()}'")

    if len(options) > 0:
        print("[+] Clicking first option...")
        options[0].click()
        page.wait_for_timeout(2000)
        page.screenshot(path="option_selected_success.png")

    # Check Post button status
    post_btn = page.locator('button:has-text("Post")').last
    print("Is Post button enabled?", post_btn.is_enabled())

    browser.close()
