import os
import re
import time
import requests
import yt_dlp
from playwright.sync_api import sync_playwright
try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

from config import (
    CHROME_USER_AGENT,
    MEDIA_DIR,
    ALLOWED_MEDIA_TYPES
)
from history_manager import is_already_posted

def extract_post_id(url):
    """Extracts unique shortcode identifier from Instagram URL."""
    match = re.search(r'/(?:p|reel)/([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else None

def scrape_account_posts(username, max_posts=15):
    """
    Scrapes recent posts from an Instagram username using TLS impersonation (curl_cffi),
    falling back to Playwright if needed. No login required.
    """
    profile_url = f"https://www.instagram.com/{username}/"
    posts = []

    # 1. Primary Strategy: curl_cffi TLS Chrome impersonator (Zero login, fast)
    if HAS_CURL_CFFI:
        try:
            print(f"[*] Fetching @{username} via TLS impersonation...")
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1"
            }
            r = cffi_requests.get(profile_url, impersonate="chrome120", headers=headers, timeout=20)
            if r.status_code == 200:
                text = r.text
                raw_matches = re.findall(r'/(?:p|reel)/([A-Za-z0-9_-]{8,15})', text)
                seen = set()
                for sc in raw_matches:
                    if sc in seen:
                        continue
                    seen.add(sc)
                    is_reel = f"/reel/{sc}" in text
                    posts.append({
                        "id": sc,
                        "account": username,
                        "type": "video" if is_reel else "photo",
                        "url": f"https://www.instagram.com/reel/{sc}/" if is_reel else f"https://www.instagram.com/p/{sc}/"
                    })
                    if len(posts) >= max_posts:
                        break

                if posts:
                    print(f"[+] Found {len(posts)} posts for @{username} via TLS.")
                    return posts
        except Exception as e:
            print(f"[!] TLS fetch failed for @{username}: {e}")

    # 2. Secondary Strategy: Headless Playwright
    try:
        print(f"[*] Fetching @{username} with Playwright...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(user_agent=CHROME_USER_AGENT, viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.goto(profile_url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(3500)

            anchors = page.locator("article a, main a, div a").all()
            seen_ids = set()
            for a in anchors:
                href = a.get_attribute("href")
                if not href or ("/p/" not in href and "/reel/" not in href):
                    continue

                post_id = extract_post_id(href)
                if not post_id or post_id in seen_ids:
                    continue
                seen_ids.add(post_id)

                is_video = "/reel/" in href
                posts.append({
                    "id": post_id,
                    "account": username,
                    "type": "video" if is_video else "photo",
                    "url": f"https://www.instagram.com{href}" if href.startswith("/") else href
                })
                if len(posts) >= max_posts:
                    break
            browser.close()
    except Exception as e:
        print(f"[!] Playwright scrape failed for @{username}: {e}")

    return posts

def download_media_file(post):
    """Downloads reel or photo to downloads folder using yt-dlp."""
    post_id = post["id"]
    output_template = os.path.join(MEDIA_DIR, f"{post_id}_raw.%(ext)s")

    ydl_opts = {
        'outtmpl': output_template,
        'format': 'bestvideo+bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'overwrites': True,
    }

    try:
        print(f"[*] Downloading {post['type']} ({post_id}) from @{post.get('account', 'unknown')}...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([post["url"]])
    except Exception as e:
        try:
            ydl_opts_fallback = {
                'outtmpl': output_template,
                'format': 'best',
                'quiet': True,
                'no_warnings': True,
                'overwrites': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts_fallback) as ydl:
                ydl.download([post["url"]])
        except Exception as e2:
            print(f"[!] Download failed for {post_id}: {e2}")
            return None

    for ext in ["mp4", "webm", "mkv", "jpg", "png", "webp"]:
        candidate = os.path.join(MEDIA_DIR, f"{post_id}_raw.{ext}")
        if os.path.exists(candidate) and os.path.getsize(candidate) > 1024:
            return candidate

    return None

def batch_download_unposted(accounts, target_count=28):
    """
    Downloads unposted reels across multiple accounts until target_count is reached.
    Cycles through accounts fairly so content is diverse.
    """
    print(f"\n=============================================================")
    print(f"[*] BATCH SCRAPING: Target {target_count} posts across {len(accounts)} accounts")
    print(f"=============================================================")

    # 1. Collect candidates per account
    account_candidates = {}
    for acc in accounts:
        posts = scrape_account_posts(acc, max_posts=20)
        unposted = [p for p in posts if not is_already_posted(p["id"]) and p["type"] in ALLOWED_MEDIA_TYPES]
        # Sort video reels first
        unposted.sort(key=lambda x: 0 if x["type"] == "video" else 1)
        account_candidates[acc] = unposted
        print(f"  - @{acc}: {len(unposted)} unposted candidates available")

    # 2. Interleave candidates across accounts for diversity
    ordered_candidates = []
    has_more = True
    idx = 0
    while has_more:
        has_more = False
        for acc in accounts:
            pool = account_candidates.get(acc, [])
            if idx < len(pool):
                ordered_candidates.append(pool[idx])
                has_more = True
        idx += 1

    print(f"\n[*] Total pooled unposted candidates: {len(ordered_candidates)}")

    # 3. Download until target_count is reached
    downloaded_items = []
    for candidate in ordered_candidates:
        if len(downloaded_items) >= target_count:
            break

        file_path = download_media_file(candidate)
        if file_path and os.path.exists(file_path):
            candidate["raw_file"] = file_path
            downloaded_items.append(candidate)
            print(f"[+] ({len(downloaded_items)}/{target_count}) Successfully downloaded: {candidate['id']}")
        else:
            print(f"[!] Skipped failed candidate: {candidate['id']}")

    print(f"\n[+] Batch Download Complete: {len(downloaded_items)}/{target_count} items ready.")
    return downloaded_items
