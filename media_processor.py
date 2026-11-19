import os
from PIL import Image
from config import (
    PROCESSED_DIR,
    TARGET_WIDTH,
    TARGET_HEIGHT,
    MAX_VIDEO_DURATION_SECONDS
)

def adapt_media_for_snapchat(raw_path, post_info):
    """
    Master media adapter: Passes downloaded media directly as-is to Snapchat.
    Zero cropping, zero blurring, zero resizing, zero aspect ratio modification.
    Uploads downloaded files 'wese ki weso' (as-is).
    """
    if not raw_path or not os.path.exists(raw_path):
        return None

    post_id = post_info.get("id", "media")
    media_type = post_info.get("type", "video")

    # If it is an image (jpg, jpeg, png, webp)
    if media_type == "photo" or raw_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        ext = os.path.splitext(raw_path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png']:
            print(f"[+] Photo preserved 100% as-is without cropping: {raw_path}")
            return raw_path
        else:
            # Convert webp to high-quality jpeg preserving exact natural resolution
            try:
                out_path = os.path.join(PROCESSED_DIR, f"{post_id}_story.jpg")
                with Image.open(raw_path) as img:
                    img = img.convert("RGB")
                    img.save(out_path, "JPEG", quality=98)
                print(f"[+] Photo converted to JPEG without cropping ({img.size}): {out_path}")
                return out_path
            except Exception as e:
                print(f"[!] Photo format conversion fallback: {e}")
                return raw_path

    # If it is a video (mp4, mov, webm)
    print(f"[+] Video preserved 100% as-is without cropping: {raw_path}")
    return raw_path
