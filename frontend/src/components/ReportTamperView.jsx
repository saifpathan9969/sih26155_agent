import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FileText, ShieldAlert, CheckCircle2, AlertOctagon, Hash, RefreshCw, Copy, Check } from 'lucide-react';
import api from '../api';

export default function ReportTamperView() {
  const [report, setReport] = useState('');
  const [reportHash, setReportHash] = useState('');
  const [tamperResult, setTamperResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const data = await api.getCurrentReport();
      setReport(data.report || '');
      setReportHash(data.sha256 || '');
      setTamperResult(null);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, []);

  const handleSimulateTamper = async () => {
    setLoading(true);
    try {
      const result = await api.tamperReport('CIS-MGMT-01', 'PASS');
      setTamperResult(result);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyHash = () => {
    navigator.clipboard.writeText(reportHash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Integrity & Tamper Header */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white font-mono flex items-center gap-2">
            <FileText className="w-5 h-5 text-brand-400" />
            FINAL AUDIT REPORT & TAMPER DETECTION DEMO
          </h2>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Step 17, 18 & 19: The final audit report is cryptographically sealed with a SHA-256 hash committed
            to the blockchain. Any post-audit alteration is immediately flagged as tamper-evident.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <button
            onClick={fetchReport}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs font-mono hover:text-white flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          <button
            onClick={handleSimulateTamper}
            disabled={loading}
            className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-mono font-bold transition flex items-center gap-1.5 shadow-lg shadow-rose-600/30"
          >
            <ShieldAlert className="w-4 h-4" />
            ⚡ SIMULATE TAMPER (FAIL → PASS)
          </button>
        </div>
      </div>

      {/* Hero Tamper Alert Box */}
      {tamperResult && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`p-6 rounded-2xl border ${
            tamperResult.tamper_detected
              ? 'bg-rose-950/40 border-rose-500 shadow-2xl shadow-rose-500/20'
              : 'bg-emerald-950/40 border-emerald-500'
          }`}
        >
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              tamperResult.tamper_detected ? 'bg-rose-900/60 text-rose-300' : 'bg-emerald-900/60 text-emerald-300'
            }`}>
              {tamperResult.tamper_detected ? (
                <AlertOctagon className="w-7 h-7 animate-bounce" />
              ) : (
                <CheckCircle2 className="w-7 h-7" />
              )}
            </div>
            <div>
              <div className="text-xl font-bold font-mono tracking-wide text-rose-300">
                STATUS: {tamperResult.status}
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                {tamperResult.explanation}
              </p>
            </div>
          </div>

          {/* Cryptographic Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5 font-mono text-xs">
            <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400 text-[11px] block font-sans font-semibold">
                STORED HASH (COMMITTED TO BLOCKCHAIN):
              </span>
              <span className="text-emerald-400 text-[11px] break-all font-bold block">
                {tamperResult.stored_hash}
              </span>
            </div>

            <div className="bg-slate-950/80 p-4 rounded-xl border border-rose-500/40 space-y-1">
              <span className="text-rose-400 text-[11px] block font-sans font-semibold">
                CURRENT RECALCULATED HASH:
              </span>
              <span className="text-rose-300 text-[11px] break-all font-bold block">
                {tamperResult.current_hash}
              </span>
            </div>
          </div>
        </motion.div>
      )}

      {/* SHA-256 Hash Display Card */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 font-mono text-xs">
        <div className="flex items-center gap-2">
          <Hash className="w-4 h-4 text-brand-400 shrink-0" />
          <span className="text-slate-400">REPORT SHA-256:</span>
          <span className="text-brand-300 font-bold break-all">{reportHash}</span>
        </div>
        <button
          onClick={handleCopyHash}
          className="px-3 py-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 text-[11px] border border-slate-700 flex items-center gap-1 shrink-0"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          {copied ? 'Copied' : 'Copy Hash'}
        </button>
      </div>

      {/* Final Markdown Report Viewer */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800">
        <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider mb-4">
          REPORT CONTENT EVIDENCE
        </h3>
        <div className="glass-panel-subtle rounded-xl p-5 bg-[#050811] text-xs font-mono text-slate-200 leading-relaxed max-h-[500px] overflow-y-auto terminal-scroll border border-slate-800">
          <pre className="whitespace-pre-wrap">{report || 'Run mission to generate complete report.'}</pre>
        </div>
      </div>
    </div>
  );
}
