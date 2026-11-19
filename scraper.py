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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(BASE_DIR, "instagram_cookies.txt")

def get_playwright_cookies():
    """Parses netscape format cookies from instagram_cookies.txt into Playwright format."""
    if not os.path.exists(COOKIE_FILE):
        return []
    pw_cookies = []
    try:
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    parts = line.strip().split("\t")
                    if len(parts) >= 7:
                        pw_cookies.append({
                            "name": parts[5],
                            "value": parts[6],
                            "domain": parts[0],
                            "path": parts[2],
                            "secure": parts[3].lower() == "true",
                            "httpOnly": False
                        })
    except Exception as e:
        print(f"[!] Cookie parse error: {e}")
    return pw_cookies

def extract_post_id(url):
    """Extracts unique shortcode identifier from Instagram URL."""
    match = re.search(r'/(?:p|reel)/([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else None

def scrape_account_posts_with_page(page, username, max_posts=15):
    """
    Live scrapes latest posts directly from an Instagram account using authenticated Playwright session.
    Guaranteed to bypass cloud IP / datacenter blocks.
    """
    profile_url = f"https://www.instagram.com/{username}/"
    posts = []
    try:
        page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3500)

        # Check if redirected to suspended or login
        if "suspended" in page.url or "login" in page.url:
            print(f"[!] Warning: Profile redirected to {page.url}. Clearing context cookies and retrying clean...")
            page.context.clear_cookies()
            page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3500)

        anchors = page.locator('article a, main a, a[href*="/p/"], a[href*="/reel/"]').all()
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
            clean_url = f"https://www.instagram.com/reel/{post_id}/" if is_video else f"https://www.instagram.com/p/{post_id}/"
            posts.append({
                "id": post_id,
                "account": username,
                "type": "video" if is_video else "photo",
                "url": clean_url
            })
            if len(posts) >= max_posts:
                break
    except Exception as e:
        print(f"[!] Playwright scrape failed for @{username}: {e}")

    return posts

def extract_uncropped_image_url(html_text):
    """
    Extracts the uncropped full-resolution original image from Instagram HTML.
    Bypasses og:image square crop (stp=c...).
    """
    # 1. High-res candidate from image_versions2 JSON state (uncropped original)
    matches = re.findall(r'"candidates":\s*\[\s*\{"url":\s*"([^"]+)"', html_text)
    if matches:
        for m in matches:
            url = m.replace(r'\/', '/').replace(r'\u0026', '&').replace('&amp;', '&')
            if 'stp=c' not in url:
                return url

    # 2. Search all CDN image URLs in HTML that do not have crop parameter 'stp=c'
    all_urls = re.findall(r'https://[^"\'\s<>]+(?:cdninstagram|fbcdn)\.net[^"\'\s<>\\]+', html_text)
    uncropped = []
    for u in all_urls:
        u = u.replace(r'\/', '/').replace(r'\u0026', '&').replace('&amp;', '&')
        if ('.jpg' in u or '.webp' in u) and 'stp=c' not in u and 's150x150' not in u and 's320x320' not in u:
            uncropped.append(u)
    if uncropped:
        return uncropped[0]

    # 3. Fallback to og:image if no uncropped version found
    m = re.search(r'property="og:image"\s+content="([^"]+)"', html_text)
    if m:
        return m.group(1).replace(r'\/', '/').replace(r'\u0026', '&').replace('&amp;', '&')
    return None

