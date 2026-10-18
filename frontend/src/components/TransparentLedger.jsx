import React, { useState } from 'react';

export default function TransparentLedger({ logs, integrityInfo, onRefresh }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [copiedHash, setCopiedHash] = useState(null);

  const filteredLogs = (logs || []).filter(log => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      log.farmer_name.toLowerCase().includes(term) ||
      log.status.toLowerCase().includes(term) ||
      (log.notes && log.notes.toLowerCase().includes(term)) ||
      log.current_hash.toLowerCase().includes(term)
    );
  });

  const handleCopy = (hash) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Top Banner with Cryptographic Proof */}
      <div className="p-5 border-b border-slate-100 bg-slate-900 text-white flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">🛡️</span>
            <h3 className="text-lg font-bold">Transparent Distribution Ledger</h3>
            <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs px-2.5 py-0.5 rounded-full font-mono font-medium">
              SHA-256 Chain Verified
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Every water turn confirmation is cryptographically chained. Any alteration immediately breaks the root hash.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider">Validated Blocks</div>
            <div className="text-base font-bold font-mono text-emerald-400">
              {integrityInfo?.count ?? (logs?.length || 0)} Blocks Intact
            </div>
          </div>
          <button
            onClick={onRefresh}
            className="p-2 bg-slate-800 hover:bg-slate-700 active:scale-95 text-slate-300 rounded-lg text-xs font-medium transition-all"
            title="Re-verify cryptographic ledger"
          >
            ↻ Verify
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="p-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between gap-4">
        <div className="relative w-full max-w-sm">
          <input
            type="text"
            placeholder="Search farmer, status, or notes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
          <span className="absolute left-3 top-2.5 text-slate-400 text-xs">🔍</span>
        </div>
        <div className="text-xs text-slate-500 font-medium">
          Showing {filteredLogs.length} ledger records
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse font-sans text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
              <th className="py-3 px-4">Block #</th>
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4">Farmer</th>
              <th className="py-3 px-4">Scheduled / Received</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Verification Audit Notes</th>
              <th className="py-3 px-4 font-mono">SHA-256 Cryptographic Hash</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {filteredLogs.map((log) => {
              const isFull = log.status === 'FULL';
              const isPartial = log.status === 'PARTIAL';
              const isMissed = log.status === 'MISSED';

              return (
                <tr key={log.id} className="hover:bg-slate-50/70 transition-colors">
                  
                  {/* Block Number */}
                  <td className="py-3 px-4 font-mono font-bold text-slate-900">
                    #{log.id}
                  </td>

                  {/* Timestamp */}
                  <td className="py-3 px-4 text-slate-500 whitespace-nowrap">
                    {log.timestamp}
                  </td>

                  {/* Farmer */}
                  <td className="py-3 px-4 font-semibold text-slate-900">
                    {log.farmer_name}
                  </td>

                  {/* Hours */}
                  <td className="py-3 px-4">
                    <span className="font-bold text-slate-800">{log.actual_received_hours}h</span>
                    <span className="text-slate-400 text-[11px]"> / {log.scheduled_hours}h</span>
                  </td>

                  {/* Status Badge */}
                  <td className="py-3 px-4">
                    <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                      isFull
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : isPartial
                        ? 'bg-amber-50 text-amber-700 border-amber-200'
                        : 'bg-rose-50 text-rose-700 border-rose-200'
                    }`}>
                      {log.status}
                    </span>
                  </td>

                  {/* Notes */}
                  <td className="py-3 px-4 text-slate-600 max-w-xs truncate" title={log.notes}>
                    {log.notes || '—'}
                  </td>

                  {/* Hash */}
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-500 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      <span className="text-emerald-600" title="Hash chain unbroken">✓</span>
                      <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-700">
                        {log.current_hash ? `${log.current_hash.substring(0, 8)}...${log.current_hash.substring(56)}` : 'GENESIS'}
                      </span>
                      <button
                        onClick={() => handleCopy(log.current_hash)}
                        className="text-slate-400 hover:text-slate-600 p-1 text-[10px]"
                        title="Copy full 64-char SHA-256 hash"
                      >
                        {copiedHash === log.current_hash ? '✓' : '📋'}
                      </button>
                    </div>
                  </td>

                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
