import os
import re
import time
import requests
import yt_dlp
from playwright.sync_api import sync_playwright
from config import (
    INSTAGRAM_PROFILE_URL,
    CHROME_USER_AGENT,
    MEDIA_DIR,
    ALLOWED_MEDIA_TYPES
)
from history_manager import is_already_posted

def extract_post_id(url):
    """Extracts unique shortcode identifier from Instagram URL."""
    match = re.search(r'/(?:p|reel)/([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else None

def scrape_profile_grid(max_posts=15, retries=3):
    """
    Scrapes the public Instagram profile grid using Playwright.
    Robust against layout changes and requires no login.
    """
    for attempt in range(1, retries + 1):
        try:
            print(f"[*] Scraping Instagram profile (attempt {attempt}/{retries})...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=CHROME_USER_AGENT,
                    viewport={"width": 1280, "height": 800}
                )
                page = context.new_page()
                page.goto(INSTAGRAM_PROFILE_URL, wait_until="domcontentloaded", timeout=25000)
                
                # Wait for grid items to settle
                page.wait_for_timeout(3500)
                
                # Close any login dialog popups if they appear
                try:
                    close_btn = page.locator('svg[aria-label="Close"], button:has-text("Close"), div[role="dialog"] button').first
                    if close_btn.is_visible(timeout=2000):
                        close_btn.click()
                except Exception:
                    pass

                # Locate all posts in the grid
                anchors = page.locator("article a, main a, div a").all()
                scraped_posts = []
                seen_ids = set()

                for a in anchors:
                    href = a.get_attribute("href")
                    if not href or ("/p/" not in href and "/reel/" not in href):
                        continue

                    post_id = extract_post_id(href)
                    if not post_id or post_id in seen_ids:
                        continue
                    seen_ids.add(post_id)

                    img_elem = a.locator("img").first if a.locator("img").count() > 0 else None
                    img_src = img_elem.get_attribute("src") if img_elem else None
                    alt_text = img_elem.get_attribute("alt") if img_elem else ""

                    is_video = "/reel/" in href or (alt_text and "video" in alt_text.lower())
                    post_type = "video" if is_video else "photo"

                    scraped_posts.append({
                        "id": post_id,
                        "type": post_type,
                        "url": f"https://www.instagram.com{href}" if href.startswith("/") else href,
                        "img_src": img_src,
                        "alt": alt_text
                    })

                    if len(scraped_posts) >= max_posts:
                        break

                browser.close()

                if scraped_posts:
                    print(f"[+] Successfully extracted {len(scraped_posts)} posts from grid.")
                    return scraped_posts
                else:
                    print(f"[-] No posts extracted on attempt {attempt}.")

        except Exception as e:
            print(f"[!] Scraper attempt {attempt} failed: {e}")
            time.sleep(3 * attempt)

    return []

def download_video_reel(post):
    """
    Downloads video reel using yt-dlp with multiple format fallbacks.
    """
    post_id = post["id"]
    output_template = os.path.join(MEDIA_DIR, f"{post_id}_raw.%(ext)s")

    # Strategy 1: Best video + best audio combined
    ydl_opts_primary = {
        'outtmpl': output_template,
        'format': 'bestvideo+bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'overwrites': True,
    }

    try:
        print(f"[*] Downloading video reel ({post_id}) via yt-dlp...")
        with yt_dlp.YoutubeDL(ydl_opts_primary) as ydl:
            ydl.download([post["url"]])
    except Exception as e1:
        print(f"[!] Primary format download failed: {e1}. Trying single-file best format fallback...")
        # Strategy 2: Direct pre-merged format fallback
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
            print(f"[!] Fallback download failed: {e2}")
            return None

    # Find the downloaded file
    for ext in ["mp4", "webm", "mkv"]:
        candidate = os.path.join(MEDIA_DIR, f"{post_id}_raw.{ext}")
        if os.path.exists(candidate) and os.path.getsize(candidate) > 1024:
            return candidate

    return None

def download_photo_meme(post):
    """
    Downloads photo meme using direct CDN stream with requests fallback.
    """
    post_id = post["id"]
    output_path = os.path.join(MEDIA_DIR, f"{post_id}_raw.jpg")

    img_url = post.get("img_src")
    if not img_url:
        print(f"[-] No direct image URL found for {post_id}.")
        return None

    headers = {
        "User-Agent": CHROME_USER_AGENT,
        "Referer": "https://www.instagram.com/",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    }

    try:
        print(f"[*] Downloading photo meme ({post_id})...")
        resp = requests.get(img_url, headers=headers, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 1024:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return output_path
        else:
            print(f"[-] HTTP {resp.status_code} while downloading image.")
    except Exception as e:
        print(f"[!] Failed to download photo {post_id}: {e}")

    return None

def fetch_next_unposted_media():
    """
    Finds the freshest unposted item from target profile and downloads it.
    Iterates through posts until a successful download occurs (fallback mechanism).
    """
    posts = scrape_profile_grid()
    if not posts:
        print("[-] Could not retrieve posts from Instagram.")
        return None, None

    unposted = [p for p in posts if not is_already_posted(p["id"]) and p["type"] in ALLOWED_MEDIA_TYPES]
    print(f"[*] Total unposted candidates available: {len(unposted)}")

    if not unposted:
        print("[i] All recent posts have already been posted to Snapchat!")
        return None, None

    # Try downloading candidates sequentially until one succeeds
    for candidate in unposted:
        print(f"[*] Attempting to fetch candidate: {candidate['id']} ({candidate['type']})")
        if candidate["type"] == "video":
            downloaded_file = download_video_reel(candidate)
        else:
            downloaded_file = download_photo_meme(candidate)

        if downloaded_file and os.path.exists(downloaded_file):
            print(f"[+] Download complete: {downloaded_file}")
            return downloaded_file, candidate
        else:
            print(f"[!] Failed to download {candidate['id']}. Moving to next unposted candidate...")

    print("[-] All candidate downloads failed in this cycle.")
    return None, None
