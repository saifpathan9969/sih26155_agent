import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  User, UserCheck, Shield, Building, Mail, CheckCircle2,
  ArrowRightLeft, Wifi, Building2, LogOut, X, Sparkles,
  Lock, KeyRound, ExternalLink, RefreshCw
} from 'lucide-react';

export default function ProfileModal({
  isOpen,
  onClose,
  currentUser,
  audienceMode,
  onSwitchPanel,
  onLogout
}) {
  if (!isOpen || !currentUser) return null;

  const email = currentUser.email || currentUser.username;
  const fullName = currentUser.full_name || currentUser.username;
  const role = currentUser.role || 'Security Auditor';
  const org = currentUser.organization || 'Cybersecurity Directorate';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="w-full max-w-2xl glass-panel p-6 sm:p-7 rounded-2xl border border-brand-500/30 bg-[#0c1222] shadow-2xl relative overflow-hidden my-6 font-sans text-slate-100"
      >
        {/* Glow ambient background accents */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          title="Close profile dialog"
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
              <h2 className="text-xl font-black font-mono text-white tracking-wide truncate">
                {fullName}
              </h2>
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

        {/* Panel Switcher Section */}
        <div className="py-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <ArrowRightLeft className="w-4 h-4 text-brand-400" />
                <h3 className="text-sm font-bold font-mono tracking-wider text-white uppercase">
                  Switch Active Audit Panel
                </h3>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Your single account has unlimited access to both environments. Switch anytime with one click.
              </p>
            </div>
            <span className="text-[11px] font-mono text-slate-400 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 hidden sm:inline-block">
              Single Account — Dual Mode
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
            {/* Enterprise Panel Card */}
            <div
              className={`p-4 rounded-xl border transition relative flex flex-col justify-between ${
                audienceMode === 'enterprise'
                  ? 'bg-brand-950/40 border-brand-500/60 shadow-lg shadow-brand-500/10'
                  : 'bg-[#060a14] border-slate-800 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-brand-500/20 text-brand-400 border border-brand-500/30">
                      <Building2 className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white font-mono">Enterprise Compliance</h4>
                      <p className="text-[10px] text-brand-300 font-mono">For Data Centers & NOCs</p>
                    </div>
                  </div>
                  {audienceMode === 'enterprise' && (
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300 text-[10px] font-mono font-bold border border-brand-500/40">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      ACTIVE
                    </span>
                  )}
                </div>

                <ul className="text-xs text-slate-400 space-y-1.5 mb-4 pl-1 font-sans">
                  <li className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                    <span>CIS Benchmarks & NIST 800-53</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                    <span>Cisco, Fortinet, Arista, Juniper, MikroTik</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                    <span>Cryptographic Merkle Tree ledger</span>
                  </li>
                </ul>
              </div>

              {audienceMode === 'enterprise' ? (
                <div className="py-2 px-3 rounded-xl bg-brand-900/30 text-brand-300 text-xs font-mono font-bold text-center border border-brand-500/30">
                  ✓ Currently In Enterprise Mode
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    onSwitchPanel('enterprise');
                    onClose();
                  }}
                  className="w-full py-2.5 px-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-mono font-bold text-xs transition shadow-md shadow-brand-500/25 flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <span>Switch to Enterprise Panel</span>
                  <ArrowRightLeft className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Home & SOHO Security Card */}
            <div
              className={`p-4 rounded-xl border transition relative flex flex-col justify-between ${
                audienceMode === 'soho'
                  ? 'bg-amber-950/40 border-amber-500/60 shadow-lg shadow-amber-500/10'
                  : 'bg-[#060a14] border-slate-800 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
                      <Wifi className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white font-mono">Home & SOHO Hub</h4>
                      <p className="text-[10px] text-amber-300 font-mono">For Residential Wi-Fi & Gateways</p>
                    </div>
                  </div>
                  {audienceMode === 'soho' && (
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-[10px] font-mono font-bold border border-amber-500/40">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                      ACTIVE
                    </span>
                  )}
                </div>

                <ul className="text-xs text-slate-400 space-y-1.5 mb-4 pl-1 font-sans">
                  <li className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    <span>Wi-Fi 6 Router Security & Guest isolation</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    <span>Default password & UPnP exploit guards</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    <span>Plain-English 1-click remediation guides</span>
                  </li>
                </ul>
              </div>

              {audienceMode === 'soho' ? (
                <div className="py-2 px-3 rounded-xl bg-amber-900/30 text-amber-300 text-xs font-mono font-bold text-center border border-amber-500/30">
                  ✓ Currently In Home & SOHO Mode
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    onSwitchPanel('soho');
                    onClose();
                  }}
                  className="w-full py-2.5 px-3 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-mono font-bold text-xs transition shadow-md shadow-amber-500/25 flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <span>Switch to Home & SOHO Panel</span>
                  <ArrowRightLeft className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            <span>Authenticated Session:</span>
            <code className="bg-slate-900 px-1.5 py-0.5 rounded text-slate-300 border border-slate-800">
              {email}
            </code>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              type="button"
              onClick={() => {
                onLogout();
                onClose();
              }}
              className="flex-1 sm:flex-none px-3 py-2 rounded-xl bg-rose-950/60 hover:bg-rose-900/80 border border-rose-500/40 text-rose-300 text-xs font-mono font-bold transition flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
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
