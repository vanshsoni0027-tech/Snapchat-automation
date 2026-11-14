@echo off
title Snapchat 1-Click Login & Auto-Upload
cd /d "D:\snapchat automation"
echo ==============================================================
echo        SNAPCHAT 1-CLICK AUTHENTICATION & LIVE POST
echo ==============================================================
echo A browser window is opening. Please log in to your Snapchat.
echo Once logged in, the window will auto-close and upload your reel!
echo ==============================================================
python login_and_post.py
pause
