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

        if (fileToSelect.commands?.length > 0) {
          handleSelectCommand(fileToSelect.commands[0]);
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
      setFeedbackMsg({
        type: verdict === 'PASS' ? 'success' : 'warning',
        text: verdict === 'PASS'
          ? `✓ Directive marked as PASS! Sealed on blockchain and integrated into Federated Learning Round #${res.federated_round?.round_id || 1}.`
          : `⚠️ Directive marked as FAIL! Routed to Failed Commands workbench. Federated Learning Round #${res.federated_round?.round_id || 1} updated.`,
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

                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border shrink-0 ${
                          count > 0
                            ? 'bg-amber-950 text-amber-300 border-amber-500/40'
                            : 'bg-emerald-950 text-emerald-300 border-emerald-500/40'
                        }`}
                      >
                        {count > 0 ? `${count} needs review` : 'All mapped'}
                      </span>
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
                    return (
                      <div
                        key={idx}
                        onClick={() => handleSelectCommand(cmd)}
                        className={`p-3 rounded-xl border text-xs font-mono transition cursor-pointer ${
                          isCmdSelected
                            ? 'bg-amber-950/40 border-amber-500/60 shadow-md shadow-amber-500/10'
                            : 'bg-[#050811] border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <span className="text-[10px] font-bold text-amber-400">
                            COMMAND #{idx + 1} {cmd.line ? `(Line ${cmd.line})` : ''}
                          </span>
                          <span className="text-[10px] text-slate-400">
                            {cmd.has_prior_info ? 'ℹ️ Prior Info' : '⚠️ Unseen'}
                          </span>
                        </div>
                        <div className="text-white font-mono text-[11px] truncate bg-black/40 px-2 py-1 rounded border border-slate-800">
                          <code>{cmd.command_raw}</code>
                        </div>
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

              {/* 2. Information We Have */}
              <div className="space-y-1.5">
                <label className="block text-xs font-mono font-bold text-slate-300">
                  2. INFORMATION WE HAVE (From Dataset & Knowledge Base):
                </label>
                <div className="p-3 rounded-xl bg-[#050811] border border-slate-800 text-xs text-slate-300 space-y-1">
                  {selectedCommand.has_prior_info ? (
                    <div className="flex items-start gap-2">
                      <span className="text-emerald-400 font-bold shrink-0">✓ Reference Match:</span>
                      <span className="text-slate-300">
                        Matches known multi-vendor security pattern for <strong>{selectedCommand.suggested_category}</strong> (mapped to <code>{selectedCommand.suggested_field}</code>).
                      </span>
                    </div>
                  ) : (
                    <div className="flex items-start gap-2 text-slate-400">
                      <span className="text-amber-400 font-bold shrink-0">⚠️ No Prior Documentation:</span>
                      <span>
                        This command syntax was not in the default database. User input will permanently train the AI model.
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* 3. Tell Agent About The Command */}
              <div className="space-y-1.5">
                <label className="block text-xs font-mono font-bold text-slate-300">
                  3. TELL AGENT ABOUT THIS COMMAND (Semantic Domain):
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
                  4. UPLOAD DOCUMENT OR VENDOR NOTES:
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
                  5. ISSUE COMPLIANCE VERDICT:
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    disabled={submitting}
                    onClick={() => handleResolveCommand('PASS')}
                    className="py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-mono font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 transition disabled:opacity-50 cursor-pointer"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>PASS (Compliant Directive)</span>
                  </button>

                  <button
                    type="button"
                    disabled={submitting}
                    onClick={() => handleResolveCommand('FAIL')}
                    className="py-3 px-4 rounded-xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white font-mono font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-rose-500/20 transition disabled:opacity-50 cursor-pointer"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>FAIL (Route to Failed Commands)</span>
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
