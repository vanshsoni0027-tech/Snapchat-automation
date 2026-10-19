#!/bin/bash
set -e

# Change to script directory
cd "$(dirname "$0")"

# Activate Python virtual environment
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

echo "=================================================================="
echo "          1-TIME SNAPCHAT ACCOUNT LOGIN"
echo "=================================================================="
echo "[*] Cleaning up old processes..."
pkill -f Xvfb || true
pkill -f x11vnc || true
pkill -f websockify || true
pkill -f cloudflared || true
sleep 1

echo "[*] Starting Virtual Display & Browser Server..."
Xvfb :99 -screen 0 1280x900x24 &
sleep 2

x11vnc -display :99 -nopw -listen localhost -xkb -ncache 10 -forever &
sleep 2

websockify --web /usr/share/novnc 6080 localhost:5900 &
sleep 2

# Download Cloudflare tunnel binary if not present (Bypasses Google Cloud firewall completely)
if [ ! -f ./cloudflared ]; then
    echo "[*] Downloading Cloudflare Tunnel (firewall bypass)..."
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O ./cloudflared
    chmod +x ./cloudflared
fi

echo "[*] Creating secure public HTTPS tunnel..."
pkill -f cloudflared || true
./cloudflared tunnel --url http://localhost:6080 > cloudflare.log 2>&1 &

# Wait for tunnel URL
CF_URL=""
for i in {1..12}; do
    sleep 1
    CF_URL=$(grep -o 'https://[-a-zA-Z0-9.]*\.trycloudflare\.com' cloudflare.log | head -n 1 || true)
    if [ -n "$CF_URL" ]; then
        break
    fi
done

echo ""
echo "=================================================================="
echo "🎉 SUCCESS! Your secure cloud link is ready (No firewall needed):"
echo ""
if [ -n "$CF_URL" ]; then
    echo "👉 CLICK OR OPEN THIS URL IN YOUR BROWSER / PHONE:"
    echo "   ${CF_URL}/vnc.html?autoconnect=true"
else
    PUBLIC_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "34.30.83.83")
    echo "👉 OPEN THIS URL:"
    echo "   http://${PUBLIC_IP}:6080/vnc.html?autoconnect=true"
fi
echo ""
echo "👉 1. In the browser window that opens, log in to your Snapchat account."
echo "👉 2. Once you see the upload portal (my.snapchat.com), come back here"
echo "      and press [ENTER] to save your session permanently!"
echo "=================================================================="
echo ""

# Ensure window manager is installed and running so windows render properly
if ! command -v openbox &> /dev/null; then
    sudo apt-get install -y openbox
fi
DISPLAY=:99 openbox &
sleep 1

# Launch Chromium on display :99 pointing to my.snapchat.com
DISPLAY=:99 python3 -c "
import os
from playwright.sync_api import sync_playwright

profile_dir = os.path.abspath('snapchat_profile')
os.makedirs(profile_dir, exist_ok=True)

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        headless=False,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-gpu',
            '--disable-dev-shm-usage',
            '--disable-software-rasterizer',
            '--no-first-run',
            '--no-default-browser-check',
            '--window-position=0,0',
            '--window-size=1280,850'
        ],
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        viewport={'width': 1280, 'height': 850}
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto('https://my.snapchat.com')
    input('>>> PRESS [ENTER] HERE ONCE YOU HAVE LOGGED IN TO SNAPCHAT <<<')
    context.close()
"


# Clean up
pkill -f Xvfb || true
pkill -f x11vnc || true
pkill -f websockify || true
pkill -f cloudflared || true

echo ""
echo "[+] Snapchat session permanently saved to snapchat_profile!"
echo "[+] Setup complete! Automation is now ready to run 24/7."
