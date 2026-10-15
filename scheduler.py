import time
import random
from main import run_single_cycle
from config import CHECK_INTERVAL_HOURS, RANDOM_JITTER_MINUTES

def start_scheduler():
    """
    Runs the Snapchat story automation 4-5 times a day.
    Includes randomized intervals to ensure natural, organic posting behavior.
    """
    print("=" * 65)
    print(" SNAPCHAT STORY 24/7 LOCAL SCHEDULER")
    print(f" Target Frequency: 4-5 times a day (every ~{CHECK_INTERVAL_HOURS} hours)")
    print("=" * 65)

    # Run one immediate check on startup
    run_single_cycle()

    while True:
        base_seconds = CHECK_INTERVAL_HOURS * 3600
        jitter_seconds = random.randint(-RANDOM_JITTER_MINUTES * 60, RANDOM_JITTER_MINUTES * 60)
        sleep_duration = max(3600, base_seconds + jitter_seconds)

        next_run_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + sleep_duration))
        print(f"\n[+] Sleeping for {sleep_duration / 3600:.2f} hours. Next cycle at: {next_run_time}")
        time.sleep(sleep_duration)

        try:
            run_single_cycle()
        except Exception as e:
            print(f"[!] Error during scheduled execution: {e}")

if __name__ == "__main__":
    start_scheduler()
