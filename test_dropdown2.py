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

    # Click ONLY Post to Public Story checkbox
    # Find the checkbox input directly
    checkboxes = page.locator('input[type="checkbox"]').all()
    print(f"Checkboxes found: {len(checkboxes)}")
    if len(checkboxes) >= 2:
        # Checkbox 0 is Spotlight, Checkbox 1 is Post to Public Story
        print("Checking Public Story checkbox...")
        checkboxes[1].check()
        page.wait_for_timeout(2000)

    # Click on 'Select more Public Profiles' placeholder or box
    target_box = page.locator('text="Select more Public Profiles"')
    if target_box.count() > 0:
        print("Clicking 'Select more Public Profiles'...")
        target_box.first.click()
        page.wait_for_timeout(2000)

    page.screenshot(path="dropdown_opened.png")
    
    # Check for options
    options = [o.inner_text().strip() for o in page.locator('li, [role="option"], div[role="listbox"] *').all() if o.inner_text()]
    print("Found options:", options[:10])

    browser.close()
