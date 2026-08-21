import React, { useState, useEffect } from 'react';
import { Search, Filter, RefreshCw, FileText, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { apiUrl } from '../api';

export default function AuditTrailView() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [entityFilter, setEntityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchLogs();
  }, [entityFilter, statusFilter]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      let url = `/api/audit?limit=200`;
      if (entityFilter) url += `&entity=${entityFilter}`;
      if (statusFilter) url += `&status=${statusFilter}`;
      if (searchTerm) url += `&search=${encodeURIComponent(searchTerm)}`;

      const res = await fetch(apiUrl(url));
      const json = await res.json();
      setLogs(json);
    } catch (e) {
      console.error("Failed to fetch audit logs:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchLogs();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">System Audit Trail</h1>
          <p className="text-slate-400 text-xs mt-1">Immutable ledger recording every database insert, transformation update, and rejected record</p>
        </div>
        <button
          onClick={fetchLogs}
          className="px-3.5 py-2 bg-[#1C2541] hover:bg-[#2A3C56] text-slate-300 border border-[#2A3C56] rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Audit Trail
        </button>
      </div>

      {/* Search & Filter Toolbar */}
      <form onSubmit={handleSearchSubmit} className="fintech-card p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search Record ID, reason, or payload..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[#0B132B] border border-[#2A3C56] rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-[#48CAE4]"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            className="bg-[#0B132B] border border-[#2A3C56] rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[#48CAE4]"
          >
            <option value="">All Entities</option>
            <option value="Customer">Customer</option>
            <option value="Account">Account</option>
            <option value="Transaction">Transaction</option>
            <option value="Beneficiary">Beneficiary</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-[#0B132B] border border-[#2A3C56] rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[#48CAE4]"
          >
            <option value="">All Statuses</option>
            <option value="SUCCESS">SUCCESS</option>
            <option value="REJECTED">REJECTED</option>
          </select>

          <button
            type="submit"
            className="px-4 py-1.5 bg-[#48CAE4] hover:bg-[#5BC0BE] text-[#0B132B] font-semibold text-xs rounded-lg transition-all"
          >
            Search
          </button>
        </div>
      </form>

      {/* Audit Log Table */}
      <div className="fintech-card overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-slate-400 text-xs">Loading Audit Trail entries...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0B132B] border-b border-[#2A3C56] text-slate-400 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="p-4">Log ID</th>
                  <th className="p-4">Run ID</th>
                  <th className="p-4">Entity</th>
                  <th className="p-4">Record ID</th>
                  <th className="p-4">Action</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Audit Reason / Detail</th>
                  <th className="p-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2A3C56]/50">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="p-8 text-center text-slate-500">
                      No audit entries found matching query.
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.logID} className="hover:bg-slate-800/40 transition-colors">
                      <td className="p-4 font-mono text-slate-400">#{log.logID}</td>
                      <td className="p-4 font-mono text-white font-medium">{log.runID}</td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium text-[11px]">
                          {log.entityName}
                        </span>
                      </td>
                      <td className="p-4 font-mono text-[#48CAE4]">{log.sourceRecordID || 'N/A'}</td>
                      <td className="p-4 font-mono text-slate-300">{log.action}</td>
                      <td className="p-4">
                        {log.status === 'SUCCESS' ? (
                          <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[11px] font-semibold">
                            SUCCESS
                          </span>
                        ) : (
                          <span className="px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[11px] font-semibold">
                            REJECTED
                          </span>
                        )}
                      </td>
                      <td className="p-4 text-slate-300 max-w-sm">
                        <div>{log.reason}</div>
                        {log.payload && (
                          <div className="font-mono text-[10px] text-slate-400 mt-0.5 truncate">{log.payload}</div>
                        )}
                      </td>
                      <td className="p-4 font-mono text-slate-400 text-[11px]">{log.createdAt?.replace('T', ' ').slice(0, 19)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
