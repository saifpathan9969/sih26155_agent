import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle, CheckCircle2, XCircle, ArrowRight,
  Sparkles, FileText, Upload, Terminal, BookOpen,
  HelpCircle, Layers, Cpu, ShieldCheck, Database, RefreshCw,
  FolderOpen, ChevronRight, FileCode2, ExternalLink
} from 'lucide-react';
import api from '../api';
import StatusBadge from './StatusBadge';

const PREDEFINED_CATEGORIES = [
  { id: 'Management', label: 'Management (SSH / Telnet / Administrative Port)' },
  { id: 'Authentication', label: 'Authentication & Password Policy (AAA / TACACS+ / Lockout)' },
  { id: 'AccessControl', label: 'Access Control & Firewall Policy (ACL / Packet Filter)' },
  { id: 'Logging', label: 'Logging & Syslog (Remote Host / Audit Events / Buffer)' },
  { id: 'Cryptography', label: 'Cryptography & TLS (Encryption / Hardened Ciphers)' },
  { id: 'NetworkServices', label: 'Network Services (Insecure Services / SNMP / NTP)' },
  { id: 'SecurityControls', label: 'Security Controls (Egress Filter / Defense)' },
];

const TRUST_BAND_STYLES = {
  high: { bar: 'bg-emerald-400', text: 'text-emerald-300', chip: 'bg-emerald-950/70 border-emerald-500/50' },
  medium: { bar: 'bg-amber-400', text: 'text-amber-300', chip: 'bg-amber-950/70 border-amber-500/50' },
  low: { bar: 'bg-rose-400', text: 'text-rose-300', chip: 'bg-rose-950/70 border-rose-500/50' },
};

const SEVERITY_STYLES = {
  critical: 'bg-rose-950/80 text-rose-300 border-rose-500/50',
  high: 'bg-orange-950/80 text-orange-300 border-orange-500/50',
  medium: 'bg-amber-950/80 text-amber-300 border-amber-500/50',
  low: 'bg-sky-950/80 text-sky-300 border-sky-500/50',
  info: 'bg-slate-900 text-slate-400 border-slate-700',
};

