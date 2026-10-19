#!/bin/bash
cd "$(dirname "$0")"
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi
export USER_DATA_DIR="$(pwd)/snapchat_profile"
xvfb-run -a python3 main.py >> automation.log 2>&1
