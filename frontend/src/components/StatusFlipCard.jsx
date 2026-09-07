import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function StatusFlipCard({ flip }) {
  const { device_id, rule_id, before_status, after_status } = flip;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className="glass-panel rounded-xl p-4 border border-brand-500/20 bg-gradient-to-r from-slate-900/90 via-navy-850 to-slate-900/90 shadow-lg relative overflow-hidden"
    >
      <div className="absolute top-0 right-0 w-32 h-32 bg-brand-500/5 rounded-full blur-2xl pointer-events-none" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-xs text-brand-400 bg-brand-950/60 px-2 py-0.5 rounded border border-brand-500/30">
              {rule_id}
            </span>
            <span className="text-xs text-slate-400 font-mono">{device_id}</span>
          </div>
          <p className="text-xs text-slate-300">
            Automated finding status transition following human-confirmed learning
          </p>
        </div>

        <div className="flex items-center gap-3 self-end sm:self-center bg-slate-950/60 px-3 py-2 rounded-lg border border-slate-800">
          <div className="flex flex-col items-center">
            <span className="text-[10px] uppercase font-mono text-slate-500 mb-1">BEFORE</span>
            <StatusBadge status={before_status} size="sm" />
          </div>

          <motion.div
            animate={{ x: [0, 4, 0] }}
            transition={{ repeat: Infinity, duration: 1.5, ease: 'easeInOut' }}
            className="text-brand-400 mx-1"
          >
            <ArrowRight className="w-4 h-4" />
          </motion.div>

          <div className="flex flex-col items-center">
            <span className="text-[10px] uppercase font-mono text-emerald-400 mb-1 flex items-center gap-0.5">
              <Sparkles className="w-2.5 h-2.5" /> AFTER
            </span>
            <AnimatePresence mode="wait">
              <StatusBadge status={after_status} size="sm" />
            </AnimatePresence>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
