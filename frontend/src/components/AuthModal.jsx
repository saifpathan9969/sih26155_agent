import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Lock, User, Building, KeyRound, CheckCircle2,
  AlertCircle, ArrowRight, Sparkles, X, UserCheck
} from 'lucide-react';
import api from '../api';

export default function AuthModal({ isOpen, onClose, onLoginSuccess, currentUser }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('saifullahpathan49@gmail.com');
  const [password, setPassword] = useState('Sentry@779969');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('Lead Security Auditor');
  const [organization, setOrganization] = useState('NTRO Cybersecurity Directorate');
  const [audience, setAudience] = useState('enterprise'); // 'enterprise' | 'home'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  if (!isOpen) return null;

  const handleAuth = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      if (isRegister) {
        const res = await api.register({
          username,
          password,
          role,
          organization,
          full_name: fullName || username,
          audience,
        });
        setSuccessMsg("Registration successful! Logging in...");
        setTimeout(() => {
          onLoginSuccess(res.user);
          onClose();
        }, 600);
      } else {
        const res = await api.login(username, password);
        setSuccessMsg("Authentication verified! Welcome back.");
        setTimeout(() => {
          onLoginSuccess(res.user);
          onClose();
        }, 500);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Authentication failed. Please verify your credentials.");
    } finally {
      setLoading(false);
    }
  };

  // Quick 1-click login presets for effortless testing/judging
  const handleQuickLogin = (uname, pwd) => {
    setUsername(uname);
    setPassword(pwd);
    setIsRegister(false);
    setError(null);
    setLoading(true);
    api.login(uname, pwd)
      .then(res => {
        setSuccessMsg(`Authenticated as ${res.user.role}!`);
        setTimeout(() => {
          onLoginSuccess(res.user);
          onClose();
        }, 400);
      })
      .catch(err => {
        setError(err.response?.data?.detail || "Quick login failed.");
      })
      .finally(() => setLoading(false));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="w-full max-w-md glass-panel p-6 sm:p-8 rounded-2xl border border-brand-500/30 bg-[#0c1222] shadow-2xl relative overflow-hidden"
      >
        {/* Cyber glow background accent */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button if already logged in */}
        {currentUser && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        )}

        {/* Header */}
        <div className="text-center space-y-2 pb-5 border-b border-slate-800">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-brand-500/30">
            <Shield className="w-6 h-6 fill-current" />
          </div>
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-brand-950 border border-brand-500/40 text-[10px] font-mono text-brand-300 font-semibold mb-1">
              <span>NTRO ACCESS GATEWAY</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            </div>
            <h2 className="text-xl font-black font-mono text-white tracking-wide">
              {isRegister ? 'OPERATOR REGISTRATION' : 'SECURITY PORTAL LOGIN'}
            </h2>
            <p className="text-xs text-slate-400">
              {isRegister ? 'Register credential for certified compliance audits' : 'Authenticate to manage missions, rules & blockchain proof'}
            </p>
          </div>
        </div>

        {/* Mode Switch Tabs */}
        <div className="flex rounded-xl bg-[#050811] p-1 border border-slate-800 my-5">
          <button
            type="button"
            onClick={() => { setIsRegister(false); setError(null); }}
            className={`flex-1 py-2 text-xs font-mono font-semibold rounded-lg transition ${
              !isRegister
                ? 'bg-brand-600 text-white shadow-md shadow-brand-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsRegister(true); setError(null); }}
            className={`flex-1 py-2 text-xs font-mono font-semibold rounded-lg transition ${
              isRegister
                ? 'bg-brand-600 text-white shadow-md shadow-brand-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Register Account
          </button>
        </div>

        {/* Feedback Alerts */}
        {error && (
          <div className="p-3 mb-4 rounded-xl bg-rose-950/50 border border-rose-500/40 flex items-start gap-2.5 text-xs text-rose-300 font-mono">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
        {successMsg && (
          <div className="p-3 mb-4 rounded-xl bg-emerald-950/50 border border-emerald-500/40 flex items-start gap-2.5 text-xs text-emerald-300 font-mono">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleAuth} className="space-y-4">
          <div>
            <label className="block text-[11px] font-mono text-slate-400 mb-1">
              OPERATOR USERNAME:
            </label>
            <div className="relative">
              <User className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. admin or auditor_id"
                className="w-full bg-[#050811] border border-slate-700 rounded-xl pl-9 pr-4 py-2.5 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>

          {isRegister && (
            <>
              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">
                  FULL NAME / CALLSIGN:
                </label>
                <div className="relative">
                  <UserCheck className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Commander A. Sharma"
                    className="w-full bg-[#050811] border border-slate-700 rounded-xl pl-9 pr-4 py-2.5 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">
                  OFFICIAL ROLE:
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full bg-[#050811] border border-slate-700 rounded-xl px-3 py-2.5 text-xs font-mono text-white focus:outline-none focus:border-brand-500"
                >
                  <option value="Lead Security Auditor">Lead Security Auditor (NTRO)</option>
                  <option value="NTRO Compliance Officer">NTRO Compliance Officer</option>
                  <option value="Network Defense Analyst">Network Defense Analyst</option>
                  <option value="System Administrator">System Administrator</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">
                  ORGANIZATION / UNIT:
                </label>
                <div className="relative">
                  <Building className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                  <input
                    type="text"
                    value={organization}
                    onChange={(e) => setOrganization(e.target.value)}
                    placeholder="e.g. NTRO Cybersecurity Directorate"
                    className="w-full bg-[#050811] border border-slate-700 rounded-xl pl-9 pr-4 py-2.5 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">
                  ENVIRONMENT / AUDIT INTERFACE:
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setAudience('enterprise')}
                    className={`py-2 px-3 rounded-xl border text-xs font-mono flex items-center justify-center gap-1.5 transition ${
                      audience === 'enterprise'
                        ? 'bg-brand-600/30 border-brand-400 text-white font-bold shadow-sm shadow-brand-500/20'
                        : 'bg-[#050811] border-slate-700 text-slate-400 hover:border-slate-600'
                    }`}
                  >
                    <span>🏢 Enterprise</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setAudience('home')}
                    className={`py-2 px-3 rounded-xl border text-xs font-mono flex items-center justify-center gap-1.5 transition ${
                      audience === 'home'
                        ? 'bg-amber-600/30 border-amber-400 text-white font-bold shadow-sm shadow-amber-500/20'
                        : 'bg-[#050811] border-slate-700 text-slate-400 hover:border-slate-600'
                    }`}
                  >
                    <span>🏠 Home & SOHO</span>
                  </button>
                </div>
                <p className="text-[10px] text-slate-500 mt-1">
                  {audience === 'enterprise'
                    ? 'CIS compliance benchmarks for corporate routers, firewalls & multi-vendor switches.'
                    : 'Personal Wi-Fi router checks with plain-English step-by-step fix guides.'}
                </p>
              </div>
            </>
          )}

          <div>
            <label className="block text-[11px] font-mono text-slate-400 mb-1">
              SECURITY PASSPHRASE:
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-[#050811] border border-slate-700 rounded-xl pl-9 pr-4 py-2.5 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-brand-600 to-cyan-600 hover:from-brand-500 hover:to-cyan-500 text-white font-mono font-bold text-xs tracking-wide shadow-lg shadow-brand-500/25 transition disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
          >
            {loading ? (
              <span>VERIFYING CRYPTOGRAPHIC CREDENTIALS...</span>
            ) : (
              <>
                <KeyRound className="w-4 h-4" />
                <span>{isRegister ? 'REGISTER & ENTER AUDITOR' : 'AUTHENTICATE & ENTER'}</span>
              </>
            )}
          </button>
        </form>
      </motion.div>
    </div>
  );
}
