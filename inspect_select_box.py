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

    # Check Post to Public Story
    page.locator('text="Post to Public Story"').last.click(force=True)
    page.wait_for_timeout(2000)

    # Find the element with text "Select more Public Profiles"
    elem = page.locator('*:has-text("Select more Public Profiles")').last
    print("Tag name:", elem.evaluate("el => el.tagName"))
    print("Outer HTML:", elem.evaluate("el => el.outerHTML.slice(0, 500)"))

    # Also find its parent
    parent = elem.locator('..')
    print("Parent outer HTML:", parent.evaluate("el => el.outerHTML.slice(0, 800)"))

    browser.close()
