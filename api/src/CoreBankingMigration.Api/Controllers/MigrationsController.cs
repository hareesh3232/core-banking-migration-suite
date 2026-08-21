using Microsoft.AspNetCore.Mvc;
using CoreBankingMigration.Api.Models;
using CoreBankingMigration.Api.Services;

namespace CoreBankingMigration.Api.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class MigrationsController : ControllerBase
    {
        private readonly IMigrationService _migrationService;

        public MigrationsController(IMigrationService migrationService)
        {
            _migrationService = migrationService;
        }

        [HttpGet]
        public async Task<IActionResult> GetPastRuns()
        {
            var runs = await _migrationService.GetAllRunsAsync();
            return Ok(runs);
        }

        [HttpPost("run")]
        public async Task<IActionResult> TriggerMigrationRun([FromBody] MigrationRequest request)
        {
            var run = await _migrationService.TriggerRunAsync(request);
            return Accepted($"/api/migrations/{run.RunID}/status", run);
        }

        [HttpGet("{runId}/status")]
        public async Task<IActionResult> GetRunStatus(string runId)
        {
            var status = await _migrationService.GetRunByIdAsync(runId);
            if (status == null) return NotFound(new { error = $"Run {runId} not found" });
            return Ok(status);
        }

        [HttpGet("{runId}/reconciliation")]
        public async Task<IActionResult> GetReconciliationReport(string runId)
        {
            var report = await _migrationService.GetReconciliationReportAsync(runId);
            if (report == null) return NotFound(new { error = $"Reconciliation for {runId} not found" });
            return Ok(report);
        }
    }
}
