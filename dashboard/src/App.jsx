import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Database, FileText, Settings, Play, ShieldAlert, Activity, RefreshCw } from 'lucide-react';
import OverviewView from './components/OverviewView';
import RunsView from './components/RunsView';
import RunDetailView from './components/RunDetailView';
import AuditTrailView from './components/AuditTrailView';
import SettingsView from './components/SettingsView';
import TriggerRunModal from './components/TriggerRunModal';
import { apiUrl } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [runs, setRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRuns();
  }, []);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const res = await fetch(apiUrl('/api/migrations'));
      const json = await res.json();
      setRuns(json);
    } catch (e) {
      console.error("Failed to load migration runs:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleViewRunDetail = (runId) => {
    setSelectedRunId(runId);
    setActiveTab('run-detail');
  };

  return (
    <div className="min-h-screen bg-[#07111f] text-slate-100 flex flex-col md:flex-row" style={{ backgroundImage: 'radial-gradient(circle at top left, rgba(56,189,248,0.12), transparent 25%), radial-gradient(circle at bottom right, rgba(14,165,233,0.10), transparent 30%)' }}>
      {/* Sidebar Navigation */}
      <aside className="w-full md:w-72 bg-[#0f172a]/90 backdrop-blur-xl border-r border-slate-700/70 p-4 flex flex-col justify-between shrink-0 shadow-2xl shadow-slate-950/40">
        <div>
          {/* Brand Branding */}
          <div className="flex items-center gap-3 px-2 py-4 mb-6 border-b border-slate-700/70">
            <div className="p-2.5 bg-gradient-to-br from-cyan-400 to-sky-500 text-slate-950 rounded-xl shadow-lg shadow-cyan-500/20">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[13px] font-bold text-white tracking-[0.18em] uppercase leading-tight">CoreBank</div>
              <div className="text-[10px] text-cyan-300 font-medium tracking-[0.26em] uppercase mt-0.5">Migration Suite</div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-2">
            <button
              onClick={() => setActiveTab('overview')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-[12px] font-semibold tracking-wide transition-all ${
                activeTab === 'overview'
                  ? 'bg-gradient-to-r from-cyan-400 to-sky-500 text-slate-950 shadow-lg shadow-cyan-500/20'
                  : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" /> Overview
            </button>

            <button
              onClick={() => setActiveTab('runs')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-[12px] font-semibold tracking-wide transition-all ${
                activeTab === 'runs' || activeTab === 'run-detail'
                  ? 'bg-gradient-to-r from-cyan-400 to-sky-500 text-slate-950 shadow-lg shadow-cyan-500/20'
                  : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
              }`}
            >
              <Database className="w-4 h-4" /> Migration Runs
            </button>

            <button
              onClick={() => setActiveTab('audit')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-[12px] font-semibold tracking-wide transition-all ${
                activeTab === 'audit'
                  ? 'bg-gradient-to-r from-cyan-400 to-sky-500 text-slate-950 shadow-lg shadow-cyan-500/20'
                  : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
              }`}
            >
              <FileText className="w-4 h-4" /> Audit Log Trail
            </button>

            <button
              onClick={() => setActiveTab('settings')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-[12px] font-semibold tracking-wide transition-all ${
                activeTab === 'settings'
                  ? 'bg-gradient-to-r from-cyan-400 to-sky-500 text-slate-950 shadow-lg shadow-cyan-500/20'
                  : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
              }`}
            >
              <Settings className="w-4 h-4" /> Settings
            </button>
          </nav>
        </div>

        {/* Quick Execution Box */}
        <div className="pt-4 border-t border-slate-700/70 mt-6">
          <div className="p-3 bg-slate-900/80 rounded-2xl border border-slate-700/80 mb-3">
            <span className="text-[10px] text-slate-400 font-semibold uppercase block mb-1.5 tracking-[0.22em]">Active database</span>
            <span className="text-xs text-emerald-400 font-mono font-medium flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> SQL / SQLite Sync
            </span>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="w-full py-2.5 bg-gradient-to-r from-cyan-500/15 to-sky-500/10 hover:from-cyan-500/20 hover:to-sky-500/15 text-cyan-300 border border-cyan-400/30 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/10"
          >
            <Play className="w-3.5 h-3.5 fill-current" /> Trigger New Run
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto max-w-full">
        <div className="max-w-7xl mx-auto">
          <header className="mb-6 flex flex-col gap-4 border-b border-slate-700/70 pb-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-[10px] font-medium tracking-[0.28em] text-cyan-300 uppercase">Operations control center</p>
              <h1 className="mt-2 text-2xl font-semibold text-white tracking-tight">Client Migration Dashboard</h1>
            </div>

            <div className="flex items-center gap-3 self-start sm:self-auto">
              <div className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.22em] text-cyan-300">
                live status
              </div>
              <div className="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1.5 text-[11px] text-emerald-300">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                System online
              </div>
            </div>
          </header>

          {activeTab === 'overview' && (
            <OverviewView
              runs={runs}
              onTriggerRun={() => setIsModalOpen(true)}
              onViewRunDetail={handleViewRunDetail}
              onNavigate={setActiveTab}
            />
          )}

          {activeTab === 'runs' && (
            <RunsView
              runs={runs}
              onTriggerRun={() => setIsModalOpen(true)}
              onViewRunDetail={handleViewRunDetail}
              onRefresh={fetchRuns}
            />
          )}

          {activeTab === 'run-detail' && (
            <RunDetailView
              runId={selectedRunId}
              onBack={() => setActiveTab('runs')}
            />
          )}

          {activeTab === 'audit' && (
            <AuditTrailView />
          )}

          {activeTab === 'settings' && (
            <SettingsView />
          )}
        </div>
      </main>

      {/* Trigger New Run Modal */}
      <TriggerRunModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={fetchRuns}
      />
    </div>
  );
}
