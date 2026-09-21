import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, AlertTriangle, MinusCircle } from 'lucide-react';

export default function StatusBadge({ status, size = 'md' }) {
  const normalized = (status || '').toLowerCase().trim();

  const config = {
    pass: {
      bg: 'bg-emerald-950/80 border-emerald-500/40 text-emerald-300',
      icon: CheckCircle,
      label: 'PASS',
      dot: 'bg-emerald-400',
    },
    fail: {
      bg: 'bg-rose-950/80 border-rose-500/40 text-rose-300',
      icon: XCircle,
      label: 'FAIL',
      dot: 'bg-rose-400',
    },
    needs_human_review: {
      bg: 'bg-amber-950/80 border-amber-500/40 text-amber-300',
      icon: AlertTriangle,
      label: 'NEEDS HUMAN REVIEW',
      dot: 'bg-amber-400',
    },
    not_applicable: {
      bg: 'bg-slate-900/80 border-slate-700/50 text-slate-400',
      icon: MinusCircle,
      label: 'NOT APPLICABLE',
      dot: 'bg-slate-500',
    },
  }[normalized] || {
    bg: 'bg-slate-900 border-slate-700 text-slate-400',
    icon: MinusCircle,
    label: (status || 'UNKNOWN').toUpperCase(),
    dot: 'bg-slate-500',
  };

  const Icon = config.icon;
  const sizeClasses = size === 'sm' 
    ? 'px-2 py-0.5 text-xs' 
    : size === 'lg' 
      ? 'px-3.5 py-1.5 text-sm font-semibold' 
      : 'px-2.5 py-1 text-xs font-medium';

  return (
    <motion.span
      key={normalized}
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 450, damping: 25 }}
      className={`inline-flex items-center gap-1.5 rounded-full border shadow-sm ${config.bg} ${sizeClasses}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot} animate-pulse`} />
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      <span>{config.label}</span>
    </motion.span>
  );
}
