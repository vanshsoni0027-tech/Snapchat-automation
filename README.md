# 👻 Snapchat 24/7 Automated Story Poster

Fully automated, 100% free system that scrapes memes and video reels from Instagram (`bakchod_nation`) and uploads them as native 9:16 vertical Snapchat Stories 4–5 times a day.

---

## 🚀 Key Features & Fallback Architecture

- **Instagram Scraper (`scraper.py`):**
  - Uses Playwright to extract fresh reels & meme photos directly from the public grid without needing an Instagram account.
  - Downloads full-resolution video streams via `yt-dlp` (with multiple format fallbacks).
  - Downloads full-resolution memes via `requests` with realistic browser headers.
  - Automatically skips previously posted media via `history.json`.

- **Creative 9:16 Media Engine (`media_processor.py`):**
  - **Videos:** Automatically detects aspect ratio. Non-vertical reels are transformed with an aesthetic blurred-backdrop filter on a 1080x1920 canvas (looks 10x better than plain black bars). Trims duration to <= 59s.
  - **Memes / Photos:** Formats square and portrait memes onto an aesthetic 1080x1920 blurred canvas with the sharp meme centered.

- **Snapchat Story Uploader (`snapchat_uploader.py`):**
  - Uses persistent session authentication (`state.json`), meaning **no password or 2FA prompts during automated runs**.
  - Multi-locator selector fallbacks for file attachment, story selection ("My Story"), and send confirmation.

- **Cloud 24/7 Automation (`.github/workflows/snapchat_automation.yml`):**
  - Runs 5 times every day in GitHub Actions (free tier).
  - Your PC/laptop can remain turned off completely.

---

## 🛠️ One-Time Setup (5 Minutes)

### Step 1: Generate your Snapchat Session
Open your terminal in `D:\snapchat automation` and run:
```bash
python save_session.py
```
1. A browser window will open to `https://web.snapchat.com`.
2. Log in with your Snapchat account.
3. Once logged in and on the main camera/chats screen, return to the terminal and press **ENTER**.
4. This creates `state.json` (your secure login session).

---

### Step 2: Push to Your New GitHub Account (`vanshsoni0027-tech`)

1. Open your browser where `vanshsoni0027-tech` is logged in:
   - Go to [https://github.com/new](https://github.com/new)
   - Create a **Private** repository named `snapchat-automation`
   - Leave "Initialize with README" **unchecked**.

2. In your terminal (`D:\snapchat automation`), run:
   ```bash
   git init
   git config user.name "vanshsoni0027-tech"
   git config user.email "vanshsoni0027@users.noreply.github.com"
   git add .
   git commit -m "Initial commit for Snapchat 24/7 automation"
   git branch -M main
   git remote add origin https://github.com/vanshsoni0027-tech/snapchat-automation.git
   git push -u origin main
   ```

---

### Step 3: Add Session Secret to GitHub

1. In your GitHub repository (`snapchat-automation`), go to:
   - **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.
2. **Name:** `SNAPCHAT_STATE_JSON`
3. **Value:** Open `D:\snapchat automation\state.json`, copy its entire contents, and paste it here.
4. Click **Add secret**.

🎉 **You're all done!** GitHub Actions will now run automatically 5 times every day, download new memes/reels, format them, and post to your Snapchat Story without you touching anything.
