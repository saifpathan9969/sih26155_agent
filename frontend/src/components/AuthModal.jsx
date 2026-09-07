import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Lock, User, Building, KeyRound, CheckCircle2,
  AlertCircle, ArrowRight, Sparkles, X, UserCheck,
  Mail, Flame, RefreshCw, Send, Check, ArrowLeft, ChevronRight
} from 'lucide-react';
import api from '../api';

export default function AuthModal({ isOpen, onClose, onLoginSuccess, currentUser }) {
  // Main view: 'signin' | 'register' | 'google_select' | 'google_otp'
  const [viewMode, setViewMode] = useState('signin');

  // Manual login / registration credentials
  const [username, setUsername] = useState('saifullahpathan49@gmail.com');
  const [password, setPassword] = useState('Sentry@779969');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('Lead Security Auditor');
  const [organization, setOrganization] = useState('NTRO Cybersecurity Directorate');
  const [audience, setAudience] = useState('enterprise'); // 'enterprise' | 'home'

  // Google flow state
  const [selectedGoogleEmail, setSelectedGoogleEmail] = useState('saifullahpathan49@gmail.com');
  const [customGoogleEmail, setCustomGoogleEmail] = useState('');
  const [isCustomGoogleEmail, setIsCustomGoogleEmail] = useState(false);
  const [googleOtpDigits, setGoogleOtpDigits] = useState(['', '', '', '', '', '']);
  const [googleNewPassword, setGoogleNewPassword] = useState('');
  const [googleConfirmPassword, setGoogleConfirmPassword] = useState('');
  const [receivedOtpHint, setReceivedOtpHint] = useState(null);
  const [resendCountdown, setResendCountdown] = useState(0);

  // Status state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const otpInputsRef = useRef([]);

  // Countdown timer for OTP resend
  useEffect(() => {
    let timer = null;
    if (resendCountdown > 0) {
      timer = setTimeout(() => setResendCountdown(resendCountdown - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [resendCountdown]);

  if (!isOpen) return null;

  // 1. Standard Manual Login or Manual Registration (kept identical)
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
        setSuccessMsg("Registration successful! Initializing security workspace...");
        setTimeout(() => {
          onLoginSuccess(res.user);
          onClose();
        }, 500);
      } else {
        const res = await api.login(username, password);
        setSuccessMsg("Credentials authenticated! Welcome back.");
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

  // 2. Step 1: Open Google account selection
  const handleOpenGoogleSelector = () => {
    setError(null);
    setSuccessMsg(null);
    setViewMode('google_select');
  };

  // 3. Step 2: Confirm selected Google account -> Send OTP
  const handleSendGoogleOtp = async () => {
    const emailToUse = isCustomGoogleEmail
      ? customGoogleEmail.trim().toLowerCase()
      : selectedGoogleEmail.trim().toLowerCase();

    if (!emailToUse || !emailToUse.includes('@')) {
      setError("Please select or enter a valid Google email address.");
      return;
    }

    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      const res = await api.sendOtp(emailToUse, 'email');
      setReceivedOtpHint(res.demo_otp || "123456");
      setResendCountdown(30);
      setGoogleOtpDigits(['', '', '', '', '', '']);
      setViewMode('google_otp');
      setSuccessMsg(`Verification code sent to ${emailToUse}`);

      setTimeout(() => {
        otpInputsRef.current[0]?.focus();
      }, 150);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to dispatch verification code to Google email.");
    } finally {
      setLoading(false);
    }
  };

  // 4. Handle OTP digit typing
  const handleOtpDigitChange = (index, value) => {
    if (value.length > 1) {
      // Paste of 6 digits
      const cleaned = value.replace(/\D/g, '').slice(0, 6);
      if (cleaned.length > 0) {
        const newDigits = [...googleOtpDigits];
        for (let i = 0; i < cleaned.length; i++) {
          newDigits[i] = cleaned[i];
        }
        setGoogleOtpDigits(newDigits);
        const nextIdx = Math.min(cleaned.length, 5);
        otpInputsRef.current[nextIdx]?.focus();
      }
      return;
    }

    const char = value.slice(-1).replace(/\D/g, '');
    const newDigits = [...googleOtpDigits];
    newDigits[index] = char;
    setGoogleOtpDigits(newDigits);

    if (char && index < 5) {
      otpInputsRef.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !googleOtpDigits[index] && index > 0) {
      otpInputsRef.current[index - 1]?.focus();
    }
  };

  // 5. Step 3: Verify Google OTP & Set Password
  const handleVerifyGoogleOtpAndSetPassword = async (e) => {
    e.preventDefault();
    const code = googleOtpDigits.join('').trim();
    if (code.length < 6) {
      setError("Please enter the complete 6-digit verification code.");
      return;
    }

    if (!googleNewPassword || googleNewPassword.length < 4) {
      setError("Please set a password of at least 4 characters for your new account.");
      return;
    }

    if (googleNewPassword !== googleConfirmPassword) {
      setError("Passwords do not match. Please re-enter your new password.");
      return;
    }

    const emailToUse = isCustomGoogleEmail ? customGoogleEmail.trim().toLowerCase() : selectedGoogleEmail;

    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      const derivedName = emailToUse.split('@')[0].replace('.', ' ').replace(/\b\w/g, c => c.toUpperCase());
      const res = await api.verifyOtp(
        emailToUse,
        code,
        googleNewPassword,
        derivedName,
        audience
      );

      setSuccessMsg(`Google account verified! Password set for ${emailToUse}`);
      setTimeout(() => {
        onLoginSuccess(res.user);
        onClose();
      }, 500);
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid or expired OTP code.");
    } finally {
      setLoading(false);
    }
  };

  const activeEmailDisplay = isCustomGoogleEmail ? customGoogleEmail : selectedGoogleEmail;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
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
              {viewMode === 'register'
                ? 'OPERATOR REGISTRATION'
                : viewMode === 'google_select'
                ? 'SELECT GOOGLE ACCOUNT'
                : viewMode === 'google_otp'
                ? 'VERIFY OTP & SET PASSWORD'
                : 'SECURITY SENTRY LOGIN'}
            </h2>
            <p className="text-xs text-slate-400">
              {viewMode === 'register'
                ? 'Manual registration for certified compliance audit access'
                : viewMode === 'google_select'
                ? 'Choose your Google account to receive verification OTP'
                : viewMode === 'google_otp'
                ? `Enter the 6-digit code sent to ${activeEmailDisplay} and set your password`
                : 'Authenticate to manage missions, rules & blockchain proof'}
            </p>
          </div>
        </div>

        {/* Mode Switch Tabs (Only between Sign In and Register) */}
        {(viewMode === 'signin' || viewMode === 'register') && (
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
        )}

        {/* Prominent "Continue with Google" on Sign In & Register views */}
        {(viewMode === 'signin' || viewMode === 'register') && (
          <div className="space-y-3 mb-4">
            <button
              type="button"
              disabled={loading}
              onClick={handleOpenGoogleSelector}
              className="w-full py-2.5 px-4 rounded-xl bg-white hover:bg-slate-100 text-slate-900 font-medium text-xs tracking-wide shadow-md transition flex items-center justify-center gap-2.5 border border-slate-300 disabled:opacity-60"
            >
              <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              <span className="font-semibold">Continue with Google</span>
            </button>

            <div className="relative flex py-1 items-center">
              <div className="flex-grow border-t border-slate-800"></div>
              <span className="flex-shrink mx-3 text-[10px] font-mono text-slate-500 uppercase tracking-widest">
                or {viewMode === 'register' ? 'manual registration' : 'credentials login'}
              </span>
              <div className="flex-grow border-t border-slate-800"></div>
            </div>
          </div>
        )}

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

        {/* ------------------------------------------------------------------ */}
        {/* VIEW 1: GOOGLE ACCOUNT SELECTION                                    */}
        {/* ------------------------------------------------------------------ */}
        {viewMode === 'google_select' && (
          <div className="space-y-4">
            <button
              type="button"
              onClick={() => { setViewMode('signin'); setError(null); }}
              className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-slate-200 transition mb-1"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to standard login</span>
            </button>

            <div className="space-y-2">
              <p className="text-[11px] font-mono text-slate-400">
                CHOOSE AN ACCOUNT TO CONTINUE:
              </p>

              {/* Account 1: Pre-configured Saifullah profile */}
              <div
                onClick={() => {
                  setSelectedGoogleEmail('saifullahpathan49@gmail.com');
                  setIsCustomGoogleEmail(false);
                }}
                className={`p-3 rounded-xl border cursor-pointer transition flex items-center justify-between ${
                  !isCustomGoogleEmail && selectedGoogleEmail === 'saifullahpathan49@gmail.com'
                    ? 'bg-brand-950/50 border-brand-500/60 ring-1 ring-brand-500'
                    : 'bg-[#050811] border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-brand-600 text-white font-bold flex items-center justify-center text-xs">
                    SP
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white">Saifullah Pathan</div>
                    <div className="text-[11px] text-slate-400 font-mono">saifullahpathan49@gmail.com</div>
                  </div>
                </div>
                {!isCustomGoogleEmail && selectedGoogleEmail === 'saifullahpathan49@gmail.com' && (
                  <Check className="w-4 h-4 text-brand-400" />
                )}
              </div>

              {/* Account 2: Auditor account */}
              <div
                onClick={() => {
                  setSelectedGoogleEmail('auditor.sih26155@gmail.com');
                  setIsCustomGoogleEmail(false);
                }}
                className={`p-3 rounded-xl border cursor-pointer transition flex items-center justify-between ${
                  !isCustomGoogleEmail && selectedGoogleEmail === 'auditor.sih26155@gmail.com'
                    ? 'bg-brand-950/50 border-brand-500/60 ring-1 ring-brand-500'
                    : 'bg-[#050811] border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-cyan-600 text-white font-bold flex items-center justify-center text-xs">
                    CA
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white">Compliance Auditor (NTRO)</div>
                    <div className="text-[11px] text-slate-400 font-mono">auditor.sih26155@gmail.com</div>
                  </div>
                </div>
                {!isCustomGoogleEmail && selectedGoogleEmail === 'auditor.sih26155@gmail.com' && (
                  <Check className="w-4 h-4 text-brand-400" />
                )}
              </div>

              {/* Account 3: Use another custom Google email */}
              <div
                onClick={() => setIsCustomGoogleEmail(true)}
                className={`p-3 rounded-xl border cursor-pointer transition ${
                  isCustomGoogleEmail
                    ? 'bg-brand-950/50 border-brand-500/60 ring-1 ring-brand-500'
                    : 'bg-[#050811] border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-slate-800 text-slate-300 font-bold flex items-center justify-center text-xs">
                      +
                    </div>
                    <div className="text-xs font-bold text-white">Use another Google Account</div>
                  </div>
                  {isCustomGoogleEmail && <Check className="w-4 h-4 text-brand-400" />}
                </div>

                {isCustomGoogleEmail && (
                  <div className="mt-2">
                    <input
                      type="email"
                      autoFocus
                      required
                      value={customGoogleEmail}
                      onChange={(e) => setCustomGoogleEmail(e.target.value)}
                      placeholder="your.email@gmail.com"
                      className="w-full bg-[#03060d] border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                    />
                  </div>
                )}
              </div>
            </div>

            <p className="text-[10px] text-slate-500">
              Clicking continue will send a 6-digit verification code to the selected email to verify identity and set your password.
            </p>

            <button
              type="button"
              disabled={loading || (isCustomGoogleEmail && !customGoogleEmail.includes('@'))}
              onClick={handleSendGoogleOtp}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white font-mono font-bold text-xs tracking-wide shadow-lg shadow-amber-500/25 transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <span>DISPATCHING VERIFICATION OTP...</span>
              ) : (
                <>
                  <span>CONTINUE & SEND OTP</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* VIEW 2: GOOGLE OTP VERIFICATION & PASSWORD SETUP                   */}
        {/* ------------------------------------------------------------------ */}
        {viewMode === 'google_otp' && (
          <form onSubmit={handleVerifyGoogleOtpAndSetPassword} className="space-y-4">
            <div className="flex items-center justify-between text-xs font-mono">
              <button
                type="button"
                onClick={() => { setViewMode('google_select'); setError(null); }}
                className="inline-flex items-center gap-1 text-slate-400 hover:text-white"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Change Email</span>
              </button>
              <span className="text-amber-300 font-bold">{activeEmailDisplay}</span>
            </div>

            {/* Simulated Delivery Banner (painless for demo & hackathon evaluation) */}
            {receivedOtpHint && (
              <div className="p-2.5 rounded-xl bg-amber-950/40 border border-amber-500/40 flex items-center justify-between text-xs font-mono text-amber-200">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>OTP Code: <span className="font-bold text-white tracking-widest">{receivedOtpHint}</span></span>
                </div>
                <button
                  type="button"
                  onClick={() => setGoogleOtpDigits(receivedOtpHint.split('').slice(0, 6))}
                  className="px-2 py-0.5 rounded bg-amber-500/20 hover:bg-amber-500/30 text-[10px] text-amber-300 border border-amber-400/40 transition"
                >
                  Auto-fill
                </button>
              </div>
            )}

            {/* 6 Digit Input Boxes */}
            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-2 text-center">
                ENTER 6-DIGIT VERIFICATION CODE:
              </label>
              <div className="flex justify-between gap-2 max-w-xs mx-auto">
                {googleOtpDigits.map((digit, idx) => (
                  <input
                    key={idx}
                    ref={(el) => (otpInputsRef.current[idx] = el)}
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    value={digit}
                    onChange={(e) => handleOtpDigitChange(idx, e.target.value)}
                    onKeyDown={(e) => handleOtpKeyDown(idx, e)}
                    className="w-10 h-12 text-center text-lg font-mono font-bold bg-[#050811] border border-slate-700 rounded-xl text-white focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 transition"
                  />
                ))}
              </div>
            </div>

            {/* Resend OTP */}
            <div className="text-center text-xs font-mono text-slate-500">
              {resendCountdown > 0 ? (
                <span>Resend code in {resendCountdown}s</span>
              ) : (
                <button
                  type="button"
                  onClick={handleSendGoogleOtp}
                  className="text-amber-400 hover:text-amber-300 inline-flex items-center gap-1"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Resend Verification Code</span>
                </button>
              )}
            </div>

            {/* Set Password Inputs */}
            <div className="space-y-3 pt-2 border-t border-slate-800/80">
              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">
                  SET SECURITY PASSPHRASE / PASSWORD:
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                  <input
                    type="password"
                    required
                    value={googleNewPassword}
                    onChange={(e) => setGoogleNewPassword(e.target.value)}
                    placeholder="Create your password (min 4 chars)"
                    className="w-full bg-[#050811] border border-slate-700 rounded-xl pl-9 pr-4 py-2.5 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">
                  CONFIRM PASSPHRASE:
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                  <input
                    type="password"
                    required
                    value={googleConfirmPassword}
                    onChange={(e) => setGoogleConfirmPassword(e.target.value)}
                    placeholder="Re-enter your password"
                    className="w-full bg-[#050811] border border-slate-700 rounded-xl pl-9 pr-4 py-2.5 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || googleOtpDigits.join('').length < 6 || !googleNewPassword}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white font-mono font-bold text-xs tracking-wide shadow-lg shadow-amber-500/25 transition disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
            >
              {loading ? (
                <span>VERIFYING OTP & SETTING CREDENTIALS...</span>
              ) : (
                <>
                  <KeyRound className="w-4 h-4" />
                  <span>VERIFY OTP, SET PASSWORD & ENTER</span>
                </>
              )}
            </button>
          </form>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* VIEW 3: MANUAL SIGN IN & MANUAL REGISTER (IDENTICAL & PRESERVED)   */}
        {/* ------------------------------------------------------------------ */}
        {(viewMode === 'signin' || viewMode === 'register') && (
          <form onSubmit={handleManualAuth} className="space-y-4">
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
                <span>VERIFYING CREDENTIALS...</span>
              ) : (
                <>
                  <KeyRound className="w-4 h-4" />
                  <span>{viewMode === 'register' ? 'REGISTER & ENTER AUDITOR' : 'AUTHENTICATE & ENTER'}</span>
                </>
              )}
            </button>
          </form>
        )}
      </motion.div>
    </div>
  );
}
