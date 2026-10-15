import os
import sys
import time
from playwright.sync_api import sync_playwright
from config import SESSION_FILE, CHROME_USER_AGENT

def main():
    print("=" * 65)
    print(" SNAPCHAT STORY UPLOADER (MY.SNAPCHAT.COM) SESSION SETUP")
    print("=" * 65)
    print("A real browser window will now open to https://my.snapchat.com.")
    print("1. Log in to your Snapchat account.")
    print("2. When you see the Story / Spotlight upload screen, return here and press ENTER.")
    print("=" * 65)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 850}
        )
        page = context.new_page()
        page.goto("https://my.snapchat.com")

        try:
            input("\n>>> PRESS [ENTER] AFTER THE UPLOAD SCREEN APPEARS <<<\n")
        except Exception:
            time.sleep(60)

        context.storage_state(path=SESSION_FILE)
        print(f"\n[+] SUCCESS! Session saved to: {SESSION_FILE}")
        browser.close()

if __name__ == "__main__":
    main()
