using CoreBankingMigration.Api.Models;

namespace CoreBankingMigration.Api.Services
{
    public interface IMigrationService
    {
        Task<List<MigrationRunModel>> GetAllRunsAsync();
        Task<MigrationRunModel?> GetRunByIdAsync(string runId);
        Task<MigrationRunModel> TriggerRunAsync(MigrationRequest request);
        Task<ReconciliationResponse?> GetReconciliationReportAsync(string runId);
        Task<List<AuditLogModel>> GetAuditLogsAsync(string? entity, string? status, string? search, int limit);
        Task<SettingsModel> GetSettingsAsync();
        Task<SettingsModel> UpdateSettingsAsync(SettingsModel settings);
    }
}
