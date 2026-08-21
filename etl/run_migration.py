import os
import sys
import uuid
import argparse
from datetime import datetime

# Ensure parent path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data-generator")))

from database.db_engine import init_db, get_connection
from generator import generate_legacy_data
from etl.loader import load_staging_data, execute_transformation_procedures
from etl.reconciler import generate_reconciliation_report

def run_migration_pipeline(data_dir="./data", mask_pii=False, generate_new=False, rows=1000, error_rate=0.05, triggered_by="MANUAL_CLI"):
    init_db()
    
    run_id = f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
    print(f"[*] Initializing Migration Run: {run_id}")

    # Generate synthetic dirty files if requested or missing
    cust_file = os.path.join(data_dir, "customers.csv")
    if generate_new or not os.path.exists(cust_file):
        print(f"[*] Generating synthetic legacy datasets in {data_dir}...")
        generate_legacy_data(num_rows=rows, error_rate=error_rate, output_dir=data_dir)

    # 1. Record Run in Database
    conn = get_connection()
    cursor = conn.cursor()
    start_time = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO Migration_Runs (RunID, Status, StartTime, MaskPII, TriggeredBy)
    VALUES (?, 'RUNNING', ?, ?, ?)
    """, (run_id, start_time, 1 if mask_pii else 0, triggered_by))
    conn.commit()
    conn.close()

    try:
        # 2. Staging Load
        load_staging_data(run_id, data_dir=data_dir, mask_pii=mask_pii)

        # 3. Procedure Transformations
        execute_transformation_procedures(run_id)

        # 4. Reconciliation Report
        summary = generate_reconciliation_report(run_id)
        print(f"[OK] Migration Run {run_id} completed successfully!")
        return summary
    except Exception as e:
        print(f"[!] Migration Run {run_id} failed: {e}")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE Migration_Runs SET Status = 'FAILED', EndTime = ?, ErrorMessage = ? WHERE RunID = ?
        """, (datetime.now().isoformat(), str(e), run_id))
        conn.commit()
        conn.close()
        raise e

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Core Banking Migration Pipeline Runner")
    parser.add_argument("--data-dir", type=str, default="./data", help="Directory containing legacy CSV files")
    parser.add_argument("--pii-masking", action="store_true", help="Enable PII masking mode for non-prod compliance")
    parser.add_argument("--generate-new", action="store_true", help="Force new synthetic data generation before run")
    parser.add_argument("--rows", type=int, default=1000, help="Number of rows if generating synthetic data")
    parser.add_argument("--error-rate", type=float, default=0.05, help="Error rate if generating synthetic data")
    parser.add_argument("--triggered-by", type=str, default="CLI_USER", help="Trigger source label")

    args = parser.parse_args()
    run_migration_pipeline(
        data_dir=args.data_dir,
        mask_pii=args.pii_masking,
        generate_new=args.generate_new,
        rows=args.rows,
        error_rate=args.error_rate,
        triggered_by=args.triggered_by
    )
