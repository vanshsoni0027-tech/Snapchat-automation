# 👻 Snapchat 100% Automated Spotlight & Public Story Pipeline

Fully automated, 100% free system running on **GitHub Actions**. It scrapes top reels and memes from Instagram accounts (like `bakchod_nation`), formats them into aesthetic 9:16 vertical videos with blurred backgrounds, and posts/schedules them to Snapchat **Spotlight** and **Public Story** (`BC Nation`).

---

## 🌟 How It Works (Zero PC Needed)

1. **Cloud GitHub Actions Engine:**
   - Runs automatically on schedule every Sunday at 05:30 AM IST (`0 0 * * 0`).
   - Can also be triggered anytime with **1-click** from GitHub Actions tab (`workflow_dispatch`).
   - Your PC/laptop can remain turned off 24/7.

2. **Instagram Scraper (`scraper.py`):**
   - Zero-login, TLS Chrome 120 fingerprint impersonation.
   - Bypasses Instagram blocks and datacenter IP filters.
   - Downloads highest quality media with `yt-dlp`.

3. **FFmpeg 9:16 Video Engine (`media_processor.py`):**
   - Transforms any video/photo into a professional 1080x1920 canvas with blurred background.

4. **Snapchat Uploader (`snapchat_uploader.py`):**
   - Posts simultaneously to both **Spotlight** and **Public Story** (`BC Nation`).
   - Auto-selects profile and submits without manual intervention.
   - Keeps track of posted media in `history.json` to prevent duplicates.

---

## 🚀 How to Run Manually on GitHub (1-Click)

1. Open your GitHub Repository: `https://github.com/vanshsoni0027-tech/Snapchat-automation`
2. Go to the **Actions** tab.
3. Select **Snapchat Weekly Batch & Scheduling Automation**.
4. Click **Run workflow** -> **Run workflow**.
5. GitHub will execute everything in the cloud, post/schedule your content, and automatically commit the updated `history.json`.
