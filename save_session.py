import os
import sys
import time
from playwright.sync_api import sync_playwright
from config import SESSION_FILE, CHROME_USER_AGENT

def main():
    print("=" * 60)
    print(" SNAPCHAT WEB 1-TIME AUTHENTICATION SETUP")
    print("=" * 60)
    print("A real browser window will now open to https://web.snapchat.com.")
    print("1. Log in to your Snapchat account.")
    print("2. Approve any 2FA or device prompt.")
    print("3. When you see your chats / camera screen, return here and press ENTER.")
    print("=" * 60)

    with sync_playwright() as p:
        # Launch visible browser for human login
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent=CHROME_USER_AGENT,
            viewport={"width": 1280, "height": 850}
        )
        page = context.new_page()
        page.goto("https://web.snapchat.com")

        try:
            input("\n>>> PRESS [ENTER] AFTER YOU HAVE LOGGED IN TO SNAPCHAT WEB <<<\n")
        except Exception:
            # Fallback timeout if stdin is non-interactive
            print("[*] Waiting 60 seconds for login completion...")
            time.sleep(60)

        # Save cookies, tokens, and storage state
        context.storage_state(path=SESSION_FILE)
        print(f"\n[+] SUCCESS! Session saved to: {SESSION_FILE}")
        print("[+] This session allows 100% automated headless posting without passwords.")
        browser.close()

if __name__ == "__main__":
    main()
