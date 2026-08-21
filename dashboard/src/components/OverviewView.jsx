import React from 'react';
import { Play, Database, CheckCircle2, AlertTriangle, XCircle, ArrowUpRight, Activity } from 'lucide-react';

export default function OverviewView({ runs, onTriggerRun, onViewRunDetail, onNavigate }) {
  const totalRuns = runs.length;
  const successfulRuns = runs.filter(r => r.status === 'SUCCESS' || r.status === 'PARTIAL_SUCCESS').length;
  const successRate = totalRuns > 0 ? Math.round((successfulRuns / totalRuns) * 100) : 100;
  
  const totalMigrated = runs.reduce((acc, r) => acc + (r.totalMigratedRecords || 0), 0);
  const totalRejected = runs.reduce((acc, r) => acc + (r.totalRejectedRecords || 0), 0);

  const recentRuns = runs.slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-[#1C2541] to-[#0B132B] p-6 rounded-xl border border-[#2A3C56]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#48CAE4]/10 text-[#48CAE4] border border-[#48CAE4]/20 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#48CAE4] animate-pulse"></span>
              Enterprise Pipeline v2.4
            </span>
            <span className="text-xs text-slate-400">Target: CoreBank Normalized Platform</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Data Migration Control Center</h1>
          <p className="text-slate-400 text-sm mt-1">Orchestrating legacy provider extraction, T-SQL procedure loads, and checksum reconciliation.</p>
        </div>
        <button
          onClick={onTriggerRun}
          className="px-5 py-2.5 bg-[#48CAE4] hover:bg-[#5BC0BE] text-[#0B132B] font-semibold text-sm rounded-lg shadow-lg shadow-[#48CAE4]/10 transition-all flex items-center justify-center gap-2 shrink-0"
        >
          <Play className="w-4 h-4 fill-current" />
          Trigger Migration Run
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="fintech-card p-5">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Pipeline Runs</span>
            <Database className="w-5 h-5 text-[#48CAE4]" />
          </div>
          <div className="text-3xl font-bold text-white">{totalRuns}</div>
          <div className="text-xs text-slate-400 mt-2 flex items-center gap-1">
            <span className="text-emerald-400 font-medium">100% Automated</span> execution
          </div>
        </div>

        <div className="fintech-card p-5">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Success Rate</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="text-3xl font-bold text-white">{successRate}%</div>
          <div className="text-xs text-slate-400 mt-2 flex items-center gap-1">
            <span className="text-[#48CAE4] font-medium">{successfulRuns} / {totalRuns}</span> runs completed
          </div>
        </div>

        <div className="fintech-card p-5">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Records Migrated</span>
            <Activity className="w-5 h-5 text-[#48CAE4]" />
          </div>
          <div className="text-3xl font-bold text-white">{totalMigrated.toLocaleString()}</div>
          <div className="text-xs text-emerald-400 mt-2 font-medium">
            Normalized to target schema
          </div>
        </div>

        <div className="fintech-card p-5">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Rejected Records</span>
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          </div>
          <div className="text-3xl font-bold text-amber-400">{totalRejected.toLocaleString()}</div>
          <div className="text-xs text-slate-400 mt-2">
            Logged with audit reasons
          </div>
        </div>
      </div>

      {/* Migration Volume Trend & Status Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 fintech-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-white">Migrated Volume vs Rejections</h2>
              <p className="text-xs text-slate-400">Historical performance across recent migration runs</p>
            </div>
            <span className="text-xs text-[#48CAE4] font-medium flex items-center gap-1">
              Live DB Telemetry
            </span>
          </div>

          {/* Custom SVG Volume Bar Visualization */}
          <div className="h-48 flex items-end justify-between gap-3 pt-6 pb-2 border-b border-[#2A3C56]">
            {runs.length === 0 ? (
              <div className="w-full text-center py-16 text-slate-500 text-sm">No migration runs recorded yet.</div>
            ) : (
              runs.slice(0, 8).reverse().map((run, idx) => {
                const total = (run.totalMigratedRecords || 0) + (run.totalRejectedRecords || 0) || 1;
                const migratedH = Math.min(100, Math.max(15, ((run.totalMigratedRecords || 0) / total) * 100));
                const rejectedH = Math.min(40, ((run.totalRejectedRecords || 0) / total) * 100);

                return (
                  <div key={run.runID || idx} className="flex-1 flex flex-col items-center gap-1 group relative">
                    {/* Tooltip */}
                    <div className="absolute -top-12 bg-slate-900 border border-[#2A3C56] text-xs rounded px-2.5 py-1 text-slate-200 hidden group-hover:block z-10 whitespace-nowrap shadow-xl">
                      <div className="font-mono font-bold text-[#48CAE4]">{run.runID}</div>
                      <div>Migrated: {run.totalMigratedRecords} | Rejected: {run.totalRejectedRecords}</div>
                    </div>

                    <div className="w-full bg-slate-800/50 rounded-t flex flex-col justify-end overflow-hidden h-36 border border-slate-700/50">
                      <div style={{ height: `${rejectedH}%` }} className="w-full bg-amber-500/80"></div>
                      <div style={{ height: `${migratedH}%` }} className="w-full bg-[#48CAE4] transition-all group-hover:bg-[#5BC0BE]"></div>
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 truncate w-full text-center">{run.runID?.split('-').pop()}</span>
                  </div>
                );
              })
            )}
          </div>
          <div className="flex items-center justify-between text-xs text-slate-400 pt-3">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-[#48CAE4]"></span> Target Migrated</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-amber-500"></span> Rejected / Cleansed</span>
            </div>
            <span>Auto-refreshing</span>
          </div>
        </div>

        {/* System Architecture & Status */}
        <div className="fintech-card p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-semibold text-white mb-1">Engine Health & Configuration</h2>
            <p className="text-xs text-slate-400 mb-4">Pipeline status and active validation flags</p>

            <div className="space-y-3">
              <div className="p-3 bg-[#0B132B] rounded-lg border border-[#2A3C56] flex items-center justify-between">
                <span className="text-xs text-slate-300 font-medium">Database Layer</span>
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">T-SQL Stored Procs</span>
              </div>
              <div className="p-3 bg-[#0B132B] rounded-lg border border-[#2A3C56] flex items-center justify-between">
                <span className="text-xs text-slate-300 font-medium">PII Masking Status</span>
                <span className="text-xs px-2 py-0.5 rounded bg-[#48CAE4]/10 text-[#48CAE4] border border-[#48CAE4]/20 font-mono">ACTIVE (Non-Prod)</span>
              </div>
              <div className="p-3 bg-[#0B132B] rounded-lg border border-[#2A3C56] flex items-center justify-between">
                <span className="text-xs text-slate-300 font-medium">Idempotency Lock</span>
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">ENABLED (UPSERT)</span>
              </div>
              <div className="p-3 bg-[#0B132B] rounded-lg border border-[#2A3C56] flex items-center justify-between">
                <span className="text-xs text-slate-300 font-medium">Checksum Verification</span>
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">AUTO-RECONCILE</span>
              </div>
            </div>
          </div>

          <button
            onClick={() => onNavigate('runs')}
            className="w-full mt-4 py-2 text-xs font-semibold text-[#48CAE4] hover:text-[#5BC0BE] border border-[#48CAE4]/30 hover:border-[#48CAE4] rounded-lg transition-all flex items-center justify-center gap-1"
          >
            View All Migration Runs <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Recent Migration Runs Table */}
      <div className="fintech-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-white">Recent Migration Runs</h2>
            <p className="text-xs text-slate-400">Latest execution batches and reconciliation outcomes</p>
          </div>
          <button
            onClick={() => onNavigate('runs')}
            className="text-xs text-[#48CAE4] hover:underline font-medium"
          >
            View Full List
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#2A3C56] text-slate-400 uppercase tracking-wider font-semibold">
                <th className="pb-3">Run ID</th>
                <th className="pb-3">Status</th>
                <th className="pb-3">Source Records</th>
                <th className="pb-3">Migrated</th>
                <th className="pb-3">Rejected</th>
                <th className="pb-3">Triggered By</th>
                <th className="pb-3">Timestamp</th>
                <th className="pb-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2A3C56]/50">
              {recentRuns.map((r) => (
                <tr key={r.runID} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 font-mono font-medium text-white">{r.runID}</td>
                  <td className="py-3.5">
                    {r.status === 'SUCCESS' && (
                      <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium flex items-center gap-1 w-fit">
                        <CheckCircle2 className="w-3 h-3" /> SUCCESS
                      </span>
                    )}
                    {r.status === 'PARTIAL_SUCCESS' && (
                      <span className="px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium flex items-center gap-1 w-fit">
                        <AlertTriangle className="w-3 h-3" /> PARTIAL SUCCESS
                      </span>
                    )}
                    {r.status === 'FAILED' && (
                      <span className="px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-medium flex items-center gap-1 w-fit">
                        <XCircle className="w-3 h-3" /> FAILED
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 font-mono text-slate-300">{r.totalSourceRecords}</td>
                  <td className="py-3.5 font-mono text-emerald-400 font-medium">{r.totalMigratedRecords}</td>
                  <td className="py-3.5 font-mono text-amber-400 font-medium">{r.totalRejectedRecords}</td>
                  <td className="py-3.5 text-slate-400">{r.triggeredBy}</td>
                  <td className="py-3.5 text-slate-400 font-mono text-[11px]">{r.startTime?.replace('T', ' ').slice(0, 19)}</td>
                  <td className="py-3.5 text-right">
                    <button
                      onClick={() => onViewRunDetail(r.runID)}
                      className="px-3 py-1 bg-[#2A3C56] hover:bg-[#3A506B] text-white rounded font-medium transition-all"
                    >
                      Reconciliation
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
