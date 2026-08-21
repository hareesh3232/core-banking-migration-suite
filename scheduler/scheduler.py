import os
import sys
import time
import argparse
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from etl.run_migration import run_migration_pipeline

def scheduled_job_task(mask_pii=True, rows=500, error_rate=0.05):
    print(f"\n[SCHEDULER] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Triggering scheduled migration run...")
    try:
        summary = run_migration_pipeline(
            data_dir="./data",
            mask_pii=mask_pii,
            generate_new=True,
            rows=rows,
            error_rate=error_rate,
            triggered_by="CRON_SCHEDULER"
        )
        print(f"[SCHEDULER] Run completed: {summary['run_id']} - Status: {summary['status']}")
    except Exception as e:
        print(f"[SCHEDULER] Scheduled run failed: {e}")

def run_scheduler(interval_seconds=60, runs_to_execute=1, mask_pii=True):
    print(f"[*] Core Banking Data Migration Suite Scheduler Daemon Started")
    print(f"[*] Running every {interval_seconds} seconds for {runs_to_execute} iteration(s)...")

    for i in range(runs_to_execute):
        scheduled_job_task(mask_pii=mask_pii)
        if i < runs_to_execute - 1:
            time.sleep(interval_seconds)

    print("[*] Scheduler daemon finished executed iterations.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Core Banking Migration Suite Scheduler")
    parser.add_argument("--interval", type=int, default=60, help="Interval between runs in seconds")
    parser.add_argument("--iterations", type=int, default=1, help="Number of scheduled iterations to execute")
    parser.add_argument("--pii-masking", action="store_true", default=True, help="Enable PII masking mode")

    args = parser.parse_args()
    run_scheduler(interval_seconds=args.interval, runs_to_execute=args.iterations, mask_pii=args.pii_masking)
