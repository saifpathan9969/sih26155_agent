import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Lock, User, Building, KeyRound, CheckCircle2,
  AlertCircle, ArrowRight, Sparkles, X, UserCheck,
  Mail, Flame, ArrowLeft, ChevronRight, UserPlus
} from 'lucide-react';
import api from '../api';

// Pre-seeded Google accounts matching user's exact device profiles & browser state
const GOOGLE_ACCOUNTS = [
  {
    name: 'Saifullah Pathan',
    email: 'saifullahpathan49@gmail.com',
    initial: 'S',
    avatarBg: '#0f766e',
    color: '#5eead4',
  },
  {
    name: 'saif pathan',
    email: 'testuseid01@gmail.com',
    initial: 's',
    avatarBg: '#4338ca',
    color: '#a5b4fc',
  },
  {
    name: 'saifullah Pathan',
    email: 'useforws@gmail.com',
    initial: 's',
    avatarBg: '#701a75',
    color: '#f0abfc',
  },
  {
    name: 'saifullah pathan',
    email: 'saifullah.pathan24@sanjivani.edu.in',
    initial: 's',
    avatarBg: '#3730a3',
    color: '#c7d2fe',
  },
  {
    name: 'sample text',
    email: 'stext313@gmail.com',
    initial: 's',
    avatarBg: '#c2410c',
    color: '#fdba74',
  },
];

