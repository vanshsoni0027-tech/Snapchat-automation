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

    # Click selector div
    print("Clicking selector div...")
    page.locator('div.styles-1hk38nh').first.click()
    page.wait_for_timeout(1500)

    # Print all interactive option elements
    items = page.locator('*').filter(has_text="BC Nation").all()
    print("Total elements with text 'BC Nation':", len(items))
    for i, it in enumerate(items):
        tag = it.evaluate("el => el.tagName")
        role = it.get_attribute("role")
        cls = it.get_attribute("class")
        print(f"[{i}] tag={tag}, role={role}, class={cls[:30] if cls else ''}")

    browser.close()
