using Microsoft.AspNetCore.Mvc;
using CoreBankingMigration.Api.Models;
using CoreBankingMigration.Api.Services;

namespace CoreBankingMigration.Api.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class SettingsController : ControllerBase
    {
        private readonly IMigrationService _migrationService;

        public SettingsController(IMigrationService migrationService)
        {
            _migrationService = migrationService;
        }

        [HttpGet]
        public async Task<IActionResult> GetSettings()
        {
            var settings = await _migrationService.GetSettingsAsync();
            return Ok(settings);
        }

        [HttpPost]
        public async Task<IActionResult> UpdateSettings([FromBody] SettingsModel updated)
        {
            var settings = await _migrationService.UpdateSettingsAsync(updated);
            return Ok(settings);
        }
    }
}
