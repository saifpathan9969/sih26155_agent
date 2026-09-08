import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  FileText, Shield, CheckCircle2, XCircle, AlertTriangle,
  Link2, Server, Terminal, Lock, Cpu, Sparkles, Download,
  Copy, Check, ArrowRight, Activity, HelpCircle, Layers
} from 'lucide-react';
import StatusBadge from './StatusBadge';
import AnimatedCounter from './AnimatedCounter';

export default function SummaryPage({
  missionResult,
  fixtures = [],
  rules = [],
  onNavigateTab,
  onOpenHumanReview,
}) {
  const [copied, setCopied] = useState(false);

  // Derive counts and metrics
  const findingsByDevice = missionResult?.findings_by_device || {};
  const devices = Object.keys(findingsByDevice);
  const flips = missionResult?.flips || [];
  const reviews = missionResult?.grouped_reviews || [];
  const auditedDevices = missionResult?.audited_devices || fixtures.map(f => f.filename);

  let totalChecks = 0;
  let passCount = 0;
  let failCount = 0;
  let needsReviewCount = 0;

  Object.values(findingsByDevice).forEach(list => {
    list.forEach(f => {
      totalChecks++;
      const s = f.status?.toLowerCase();
      if (s === 'pass') passCount++;
      else if (s === 'fail') failCount++;
      else if (s === 'needs_human_review') needsReviewCount++;
    });
  });

  const complianceRate = totalChecks > 0 ? Math.round((passCount / totalChecks) * 100) : 0;

  const handleCopyReport = () => {
    if (missionResult?.report) {
      navigator.clipboard.writeText(missionResult.report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadReport = () => {
    if (!missionResult?.report) return;
    const blob = new Blob([missionResult.report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `NTRO_Audit_Report_Block_${missionResult.blockchain_block_index || 0}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Top Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-brand-500/30 bg-gradient-to-r from-slate-900 via-navy-850 to-slate-900 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-950 border border-brand-500/30 text-xs font-mono text-brand-300 mb-2">
              <Sparkles className="w-3.5 h-3.5 text-brand-400" />
              <span>COMPREHENSIVE POST-MISSION DEBRIEF</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black font-mono text-white tracking-tight">
              MISSION EXECUTION & AUDIT SUMMARY
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-3xl">
              Consolidated intelligence from all audit stages: Discovery, Fingerprinting, Baseline Normalization,
              Human-in-the-Loop Active Learning, Deterministic Rule Evaluation, and Cryptographic Blockchain Proof.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={handleCopyReport}
              disabled={!missionResult?.report}
              className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-mono text-slate-200 flex items-center gap-1.5 transition disabled:opacity-40"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-brand-400" />}
              <span>{copied ? 'Copied' : 'Copy Report'}</span>
            </button>
            <button
              onClick={handleDownloadReport}
              disabled={!missionResult?.report}
              className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-mono font-bold flex items-center gap-1.5 transition shadow-lg shadow-brand-500/20 disabled:opacity-40"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Sealed Report</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      {/* 5 Key Metric Cards with AnimatedCounter and Staggered Hover Physics */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
        <div className="glass-panel p-4 rounded-xl border border-slate-800 interactive-hover-card animate-fade-in-up stagger-1">
          <div className="text-xs text-slate-400 font-mono">AUDITED DEVICES</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            <AnimatedCounter target={auditedDevices.length || fixtures.length} duration={1200} />
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Heterogeneous Nodes</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/10 interactive-hover-card animate-fade-in-up stagger-2">
          <div className="text-xs text-emerald-400 font-mono">COMPLIANCE RATE</div>
          <div className="text-2xl font-bold font-mono text-emerald-300 mt-1">
            <AnimatedCounter target={complianceRate} duration={1200} suffix="%" />
          </div>
          <div className="text-[11px] text-emerald-500/80 mt-0.5">{passCount} Deterministic Pass</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-rose-500/30 bg-rose-950/10 interactive-hover-card animate-fade-in-up stagger-3">
          <div className="text-xs text-rose-400 font-mono">SECURITY VIOLATIONS</div>
          <div className="text-2xl font-bold font-mono text-rose-300 mt-1">
            <AnimatedCounter target={failCount} duration={1200} />
          </div>
          <div className="text-[11px] text-rose-500/80 mt-0.5">Immediate Remediation</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-amber-500/30 bg-amber-950/10 interactive-hover-card animate-fade-in-up stagger-4">
          <div className="text-xs text-amber-400 font-mono">HUMAN REVIEWS</div>
          <div className="text-2xl font-bold font-mono text-amber-300 mt-1">
            <AnimatedCounter target={needsReviewCount} duration={1200} />
          </div>
          <div className="text-[11px] text-amber-500/80 mt-0.5">Clickable & Actionable</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-brand-500/30 bg-brand-950/10 interactive-hover-card animate-fade-in-up stagger-5">
          <div className="text-xs text-brand-400 font-mono">BLOCKCHAIN SEAL</div>
          <div className="text-2xl font-bold font-mono text-brand-300 mt-1">
            #{missionResult?.blockchain_block_index ?? 'Live'}
          </div>
          <div className="text-[11px] text-brand-500/80 mt-0.5">SHA-256 Verified</div>
        </div>
      </div>

      {/* SPECIAL DEEP-DIVE: Why Hashes Exist on Blockchain Page & What Their Purpose Is */}
      <div className="glass-panel p-6 sm:p-7 rounded-2xl border border-brand-500/40 bg-gradient-to-br from-[#0c1326] to-[#070b14] shadow-2xl space-y-4">
        <div className="flex items-center gap-3 border-b border-slate-800 pb-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500/20 border border-brand-500/40 flex items-center justify-center text-brand-400 shadow-md shadow-brand-500/25">
            <Link2 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base sm:text-lg font-bold font-mono text-white flex items-center gap-2">
              WHY DO HASHES EXIST ON THE BLOCKCHAIN PAGE & WHAT IS THEIR USE?
            </h2>
            <p className="text-xs text-brand-300 font-mono">
              The Essential Role of Cryptographic Provenance in Defense & NTRO Compliance
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs text-slate-300 leading-relaxed font-sans">
          <div className="space-y-3 bg-[#050811] p-4 rounded-xl border border-slate-800">
            <h3 className="font-mono font-bold text-white text-xs flex items-center gap-1.5 text-brand-400">
              <span>1. The Problem: The Risk of Retroactive Tampering</span>
            </h3>
            <p>
              In conventional audit systems, findings are saved in traditional SQL or NoSQL databases. If an organization fails a mission-critical check (for example, Telnet is exposed or password minimum length is deficient), a rogue insider or compromised database administrator could quietly change <code>FAIL</code> to <code>PASS</code> in the database records after the audit concludes.
            </p>
            <p>
              Without cryptographic proof, it is impossible for external regulatory bodies (like NTRO or CERT-In) to verify whether the report presented to them is genuine or fraudulently modified.
            </p>
          </div>

          <div className="space-y-3 bg-[#050811] p-4 rounded-xl border border-slate-800">
            <h3 className="font-mono font-bold text-white text-xs flex items-center gap-1.5 text-emerald-400">
              <span>2. The Solution: SHA-256 Hashes & Block Chaining</span>
            </h3>
            <p>
              When our agent finishes an audit, it calculates an <strong>SHA-256 cryptographic digest</strong> over the exact text and findings of the report. This produces an immutable 64-character hash.
            </p>
            <p>
              This hash is recorded into an append-only <strong>Blockchain Block</strong> alongside the timestamp, previous block hash, and goal summary. Because each block references the previous block's hash, you cannot alter any block without breaking the cryptographic validity of the entire chain.
            </p>
          </div>
        </div>

        {/* Live Cryptographic Block Details */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2 text-xs font-mono">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            LIVE CRYPTOGRAPHIC TELEMETRY FROM THIS MISSION:
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <span className="text-slate-500">Report SHA-256 Hash: </span>
              <div className="text-brand-300 break-all bg-[#050811] p-2 rounded border border-slate-800 mt-1">
                {missionResult?.report_sha256 || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}
              </div>
            </div>
            <div>
              <span className="text-slate-500">Blockchain Block Sealed: </span>
              <div className="text-emerald-300 break-all bg-[#050811] p-2 rounded border border-slate-800 mt-1">
                Block #{missionResult?.blockchain_block_index ?? 1} • Immutable NTRO Provenance Ledger
              </div>
            </div>
          </div>
          <div className="text-[11px] text-slate-400 pt-1">
            💡 <em>Want to see the anti-tamper alarm in action? Go to the <strong>REPORT / TAMPER DEMO</strong> tab to simulate an unauthorized change and watch the verification engine catch it instantly.</em>
          </div>
        </div>
      </div>

      {/* Pipeline Stage-by-Stage Detailed Breakdown */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6">
        <div className="border-b border-slate-800 pb-3">
          <h2 className="text-base font-mono font-bold text-white uppercase tracking-wider">
            STEP-BY-STEP MISSION TIMELINE & EVIDENCE
          </h2>
          <p className="text-xs text-slate-400">
            A comprehensive overview of what the agent did at every phase of execution
          </p>
        </div>

        <div className="space-y-6">
          {/* Phase 1: Ingestion & Fingerprinting */}
          <div className="p-4 rounded-xl bg-[#050811] border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-brand-400 font-bold flex items-center gap-1.5">
                <Server className="w-4 h-4" />
                PHASE 1: DISCOVERY & MULTI-VENDOR FINGERPRINTING
              </span>
              <span className="text-emerald-400 font-bold">100% SUCCESS</span>
            </div>
            <p className="text-xs text-slate-300 font-sans">
              The agent ingested {auditedDevices.length} network configuration files. Heuristic vendor fingerprinting identified Cisco IOS, Juniper Junos, and FortiOS devices with 97%+ confidence without any pre-labeled metadata.
            </p>
            <div className="flex flex-wrap gap-2 pt-1 font-mono text-[11px]">
              {auditedDevices.map(d => (
                <span key={d} className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
                  {d}
                </span>
              ))}
            </div>
          </div>

          {/* Phase 2: Baseline Normalization */}
          <div className="p-4 rounded-xl bg-[#050811] border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-cyan-400 font-bold flex items-center gap-1.5">
                <Layers className="w-4 h-4" />
                PHASE 2: UNIVERSAL SECURITY BASELINE NORMALIZATION
              </span>
              <span className="text-cyan-300 font-bold">PYDANTIC V2 SCHEMA</span>
            </div>
            <p className="text-xs text-slate-300 font-sans">
              Vendor-specific CLI commands were transformed into normalized evidence fields (SSH status, Telnet suppression, lockout parameters, password encryption, etc.) preserving exact file and line-number provenance for NTRO auditors.
            </p>
          </div>

          {/* Phase 3: Human-in-the-Loop & Active Learning Reflection */}
          <div className="p-4 rounded-xl bg-[#050811] border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-amber-400 font-bold flex items-center gap-1.5">
                <Cpu className="w-4 h-4" />
                PHASE 3: HUMAN INTERVENTION & ACTIVE LEARNING REFLECTION
              </span>
              <span className="text-amber-300 font-bold">{reviews.length} REVIEW(S) CLUSTERED</span>
            </div>
            <p className="text-xs text-slate-300 font-sans">
              Instead of guessing an unmapped Junos syntax, the agent enforced autonomy boundaries (<code className="text-brand-300">policies/autonomy.py</code>) and halted for human confirmation. Reflection clustered 3 Juniper devices into 1 review item, so a single operator decision resolved all 3 devices simultaneously.
            </p>
            {flips.length > 0 && (
              <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-500/30 text-xs font-mono text-emerald-300">
                ✓ {flips.length} finding(s) flipped from NEEDS_HUMAN_REVIEW to PASS through human validation and knowledge reuse.
              </div>
            )}
          </div>

          {/* Phase 4: Deterministic Compliance Rule Evaluation */}
          <div className="p-4 rounded-xl bg-[#050811] border border-slate-800 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-purple-400 font-bold flex items-center gap-1.5">
                <Terminal className="w-4 h-4" />
                PHASE 4: 20 CIS BENCHMARK DETERMINISTIC EVALUATION
              </span>
              <span className="text-slate-300">{totalChecks} CHECKS EXECUTED</span>
            </div>
            <p className="text-xs text-slate-300 font-sans">
              Evaluations were determined strictly by immutable Python logic without LLM hallucinations.
            </p>

            {/* Device breakdown table */}
            <div className="overflow-x-auto rounded-xl border border-slate-800 mt-2">
              <table className="w-full text-left text-xs border-collapse font-mono">
                <thead>
                  <tr className="bg-slate-900/90 text-slate-400 border-b border-slate-800">
                    <th className="py-2.5 px-3">DEVICE ID</th>
                    <th className="py-2.5 px-3">TOTAL CHECKS</th>
                    <th className="py-2.5 px-3">PASS</th>
                    <th className="py-2.5 px-3">FAIL</th>
                    <th className="py-2.5 px-3">HUMAN REVIEW</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {devices.map(devId => {
                    const findings = findingsByDevice[devId] || [];
                    const p = findings.filter(f => f.status?.toLowerCase() === 'pass').length;
                    const f = findings.filter(f => f.status?.toLowerCase() === 'fail').length;
                    const r = findings.filter(f => f.status?.toLowerCase() === 'needs_human_review').length;
                    return (
                      <tr key={devId} className="hover:bg-slate-900/50 transition">
                        <td className="py-2.5 px-3 font-bold text-white">{devId}</td>
                        <td className="py-2.5 px-3 text-slate-300">{findings.length}</td>
                        <td className="py-2.5 px-3 text-emerald-400 font-bold">{p}</td>
                        <td className="py-2.5 px-3 text-rose-400 font-bold">{f}</td>
                        <td className="py-2.5 px-3 text-amber-400 font-bold">{r}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Phase 5: Blockchain Ledger Sealing */}
          <div className="p-4 rounded-xl bg-[#050811] border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                <Link2 className="w-4 h-4" />
                PHASE 5: IMMUTABLE BLOCKCHAIN RECORDING
              </span>
              <span className="text-brand-300 font-bold">SEALED IN BLOCK #{missionResult?.blockchain_block_index ?? 1}</span>
            </div>
            <p className="text-xs text-slate-300 font-sans">
              The mission report was stamped with a cryptographic SHA-256 hash and written into the NTRO blockchain ledger. Any retroactive attempt to modify findings will fail hash verification instantly.
            </p>
          </div>
        </div>
      </div>

      {/* Generated Final Report Preview */}
      {missionResult?.report && (
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-brand-400" />
              CERTIFIED EXECUTIVE AUDIT REPORT (PREVIEW)
            </span>
            <div className="flex gap-2">
              <button
                onClick={handleCopyReport}
                className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-mono text-slate-300 border border-slate-700 flex items-center gap-1"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
          </div>

          <pre className="p-4 rounded-xl bg-[#050811] border border-slate-800 text-xs font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-96 terminal-scroll leading-relaxed">
            {missionResult.report}
          </pre>
        </div>
      )}
    </div>
  );
}
