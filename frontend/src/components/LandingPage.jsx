import React from 'react';
import { motion } from 'framer-motion';
import {
  Shield, Play, Sparkles, Terminal, ArrowRight, Server,
  Lock, CheckCircle2, AlertTriangle, Cpu, Layers,
  ShieldAlert, Database, UserCheck, ShieldCheck
} from 'lucide-react';

export default function LandingPage({
  onGetStarted,
  fixtures = [],
  selectedDevices = [],
  setSelectedDevices,
  onOpenUploadModal,
}) {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.15,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
    },
  };

  // Helper for toggling device in selection
  const handleToggleDevice = (filename) => {
    if (!setSelectedDevices) return;
    if (selectedDevices.includes(filename)) {
      if (selectedDevices.length === 1) return; // keep at least 1
      setSelectedDevices(selectedDevices.filter(f => f !== filename));
    } else {
      setSelectedDevices([...selectedDevices, filename]);
    }
  };

  const handleSelectAll = () => {
    if (!setSelectedDevices) return;
    setSelectedDevices(fixtures.map(f => f.filename));
  };

  const metrics = [
    { label: 'SUPPORTED PLATFORMS', value: 'Multi-Vendor', sub: 'Cisco, Juniper, Fortinet, SOHO', color: 'text-white' },
    { label: 'EVALUATED RULES', value: '20+ Checks', sub: 'CIS Benchmarks & SOHO Wi-Fi', color: 'text-brand-400' },
    { label: 'DECISION ACCURACY', value: '100%', sub: 'Deterministic Enforcement', color: 'text-emerald-400' },
    { label: 'TAMPER DETECTION', value: 'Instant', sub: 'SHA-256 Blockchain Ledger', color: 'text-purple-400' },
  ];

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-12 max-w-5xl mx-auto py-4"
    >
      {/* Hero Section */}
      <motion.section variants={itemVariants} className="relative overflow-hidden pt-6 pb-6">
        {/* Glowing Background Radial Accents */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[320px] bg-gradient-to-tr from-brand-600/15 via-purple-600/10 to-emerald-500/10 rounded-full blur-[110px] pointer-events-none" />

        <div className="text-center space-y-6 relative z-10">
          {/* Top Pill Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-panel border border-brand-500/30 text-xs font-mono text-brand-300 shadow-lg shadow-brand-500/10"
          >
            <span className="w-2 h-2 rounded-full bg-brand-400 animate-ping" />
            <span className="font-semibold">SIH26155</span>
            <span className="text-slate-500">|</span>
            <span>Autonomous Multi-Vendor Network Compliance Auditor</span>
            <Sparkles className="w-3.5 h-3.5 text-brand-400 ml-0.5" />
          </motion.div>

          {/* Main Hero Heading */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black font-mono tracking-tight text-white max-w-4xl mx-auto leading-[1.12]">
            Deterministic Network Security with{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 via-cyan-300 to-emerald-400">
              Zero Hallucination
            </span>
          </h1>

          {/* Subtitle / Core Principle */}
          <p className="text-sm sm:text-base text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Engineered for enterprise defence associations, government infrastructure, and small business networks.
            AI parses unknown syntax into canonical baselines while deterministic engines decide PASS/FAIL verdicts sealed on chain.
          </p>

          {/* STRICT SINGLE CALL TO ACTION BUTTON (LOGIN & GET STARTED) */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <motion.button
              whileHover={{ scale: 1.04, boxShadow: '0 0 35px rgba(14, 165, 233, 0.45)' }}
              whileTap={{ scale: 0.97 }}
              onClick={onGetStarted}
              className="px-10 py-4 rounded-2xl bg-gradient-to-r from-brand-600 via-cyan-500 to-emerald-500 text-white font-mono font-bold text-base tracking-wide shadow-2xl shadow-brand-500/30 flex items-center gap-3 transition"
            >
              <UserCheck className="w-5 h-5" />
              <span>GET STARTED — LOGIN & ENTER AUDITOR</span>
              <ArrowRight className="w-5 h-5" />
            </motion.button>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            Access credentials or register a security operator profile to launch full mission controls.
          </p>
        </div>
      </motion.section>

      {/* Metrics Strip */}
      <motion.section variants={itemVariants} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map((metric, idx) => (
          <div
            key={idx}
            className="glass-panel p-5 rounded-xl border border-slate-800/80 hover:border-slate-700 transition"
          >
            <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">{metric.label}</div>
            <div className={`text-2xl font-black font-mono mt-1 ${metric.color}`}>{metric.value}</div>
            <div className="text-[11px] text-slate-500 mt-0.5">{metric.sub}</div>
          </div>
        ))}
      </motion.section>

      {/* Three Pillars Overview */}
      <motion.section variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs font-mono">
        <div className="bg-slate-950/70 p-5 rounded-2xl border border-brand-500/20 space-y-3">
          <div className="text-brand-400 font-bold uppercase tracking-wider text-xs flex items-center gap-1.5">
            <Cpu className="w-4 h-4" /> 1. Vector AI Ingestion
          </div>
          <p className="text-slate-300 font-sans text-xs leading-relaxed">
            Extracts unknown FortiOS CLI statements (`config system admin`) and queries historical patterns with TF-IDF cosine similarity.
          </p>
        </div>

        <div className="bg-slate-950/70 p-5 rounded-2xl border border-emerald-500/20 space-y-3">
          <div className="text-emerald-400 font-bold uppercase tracking-wider text-xs flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4" /> 2. Dual Audience Defense
          </div>
          <p className="text-slate-300 font-sans text-xs leading-relaxed">
            Enterprise Mode for CIS defense benchmarks alongside Home/SOHO Mode for Wi-Fi routers with step-by-step fix guides and copy payloads.
          </p>
        </div>

        <div className="bg-slate-950/70 p-5 rounded-2xl border border-purple-500/20 space-y-3">
          <div className="text-purple-400 font-bold uppercase tracking-wider text-xs flex items-center gap-1.5">
            <Lock className="w-4 h-4" /> 3. Cryptographic Ledger
          </div>
          <p className="text-slate-300 font-sans text-xs leading-relaxed">
            Every baseline, human override, and final report is signed with SHA-256 blocks making post-audit tampering immediately evident.
          </p>
        </div>
      </motion.section>
    </motion.div>
  );
}
