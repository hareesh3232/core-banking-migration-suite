using Microsoft.AspNetCore.Mvc;
using CoreBankingMigration.Api.Services;

namespace CoreBankingMigration.Api.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class AuditController : ControllerBase
    {
        private readonly IMigrationService _migrationService;

        public AuditController(IMigrationService migrationService)
        {
            _migrationService = migrationService;
        }

        [HttpGet]
        public async Task<IActionResult> GetAuditLogs([FromQuery] string? entity, [FromQuery] string? status, [FromQuery] string? search, [FromQuery] int limit = 100)
        {
            var logs = await _migrationService.GetAuditLogsAsync(entity, status, search, limit);
            return Ok(logs);
        }
    }
}
