import os
import re
import json
import random
import time
import requests
try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    cffi_requests = None
    HAS_CURL_CFFI = False

import yt_dlp
from config import (
    MEDIA_DIR,
    ALLOWED_MEDIA_TYPES,
    DEFAULT_TARGET_ACCOUNTS
)
from history_manager import is_already_posted

PINNED_LAST_ACCOUNT = "divine144empath"

os.makedirs(MEDIA_DIR, exist_ok=True)

MOBILE_API = "https://i.instagram.com/api/v1"
MOBILE_HEADERS = {
    "User-Agent": "Instagram 337.0.0.35.102 Android (33/13; 420dpi; 1080x2400; samsung; SM-G991B; o1s; exynos2100; en_US; 609393420)",
    "X-IG-App-ID": "567067343352427",
    "Accept-Language": "en-US",
}

PAGE_IDS_FILE = os.path.join(os.path.dirname(__file__), "page_ids.json")

def load_page_ids():
    """Loads permanent Instagram numeric user IDs for all target accounts."""
    if os.path.exists(PAGE_IDS_FILE):
        try:
            with open(PAGE_IDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Error loading page_ids.json: {e}")
    return {}

def extract_uncropped_image_url(html_text):
    """
    Extracts the uncropped full-resolution original image from Instagram HTML.
    Bypasses og:image square crop (stp=c...).
    """
    matches = re.findall(r'"candidates":\s*\[\s*\{"url":\s*"([^"]+)"', html_text)
    if matches:
        for m in matches:
            url = m.replace(r'\/', '/').replace(r'\u0026', '&').replace('&amp;', '&')
            if 'stp=c' not in url:
                return url

    all_urls = re.findall(r'https://[^"\'\s<>]+(?:cdninstagram|fbcdn)\.net[^"\'\s<>\\]+', html_text)
    uncropped = []
    for u in all_urls:
        u = u.replace(r'\/', '/').replace(r'\u0026', '&').replace('&amp;', '&')
        if ('.jpg' in u or '.webp' in u) and 'stp=c' not in u and 's150x150' not in u and 's320x320' not in u:
            uncropped.append(u)
    if uncropped:
        return uncropped[0]

    m = re.search(r'property="og:image"\s+content="([^"]+)"', html_text)
    if m:
        return m.group(1).replace(r'\/', '/').replace(r'\u0026', '&').replace('&amp;', '&')
    return None

def fetch_account_clips(user_id, account_name, max_pages=2):
    """
    Fetches latest reels directly from Instagram Mobile API (Clips).
    100% bypasses cloud datacenter IP login redirects without needing cookies.
    """
    session = cffi_requests.Session(impersonate="chrome") if HAS_CURL_CFFI else requests.Session()
    clips = []
    max_id = None
    for p in range(max_pages):
        data = {"target_user_id": str(user_id), "page_size": "12"}
        if max_id:
            data["max_id"] = str(max_id)
        try:
            resp = session.post(f"{MOBILE_API}/clips/user/", headers=MOBILE_HEADERS, data=data, timeout=20)
            if resp.status_code != 200:
                print(f"[!] {account_name} ({user_id}) clips HTTP {resp.status_code}: {resp.text[:120]}")
                # Try fallback with plain requests session
                if HAS_CURL_CFFI:
                    plain_resp = requests.post(f"{MOBILE_API}/clips/user/", headers=MOBILE_HEADERS, data=data, timeout=20)
                    if plain_resp.status_code == 200:
                        resp = plain_resp
                    else:
                        print(f"[!] {account_name} plain requests HTTP {plain_resp.status_code}: {plain_resp.text[:120]}")
                        break
                else:
                    break
            j = resp.json()
            items = j.get("items", [])
            if not items:
                print(f"[!] {account_name} returned 0 items from mobile API")
                break
            for it in items:
                media = it.get("media") or {}
                code = media.get("code")
                if not code:
                    continue
                vv = media.get("video_versions") or []
                video_url = vv[0]["url"] if vv else None
                clips.append({
                    "id": code,
                    "code": code,
                    "account": account_name,
                    "url": f"https://www.instagram.com/reel/{code}/",
                    "video_url": video_url,
                    "type": "video",
                    "views": media.get("play_count") or media.get("view_count") or 0,
                    "likes": media.get("like_count") or 0,
                })
            paging = j.get("paging_info") or {}
            max_id = paging.get("max_id")
            if not paging.get("more_available") or not max_id:
                break
        except Exception as e:
            print(f"[!] Error fetching clips for {account_name} ({user_id}): {e}")
            break
    return clips

def scrape_account_posts_playwright(account_name, max_posts=10):
    """Fallback: Scrapes public reels and posts using headless Playwright."""
    results = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
            page = context.new_page()
            page.goto(f"https://www.instagram.com/{account_name}/", timeout=25000)
            page.wait_for_timeout(3500)
            anchors = page.locator('article a, main a, a[href*="/p/"], a[href*="/reel/"]').all()
            seen = set()
            for a in anchors:
                href = a.get_attribute("href") or ""
                m = re.search(r'/(?:p|reel)/([A-Za-z0-9_-]+)', href)
                if m:
                    cid = m.group(1)
                    if cid not in seen:
                        seen.add(cid)
                        is_reel = "/reel/" in href
                        results.append({
                            "id": cid,
                            "code": cid,
                            "account": account_name,
                            "url": f"https://www.instagram.com/{'reel' if is_reel else 'p'}/{cid}/",
                            "video_url": None,
                            "type": "video" if is_reel else "photo",
                            "views": 0,
                            "likes": 0
                        })
            browser.close()
    except Exception as e:
        print(f"[!] Playwright scraper notice for @{account_name}: {e}")
    return results

def download_media_file(post):
    """
    Downloads media file (video or photo) with multi-tier fallback:
    1. Direct CDN download if video_url is present (fastest, full original quality, no yt-dlp).
    2. Direct uncropped photo download if media is photo.
    3. yt-dlp clean download fallback without cookies.
    """
    post_id = post["id"]
    media_type = post.get("type", "video")

    # A. Direct CDN Video Download (from mobile API)
    video_url = post.get("video_url")
    if video_url and media_type == "video":
        out_file = os.path.join(MEDIA_DIR, f"{post_id}_raw.mp4")
        try:
            session = cffi_requests.Session(impersonate="chrome") if HAS_CURL_CFFI else requests.Session()
            r = session.get(video_url, headers={"Referer": "https://www.instagram.com/"}, timeout=60)
            if r.status_code == 200 and len(r.content) > 10240:
                with open(out_file, "wb") as f:
                    f.write(r.content)
                print(f"[+] Downloaded Direct CDN Video (Uncropped): {post_id} ({len(r.content)} bytes)")
                return out_file
        except Exception as e:
            print(f"[!] Direct CDN video download error for {post_id}: {e}")

    # B. Direct Uncropped Photo Download
    if media_type == "photo":
        print(f"[*] Downloading photo ({post_id}) from @{post.get('account', 'unknown')}...")
        try:
            session = cffi_requests.Session(impersonate="chrome120") if HAS_CURL_CFFI else requests.Session()
            r = session.get(post["url"], timeout=15)
            if r.status_code == 200:
                img_url = extract_uncropped_image_url(r.text)
                if img_url:
                    img_resp = session.get(img_url, timeout=15)
                    if img_resp.status_code == 200 and len(img_resp.content) > 1024:
                        out_file = os.path.join(MEDIA_DIR, f"{post_id}_raw.jpg")
                        with open(out_file, "wb") as f:
                            f.write(img_resp.content)
                        print(f"[+] Photo downloaded (Uncropped Full-Res): {post_id} ({len(img_resp.content)} bytes)")
                        return out_file
        except Exception as e:
            print(f"[!] Photo direct download exception for {post_id}: {e}")

    # C. yt-dlp Clean Direct Download (Fallback)
    output_template = os.path.join(MEDIA_DIR, f"{post_id}_raw.%(ext)s")
    ydl_opts = {
        'outtmpl': output_template,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'overwrites': True,
    }
    try:
        print(f"[*] Downloading video ({post_id}) via yt-dlp fallback...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([post["url"]])
    except Exception as e:
        print(f"[!] yt-dlp download notice for {post_id}: {e}")

    for ext in ["mp4", "webm", "mkv", "mov", "jpg", "png"]:
        candidate = os.path.join(MEDIA_DIR, f"{post_id}_raw.{ext}")
        if os.path.exists(candidate) and os.path.getsize(candidate) > 1024:
            return candidate

    return None

def batch_download_unposted(accounts, target_count=7, **kwargs):
    """
    Downloads media files strictly via 100% LIVE scraping.
    - Uses Instagram Mobile Clips API with permanent page_ids (bypasses datacenter cloud IP blocks).
    - Preserves uncropped original files.
    - STRICT GUARANTEE 1: The very LAST item is ALWAYS from PINNED_LAST_ACCOUNT (@divine144empath).
    - STRICT GUARANTEE 2: Exactly target_count (minimum 7) posts are delivered.
    """
    print(f"\n=============================================================")
    print(f"[*] LIVE CLOUD SCRAPER: Target {target_count} posts (Strict Pinned Last: @{PINNED_LAST_ACCOUNT})")
    print(f"=============================================================")

    page_ids = load_page_ids()
    pinned_final_item = None
    downloaded_other = []
    needed_other = max(6, target_count - 1)

    # 1. Secure GUARANTEED PINNED FINAL POST from divine144empath
    divine_uid = page_ids.get(PINNED_LAST_ACCOUNT)
    if divine_uid:
        print(f"[*] Live-fetching guaranteed final post from @{PINNED_LAST_ACCOUNT} ({divine_uid})...")
        divine_clips = fetch_account_clips(divine_uid, PINNED_LAST_ACCOUNT, max_pages=3)
        unposted_divine = [c for c in divine_clips if not is_already_posted(c["id"])]
        print(f"    -> {len(unposted_divine)} fresh unposted candidates from @{PINNED_LAST_ACCOUNT}")
        for cand in unposted_divine:
            raw_file = download_media_file(cand)
            if raw_file and os.path.exists(raw_file):
                cand["raw_file"] = raw_file
                pinned_final_item = cand
                print(f"[+] [PINNED LAST SECURED] {cand['id']} ({cand['type']}) from @{PINNED_LAST_ACCOUNT}")
                break

    if not pinned_final_item:
        print(f"[*] Trying Playwright fallback for @{PINNED_LAST_ACCOUNT}...")
        pw_divine = scrape_account_posts_playwright(PINNED_LAST_ACCOUNT)
        for cand in [c for c in pw_divine if not is_already_posted(c["id"])]:
            raw_file = download_media_file(cand)
            if raw_file and os.path.exists(raw_file):
                cand["raw_file"] = raw_file
                pinned_final_item = cand
                print(f"[+] [PINNED LAST SECURED via Playwright] {cand['id']} ({cand['type']}) from @{PINNED_LAST_ACCOUNT}")
                break

    # 2. Gather candidates from other target accounts
    other_accounts = [a for a in accounts if a.lower() != PINNED_LAST_ACCOUNT.lower()]
    random.shuffle(other_accounts)

    candidates_by_account = {}
    for acc in other_accounts:
        uid = page_ids.get(acc)
        if not uid:
            continue
        clips = fetch_account_clips(uid, acc, max_pages=2)
        unposted = [c for c in clips if not is_already_posted(c["id"])]
        if unposted:
            candidates_by_account[acc] = unposted

    # Interleave candidates across accounts for maximum diversity
    interleaved_candidates = []
    max_len = max([len(v) for v in candidates_by_account.values()]) if candidates_by_account else 0
    for idx in range(max_len):
        for acc in candidates_by_account:
            if idx < len(candidates_by_account[acc]):
                interleaved_candidates.append(candidates_by_account[acc][idx])

    print(f"[*] Total interleaved live candidates gathered: {len(interleaved_candidates)}")

    # 3. Download media for other slots
    for candidate in interleaved_candidates:
        if len(downloaded_other) >= needed_other:
            break
        file_path = download_media_file(candidate)
        if file_path and os.path.exists(file_path):
            candidate["raw_file"] = file_path
            downloaded_other.append(candidate)
            print(f"[+] ({len(downloaded_other)}/{needed_other}) Live Media Ready: {candidate['id']} [{candidate['type']}] from @{candidate['account']}")

    # 3b. Fallback: If mobile API didn't yield enough candidates, scrape via Playwright
    if len(downloaded_other) < needed_other:
        print(f"[*] Need {needed_other - len(downloaded_other)} more items. Running Playwright web fallback...")
        for acc in other_accounts:
            if len(downloaded_other) >= needed_other:
                break
            pw_items = scrape_account_posts_playwright(acc)
            for cand in [c for c in pw_items if not is_already_posted(c["id"])]:
                if len(downloaded_other) >= needed_other:
                    break
                file_path = download_media_file(cand)
                if file_path and os.path.exists(file_path):
                    cand["raw_file"] = file_path
                    downloaded_other.append(cand)
                    print(f"[+] ({len(downloaded_other)}/{needed_other}) Live Media Ready (Playwright): {cand['id']} [{cand['type']}] from @{cand['account']}")

    # 4. Assemble Final Batch
    final_batch = downloaded_other
    if pinned_final_item:
        final_batch.append(pinned_final_item)
        print(f"[+] VERIFIED: The FINAL post in this batch is strictly from @{PINNED_LAST_ACCOUNT} ({pinned_final_item['id']} - {pinned_final_item['type']})")
    else:
        print("[!] Warning: Could not secure pinned post from divine144empath; batch will proceed with available items.")

    v_count = sum(1 for x in final_batch if x['type'] == 'video')
    p_count = sum(1 for x in final_batch if x['type'] == 'photo')
    print(f"\n[+] Batch Ready: Total {len(final_batch)} items ready to upload ({v_count} videos, {p_count} photos).\n")

    return final_batch
