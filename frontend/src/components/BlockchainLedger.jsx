import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link2, ShieldCheck, CheckCircle2, AlertTriangle, RefreshCw, Hash, Clock, FileCheck } from 'lucide-react';
import api from '../api';

export default function BlockchainLedger() {
  const [blocks, setBlocks] = useState([]);
  const [verification, setVerification] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchLedger = async () => {
    setLoading(true);
    try {
      const data = await api.getBlockchainLedger();
      setBlocks(data.blocks || []);
      const v = await api.verifyBlockchain();
      setVerification(v);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLedger();
  }, []);

  const getEventBadge = (type) => {
    const colors = {
      GENESIS: 'bg-blue-950/80 text-blue-300 border-blue-500/40',
      RULE_APPROVAL: 'bg-purple-950/80 text-purple-300 border-purple-500/40',
      REPORT_INTEGRITY: 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40',
      KNOWLEDGE_CONFIRMATION: 'bg-amber-950/80 text-amber-300 border-amber-500/40',
    }[type] || 'bg-slate-800 text-slate-300 border-slate-700';

    return (
      <span className={`px-2 py-0.5 text-[10px] uppercase font-mono font-bold rounded border ${colors}`}>
        {type}
      </span>
    );
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Integrity Status Header */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-bold text-white font-mono flex items-center gap-2">
              <Link2 className="w-5 h-5 text-brand-400" />
              CRYPTOGRAPHIC PROVENANCE & BLOCKCHAIN INTEGRITY
            </h2>
            {verification?.valid ? (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 font-mono font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                VERIFIED (NO TAMPERING)
              </span>
            ) : (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-rose-950/80 text-rose-300 border border-rose-500/40 font-mono font-bold flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                TAMPERING DETECTED
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Theme: Blockchain & Cybersecurity (NTRO). Immutable cryptographic audit trail proving approved rules,
            human training confirmations, and finalized audit report SHA-256 hashes.
          </p>
        </div>

        <button
          onClick={fetchLedger}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-mono font-semibold transition flex items-center gap-1.5 self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Verify Cryptographic Chain
        </button>
      </div>

      {/* Verifying Loading Banner */}
      {loading && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="glass-panel p-4 rounded-xl border border-brand-500/40 bg-brand-950/20 flex items-center justify-between font-mono text-xs text-brand-300 shadow-lg shadow-brand-500/10"
        >
          <div className="flex items-center gap-3">
            <RefreshCw className="w-5 h-5 animate-spin text-brand-400" />
            <div>
              <div className="font-bold tracking-wide">CRYPTOGRAPHIC CHAIN VERIFICATION IN PROGRESS...</div>
              <div className="text-[11px] text-slate-400 font-sans">
                Recalculating SHA-256 hashes across all {blocks.length} blocks & proving hash continuity.
              </div>
            </div>
          </div>
          <div className="w-32 h-2.5 rounded-full shimmer hidden sm:block" />
        </motion.div>
      )}

      {/* Block Explorer List */}
      <div className="space-y-4">

        {blocks.map((block, index) => (
          <motion.div
            key={block.block_hash}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="glass-panel rounded-xl p-5 border border-slate-800 hover:border-slate-700 transition relative overflow-hidden"
          >
            {/* Block Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800/80 gap-2">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center font-mono font-bold text-brand-300 text-xs">
                  #{block.index}
                </div>
                <div>
                  <span className="font-mono text-xs font-bold text-white mr-2">BLOCK {block.index}</span>
                  {getEventBadge(block.event_type)}
                </div>
              </div>

              <div className="flex items-center gap-1.5 text-slate-400 text-[11px] font-mono">
                <Clock className="w-3.5 h-3.5" />
                <span>{block.timestamp}</span>
              </div>
            </div>

            {/* Block Body */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3 text-xs font-mono">
              <div className="md:col-span-2 space-y-1.5 bg-[#050811] p-3 rounded-lg border border-slate-850">
                <div className="text-slate-400 text-[11px] font-sans font-semibold">BLOCK PAYLOAD:</div>
                <pre className="text-brand-300 text-[11px] whitespace-pre-wrap overflow-x-auto max-h-32 terminal-scroll">
                  {JSON.stringify(block.payload, null, 2)}
                </pre>
              </div>

              <div className="space-y-2 bg-[#050811] p-3 rounded-lg border border-slate-850">
                <div>
                  <span className="text-slate-500 text-[10px] block">BLOCK SHA-256 HASH:</span>
                  <span className="text-emerald-400 text-[10px] break-all font-bold">
                    {block.block_hash}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] block">PREVIOUS BLOCK HASH:</span>
                  <span className="text-slate-400 text-[10px] break-all">
                    {block.previous_hash}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
