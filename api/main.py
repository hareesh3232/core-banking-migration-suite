import os
import sys
import uvicorn
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.db_engine import init_db, get_connection
from etl.run_migration import run_migration_pipeline

app = FastAPI(
    title="Core Banking Data Migration API",
    description="REST API Service Layer for Core Banking Data Migration Suite",
    version="1.0.0"
)

# Enable CORS for React dashboard frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GLOBAL_SETTINGS = {
    "piiMaskingEnabled": True,
    "databaseType": "SQL Server / SQLite Engine",
    "connectionStatus": "CONNECTED",
    "targetPlatform": "CoreBank v2.4 Normalized Core Target"
}

@app.get("/")
def root():
    """Basic service health response for hosting-platform checks."""
    return {
        "service": "Core Banking Data Migration API",
        "status": "healthy",
        "docs": "/docs",
        "migrations": "/api/migrations"
    }

@app.get("/healthz")
def health_check():
    return {"status": "healthy"}

@app.get("/ping")
def ping():
    return {"status": "ok"}

class MigrationRequest(BaseModel):
    maskPII: Optional[bool] = False
    rows: Optional[int] = 1000
    errorRate: Optional[float] = 0.05
    triggeredBy: Optional[str] = "WEB_DASHBOARD"

class SettingsModel(BaseModel):
    piiMaskingEnabled: bool
    databaseType: Optional[str] = "SQL Server / SQLite Engine"
    connectionStatus: Optional[str] = "CONNECTED"
    targetPlatform: Optional[str] = "CoreBank v2.4 Normalized Core Target"

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/api/migrations")
def get_past_runs():
    """Returns list of past migration runs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT RunID, Status, StartTime, EndTime, TotalSourceRecords, TotalMigratedRecords, TotalRejectedRecords, MaskPII, TriggeredBy, ErrorMessage
    FROM Migration_Runs ORDER BY StartTime DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    runs = []
    for r in rows:
        runs.append({
            "runID": r[0],
            "status": r[1],
            "startTime": r[2],
            "endTime": r[3],
            "totalSourceRecords": r[4],
            "totalMigratedRecords": r[5],
            "totalRejectedRecords": r[6],
            "maskPII": bool(r[7]),
            "triggeredBy": r[8],
            "errorMessage": r[9]
        })
    return runs

@app.post("/api/migrations/run")
def trigger_migration_run(req: MigrationRequest):
    """Triggers a new migration run pipeline."""
    mask_pii = req.maskPII or GLOBAL_SETTINGS["piiMaskingEnabled"]
    try:
        summary = run_migration_pipeline(
            data_dir="./data",
            mask_pii=mask_pii,
            generate_new=True,
            rows=req.rows or 1000,
            error_rate=req.errorRate or 0.05,
            triggered_by=req.triggeredBy or "WEB_DASHBOARD"
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/migrations/{run_id}/status")
def get_run_status(run_id: str):
    """Returns status details for a specific migration run."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT RunID, Status, StartTime, EndTime, TotalSourceRecords, TotalMigratedRecords, TotalRejectedRecords, MaskPII, TriggeredBy, ErrorMessage
    FROM Migration_Runs WHERE RunID = ?
    """, (run_id,))
    r = cursor.fetchone()
    conn.close()

    if not r:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return {
        "runID": r[0],
        "status": r[1],
        "startTime": r[2],
        "endTime": r[3],
        "totalSourceRecords": r[4],
        "totalMigratedRecords": r[5],
        "totalRejectedRecords": r[6],
        "maskPII": bool(r[7]),
        "triggeredBy": r[8],
        "errorMessage": r[9]
    }

@app.get("/api/migrations/{run_id}/reconciliation")
def get_reconciliation(run_id: str):
    """Returns source vs target row counts, checksums, and rejected records for a run."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get Run details
    cursor.execute("SELECT RunID, Status, StartTime, EndTime, TotalSourceRecords, TotalMigratedRecords, TotalRejectedRecords, MaskPII, TriggeredBy FROM Migration_Runs WHERE RunID = ?", (run_id,))
    run_row = cursor.fetchone()
    if not run_row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    run_dict = {
        "runID": run_row[0],
        "status": run_row[1],
        "startTime": run_row[2],
        "endTime": run_row[3],
        "totalSourceRecords": run_row[4],
        "totalMigratedRecords": run_row[5],
        "totalRejectedRecords": run_row[6],
        "maskPII": bool(run_row[7]),
        "triggeredBy": run_row[8]
    }

    # Get Reports
    cursor.execute("""
    SELECT ReportID, RunID, EntityName, SourceCount, TargetCount, RejectedCount, SourceChecksum, TargetChecksum, MatchStatus, GeneratedAt
    FROM Reconciliation_Reports WHERE RunID = ?
    """, (run_id,))
    report_rows = cursor.fetchall()
    reports = []
    for rep in report_rows:
        reports.append({
            "reportID": rep[0],
            "runID": rep[1],
            "entityName": rep[2],
            "sourceCount": rep[3],
            "targetCount": rep[4],
            "rejectedCount": rep[5],
            "sourceChecksum": rep[6],
            "targetChecksum": rep[7],
            "matchStatus": rep[8],
            "generatedAt": rep[9]
        })

    # Get Rejected Records
    cursor.execute("""
    SELECT LogID, RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload, CreatedAt
    FROM Audit_Logs WHERE RunID = ? AND Status = 'REJECTED' ORDER BY LogID DESC LIMIT 300
    """, (run_id,))
    rej_rows = cursor.fetchall()
    rejected = []
    for r in rej_rows:
        rejected.append({
            "logID": r[0],
            "runID": r[1],
            "entityName": r[2],
            "sourceRecordID": r[3],
            "action": r[4],
            "status": r[5],
            "reason": r[6],
            "payload": r[7],
            "createdAt": r[8]
        })

    conn.close()

    return {
        "run": run_dict,
        "reports": reports,
        "rejectedRecords": rejected
    }

@app.get("/api/audit")
def get_audit_logs(
    entity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100)
):
    """Returns searchable/filterable audit log entries."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT LogID, RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload, CreatedAt FROM Audit_Logs WHERE 1=1"
    params = []

    if entity:
        query += " AND EntityName = ?"
        params.append(entity)
    if status:
        query += " AND Status = ?"
        params.append(status)
    if search:
        query += " AND (SourceRecordID LIKE ? OR Reason LIKE ? OR Payload LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " ORDER BY LogID DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    logs = []
    for r in rows:
        logs.append({
            "logID": r[0],
            "runID": r[1],
            "entityName": r[2],
            "sourceRecordID": r[3],
            "action": r[4],
            "status": r[5],
            "reason": r[6],
            "payload": r[7],
            "createdAt": r[8]
        })
    return logs

@app.get("/api/settings")
def get_settings():
    """Returns system settings and PII masking status."""
    runs = get_past_runs()
    last_run_id = runs[0]["runID"] if runs else "NONE"
    return {
        "piiMaskingEnabled": GLOBAL_SETTINGS["piiMaskingEnabled"],
        "databaseType": GLOBAL_SETTINGS["databaseType"],
        "connectionStatus": GLOBAL_SETTINGS["connectionStatus"],
        "lastMigrationRunID": last_run_id,
        "targetPlatform": GLOBAL_SETTINGS["targetPlatform"]
    }

@app.post("/api/settings")
def update_settings(settings: SettingsModel):
    """Updates PII masking toggle and configuration."""
    GLOBAL_SETTINGS["piiMaskingEnabled"] = settings.piiMaskingEnabled
    return get_settings()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
