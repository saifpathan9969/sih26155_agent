import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Cpu, Terminal, Radio, Server, CheckCircle2, Lock, Zap } from 'lucide-react';

export default function CyberLoadingOverlay({ isVisible, goal, onCancel }) {
  const [progress, setProgress] = useState(0);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const steps = [
    { title: "DISCOVERING NETWORK CONFIGURATIONS", sub: "Scanning uploaded assets for Cisco, Juniper, Fortinet", icon: Server },
    { title: "FINGERPRINTING VENDOR SIGNATURES", sub: "Classifying OS families & calculating confidence scores", icon: Cpu },
    { title: "NORMALIZING TO UNIVERSAL SECURITY BASELINE", sub: "Populating Pydantic v2 schema with line provenance", icon: Terminal },
    { title: "EVALUATING 20 DETERMINISTIC COMPLIANCE RULES", sub: "Zero AI hallucination: strict deterministic evaluation", icon: Shield },
    { title: "CLUSTERING UNKNOWN SYNTAX (REFLECTION)", sub: "Grouping repeated unmapped patterns across 3 Juniper devices", icon: Zap },
    { title: "GENERATING REPORT & BLOCKCHAIN SEAL", sub: "Computing SHA-256 hash & committing block to ledger", icon: Lock },
  ];

  useEffect(() => {
    if (!isVisible) {
      setProgress(0);
      setCurrentStepIndex(0);
      return;
    }

    // Smooth cyber progress animation over ~3.5 seconds
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        const next = prev + 2.5;
        const stepIdx = Math.min(steps.length - 1, Math.floor((next / 100) * steps.length));
        setCurrentStepIndex(stepIdx);
        return next;
      });
    }, 85);

    return () => clearInterval(interval);
  }, [isVisible]);

  if (!isVisible) return null;

  const currentStep = steps[currentStepIndex] || steps[0];
  const StepIcon = currentStep.icon;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-[#040711]/90 backdrop-blur-xl flex items-center justify-center p-4 select-none"
      >
        {/* Subtle Cyber Scanline Overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-brand-500/5 to-transparent h-24 w-full pointer-events-none animate-scanline" />

        <motion.div
          initial={{ scale: 0.9, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.9, y: 20 }}
          transition={{ type: 'spring', stiffness: 350, damping: 25 }}
          className="glass-panel rounded-3xl p-8 max-w-xl w-full border border-brand-500/30 shadow-2xl relative overflow-hidden bg-gradient-to-b from-slate-900/95 via-navy-850 to-slate-950/95"
        >
          {/* Top Radial Glow */}
          <div className="absolute top-0 right-1/2 translate-x-1/2 w-64 h-32 bg-brand-500/15 rounded-full blur-3xl pointer-events-none" />

          {/* Radar Scanner Graphic */}
          <div className="relative w-36 h-36 mx-auto mb-6 flex items-center justify-center">
            {/* Outer Concentric Rings */}
            <div className="absolute inset-0 rounded-full border border-brand-500/20" />
            <div className="absolute inset-3 rounded-full border border-brand-500/30 border-dashed" />
            <div className="absolute inset-7 rounded-full border border-brand-500/40" />
            <div className="absolute inset-11 rounded-full border border-brand-500/20" />

            {/* Crosshairs */}
            <div className="absolute w-full h-[1px] bg-brand-500/20" />
            <div className="absolute h-full w-[1px] bg-brand-500/20" />

            {/* Rotating Radar Sweep */}
            <div className="absolute inset-0 rounded-full overflow-hidden animate-radar pointer-events-none">
              <div className="w-1/2 h-1/2 bg-gradient-to-br from-brand-400/40 via-brand-500/10 to-transparent origin-bottom-right" />
            </div>

            {/* Center Core Pulse */}
            <div className="relative z-10 w-12 h-12 rounded-full bg-brand-950 border border-brand-400 flex items-center justify-center shadow-lg shadow-brand-500/50">
              <StepIcon className="w-6 h-6 text-brand-300 animate-pulse" />
            </div>

            {/* Blinking Targets */}
            <span className="absolute top-4 left-6 w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span className="absolute bottom-6 right-8 w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
            <span className="absolute top-8 right-6 w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
          </div>

          {/* Header Info */}
          <div className="text-center space-y-1.5">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-950/80 border border-brand-500/40 text-[11px] font-mono text-brand-300">
              <Radio className="w-3 h-3 text-brand-400 animate-spin" />
              <span>AUTONOMOUS AUDIT PIPELINE ACTIVE</span>
            </div>
            <h3 className="text-lg font-bold font-mono text-white tracking-wide">
              {currentStep.title}
            </h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto font-sans">
              {currentStep.sub}
            </p>
          </div>

          {/* Progress Bar with Percentage */}
          <div className="mt-6 space-y-2 font-mono">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">
                STAGE {currentStepIndex + 1} OF {steps.length}
              </span>
              <span className="text-brand-300 font-bold">{Math.round(progress)}%</span>
            </div>

            <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden border border-slate-800 p-0.5">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-brand-600 via-brand-400 to-cyan-300 shadow-lg shadow-brand-500/50"
                style={{ width: `${progress}%` }}
                transition={{ duration: 0.1 }}
              />
            </div>
          </div>

          {/* Real-time Telemetry Readout */}
          <div className="grid grid-cols-3 gap-2 mt-6 font-mono text-center text-[10px] bg-slate-950/80 p-3 rounded-xl border border-slate-800">
            <div>
              <span className="text-slate-500 block">DEVICES</span>
              <span className="text-white font-bold">6 Scanned</span>
            </div>
            <div>
              <span className="text-slate-500 block">CIS RULES</span>
              <span className="text-brand-400 font-bold">20 Checked</span>
            </div>
            <div>
              <span className="text-slate-500 block">INTEGRITY</span>
              <span className="text-emerald-400 font-bold">SHA-256</span>
            </div>
          </div>

          {goal && (
            <div className="mt-4 text-center">
              <span className="text-[11px] font-mono text-slate-500 truncate max-w-full block">
                Mission Goal: "{goal}"
              </span>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
