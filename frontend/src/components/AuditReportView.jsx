import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FileText, ShieldAlert, CheckCircle2, AlertOctagon, Hash,
  RefreshCw, Copy, Check, Download, ArrowDownToLine, Code
} from 'lucide-react';
import api from '../api';

export default function AuditReportView() {
  const [report, setReport] = useState('');
  const [reportHash, setReportHash] = useState('');
  const [tamperResult, setTamperResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedReport, setCopiedReport] = useState(false);

  const fetchReport = async () => {
    setLoading(true);
    try {
      let uname = null;
      try {
        const u = JSON.parse(localStorage.getItem('ntro_user') || '{}');
        uname = u.username || u.email || null;
      } catch (e) {}
      const data = await api.getCurrentReport(uname);
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
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleCopyReport = () => {
    navigator.clipboard.writeText(report);
    setCopiedReport(true);
    setTimeout(() => setCopiedReport(false), 2000);
  };

  const downloadFile = (content, filename, type) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadMarkdown = () => {
    const timestamp = new Date().toISOString().slice(0, 10);
    downloadFile(report, `compliance_audit_report_${timestamp}.md`, 'text/markdown;charset=utf-8');
  };

  const handleDownloadText = () => {
    const timestamp = new Date().toISOString().slice(0, 10);
    downloadFile(report, `compliance_audit_report_${timestamp}.txt`, 'text/plain;charset=utf-8');
  };

  const handleDownloadJson = () => {
    const timestamp = new Date().toISOString().slice(0, 10);
    const exportData = {
      timestamp: new Date().toISOString(),
      blockchain_sha256: reportHash,
      report_content: report
    };
    downloadFile(JSON.stringify(exportData, null, 2), `compliance_audit_report_${timestamp}.json`, 'application/json;charset=utf-8');
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Integrity & Actions Header */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white font-mono flex items-center gap-2">
            <FileText className="w-5 h-5 text-brand-400" />
            CERTIFIED COMPLIANCE AUDIT REPORT & BLOCKCHAIN SEAL
          </h2>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Cryptographically sealed with SHA-256 and committed to the distributed blockchain ledger.
            Directly export or verify the integrity proof below.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={fetchReport}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs font-mono hover:text-white flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          <button
            onClick={handleDownloadMarkdown}
            disabled={!report}
            className="px-3.5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-mono font-medium transition flex items-center gap-1.5 shadow-lg shadow-brand-500/20"
          >
            <ArrowDownToLine className="w-3.5 h-3.5" />
            Download (.md)
          </button>

          <button
            onClick={handleDownloadText}
            disabled={!report}
            className="px-3.5 py-2 rounded-xl bg-slate-850 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono font-medium transition flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            Download (.txt)
          </button>

          <button
            onClick={handleDownloadJson}
            disabled={!report}
            className="px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs font-mono flex items-center gap-1.5"
            title="Download JSON audit metadata and ledger proof"
          >
            <Code className="w-3.5 h-3.5 text-brand-400" />
            JSON
          </button>

          <button
            onClick={handleSimulateTamper}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-rose-600/90 hover:bg-rose-500 text-white text-xs font-mono font-bold transition flex items-center gap-1.5 shadow-lg shadow-rose-600/20 ml-1"
            title="Demonstrate blockchain tamper-evidence by altering a finding"
          >
            <ShieldAlert className="w-4 h-4" />
            Verify Tamper Proof
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

      {/* SHA-256 Hash and Copy Bar */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 font-mono text-xs">
        <div className="flex items-center gap-2 overflow-hidden">
          <Hash className="w-4 h-4 text-brand-400 shrink-0" />
          <span className="text-slate-400 shrink-0">BLOCKCHAIN SHA-256:</span>
          <span className="text-brand-300 font-bold truncate">{reportHash || 'Calculating ledger digest...'}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleCopyHash}
            className="px-3 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 text-[11px] border border-slate-700 flex items-center gap-1"
          >
            {copiedHash ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            {copiedHash ? 'Hash Copied' : 'Copy Hash'}
          </button>
          <button
            onClick={handleCopyReport}
            className="px-3 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 text-[11px] border border-slate-700 flex items-center gap-1"
          >
            {copiedReport ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            {copiedReport ? 'Report Copied' : 'Copy Report'}
          </button>
        </div>
      </div>

      {/* Final Markdown Report Viewer */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider">
            CERTIFIED REPORT CONTENT EVIDENCE
          </h3>
          <span className="text-[11px] text-slate-500 font-mono">
            {report ? `${report.length} characters` : ''}
          </span>
        </div>
        <div className="glass-panel-subtle rounded-xl p-5 bg-[#050811] text-xs font-mono text-slate-200 leading-relaxed max-h-[550px] overflow-y-auto terminal-scroll border border-slate-800">
          <pre className="whitespace-pre-wrap">{report || 'Run mission to generate complete certified report.'}</pre>
        </div>
      </div>
    </div>
  );
}
