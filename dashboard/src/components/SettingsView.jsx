import React, { useState, useEffect } from 'react';
import { Shield, Database, Lock, Server, CheckCircle2, Save } from 'lucide-react';

export default function SettingsView() {
  const [settings, setSettings] = useState({
    piiMaskingEnabled: true,
    databaseType: 'SQL Server / SQLite Engine',
    connectionStatus: 'CONNECTED',
    targetPlatform: 'CoreBank v2.4 Enterprise Normalized Schema'
  });
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await fetch('/api/settings');
      const json = await res.json();
      setSettings(json);
    } catch (e) {
      console.error("Failed to load settings:", e);
    }
  };

  const handleSave = async (newPiiState) => {
    setSaving(true);
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...settings, piiMaskingEnabled: newPiiState })
      });
      const json = await res.json();
      setSettings(json);
      setToast('Configuration updated successfully!');
      setTimeout(() => setToast(null), 3000);
    } catch (e) {
      console.error("Failed to update settings:", e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">System Settings & Compliance</h1>
        <p className="text-slate-400 text-xs mt-1">Configure security compliance flags, target database parameters, and PII masking behavior</p>
      </div>

      {toast && (
        <div className="p-3 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-lg text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> {toast}
        </div>
      )}

      {/* PII Masking Card */}
      <div className="fintech-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#48CAE4]/10 text-[#48CAE4] rounded-lg">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">PII Data Masking Mode (Non-Prod Compliance)</h2>
              <p className="text-xs text-slate-400 mt-0.5">Automatically mask SSNs (XXX-XX-1234) and Account Numbers (****5678) during extraction & target loading.</p>
            </div>
          </div>

          <label className="relative inline-flex items-center cursor-pointer shrink-0">
            <input
              type="checkbox"
              checked={settings.piiMaskingEnabled}
              onChange={(e) => handleSave(e.target.checked)}
              disabled={saving}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#48CAE4]"></div>
          </label>
        </div>
        <div className="text-xs text-slate-400 bg-[#0B132B] p-3 rounded border border-[#2A3C56]">
          Status: <span className="font-mono text-[#48CAE4] font-semibold">{settings.piiMaskingEnabled ? 'MASKING ACTIVE' : 'UNMASKED (PROD DIRECT)'}</span>
        </div>
      </div>

      {/* Database Connection Info */}
      <div className="fintech-card p-6 space-y-4">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-[#48CAE4]/10 text-[#48CAE4] rounded-lg">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Database Engine Telemetry</h2>
            <p className="text-xs text-slate-400">SQL Server & T-SQL procedure connection settings</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-4 bg-[#0B132B] rounded-lg border border-[#2A3C56]">
            <span className="text-slate-400 block mb-1">Target Engine</span>
            <span className="font-mono text-white font-semibold">{settings.databaseType}</span>
          </div>
          <div className="p-4 bg-[#0B132B] rounded-lg border border-[#2A3C56]">
            <span className="text-slate-400 block mb-1">Connection State</span>
            <span className="font-mono text-emerald-400 font-semibold flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> {settings.connectionStatus}
            </span>
          </div>
          <div className="p-4 bg-[#0B132B] rounded-lg border border-[#2A3C56]">
            <span className="text-slate-400 block mb-1">Target Platform Schema</span>
            <span className="font-mono text-slate-300 font-semibold">{settings.targetPlatform}</span>
          </div>
          <div className="p-4 bg-[#0B132B] rounded-lg border border-[#2A3C56]">
            <span className="text-slate-400 block mb-1">DB Connection String (Masked)</span>
            <span className="font-mono text-slate-400">Server=localhost,1433;Database=CoreBank;User=sa;Password=••••••••</span>
          </div>
        </div>
      </div>
    </div>
  );
}