/** Compact trust pill used in the command list. */
function TrustBadge({ percent = 0, band = 'low' }) {
  const s = TRUST_BAND_STYLES[band] || TRUST_BAND_STYLES.low;
  return (
    <span
      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${s.chip} ${s.text}`}
      title={`Agent trust score: ${percent}%`}
    >
      {percent}%
    </span>
  );
}

/**
 * Full trust breakdown. The score is a weighted blend of independent signals,
 * so every contributing factor is shown rather than a single opaque number —
 * an operator signing off on a security verdict needs to see *why* the agent
 * is or is not confident.
 */
function TrustMeter({ command }) {
  const band = command.trust_band || 'low';
  const s = TRUST_BAND_STYLES[band] || TRUST_BAND_STYLES.low;
  const percent = command.trust_percent ?? 0;

  return (
    <div className="p-3.5 rounded-xl bg-[#050811] border border-slate-800 space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-baseline gap-2">
          <span className={`text-2xl font-black font-mono ${s.text}`}>{percent}%</span>
          <span className={`text-[11px] font-mono font-bold ${s.text}`}>
            {command.trust_band_label || 'Low confidence'}
          </span>
        </div>
        <span className="text-[10px] font-mono text-slate-500">AGENT TRUST SCORE</span>
      </div>

      <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
        <div
          className={`h-full ${s.bar} transition-all duration-500`}
          style={{ width: `${Math.max(2, percent)}%` }}
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Agent trust score"
        />
      </div>

      <div className="space-y-1.5 pt-1">
        {(command.trust_factors || []).map((f) => (
          <div key={f.label} className="flex items-center gap-2 text-[10px] font-mono">
            <span className="text-slate-400 w-32 shrink-0 truncate" title={f.label}>
              {f.label}
            </span>
            <div className="h-1.5 flex-1 rounded-full bg-slate-800/80 overflow-hidden">
              <div
                className="h-full bg-brand-400/70"
                style={{ width: `${Math.round((f.value ?? 0) * 100)}%` }}
              />
            </div>
            <span className="text-slate-300 w-9 text-right shrink-0">
              {Math.round((f.value ?? 0) * 100)}%
            </span>
            <span className="text-slate-600 w-10 text-right shrink-0">
              ×{f.weight}
            </span>
          </div>
        ))}
      </div>

      {(command.trust_factors || []).some(f => f.detail) && (
        <ul className="pt-1 space-y-0.5 border-t border-slate-800">
          {command.trust_factors.filter(f => f.detail).map(f => (
            <li key={`${f.label}-d`} className="text-[10px] text-slate-500 font-sans">
              <span className="text-slate-400">{f.label}:</span> {f.detail}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function TrainingWizard({ onMissionUpdate, fixtures = [] }) {
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [filesWithReviews, setFilesWithReviews] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedCommand, setSelectedCommand] = useState(null);

  // Teaching input state
  const [selectedCategory, setSelectedCategory] = useState('Management');
  const [customNotes, setCustomNotes] = useState('');
  const [uploadedDocName, setUploadedDocName] = useState('');
  const [uploadedDocContent, setUploadedDocContent] = useState('');
  const [feedbackMsg, setFeedbackMsg] = useState(null);
  const [federatedInfo, setFederatedInfo] = useState(null);

  // Fetch unknown / human-needed commands config-file-wise
  const loadFilesAndCommands = async () => {
    setLoading(true);
    try {
      const user = JSON.parse(localStorage.getItem('ntro_user') || 'null');
      const uname = user?.username || user?.email;
      const res = await api.getHumanNeededByConfig(uname);
      const fileList = res.files || [];
      setFilesWithReviews(fileList);

      if (fileList.length > 0) {
        // Keep current selected file if still valid, otherwise pick first
        const currentStillValid = fileList.find(f => f.filename === selectedFile?.filename);
        const fileToSelect = currentStillValid || fileList[0];
        setSelectedFile(fileToSelect);

        // Preserve the operator's place in the queue. Resetting to commands[0]
        // on every refetch yanked the view away from the directive they just
        // ruled on, hiding the confirmation.
        const stillSelected = selectedCommand
          ? fileToSelect.commands?.find(c => c.command_raw === selectedCommand.command_raw)
          : null;

        if (stillSelected) {
          setSelectedCommand(stillSelected);
        } else if (fileToSelect.commands?.length > 0) {
          const firstPending =
            fileToSelect.commands.find(c => !c.resolved) || fileToSelect.commands[0];
          handleSelectCommand(firstPending);
        } else {
          setSelectedCommand(null);
        }
      } else {
        setSelectedFile(null);
        setSelectedCommand(null);
      }

      // Also get federated learning status
      const flRes = await api.getFederatedStatus();
      setFederatedInfo(flRes);
    } catch (err) {
      console.error("Error loading human-needed commands by config:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFilesAndCommands();
  }, []);

  const handleSelectFile = (fileObj) => {
    setSelectedFile(fileObj);
    setFeedbackMsg(null);
    if (fileObj.commands && fileObj.commands.length > 0) {
      handleSelectCommand(fileObj.commands[0]);
    } else {
      setSelectedCommand(null);
    }
  };

  const handleSelectCommand = (cmdObj) => {
    setSelectedCommand(cmdObj);
    setFeedbackMsg(null);
    if (cmdObj.suggested_category) {
      setSelectedCategory(cmdObj.suggested_category);
    }
    setCustomNotes('');
    setUploadedDocName('');
    setUploadedDocContent('');
  };

  // Handle local file upload (notes or vendor documentation)
  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadedDocName(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      setUploadedDocContent(event.target?.result || '');
    };
    reader.readAsText(file);
  };

  /**
   * Immediately reflect the verdict in local state.
   *
   * The backend now persists verdicts, but the list is only refetched after a
   * delay — without this the operator clicked PASS and saw no change, which
   * read as a broken button. Optimistically marking the command keeps the UI
   * honest; the subsequent refetch confirms it from the server.
   */
  const applyLocalResolution = (verdict, reviewerName, resolvedAt) => {
    const stamp = resolvedAt || new Date().toISOString();

    setFilesWithReviews(prev => prev.map(f => {
      if (f.filename !== selectedFile?.filename) return f;
      const commands = (f.commands || []).map(c =>
        c.command_raw === selectedCommand?.command_raw
          ? {
              ...c,
              resolved: true,
              verdict,
              resolved_by: reviewerName,
              resolved_at: stamp,
              resolved_category: selectedCategory,
            }
          : c
      );
      const pending = commands.filter(c => !c.resolved).length;
      return {
        ...f,
        commands,
        total_commands_needing_review: pending,
        total_commands_resolved: commands.length - pending,
      };
    }));

    setSelectedCommand(prev => prev ? {
      ...prev,
      resolved: true,
      verdict,
      resolved_by: reviewerName,
      resolved_at: stamp,
      resolved_category: selectedCategory,
    } : prev);
  };

  // Handle Pass / Fail Verdict Resolution
  const handleResolveCommand = async (verdict) => {
    if (!selectedCommand || !selectedFile) return;

    setSubmitting(true);
    setFeedbackMsg(null);

    const user = JSON.parse(localStorage.getItem('ntro_user') || 'null');
    const reviewerName = user?.full_name || user?.username || 'Lead Security Auditor';

    const payload = {
      filename: selectedFile.filename,
      command_raw: selectedCommand.command_raw,
      category: selectedCategory,
      verdict: verdict, // "PASS" | "FAIL"
      documentation: uploadedDocContent || customNotes || `Operator confirmed ${verdict} directive for ${selectedCategory}`,
      rule_id: selectedCommand.rule_id || 'CIS-GENERIC-REVIEW',
      reviewer: reviewerName,
      username: user?.username || user?.email,
    };

    try {
      const res = await api.resolveCommandInTraining(payload);

      // Reflect the verdict straight away so the operator sees it land
      applyLocalResolution(verdict, reviewerName, res.resolved_at);

      setFeedbackMsg({
        type: verdict === 'PASS' ? 'success' : 'warning',
        text: verdict === 'PASS'
          ? `✓ Directive recorded as PASS. Sealed in block #${res.blockchain_block_index} and integrated into Federated Learning round #${res.federated_round?.round_id || 1}.`
          : `⚠️ Directive recorded as FAIL. Routed to the Failed Commands workbench. Federated Learning round #${res.federated_round?.round_id || 1} updated.`,
      });

      if (onMissionUpdate) {
        onMissionUpdate();
      }

      // Reload files after brief pause
      setTimeout(() => {
        loadFilesAndCommands();
      }, 1200);
    } catch (err) {
      setFeedbackMsg({
        type: 'error',
        text: err.response?.data?.detail || "Failed to resolve command. Please try again.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto font-sans">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-brand-500/30 bg-gradient-to-r from-brand-950/30 via-[#0d1424] to-[#070b14] shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-brand-600/30 border border-brand-400/40 flex items-center justify-center text-brand-300 shadow-lg shadow-brand-500/20">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-brand-950 border border-brand-500/40 text-[10px] font-mono text-brand-300 font-bold mb-1">
                <span>AI RETRIEVAL & FEDERATED ACTIVE LEARNING</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              </div>
              <h2 className="text-xl font-black font-mono text-white tracking-wide">
                CONFIG-FILE-WISE SYNTAX TEACHING & RESOLUTION
              </h2>
              <p className="text-xs text-slate-400">
                Inspect unmapped commands by configuration file, attach documentation, and train the agent with Pass/Fail verdicts.
              </p>
            </div>
          </div>

          {/* Federated Learning Status Pill */}
          <div className="flex items-center gap-3 bg-[#050811] px-4 py-2.5 rounded-xl border border-slate-800 text-xs font-mono">
            <div className="text-right">
              <div className="text-[10px] text-slate-500 uppercase">FL Framework</div>
              <div className="text-brand-300 font-bold">Flower & PySyft</div>
            </div>
            <div className="h-6 w-px bg-slate-800" />
            <div>
              <div className="text-[10px] text-slate-500 uppercase">Current Round</div>
              <div className="text-emerald-400 font-bold">Round #{federatedInfo?.current_round || 1}</div>
            </div>
            <button
              onClick={loadFilesAndCommands}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
              title="Refresh config files and commands"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid: Left Column Config Files & Commands; Right Column Inspection & Resolution */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Config File Tabs & Command List (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="glass-panel p-4 rounded-2xl border border-slate-800 bg-[#090e1a]">
            <h3 className="text-xs font-bold font-mono text-slate-400 uppercase tracking-wider mb-3 flex items-center justify-between">
              <span>Configuration Files ({filesWithReviews.length})</span>
              <span className="text-[10px] text-brand-400 font-normal">Select a file</span>
            </h3>

            {filesWithReviews.length === 0 ? (
              <div className="p-6 text-center text-xs font-mono text-slate-500 border border-dashed border-slate-800 rounded-xl">
                <FolderOpen className="w-8 h-8 mx-auto text-slate-600 mb-2" />
                <p>No configuration files uploaded yet.</p>
                <p className="text-[11px] text-slate-600 mt-1">Upload files using the Config Manager to start.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {filesWithReviews.map((fileObj) => {
                  const isSelected = selectedFile?.filename === fileObj.filename;
                  const count = fileObj.total_commands_needing_review || fileObj.commands?.length || 0;
                  return (
                    <button
                      key={fileObj.filename}
                      type="button"
                      onClick={() => handleSelectFile(fileObj)}
                      className={`w-full p-3 rounded-xl border text-left transition flex items-center justify-between cursor-pointer ${
                        isSelected
                          ? 'bg-brand-950/50 border-brand-500/60 text-white shadow-md shadow-brand-500/10'
                          : 'bg-[#050811] border-slate-800/80 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <div className="min-w-0 pr-2">
                        <div className="flex items-center gap-2">
                          <FileCode2 className="w-4 h-4 text-brand-400 shrink-0" />
                          <span className="font-mono text-xs font-bold truncate">{fileObj.filename}</span>
                        </div>
                        <span className="text-[10px] font-mono text-slate-500 block mt-0.5">
                          Vendor: {fileObj.vendor_display || fileObj.vendor}
                        </span>
                      </div>

                      <div className="flex flex-col items-end gap-1 shrink-0">
                        <span
                          className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${
                            count > 0
                              ? 'bg-amber-950 text-amber-300 border-amber-500/40'
                              : 'bg-emerald-950 text-emerald-300 border-emerald-500/40'
                          }`}
                        >
                          {count > 0 ? `${count} pending` : 'All resolved'}
                        </span>
                        {(fileObj.total_commands_resolved || 0) > 0 && (
                          <span className="text-[9px] font-mono text-emerald-400">
                            ✓ {fileObj.total_commands_resolved} ruled
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Commands inside Selected Config File */}
          {selectedFile && (
            <div className="glass-panel p-4 rounded-2xl border border-slate-800 bg-[#090e1a]">
              <h3 className="text-xs font-bold font-mono text-slate-400 uppercase tracking-wider mb-3 flex items-center justify-between">
                <span>Commands in {selectedFile.filename}</span>
                <span className="text-[10px] text-amber-400">
                  {selectedFile.commands?.length || 0} to resolve
                </span>
              </h3>

              {(!selectedFile.commands || selectedFile.commands.length === 0) ? (
                <div className="p-4 text-center text-xs font-mono text-emerald-400 border border-emerald-500/20 bg-emerald-950/10 rounded-xl">
                  ✓ All commands in this file are parsed and compliant.
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                  {selectedFile.commands.map((cmd, idx) => {
                    const isCmdSelected = selectedCommand?.command_raw === cmd.command_raw;
                    const isResolved = !!cmd.resolved;
                    const passed = cmd.verdict === 'PASS';

                    return (
                      <div
                        key={`${cmd.command_raw}-${idx}`}
                        onClick={() => handleSelectCommand(cmd)}
                        className={`p-3 rounded-xl border text-xs font-mono transition cursor-pointer ${
                          isCmdSelected
                            ? 'bg-amber-950/40 border-amber-500/60 shadow-md shadow-amber-500/10'
                            : isResolved
                            ? 'bg-[#050811]/60 border-slate-800/60 hover:border-slate-700 opacity-75'
                            : 'bg-[#050811] border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <span className={`text-[10px] font-bold ${isResolved ? 'text-slate-500' : 'text-amber-400'}`}>
                            #{idx + 1} {cmd.line ? `· L${cmd.line}` : ''}
                          </span>
                          <div className="flex items-center gap-1.5 shrink-0">
                            <TrustBadge percent={cmd.trust_percent} band={cmd.trust_band} />
                            {isResolved ? (
                              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                                passed
                                  ? 'bg-emerald-950/70 text-emerald-300 border-emerald-500/50'
                                  : 'bg-rose-950/70 text-rose-300 border-rose-500/50'
                              }`}>
                                {passed ? '✓ PASS' : '✗ FAIL'}
                              </span>
                            ) : (
                              <span className="text-[10px] text-slate-400">
                                {cmd.has_prior_info ? 'ℹ️ Known' : '⚠️ Unseen'}
                              </span>
                            )}
                          </div>
                        </div>

                        <div className={`font-mono text-[11px] truncate bg-black/40 px-2 py-1 rounded border border-slate-800 ${
                          isResolved ? 'text-slate-400 line-through decoration-slate-600' : 'text-white'
                        }`}>
                          <code>{cmd.command_raw}</code>
                        </div>

                        {cmd.benchmark_id && cmd.benchmark_id !== 'UNMAPPED' && (
                          <div className="mt-1.5 flex items-center gap-1.5">
                            <span className="text-[9px] font-mono text-brand-300 bg-brand-950/60 px-1.5 py-0.5 rounded border border-brand-500/30">
                              {cmd.benchmark_id}
                            </span>
                            <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                              SEVERITY_STYLES[cmd.benchmark_severity] || SEVERITY_STYLES.info
                            }`}>
                              {(cmd.benchmark_severity || 'info').toUpperCase()}
                            </span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Detailed Inspection, Documentation Upload & Pass/Fail Resolution (7 cols) */}
        <div className="lg:col-span-7">
          {selectedCommand ? (
            <div className="glass-panel p-6 rounded-2xl border border-brand-500/30 bg-[#090e1a] shadow-xl space-y-5">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Terminal className="w-5 h-5 text-brand-400" />
                  <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
                    Inspect & Resolve Directive
                  </h3>
                </div>
                <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2.5 py-1 rounded-lg border border-slate-800">
                  Target: {selectedFile?.filename}
                </span>
              </div>

              {/* 1. Actual CLI Command */}
              <div className="space-y-1.5">
                <label className="block text-xs font-mono font-bold text-slate-300">
                  1. ACTUAL CLI COMMAND:
                </label>
                <div className="p-3.5 rounded-xl bg-[#03060f] border border-amber-500/40 text-amber-300 font-mono text-xs overflow-x-auto shadow-inner">
                  <code>{selectedCommand.command_raw}</code>
                </div>
              </div>

              {/* Already-resolved banner */}
              {selectedCommand.resolved && (
                <div className={`p-3.5 rounded-xl border text-xs font-mono flex items-start gap-2.5 ${
                  selectedCommand.verdict === 'PASS'
                    ? 'bg-emerald-950/50 border-emerald-500/50 text-emerald-300'
                    : 'bg-rose-950/50 border-rose-500/50 text-rose-300'
                }`}>
                  {selectedCommand.verdict === 'PASS'
                    ? <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                    : <XCircle className="w-4 h-4 shrink-0 mt-0.5" />}
                  <div className="space-y-0.5">
                    <p className="font-bold">
                      Already ruled {selectedCommand.verdict} by {selectedCommand.resolved_by || 'an operator'}.
                    </p>
                    <p className="text-[11px] opacity-80 font-sans">
                      {selectedCommand.resolved_at
                        ? `Recorded ${new Date(selectedCommand.resolved_at).toLocaleString()}. `
                        : ''}
                      Submitting again overwrites the stored verdict and starts a new
                      federated round.
                    </p>
                  </div>
                </div>
              )}

              {/* 2. Agent trust score */}
              <div className="space-y-1.5">
                <label className="block text-xs font-mono font-bold text-slate-300">
                  2. AGENT TRUST SCORE (Why the agent stopped here):
                </label>
                <TrustMeter command={selectedCommand} />
              </div>

              {/* 3. Benchmark control this directive relates to */}
              <div className="space-y-1.5">
                <label className="block text-xs font-mono font-bold text-slate-300">
                  3. SECURITY BENCHMARK NOT SATISFIED:
                </label>
                <div className="p-3.5 rounded-xl bg-[#050811] border border-slate-800 space-y-2.5">
                  {selectedCommand.benchmark_id && selectedCommand.benchmark_id !== 'UNMAPPED' ? (
                    <>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[11px] font-mono font-bold text-brand-300 bg-brand-950/70 px-2 py-0.5 rounded border border-brand-500/40">
                          {selectedCommand.benchmark_id}
                        </span>
                        <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                          SEVERITY_STYLES[selectedCommand.benchmark_severity] || SEVERITY_STYLES.info
                        }`}>
                          {(selectedCommand.benchmark_severity || 'info').toUpperCase()}
                        </span>
                        <span className="text-[10px] font-mono text-slate-500 uppercase">
                          {selectedCommand.benchmark_framework || 'cis'}
                        </span>
                      </div>

                      <p className="text-xs font-semibold text-white">
                        {selectedCommand.benchmark_title}
                      </p>

                      {selectedCommand.benchmark_description && (
                        <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
                          {selectedCommand.benchmark_description}
                        </p>
                      )}

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                        {selectedCommand.benchmark_field_path && (
                          <div className="text-[10px] font-mono">
                            <span className="text-slate-500">Schema field: </span>
                            <code className="text-brand-300">{selectedCommand.benchmark_field_path}</code>
                          </div>
                        )}
                        {selectedCommand.benchmark_expected !== null &&
                         selectedCommand.benchmark_expected !== undefined && (
                          <div className="text-[10px] font-mono">
                            <span className="text-slate-500">Expected: </span>
                            <code className="text-emerald-300">
                              {String(selectedCommand.benchmark_expected)}
                            </code>
                          </div>
                        )}
                      </div>

                      {selectedCommand.benchmark_remediation?.command && (
                        <div className="pt-2 border-t border-slate-800 space-y-1">
                          <span className="text-[10px] font-mono font-bold text-slate-400">
                            VENDOR REMEDIATION:
                          </span>
                          <pre className="text-[10px] font-mono text-emerald-300 bg-black/50 p-2 rounded border border-slate-800 whitespace-pre-wrap overflow-x-auto">
{selectedCommand.benchmark_remediation.command}
                          </pre>
                          {selectedCommand.benchmark_remediation.rationale && (
                            <p className="text-[10px] text-slate-500 font-sans">
                              {selectedCommand.benchmark_remediation.rationale}
                            </p>
                          )}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="flex items-start gap-2 text-slate-400 text-xs">
                      <HelpCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <span>
                        No benchmark control is mapped to this directive yet. Classifying it
                        below teaches the agent which control family it belongs to.
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* 4. What the knowledge base already knows */}
              <div className="space-y-1.5">
                <label className="block text-xs font-mono font-bold text-slate-300">
                  4. INFORMATION WE HAVE (From Dataset & Knowledge Base):
                </label>
                <div className="p-3 rounded-xl bg-[#050811] border border-slate-800 text-xs text-slate-300 space-y-1">
                  {selectedCommand.has_prior_info ? (
                    <div className="flex items-start gap-2">
                      <span className="text-emerald-400 font-bold shrink-0">✓ Reference Match:</span>
                      <span className="text-slate-300">
                        Matches a known multi-vendor security pattern for{' '}
                        <strong>{selectedCommand.suggested_category}</strong>
                        {selectedCommand.suggested_field && (
                          <> (mapped to <code>{selectedCommand.suggested_field}</code>)</>
                        )}
                        {selectedCommand.suggested_value && (
                          <> with expected value <code>{selectedCommand.suggested_value}</code></>
                        )}.
                      </span>
                    </div>
                  ) : (
                    <div className="flex items-start gap-2 text-slate-400">
                      <span className="text-amber-400 font-bold shrink-0">⚠️ No Prior Documentation:</span>
                      <span>
                        This syntax was not in the reference dataset. Your input permanently
                        trains the model for every future device of this vendor.
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* 3. Tell Agent About The Command */}
              <div className="space-y-1.5">
                <label className="block text-xs font-mono font-bold text-slate-300">
                  5. TELL AGENT ABOUT THIS COMMAND (Semantic Domain):
                </label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full bg-[#050811] border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs font-mono text-white focus:outline-none focus:border-brand-500 cursor-pointer"
                >
                  {PREDEFINED_CATEGORIES.map(c => (
                    <option key={c.id} value={c.id} className="bg-[#0c1222] text-white">
                      {c.label}
                    </option>
                  ))}
                </select>
                <input
                  type="text"
                  value={customNotes}
                  onChange={(e) => setCustomNotes(e.target.value)}
                  placeholder="Optional: Enter notes about this command (e.g. 'Enforces password complexity on admin accounts')"
                  className="w-full bg-[#050811] border border-slate-800 rounded-xl px-3.5 py-2 text-xs font-mono text-slate-300 placeholder-slate-500 focus:outline-none focus:border-brand-500 mt-1"
                />
              </div>

              {/* 4. Upload Document Containing Info About Command */}
              <div className="space-y-1.5">
                <label className="block text-xs font-mono font-bold text-slate-300">
                  6. UPLOAD DOCUMENT OR VENDOR NOTES:
                </label>
                <div className="flex items-center gap-3">
                  <label className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono text-slate-200 flex items-center gap-2 cursor-pointer transition">
                    <Upload className="w-3.5 h-3.5 text-brand-400" />
                    <span>{uploadedDocName ? 'Change Document' : 'Upload Document (.txt, .md, .pdf)'}</span>
                    <input
                      type="file"
                      onChange={handleFileUpload}
                      className="hidden"
                      accept=".txt,.md,.cfg,.conf,.json,.pdf"
                    />
                  </label>
                  {uploadedDocName && (
                    <span className="text-xs font-mono text-emerald-400 truncate max-w-xs">
                      ✓ Attached: {uploadedDocName}
                    </span>
                  )}
                </div>
              </div>

              {/* Feedback Alert */}
              {feedbackMsg && (
                <div
                  className={`p-3.5 rounded-xl border text-xs font-mono flex items-start gap-2.5 ${
                    feedbackMsg.type === 'success'
                      ? 'bg-emerald-950/60 border-emerald-500/50 text-emerald-300'
                      : feedbackMsg.type === 'warning'
                      ? 'bg-amber-950/60 border-amber-500/50 text-amber-300'
                      : 'bg-rose-950/60 border-rose-500/50 text-rose-300'
                  }`}
                >
                  {feedbackMsg.type === 'success' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  )}
                  <span>{feedbackMsg.text}</span>
                </div>
              )}

              {/* 5. Two Simple Verdict Options: PASS and FAIL */}
              <div className="pt-2 border-t border-slate-800 space-y-2">
                <label className="block text-xs font-mono font-bold text-slate-300">
                  7. ISSUE COMPLIANCE VERDICT:
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    disabled={submitting}
                    onClick={() => handleResolveCommand('PASS')}
                    className={`py-3 px-4 rounded-xl font-mono font-bold text-xs flex items-center justify-center gap-2 shadow-lg transition disabled:opacity-50 cursor-pointer ${
                      selectedCommand.resolved && selectedCommand.verdict === 'PASS'
                        ? 'bg-emerald-700 text-white ring-2 ring-emerald-400 shadow-emerald-500/30'
                        : 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-emerald-500/20'
                    }`}
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>
                      {selectedCommand.resolved && selectedCommand.verdict === 'PASS'
                        ? '✓ MARKED PASS'
                        : 'PASS (Compliant Directive)'}
                    </span>
                  </button>

                  <button
                    type="button"
                    disabled={submitting}
                    onClick={() => handleResolveCommand('FAIL')}
                    className={`py-3 px-4 rounded-xl font-mono font-bold text-xs flex items-center justify-center gap-2 shadow-lg transition disabled:opacity-50 cursor-pointer ${
                      selectedCommand.resolved && selectedCommand.verdict === 'FAIL'
                        ? 'bg-rose-700 text-white ring-2 ring-rose-400 shadow-rose-500/30'
                        : 'bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white shadow-rose-500/20'
                    }`}
                  >
                    <XCircle className="w-4 h-4" />
                    <span>
                      {selectedCommand.resolved && selectedCommand.verdict === 'FAIL'
                        ? '✗ MARKED FAIL'
                        : 'FAIL (Route to Failed Commands)'}
                    </span>
                  </button>
                </div>
                <p className="text-[11px] text-slate-500 font-mono text-center pt-1">
                  Either verdict automatically trains the agent and updates the local dataset via Federated Learning.
                </p>
              </div>
            </div>
          ) : (
            <div className="glass-panel p-12 rounded-2xl border border-slate-800 bg-[#090e1a] text-center space-y-3 text-slate-400 font-mono">
              <Sparkles className="w-10 h-10 mx-auto text-slate-600" />
              <h4 className="text-sm font-bold text-slate-300">Select a Command to Begin Inspection</h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Choose a configuration file from the left, then select an unmapped command to review documentation and issue Pass/Fail verdicts.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