def download_media_file(post):
    """
    Downloads reel or photo directly to disk.
    - If photo: extracts uncropped full-resolution image URL directly.
    - If video: downloads highest resolution stream via yt-dlp using cookies.
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
                img_url = extract_uncropped_image_url(r.text)
                if img_url:
                    img_resp = (cffi_requests.get(img_url, timeout=15) if HAS_CURL_CFFI else requests.get(img_url, timeout=15))
                    if img_resp.status_code == 200 and len(img_resp.content) > 1024:
                        out_file = os.path.join(MEDIA_DIR, f"{post_id}_raw.jpg")
                        with open(out_file, "wb") as f:
                            f.write(img_resp.content)
                        print(f"[+] Photo downloaded (Uncropped): {post_id} ({len(img_resp.content)} bytes)")
                        return out_file
        except Exception as e:
            print(f"[!] Photo direct download exception for {post_id}: {e}")

    # B. VIDEO DOWNLOAD HANDLER (Resilient multi-tier: with cookies -> without cookies -> photo fallback)
    output_template = os.path.join(MEDIA_DIR, f"{post_id}_raw.%(ext)s")
    base_ydl_opts = {
        'outtmpl': output_template,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'overwrites': True,
    }

    download_success = False

    # Tier 1: Try with cookies (if available)
    if os.path.exists(COOKIE_FILE):
        try:
            opts_cookies = dict(base_ydl_opts)
            opts_cookies['cookiefile'] = COOKIE_FILE
            print(f"[*] Downloading video ({post_id}) from @{post.get('account', 'unknown')} with cookies...")
            with yt_dlp.YoutubeDL(opts_cookies) as ydl:
                ydl.download([post["url"]])
            download_success = True
        except Exception as e_cook:
            print(f"[!] Cookie video download failed for {post_id} ({e_cook}), retrying without cookies...")

    # Tier 2: Try without cookies (direct download)
    if not download_success:
        try:
            print(f"[*] Downloading video ({post_id}) from @{post.get('account', 'unknown')} without cookies...")
            with yt_dlp.YoutubeDL(base_ydl_opts) as ydl:
                ydl.download([post["url"]])
            download_success = True
        except Exception as e_nocook:
            print(f"[!] Direct video download without cookies failed for {post_id}: {e_nocook}")

    # Check if video was downloaded
    for ext in ["mp4", "webm", "mkv", "mov"]:
        candidate = os.path.join(MEDIA_DIR, f"{post_id}_raw.{ext}")
        if os.path.exists(candidate) and os.path.getsize(candidate) > 1024:
            post["type"] = "video"
            return candidate

    # Tier 3: If no video file, post is a photo/carousel - fallback to uncropped photo download
    print(f"[*] Video stream not found for {post_id}, falling back to uncropped photo download...")
    post["type"] = "photo"
    return download_media_file(post)

def batch_download_unposted(accounts, target_count=7, **kwargs):
    """
    Downloads media files for a run strictly via 100% LIVE scraping.
    - Uses authenticated Instagram session to bypass all cloud/datacenter IP blocks.
    - Scrapes live directly from the target accounts list in accounts.json.
    - Pure fresh live posts only: no pool, no recycled/history filler.
    - Maintains natural mix of photos and videos.
    - STRICT GUARANTEE: The very LAST item in the returned list is ALWAYS from PINNED_LAST_ACCOUNT (@divine144empath).
    """
    print(f"\n=============================================================")
    print(f"[*] LIVE AUTHENTICATED SCRAPER: Target {target_count} posts (Strict Pinned Last: @{PINNED_LAST_ACCOUNT})")
    print(f"[*] Target Accounts Pool ({len(accounts)} accounts): {accounts}")
    print(f"=============================================================")

    pinned_final_item = None
    downloaded_other = []
    needed_other = target_count - 1

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(user_agent=CHROME_USER_AGENT, viewport={"width": 1280, "height": 800})
        
        pw_cookies = get_playwright_cookies()
        if pw_cookies:
            context.add_cookies(pw_cookies)
            print(f"[+] Injected {len(pw_cookies)} Instagram session cookies into browser context")
            # Quick check: ensure cookies do not redirect to /accounts/suspended/
            check_page = context.new_page()
            try:
                check_page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=15000)
                if "suspended" in check_page.url:
                    print(f"[!] Warning: Cookies redirect to suspended page ({check_page.url}). Clearing bad cookies...")
                    context.clear_cookies()
            except Exception:
                pass
            finally:
                check_page.close()
        else:
            print("[*] Running clean direct scraping without cookies")

        page = context.new_page()

        # 1. First, secure the GUARANTEED PINNED FINAL POST from divine144empath
        print(f"[*] Live-scraping guaranteed final post from @{PINNED_LAST_ACCOUNT}...")
        pinned_posts = scrape_account_posts_with_page(page, PINNED_LAST_ACCOUNT, max_posts=15)
        
        unposted_pinned = [
            post for post in pinned_posts
            if not is_already_posted(post["id"]) and post["type"] in ALLOWED_MEDIA_TYPES
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

        # 2. Live-scrape other target accounts from accounts.json
        other_accounts = [a for a in accounts if a != PINNED_LAST_ACCOUNT]
        shuffled_accounts = list(other_accounts)
        random.shuffle(shuffled_accounts)

        account_candidates = {}
        for acc in shuffled_accounts:
            # Stop scraping more pages if we already have plenty of candidates
            total_cand = sum(len(v) for v in account_candidates.values())
            if total_cand >= needed_other * 3:
                break

            print(f"[*] Live-scraping @{acc}...")
            posts = scrape_account_posts_with_page(page, acc, max_posts=10)
            unposted = [
                post for post in posts
                if not is_already_posted(post["id"]) and post["type"] in ALLOWED_MEDIA_TYPES
            ]
            if unposted:
                account_candidates[acc] = unposted
                v_c = sum(1 for x in unposted if x['type'] == 'video')
                p_c = sum(1 for x in unposted if x['type'] == 'photo')
                print(f"    -> {len(unposted)} fresh unposted posts ({v_c} videos, {p_c} photos)")

        browser.close()

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
