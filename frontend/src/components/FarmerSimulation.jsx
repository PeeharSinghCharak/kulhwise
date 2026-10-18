import React, { useState, useEffect } from 'react';

export default function FarmerSimulation({ farmers, selectedFarmerId, onSelectFarmer, onConfirmTurn, isSubmitting }) {
  const [selectedId, setSelectedId] = useState(selectedFarmerId || (farmers[0]?.id ?? ''));
  const [status, setStatus] = useState('FULL');
  const [partialHours, setPartialHours] = useState(1.5);
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (selectedFarmerId) {
      setSelectedId(selectedFarmerId);
    } else if (farmers.length > 0 && !selectedId) {
      setSelectedId(farmers[0].id);
    }
  }, [selectedFarmerId, farmers]);

  const currentFarmer = farmers.find(f => String(f.id) === String(selectedId)) || farmers[0];

  const handleFarmerChange = (e) => {
    const id = e.target.value;
    setSelectedId(id);
    onSelectFarmer(id);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!currentFarmer) return;

    onConfirmTurn({
      farmer_id: currentFarmer.id,
      status: status,
      actual_received_hours: status === 'PARTIAL' ? parseFloat(partialHours) : null,
      notes: notes
    });
  };

  if (!farmers || farmers.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Farmer Interactive Simulation</h3>
          <p className="text-xs text-slate-500">
            Simulate a farmer reporting water delivery or canal diversion from their mobile/SMS
          </p>
        </div>
        <span className="bg-emerald-50 text-emerald-700 text-xs px-2.5 py-1 rounded-full font-semibold border border-emerald-200">
          Mobile Node Active
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        
        {/* Left Column: Farmer Picker & Details */}
        <div className="md:col-span-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1.5">
              Select Farmer
            </label>
            <select
              value={selectedId}
              onChange={handleFarmerChange}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              {farmers.map(f => (
                <option key={f.id} value={f.id}>
                  {f.name} ({f.canal_reach} Reach) — Deficit: {f.accumulated_deficit_hours}h
                </option>
              ))}
            </select>
          </div>

          {currentFarmer && (
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80">
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-slate-900 text-base">{currentFarmer.name}</span>
                <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                  currentFarmer.canal_reach === 'Tail' 
                    ? 'bg-purple-50 text-purple-700 border-purple-200' 
                    : currentFarmer.canal_reach === 'Middle'
                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                    : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                }`}>
                  {currentFarmer.canal_reach} Reach Canal
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 mt-3">
                <div className="bg-white p-2 rounded-lg border border-slate-100">
                  <span className="text-slate-400 block text-[10px]">Crop & Land:</span>
                  <span className="font-semibold text-slate-800">{currentFarmer.crop_type} ({currentFarmer.plot_acres} ac)</span>
                </div>
                <div className="bg-white p-2 rounded-lg border border-slate-100">
                  <span className="text-slate-400 block text-[10px]">Village Section:</span>
                  <span className="font-semibold text-slate-800">{currentFarmer.village}</span>
                </div>
                <div className="bg-white p-2 rounded-lg border border-slate-100">
                  <span className="text-slate-400 block text-[10px]">Accumulated Deficit:</span>
                  <span className={`font-bold ${currentFarmer.accumulated_deficit_hours > 5 ? 'text-rose-600' : 'text-slate-800'}`}>
                    {currentFarmer.accumulated_deficit_hours} Hours
                  </span>
                </div>
                <div className="bg-white p-2 rounded-lg border border-slate-100">
                  <span className="text-slate-400 block text-[10px]">Watered History:</span>
                  <span className="font-semibold text-sky-700">{currentFarmer.total_received_hours} hrs received</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Reporting Actions */}
        <div className="md:col-span-6 bg-slate-50/70 p-4 rounded-xl border border-slate-200 flex flex-col justify-between">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
              Report Delivery Outcome
            </label>

            {/* Action Radio Options */}
            <div className="space-y-2 mb-3">
              <label 
                className={`flex items-center gap-3 p-2.5 rounded-xl border cursor-pointer transition-all ${
                  status === 'FULL' 
                    ? 'bg-emerald-50 border-emerald-300 text-emerald-900 font-semibold' 
                    : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <input
                  type="radio"
                  name="status"
                  value="FULL"
                  checked={status === 'FULL'}
                  onChange={() => setStatus('FULL')}
                  className="accent-emerald-600"
                />
                <div className="text-xs">
                  <span className="block font-bold">✅ Confirm Water Received (Full Turn)</span>
                  <span className="text-[11px] text-emerald-700 font-normal">
                    Water arrived at scheduled gate volume. Deficit cleared.
                  </span>
                </div>
              </label>

              <label 
                className={`flex items-center gap-3 p-2.5 rounded-xl border cursor-pointer transition-all ${
                  status === 'PARTIAL' 
                    ? 'bg-amber-50 border-amber-300 text-amber-900 font-semibold' 
                    : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <input
                  type="radio"
                  name="status"
                  value="PARTIAL"
                  checked={status === 'PARTIAL'}
                  onChange={() => setStatus('PARTIAL')}
                  className="accent-amber-600"
                />
                <div className="text-xs">
                  <span className="block font-bold">⚠️ Report Partial Water Received</span>
                  <span className="text-[11px] text-amber-700 font-normal">
                    Pressure was low or diverted early. Remaining deficit credited.
                  </span>
                </div>
              </label>

              <label 
                className={`flex items-center gap-3 p-2.5 rounded-xl border cursor-pointer transition-all ${
                  status === 'MISSED' 
                    ? 'bg-rose-50 border-rose-300 text-rose-900 font-semibold' 
                    : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <input
                  type="radio"
                  name="status"
                  value="MISSED"
                  checked={status === 'MISSED'}
                  onChange={() => setStatus('MISSED')}
                  className="accent-rose-600"
                />
                <div className="text-xs">
                  <span className="block font-bold">❌ Report Water Missed (Canal Dry / Diverted)</span>
                  <span className="text-[11px] text-rose-700 font-normal">
                    No water reached plot. Deficit increased & priority boosted in next rotation.
                  </span>
                </div>
              </label>
            </div>

            {/* Partial hours input if selected */}
            {status === 'PARTIAL' && (
              <div className="mb-3 p-2.5 bg-amber-50/70 rounded-lg border border-amber-200">
                <label className="block text-[11px] font-bold text-amber-900 mb-1">
                  Actual Hours of Flow Received:
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  max="10"
                  value={partialHours}
                  onChange={(e) => setPartialHours(e.target.value)}
                  className="w-full px-3 py-1.5 bg-white border border-amber-300 rounded-lg text-xs font-semibold text-amber-900"
                />
              </div>
            )}

            {/* Custom Notes */}
            <div className="mb-3">
              <input
                type="text"
                placeholder="Optional incident note (e.g., upstream headgate diverted)"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>
          </div>

          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="w-full py-2.5 px-4 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm active:scale-95 disabled:opacity-50"
          >
            {isSubmitting ? 'Recording on Immutable Ledger...' : 'Submit Confirmation & Update Deficit'}
          </button>
        </div>

      </div>
    </div>
  );
}
