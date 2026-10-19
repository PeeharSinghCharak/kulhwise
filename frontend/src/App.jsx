import React, { useState, useEffect, useMemo } from 'react';

export default function App() {
  const [systemState, setSystemState] = useState(null);
  const [selectedPlotId, setSelectedPlotId] = useState(24);
  const [isLoading, setIsLoading] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState(null);

  // Parameter sliders
  const [supplySlider, setSupplySlider] = useState(100);
  const [seepageSlider, setSeepageSlider] = useState(65);
  const [debtSlider, setDebtSlider] = useState(80);

  // Farmer Bot Simulator state
  const [botPlotId, setBotPlotId] = useState(14);
  const [botReportType, setBotReportType] = useState('LOW_OR_NO');
  const [botResult, setBotResult] = useState(null);

  // Ledger blocks
  const [ledgerBlocks, setLedgerBlocks] = useState([]);

  const loadState = async () => {
    try {
      const res = await fetch('/api/state');
      if (res.ok) {
        const json = await res.json();
        setSystemState(json.data);
        if (json.data.parameters) {
          setSupplySlider(json.data.parameters.main_canal_supply);
          setSeepageSlider(json.data.parameters.seepage_compensation_weight);
          setDebtSlider(json.data.parameters.water_debt_weight);
        }
      }
    } catch (e) {
      console.error('Failed to load state from API:', e);
    }
  };

  const loadLedger = async () => {
    try {
      const res = await fetch('/api/ledger');
      if (res.ok) {
        const json = await res.json();
        setLedgerBlocks(json.data || []);
      }
    } catch (e) {
      console.error('Failed to load ledger:', e);
    }
  };

  useEffect(() => {
    loadState();
    loadLedger();
  }, []);

  const showToast = (text, type = 'info') => {
    setFeedbackMsg({ text, type });
    setTimeout(() => setFeedbackMsg(null), 5000);
  };

  const handleReset = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/reset', { method: 'POST' });
      if (res.ok) {
        const json = await res.json();
        setSystemState(json.data);
        showToast('↺ System successfully reset to Static Week 1 baseline state.', 'info');
        loadLedger();
      }
    } catch (e) {
      showToast('Error resetting database.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSimulateChaos = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/simulate-week1-chaos', { method: 'POST' });
      if (res.ok) {
        const json = await res.json();
        setSystemState(json.data);
        showToast('⚠️ Disruption simulated: Head overdraw, tail shortages, and contradiction anomaly at Plot #14!', 'warning');
        loadLedger();
      }
    } catch (e) {
      showToast('Error simulating chaos.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunWeek2 = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/run-week2-scheduler', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          supply_percent: Number(supplySlider),
          seepage_weight: Number(seepageSlider),
          debt_weight: Number(debtSlider)
        })
      });
      if (res.ok) {
        const json = await res.json();
        setSystemState(json.data);
        showToast(`⚡ KulhWise Week 2 computed! Jain's Fairness Index reached ${json.data.metrics.jains_fairness_index.toFixed(4)}.`, 'success');
        loadLedger();
      }
    } catch (e) {
      showToast('Error running KulhWise scheduler.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitBotReport = async (targetPlot, targetReport) => {
    const pId = targetPlot !== undefined ? targetPlot : botPlotId;
    const rType = targetReport !== undefined ? targetReport : botReportType;
    setIsLoading(true);
    try {
      const res = await fetch('/api/bot-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plot_id: Number(pId), report_type: rType })
      });
      if (res.ok) {
        const json = await res.json();
        setBotResult(json.consensus);
        setSystemState(json.data);
        setSelectedPlotId(Number(pId));
        loadLedger();
        if (json.consensus.is_anomaly) {
          showToast(`🔍 Anomaly Flagged for Plot #${pId}: ${json.consensus.explanation}`, 'warning');
        } else {
          showToast(`Report recorded for Plot #${pId}: ${json.consensus.explanation}`, 'success');
        }
      }
    } catch (e) {
      showToast('Error recording report.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTamperTest = async () => {
    try {
      const res = await fetch('/api/tamper-test', { method: 'POST' });
      if (res.ok) {
        const json = await res.json();
        setSystemState(json.data);
        showToast('🚨 Tamper test executed! Block #5 modified. SHA-256 hash check broken!', 'error');
        loadLedger();
      }
    } catch (e) {}
  };

  const handleRepairLedger = async () => {
    try {
      const res = await fetch('/api/repair-ledger', { method: 'POST' });
      if (res.ok) {
        const json = await res.json();
        setSystemState(json.data);
        showToast('🛡️ Audit ledger restored to clean verified state.', 'success');
        loadLedger();
      }
    } catch (e) {}
  };

  const selectedPlot = useMemo(() => {
    if (!systemState || !systemState.plots) return null;
    return systemState.plots.find((p) => p.plot_id === Number(selectedPlotId)) || systemState.plots[0];
  }, [systemState, selectedPlotId]);

  if (!systemState) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-6 text-center text-slate-100">
        <div className="bg-slate-900 p-8 rounded-2xl border border-slate-800 max-w-md shadow-2xl">
          <div className="w-12 h-12 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <h2 className="text-xl font-bold">Connecting to KulhWise API...</h2>
          <p className="text-slate-400 text-sm mt-2">Loading 30-plot canal rotation model & ledger...</p>
        </div>
      </div>
    );
  }

  const metrics = systemState.metrics || {};
  const mode = systemState.mode || 'Static Week 1';
  const plots = systemState.plots || [];

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Delivered':
        return { bg: 'bg-emerald-950/80 border-emerald-500/40 text-emerald-400', icon: '✓', text: 'Delivered' };
      case 'Overdrawn':
        return { bg: 'bg-purple-950/80 border-purple-500/40 text-purple-400', icon: '▲', text: 'Overdrawn' };
      case 'Shortage':
        return { bg: 'bg-rose-950/80 border-rose-500/40 text-rose-400', icon: '▼', text: 'Shortage' };
      case 'Suspected Anomaly':
        return { bg: 'bg-amber-950/80 border-amber-500/40 text-amber-400', icon: '⚠', text: 'Suspected Anomaly' };
      case 'Compensated':
        return { bg: 'bg-cyan-950/80 border-cyan-500/40 text-cyan-400', icon: '★', text: 'Compensated' };
      default:
        return { bg: 'bg-slate-800 border-slate-600 text-slate-300', icon: '•', text: status };
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-16 font-sans">
      {feedbackMsg && (
        <div className={`fixed top-4 right-4 z-50 max-w-lg p-4 rounded-xl shadow-2xl border text-sm font-medium ${
          feedbackMsg.type === 'success' ? 'bg-emerald-900/90 border-emerald-500 text-emerald-100' :
          feedbackMsg.type === 'error' ? 'bg-rose-900/90 border-rose-500 text-rose-100' :
          feedbackMsg.type === 'warning' ? 'bg-amber-900/90 border-amber-500 text-amber-100' :
          'bg-cyan-900/90 border-cyan-500 text-cyan-100'
        }`}>
          <div className="flex items-start gap-3">
            <span className="text-xl">
              {feedbackMsg.type === 'success' ? '✓' : feedbackMsg.type === 'error' ? '🚨' : feedbackMsg.type === 'warning' ? '⚠️' : 'ℹ'}
            </span>
            <p className="flex-1">{feedbackMsg.text}</p>
            <button onClick={() => setFeedbackMsg(null)} className="text-slate-400 hover:text-white">&times;</button>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/90 sticky top-0 z-40 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-emerald-500 flex items-center justify-center text-xl shadow-lg shadow-cyan-950">
              💧
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-black text-white">KulhWise</h1>
                <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-900/80 text-cyan-300 font-semibold border border-cyan-700/60">
                  Digital Kohli
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Transparent Shared Canal Irrigation Scheduling & Accountability
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-xs font-bold px-2.5 py-1 rounded-md border ${
              mode === 'KulhWise Week 2' ? 'bg-emerald-950 border-emerald-500 text-emerald-300' :
              mode === 'Week 1 Chaos' ? 'bg-rose-950 border-rose-500 text-rose-300' :
              'bg-slate-800 border-slate-600 text-slate-300'
            }`}>
              ● {mode}
            </span>
            <div className="px-3 py-1 rounded-lg bg-cyan-950/60 border border-cyan-700/50 text-[11px] font-semibold text-cyan-300">
              ⚡ SIMULATION / ILLUSTRATIVE DATA
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 pt-6 space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 shadow-sm col-span-2 md:col-span-1">
            <div className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">Rotation Mode</div>
            <div className="text-base font-bold text-white mt-1 truncate">{mode}</div>
            <div className="text-[11px] text-cyan-400 mt-1 font-mono">
              {mode === 'KulhWise Week 2' ? 'Adaptive Need-Aware' : 'Rigid Timetable'}
            </div>
          </div>

          <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 shadow-sm">
            <div className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">Jain's Fairness</div>
            <div className="text-2xl font-black text-emerald-400 mt-1 font-mono">
              {metrics.jains_fairness_index ? metrics.jains_fairness_index.toFixed(4) : '0.8487'}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              {metrics.jains_fairness_index >= 0.98 ? '✨ Optimal Equity' : '⚠ Severe Tail Shortage'}
            </div>
          </div>

          <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 shadow-sm">
            <div className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">Head vs Tail Access</div>
            <div className="text-lg font-bold text-white mt-1">
              <span className="text-emerald-400">{metrics.head_satisfaction_percent || 100}%</span>
              <span className="text-slate-500 mx-1">vs</span>
              <span className={metrics.tail_satisfaction_percent > 70 ? 'text-emerald-400' : 'text-rose-400'}>
                {metrics.tail_satisfaction_percent || 36.2}%
              </span>
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Ratio: <strong className="text-cyan-300 font-mono">{metrics.tail_to_head_equity_ratio || 0.36}</strong>
            </div>
          </div>

          <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 shadow-sm">
            <div className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">Verified Water Debt</div>
            <div className="text-2xl font-black text-amber-400 mt-1 font-mono">
              {metrics.total_water_debt_minutes ?? 280}
              <span className="text-xs text-slate-400 font-normal ml-1">min</span>
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              {metrics.total_water_debt_minutes === 0 ? '✓ No pending debt' : 'Eligible for Week 2 credit'}
            </div>
          </div>

          <div className={`p-4 rounded-xl border shadow-sm ${
            metrics.ledger_intact ? 'bg-slate-900/80 border-slate-800' : 'bg-rose-950/80 border-rose-500'
          }`}>
            <div className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">SHA-256 Ledger</div>
            <div className={`text-sm font-black mt-1 flex items-center gap-1.5 ${
              metrics.ledger_intact ? 'text-emerald-400' : 'text-rose-300 animate-pulse'
            }`}>
              {metrics.ledger_intact ? '✓ INTACT & VERIFIED' : `🚨 TAMPER AT #${metrics.ledger_broken_at || 5}`}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5 truncate">
              {metrics.ledger_intact ? '30 Blocks cryptographically chained' : 'Signature mismatch!'}
            </div>
          </div>
        </div>

        {/* Simulation Controls & Parameters */}
        <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 shadow-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <span>⚙️</span> Simulation Controls & Scenarios
              </h2>
              <p className="text-xs text-slate-400">
                Switch between baseline static rotation, disruption, and KulhWise algorithm.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={handleReset}
                disabled={isLoading}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition"
              >
                ↺ Reset to Week 1
              </button>
              <button
                onClick={handleSimulateChaos}
                disabled={isLoading}
                className="px-4 py-2 rounded-xl bg-amber-950 hover:bg-amber-900 text-amber-200 text-xs font-bold border border-amber-600 transition"
              >
                ⚠️ Simulate Week 1 Chaos
              </button>
              <button
                onClick={handleRunWeek2}
                disabled={isLoading}
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 text-white text-xs font-black shadow-lg shadow-emerald-950 transition"
              >
                ⚡ Run KulhWise Week 2
              </button>
            </div>
          </div>

          {/* Sliders */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-3 border-t border-slate-800">
            <div className="space-y-1">
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-300">1. Main Canal Supply</span>
                <span className="font-mono text-cyan-400 font-bold">{supplySlider}%</span>
              </div>
              <input
                type="range"
                min="60"
                max="110"
                value={supplySlider}
                onChange={(e) => setSupplySlider(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg cursor-pointer accent-cyan-400"
              />
            </div>

            <div className="space-y-1">
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-300">2. Seepage Boost Weight</span>
                <span className="font-mono text-emerald-400 font-bold">{seepageSlider}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={seepageSlider}
                onChange={(e) => setSeepageSlider(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg cursor-pointer accent-emerald-400"
              />
            </div>

            <div className="space-y-1">
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-300">3. Debt Carry-Forward (β)</span>
                <span className="font-mono text-amber-400 font-bold">{debtSlider}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={debtSlider}
                onChange={(e) => setDebtSlider(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg cursor-pointer accent-amber-400"
              />
            </div>
          </div>
        </div>

        {/* 30-Plot Canal Map */}
        <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 shadow-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <span>🗺️</span> 30-Plot Canal Map
              </h2>
              <p className="text-xs text-slate-400">Head (#1) to Tail (#30). Click any plot to view full calculation.</p>
            </div>
            <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-cyan-400">Head (Intake)</span>
              <span className="text-slate-500">━━━━▶</span>
              <span className="text-slate-300">Middle</span>
              <span className="text-slate-500">━━━━▶</span>
              <span className="text-rose-400">Tail (Dead-end)</span>
            </div>
          </div>

          {/* Plots Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-5 md:grid-cols-10 gap-2">
            {plots.map((plot) => {
              const badge = getStatusBadge(plot.status);
              const isSelected = selectedPlotId === plot.plot_id;
              return (
                <div
                  key={plot.plot_id}
                  onClick={() => setSelectedPlotId(plot.plot_id)}
                  className={`p-2 rounded-xl cursor-pointer transition border text-left flex flex-col justify-between h-24 ${badge.bg} ${
                    isSelected ? 'ring-2 ring-cyan-400 scale-105 z-10 shadow-lg' : 'hover:border-slate-500'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <span className="text-xs font-black font-mono">#{plot.plot_id}</span>
                    <span className="text-[10px] font-bold">{badge.icon}</span>
                  </div>
                  <div>
                    <div className="text-[11px] font-bold text-slate-100 truncate">{plot.farmer_name}</div>
                    <div className="text-[10px] text-slate-400 truncate">{plot.crop}</div>
                  </div>
                  <div className="flex justify-between items-center text-[10px] border-t border-slate-700/40 pt-1 font-mono">
                    <span className="text-slate-300">{plot.scheduled_minutes}m</span>
                    <span className="font-bold">{badge.text}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Plot Inspector & Farmer Bot Simulator */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Plot Inspector */}
          <div className="lg:col-span-7 bg-slate-900/90 p-5 rounded-2xl border border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-[10px] uppercase tracking-wider text-cyan-400 font-bold">Selected Plot Inspector</span>
                <h3 className="text-lg font-black text-white">
                  Plot #{selectedPlot?.plot_id} — {selectedPlot?.farmer_name}
                </h3>
              </div>
              {selectedPlot && (
                <span className={`px-2.5 py-1 rounded-md text-xs font-bold border ${getStatusBadge(selectedPlot.status).bg}`}>
                  {selectedPlot.status}
                </span>
              )}
            </div>

            {selectedPlot && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold">Reach / Distance</span>
                    <strong className="text-white text-sm">{selectedPlot.reach}</strong>
                    <div className="text-slate-400 text-[11px] font-mono">{selectedPlot.distance_km} km</div>
                  </div>
                  <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold">Land Area</span>
                    <strong className="text-white text-sm">{selectedPlot.area_kanals} Kanals</strong>
                    <div className="text-slate-400 text-[11px]">~{(selectedPlot.area_kanals / 8).toFixed(1)} Acres</div>
                  </div>
                  <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold">Crop & Duty</span>
                    <strong className="text-white text-sm">{selectedPlot.crop}</strong>
                    <div className="text-cyan-300 text-[11px] font-mono">K_crop = {selectedPlot.crop_factor}</div>
                  </div>
                  <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold">Seepage Loss</span>
                    <strong className="text-amber-400 text-sm font-mono">{selectedPlot.estimated_seepage_loss}%</strong>
                    <div className="text-slate-400 text-[11px]">Unlined channel</div>
                  </div>
                </div>

                <div className="p-4 bg-slate-950/90 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex justify-between items-center text-xs border-b border-slate-800 pb-2">
                    <span className="font-bold text-slate-300 uppercase">Turn Calculation</span>
                    <span className="text-cyan-400 font-mono text-[11px]">Tᵢ = [Base × Seepage] + (β × Debt) − Penalty</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                    <div className="p-2 rounded bg-slate-900 border border-slate-800">
                      <span className="text-slate-400 text-[10px] block">Base Duration</span>
                      <strong className="text-white font-mono">{selectedPlot.base_minutes}m</strong>
                    </div>
                    <div className="p-2 rounded bg-slate-900 border border-slate-800">
                      <span className="text-slate-400 text-[10px] block">Carried Debt</span>
                      <strong className="text-amber-400 font-mono">+{selectedPlot.water_debt}m</strong>
                    </div>
                    <div className="p-2 rounded bg-slate-900 border border-slate-800">
                      <span className="text-slate-400 text-[10px] block">Overdraw Penalty</span>
                      <strong className="text-rose-400 font-mono">-{selectedPlot.overdraw_adjustment}m</strong>
                    </div>
                    <div className="p-2 rounded bg-cyan-950/80 border border-cyan-800">
                      <span className="text-cyan-300 text-[10px] block font-semibold">Scheduled Turn</span>
                      <strong className="text-cyan-200 font-mono text-base">{selectedPlot.scheduled_minutes}m</strong>
                    </div>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-1">Explanation</span>
                  <p className="text-slate-200 leading-relaxed">{selectedPlot.explanation}</p>
                </div>
              </div>
            )}
          </div>

          {/* Bot Simulator & Activity Feed */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 shadow-xl space-y-4">
              <div className="border-b border-slate-800 pb-2">
                <span className="text-[10px] uppercase tracking-wider text-emerald-400 font-bold">Farmer Simulator</span>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>📱</span> Bot Report Simulator
                </h3>
              </div>

              <div className="space-y-3">
                <select
                  value={botPlotId}
                  onChange={(e) => setBotPlotId(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-100 font-mono"
                >
                  {plots.map((p) => (
                    <option key={p.plot_id} value={p.plot_id}>
                      Plot #{p.plot_id}: {p.farmer_name} ({p.reach})
                    </option>
                  ))}
                </select>

                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => handleSubmitBotReport(botPlotId, 'FULL')}
                    disabled={isLoading}
                    className="py-2.5 px-3 bg-emerald-950 hover:bg-emerald-900 border border-emerald-600/70 text-emerald-200 rounded-xl text-xs font-bold"
                  >
                    ✓ Got Full Water
                  </button>
                  <button
                    onClick={() => handleSubmitBotReport(botPlotId, 'LOW_OR_NO')}
                    disabled={isLoading}
                    className="py-2.5 px-3 bg-rose-950 hover:bg-rose-900 border border-rose-600/70 text-rose-200 rounded-xl text-xs font-bold"
                  >
                    ▼ Low / No Water
                  </button>
                </div>

                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Presets:</span>
                  <button
                    onClick={() => {
                      setBotPlotId(14);
                      handleSubmitBotReport(14, 'LOW_OR_NO');
                    }}
                    className="w-full text-left px-2.5 py-1.5 rounded-lg bg-amber-950/60 text-amber-300 border border-amber-800/60 text-xs font-medium"
                  >
                    🧪 Contradiction (Plot #14 Low while #13 & #15 Full) → Anomaly!
                  </button>
                  <button
                    onClick={() => {
                      setBotPlotId(24);
                      handleSubmitBotReport(24, 'LOW_OR_NO');
                    }}
                    className="w-full text-left px-2.5 py-1.5 rounded-lg bg-cyan-950/60 text-cyan-300 border border-cyan-800/60 text-xs font-medium"
                  >
                    🧪 Contiguous Shortage (Tail #24) → Corroborated!
                  </button>
                </div>

                {botResult && (
                  <div className={`p-3 rounded-xl border text-xs ${
                    botResult.is_anomaly ? 'bg-amber-950 border-amber-500 text-amber-200' : 'bg-slate-950 border-slate-800 text-slate-300'
                  }`}>
                    <strong className="block mb-1">{botResult.is_anomaly ? '⚠ Anomaly Flagged' : '✓ Consensus Verified'}</strong>
                    <p className="text-[11px]">{botResult.explanation}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Activity Feed */}
            <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 shadow-xl space-y-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>🔔</span> Activity Feed
              </h3>
              <div className="max-h-48 overflow-y-auto space-y-2">
                {(systemState.activity_feed || []).map((act, i) => (
                  <div key={i} className="p-2 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                    <div className="flex justify-between text-[10px] text-slate-400 font-mono mb-0.5">
                      <span>{act.timestamp}</span>
                      <span className="font-bold text-cyan-300">{act.event_type}</span>
                    </div>
                    <p className="text-slate-300">{act.explanation}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Cryptographic Ledger */}
        <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 shadow-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <span>🛡️</span> Cryptographic Tamper-Evident Ledger (SHA-256)
              </h2>
              <p className="text-xs text-slate-400">Chained block verification detects post-hoc data tampering.</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleTamperTest}
                className="px-3.5 py-2 rounded-xl bg-rose-950 hover:bg-rose-900 text-rose-300 border border-rose-700 text-xs font-bold"
              >
                🚨 Simulate Tampering (Block #5)
              </button>
              <button
                onClick={handleRepairLedger}
                className="px-3.5 py-2 rounded-xl bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-700 text-xs font-bold"
              >
                🛡️ Restore Verified State
              </button>
            </div>
          </div>

          <div className="max-h-60 overflow-y-auto border border-slate-800 rounded-xl">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 sticky top-0 border-b border-slate-800">
                <tr>
                  <th className="py-2 px-3">Block #</th>
                  <th className="py-2 px-3">Plot / Farmer</th>
                  <th className="py-2 px-3">Allocated (m)</th>
                  <th className="py-2 px-3">Delivered (m)</th>
                  <th className="py-2 px-3">Event Type</th>
                  <th className="py-2 px-3">Current SHA-256 Hash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {ledgerBlocks.map((block) => (
                  <tr key={block.id || block.block_index} className="hover:bg-slate-800/40">
                    <td className="py-2 px-3 font-bold text-white">#{block.block_index}</td>
                    <td className="py-2 px-3 font-sans">{block.farmer_name} (Plot #{block.plot_id})</td>
                    <td className="py-2 px-3 text-cyan-300">{block.allocated_minutes}m</td>
                    <td className="py-2 px-3 text-emerald-300">{block.reported_minutes}m</td>
                    <td className="py-2 px-3">{block.event_type}</td>
                    <td className="py-2 px-3 text-[10px] text-slate-400 truncate max-w-xs">{block.current_hash?.slice(0, 16)}...</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
