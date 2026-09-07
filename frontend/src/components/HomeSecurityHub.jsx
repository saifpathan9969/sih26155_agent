import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Wifi, ShieldCheck, AlertTriangle, CheckCircle2, Copy, Check,
  ExternalLink, ArrowRight, RefreshCw, Lock, Radio, Cpu, Wrench
} from 'lucide-react';
import api from '../api';

export default function HomeSecurityHub({ fixtures = [], onOpenUploadModal }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  const [expandedCheck, setExpandedCheck] = useState(null);

  const fetchChecks = async () => {
    setLoading(true);
    try {
      const res = await api.getSohoChecks();
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChecks();
  }, []);

  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  const passCount = data?.checks?.filter(c => c.status === 'PASS').length || 0;
  const failCount = data?.checks?.filter(c => c.status === 'FAIL').length || 0;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Home / SOHO Header */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-navy-900 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">🏠</span>
            <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-widest bg-amber-950/60 px-2.5 py-0.5 rounded border border-amber-500/30">
              Homeowner & Small Business Mode
            </span>
          </div>
          <h2 className="text-lg font-bold text-white font-mono">
            HOME ROUTER & SOHO WI-FI SECURITY GUARDIAN
          </h2>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl">
            Plain-English security verification for off-the-shelf home Wi-Fi routers (TP-Link, Netgear, ASUS, D-Link, MikroTik, Ubiquiti).
            Every issue includes clear step-by-step fix instructions and ready-to-copy configuration payloads.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {onOpenUploadModal && (
            <button
              type="button"
              onClick={onOpenUploadModal}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-200 border border-slate-700 flex items-center gap-1.5 transition cursor-pointer"
            >
              <span>📤 Upload Router Config</span>
            </button>
          )}
          <button
            onClick={fetchChecks}
            disabled={loading}
            className="px-3.5 py-1.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-xs font-mono font-bold flex items-center gap-1.5 transition cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh Router Status
          </button>
        </div>
      </div>

      {/* Dynamic Target Home Router Configurations Selector */}
      <div className="glass-panel p-4 rounded-xl border border-amber-500/30 bg-[#070b16] space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-bold text-amber-300 flex items-center gap-1.5">
            <Radio className="w-4 h-4 text-amber-400" />
            TARGET HOME / SOHO CONFIGURATIONS:
          </span>
          <span className="text-[11px] font-mono text-slate-400">{fixtures.length} Config{fixtures.length === 1 ? '' : 's'} Active</span>
        </div>

        {fixtures.length === 0 ? (
          <div className="p-6 rounded-xl border border-dashed border-slate-800 text-center space-y-3 font-mono">
            <p className="text-xs text-slate-400">
              No home router configurations uploaded yet. Upload your Wi-Fi router / firewall backup file (<code className="text-amber-300">.conf, .cfg, .rsc, .txt</code>) to evaluate security hardening.
            </p>
            {onOpenUploadModal && (
              <button
                type="button"
                onClick={onOpenUploadModal}
                className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs inline-flex items-center gap-2 cursor-pointer transition shadow-lg shadow-amber-500/20"
              >
                <span>📤 Upload Wi-Fi Router Config</span>
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 font-mono text-xs">
            {fixtures.map((r, idx) => (
              <div
                key={r.filename}
                className="p-3 rounded-lg border border-amber-500/20 bg-slate-900/60 flex flex-col justify-between"
              >
                <div>
                  <div className="text-[10px] text-amber-400 font-bold uppercase">Device #{idx + 1}</div>
                  <div className="text-white font-semibold text-xs mt-0.5">{r.filename}</div>
                  <div className="text-[10px] text-slate-400 mt-1 font-mono">{r.vendor_display || r.vendor} ({r.line_count || 0} lines)</div>
                </div>
                <div className="text-[10px] text-emerald-400 mt-2 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Ready for Audit
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-slate-400 text-[11px]">AUDITED HOME FLEET</div>
            <div className="text-white font-bold text-sm mt-0.5">{fixtures.length} SOHO Device{fixtures.length === 1 ? '' : 's'}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-slate-800/80 flex items-center justify-center text-brand-400">
            <Wifi className="w-5 h-5" />
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-emerald-500/20 bg-emerald-950/10 flex items-center justify-between">
          <div>
            <div className="text-emerald-400 text-[11px]">SECURE CHECKS</div>
            <div className="text-emerald-300 font-bold text-lg mt-0.5">{passCount} PASS</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-950/60 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-rose-500/20 bg-rose-950/10 flex items-center justify-between">
          <div>
            <div className="text-rose-400 text-[11px]">ACTION REQUIRED</div>
            <div className="text-rose-300 font-bold text-lg mt-0.5">{failCount} VULNERABLE</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-rose-950/60 border border-rose-500/30 flex items-center justify-center text-rose-400">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Security Checks List */}
      <div className="space-y-4">
        {data?.checks?.map((check) => {
          const isFail = check.status === 'FAIL';
          const isExpanded = expandedCheck === check.id || isFail;

          return (
            <motion.div
              key={check.id}
              layout
              className={`glass-panel rounded-2xl border transition overflow-hidden ${
                isFail
                  ? 'border-rose-500/40 bg-rose-950/10'
                  : 'border-slate-800 bg-slate-900/40'
              }`}
            >
              {/* Card Header */}
              <div
                onClick={() => setExpandedCheck(expandedCheck === check.id ? null : check.id)}
                className="p-5 cursor-pointer flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
              >
                <div className="flex items-start gap-3.5">
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${
                    isFail
                      ? 'bg-rose-950/80 border border-rose-500/40 text-rose-400'
                      : 'bg-emerald-950/80 border border-emerald-500/40 text-emerald-400'
                  }`}>
                    {isFail ? <AlertTriangle className="w-5 h-5" /> : <CheckCircle2 className="w-5 h-5" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-bold text-white font-mono">{check.title}</h3>
                      <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                        isFail
                          ? 'bg-rose-950 text-rose-300 border-rose-500/40'
                          : 'bg-emerald-950 text-emerald-300 border-emerald-500/40'
                      }`}>
                        {check.status}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">
                        {check.category}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-1">{check.explanation}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-auto font-mono text-xs">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    check.severity === 'CRITICAL' ? 'bg-rose-900/80 text-rose-200' :
                    check.severity === 'HIGH' ? 'bg-amber-900/80 text-amber-200' :
                    check.severity === 'MEDIUM' ? 'bg-blue-900/80 text-blue-200' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {check.severity}
                  </span>
                  <span className="text-slate-500 text-xs">{isExpanded ? '▲' : '▼'}</span>
                </div>
              </div>

              {/* Expanded Remediation Drawer */}
              {isExpanded && (
                <div className="border-t border-slate-800/80 bg-slate-950/80 p-5 space-y-4">
                  {/* Why it matters */}
                  <div className="bg-slate-900/70 p-3 rounded-xl border border-slate-800 text-xs">
                    <span className="text-amber-400 font-mono font-bold">Why this matters: </span>
                    <span className="text-slate-300">{check.why_it_matters}</span>
                  </div>

                  {/* Step-by-Step Fix Steps */}
                  <div className="space-y-2">
                    <div className="text-xs font-mono font-bold text-brand-300 flex items-center gap-1.5">
                      <Wrench className="w-4 h-4 text-brand-400" />
                      HOW TO FIX THIS IN YOUR ROUTER SETTINGS:
                    </div>
                    <ol className="space-y-1.5 text-xs text-slate-300 pl-5 list-decimal font-sans">
                      {check.remediation_steps?.map((step, idx) => (
                        <li key={idx} className="leading-relaxed">{step}</li>
                      ))}
                    </ol>
                  </div>

                  {/* Copy Fix Payload Block */}
                  {check.copy_fix_payload && (
                    <div className="space-y-2 pt-2 border-t border-slate-800">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono text-slate-400 flex items-center gap-1.5">
                          <Cpu className="w-3.5 h-3.5 text-emerald-400" />
                          Ready-to-Apply CLI / Setting Payload:
                        </span>
                        <button
                          onClick={() => handleCopy(check.id, check.copy_fix_payload)}
                          className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-bold transition flex items-center gap-1 shadow-lg shadow-emerald-600/20"
                        >
                          {copiedId === check.id ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                          {copiedId === check.id ? 'Copied Payload!' : '📋 Copy Fix Payload'}
                        </button>
                      </div>

                      <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 font-mono text-xs text-emerald-300 overflow-x-auto">
                        <pre className="whitespace-pre-wrap">{check.copy_fix_payload}</pre>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
