import React, { useState, useMemo } from 'react';
import {
  XCircle, AlertTriangle, Filter, Terminal, Wrench,
  CheckCircle2, Copy, ShieldAlert, ArrowRight, Server, FileText,
  Send, Sparkles, HelpCircle, PhoneCall
} from 'lucide-react';
import api from '../api';
import StatusBadge from './StatusBadge';

const KNOWN_FIXES = {
  'CIS-MGMT-01': 'line vty 0 4\n transport input ssh\n exit',
  'CIS-AUTH-02': 'security passwords min-length 14',
  'CIS-AUTH-03': 'set system login retry-options tries-before-disconnect 5 lockout-period 15',
  'CIS-MGMT-02': 'ip ssh version 2',
  'CIS-MGMT-05': 'no snmp-server community public\nsnmp-server community <unique_secret> RO',
  'CIS-MGMT-07': 'line vty 0 4\n exec-timeout 10 0',
  'CIS-MGMT-03': 'no ip http server',
  'CIS-MGMT-04': 'ip http secure-server',
  'CIS-AUTH-01': 'service password-encryption',
  'CIS-LOG-01': 'logging host 192.0.2.100',
  'CIS-LOG-02': 'logging buffered 50000',
  'CIS-CRYPTO-01': 'ip http tls-version TLSv1.2',
};

