import React, { useState } from 'react';

export default function ScheduleTimeline({ schedule, onQuickConfirm }) {
  const [filterReach, setFilterReach] = useState('ALL');

  const filteredSchedule = schedule.filter(slot => {
    if (filterReach === 'ALL') return true;
    return slot.canal_reach.toUpperCase() === filterReach;
  });

  const getReachBadge = (reach) => {
    switch (reach.toLowerCase()) {
      case 'tail':
        return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'middle':
        return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'head':
        return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'FULL':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'PARTIAL':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'MISSED':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      default:
        return 'bg-sky-50 text-sky-700 border-sky-200';
    }
  };

  if (!schedule || schedule.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-10 text-center border border-slate-200 shadow-sm">
        <div className="w-16 h-16 bg-sky-50 text-sky-500 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
          💧
        </div>
        <h4 className="text-lg font-bold text-slate-800 mb-1">No Active Rotation Schedule</h4>
        <p className="text-sm text-slate-500 max-w-md mx-auto mb-5">
          Click the <strong>"Run KulhWise Algorithm"</strong> button above to calculate fair time slots based on plot sizes and accumulated farmer deficits.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Header and Filter */}
      <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-slate-900">Today's Kulh Rotation Schedule</h3>
            <span className="bg-sky-100 text-sky-700 text-xs px-2.5 py-0.5 rounded-full font-semibold">
              {schedule.length} Rotation Slots
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Fair rotation prioritized by accumulated deficit hours & crop water duty
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl text-xs font-medium">
          {['ALL', 'TAIL', 'MIDDLE', 'HEAD'].map((reach) => (
            <button
              key={reach}
              onClick={() => setFilterReach(reach)}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                filterReach === reach
                  ? 'bg-white text-slate-800 shadow-sm font-semibold'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {reach === 'ALL' ? 'All Sections' : `${reach} Reach`}
            </button>
          ))}
        </div>
      </div>

      {/* Table view */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/75 border-b border-slate-100 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              <th className="py-3 px-4">Rank</th>
              <th className="py-3 px-4">Time Slot</th>
              <th className="py-3 px-4">Farmer Details</th>
              <th className="py-3 px-4">Canal Reach</th>
              <th className="py-3 px-4">Crop & Acres</th>
              <th className="py-3 px-4">Allocated Flow</th>
              <th className="py-3 px-4">Priority Score</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
            {filteredSchedule.map((slot) => (
              <tr key={slot.id || slot.farmer_id} className="hover:bg-slate-50/80 transition-colors">
                
                {/* Priority Rank */}
                <td className="py-3.5 px-4 font-semibold">
                  <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                    slot.priority_rank <= 5 
                      ? 'bg-purple-600 text-white shadow-sm' 
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    #{slot.priority_rank}
                  </span>
                </td>

                {/* Time Slot */}
                <td className="py-3.5 px-4 font-medium text-slate-900 whitespace-nowrap">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sky-600">⏱</span>
                    <span>{slot.start_time} – {slot.end_time}</span>
                  </div>
                </td>

                {/* Farmer Details */}
                <td className="py-3.5 px-4">
                  <div className="font-semibold text-slate-900">{slot.farmer_name}</div>
                  <div className="text-xs text-slate-400">Farmer ID: #{slot.farmer_id}</div>
                </td>

                {/* Reach */}
                <td className="py-3.5 px-4">
                  <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${getReachBadge(slot.canal_reach)}`}>
                    {slot.canal_reach} Reach
                  </span>
                </td>

                {/* Crop & Plot */}
                <td className="py-3.5 px-4">
                  <div className="text-xs font-medium text-slate-800">{slot.crop_type}</div>
                  <div className="text-[11px] text-slate-400">{slot.plot_acres} Acres</div>
                </td>

                {/* Allocated Hours & Compensation */}
                <td className="py-3.5 px-4">
                  <div className="font-bold text-sky-700">{slot.allocated_hours} hrs</div>
                  {slot.compensation_applied > 0 && (
                    <div className="text-[10px] text-purple-600 font-semibold bg-purple-50 px-1.5 py-0.5 rounded inline-block mt-0.5 border border-purple-100">
                      +{slot.compensation_applied}h Deficit Relief
                    </div>
                  )}
                </td>

                {/* Priority Score */}
                <td className="py-3.5 px-4 font-mono text-xs font-semibold text-slate-600">
                  {slot.priority_score}
                </td>

                {/* Status */}
                <td className="py-3.5 px-4">
                  <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${getStatusBadge(slot.status)}`}>
                    {slot.status}
                  </span>
                </td>

                {/* Quick Action */}
                <td className="py-3.5 px-4 text-right">
                  <button
                    onClick={() => onQuickConfirm(slot.farmer_id)}
                    className="px-3 py-1 text-xs font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-all"
                  >
                    Simulate
                  </button>
                </td>

              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
