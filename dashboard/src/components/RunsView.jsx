import React, { useState } from 'react';
import { Play, CheckCircle2, AlertTriangle, XCircle, Search, RefreshCw, Eye } from 'lucide-react';

export default function RunsView({ runs, onTriggerRun, onViewRunDetail, onRefresh }) {
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredRuns = runs.filter(r => {
    const matchesStatus = filterStatus === 'ALL' || r.status === filterStatus;
    const matchesSearch = r.runID.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          (r.triggeredBy && r.triggeredBy.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Migration Runs Execution Log</h1>
          <p className="text-slate-400 text-xs mt-1">Audit log of all pipeline extractions, transformations, and reconciliation runs</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={onRefresh}
            className="px-3.5 py-2 bg-[#1C2541] hover:bg-[#2A3C56] text-slate-300 border border-[#2A3C56] rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
          <button
            onClick={onTriggerRun}
            className="px-4 py-2 bg-[#48CAE4] hover:bg-[#5BC0BE] text-[#0B132B] font-semibold text-xs rounded-lg transition-all flex items-center gap-1.5 shadow-md shadow-[#48CAE4]/10"
          >
            <Play className="w-3.5 h-3.5 fill-current" /> Trigger New Run
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="fintech-card p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search Run ID or trigger source..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[#0B132B] border border-[#2A3C56] rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-[#48CAE4]"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto">
          {['ALL', 'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED'].map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 ${
                filterStatus === status
                  ? 'bg-[#48CAE4] text-[#0B132B] font-semibold'
                  : 'bg-[#0B132B] text-slate-400 hover:text-white border border-[#2A3C56]'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Runs Table */}
      <div className="fintech-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0B132B] border-b border-[#2A3C56] text-slate-400 uppercase tracking-wider font-semibold">
              <tr>
                <th className="p-4">Run ID</th>
                <th className="p-4">Status</th>
                <th className="p-4">PII Mode</th>
                <th className="p-4">Source Count</th>
                <th className="p-4">Migrated</th>
                <th className="p-4">Rejected</th>
                <th className="p-4">Triggered By</th>
                <th className="p-4">Start Time</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2A3C56]/50">
              {filteredRuns.length === 0 ? (
                <tr>
                  <td colSpan="9" className="p-8 text-center text-slate-500">
                    No migration runs found matching criteria.
                  </td>
                </tr>
              ) : (
                filteredRuns.map((r) => (
                  <tr key={r.runID} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-4 font-mono font-medium text-white">{r.runID}</td>
                    <td className="p-4">
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
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-mono ${
                        r.maskPII ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {r.maskPII ? 'MASKED' : 'UNMASKED'}
                      </span>
                    </td>
                    <td className="p-4 font-mono text-slate-300">{r.totalSourceRecords}</td>
                    <td className="p-4 font-mono text-emerald-400 font-medium">{r.totalMigratedRecords}</td>
                    <td className="p-4 font-mono text-amber-400 font-medium">{r.totalRejectedRecords}</td>
                    <td className="p-4 text-slate-400">{r.triggeredBy}</td>
                    <td className="p-4 font-mono text-slate-400 text-[11px]">{r.startTime?.replace('T', ' ').slice(0, 19)}</td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => onViewRunDetail(r.runID)}
                        className="px-3 py-1.5 bg-[#48CAE4]/10 hover:bg-[#48CAE4]/20 text-[#48CAE4] border border-[#48CAE4]/30 rounded font-medium transition-all flex items-center gap-1 ml-auto"
                      >
                        <Eye className="w-3.5 h-3.5" /> Reconciliation
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
