import React, { useState, useMemo } from 'react';
import {
  XCircle, AlertTriangle, Filter, Terminal, Wrench,
  CheckCircle2, Copy, ShieldAlert, ArrowRight, Server, FileText
} from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function FailedRulesView({ findingsByDevice = {}, rules = [], fixtures = [], onOpenHumanReview }) {
  const [selectedFile, setSelectedFile] = useState('all');
  const [copiedId, setCopiedId] = useState(null);

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
          list.push({
            ...f,
            deviceId: dev,
            title: ruleMeta.title || f.rule_id,
            description: ruleMeta.description || '',
            severity: ruleMeta.severity || f.severity || 'high',
            operator: ruleMeta.evaluation?.operator,
            expected: ruleMeta.evaluation?.expected,
            remediation: ruleMeta.remediation || {},
          });
        }
      }
    }
    return list;
  }, [findingsByDevice, rules, selectedFile]);

  const handleCopyRemediation = (finding) => {
    let fixCmd = `# Remediate ${finding.rule_id} on ${finding.deviceId}\n`;
    if (finding.rule_id === 'CIS-MGMT-01') {
      fixCmd = `line vty 0 4\n transport input ssh\n exit`;
    } else if (finding.rule_id === 'CIS-AUTH-02') {
      fixCmd = `security passwords min-length 14`;
    } else if (finding.rule_id === 'CIS-AUTH-03') {
      fixCmd = `set system login retry-options tries-before-disconnect 5 lockout-period 15`;
    } else if (finding.rule_id === 'CIS-MGMT-02') {
      fixCmd = `ip ssh version 2`;
    } else if (finding.rule_id === 'CIS-MGMT-05') {
      fixCmd = `no snmp-server community public\nsnmp-server community <unique_secret> RO`;
    } else if (finding.rule_id === 'CIS-MGMT-07') {
      fixCmd = `line vty 0 4\n exec-timeout 10 0`;
    } else {
      fixCmd = `# Hardening directive for ${finding.baseline_field_path}:\n# Apply compliance configuration and save running state.`;
    }

    navigator.clipboard.writeText(fixCmd);
    setCopiedId(finding.rule_id + finding.deviceId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-rose-500/30 bg-gradient-to-r from-[#12070e] via-[#0d111d] to-[#070b14] shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-rose-950/80 border border-rose-500/40 flex items-center justify-center text-rose-400 shadow-lg shadow-rose-500/20">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-rose-950 border border-rose-500/40 text-[10px] font-mono text-rose-300 font-bold mb-1">
                <span>NON-COMPLIANT FINDINGS</span>
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
              </div>
              <h2 className="text-xl font-black font-mono text-white tracking-wide">
                FAILED COMMANDS & REMEDIATION WORKBENCH
              </h2>
              <p className="text-xs text-slate-400">
                Deterministic security policy violations with actionable vendor CLI fix syntax
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
          <div className="text-slate-400 uppercase text-[10px]">TOTAL VIOLATIONS</div>
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
          <div className="text-slate-400 uppercase text-[10px]">FIX PAYLOADS READY</div>
          <div className="text-2xl font-black text-emerald-400 mt-1">{failedFindings.length}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">1-Click CLI Remediation</div>
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
            const copyKey = finding.rule_id + finding.deviceId;
            const isCopied = copiedId === copyKey;

            return (
              <div
                key={`${finding.deviceId}-${finding.rule_id}-${idx}`}
                className="glass-panel p-5 rounded-2xl border border-rose-500/30 bg-[#0c1222]/90 space-y-4 relative overflow-hidden"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3 font-mono text-xs">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="px-2.5 py-1 rounded-md bg-rose-950/80 border border-rose-500/50 text-rose-300 font-bold text-xs">
                      {finding.rule_id}
                    </span>
                    <span className="text-white font-semibold font-sans text-sm">
                      {finding.title}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300 text-[11px]">
                      {finding.deviceId}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
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

                  {/* Remediation & CLI Fix Payload */}
                  <div className="space-y-2 bg-[#050811] p-3.5 rounded-xl border border-slate-800">
                    <div className="flex items-center justify-between">
                      <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                        <Wrench className="w-3.5 h-3.5 text-emerald-400" /> RECOMMENDED CLI FIX
                      </div>
                      <button
                        type="button"
                        onClick={() => handleCopyRemediation(finding)}
                        className={`px-2.5 py-1 rounded-lg text-[10px] font-mono font-bold flex items-center gap-1.5 transition ${
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

                    <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-[11px] text-emerald-300 font-mono overflow-x-auto">
                      {finding.rule_id === 'CIS-MGMT-01' ? (
                        <code>line vty 0 4<br />&nbsp;transport input ssh<br />exit</code>
                      ) : finding.rule_id === 'CIS-AUTH-02' ? (
                        <code>security passwords min-length 14</code>
                      ) : finding.rule_id === 'CIS-AUTH-03' ? (
                        <code>set system login retry-options tries-before-disconnect 5 lockout-period 15</code>
                      ) : finding.rule_id === 'CIS-MGMT-02' ? (
                        <code>ip ssh version 2</code>
                      ) : finding.rule_id === 'CIS-MGMT-05' ? (
                        <code>no snmp-server community public<br />snmp-server community &lt;unique_secret&gt; RO</code>
                      ) : finding.rule_id === 'CIS-MGMT-07' ? (
                        <code>line vty 0 4<br />&nbsp;exec-timeout 10 0</code>
                      ) : (
                        <code># Apply vendor baseline fix for {finding.baseline_field_path}</code>
                      )}
                    </div>
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
