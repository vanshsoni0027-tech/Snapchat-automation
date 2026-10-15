import os
import time
from playwright.sync_api import sync_playwright

SESSION_FILE = "state.json"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        storage_state=SESSION_FILE,
        viewport={"width": 1280, "height": 850}
    )
    page = context.new_page()
    page.goto("https://web.snapchat.com", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(5000)

    print("Current URL:", page.url)
    print("Page Title:", page.title())
    
    # Check for login redirection
    if "login" in page.url or page.locator("input[name='accountIdentifier']").is_visible():
        print("[!] Session is NOT logged in. Redirected to login page!")
    else:
        print("[+] Session is authenticated.")

    # Check for file inputs or upload buttons
    file_inputs = page.locator('input[type="file"]').count()
    print("File inputs count:", file_inputs)

    # List all buttons on page
    buttons = [b.inner_text().strip() for b in page.locator("button").all() if b.inner_text()]
    print("Visible buttons (first 10):", buttons[:10])

    page.screenshot(path="snapchat_diagnostic.png")
    print("Screenshot saved to snapchat_diagnostic.png")
    browser.close()
