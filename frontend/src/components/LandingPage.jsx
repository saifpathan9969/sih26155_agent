import React from 'react';
import { motion } from 'framer-motion';
import {
  Shield, Play, Sparkles, Terminal, ArrowRight, Server,
  Lock, CheckCircle2, AlertTriangle, Cpu, Layers,
  ShieldAlert, Database, UserCheck, ShieldCheck
} from 'lucide-react';
import AnimatedCounter from './AnimatedCounter';

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

  const metrics = [
    { label: 'SUPPORTED PLATFORMS', value: 'Multi-Vendor', isNumber: false, sub: 'Cisco, Juniper, Fortinet, SOHO', color: 'text-white' },
    { label: 'EVALUATED RULES', value: 20, isNumber: true, suffix: '+ Checks', sub: 'CIS Benchmarks & SOHO Wi-Fi', color: 'text-brand-400' },
    { label: 'DECISION ACCURACY', value: 100, isNumber: true, suffix: '%', sub: 'Deterministic Enforcement', color: 'text-emerald-400' },
    { label: 'TAMPER DETECTION', value: 'Instant', isNumber: false, sub: 'SHA-256 Blockchain Ledger', color: 'text-purple-400' },
  ];

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-12 max-w-5xl mx-auto py-4 relative"
    >
      {/* Floating Ambient Glowing Background Orbs (Master Animation Engine) */}
      <div className="ambient-orb ambient-orb-cyan w-80 h-80 -top-10 -left-20" />
      <div className="ambient-orb ambient-orb-purple w-96 h-96 -bottom-10 -right-20" />

      {/* Hero Section */}
      <motion.section variants={itemVariants} className="relative overflow-hidden pt-6 pb-6">
        {/* Glowing Background Radial Accents */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[350px] bg-gradient-to-tr from-brand-600/20 via-purple-600/15 to-emerald-500/15 rounded-full blur-[110px] pointer-events-none animate-pulse-subtle" />

        <div className="text-center space-y-6 relative z-10">
          {/* Top Pill Badge with Scale In Bounce Physics */}
          <div className="inline-block animate-scale-bounce">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-panel border border-brand-500/30 text-xs font-mono text-brand-300 shadow-lg shadow-brand-500/10">
              <span className="w-2 h-2 rounded-full bg-brand-400 animate-ping" />
              <span className="font-semibold">SIH26155</span>
              <span className="text-slate-500">|</span>
              <span>Autonomous Multi-Vendor Network Compliance Auditor</span>
              <Sparkles className="w-3.5 h-3.5 text-brand-400 ml-0.5 animate-spin-smooth" style={{ animationDuration: '6s' }} />
            </div>
          </div>

          {/* Main Hero Heading with Cyber Shimmer */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black font-mono tracking-tight text-white max-w-4xl mx-auto leading-[1.12]">
            Deterministic Network Security with{' '}
            <span className="cyber-shimmer-text font-black">
              Zero Hallucination
            </span>
          </h1>

          {/* Subtitle / Core Principle */}
          <p className="text-sm sm:text-base text-slate-300 max-w-2xl mx-auto leading-relaxed animate-fade-in-up stagger-2">
            Engineered for enterprise defence associations, government infrastructure, and small business networks.
            AI parses unknown syntax into canonical baselines while deterministic engines decide PASS/FAIL verdicts sealed on chain.
          </p>

          {/* Call to Action Button with Hover Elevation and Glow */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <motion.button
              whileHover={{ scale: 1.04, boxShadow: '0 0 35px rgba(14, 165, 233, 0.45)' }}
              whileTap={{ scale: 0.97 }}
              onClick={onGetStarted}
              className="px-10 py-4 rounded-2xl bg-gradient-to-r from-brand-600 via-cyan-500 to-emerald-500 text-white font-mono font-bold text-base tracking-wide shadow-2xl shadow-brand-500/30 flex items-center gap-3 transition cursor-pointer"
            >
              <UserCheck className="w-5 h-5 card-icon-bounce" />
              <span>GET STARTED — LOGIN & ENTER AUDITOR</span>
              <ArrowRight className="w-5 h-5" />
            </motion.button>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            Access credentials or register a security operator profile to launch full mission controls.
          </p>
        </div>
      </motion.section>

      {/* Metrics Strip with Animated Counter & Staggered Hover Cards */}
      <motion.section variants={itemVariants} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map((metric, idx) => (
          <div
            key={idx}
            className={`glass-panel p-5 rounded-xl border border-slate-800/80 interactive-hover-card animate-fade-in-up stagger-${idx + 1}`}
          >
            <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">{metric.label}</div>
            <div className={`text-2xl font-black font-mono mt-1 ${metric.color}`}>
              {metric.isNumber ? (
                <AnimatedCounter target={metric.value} suffix={metric.suffix} duration={1600} />
              ) : (
                metric.value
              )}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">{metric.sub}</div>
          </div>
        ))}
      </motion.section>

      {/* Three Pillars Overview with Interactive Hover Elevation & Icon Spring */}
      <motion.section variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs font-mono">
        <div className="bg-slate-950/70 p-5 rounded-2xl border border-brand-500/20 space-y-3 interactive-hover-card animate-fade-in-up stagger-1">
          <div className="text-brand-400 font-bold uppercase tracking-wider text-xs flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-brand-500/10 card-icon-bounce">
              <Cpu className="w-4 h-4" />
            </div>
            <span>1. Vector AI Ingestion</span>
          </div>
          <p className="text-slate-300 font-sans text-xs leading-relaxed">
            Extracts unknown FortiOS CLI statements (`config system admin`) and queries historical patterns with TF-IDF cosine similarity.
          </p>
        </div>

        <div className="bg-slate-950/70 p-5 rounded-2xl border border-emerald-500/20 space-y-3 interactive-hover-card animate-fade-in-up stagger-2">
          <div className="text-emerald-400 font-bold uppercase tracking-wider text-xs flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-emerald-500/10 card-icon-bounce">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <span>2. Dual Audience Defense</span>
          </div>
          <p className="text-slate-300 font-sans text-xs leading-relaxed">
            Enterprise Mode for CIS defense benchmarks alongside Home/SOHO Mode for Wi-Fi routers with step-by-step fix guides and copy payloads.
          </p>
        </div>

        <div className="bg-slate-950/70 p-5 rounded-2xl border border-purple-500/20 space-y-3 interactive-hover-card animate-fade-in-up stagger-3">
          <div className="text-purple-400 font-bold uppercase tracking-wider text-xs flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-purple-500/10 card-icon-bounce">
              <Lock className="w-4 h-4" />
            </div>
            <span>3. Cryptographic Ledger</span>
          </div>
          <p className="text-slate-300 font-sans text-xs leading-relaxed">
            Every baseline, human override, and final report is signed with SHA-256 blocks making post-audit tampering immediately evident.
          </p>
        </div>
      </motion.section>
    </motion.div>
  );
}
