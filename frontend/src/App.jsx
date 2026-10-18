import React, { useState, useEffect } from 'react';
import OverviewPanel from './components/OverviewPanel';
import ScheduleTimeline from './components/ScheduleTimeline';
import FarmerSimulation from './components/FarmerSimulation';
import TransparentLedger from './components/TransparentLedger';

export default function App() {
  const [stats, setStats] = useState(null);
  const [farmers, setFarmers] = useState([]);
  const [schedule, setSchedule] = useState([]);
  const [logs, setLogs] = useState([]);
  const [integrityInfo, setIntegrityInfo] = useState(null);
  const [selectedFarmerId, setSelectedFarmerId] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [notification, setNotification] = useState(null);

  // Load all initial state
  const fetchAllData = async () => {
    try {
      const [statsRes, farmersRes, scheduleRes, logsRes] = await Promise.all([
        fetch('/stats'),
        fetch('/farmers'),
        fetch('/schedule'),
        fetch('/logs')
      ]);

      const statsData = await statsRes.json();
      const farmersData = await farmersRes.json();
      const scheduleData = await scheduleRes.json();
      const logsData = await logsRes.json();

      setStats(statsData);
      setFarmers(farmersData.data || []);
      setSchedule(scheduleData.data || []);
      setLogs(logsData.data || []);
      setIntegrityInfo(logsData.cryptographic_integrity);
    } catch (err) {
      console.error('Failed to fetch KulhWise data:', err);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  const showNotification = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 5000);
  };

  // Run KulhWise Algorithm
  const handleRunAlgorithm = async () => {
    setIsRunning(true);
    try {
      const res = await fetch('/schedule/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ available_canal_hours: 24.0 })
      });
      const data = await res.json();
      if (res.ok) {
        showNotification(
          `✨ KulhWise Algorithm executed! Fairness increased from ${data.before_fairness_score}% → ${data.after_fairness_score}% (+${data.improvement_percentage}%). Deprived tail farmers prioritized!`,
          'success'
        );
        await fetchAllData();
      } else {
        showNotification(data.detail || 'Failed to generate schedule', 'error');
      }
    } catch (err) {
      showNotification('Error communicating with backend server', 'error');
    } finally {
      setIsRunning(false);
    }
  };

  // Reset to initial unfair state
  const handleReset = async () => {
    try {
      const res = await fetch('/reset', { method: 'POST' });
      const data = await res.json();
      showNotification('↺ System reset to initial unfair baseline. Ready to demonstrate again!', 'info');
      await fetchAllData();
    } catch (err) {
      showNotification('Failed to reset database', 'error');
    }
  };

  // Submit farmer turn confirmation
  const handleConfirmTurn = async (payload) => {
    setIsSubmitting(true);
    try {
      const res = await fetch('/turn/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        showNotification(
          `📝 ${data.message} Verified block #${data.log_entry.id} added to SHA-256 chain.`,
          'success'
        );
        await fetchAllData();
      } else {
        showNotification(data.detail || 'Failed to confirm turn', 'error');
      }
    } catch (err) {
      showNotification('Error recording turn', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-16">
      
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-600 rounded-xl flex items-center justify-center text-white text-xl shadow-sm">
              💧
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-slate-900">KulhWise</h1>
                <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                  Prototype v1.0
                </span>
              </div>
              <p className="text-xs text-slate-500">Smart Water Rotation for Shared Rural Canals</p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="hidden sm:flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Canal Flow Status: <strong>Optimal</strong></span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-8">

        {/* Global Notification Banner */}
        {notification && (
          <div className={`p-4 rounded-xl text-sm font-medium flex items-center justify-between shadow-sm transition-all animate-in fade-in slide-in-from-top-2 ${
            notification.type === 'error'
              ? 'bg-rose-50 text-rose-800 border border-rose-200'
              : notification.type === 'info'
              ? 'bg-sky-50 text-sky-800 border border-sky-200'
              : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
          }`}>
            <div className="flex items-center gap-2">
              <span>{notification.type === 'error' ? '⚠️' : '✅'}</span>
              <span>{notification.msg}</span>
            </div>
            <button
              onClick={() => setNotification(null)}
              className="text-xs opacity-60 hover:opacity-100 font-bold ml-4"
            >
              ✕
            </button>
          </div>
        )}

        {/* 1. Overview Panel */}
        <OverviewPanel
          stats={stats}
          onRunAlgorithm={handleRunAlgorithm}
          onReset={handleReset}
          isRunning={isRunning}
        />

        {/* 2. Schedule Timeline */}
        <ScheduleTimeline
          schedule={schedule}
          onQuickConfirm={(farmerId) => {
            setSelectedFarmerId(farmerId);
            window.scrollTo({ top: document.body.scrollHeight / 2, behavior: 'smooth' });
          }}
        />

        {/* 3. Farmer Simulation Section */}
        <FarmerSimulation
          farmers={farmers}
          selectedFarmerId={selectedFarmerId}
          onSelectFarmer={(id) => setSelectedFarmerId(id)}
          onConfirmTurn={handleConfirmTurn}
          isSubmitting={isSubmitting}
        />

        {/* 4. Transparent Cryptographic Ledger */}
        <TransparentLedger
          logs={logs}
          integrityInfo={integrityInfo}
          onRefresh={fetchAllData}
        />

      </main>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-16 pt-8 border-t border-slate-200 text-center text-xs text-slate-400">
        <p>KulhWise – Built for 24-Hour Hackathon • Python (FastAPI) + SQLite + React + Tailwind CSS</p>
        <p className="mt-1">Empowering Himalayan "Kulh" and rural canal communities with algorithmic fairness and tamper-proof records.</p>
      </footer>

    </div>
  );
}