export default function FailedRulesView({ findingsByDevice = {}, rules = [], fixtures = [], onOpenHumanReview }) {
  const [selectedFile, setSelectedFile] = useState('all');
  const [copiedId, setCopiedId] = useState(null);

  // Vendor solution input state keyed by finding ID
  const [vendorSolutions, setVendorSolutions] = useState({});
  const [submittingSolution, setSubmittingSolution] = useState(null);
  const [submissionFeedback, setSubmissionFeedback] = useState({});

  const deviceList = useMemo(() => {
    const fromFindings = Object.keys(findingsByDevice);
    if (fromFindings.length > 0) return fromFindings;
    return fixtures.map(f => f.filename);
  }, [findingsByDevice, fixtures]);

  // Filter to only FAIL findings
  const failedFindings = useMemo(() => {
    const list = [];
    const targetDevices = selectedFile === 'all' ? deviceList : [selectedFile];

    for (const dev of targetDevices) {
      const devFindings = findingsByDevice[dev] || [];
      for (const f of devFindings) {
        if (f.status?.toLowerCase() === 'fail') {
          const ruleMeta = rules.find(r => r.id === f.rule_id) || {};
          const knownFix = KNOWN_FIXES[f.rule_id] || (f.remediation_cli) || (f.remediation?.cli_commands);
          list.push({
            ...f,
            deviceId: dev,
            title: ruleMeta.title || f.rule_id,
            description: ruleMeta.description || '',
            severity: ruleMeta.severity || f.severity || 'high',
            operator: ruleMeta.evaluation?.operator,
            expected: ruleMeta.evaluation?.expected,
            hasKnownFix: !!knownFix,
            fixSyntax: knownFix || null,
          });
        }
      }
    }
    return list;
  }, [findingsByDevice, rules, selectedFile, deviceList]);

  const handleCopyRemediation = (finding, customSyntax = null) => {
    const syntaxToCopy = customSyntax || finding.fixSyntax || `# Apply compliance hardening for ${finding.baseline_field_path}`;
    navigator.clipboard.writeText(syntaxToCopy);
    setCopiedId(finding.rule_id + finding.deviceId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Submit vendor remedy and train agent via Federated Learning
  const handleSubmitVendorSolution = async (finding) => {
    const key = `${finding.deviceId}_${finding.rule_id}`;
    const solutionText = vendorSolutions[key];
    if (!solutionText || !solutionText.trim()) return;

    setSubmittingSolution(key);
    try {
      const user = JSON.parse(localStorage.getItem('ntro_user') || 'null');
      const payload = {
        device_id: finding.deviceId,
        rule_id: finding.rule_id,
        command_raw: String(finding.evidence?.value ?? finding.baseline_field_path),
        solution_text: solutionText.trim(),
        vendor_name: `${finding.deviceId.split('_')[1] || 'Vendor'} Support Specialist`,
        provider: user?.full_name || user?.username || 'Lead Auditor',
        username: user?.username || user?.email,
      };

      const res = await api.submitVendorSolution(payload);
      setSubmissionFeedback(prev => ({
        ...prev,
        [key]: {
          type: 'success',
          text: `✓ Solution learned & synced into dataset via Federated Learning Round #${res.federated_round?.round_id || 1}!`,
        },
      }));
    } catch (err) {
      setSubmissionFeedback(prev => ({
        ...prev,
        [key]: {
          type: 'error',
          text: err.response?.data?.detail || 'Failed to submit vendor solution.',
        },
      }));
    } finally {
      setSubmittingSolution(null);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto font-sans">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-rose-500/30 bg-gradient-to-r from-[#12070e] via-[#0d111d] to-[#070b14] shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-rose-950/80 border border-rose-500/40 flex items-center justify-center text-rose-400 shadow-lg shadow-rose-500/20">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-rose-950 border border-rose-500/40 text-[10px] font-mono text-rose-300 font-bold mb-1">
                <span>NON-COMPLIANT FINDINGS & VENDOR RESOLUTION</span>
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
              </div>
              <h2 className="text-xl font-black font-mono text-white tracking-wide">
                FAILED COMMANDS & REMEDIATION WORKBENCH
              </h2>
              <p className="text-xs text-slate-400">
                Actionable vendor CLI fixes with automated Federated Learning ingestion for unknown solutions.
              </p>
            </div>
          </div>

          {/* Config File Filter Selector */}
          <div className="flex items-center gap-2 bg-[#050811] px-3.5 py-2 rounded-xl border border-slate-700">
            <Filter className="w-4 h-4 text-brand-400 shrink-0" />
            <span className="text-xs font-mono text-slate-400">Config:</span>
            <select
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              className="bg-transparent text-xs font-mono text-white font-bold focus:outline-none cursor-pointer"
            >
              <option value="all" className="bg-[#0c1222] text-white">All Config Files ({deviceList.length})</option>
              {deviceList.map(dev => {
                const count = (findingsByDevice[dev] || []).filter(f => f.status?.toLowerCase() === 'fail').length;
                return (
                  <option key={dev} value={dev} className="bg-[#0c1222] text-white">
                    {dev} ({count} failed)
                  </option>
                );
              })}
            </select>
          </div>
        </div>
      </div>

      {/* Metrics Summary Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-[#0c1222]/80 font-mono text-xs">
          <div className="text-slate-400 uppercase text-[10px]">TOTAL FAILED DIRECTIVES</div>
          <div className="text-2xl font-black text-rose-400 mt-1">{failedFindings.length}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Strict CIS / SOHO Rule Failures</div>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-[#0c1222]/80 font-mono text-xs">
          <div className="text-slate-400 uppercase text-[10px]">ACTIVE TARGET FILE</div>
          <div className="text-sm font-bold text-white mt-1 truncate">{selectedFile === 'all' ? 'All Audited Devices' : selectedFile}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            {selectedFile === 'all' ? `${deviceList.length} Network Nodes Ingested` : 'Single Device Filtered'}
          </div>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-[#0c1222]/80 font-mono text-xs">
          <div className="text-slate-400 uppercase text-[10px]">KNOWN REMEDIES</div>
          <div className="text-2xl font-black text-emerald-400 mt-1">
            {failedFindings.filter(f => f.hasKnownFix).length}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">1-Click Automated CLI Payloads</div>
        </div>
      </div>

      {/* Failed Rules Cards List */}
      {failedFindings.length === 0 ? (
        <div className="glass-panel p-12 rounded-2xl border border-slate-800 text-center space-y-3 font-mono">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
          <h3 className="text-base font-bold text-white">No Failed Directives in Selected Configuration</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            All deterministic baseline checks for this configuration either passed or require human ambiguity confirmation.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {failedFindings.map((finding, idx) => {
            const isCopied = copiedId === (finding.rule_id + finding.deviceId);
            const key = `${finding.deviceId}_${finding.rule_id}`;
            const feedback = submissionFeedback[key];

            return (
              <div
                key={idx}
                className="glass-panel p-5 rounded-2xl border border-rose-500/30 bg-[#090e18] shadow-lg space-y-4"
              >
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 font-mono font-bold text-xs border border-rose-500/40">
                      {finding.rule_id}
                    </span>
                    <span className="font-mono text-sm font-bold text-white">
                      {finding.title}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300 text-[11px] font-mono">
                      {finding.deviceId}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 font-mono">
                    <span className="px-2 py-0.5 rounded bg-rose-900/40 text-rose-300 border border-rose-700/50 text-[10px] font-bold uppercase">
                      FAIL
                    </span>
                    <span className="text-slate-400 text-[10px]">
                      Severity: <span className="text-amber-400 uppercase font-bold">{finding.severity}</span>
                    </span>
                  </div>
                </div>

                {/* Evidence & Root Cause */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                  {/* Left: Failure Root Cause */}
                  <div className="space-y-2 bg-[#050811] p-3.5 rounded-xl border border-slate-800">
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                      <XCircle className="w-3.5 h-3.5 text-rose-400" /> FAILURE ROOT CAUSE
                    </div>
                    <div className="space-y-1 text-slate-300">
                      <div>
                        <span className="text-slate-500">Evaluated Path: </span>
                        <span className="text-brand-300">{finding.baseline_field_path}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Expected Value: </span>
                        <span className="text-emerald-400 font-bold">{JSON.stringify(finding.expected)}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Observed State: </span>
                        <span className="text-rose-400 font-bold">{String(finding.evidence?.value ?? 'insecure_default')}</span>
                      </div>
                    </div>
                    {finding.description && (
                      <p className="text-[11px] text-slate-400 font-sans pt-1 border-t border-slate-800/80">
                        {finding.description}
                      </p>
                    )}
                  </div>

                  {/* Right: Remediation OR Connect with Vendor Section */}
                  <div className="space-y-3 bg-[#050811] p-3.5 rounded-xl border border-slate-800">
                    {finding.hasKnownFix ? (
                      <>
                        <div className="flex items-center justify-between">
                          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                            <Wrench className="w-3.5 h-3.5 text-emerald-400" /> RECOMMENDED CLI FIX
                          </div>
                          <button
                            type="button"
                            onClick={() => handleCopyRemediation(finding)}
                            className={`px-2.5 py-1 rounded-lg text-[10px] font-mono font-bold flex items-center gap-1.5 transition cursor-pointer ${
                              isCopied
                                ? 'bg-emerald-600 text-white'
                                : 'bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-900/80'
                            }`}
                          >
                            <Copy className="w-3 h-3" />
                            <span>{isCopied ? 'COPIED!' : 'COPY PAYLOAD'}</span>
                          </button>
                        </div>

                        <div className="text-[11px] text-slate-400 font-sans space-y-1">
                          <div>1. Enter device privileged configuration mode (`configure terminal`).</div>
                          <div>2. Paste the hardening payload below.</div>
                          <div>3. Commit changes to immutable running configuration.</div>
                        </div>

                        <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-[11px] text-emerald-300 font-mono overflow-x-auto whitespace-pre">
                          <code>{finding.fixSyntax}</code>
                        </div>
                      </>
                    ) : (
                      <>
                        {/* No known fix -> Show vendor notification and input */}
                        <div className="p-2.5 rounded-lg bg-amber-950/60 border border-amber-500/40 flex items-start gap-2 text-xs font-mono text-amber-200">
                          <PhoneCall className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                          <div>
                            <div className="font-bold text-amber-300">
                              User needs to connect with the config vendor.
                            </div>
                            <div className="text-[11px] text-amber-300/80 font-sans mt-0.5">
                              No automated remediation recipe is currently indexed for this proprietary directive.
                            </div>
                          </div>
                        </div>

                        {/* Input Option to Submit Vendor Solution */}
                        <div className="space-y-2 pt-1">
                          <label className="block text-[11px] font-mono font-bold text-slate-300">
                            PROVIDE VENDOR SOLUTION / FIX RECEIVED:
                          </label>
                          <textarea
                            rows={2}
                            value={vendorSolutions[key] || ''}
                            onChange={(e) => setVendorSolutions({ ...vendorSolutions, [key]: e.target.value })}
                            placeholder="Paste the vendor solution or CLI syntax here (e.g. 'set security policy default drop')..."
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                          />
                          <button
                            type="button"
                            disabled={submittingSolution === key || !vendorSolutions[key]?.trim()}
                            onClick={() => handleSubmitVendorSolution(finding)}
                            className="w-full py-2 px-3 rounded-lg bg-gradient-to-r from-brand-600 to-cyan-600 hover:from-brand-500 hover:to-cyan-500 text-white font-mono font-bold text-xs flex items-center justify-center gap-1.5 shadow-md shadow-brand-500/20 transition disabled:opacity-50 cursor-pointer"
                          >
                            <Send className="w-3.5 h-3.5" />
                            <span>
                              {submittingSolution === key ? 'Training Agent via Federated Learning...' : 'Submit Vendor Fix & Train Agent'}
                            </span>
                          </button>

                          {feedback && (
                            <div className={`p-2 rounded-lg text-[11px] font-mono ${
                              feedback.type === 'success' ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40' : 'bg-rose-950 text-rose-300'
                            }`}>
                              {feedback.text}
                            </div>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
