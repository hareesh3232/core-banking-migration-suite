namespace CoreBankingMigration.Api.Models
{
    public class MigrationRunModel
    {
        public string RunID { get; set; } = string.Empty;
        public string Status { get; set; } = "PENDING";
        public string StartTime { get; set; } = string.Empty;
        public string? EndTime { get; set; }
        public int TotalSourceRecords { get; set; }
        public int TotalMigratedRecords { get; set; }
        public int TotalRejectedRecords { get; set; }
        public bool MaskPII { get; set; }
        public string TriggeredBy { get; set; } = "SYSTEM";
        public string? ErrorMessage { get; set; }
    }

    public class MigrationRequest
    {
        public bool MaskPII { get; set; } = false;
        public int Rows { get; set; } = 1000;
        public double ErrorRate { get; set; } = 0.05;
        public string TriggeredBy { get; set; } = "WEB_DASHBOARD";
    }

    public class ReconciliationItem
    {
        public int ReportID { get; set; }
        public string RunID { get; set; } = string.Empty;
        public string EntityName { get; set; } = string.Empty;
        public int SourceCount { get; set; }
        public int TargetCount { get; set; }
        public int RejectedCount { get; set; }
        public double SourceChecksum { get; set; }
        public double TargetChecksum { get; set; }
        public string MatchStatus { get; set; } = "MATCH";
        public string GeneratedAt { get; set; } = string.Empty;
    }

    public class AuditLogModel
    {
        public int LogID { get; set; }
        public string RunID { get; set; } = string.Empty;
        public string EntityName { get; set; } = string.Empty;
        public string? SourceRecordID { get; set; }
        public string Action { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public string? Reason { get; set; }
        public string? Payload { get; set; }
        public string CreatedAt { get; set; } = string.Empty;
    }

    public class ReconciliationResponse
    {
        public MigrationRunModel Run { get; set; } = new();
        public List<ReconciliationItem> Reports { get; set; } = new();
        public List<AuditLogModel> RejectedRecords { get; set; } = new();
    }

    public class SettingsModel
    {
        public bool PiiMaskingEnabled { get; set; } = true;
        public string DatabaseType { get; set; } = "SQL Server / SQLite Engine";
        public string ConnectionStatus { get; set; } = "CONNECTED";
        public string LastMigrationRunID { get; set; } = string.Empty;
        public string TargetPlatform { get; set; } = "CoreBank v2.4 Normalized Target";
    }
}
