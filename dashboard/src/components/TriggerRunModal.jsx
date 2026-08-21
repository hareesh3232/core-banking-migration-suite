import React, { useState } from 'react';
import { X, Play, Shield, Sliders } from 'lucide-react';

export default function TriggerRunModal({ isOpen, onClose, onSuccess }) {
  const [rows, setRows] = useState(1000);
  const [errorRate, setErrorRate] = useState(0.05);
  const [maskPii, setMaskPii] = useState(true);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('/api/migrations/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rows: parseInt(rows, 10),
          errorRate: parseFloat(errorRate),
          maskPII: maskPii,
          triggeredBy: 'WEB_DASHBOARD'
        })
      });
      if (res.ok) {
        onSuccess();
        onClose();
      }
    } catch (e) {
      console.error("Failed to trigger run:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-[#1C2541] border border-[#2A3C56] rounded-xl w-full max-w-md p-6 space-y-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-[#2A3C56] pb-3">
          <div className="flex items-center gap-2">
            <Play className="w-4 h-4 text-[#48CAE4] fill-current" />
            <h2 className="text-base font-bold text-white">Trigger New Data Migration Run</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 text-xs">
          <div>
            <div className="flex justify-between mb-1 text-slate-300 font-medium">
              <span>Synthetic Legacy Base Records</span>
              <span className="font-mono text-[#48CAE4] font-bold">{rows.toLocaleString()} Rows</span>
            </div>
            <input
              type="range"
              min="100"
              max="5000"
              step="100"
              value={rows}
              onChange={(e) => setRows(e.target.value)}
              className="w-full accent-[#48CAE4] cursor-pointer"
            />
            <p className="text-[11px] text-slate-500 mt-1">Generates customers.csv, accounts.csv, transactions.csv, beneficiaries.csv</p>
          </div>

          <div>
            <div className="flex justify-between mb-1 text-slate-300 font-medium">
              <span>Dirty Data Anomaly Rate</span>
              <span className="font-mono text-amber-400 font-bold">{(errorRate * 100).toFixed(1)}%</span>
            </div>
            <input
              type="range"
              min="0.01"
              max="0.20"
              step="0.01"
              value={errorRate}
              onChange={(e) => setErrorRate(e.target.value)}
              className="w-full accent-amber-400 cursor-pointer"
            />
            <p className="text-[11px] text-slate-500 mt-1">Injects date formatting mismatches, orphaned FKs, null SSNs, currency strings</p>
          </div>

          <div className="p-3 bg-[#0B132B] rounded-lg border border-[#2A3C56] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-[#48CAE4]" />
              <div>
                <span className="text-white font-medium block">PII Masking Mode</span>
                <span className="text-[10px] text-slate-400">Mask SSNs and Account Numbers</span>
              </div>
            </div>
            <input
              type="checkbox"
              checked={maskPii}
              onChange={(e) => setMaskPii(e.target.checked)}
              className="w-4 h-4 accent-[#48CAE4] cursor-pointer"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#2A3C56]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-[#0B132B] hover:bg-[#2A3C56] text-slate-300 font-semibold rounded-lg transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 bg-[#48CAE4] hover:bg-[#5BC0BE] text-[#0B132B] font-bold rounded-lg shadow-lg shadow-[#48CAE4]/10 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>Executing Migration Pipeline...</>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" /> Execute Migration
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
