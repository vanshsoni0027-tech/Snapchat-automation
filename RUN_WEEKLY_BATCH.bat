@echo off
title Snapchat Weekly Batch & Scheduling Pipeline
cd /d "D:\snapchat automation"
echo ====================================================================
echo         SNAPCHAT 1-WEEK BATCH DOWNLOAD & AUTO-SCHEDULER
echo ====================================================================
echo  1. Scrapes unposted reels/memes from all target accounts
echo  2. Formats all items to 9:16 vertical with blurred backdrop
echo  3. Generates 7-day schedule slots (4 posts per day)
echo  4. Schedules all posts into Snapchat Creator Portal
echo ====================================================================
python weekly_scheduler.py
echo.
echo Done! Check history.json or logs above.
pause
