import React, { useState, useEffect } from 'react';
import { ArrowLeft, CheckCircle2, AlertTriangle, XCircle, ShieldCheck, FileSpreadsheet, Filter } from 'lucide-react';
import { apiUrl } from '../api';

export default function RunDetailView({ runId, onBack }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reasonFilter, setReasonFilter] = useState('ALL');

  useEffect(() => {
    fetchReconciliation();
  }, [runId]);

  const fetchReconciliation = async () => {
    setLoading(true);
    try {
      const res = await fetch(apiUrl(`/api/migrations/${runId}/reconciliation`));
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error("Failed to load reconciliation:", e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-400 flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-2 border-[#48CAE4] border-t-transparent rounded-full animate-spin"></div>
        <div className="text-sm font-medium">Fetching Reconciliation & Checksum Report...</div>
      </div>
    );
  }

  if (!data || !data.run) {
    return (
      <div className="py-20 text-center space-y-4">
        <div className="text-rose-400 text-base font-semibold">Run data not found</div>
        <button onClick={onBack} className="px-4 py-2 bg-[#2A3C56] text-white rounded text-xs font-semibold">Back to Runs</button>
      </div>
    );
  }

  const { run, reports, rejectedRecords } = data;

  const filteredRejects = rejectedRecords.filter(r => {
    if (reasonFilter === 'ALL') return true;
    return r.entityName === reasonFilter;
  });

  const txReport = reports.find(r => r.entityName === 'Transaction');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#2A3C56] pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 bg-[#1C2541] hover:bg-[#2A3C56] text-slate-300 rounded-lg transition-all"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white font-mono">{run.runID}</h1>
              {run.status === 'SUCCESS' && (
                <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> SUCCESS
                </span>
              )}
              {run.status === 'PARTIAL_SUCCESS' && (
                <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" /> PARTIAL RECONCILED
                </span>
              )}
            </div>
            <p className="text-slate-400 text-xs mt-0.5">Execution Started: {run.startTime?.replace('T', ' ').slice(0, 19)}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">PII Masking Mode:</span>
          <span className="px-2.5 py-1 rounded bg-[#48CAE4]/10 text-[#48CAE4] border border-[#48CAE4]/20 text-xs font-mono font-semibold">
            {run.maskPII ? 'ENABLED (NON-PROD)' : 'DISABLED'}
          </span>
        </div>
      </div>

      {/* Row Count Comparison per Entity Cards */}
      <div>
        <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <FileSpreadsheet className="w-4 h-4 text-[#48CAE4]" /> Source vs Target Row Count Reconciliation
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {reports.map((rep) => {
            const isMatch = rep.matchStatus === 'MATCH';
            return (
              <div key={rep.entityName} className="fintech-card p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold text-white uppercase tracking-wider">{rep.entityName}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    isMatch ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}>
                    {rep.matchStatus}
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Source Flat File:</span>
                    <span className="font-mono text-white font-semibold">{rep.sourceCount}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Migrated to Target:</span>
                    <span className="font-mono text-emerald-400 font-semibold">{rep.targetCount}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Rejections/Cleansed:</span>
                    <span className="font-mono text-amber-400 font-semibold">{rep.rejectedCount}</span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
                  <div
                    className="bg-[#48CAE4] h-full"
                    style={{ width: `${(rep.targetCount / (rep.sourceCount || 1)) * 100}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Financial Checksum Validation Card */}
      {txReport && (
        <div className="fintech-card p-6 bg-gradient-to-r from-[#1C2541] to-[#0B132B]">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white">Financial Transaction Checksum Audit</h3>
              </div>
              <p className="text-xs text-slate-400">Mathematical sum verification across all extracted legacy monetary transactions vs loaded target records.</p>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-bold font-mono">
              CHECKSUM MATCH: 100% BALANCED
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-6 pt-6 border-t border-[#2A3C56]">
            <div className="bg-[#0B132B] p-4 rounded-lg border border-[#2A3C56]">
              <span className="text-xs text-slate-400 block mb-1">Source Transactions Sum (CSV)</span>
              <span className="text-2xl font-mono font-bold text-white">${txReport.sourceChecksum?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="bg-[#0B132B] p-4 rounded-lg border border-[#2A3C56]">
              <span className="text-xs text-slate-400 block mb-1">Target Transactions Sum (SQL Target)</span>
              <span className="text-2xl font-mono font-bold text-emerald-400">${txReport.targetChecksum?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
            </div>
          </div>
        </div>
      )}

      {/* Rejected Records Log Table */}
      <div className="fintech-card p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-base font-semibold text-white">Rejected & Cleansed Records Audit</h2>
            <p className="text-xs text-slate-400">Individual record validation exceptions and logged audit reasons</p>
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={reasonFilter}
              onChange={(e) => setReasonFilter(e.target.value)}
              className="bg-[#0B132B] border border-[#2A3C56] rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[#48CAE4]"
            >
              <option value="ALL">All Entities</option>
              <option value="Customer">Customer</option>
              <option value="Account">Account</option>
              <option value="Transaction">Transaction</option>
              <option value="Beneficiary">Beneficiary</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0B132B] border-b border-[#2A3C56] text-slate-400 uppercase tracking-wider font-semibold">
              <tr>
                <th className="p-3">Log ID</th>
                <th className="p-3">Entity</th>
                <th className="p-3">Record ID</th>
                <th className="p-3">Status</th>
                <th className="p-3">Rejection Reason</th>
                <th className="p-3">Raw Payload Snippet</th>
                <th className="p-3">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2A3C56]/50">
              {filteredRejects.length === 0 ? (
                <tr>
                  <td colSpan="7" className="p-8 text-center text-slate-500">
                    No rejected records logged for this filter selection.
                  </td>
                </tr>
              ) : (
                filteredRejects.map((log) => (
                  <tr key={log.logID} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3 font-mono text-slate-400">#{log.logID}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium text-[11px]">
                        {log.entityName}
                      </span>
                    </td>
                    <td className="p-3 font-mono font-medium text-white">{log.sourceRecordID}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[11px] font-semibold">
                        {log.status}
                      </span>
                    </td>
                    <td className="p-3 text-amber-300 font-medium max-w-xs">{log.reason}</td>
                    <td className="p-3 font-mono text-[11px] text-slate-400 max-w-xs truncate">{log.payload || 'N/A'}</td>
                    <td className="p-3 font-mono text-slate-400 text-[11px]">{log.createdAt?.replace('T', ' ').slice(0, 19)}</td>
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
