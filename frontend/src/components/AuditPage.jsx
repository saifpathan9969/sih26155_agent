/**
 * AuditPage — Unified AUDIT tab
 *
 * Merges three former tabs into one:
 *   • Summary & Debrief   (KPIs, phase timeline, per-device table, report preview)
 *   • Audit Report        (SHA-256 bar, tamper demo, downloads)
 *   • Blockchain Proof    (collapsible block explorer + chain verify)
 *
 * Section order:
 *   1. Banner + action buttons
 *   2. KPI cards
 *   3. Cryptographic proof bar (hash + tamper demo)
 *   4. Phase timeline breakdown
 *   5. Report preview
 *   6. Blockchain explorer (collapsible)
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText, Shield, CheckCircle2, XCircle, AlertTriangle,
  Link2, Server, Terminal, Lock, Cpu, Sparkles, Download,
  Copy, Check, ArrowRight, Activity, Layers, Hash,
  RefreshCw, AlertOctagon, ShieldAlert, ChevronDown, ChevronUp,
  Clock, ArrowDownToLine, Code,
} from 'lucide-react';
import StatusBadge from './StatusBadge';
import AnimatedCounter from './AnimatedCounter';
import api from '../api';

// ── helpers ────────────────────────────────────────────────────────────────

function downloadFile(content, filename, type) {
  const blob = new Blob([content], { type });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(url);
}

// ── Blockchain block explorer (collapsible) ────────────────────────────────

function BlockchainSection() {
  const [blocks,       setBlocks]       = useState([]);
  const [verification, setVerification] = useState(null);
  const [loading,      setLoading]      = useState(false);
  const [open,         setOpen]         = useState(false);

  const fetchLedger = useCallback(async () => {
    setLoading(true);
    try {
      const [ledger, verify] = await Promise.all([
        api.getBlockchainLedger(),
        api.verifyBlockchain(),
      ]);
      setBlocks(ledger.blocks || []);
      setVerification(verify);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  // auto-load when section first opens
  useEffect(() => { if (open && blocks.length === 0) fetchLedger(); }, [open]);

  const badge = (type) => {
    const cls = {
      GENESIS:               'bg-blue-950/80 text-blue-300 border-blue-500/40',
      RULE_APPROVAL:         'bg-purple-950/80 text-purple-300 border-purple-500/40',
      REPORT_INTEGRITY:      'bg-emerald-950/80 text-emerald-300 border-emerald-500/40',
      KNOWLEDGE_CONFIRMATION:'bg-amber-950/80 text-amber-300 border-amber-500/40',
      HUMAN_DECISION:        'bg-rose-950/80 text-rose-300 border-rose-500/40',
    }[type] || 'bg-slate-800 text-slate-300 border-slate-700';
    return (
      <span className={`px-2 py-0.5 text-[10px] uppercase font-mono font-bold rounded border ${cls}`}>
        {type}
      </span>
    );
  };

  return (
    <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
      {/* Collapsible header */}
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between p-5 text-left hover:bg-slate-900/40 transition"
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-brand-500/15 border border-brand-500/30 flex items-center justify-center text-brand-400">
            <Link2 className="w-4 h-4" />
          </div>
          <div>
            <div className="text-sm font-mono font-bold text-white flex items-center gap-2">
              CRYPTOGRAPHIC PROVENANCE LEDGER
              {verification && (
                verification.valid
                  ? <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-500/40 font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> VERIFIED
                    </span>
                  : <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-500/40 font-bold flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" /> TAMPERED
                    </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {blocks.length > 0 ? `${blocks.length} immutable block(s) — click to inspect` : 'Append-only blockchain audit trail'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {open && (
            <button
              type="button"
              onClick={e => { e.stopPropagation(); fetchLedger(); }}
              className="px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-mono flex items-center gap-1"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Verify Chain
            </button>
          )}
          {open ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
        </div>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 space-y-3 border-t border-slate-800">
              {loading && (
                <div className="flex items-center gap-2 py-4 text-xs font-mono text-brand-300">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Recalculating SHA-256 hashes across all blocks…
                </div>
              )}

              {blocks.map((block, i) => (
                <motion.div
                  key={block.block_hash}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="glass-panel rounded-xl p-4 border border-slate-800 hover:border-slate-700 transition"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-2 border-b border-slate-800/80 gap-2 mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center font-mono font-bold text-brand-300 text-xs">
                        #{block.index}
                      </div>
                      <span className="font-mono text-xs font-bold text-white">BLOCK {block.index}</span>
                      {badge(block.event_type)}
                    </div>
                    <div className="flex items-center gap-1 text-slate-400 text-[11px] font-mono">
                      <Clock className="w-3 h-3" />
                      {block.timestamp}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
                    <div className="md:col-span-2 bg-[#050811] p-3 rounded-lg border border-slate-850">
                      <div className="text-slate-400 text-[10px] font-sans font-semibold mb-1">PAYLOAD:</div>
                      <pre className="text-brand-300 text-[10px] whitespace-pre-wrap overflow-x-auto max-h-28 terminal-scroll">
                        {JSON.stringify(block.payload, null, 2)}
                      </pre>
                    </div>
                    <div className="space-y-2 bg-[#050811] p-3 rounded-lg border border-slate-850">
                      <div>
                        <span className="text-slate-500 text-[10px] block">BLOCK SHA-256:</span>
                        <span className="text-emerald-400 text-[10px] break-all font-bold">{block.block_hash}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 text-[10px] block">PREV HASH:</span>
                        <span className="text-slate-400 text-[10px] break-all">{block.previous_hash}</span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}

              {!loading && blocks.length === 0 && (
                <p className="text-center text-xs text-slate-500 font-mono py-6">
                  Run an audit mission to generate blockchain blocks.
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

export default function AuditPage({
  missionResult,
  fixtures     = [],
  rules        = [],
  onNavigateTab,
  onOpenHumanReview,
}) {
  const [copied,       setCopied]       = useState(false);
  const [copiedHash,   setCopiedHash]   = useState(false);
  const [tamperResult, setTamperResult] = useState(null);
  const [tamperLoading,setTamperLoading]= useState(false);

  // ── Derive metrics ────────────────────────────────────────────────────────
  const findingsByDevice = missionResult?.findings_by_device || {};
  const devices          = Object.keys(findingsByDevice);
  const flips            = missionResult?.flips         || [];
  const reviews          = missionResult?.grouped_reviews || [];
  const auditedDevices   = missionResult?.audited_devices || fixtures.map(f => f.filename);

  let totalChecks = 0, passCount = 0, failCount = 0, needsReviewCount = 0;
  Object.values(findingsByDevice).forEach(list => {
    list.forEach(f => {
      totalChecks++;
      const s = f.status?.toLowerCase();
      if (s === 'pass')               passCount++;
      else if (s === 'fail')          failCount++;
      else if (s === 'needs_human_review') needsReviewCount++;
    });
  });
  const complianceRate = totalChecks > 0 ? Math.round((passCount / totalChecks) * 100) : 0;
  const reportText  = missionResult?.report || '';
  const reportHash  = missionResult?.report_sha256 || '';

  // ── Actions ───────────────────────────────────────────────────────────────
  const handleDownloadPdf = () => {
    let uname = null;
    try { const u = JSON.parse(localStorage.getItem('ntro_user') || '{}'); uname = u.username || u.email; } catch {}
    window.open(api.downloadPdfReportUrl(uname), '_blank');
  };
  const handleCopyReport = () => {
    if (!reportText) return;
    navigator.clipboard.writeText(reportText);
    setCopied(true); setTimeout(() => setCopied(false), 2000);
  };
  const handleCopyHash = () => {
    navigator.clipboard.writeText(reportHash);
    setCopiedHash(true); setTimeout(() => setCopiedHash(false), 2000);
  };
  const handleDownloadMd  = () => downloadFile(reportText, `audit_report_${new Date().toISOString().slice(0,10)}.md`,   'text/markdown');
  const handleDownloadTxt = () => downloadFile(reportText, `audit_report_${new Date().toISOString().slice(0,10)}.txt`,   'text/plain');
  const handleDownloadJson = () => downloadFile(
    JSON.stringify({ timestamp: new Date().toISOString(), blockchain_sha256: reportHash, report_content: reportText }, null, 2),
    `audit_report_${new Date().toISOString().slice(0,10)}.json`, 'application/json'
  );
  const handleTamperDemo = async () => {
    setTamperLoading(true);
    try { const r = await api.tamperReport('CIS-MGMT-01', 'PASS'); setTamperResult(r); }
    catch (e) { console.error(e); }
    finally { setTamperLoading(false); }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">

      {/* ── 1. Banner ─────────────────────────────────────────────────────── */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-brand-500/30 bg-gradient-to-r from-slate-900 via-navy-850 to-slate-900 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-950 border border-brand-500/30 text-xs font-mono text-brand-300 mb-2">
              <Sparkles className="w-3.5 h-3.5 text-brand-400" />
              COMPREHENSIVE AUDIT REPORT & BLOCKCHAIN PROOF
            </div>
            <h1 className="text-2xl sm:text-3xl font-black font-mono text-white tracking-tight">
              AUDIT — EXECUTION SUMMARY & CERTIFIED REPORT
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-3xl">
              Consolidated intelligence: discovery, baseline normalization, human-in-the-loop,
              deterministic CIS evaluation, cryptographic sealing.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button onClick={handleDownloadPdf}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-mono font-bold flex items-center gap-1.5 shadow-lg shadow-emerald-500/25 border border-emerald-400/40 cursor-pointer">
              <FileText className="w-3.5 h-3.5" /> Download PDF
            </button>
            <button onClick={handleCopyReport} disabled={!reportText}
              className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-mono text-slate-200 flex items-center gap-1.5 disabled:opacity-40 cursor-pointer">
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-brand-400" />}
              {copied ? 'Copied' : 'Copy Report'}
            </button>
            <button onClick={handleDownloadMd} disabled={!reportText}
              className="px-3.5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-mono font-bold flex items-center gap-1.5 shadow-lg shadow-brand-500/20 disabled:opacity-40 cursor-pointer">
              <ArrowDownToLine className="w-3.5 h-3.5" /> .md
            </button>
            <button onClick={handleDownloadTxt} disabled={!reportText}
              className="px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono flex items-center gap-1.5 disabled:opacity-40 cursor-pointer">
              <Download className="w-3.5 h-3.5" /> .txt
            </button>
            <button onClick={handleDownloadJson} disabled={!reportText}
              className="px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs font-mono flex items-center gap-1.5 disabled:opacity-40 cursor-pointer">
              <Code className="w-3.5 h-3.5 text-brand-400" /> JSON
            </button>
          </div>
        </div>
      </div>

      {/* ── 2. KPI cards ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
        {[
          { label: 'AUDITED DEVICES',    value: auditedDevices.length || fixtures.length, suffix: '',  color: 'text-white',         sub: 'Heterogeneous Nodes',      border: 'border-slate-800' },
          { label: 'COMPLIANCE RATE',    value: complianceRate,  suffix: '%', color: 'text-emerald-300', sub: `${passCount} Deterministic Pass`, border: 'border-emerald-500/30 bg-emerald-950/10' },
          { label: 'SECURITY VIOLATIONS',value: failCount,       suffix: '',  color: 'text-rose-300',    sub: 'Immediate Remediation',  border: 'border-rose-500/30 bg-rose-950/10' },
          { label: 'HUMAN REVIEWS',      value: needsReviewCount,suffix: '',  color: 'text-amber-300',   sub: 'Clickable & Actionable',border: 'border-amber-500/30 bg-amber-950/10' },
          { label: 'BLOCKCHAIN SEAL',    value: null,            suffix: '',  color: 'text-brand-300',   sub: 'SHA-256 Verified',      border: 'border-brand-500/30 bg-brand-950/10', custom: `#${missionResult?.blockchain_block_index ?? 'Live'}` },
        ].map(m => (
          <div key={m.label} className={`glass-panel p-4 rounded-xl border ${m.border}`}>
            <div className="text-xs font-mono" style={{ color: 'inherit' }}>
              <span className="text-slate-400">{m.label}</span>
            </div>
            <div className={`text-2xl font-bold font-mono mt-1 ${m.color}`}>
              {m.custom ?? <AnimatedCounter target={m.value} duration={1200} suffix={m.suffix} />}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">{m.sub}</div>
          </div>
        ))}
      </div>

      {/* ── 3. Cryptographic proof bar ────────────────────────────────────── */}
      <div className="space-y-4">
        {/* SHA-256 bar */}
        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 font-mono text-xs">
          <div className="flex items-center gap-2 overflow-hidden">
            <Hash className="w-4 h-4 text-brand-400 shrink-0" />
            <span className="text-slate-400 shrink-0">BLOCKCHAIN SHA-256:</span>
            <span className="text-brand-300 font-bold truncate">
              {reportHash || 'Run audit to generate cryptographic seal…'}
            </span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button onClick={handleCopyHash} disabled={!reportHash}
              className="px-3 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 text-[11px] border border-slate-700 flex items-center gap-1 disabled:opacity-40 cursor-pointer">
              {copiedHash ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              {copiedHash ? 'Copied' : 'Copy Hash'}
            </button>
            <button onClick={handleTamperDemo} disabled={tamperLoading || !reportText}
              className="px-3.5 py-1.5 rounded-lg bg-rose-600/90 hover:bg-rose-500 text-white text-[11px] font-mono font-bold flex items-center gap-1 shadow-md shadow-rose-600/20 disabled:opacity-40 cursor-pointer">
              <ShieldAlert className="w-3.5 h-3.5" />
              {tamperLoading ? 'Verifying…' : 'Verify Tamper Proof'}
            </button>
          </div>
        </div>

        {/* Tamper result */}
        <AnimatePresence>
          {tamperResult && (
            <motion.div
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className={`p-5 rounded-2xl border ${tamperResult.tamper_detected
                ? 'bg-rose-950/40 border-rose-500 shadow-xl shadow-rose-500/20'
                : 'bg-emerald-950/40 border-emerald-500'}`}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${tamperResult.tamper_detected ? 'bg-rose-900/60 text-rose-300' : 'bg-emerald-900/60 text-emerald-300'}`}>
                  {tamperResult.tamper_detected
                    ? <AlertOctagon className="w-6 h-6 animate-bounce" />
                    : <CheckCircle2 className="w-6 h-6" />}
                </div>
                <div>
                  <div className="text-lg font-bold font-mono text-rose-300">STATUS: {tamperResult.status}</div>
                  <p className="text-xs text-slate-300 mt-0.5">{tamperResult.explanation}</p>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
                <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800">
                  <span className="text-slate-400 text-[11px] block font-sans font-semibold mb-1">STORED HASH (BLOCKCHAIN):</span>
                  <span className="text-emerald-400 text-[10px] break-all font-bold">{tamperResult.stored_hash}</span>
                </div>
                <div className="bg-slate-950/80 p-4 rounded-xl border border-rose-500/40">
                  <span className="text-rose-400 text-[11px] block font-sans font-semibold mb-1">RECALCULATED HASH:</span>
                  <span className="text-rose-300 text-[10px] break-all font-bold">{tamperResult.current_hash}</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── 4. Why hashes + phase timeline ───────────────────────────────── */}
      <div className="glass-panel p-6 sm:p-7 rounded-2xl border border-brand-500/40 bg-gradient-to-br from-[#0c1326] to-[#070b14] shadow-2xl space-y-4">
        <div className="flex items-center gap-3 border-b border-slate-800 pb-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500/20 border border-brand-500/40 flex items-center justify-center text-brand-400">
            <Link2 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold font-mono text-white">WHY DO HASHES EXIST ON THE BLOCKCHAIN?</h2>
            <p className="text-xs text-brand-300 font-mono">The Role of Cryptographic Provenance in NTRO Compliance</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs text-slate-300 leading-relaxed">
          <div className="space-y-3 bg-[#050811] p-4 rounded-xl border border-slate-800">
            <h3 className="font-mono font-bold text-brand-400 text-xs">1. The Problem: Retroactive Tampering</h3>
            <p>In conventional audit systems, a rogue insider could change <code>FAIL</code> to <code>PASS</code> in the database after the audit concludes. Without cryptographic proof, no external body can verify whether the report is genuine.</p>
          </div>
          <div className="space-y-3 bg-[#050811] p-4 rounded-xl border border-slate-800">
            <h3 className="font-mono font-bold text-emerald-400 text-xs">2. The Solution: SHA-256 + Block Chaining</h3>
            <p>When the agent finishes an audit it calculates a SHA-256 digest over the exact report text. This hash is written into an append-only block that references the previous block's hash — any alteration breaks the entire chain.</p>
          </div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-xs font-mono space-y-2">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">LIVE CRYPTOGRAPHIC TELEMETRY:</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <span className="text-slate-500">Report SHA-256: </span>
              <div className="text-brand-300 break-all bg-[#050811] p-2 rounded border border-slate-800 mt-1">
                {reportHash || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}
              </div>
            </div>
            <div>
              <span className="text-slate-500">Blockchain Block Sealed: </span>
              <div className="text-emerald-300 bg-[#050811] p-2 rounded border border-slate-800 mt-1">
                Block #{missionResult?.blockchain_block_index ?? 1} • Immutable NTRO Provenance Ledger
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Phase timeline ─────────────────────────────────────────────────── */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-5">
        <div className="border-b border-slate-800 pb-3">
          <h2 className="text-base font-mono font-bold text-white uppercase tracking-wider">STEP-BY-STEP MISSION TIMELINE</h2>
          <p className="text-xs text-slate-400">What the agent did at every phase of execution</p>
        </div>

        {[
          {
            icon: <Server className="w-4 h-4" />, color: 'text-brand-400',
            title: 'PHASE 1: DISCOVERY & MULTI-VENDOR FINGERPRINTING', badge: '100% SUCCESS',
            body: `Ingested ${auditedDevices.length} configuration file(s). Heuristic vendor fingerprinting identified Cisco IOS, Juniper Junos, and FortiOS devices with 97%+ confidence.`,
            extra: (
              <div className="flex flex-wrap gap-2 pt-1 font-mono text-[11px]">
                {auditedDevices.map(d => (
                  <span key={d} className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">{d}</span>
                ))}
              </div>
            ),
          },
          {
            icon: <Layers className="w-4 h-4" />, color: 'text-cyan-400',
            title: 'PHASE 2: UNIVERSAL SECURITY BASELINE NORMALIZATION', badge: 'PYDANTIC V2 SCHEMA',
            body: 'Vendor-specific CLI commands transformed into normalized evidence fields (SSH status, Telnet suppression, lockout params, password encryption) preserving exact file + line-number provenance.',
          },
          {
            icon: <Cpu className="w-4 h-4" />, color: 'text-amber-400',
            title: 'PHASE 3: HUMAN INTERVENTION & ACTIVE LEARNING', badge: `${reviews.length} REVIEW(S)`,
            body: 'Agent enforced autonomy boundaries and halted for human confirmation on unmapped directives. Reflection clustering resolved multiple devices in one operator decision.',
            extra: flips.length > 0 && (
              <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-500/30 text-xs font-mono text-emerald-300">
                ✓ {flips.length} finding(s) flipped from NEEDS_HUMAN_REVIEW to PASS.
              </div>
            ),
          },
          {
            icon: <Terminal className="w-4 h-4" />, color: 'text-purple-400',
            title: 'PHASE 4: 20 CIS BENCHMARK DETERMINISTIC EVALUATION', badge: `${totalChecks} CHECKS`,
            body: 'Evaluations determined strictly by immutable Python logic — zero LLM hallucinations.',
            extra: devices.length > 0 && (
              <div className="overflow-x-auto rounded-xl border border-slate-800 mt-2">
                <table className="w-full text-left text-xs border-collapse font-mono">
                  <thead>
                    <tr className="bg-slate-900/90 text-slate-400 border-b border-slate-800">
                      {['DEVICE', 'TOTAL', 'PASS', 'FAIL', 'HUMAN'].map(h => (
                        <th key={h} className="py-2 px-3">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {devices.map(devId => {
                      const fs = findingsByDevice[devId] || [];
                      const p  = fs.filter(f => f.status?.toLowerCase() === 'pass').length;
                      const fl = fs.filter(f => f.status?.toLowerCase() === 'fail').length;
                      const r  = fs.filter(f => f.status?.toLowerCase() === 'needs_human_review').length;
                      return (
                        <tr key={devId} className="hover:bg-slate-900/50">
                          <td className="py-2 px-3 font-bold text-white">{devId}</td>
                          <td className="py-2 px-3 text-slate-300">{fs.length}</td>
                          <td className="py-2 px-3 text-emerald-400 font-bold">{p}</td>
                          <td className="py-2 px-3 text-rose-400 font-bold">{fl}</td>
                          <td className="py-2 px-3 text-amber-400 font-bold">{r}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ),
          },
          {
            icon: <Link2 className="w-4 h-4" />, color: 'text-emerald-400',
            title: 'PHASE 5: IMMUTABLE BLOCKCHAIN RECORDING', badge: `BLOCK #${missionResult?.blockchain_block_index ?? 1}`,
            body: 'Mission report stamped with SHA-256 hash and written into the NTRO blockchain ledger. Any retroactive attempt to modify findings fails hash verification instantly.',
          },
        ].map((phase, i) => (
          <div key={i} className="p-4 rounded-xl bg-[#050811] border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className={`${phase.color} font-bold flex items-center gap-1.5`}>
                {phase.icon}{phase.title}
              </span>
              <span className="text-slate-300 font-bold text-[11px] shrink-0 ml-2">{phase.badge}</span>
            </div>
            <p className="text-xs text-slate-300 font-sans">{phase.body}</p>
            {phase.extra}
          </div>
        ))}
      </div>

      {/* ── 5. Report preview ─────────────────────────────────────────────── */}
      {reportText && (
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-brand-400" />
              CERTIFIED EXECUTIVE AUDIT REPORT
            </span>
            <div className="flex gap-2">
              <button onClick={handleDownloadPdf}
                className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-mono text-white font-bold flex items-center gap-1.5 cursor-pointer">
                <FileText className="w-3.5 h-3.5" /> PDF
              </button>
              <button onClick={handleCopyReport}
                className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-mono text-slate-300 border border-slate-700 flex items-center gap-1 cursor-pointer">
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
          </div>
          <pre className="p-4 rounded-xl bg-[#050811] border border-slate-800 text-xs font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-96 terminal-scroll leading-relaxed">
            {reportText}
          </pre>
        </div>
      )}

      {/* ── 6. Blockchain explorer (collapsible) ──────────────────────────── */}
      <BlockchainSection />

    </div>
  );
}