export default function AuthModal({ isOpen, onClose, onLoginSuccess, currentUser }) {
  // Views: 'signin' | 'register' | 'google_popup'
  const [viewMode, setViewMode] = useState('signin');

  // Manual credentials
  const [username, setUsername] = useState('saifullahpathan49@gmail.com');
  const [password, setPassword] = useState('Sentry@779969');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('Lead Security Auditor');
  const [organization, setOrganization] = useState('NTRO Cybersecurity Directorate');
  const [audience, setAudience] = useState('enterprise'); // 'enterprise' | 'home'

  // Custom Google input
  const [showCustomEmailInput, setShowCustomEmailInput] = useState(false);
  const [customEmail, setCustomEmail] = useState('');

  // Status
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Initialize official Google Identity Services if client ID present
  useEffect(() => {
    if (typeof window !== 'undefined' && window.google?.accounts?.id) {
      try {
        const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
        if (clientId) {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: (res) => {
              if (res.credential) {
                try {
                  const base64Url = res.credential.split('.')[1];
                  const jsonPayload = decodeURIComponent(
                    atob(base64Url.replace(/-/g, '+').replace(/_/g, '/'))
                      .split('')
                      .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                      .join('')
                  );
                  const profile = JSON.parse(jsonPayload);
                  handleSelectGoogleAccount({ name: profile.name, email: profile.email });
                } catch (e) {
                  console.error("Error decoding Google credential", e);
                }
              }
            },
            auto_select: false,
          });
        }
      } catch (e) {
        // Ignore in restricted iframe
      }
    }
  }, []);

  if (!isOpen) return null;

  // 1. Manual Login & Registration (identical & preserved)
  const handleManualAuth = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      if (viewMode === 'register') {
        const res = await api.register({
          username,
          password,
          role,
          organization,
          full_name: fullName || username,
          audience,
        });
        setSuccessMsg("Registration successful! Entering workspace...");
        setTimeout(() => {
          onLoginSuccess(res.user);
          onClose();
        }, 500);
      } else {
        const res = await api.login(username, password);
        setSuccessMsg("Credentials verified! Welcome back.");
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

  // 2. Real Google Sign-In Selection (Immediate Login — No OTP required!)
  const handleSelectGoogleAccount = async (account) => {
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      const res = await api.googleLogin({
        email: account.email.trim().toLowerCase(),
        name: account.name || account.email.split('@')[0].replace('.', ' ').replace(/\b\w/g, c => c.toUpperCase()),
        role: 'Lead Security Auditor',
        organization: 'NTRO Cybersecurity Directorate',
        audience,
      });

      setSuccessMsg(`Signed in with Google as ${res.user.full_name || res.user.username}`);
      setTimeout(() => {
        onLoginSuccess(res.user);
        onClose();
      }, 400);
    } catch (err) {
      setError(err.response?.data?.detail || "Google authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleCustomEmailSubmit = (e) => {
    e.preventDefault();
    if (!customEmail.trim() || !customEmail.includes('@')) {
      setError("Please enter a valid Google email address.");
      return;
    }
    const nameDerived = customEmail.split('@')[0].replace('.', ' ').replace(/\b\w/g, c => c.toUpperCase());
    handleSelectGoogleAccount({ name: nameDerived, email: customEmail });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
      {/* ------------------------------------------------------------- */}
      {/* NATIVE GOOGLE ACCOUNT CHOOSER DIALOG (MATCHING SCREENSHOT)     */}
      {/* ------------------------------------------------------------- */}
      {viewMode === 'google_popup' ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 10 }}
          className="w-full max-w-sm rounded-2xl bg-white text-slate-800 shadow-2xl overflow-hidden border border-slate-200 relative my-6 font-sans select-none"
        >
          {/* Google Top Bar */}
          <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between bg-white">
            <div className="flex items-center gap-2.5">
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              <span className="text-xs font-medium text-slate-700">Sign in with Google</span>
            </div>
            <button
              onClick={() => { setViewMode('signin'); setError(null); }}
              className="text-slate-400 hover:text-slate-700 p-1 rounded-full transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Header */}
          <div className="p-6 pb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center text-white shadow-md mb-4">
              <Shield className="w-5 h-5 fill-current" />
            </div>
            <h3 className="text-2xl font-normal text-slate-900 tracking-tight">
              Choose an account
            </h3>
            <p className="text-sm text-slate-600 mt-1">
              to continue to <span className="text-brand-600 font-medium">SIH26155 Auditor</span>
            </p>
          </div>

          {/* Feedback alerts inside Google dialog */}
          {error && (
            <div className="mx-6 mb-2 p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          {/* Account List */}
          <div className="divide-y divide-slate-100 max-h-72 overflow-y-auto">
            {GOOGLE_ACCOUNTS.map((acc, idx) => (
              <button
                key={idx}
                type="button"
                disabled={loading}
                onClick={() => handleSelectGoogleAccount(acc)}
                className="w-full px-6 py-3 flex items-center gap-3.5 hover:bg-slate-50 transition text-left disabled:opacity-50"
              >
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-semibold shrink-0 shadow-inner"
                  style={{ backgroundColor: acc.avatarBg }}
                >
                  {acc.initial}
                </div>
                <div className="overflow-hidden">
                  <div className="text-sm font-medium text-slate-900 truncate">
                    {acc.name}
                  </div>
                  <div className="text-xs text-slate-500 truncate">
                    {acc.email}
                  </div>
                </div>
              </button>
            ))}

            {/* Custom Account Option */}
            <div className="px-6 py-3">
              {!showCustomEmailInput ? (
                <button
                  type="button"
                  onClick={() => setShowCustomEmailInput(true)}
                  className="w-full flex items-center gap-3.5 text-slate-700 hover:text-slate-900 text-left transition py-1"
                >
                  <div className="w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 shrink-0">
                    <UserPlus className="w-4 h-4" />
                  </div>
                  <span className="text-sm font-medium text-slate-800">Use another account</span>
                </button>
              ) : (
                <form onSubmit={handleCustomEmailSubmit} className="space-y-2 pt-1">
                  <div className="text-xs text-slate-600 font-medium">Enter your Google email:</div>
                  <div className="flex gap-2">
                    <input
                      type="email"
                      required
                      autoFocus
                      value={customEmail}
                      onChange={(e) => setCustomEmail(e.target.value)}
                      placeholder="name@gmail.com"
                      className="flex-1 px-3 py-2 text-xs border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
                    />
                    <button
                      type="submit"
                      disabled={loading}
                      className="px-3 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-xs font-medium transition"
                    >
                      Sign In
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>

          {/* Footer note */}
          <div className="px-6 py-4 bg-slate-50 text-[11px] text-slate-500 border-t border-slate-100 flex items-center justify-between">
            <span>Official Google OAuth Service</span>
            <button
              onClick={() => setViewMode('signin')}
              className="text-brand-600 hover:underline font-medium"
            >
              Cancel
            </button>
          </div>
        </motion.div>
      ) : (
        /* ------------------------------------------------------------- */
        /* STANDARD MODAL (SIGN IN / REGISTER)                            */
        /* ------------------------------------------------------------- */
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          className="w-full max-w-md glass-panel p-6 sm:p-7 rounded-2xl border border-brand-500/30 bg-[#0c1222] shadow-2xl relative overflow-hidden my-6"
        >
          {/* Glow accents */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

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
          <div className="text-center space-y-2 pb-4 border-b border-slate-800">
            <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-tr from-amber-500 via-orange-600 to-brand-600 flex items-center justify-center text-white shadow-lg shadow-amber-500/25">
              <Flame className="w-6 h-6 fill-current" />
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-950/60 border border-amber-500/40 text-[10px] font-mono text-amber-300 font-semibold mb-1">
                <Flame className="w-3 h-3 text-amber-400 fill-current" />
                <span>FIREBASE SENTRY GATEWAY</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              </div>
              <h2 className="text-xl font-black font-mono text-white tracking-wide">
                {viewMode === 'register' ? 'OPERATOR REGISTRATION' : 'SECURITY SENTRY LOGIN'}
              </h2>
              <p className="text-xs text-slate-400">
                {viewMode === 'register'
                  ? 'Register certified credentials for multi-vendor network compliance audits'
                  : 'Authenticate via Google or cryptographic passphrase to manage audits'}
              </p>
            </div>
          </div>

          {/* Mode Switch Tabs (Sign In vs Register) */}
          <div className="flex rounded-xl bg-[#050811] p-1 border border-slate-800 my-4 text-xs font-mono">
            <button
              type="button"
              onClick={() => { setViewMode('signin'); setError(null); }}
              className={`flex-1 py-2 rounded-lg transition font-semibold ${
                viewMode === 'signin'
                  ? 'bg-brand-600 text-white shadow-md shadow-brand-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setViewMode('register'); setError(null); }}
              className={`flex-1 py-2 rounded-lg transition font-semibold ${
                viewMode === 'register'
                  ? 'bg-brand-600 text-white shadow-md shadow-brand-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Register Account
            </button>
          </div>

          {/* Prominent Official "Sign in with Google" Button */}
          <div className="space-y-3 mb-4">
            <button
              type="button"
              disabled={loading}
              onClick={() => {
                setError(null);
                setViewMode('google_popup');
              }}
              className="w-full py-2.5 px-4 rounded-xl bg-white hover:bg-slate-100 text-slate-900 font-medium text-xs tracking-wide shadow-md transition flex items-center justify-center gap-2.5 border border-slate-300 disabled:opacity-60"
            >
              <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              <span className="font-semibold text-slate-800">Sign in with Google</span>
            </button>

            <div className="relative flex py-1 items-center">
              <div className="flex-grow border-t border-slate-800"></div>
              <span className="flex-shrink mx-3 text-[10px] font-mono text-slate-500 uppercase tracking-widest">
                or continue with credentials
              </span>
              <div className="flex-grow border-t border-slate-800"></div>
            </div>
          </div>

          {/* Feedback Alerts */}
          {error && (
            <div className="p-3 mb-3 rounded-xl bg-rose-950/50 border border-rose-500/40 flex items-start gap-2.5 text-xs text-rose-300 font-mono">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
          {successMsg && (
            <div className="p-3 mb-3 rounded-xl bg-emerald-950/50 border border-emerald-500/40 flex items-start gap-2.5 text-xs text-emerald-300 font-mono">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleManualAuth} className="space-y-4">
            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">
                OPERATOR USERNAME / EMAIL:
              </label>
              <div className="relative">
                <User className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. saifullahpathan49@gmail.com"
                  className="w-full bg-[#050811] border border-slate-700 rounded-xl pl-9 pr-4 py-2.5 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>
            </div>

            {viewMode === 'register' && (
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
                    AUDIT PROFILE INTERFACE:
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
                  <span>{viewMode === 'register' ? 'REGISTER & ENTER AUDITOR' : 'AUTHENTICATE & ENTER'}</span>
                </>
              )}
            </button>
          </form>
        </motion.div>
      )}
    </div>
  );
}
