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

    # Attach dummy file or sample
    sample = "processed/DGOQJk9SKL4_story.jpg"
    page.locator('input[type="file"]').set_input_files(sample)
    page.wait_for_timeout(6000)

    # Check Post to Public Story
    page.locator('text="Post to Public Story"').first.click()
    page.wait_for_timeout(2000)

    # Click on 'Select more Public Profiles' input
    profile_inputs = page.locator('input[placeholder*="profile" i], [aria-label*="profile" i], input').all()
    print("Found inputs:", len(profile_inputs))
    
    # Click the first profile selection field
    dropdown_field = page.locator('div:has-text("Select 1 to 5 profiles to post to")').locator('..').locator('input')
    if dropdown_field.count() > 0:
        dropdown_field.first.click()
        page.wait_for_timeout(2000)
        
        # Print options in dropdown
        options = [o.inner_text().strip() for o in page.locator('div[role="option"], li, div[role="listbox"] div').all() if o.inner_text()]
        print("Dropdown options:", options[:10])

    page.screenshot(path="dropdown_options.png")
    browser.close()
