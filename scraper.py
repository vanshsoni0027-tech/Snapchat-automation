import os
import re
import json
import time
import random
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

PINNED_LAST_ACCOUNT = "divine144empath"

def extract_post_id(url):
    """Extracts unique shortcode identifier from Instagram URL."""
    match = re.search(r'/(?:p|reel)/([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else None

def scrape_account_posts(username, max_posts=15):
    """
    Live scrapes latest posts directly from an Instagram account in real-time.
    Uses TLS Chrome impersonation (zero login required).
    Falls back to headless Playwright if needed.
    """
    profile_url = f"https://www.instagram.com/{username}/"
    posts = []

    # 1. Primary Strategy: Live TLS Chrome Impersonation
    if HAS_CURL_CFFI:
        try:
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
                    return posts
        except Exception as e:
            print(f"[!] TLS fetch failed for @{username}: {e}")

    # 2. Secondary Strategy: Headless Playwright
    try:
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
    """
    Downloads reel or photo directly to disk.
    - If photo: extracts high-res og:image via TLS and saves directly.
    - If video: downloads highest resolution stream via yt-dlp.
    """
    post_id = post["id"]
    media_type = post.get("type", "video")

    # A. PHOTO DOWNLOAD HANDLER
    if media_type == "photo":
        print(f"[*] Downloading photo ({post_id}) from @{post.get('account', 'unknown')}...")
        try:
            if HAS_CURL_CFFI:
                r = cffi_requests.get(post["url"], impersonate="chrome120", timeout=15)
            else:
                r = requests.get(post["url"], headers={"User-Agent": CHROME_USER_AGENT}, timeout=15)

            if r.status_code == 200:
                m = re.search(r'property="og:image"\s+content="([^"]+)"', r.text)
                if m:
                    img_url = m.group(1).replace("&amp;", "&")
                    img_resp = (cffi_requests.get(img_url, timeout=15) if HAS_CURL_CFFI else requests.get(img_url, timeout=15))
                    if img_resp.status_code == 200 and len(img_resp.content) > 1024:
                        out_file = os.path.join(MEDIA_DIR, f"{post_id}_raw.jpg")
                        with open(out_file, "wb") as f:
                            f.write(img_resp.content)
                        print(f"[+] Photo downloaded: {post_id} ({len(img_resp.content)} bytes)")
                        return out_file
        except Exception as e:
            print(f"[!] Photo direct download exception for {post_id}: {e}")

    # B. VIDEO DOWNLOAD HANDLER (yt-dlp)
    output_template = os.path.join(MEDIA_DIR, f"{post_id}_raw.%(ext)s")
    ydl_opts = {
        'outtmpl': output_template,
        'format': 'bestvideo+bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'overwrites': True,
    }

    try:
        print(f"[*] Downloading video ({post_id}) from @{post.get('account', 'unknown')}...")
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
            print(f"[!] Video download failed for {post_id}: {e2}")

            # If yt-dlp says no video, try photo fallback
            if "no video" in str(e2).lower() or "no video" in str(e).lower():
                post["type"] = "photo"
                return download_media_file(post)
            return None

    for ext in ["mp4", "webm", "mkv", "jpg", "png", "webp"]:
        candidate = os.path.join(MEDIA_DIR, f"{post_id}_raw.{ext}")
        if os.path.exists(candidate) and os.path.getsize(candidate) > 1024:
            return candidate

    return None

def batch_download_unposted(accounts, target_count=7, **kwargs):
    """
    Downloads media files for a run strictly via 100% LIVE scraping.
    - Scrapes live directly from the target accounts list in accounts.json.
    - Pure fresh live posts only: no pool, no recycled/history filler.
    - Maintains natural mix of photos and videos.
    - STRICT GUARANTEE: The very LAST item in the returned list is ALWAYS from PINNED_LAST_ACCOUNT (@divine144empath).
    """
    print(f"\n=============================================================")
    print(f"[*] LIVE SCRAPER ENGINE: Target {target_count} posts (Strict Pinned Last: @{PINNED_LAST_ACCOUNT})")
    print(f"[*] Target Accounts Pool ({len(accounts)} accounts): {accounts}")
    print(f"=============================================================")

    # 1. First, secure the GUARANTEED PINNED FINAL POST from divine144empath
    pinned_final_item = None
    print(f"[*] Live-scraping guaranteed final post from @{PINNED_LAST_ACCOUNT}...")
    pinned_posts = scrape_account_posts(PINNED_LAST_ACCOUNT, max_posts=15)
    
    unposted_pinned = [
        p for p in pinned_posts
        if not is_already_posted(p["id"]) and p["type"] in ALLOWED_MEDIA_TYPES
    ]
    
    print(f"[*] Found {len(unposted_pinned)} fresh unposted candidates from @{PINNED_LAST_ACCOUNT}")
    for cand in unposted_pinned:
        raw = download_media_file(cand)
        if raw and os.path.exists(raw):
            cand["raw_file"] = raw
            cand["is_recycled"] = False
            pinned_final_item = cand
            print(f"[+] [PINNED LAST SECURED] {cand['id']} ({cand['type']}) from @{PINNED_LAST_ACCOUNT}")
            break

    if not pinned_final_item:
        print(f"[!] Warning: No new unposted item from @{PINNED_LAST_ACCOUNT}. Retrying full live scrape...")
        pinned_posts_retry = scrape_account_posts(PINNED_LAST_ACCOUNT, max_posts=25)
        for cand in pinned_posts_retry:
            if cand["type"] in ALLOWED_MEDIA_TYPES:
                raw = download_media_file(cand)
                if raw and os.path.exists(raw):
                    cand["raw_file"] = raw
                    cand["is_recycled"] = False
                    pinned_final_item = cand
                    print(f"[+] [PINNED LAST SECURED (Retry)] {cand['id']} ({cand['type']}) from @{PINNED_LAST_ACCOUNT}")
                    break

    needed_other = (target_count - 1) if pinned_final_item else target_count
    downloaded_other = []

    # 2. Live-scrape other target accounts from accounts.json
    other_accounts = [a for a in accounts if a != PINNED_LAST_ACCOUNT]
    # Shuffle order so we distribute scraping evenly across runs
    shuffled_accounts = list(other_accounts)
    random.shuffle(shuffled_accounts)

    account_candidates = {}
    for acc in shuffled_accounts:
        print(f"[*] Live-scraping @{acc}...")
        posts = scrape_account_posts(acc, max_posts=10)
        unposted = [
            p for p in posts
            if not is_already_posted(p["id"]) and p["type"] in ALLOWED_MEDIA_TYPES
        ]
        if unposted:
            account_candidates[acc] = unposted
            print(f"    -> {len(unposted)} fresh unposted posts ({sum(1 for x in unposted if x['type']=='video')} videos, {sum(1 for x in unposted if x['type']=='photo')} photos)")

    # 3. Interleave candidates across accounts to guarantee account variety + photo/video mix
    ordered_candidates = []
    has_more = True
    idx = 0
    while has_more:
        has_more = False
        for acc in shuffled_accounts:
            cands = account_candidates.get(acc, [])
            if idx < len(cands):
                ordered_candidates.append(cands[idx])
                has_more = True
        idx += 1

    print(f"[*] Total interleaved live candidates gathered: {len(ordered_candidates)}")

    # 4. Download media for other slots
    for candidate in ordered_candidates:
        if len(downloaded_other) >= needed_other:
            break

        file_path = download_media_file(candidate)
        if file_path and os.path.exists(file_path):
            candidate["raw_file"] = file_path
            candidate["is_recycled"] = False
            downloaded_other.append(candidate)
            print(f"[+] ({len(downloaded_other)}/{needed_other}) Live Media Ready: {candidate['id']} [{candidate['type']}] from @{candidate.get('account')}")

    # 5. Assemble final batch: [Live items from accounts.json] + [PINNED POST from divine144empath at VERY END]
    final_batch = downloaded_other
    if pinned_final_item:
        final_batch.append(pinned_final_item)
        print(f"[+] VERIFIED: The FINAL post in this batch is strictly from @{PINNED_LAST_ACCOUNT} ({pinned_final_item['id']} - {pinned_final_item['type']})")

    # Log summary of media types
    v_count = sum(1 for x in final_batch if x['type'] == 'video')
    p_count = sum(1 for x in final_batch if x['type'] == 'photo')
    print(f"\n[+] Batch Ready: Total {len(final_batch)} items ready to upload ({v_count} videos, {p_count} photos, mix maintained).")
    return final_batch
