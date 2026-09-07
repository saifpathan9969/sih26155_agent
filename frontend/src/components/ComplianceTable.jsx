import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, ChevronDown, ChevronRight, AlertCircle, CheckCircle2, Wrench, Search, Filter } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function ComplianceTable({
  findingsByDevice = {},
  rules = [],
  onOpenHumanReview,
}) {
  const [selectedDevice, setSelectedDevice] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedRule, setExpandedRule] = useState(null);

  // Flatten findings across devices
  const allFindings = [];
  Object.entries(findingsByDevice).forEach(([deviceId, findings]) => {
    findings.forEach(f => {
      const ruleMeta = rules.find(r => r.rule_id === f.rule_id) || {};
      allFindings.push({
        ...f,
        deviceId,
        title: ruleMeta.title || f.rule_id,
        framework: f.framework || ruleMeta.framework || 'cis',
        expected: ruleMeta.evaluation?.expected,
        operator: ruleMeta.evaluation?.operator,
      });
    });
  });

  const devices = Object.keys(findingsByDevice);

  // Filtering
  const filteredFindings = allFindings.filter(item => {
    if (selectedDevice !== 'all' && item.deviceId !== selectedDevice) return false;
    if (statusFilter !== 'all' && item.status.toLowerCase() !== statusFilter.toLowerCase()) return false;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      const matchId = item.rule_id.toLowerCase().includes(term);
      const matchTitle = item.title.toLowerCase().includes(term);
      const matchField = item.baseline_field_path?.toLowerCase().includes(term);
      if (!matchId && !matchTitle && !matchField) return false;
    }
    return true;
  });

  // Calculate summary counts
  const counts = {
    total: allFindings.length,
    pass: allFindings.filter(f => f.status.toLowerCase() === 'pass').length,
    fail: allFindings.filter(f => f.status.toLowerCase() === 'fail').length,
    needs_review: allFindings.filter(f => f.status.toLowerCase() === 'needs_human_review').length,
  };

  const getSeverityBadge = (sev) => {
    const s = (sev || 'medium').toLowerCase();
    const colors = {
      critical: 'bg-rose-950/80 text-rose-300 border-rose-500/40',
      high: 'bg-orange-950/80 text-orange-300 border-orange-500/40',
      medium: 'bg-amber-950/80 text-amber-300 border-amber-500/40',
      low: 'bg-blue-950/80 text-blue-300 border-blue-500/40',
    }[s] || 'bg-slate-800 text-slate-300 border-slate-700';

    return (
      <span className={`px-2 py-0.5 text-[10px] uppercase font-bold rounded border ${colors}`}>
        {s}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Metric Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-slate-800">
          <div className="text-xs text-slate-400 font-mono">EVALUATED CHECKS</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{counts.total}</div>
          <div className="text-[11px] text-slate-500 mt-1">20 Rules × 6 Devices</div>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-emerald-500/20 bg-emerald-950/10">
          <div className="text-xs text-emerald-400 font-mono">COMPLIANT (PASS)</div>
          <div className="text-2xl font-bold font-mono text-emerald-300 mt-1">{counts.pass}</div>
          <div className="text-[11px] text-emerald-500/80 mt-1">Deterministic Pass</div>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-rose-500/20 bg-rose-950/10">
          <div className="text-xs text-rose-400 font-mono">VIOLATIONS (FAIL)</div>
          <div className="text-2xl font-bold font-mono text-rose-300 mt-1">{counts.fail}</div>
          <div className="text-[11px] text-rose-500/80 mt-1">Remediation Required</div>
        </div>
        <div
          onClick={() => setStatusFilter('needs_human_review')}
          className="glass-panel p-4 rounded-xl border border-amber-500/20 bg-amber-950/10 cursor-pointer hover:border-amber-500/50 transition"
        >
          <div className="text-xs text-amber-400 font-mono flex items-center justify-between">
            <span>NEEDS HUMAN REVIEW</span>
            <span className="text-[10px] text-amber-300 underline">Filter</span>
          </div>
          <div className="text-2xl font-bold font-mono text-amber-300 mt-1">{counts.needs_review}</div>
          <div className="text-[11px] text-amber-500/80 mt-1">Gated for Human (Click to Filter)</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="glass-panel rounded-xl p-4 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Device Filter */}
          <select
            value={selectedDevice}
            onChange={(e) => setSelectedDevice(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-brand-500"
          >
            <option value="all">All Devices (6)</option>
            {devices.map(d => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-brand-500"
          >
            <option value="all">All Verdicts</option>
            <option value="pass">Pass Only</option>
            <option value="fail">Fail Only</option>
            <option value="needs_human_review">Needs Review Only</option>
          </select>
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search rule ID, title, field..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500"
          />
        </div>
      </div>

      {/* Findings Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-slate-800 shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-900/90 text-slate-400 font-mono border-b border-slate-800">
                <th className="py-3 px-4 w-10"></th>
                <th className="py-3 px-4">RULE ID</th>
                <th className="py-3 px-4">DEVICE</th>
                <th className="py-3 px-4">DESCRIPTION</th>
                <th className="py-3 px-4">SEVERITY</th>
                <th className="py-3 px-4">STATUS</th>
                <th className="py-3 px-4">OBSERVED VALUE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filteredFindings.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500">
                    No compliance findings match the current filters.
                  </td>
                </tr>
              ) : (
                filteredFindings.map((finding, idx) => {
                  const key = `${finding.deviceId}-${finding.rule_id}-${idx}`;
                  const isExpanded = expandedRule === key;
                  const observedVal = finding.evidence?.value;
                  const isNeedsReview = finding.status?.toLowerCase() === 'needs_human_review';

                  return (
                    <React.Fragment key={key}>
                      <tr
                        onClick={() => setExpandedRule(isExpanded ? null : key)}
                        className={`hover:bg-slate-800/40 cursor-pointer transition ${
                          isExpanded ? 'bg-slate-800/60' : ''
                        }`}
                      >
                        <td className="py-3 px-4 text-slate-500">
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-brand-400" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </td>
                        <td className="py-3 px-4 font-bold text-brand-300">
                          {finding.rule_id}
                        </td>
                        <td className="py-3 px-4 text-slate-300">
                          {finding.deviceId}
                        </td>
                        <td className="py-3 px-4 text-slate-200 font-sans max-w-xs truncate">
                          {finding.title}
                        </td>
                        <td className="py-3 px-4">
                          {getSeverityBadge(finding.severity)}
                        </td>
                        <td className="py-3 px-4">
                          {isNeedsReview ? (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                if (onOpenHumanReview) onOpenHumanReview(finding);
                              }}
                              className="px-2.5 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-[10px] font-mono font-bold flex items-center gap-1.5 transition shadow-sm animate-pulse"
                              title="Click to inspect and decide PASS or FAIL"
                            >
                              <span>NEEDS HUMAN REVIEW</span>
                              <span className="text-[10px] text-amber-200 underline">Decide ➔</span>
                            </button>
                          ) : (
                            <StatusBadge status={finding.status} size="sm" />
                          )}
                        </td>
                        <td className="py-3 px-4 text-slate-300 truncate max-w-[140px]">
                          {observedVal === null ? 'null' : String(observedVal)}
                        </td>
                      </tr>

                      {/* Expanded Evidence & Remediation Drawer */}
                      {isExpanded && (
                        <tr className="bg-slate-950/80 border-b border-slate-800">
                          <td colSpan={7} className="p-4 pl-12 space-y-3 font-sans">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 font-mono">
                                  COMPLIANCE LOGIC & EVIDENCE
                                </h4>
                                <div className="text-xs bg-slate-900 p-3 rounded-lg border border-slate-800 space-y-1.5 font-mono">
                                  <div>
                                    <span className="text-slate-500">Baseline Field: </span>
                                    <span className="text-brand-300">{finding.baseline_field_path}</span>
                                  </div>
                                  <div>
                                    <span className="text-slate-500">Expected: </span>
                                    <span className="text-white">
                                      {finding.operator ? `${finding.operator} ` : ''}
                                      {JSON.stringify(finding.expected)}
                                    </span>
                                  </div>
                                  <div>
                                    <span className="text-slate-500">Observed: </span>
                                    <span className="text-emerald-300">{String(observedVal)}</span>
                                  </div>
                                  <div>
                                    <span className="text-slate-500">Provenance: </span>
                                    <span className="text-slate-400">
                                      {finding.evidence?.source?.file || finding.deviceId}:L{finding.evidence?.source?.line || 'N/A'}
                                    </span>
                                  </div>
                                  {finding.evidence?.source?.raw && (
                                    <div className="text-slate-400 mt-1 bg-slate-950 p-2 rounded border border-slate-800 text-[11px]">
                                      CLI Evidence: <span className="text-amber-300">"{finding.evidence.source.raw}"</span>
                                    </div>
                                  )}
                                </div>
                              </div>

                              <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 font-mono flex items-center gap-1.5">
                                    <Wrench className="w-3.5 h-3.5 text-brand-400" />
                                    STEP-BY-STEP REMEDIATION & CLI FIX
                                  </h4>
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      const fixCmd = finding.rule_id === 'CIS-MGMT-01' ? 'line vty 0 4\n transport input ssh\n exit' : 
                                       finding.rule_id === 'CIS-AUTH-02' ? 'security passwords min-length 14' :
                                       finding.rule_id === 'CIS-AUTH-03' ? 'set system login retry-options tries-before-disconnect 5' :
                                       `# Remediate ${finding.rule_id} on ${finding.deviceId}`;
                                      navigator.clipboard.writeText(fixCmd);
                                      alert('Copied remediation payload to clipboard!');
                                    }}
                                    className="px-2.5 py-1 rounded-md bg-emerald-600/80 hover:bg-emerald-500 text-white font-mono text-[10px] font-bold flex items-center gap-1 transition shadow"
                                    title="Copy exact configuration payload"
                                  >
                                    📋 Copy Fix Payload
                                  </button>
                                </div>
                                <div className="text-xs bg-slate-900 p-3 rounded-lg border border-slate-800 font-mono space-y-2">
                                  <div className="text-slate-400 font-sans text-[11px]">
                                    <span className="font-bold text-amber-300">Step 1:</span> Access device terminal / configuration mode (`configure terminal` or `edit`).<br />
                                    <span className="font-bold text-amber-300">Step 2:</span> Apply the vendor-specific compliance block below.<br />
                                    <span className="font-bold text-amber-300">Step 3:</span> Save or commit the running configuration (`commit` or `write memory`).
                                  </div>
                                  <code className="text-emerald-300 bg-slate-950 px-2.5 py-1.5 rounded block border border-slate-800 whitespace-pre">
                                    {finding.rule_id === 'CIS-MGMT-01' ? 'line vty 0 4\n transport input ssh\n exit' : 
                                     finding.rule_id === 'CIS-AUTH-02' ? 'security passwords min-length 14' :
                                     finding.rule_id === 'CIS-AUTH-03' ? 'set system login retry-options tries-before-disconnect 5' :
                                     `# Apply hardening for ${finding.rule_id} on ${finding.deviceId}`}
                                  </code>
                                </div>

                                {finding.status?.toLowerCase() === 'needs_human_review' && (
                                  <div className="pt-2">
                                    <button
                                      type="button"
                                      onClick={() => onOpenHumanReview && onOpenHumanReview(finding)}
                                      className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 text-white font-mono font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-amber-500/20 transition"
                                    >
                                      <AlertCircle className="w-4 h-4" />
                                      <span>Click to Inspect Unknown Command & Decide (PASS / FAIL)</span>
                                    </button>
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
