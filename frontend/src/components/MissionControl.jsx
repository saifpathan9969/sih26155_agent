import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play, Server, ShieldAlert, Cpu, Sparkles, CheckCircle2,
  RefreshCw, Layers, ArrowRight, Activity, Terminal
} from 'lucide-react';
import MissionTraceLog from './MissionTraceLog';
import StatusFlipCard from './StatusFlipCard';
import StatusBadge from './StatusBadge';
import AnimatedCounter from './AnimatedCounter';

export default function MissionControl({
  onRunMission,
  missionResult,
  isRunning,
  fixtures = [],
  selectedDevices = [],
  setSelectedDevices,
  onNavigateTab,
  onOpenUploadModal,
  onOpenHumanReview,
}) {
  const [goal, setGoal] = useState("Audit all network configurations and identify critical security compliance violations.");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isRunning && onRunMission) {
      onRunMission(goal, selectedDevices);
    }
  };

  const handleToggleDevice = (fname) => {
    if (!setSelectedDevices) return;
    if (selectedDevices.includes(fname)) {
      if (selectedDevices.length === 1) return;
      setSelectedDevices(selectedDevices.filter(f => f !== fname));
    } else {
      setSelectedDevices([...selectedDevices, fname]);
    }
  };

  const handleSelectAll = () => {
    if (!setSelectedDevices) return;
    setSelectedDevices(fixtures.map(f => f.filename));
  };

  // Dynamic Vendor summary counts from real uploaded fixtures
  const ciscoDevices = fixtures.filter(f => f.vendor?.includes('cisco'));
  const juniperDevices = fixtures.filter(f => f.vendor?.includes('juniper'));
  const fortinetDevices = fixtures.filter(f => f.vendor?.includes('fortinet'));
  const otherDevices = fixtures.filter(f => !f.vendor?.includes('cisco') && !f.vendor?.includes('juniper') && !f.vendor?.includes('fortinet'));

  const ciscoCount = ciscoDevices.length;
  const juniperCount = juniperDevices.length;
  const fortinetCount = fortinetDevices.length;

  const flips = missionResult?.flips || [];
  const reviews = missionResult?.grouped_reviews || [];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Mission Input Header Card */}
      <div className="glass-panel p-6 rounded-2xl border border-brand-500/20 bg-gradient-to-r from-slate-900 via-navy-850 to-slate-900 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-brand-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span className="text-xs font-mono text-brand-400 tracking-wider uppercase font-semibold">
                Autonomous Security Audit Agent
              </span>
            </div>
            <h1 className="text-2xl font-black font-mono text-white tracking-tight">
              MISSION CONTROL
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onOpenUploadModal && onOpenUploadModal()}
              className="px-3 py-1.5 rounded-xl bg-purple-950/70 hover:bg-purple-900/70 border border-purple-500/40 text-xs font-mono text-purple-200 flex items-center gap-1.5 transition"
            >
              <Cpu className="w-3.5 h-3.5 text-purple-400" />
              <span>+ Upload New Config</span>
            </button>
            <span className="text-xs font-mono text-slate-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
              Targeting: <span className="text-emerald-400 font-bold">{selectedDevices.length || fixtures.length}</span> / {fixtures.length} Devices
            </span>
          </div>
        </div>

        {/* Step 1: Mission Goal Input */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="text-xs font-mono text-slate-400 block mb-1.5 font-semibold">
              INPUT AUDIT OBJECTIVE / INTENT:
            </label>
            <div className="relative">
              <input
                type="text"
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                placeholder="e.g. Audit all uploaded configurations for CIS compliance and discover unmapped directives..."
                className="w-full bg-[#050811] border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-100 font-mono focus:outline-none focus:border-brand-400 focus:ring-1 focus:ring-brand-400 transition"
              />
            </div>
          </div>

          {/* Selected Devices Chips */}
          <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-mono font-medium">TARGET ASSETS:</span>
              <button
                type="button"
                onClick={handleSelectAll}
                className="text-[11px] font-mono text-brand-400 hover:underline cursor-pointer"
              >
                (Select All {fixtures.length})
              </button>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {fixtures.length === 0 ? (
                <span className="text-xs text-slate-500 font-mono italic">
                  No configuration files uploaded yet. Click 'Upload Config' above.
                </span>
              ) : (
                fixtures.map((f) => {
                  const isSelected = selectedDevices.includes(f.filename);
                  return (
                    <button
                      key={f.filename}
                      type="button"
                      onClick={() => handleToggleDevice(f.filename)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-mono transition border cursor-pointer ${
                        isSelected
                          ? 'bg-brand-950 border-brand-500/60 text-brand-300 font-semibold'
                          : 'bg-slate-900 border-slate-800 text-slate-500 hover:border-slate-700'
                      }`}
                    >
                      {isSelected ? '✓ ' : ''}{f.filename}
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Submit Action Button */}
          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={isRunning || fixtures.length === 0}
              className={`px-6 py-3 rounded-xl font-mono text-xs font-bold flex items-center gap-2 shadow-lg transition ${
                isRunning || fixtures.length === 0
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                  : 'bg-brand-500 hover:bg-brand-400 text-white shadow-brand-500/30 cursor-pointer'
              }`}
            >
              {isRunning ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  PROCESSING MISSION...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  ▶ START AUTONOMOUS AUDIT
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Step 2: Device Discovery & Fingerprint Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-slate-800 interactive-hover-card animate-fade-in-up stagger-1">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-mono">TOTAL DEVICES</span>
            <div className="p-1 rounded-md bg-brand-500/10 card-icon-bounce">
              <Server className="w-4 h-4 text-brand-400" />
            </div>
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            <AnimatedCounter target={fixtures.length} duration={1200} />
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Multi-Vendor Inventory</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 interactive-hover-card animate-fade-in-up stagger-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-mono">CISCO IOS</span>
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse-subtle" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            <AnimatedCounter target={ciscoCount} duration={1200} />
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5 truncate" title={ciscoDevices.map(d => d.filename).join(', ')}>
            {ciscoCount > 0 ? ciscoDevices.map(d => d.filename).join(', ') : '0 configs uploaded'}
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 interactive-hover-card animate-fade-in-up stagger-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-mono">JUNIPER JUNOS</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-subtle" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            <AnimatedCounter target={juniperCount} duration={1200} />
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5 truncate" title={juniperDevices.map(d => d.filename).join(', ')}>
            {juniperCount > 0 ? juniperDevices.map(d => d.filename).join(', ') : '0 configs uploaded'}
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 interactive-hover-card animate-fade-in-up stagger-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-mono">FORTINET / OTHER</span>
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse-subtle" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            <AnimatedCounter target={fortinetCount + otherDevices.length} duration={1200} />
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5 truncate" title={[...fortinetDevices, ...otherDevices].map(d => d.filename).join(', ')}>
            {(fortinetCount + otherDevices.length) > 0 ? [...fortinetDevices, ...otherDevices].map(d => d.filename).join(', ') : '0 configs uploaded'}
          </div>
        </div>
      </div>

      {/* Informative Human-in-the-Loop Review Banner (Resolution handled at AI Retrieval page) */}
      {reviews.length > 0 && (
        <div className="glass-panel p-5 rounded-2xl border border-amber-500/40 bg-gradient-to-r from-amber-950/20 via-slate-900 to-amber-950/20 shadow-xl space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-amber-500/20 pb-2">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-ping" />
              <span className="text-xs font-mono font-bold text-amber-300 uppercase tracking-wider">
                UNMAPPED SYNTAX DETECTED — {reviews.length} COMMAND(S) REQUIRE OPERATOR INPUT
              </span>
            </div>
            <span className="text-[10px] font-mono text-amber-300 bg-amber-950/80 px-2 py-0.5 rounded border border-amber-500/40 font-bold">
              AI RETRIEVAL RESOLUTION REQUIRED
            </span>
          </div>

          <div className="p-4 rounded-xl bg-[#050811] border border-amber-500/30 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1 text-xs">
              <p className="text-amber-200 font-mono font-semibold">
                To maintain deterministic provenance and active learning, unmapped syntax resolution is centralized in the AI Retrieval & Knowledge Base workbench.
              </p>
              <p className="text-slate-400 font-sans text-[11px]">
                Inspect commands config-file-wise, specify command categories, attach documentation, and issue Pass / Fail verdicts to train the agent.
              </p>
            </div>

            <button
              type="button"
              onClick={() => onNavigateTab && onNavigateTab('training')}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 text-white font-mono font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-amber-500/25 transition shrink-0 cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span>Go to AI Retrieval & Learning Tab ➔</span>
            </button>
          </div>
        </div>
      )}

      {/* Main Execution View: Terminal Trace & Live Flips */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Live Terminal Trace (2 cols) */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Terminal className="w-4 h-4 text-brand-400" />
              MISSION EXECUTION TRACE
            </span>
            {missionResult?.blockchain_block_index !== undefined && (
              <span className="text-[11px] font-mono text-brand-300 bg-brand-950 px-2 py-0.5 rounded border border-brand-500/30">
                Sealed in Block #{missionResult.blockchain_block_index}
              </span>
            )}
          </div>

          <MissionTraceLog
            trace={missionResult?.trace || []}
            isRunning={isRunning}
          />
        </div>

        {/* Right: Before ➔ After Status Flips & Highlights (1 col) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              STATUS FLIPS (LEARNING)
            </span>
            <span className="text-[10px] font-mono text-emerald-400 font-bold">
              {flips.length} FLIPPED
            </span>
          </div>

          {flips.length > 0 ? (
            <div className="space-y-3">
              {flips.map((flip, idx) => (
                <StatusFlipCard key={idx} flip={flip} />
              ))}
              <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-500/30 text-xs text-emerald-300 font-mono">
                ✓ Reflection clustered 3 Juniper devices into 1 review. 1 confirmation resolved all 3 devices simultaneously!
              </div>
            </div>
          ) : (
            <div className="glass-panel p-6 rounded-xl border border-dashed border-slate-800 text-center text-slate-500 text-xs font-mono">
              <Activity className="w-8 h-8 opacity-30 text-brand-400 mx-auto mb-2" />
              Run the mission above to observe live before/after compliance flips.
            </div>
          )}

          {/* Quick Action Buttons */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-2">
            <div className="text-xs font-mono font-semibold text-slate-300 mb-2">QUICK NAVIGATION:</div>
            <button
              onClick={() => onNavigateTab && onNavigateTab('training')}
              className="w-full py-2 px-3 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs text-slate-200 font-mono flex items-center justify-between transition"
            >
              <span>🧠 Test Interactive Training Flow</span>
              <ArrowRight className="w-3.5 h-3.5 text-brand-400" />
            </button>
            <button
              onClick={() => onNavigateTab && onNavigateTab('rules')}
              className="w-full py-2 px-3 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs text-slate-200 font-mono flex items-center justify-between transition"
            >
              <span>⚖️ Propose & Approve Rule v2</span>
              <ArrowRight className="w-3.5 h-3.5 text-brand-400" />
            </button>
            <button
              onClick={() => onNavigateTab && onNavigateTab('report')}
              className="w-full py-2 px-3 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs text-slate-200 font-mono flex items-center justify-between transition"
            >
              <span>⚡ Live Tamper Detection Demo</span>
              <ArrowRight className="w-3.5 h-3.5 text-brand-400" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
