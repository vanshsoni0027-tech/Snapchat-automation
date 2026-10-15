import os
import json
import subprocess
from PIL import Image, ImageFilter
from config import (
    PROCESSED_DIR,
    TARGET_WIDTH,
    TARGET_HEIGHT,
    MAX_VIDEO_DURATION_SECONDS
)

def inspect_video(file_path):
    """Inspects video resolution and duration using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height,duration,codec_type",
        "-show_entries", "format=duration",
        "-of", "json",
        file_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(res.stdout)
        width, height, duration = 1080, 1920, 30.0
        
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                width = int(stream.get("width", 1080))
                height = int(stream.get("height", 1920))
                break
                
        dur_str = data.get("format", {}).get("duration")
        if dur_str:
            duration = float(dur_str)

        return width, height, duration
    except Exception as e:
        print(f"[!] ffprobe inspection error: {e}")
        return 1080, 1920, 30.0

def process_video_reel(input_path, output_path):
    """
    Formats video into a clean 9:16 vertical 1080x1920 video with creative blurred background.
    Has automated fallback to simple padding if complex filters fail.
    """
    width, height, duration = inspect_video(input_path)
    aspect_ratio = width / height if height > 0 else 0.5625
    trim_duration = min(duration, MAX_VIDEO_DURATION_SECONDS)

    print(f"[*] Processing video: {width}x{height} (duration: {duration:.1f}s, target trim: {trim_duration:.1f}s)")

    # Strategy 1: Modern Blurred Background Overlay (Creative 9:16 presentation)
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[outv]"
    )
    cmd_creative = [
        "ffmpeg", "-y", "-i", input_path,
        "-t", str(trim_duration),
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    try:
        print("[*] Running creative 9:16 blurred-backdrop video rendering...")
        res = subprocess.run(cmd_creative, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
            print("[+] Creative video processing succeeded.")
            return output_path
        else:
            print(f"[!] Creative video filter returned error: {res.stderr[:200]}")
    except Exception as e:
        print(f"[!] Creative filter execution exception: {e}")

    # Strategy 2: Simple Pad Fallback
    print("[*] Falling back to standard scale & pad filter...")
    cmd_fallback = [
        "ffmpeg", "-y", "-i", input_path,
        "-t", str(trim_duration),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    try:
        res = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0 and os.path.exists(output_path):
            print("[+] Standard pad processing succeeded.")
            return output_path
    except Exception as e:
        print(f"[!] Fallback video processing failed: {e}")

    return input_path

def process_photo_meme(input_path, output_path):
    """
    Formats photo/meme into 1080x1920 9:16 vertical canvas with aesthetic blurred background.
    """
    print(f"[*] Processing meme image: {input_path}")
    try:
        with Image.open(input_path) as img:
            img = img.convert("RGB")
            orig_w, orig_h = img.size

            # Create background canvas (1080x1920) with blurred zoomed version
            bg_scale = max(TARGET_WIDTH / orig_w, TARGET_HEIGHT / orig_h)
            bg_w = int(orig_w * bg_scale)
            bg_h = int(orig_h * bg_scale)
            bg_img = img.resize((bg_w, bg_h), Image.Resampling.LANCZOS)
            
            # Crop to exact 1080x1920
            left = (bg_w - TARGET_WIDTH) // 2
            top = (bg_h - TARGET_HEIGHT) // 2
            bg_cropped = bg_img.crop((left, top, left + TARGET_WIDTH, top + TARGET_HEIGHT))
            bg_blurred = bg_cropped.filter(ImageFilter.GaussianBlur(radius=25))

            # Foreground sharp meme (scale to fit within 1080x1920 without cropping)
            fg_scale = min(TARGET_WIDTH / orig_w, TARGET_HEIGHT / orig_h)
            fg_w = int(orig_w * fg_scale)
            fg_h = int(orig_h * fg_scale)
            fg_img = img.resize((fg_w, fg_h), Image.Resampling.LANCZOS)

            # Paste centered
            paste_x = (TARGET_WIDTH - fg_w) // 2
            paste_y = (TARGET_HEIGHT - fg_h) // 2
            bg_blurred.paste(fg_img, (paste_x, paste_y))

            bg_blurred.save(output_path, "JPEG", quality=95)
            print(f"[+] Meme formatted to 9:16 vertical successfully: {output_path}")
            return output_path

    except Exception as e:
        print(f"[!] Pillow image processing failed: {e}. Trying raw fallback...")
        return input_path

def adapt_media_for_snapchat(raw_path, post_info):
    """
    Master adapter dispatching video or photo processing.
    """
    post_id = post_info["id"]
    media_type = post_info["type"]

    if media_type == "video":
        output_file = os.path.join(PROCESSED_DIR, f"{post_id}_story.mp4")
        return process_video_reel(raw_path, output_file)
    else:
        output_file = os.path.join(PROCESSED_DIR, f"{post_id}_story.jpg")
        return process_photo_meme(raw_path, output_file)
