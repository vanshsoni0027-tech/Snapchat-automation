# 👻 Snapchat 100% Automated Cloud Poster (Spotlight & Public Story)

Fully automated pipeline running on **GitHub Actions** (100% Free, Zero PC needed). It automatically gathers top reels & memes from 16 target Instagram accounts, formats them into aesthetic 9:16 vertical videos with blurred background backdrops, and publishes them to Snapchat **Spotlight** and **Public Story** (`BC Nation`).

---

## ⏰ Daily Automatic Schedule (3 Runs, 20 Posts/Day)

| Run Slot | Time (IST) | Time (UTC) | Posts Count | Content Mix |
| :--- | :--- | :--- | :--- | :--- |
| **Morning Run** | **10:00 AM IST** | 04:30 AM UTC | 7 Posts | 60% Fresh + 40% Recycle (>=7d old) |
| **Afternoon Run** | **04:00 PM IST** | 10:30 AM UTC | 7 Posts | 60% Fresh + 40% Recycle (>=7d old) |
| **Evening Run** | **08:00 PM IST** | 02:30 PM UTC | 6 Posts | 60% Fresh + 40% Recycle (>=7d old) |
| **Total** | | | **20 Posts / Day** | Continuous hands-off publishing |

---

## 🎯 Target Instagram Accounts (16 Sources)
- `@adultfamily`
- `@comedyslam`
- `@darkhumor.raw`
- `@abhishekbandrememes`
- `@scream_for_sinclaire`
- `@just.x_vibes`
- `@__whos._lizy__`
- `@daily.dark.laughs`
- `@melowmark`
- `@whispersoflove100`
- `@lov4usss`
- `@love.and.laugh_world`
- `@couples__love__goals__1`
- `@baefeelings.al`
- `@shezhyk_couple`
- `@bakchod_nation`

---

## 🔄 40% Content Recycle Logic
- Script checks `history.json`.
- Any post older than **7 days** becomes eligible for recycling.
- In each run, up to **40%** is selected from the best 7-day-old posts, and **60%+** is scraped fresh.
- Ensures a steady, endless stream of viral content without ever running dry.

---

## 🚀 Manual 1-Click Trigger
1. Go to your GitHub repository: [Snapchat-automation](https://github.com/vanshsoni0027-tech/Snapchat-automation)
2. Go to the **Actions** tab.
3. Select **Snapchat 3x Daily Automated Poster (Spotlight & Story)**.
4. Click **Run workflow** -> **Run workflow**.
