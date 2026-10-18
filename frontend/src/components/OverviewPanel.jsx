import React from 'react';

export default function OverviewPanel({ stats, onRunAlgorithm, onReset, isRunning }) {
  const fairnessScore = stats?.current_fairness_score ?? 29.5;
  const initialScore = stats?.initial_fairness_score ?? 29.5;
  const isOptimized = fairnessScore > 75;

  // Determine color and status label
  const getScoreColor = (score) => {
    if (score >= 80) return { ring: 'text-emerald-500', bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', text: 'Fair & Balanced' };
    if (score >= 50) return { ring: 'text-amber-500', bg: 'bg-amber-50 text-amber-700 border-amber-200', text: 'Moderate Disparity' };
    return { ring: 'text-rose-500', bg: 'bg-rose-50 text-rose-700 border-rose-200', text: 'Severe Tail Deprivation' };
  };

  const scoreMeta = getScoreColor(fairnessScore);
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (fairnessScore / 100) * circumference;

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 mb-8">
      <div className="flex flex-col lg:flex-row items-center justify-between gap-6">
        
        {/* Left: Fairness Gauge */}
        <div className="flex items-center gap-6">
          <div className="relative w-28 h-28 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="56"
                cy="56"
                r="45"
                stroke="currentColor"
                strokeWidth="8"
                className="text-slate-100"
                fill="transparent"
              />
              <circle
                cx="56"
                cy="56"
                r="45"
                stroke="currentColor"
                strokeWidth="8"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                className={`transition-all duration-1000 ease-out ${scoreMeta.ring}`}
                fill="transparent"
              />
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className="text-2xl font-bold tracking-tight text-slate-800">
                {fairnessScore}%
              </span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
                Jain's Index
              </span>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-bold text-slate-900">System Fairness Score</h3>
              <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border ${scoreMeta.bg}`}>
                {scoreMeta.text}
              </span>
            </div>
            <p className="text-sm text-slate-500 max-w-md">
              {isOptimized 
                ? "KulhWise rotation algorithm is active! Water deficits at tail canal are compensated."
                : "Initial village baseline: Head-reach farmers have captured water while tail-end farmers are starving."}
            </p>
            <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
              <span>Baseline: <strong>{initialScore}%</strong></span>
              <span>•</span>
              <span className={isOptimized ? "text-emerald-600 font-bold" : ""}>
                Status: {isOptimized ? `+${(fairnessScore - initialScore).toFixed(1)}% Improvement` : "Requires Optimization"}
              </span>
            </div>
          </div>
        </div>

        {/* Middle: Key Metric Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full lg:w-auto">
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-center">
            <div className="text-xs font-medium text-slate-400 uppercase">Total Farmers</div>
            <div className="text-xl font-bold text-slate-800 mt-0.5">{stats?.total_farmers ?? 30}</div>
            <div className="text-[11px] text-slate-500">Upper / Mid / Tail</div>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-center">
            <div className="text-xs font-medium text-slate-400 uppercase">Distributed</div>
            <div className="text-xl font-bold text-sky-600 mt-0.5">{stats?.total_received_hours ?? 0} hrs</div>
            <div className="text-[11px] text-slate-500">Canal flow hours</div>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-center">
            <div className="text-xs font-medium text-slate-400 uppercase">Tail Deficit</div>
            <div className="text-xl font-bold text-rose-600 mt-0.5">{stats?.tail_deficit_hours ?? 0} hrs</div>
            <div className="text-[11px] text-rose-400">Starved tail fields</div>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-center">
            <div className="text-xs font-medium text-slate-400 uppercase">Ledger Status</div>
            <div className="text-xl font-bold text-emerald-600 mt-0.5">SHA-256</div>
            <div className="text-[11px] text-emerald-600 font-medium">✓ Cryptographic</div>
          </div>
        </div>

        {/* Right: Demo Action Buttons */}
        <div className="flex flex-col sm:flex-row lg:flex-col gap-2.5 w-full lg:w-auto">
          <button
            onClick={onRunAlgorithm}
            disabled={isRunning}
            className={`w-full px-5 py-3 rounded-xl font-semibold text-white shadow-md transition-all flex items-center justify-center gap-2 text-sm ${
              isRunning 
                ? 'bg-emerald-400 cursor-not-allowed' 
                : 'bg-emerald-600 hover:bg-emerald-700 active:scale-95 shadow-emerald-200'
            }`}
          >
            {isRunning ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <span>Optimizing Schedule...</span>
              </>
            ) : (
              <>
                <span>⚡ Run KulhWise Algorithm</span>
              </>
            )}
          </button>

          <button
            onClick={onReset}
            className="w-full px-4 py-2 rounded-xl text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 active:scale-95 transition-all text-center"
          >
            ↺ Reset to Unfair Baseline
          </button>
        </div>

      </div>
    </div>
  );
}
