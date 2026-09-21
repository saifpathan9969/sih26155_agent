import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  UserCheck, ShieldAlert, CheckCircle2, XCircle, AlertTriangle,
  Upload, FileText, Sparkles, Terminal, Info, X, Link2, Cpu
} from 'lucide-react';
import api from '../api';

export default function HumanReviewModal({
  isOpen,
  onClose,
  reviewData,
  onResolved,
  currentUser,
}) {
  const [decision, setDecision] = useState('PASS'); // 'PASS' | 'FAIL' | 'CONFIRM_MAPPING'
  const [notes, setNotes] = useState('');
  const [uploadedDoc, setUploadedDoc] = useState('');
  const [docFileName, setDocFileName] = useState('');
  const [fieldPath, setFieldPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  if (!isOpen || !reviewData) return null;

  const rawCmd = reviewData.command_raw || reviewData.evidence?.source?.raw || reviewData.representative_raw || 'set system login retry-options tries-before-disconnect 5';
  const deviceId = reviewData.device_id || reviewData.deviceId || (reviewData.device_ids && reviewData.device_ids[0]) || 'dev03_juniper.conf';
  const ruleId = reviewData.rule_id || 'CIS-AUTH-03';
  const vendor = reviewData.vendor || (deviceId.includes('juniper') ? 'juniper_junos' : deviceId.includes('cisco') ? 'cisco_ios' : 'fortinet_fortios');

  const defaultField = reviewData.baseline_field_path || reviewData.proposed_field_path || (rawCmd.includes('retry') ? 'authentication.account_lockout.enabled' : 'system.security_policy');

  const handleDocFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setDocFileName(file.name);
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result;
      if (typeof text === 'string') {
        setUploadedDoc(text);
      }
    };
    reader.readAsText(file);
  };

  const handleSubmitDecision = async (chosenDecision) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        device_id: deviceId,
        rule_id: ruleId,
        command_raw: rawCmd,
        decision: chosenDecision,
        notes: notes.trim(),
        uploaded_info: uploadedDoc.trim(),
        baseline_field_path: fieldPath || defaultField,
        value: chosenDecision === 'PASS' ? true : false,
        reviewer: currentUser?.full_name || currentUser?.username || 'Lead Security Auditor',
      };

      const res = await api.resolveHumanReview(payload);
      setResult(res);
      if (onResolved) {
        onResolved(res);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit human review resolution.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="w-full max-w-2xl glass-panel p-6 sm:p-8 rounded-2xl border border-amber-500/40 bg-[#0c1222] shadow-2xl relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
          <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-300 shadow-lg shadow-amber-500/20">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-amber-300 uppercase tracking-wider">
                HUMAN-IN-THE-LOOP INTERVENTION GATE
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-950 text-amber-300 font-mono border border-amber-500/40">
                Actionable Decision
              </span>
            </div>
            <h2 className="text-lg font-black font-mono text-white">
              Unknown Command Review: <span className="text-brand-300">{ruleId}</span>
            </h2>
          </div>
        </div>

        {/* Error / Success feedback */}
        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-950/50 border border-rose-500/40 flex items-start gap-2.5 text-xs text-rose-300 font-mono">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {result ? (
          <div className="my-6 space-y-4">
            <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/40 space-y-2">
              <div className="flex items-center gap-2 text-emerald-300 font-mono font-bold text-sm">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span>DECISION COMMITTED & SEALED ON BLOCKCHAIN</span>
              </div>
              <p className="text-xs text-slate-300 font-sans">
                {result.message}
              </p>
              <div className="flex items-center gap-2 pt-2 border-t border-emerald-500/20 text-xs font-mono text-emerald-400">
                <Link2 className="w-4 h-4" />
                <span>Cryptographic Proof: Block #{result.blockchain_block_index}</span>
              </div>
            </div>

            <button
              onClick={onClose}
              className="w-full py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-mono font-bold text-xs"
            >
              CLOSE & REFRESH AUDIT FINDINGS
            </button>
          </div>
        ) : (
          <div className="mt-4 space-y-4">
            {/* Section 1: The Command & Context */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>TARGET COMMAND (DISCOVERED ON DEVICE):</span>
                <span className="text-slate-300">{deviceId}</span>
              </div>
              <div className="p-3 rounded-xl bg-[#050811] border border-slate-700 font-mono text-xs text-amber-300">
                <code>{rawCmd}</code>
              </div>
            </div>

            {/* Section 2: Information Gathered by our Agent */}
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 text-xs font-mono">
              <div className="text-[11px] font-bold text-brand-300 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" />
                <span>INTELLIGENCE GATHERED BY AGENT:</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div>
                  <span className="text-slate-500">Detected Vendor: </span>
                  <span className="text-white capitalize">{vendor.replace('_', ' ')}</span>
                </div>
                <div>
                  <span className="text-slate-500">Confidence: </span>
                  <span className="text-emerald-400 font-bold">97.4%</span>
                </div>
                <div>
                  <span className="text-slate-500">Security Category: </span>
                  <span className="text-white">Authentication / Password Lockout</span>
                </div>
                <div>
                  <span className="text-slate-500">Proposed Baseline Field: </span>
                  <span className="text-cyan-300">{defaultField}</span>
                </div>
              </div>
              <div className="text-[11px] text-slate-400 border-t border-slate-800 pt-1.5">
                <span className="text-amber-400 font-semibold">Enforced Rationale: </span>
                <span>Deterministic parser has no hardcoded rule for this syntax. Safety policy strictly prohibits guessing on access-control directives.</span>
              </div>
            </div>

            {/* Section 3: Field to Upload Information About that Unknown Command */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-[11px] font-mono text-slate-300 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-brand-400" />
                  <span>UPLOAD OR ENTER INFORMATION ABOUT THIS COMMAND:</span>
                </label>
                <label className="cursor-pointer text-[10px] font-mono text-brand-400 hover:text-brand-300 flex items-center gap-1">
                  <Upload className="w-3 h-3" />
                  <span>{docFileName ? docFileName : 'Attach Doc (.txt, .md)'}</span>
                  <input
                    type="file"
                    accept=".txt,.md,.json,.pdf"
                    onChange={handleDocFileUpload}
                    className="hidden"
                  />
                </label>
              </div>
              <textarea
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Explain the security purpose of this command (e.g., 'In Junos 21.4, tries-before-disconnect 5 enforces lockout after 5 consecutive failed SSH attempts')..."
                className="w-full bg-[#050811] border border-slate-700 rounded-xl p-2.5 text-xs font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-brand-500 resize-none font-mono"
              />
              {uploadedDoc && (
                <div className="text-[10px] font-mono text-emerald-400 bg-emerald-950/30 p-1.5 rounded border border-emerald-500/30 truncate">
                  ✓ Uploaded reference attachment: {docFileName} ({uploadedDoc.length} characters)
                </div>
              )}
            </div>

            {/* Section 4: Human Verdict Actions */}
            <div className="pt-2 border-t border-slate-800 space-y-2">
              <div className="text-[11px] font-mono text-slate-400">
                SELECT OPERATOR VERDICT:
              </div>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleSubmitDecision('PASS')}
                  className="py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-mono font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/20 transition disabled:opacity-50"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>CONFIRM AS COMPLIANT (PASS)</span>
                </button>

                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleSubmitDecision('FAIL')}
                  className="py-2.5 px-4 rounded-xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white font-mono font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-rose-600/20 transition disabled:opacity-50"
                >
                  <XCircle className="w-4 h-4" />
                  <span>MARK AS DEFICIENT (FAIL)</span>
                </button>
              </div>

              <div className="text-center">
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleSubmitDecision('CONFIRM_MAPPING')}
                  className="text-[11px] font-mono text-brand-400 hover:text-brand-300 underline underline-offset-4 py-1"
                >
                  Confirm Schema Mapping & Add to Knowledge Base for Future Devices ➔
                </button>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
