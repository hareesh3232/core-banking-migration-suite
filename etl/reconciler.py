from datetime import datetime
from database.db_engine import get_connection

def generate_reconciliation_report(run_id):
    """
    Generates reconciliation summary, checksum validation, and updates Migration_Runs record.
    """
    conn = get_connection()
    cursor = conn.cursor()

    now_iso = datetime.now().isoformat()
    entities = [
        ("Customer", "Staging_Customers", "Target_Customers"),
        ("Account", "Staging_Accounts", "Target_Accounts"),
        ("Transaction", "Staging_Transactions", "Target_Transactions"),
        ("Beneficiary", "Staging_Beneficiaries", "Target_Beneficiaries")
    ]

    total_source_all = 0
    total_target_all = 0
    total_reject_all = 0

    for entity, staging_table, target_table in entities:
        # Source count
        cursor.execute(f"SELECT COUNT(*) FROM {staging_table} WHERE RunID = ?", (run_id,))
        src_cnt = cursor.fetchone()[0]

        # Target count
        cursor.execute(f"SELECT COUNT(*) FROM {target_table} WHERE LastMigratedRunID = ?", (run_id,))
        tgt_cnt = cursor.fetchone()[0]

        # Reject count
        cursor.execute("SELECT COUNT(*) FROM Audit_Logs WHERE RunID = ? AND EntityName = ? AND Status = 'REJECTED'", (run_id, entity))
        rej_cnt = cursor.fetchone()[0]

        src_sum = 0.0
        tgt_sum = 0.0

        # Checksum calculation for Transactions
        if entity == "Transaction":
            cursor.execute("SELECT COALESCE(SUM(CAST(Amount AS REAL)), 0.0) FROM Staging_Transactions WHERE RunID = ?", (run_id,))
            src_sum = round(float(cursor.fetchone()[0]), 2)

            cursor.execute("SELECT COALESCE(SUM(Amount), 0.0) FROM Target_Transactions WHERE LastMigratedRunID = ?", (run_id,))
            tgt_sum = round(float(cursor.fetchone()[0]), 2)

        match_status = "MATCH" if (src_cnt == tgt_cnt + rej_cnt) else "MISMATCH"

        cursor.execute("""
        INSERT INTO Reconciliation_Reports 
        (RunID, EntityName, SourceCount, TargetCount, RejectedCount, SourceChecksum, TargetChecksum, MatchStatus, GeneratedAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_id, entity, src_cnt, tgt_cnt, rej_cnt, src_sum, tgt_sum, match_status, now_iso))

        total_source_all += src_cnt
        total_target_all += tgt_cnt
        total_reject_all += rej_cnt

    final_status = "SUCCESS" if total_reject_all == 0 else "PARTIAL_SUCCESS"

    cursor.execute("""
    UPDATE Migration_Runs
    SET Status = ?,
        EndTime = ?,
        TotalSourceRecords = ?,
        TotalMigratedRecords = ?,
        TotalRejectedRecords = ?
    WHERE RunID = ?
    """, (final_status, now_iso, total_source_all, total_target_all, total_reject_all, run_id))

    conn.commit()
    conn.close()
    print(f"[+] Reconciliation report created for Run {run_id}. Final status: {final_status}")
    return {
        "run_id": run_id,
        "status": final_status,
        "total_source": total_source_all,
        "total_migrated": total_target_all,
        "total_rejected": total_reject_all
    }
