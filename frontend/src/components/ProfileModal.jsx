import React from 'react';
import { motion } from 'framer-motion';
import {
  Mail, Building, CheckCircle2,
  LogOut, X, Lock,
} from 'lucide-react';

export default function ProfileModal({ isOpen, onClose, currentUser, onLogout }) {
  if (!isOpen || !currentUser) return null;

  const email    = currentUser.email    || currentUser.username;
  const fullName = currentUser.full_name || currentUser.username;
  const role     = currentUser.role     || 'Security Auditor';
  const org      = currentUser.organization || 'Cybersecurity Directorate';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="w-full max-w-lg glass-panel p-6 sm:p-7 rounded-2xl border border-brand-500/30 bg-[#0c1222] shadow-2xl relative overflow-hidden my-6 font-sans text-slate-100"
      >
        <div className="absolute top-0 right-0 w-80 h-80 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Close */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Profile Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 pb-6 border-b border-slate-800/90">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-600 via-brand-500 to-cyan-500 flex items-center justify-center text-white text-2xl font-black shadow-lg shadow-brand-500/30 border border-brand-400/40 shrink-0">
            {fullName.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <h2 className="text-xl font-black font-mono text-white tracking-wide truncate">{fullName}</h2>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-950 text-brand-300 font-mono border border-brand-500/40 font-bold">
                {role}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 font-mono">
              <span className="flex items-center gap-1.5 truncate">
                <Mail className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                <span className="text-slate-300 font-medium">{email}</span>
              </span>
              <span className="flex items-center gap-1.5 truncate">
                <Building className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                <span>{org}</span>
              </span>
            </div>
          </div>
        </div>

        {/* Capabilities */}
        <div className="py-5 space-y-3">
          <h3 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
            Enterprise Compliance Features
          </h3>
          <ul className="space-y-2 text-xs text-slate-300 font-sans">
            {[
              'CIS Benchmarks & NIST 800-53 rule engine',
              'Cisco, Fortinet, Arista, Juniper, MikroTik support',
              'Cryptographic Merkle Tree blockchain ledger',
              'Human-in-the-loop active learning',
              'Verified sandbox remediation workflow',
            ].map((item, i) => (
              <li key={i} className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            <span>Session:</span>
            <code className="bg-slate-900 px-1.5 py-0.5 rounded text-slate-300 border border-slate-800">
              {email}
            </code>
          </div>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              type="button"
              onClick={() => { onLogout(); onClose(); }}
              className="flex-1 sm:flex-none px-3 py-2 rounded-xl bg-rose-950/60 hover:bg-rose-900/80 border border-rose-500/40 text-rose-300 text-xs font-mono font-bold transition flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign Out
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 sm:flex-none px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-semibold transition cursor-pointer"
            >
              Done
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
