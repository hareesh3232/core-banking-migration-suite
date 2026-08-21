using System.Data;
using System.Diagnostics;
using Microsoft.Data.Sqlite;
using CoreBankingMigration.Api.Models;

namespace CoreBankingMigration.Api.Services
{
    public class MigrationService : IMigrationService
    {
        private readonly string _dbPath;
        private static bool _globalPiiMasking = true;

        public MigrationService(IConfiguration configuration)
        {
            var envPath = configuration["Database:SqlitePath"] ?? "migration_suite.db";
            var candidatePaths = new[]
            {
                Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), envPath)),
                Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, envPath)),
                Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", envPath)),
                Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", envPath)),
                Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), "..", envPath))
            };

            _dbPath = candidatePaths
                .Where(path => !string.IsNullOrWhiteSpace(path))
                .FirstOrDefault(path => File.Exists(path)) ?? candidatePaths[0];

            EnsureDatabaseExists();
        }

        private void EnsureDatabaseExists()
        {
            var directory = Path.GetDirectoryName(_dbPath);
            if (!string.IsNullOrEmpty(directory))
            {
                Directory.CreateDirectory(directory);
            }

            using var conn = new SqliteConnection($"Data Source={_dbPath}");
            conn.Open();

            var schema = @"
                CREATE TABLE IF NOT EXISTS Migration_Runs (
                    RunID TEXT PRIMARY KEY,
                    Status TEXT NOT NULL DEFAULT 'PENDING',
                    StartTime TEXT NOT NULL,
                    EndTime TEXT,
                    TotalSourceRecords INTEGER NOT NULL DEFAULT 0,
                    TotalMigratedRecords INTEGER NOT NULL DEFAULT 0,
                    TotalRejectedRecords INTEGER NOT NULL DEFAULT 0,
                    MaskPII INTEGER NOT NULL DEFAULT 0,
                    TriggeredBy TEXT NOT NULL DEFAULT 'SYSTEM_SCHEDULER',
                    ErrorMessage TEXT
                );

                CREATE TABLE IF NOT EXISTS Audit_Logs (
                    LogID INTEGER PRIMARY KEY AUTOINCREMENT,
                    RunID TEXT NOT NULL,
                    EntityName TEXT NOT NULL,
                    SourceRecordID TEXT,
                    Action TEXT NOT NULL,
                    Status TEXT NOT NULL,
                    Reason TEXT,
                    Payload TEXT,
                    CreatedAt TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS Reconciliation_Reports (
                    ReportID INTEGER PRIMARY KEY AUTOINCREMENT,
                    RunID TEXT NOT NULL,
                    EntityName TEXT NOT NULL,
                    SourceCount INTEGER NOT NULL DEFAULT 0,
                    TargetCount INTEGER NOT NULL DEFAULT 0,
                    RejectedCount INTEGER NOT NULL DEFAULT 0,
                    SourceChecksum REAL DEFAULT 0.0,
                    TargetChecksum REAL DEFAULT 0.0,
                    MatchStatus TEXT NOT NULL,
                    GeneratedAt TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS Staging_Customers (
                    RawID INTEGER PRIMARY KEY AUTOINCREMENT,
                    RunID TEXT NOT NULL,
                    CustomerID TEXT,
                    SSN TEXT,
                    FirstName TEXT,
                    LastName TEXT,
                    DateOfBirth TEXT,
                    Email TEXT,
                    Phone TEXT,
                    Address TEXT,
                    CreatedAt TEXT
                );

                CREATE TABLE IF NOT EXISTS Staging_Accounts (
                    RawID INTEGER PRIMARY KEY AUTOINCREMENT,
                    RunID TEXT NOT NULL,
                    AccountNumber TEXT,
                    CustomerID TEXT,
                    AccountType TEXT,
                    Currency TEXT,
                    Balance TEXT,
                    OpenDate TEXT,
                    Status TEXT
                );

                CREATE TABLE IF NOT EXISTS Staging_Transactions (
                    RawID INTEGER PRIMARY KEY AUTOINCREMENT,
                    RunID TEXT NOT NULL,
                    TransactionID TEXT,
                    AccountNumber TEXT,
                    Amount TEXT,
                    Currency TEXT,
                    TransactionType TEXT,
                    TransactionDate TEXT,
                    Description TEXT
                );

                CREATE TABLE IF NOT EXISTS Staging_Beneficiaries (
                    RawID INTEGER PRIMARY KEY AUTOINCREMENT,
                    RunID TEXT NOT NULL,
                    BeneficiaryID TEXT,
                    CustomerID TEXT,
                    BeneficiaryName TEXT,
                    AccountNumber TEXT,
                    BankRoutingNumber TEXT,
                    AddedDate TEXT
                );

                CREATE TABLE IF NOT EXISTS Target_Customers (
                    CustomerID TEXT PRIMARY KEY,
                    SSN TEXT,
                    FirstName TEXT NOT NULL,
                    LastName TEXT NOT NULL,
                    DateOfBirth TEXT,
                    Email TEXT,
                    Phone TEXT,
                    Address TEXT,
                    CreatedAt TEXT NOT NULL,
                    LastMigratedRunID TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS Target_Accounts (
                    AccountNumber TEXT PRIMARY KEY,
                    CustomerID TEXT NOT NULL,
                    AccountType TEXT NOT NULL,
                    Currency TEXT NOT NULL DEFAULT 'USD',
                    Balance REAL NOT NULL DEFAULT 0.0,
                    OpenDate TEXT,
                    Status TEXT NOT NULL DEFAULT 'ACTIVE',
                    LastMigratedRunID TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS Target_Transactions (
                    TransactionID TEXT PRIMARY KEY,
                    AccountNumber TEXT NOT NULL,
                    Amount REAL NOT NULL,
                    Currency TEXT NOT NULL DEFAULT 'USD',
                    TransactionType TEXT NOT NULL,
                    TransactionDate TEXT NOT NULL,
                    Description TEXT,
                    LastMigratedRunID TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS Target_Beneficiaries (
                    BeneficiaryID TEXT PRIMARY KEY,
                    CustomerID TEXT NOT NULL,
                    BeneficiaryName TEXT NOT NULL,
                    AccountNumber TEXT NOT NULL,
                    BankRoutingNumber TEXT NOT NULL,
                    AddedDate TEXT,
                    LastMigratedRunID TEXT NOT NULL
                );";

            using var cmd = conn.CreateCommand();
            cmd.CommandText = schema;
            cmd.ExecuteNonQuery();
        }

        private SqliteConnection GetConnection()
        {
            EnsureDatabaseExists();
            var conn = new SqliteConnection($"Data Source={_dbPath}");
            conn.Open();
            return conn;
        }

        public async Task<List<MigrationRunModel>> GetAllRunsAsync()
        {
            var list = new List<MigrationRunModel>();
            using var conn = GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT RunID, Status, StartTime, EndTime, TotalSourceRecords, TotalMigratedRecords, TotalRejectedRecords, MaskPII, TriggeredBy, ErrorMessage FROM Migration_Runs ORDER BY StartTime DESC";

            using var reader = await cmd.ExecuteReaderAsync();
            while (await reader.ReadAsync())
            {
                list.Add(new MigrationRunModel
                {
                    RunID = reader.GetString(0),
                    Status = reader.GetString(1),
                    StartTime = reader.GetString(2),
                    EndTime = reader.IsDBNull(3) ? null : reader.GetString(3),
                    TotalSourceRecords = reader.GetInt32(4),
                    TotalMigratedRecords = reader.GetInt32(5),
                    TotalRejectedRecords = reader.GetInt32(6),
                    MaskPII = reader.GetInt32(7) == 1,
                    TriggeredBy = reader.GetString(8),
                    ErrorMessage = reader.IsDBNull(9) ? null : reader.GetString(9)
                });
            }
            return list;
        }

        public async Task<MigrationRunModel?> GetRunByIdAsync(string runId)
        {
            using var conn = GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT RunID, Status, StartTime, EndTime, TotalSourceRecords, TotalMigratedRecords, TotalRejectedRecords, MaskPII, TriggeredBy, ErrorMessage FROM Migration_Runs WHERE RunID = @runId";
            cmd.Parameters.AddWithValue("@runId", runId);

            using var reader = await cmd.ExecuteReaderAsync();
            if (await reader.ReadAsync())
            {
                return new MigrationRunModel
                {
                    RunID = reader.GetString(0),
                    Status = reader.GetString(1),
                    StartTime = reader.GetString(2),
                    EndTime = reader.IsDBNull(3) ? null : reader.GetString(3),
                    TotalSourceRecords = reader.GetInt32(4),
                    TotalMigratedRecords = reader.GetInt32(5),
                    TotalRejectedRecords = reader.GetInt32(6),
                    MaskPII = reader.GetInt32(7) == 1,
                    TriggeredBy = reader.GetString(8),
                    ErrorMessage = reader.IsDBNull(9) ? null : reader.GetString(9)
                };
            }
            return null;
        }

        public async Task<MigrationRunModel> TriggerRunAsync(MigrationRequest request)
        {
            var piiFlag = request.MaskPII || _globalPiiMasking ? "--pii-masking" : "";
            var psi = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = $"etl/run_migration.py --generate-new --rows {request.Rows} --error-rate {request.ErrorRate} {piiFlag} --triggered-by \"{request.TriggeredBy}\"",
                WorkingDirectory = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../..")),
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            var proc = Process.Start(psi);
            if (proc != null)
            {
                await proc.WaitForExitAsync();
            }

            var runs = await GetAllRunsAsync();
            return runs.FirstOrDefault() ?? new MigrationRunModel { RunID = "RUN-PENDING", Status = "RUNNING" };
        }

        public async Task<ReconciliationResponse?> GetReconciliationReportAsync(string runId)
        {
            var run = await GetRunByIdAsync(runId);
            if (run == null) return null;

            var reports = new List<ReconciliationItem>();
            using var conn = GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT ReportID, RunID, EntityName, SourceCount, TargetCount, RejectedCount, SourceChecksum, TargetChecksum, MatchStatus, GeneratedAt FROM Reconciliation_Reports WHERE RunID = @runId";
            cmd.Parameters.AddWithValue("@runId", runId);

            using (var reader = await cmd.ExecuteReaderAsync())
            {
                while (await reader.ReadAsync())
                {
                    reports.Add(new ReconciliationItem
                    {
                        ReportID = reader.GetInt32(0),
                        RunID = reader.GetString(1),
                        EntityName = reader.GetString(2),
                        SourceCount = reader.GetInt32(3),
                        TargetCount = reader.GetInt32(4),
                        RejectedCount = reader.GetInt32(5),
                        SourceChecksum = reader.GetDouble(6),
                        TargetChecksum = reader.GetDouble(7),
                        MatchStatus = reader.GetString(8),
                        GeneratedAt = reader.GetString(9)
                    });
                }
            }

            var rejected = new List<AuditLogModel>();
            using var cmd2 = conn.CreateCommand();
            cmd2.CommandText = "SELECT LogID, RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload, CreatedAt FROM Audit_Logs WHERE RunID = @runId AND Status = 'REJECTED' LIMIT 200";
            cmd2.Parameters.AddWithValue("@runId", runId);

            using (var reader2 = await cmd2.ExecuteReaderAsync())
            {
                while (await reader2.ReadAsync())
                {
                    rejected.Add(new AuditLogModel
                    {
                        LogID = reader2.GetInt32(0),
                        RunID = reader2.GetString(1),
                        EntityName = reader2.GetString(2),
                        SourceRecordID = reader2.IsDBNull(3) ? null : reader2.GetString(3),
                        Action = reader2.GetString(4),
                        Status = reader2.GetString(5),
                        Reason = reader2.IsDBNull(6) ? null : reader2.GetString(6),
                        Payload = reader2.IsDBNull(7) ? null : reader2.GetString(7),
                        CreatedAt = reader2.GetString(8)
                    });
                }
            }

            return new ReconciliationResponse
            {
                Run = run,
                Reports = reports,
                RejectedRecords = rejected
            };
        }

        public async Task<List<AuditLogModel>> GetAuditLogsAsync(string? entity, string? status, string? search, int limit)
        {
            var logs = new List<AuditLogModel>();
            using var conn = GetConnection();
            using var cmd = conn.CreateCommand();

            var query = "SELECT LogID, RunID, EntityName, SourceRecordID, Action, Status, Reason, Payload, CreatedAt FROM Audit_Logs WHERE 1=1";
            if (!string.IsNullOrEmpty(entity))
            {
                query += " AND EntityName = @entity";
                cmd.Parameters.AddWithValue("@entity", entity);
            }
            if (!string.IsNullOrEmpty(status))
            {
                query += " AND Status = @status";
                cmd.Parameters.AddWithValue("@status", status);
            }
            if (!string.IsNullOrEmpty(search))
            {
                query += " AND (SourceRecordID LIKE @search OR Reason LIKE @search OR Payload LIKE @search)";
                cmd.Parameters.AddWithValue("@search", $"%{search}%");
            }
            query += " ORDER BY LogID DESC LIMIT @limit";
            cmd.Parameters.AddWithValue("@limit", limit);

            cmd.CommandText = query;
            using var reader = await cmd.ExecuteReaderAsync();
            while (await reader.ReadAsync())
            {
                logs.Add(new AuditLogModel
                {
                    LogID = reader.GetInt32(0),
                    RunID = reader.GetString(1),
                    EntityName = reader.GetString(2),
                    SourceRecordID = reader.IsDBNull(3) ? null : reader.GetString(3),
                    Action = reader.GetString(4),
                    Status = reader.GetString(5),
                    Reason = reader.IsDBNull(6) ? null : reader.GetString(6),
                    Payload = reader.IsDBNull(7) ? null : reader.GetString(7),
                    CreatedAt = reader.GetString(8)
                });
            }
            return logs;
        }

        public async Task<SettingsModel> GetSettingsAsync()
        {
            var runs = await GetAllRunsAsync();
            var lastRunId = runs.FirstOrDefault()?.RunID ?? "NONE";
            return new SettingsModel
            {
                PiiMaskingEnabled = _globalPiiMasking,
                DatabaseType = "SQL Server / SQLite Emulated Engine",
                ConnectionStatus = "CONNECTED",
                LastMigrationRunID = lastRunId,
                TargetPlatform = "CoreBank v2.4 Enterprise Normalized Schema"
            };
        }

        public async Task<SettingsModel> UpdateSettingsAsync(SettingsModel settings)
        {
            _globalPiiMasking = settings.PiiMaskingEnabled;
            return await GetSettingsAsync();
        }
    }
}
