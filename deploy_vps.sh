#!/bin/bash
# ==============================================================================
# SNAPCHAT 24/7 100% AUTOMATED BOT - VPS DEPLOYMENT SCRIPT
# Supports: Ubuntu 22.04 / 24.04 (Oracle Cloud Always-Free / AWS / GCP / DigitalOcean)
# ==============================================================================

set -e

echo "=================================================================="
echo "    INSTALLING 24/7 SNAPCHAT STORY AUTOMATION BOT"
echo "=================================================================="

# 0. Ensure 2GB Swap for 1GB RAM instances
if [ $(swapon --show | wc -l) -le 1 ]; then
    echo "[*] Creating 2GB Swap space for smooth Chromium performance..."
    sudo fallocate -l 2G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# 1. Update OS and Install System Packages
echo "[*] Updating system packages and installing dependencies..."

sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 python3-pip python3-venv \
    ffmpeg git curl wget cron \
    xvfb x11vnc novnc websockify \

    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2t64 || sudo apt-get install -y libasound2

# 2. Setup Working Directory and Python Virtualenv
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

echo "[*] Setting up Python virtual environment in $APP_DIR..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install-deps chromium
playwright install chromium

# Ensure folders exist
mkdir -p downloads processed snapchat_profile

# 3. Create 1-Click Login Helper
cat << 'EOF' > login.sh
#!/bin/bash
source venv/bin/activate

echo "=================================================================="
echo "          1-TIME SNAPCHAT ACCOUNT LOGIN"
echo "=================================================================="
echo "[*] Starting Virtual Display & Web Browser Interface..."

# Kill previous instances if any
pkill -f Xvfb || true
pkill -f x11vnc || true
pkill -f websockify || true

# Start Virtual Display (1280x900)
Xvfb :99 -screen 0 1280x900x24 &
sleep 2

# Start VNC Server
x11vnc -display :99 -nopw -listen localhost -xkb -ncache 10 -forever &
sleep 2

# Start Web VNC (noVNC) on port 6080
websockify --web /usr/share/novnc 6080 localhost:5900 &
sleep 2

# Download Cloudflare tunnel binary if not present (Bypasses all Google Cloud firewalls)
if [ ! -f ./cloudflared ]; then
    echo "[*] Setting up instant Cloudflare Tunnel (no firewall required)..."
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O ./cloudflared
    chmod +x ./cloudflared
fi

pkill -f cloudflared || true
./cloudflared tunnel --url http://localhost:6080 > cloudflare.log 2>&1 &
sleep 6

CF_URL=$(grep -o 'https://[-a-zA-Z0-9.]*\.trycloudflare\.com' cloudflare.log | head -n 1)

echo ""
echo "=================================================================="
echo "🎉 SUCCESS! Your secure cloud link is ready (No firewall needed):"
echo ""
echo "👉 CLICK OR OPEN THIS URL IN YOUR BROWSER / PHONE:"
if [ -n "$CF_URL" ]; then
    echo "   ${CF_URL}/vnc.html?autoconnect=true"
else
    PUBLIC_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "34.30.83.83")
    echo "   http://${PUBLIC_IP}:6080/vnc.html?autoconnect=true"
fi
echo ""
echo "👉 1. In the browser window that opens, log in to your Snapchat account."
echo "👉 2. Once you see the upload portal (my.snapchat.com), come back here"
echo "      and press [ENTER] to save your session permanently!"
echo "=================================================================="
echo ""


# Launch real Chromium on display :99 pointing to my.snapchat.com
DISPLAY=:99 python3 -c "
import os
from playwright.sync_api import sync_playwright

profile_dir = os.path.abspath('snapchat_profile')
with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        headless=False,
        args=['--disable-blink-features=AutomationControlled', '--no-sandbox'],
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        viewport={'width': 1280, 'height': 850}
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto('https://my.snapchat.com')
    input('>>> PRESS [ENTER] HERE ONCE YOU HAVE LOGGED IN TO SNAPCHAT <<<')
    context.close()
"

# Clean up VNC processes
pkill -f Xvfb || true
pkill -f x11vnc || true
pkill -f websockify || true
pkill -f cloudflared || true


echo ""
echo "[+] Snapchat session permanently saved to snapchat_profile!"
echo "[+] You will NEVER need to log in again!"
EOF
chmod +x login.sh

# 4. Create Run Wrapper for Cron
cat << EOF > run_cycle.sh
#!/bin/bash
cd $APP_DIR
source venv/bin/activate
export USER_DATA_DIR="$APP_DIR/snapchat_profile"
xvfb-run -a python3 main.py >> automation.log 2>&1
EOF
chmod +x run_cycle.sh

# 5. Setup Linux Cron Job (Runs 5 times daily: every 4.8 hours)
CRON_CMD="0 2,7,12,17,22 * * * $APP_DIR/run_cycle.sh"
(crontab -l 2>/dev/null | grep -v "$APP_DIR/run_cycle.sh" ; echo "$CRON_CMD") | crontab -

echo ""
echo "=================================================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo ""
echo "To log in to your Snapchat account, run:"
echo "   bash login.sh"
echo ""
echo "Your bot is now scheduled to post automatically 5 times every day!"
echo "You can check logs anytime with:"
echo "   tail -f automation.log"
echo "=================================================================="
