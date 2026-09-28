import React, { useState, useMemo, useCallback } from 'react';
import {
  XCircle, AlertTriangle, Filter, Terminal, Wrench,
  CheckCircle2, Copy, ShieldAlert, Server, FileText,
  Send, PhoneCall, FlaskConical, ShieldCheck, ShieldX,
  ChevronDown, ChevronUp, Download, Rocket, Trash2,
  Loader2, RotateCcw, Eye, AlertOctagon
} from 'lucide-react';
import api from '../api';
import StatusBadge from './StatusBadge';

// ── Static fallback CLI fixes (shown instantly, before sandbox) ──────────────
const KNOWN_FIXES = {
  'CIS-MGMT-01': 'line vty 0 4\n transport input ssh\n exit',
  'CIS-MGMT-02': 'ip ssh version 2',
  'CIS-MGMT-03': 'no ip http server',
  'CIS-MGMT-04': 'ip http secure-server',
  'CIS-MGMT-05': 'no snmp-server community public\nsnmp-server community <unique_secret> RO',
  'CIS-MGMT-07': 'line vty 0 4\n exec-timeout 10 0\n exit',
  'CIS-AUTH-01': 'service password-encryption',
  'CIS-AUTH-02': 'security passwords min-length 14',
  'CIS-AUTH-03': 'aaa authentication login default local\nlogin block-for 900 attempts 5 within 300',
  'CIS-LOG-01':  'logging host 192.0.2.100',
  'CIS-LOG-02':  'logging buffered 50000',
  'CIS-CRYPTO-01': 'ip ssh version 2\nip ssh dh-group-exchange min 2048 max 4096 optimal 4096',
};

// ── Sandbox status for a single finding (keyed by deviceId+ruleId) ──────────
// Shape: { phase, session_id, fixes, validation, promotion, error }
// phase: idle | proposing | testing | done | promoting | promoted | failed

// ── Gate pill component ───────────────────────────────────────────────────────
function GatePill({ label, passed, loading }) {
  if (loading) return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-slate-800 text-slate-400 border border-slate-700">
      <Loader2 className="w-3 h-3 animate-spin" /> {label}
    </span>
  );
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border ${
      passed
        ? 'bg-emerald-950 text-emerald-300 border-emerald-700/60'
        : 'bg-rose-950 text-rose-300 border-rose-700/60'
    }`}>
      {passed ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
      {label}
    </span>
  );
}

// ── Diff viewer (collapsible) ─────────────────────────────────────────────────
function DiffBlock({ diff }) {
  const [open, setOpen] = useState(false);
  if (!diff) return null;
  const lines = diff.split('\n');
  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 text-[11px] font-mono text-brand-400 hover:text-brand-300 transition"
      >
        <Eye className="w-3.5 h-3.5" />
        {open ? 'Hide diff' : 'View config diff'}
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>
      {open && (
        <pre className="mt-2 bg-slate-950 border border-slate-800 rounded-lg p-3 text-[10px] font-mono overflow-x-auto max-h-48 overflow-y-auto leading-relaxed">
          {lines.map((ln, i) => (
            <div
              key={i}
              className={
                ln.startsWith('+') && !ln.startsWith('+++') ? 'text-emerald-400' :
                ln.startsWith('-') && !ln.startsWith('---') ? 'text-rose-400' :
                ln.startsWith('@@') ? 'text-brand-400' :
                'text-slate-400'
              }
            >
              {ln}
            </div>
          ))}
        </pre>
      )}
    </div>
  );
}

// ── Per-finding sandbox panel ─────────────────────────────────────────────────
function SandboxPanel({ sandboxState, onTestFix, onPromote, onDiscard, finding, username }) {
  const { phase, fixes, validation, promotion, error, diff } = sandboxState;
  const gates = validation?.gates;

  // Download diff as .patch file
  const handleDownloadDiff = () => {
    if (!diff) return;
    const blob = new Blob([diff], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${finding.deviceId}_${finding.rule_id}.patch`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ── Idle: show "Test Fix in Sandbox" button ──
  if (phase === 'idle') {
    return (
      <div className="mt-3 pt-3 border-t border-slate-800">
        <button
          type="button"
          onClick={onTestFix}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-gradient-to-r from-brand-700 to-cyan-700 hover:from-brand-600 hover:to-cyan-600 text-white font-mono font-bold text-xs shadow-md shadow-brand-500/20 transition cursor-pointer"
        >
          <FlaskConical className="w-4 h-4" />
          Test Fix in Sandbox
        </button>
        <p className="mt-1.5 text-[10px] text-slate-500 font-mono">
          Applies fix to isolated candidate · validates 4 gates · never touches original
        </p>
      </div>
    );
  }

  // ── Proposing / testing: spinner ──
  if (phase === 'proposing' || phase === 'testing') {
    const label = phase === 'proposing' ? 'Generating fix proposals…' : 'Running sandbox validation…';
    return (
      <div className="mt-3 pt-3 border-t border-slate-800 flex items-center gap-2 text-xs font-mono text-slate-400">
        <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
        {label}
      </div>
    );
  }

  // ── Error ──
  if (phase === 'failed') {
    return (
      <div className="mt-3 pt-3 border-t border-slate-800 space-y-2">
        <div className="flex items-start gap-2 p-2.5 rounded-lg bg-rose-950/60 border border-rose-700/50 text-xs font-mono text-rose-300">
          <AlertOctagon className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold">Sandbox error</div>
            <div className="text-rose-400/80 mt-0.5">{error}</div>
          </div>
        </div>
        <button type="button" onClick={onTestFix}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs transition cursor-pointer">
          <RotateCcw className="w-3.5 h-3.5" /> Retry
        </button>
      </div>
    );
  }

  // ── Done (validation result shown) ──
  if (phase === 'done' || phase === 'promoting' || phase === 'promoted') {
    const allPassed = validation?.passed;
    return (
      <div className="mt-3 pt-3 border-t border-slate-800 space-y-3">

        {/* Gate status strip */}
        <div className="space-y-1.5">
          <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <FlaskConical className="w-3.5 h-3.5 text-brand-400" />
            Sandbox Validation
            {allPassed
              ? <span className="ml-auto text-emerald-400 flex items-center gap-1"><ShieldCheck className="w-3.5 h-3.5" /> ALL GATES PASSED</span>
              : <span className="ml-auto text-rose-400 flex items-center gap-1"><ShieldX className="w-3.5 h-3.5" /> BLOCKED</span>
            }
          </div>
          <div className="flex flex-wrap gap-1.5">
            <GatePill label="Syntax"     passed={gates?.syntax_validation?.passed} />
            <GatePill label="Target Fix" passed={gates?.target_resolution?.passed} />
            <GatePill label="No Regress" passed={gates?.regression_audit?.passed} />
            <GatePill label="Invariants" passed={gates?.security_invariants?.passed} />
          </div>

          {/* Target resolution detail when failing */}
          {!gates?.target_resolution?.passed && (
            <div className="text-[10px] font-mono text-rose-400/80 pl-1">
              {(gates?.target_resolution?.details?.unresolved || []).map((u, i) => (
                <div key={i}>↳ {u.rule_id}: {u.reason}</div>
              ))}
            </div>
          )}

          {/* Regression detail */}
          {!gates?.regression_audit?.passed && (
            <div className="text-[10px] font-mono text-rose-400/80 pl-1">
              {(gates?.regression_audit?.details?.regressions || []).map((r, i) => (
                <div key={i}>↳ {r.rule_id} introduced ({r.severity})</div>
              ))}
            </div>
          )}

          {/* Summary */}
          {validation?.summary && (
            <p className="text-[10px] text-slate-500 font-mono">{validation.summary}</p>
          )}
        </div>

        {/* Fixes applied */}
        {fixes && fixes.length > 0 && (
          <div className="space-y-1">
            <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
              Applied Fixes ({fixes.length})
            </div>
            {fixes.map((fix, i) => (
              <div key={i} className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-[10px] font-mono">
                <span className="text-brand-400">{fix.rule_id}</span>
                <span className="text-slate-500 mx-1.5">·</span>
                <span className="text-slate-300">{fix.description}</span>
              </div>
            ))}
          </div>
        )}

        {/* Diff */}
        <DiffBlock diff={diff} />

        {/* Action buttons */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          {allPassed && phase !== 'promoted' && (
            <button
              type="button"
              onClick={onPromote}
              disabled={phase === 'promoting'}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-gradient-to-r from-emerald-700 to-teal-700 hover:from-emerald-600 hover:to-teal-600 disabled:opacity-50 text-white font-mono font-bold text-xs shadow-md shadow-emerald-500/20 transition cursor-pointer"
            >
              {phase === 'promoting'
                ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Promoting…</>
                : <><Rocket className="w-3.5 h-3.5" /> Promote to Fixed</>
              }
            </button>
          )}

          {phase === 'promoted' && (
            <div className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-emerald-950 border border-emerald-700/50 text-emerald-300 font-mono font-bold text-xs">
              <CheckCircle2 className="w-4 h-4" />
              Promoted — {promotion?.promoted_path || 'output/fixed/'}
            </div>
          )}

          {diff && (
            <button type="button" onClick={handleDownloadDiff}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs transition cursor-pointer">
              <Download className="w-3.5 h-3.5" /> Diff
            </button>
          )}

          {phase !== 'promoted' && (
            <button type="button" onClick={onDiscard}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-rose-950 text-slate-500 hover:text-rose-400 font-mono text-xs transition cursor-pointer ml-auto">
              <Trash2 className="w-3.5 h-3.5" /> Discard
            </button>
          )}
        </div>

        {/* Promotion blocked message */}
        {!allPassed && (
          <div className="flex items-start gap-2 p-2.5 rounded-lg bg-amber-950/40 border border-amber-700/40 text-[11px] font-mono text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-400" />
            Promotion blocked. Fix the root cause and retry.
          </div>
        )}
      </div>
    );
  }

  return null;
}

// ── Main component ────────────────────────────────────────────────────────────
export default function FailedRulesView({ findingsByDevice = {}, rules = [], fixtures = [], onOpenHumanReview }) {
  const [selectedFile, setSelectedFile] = useState('all');
  const [copiedId, setCopiedId]         = useState(null);

  // Vendor solution state (unchanged flow for no-known-fix cards)
  const [vendorSolutions, setVendorSolutions]       = useState({});
  const [submittingSolution, setSubmittingSolution] = useState(null);
  const [submissionFeedback, setSubmissionFeedback] = useState({});

  // Sandbox state map: key = `${deviceId}_${ruleId}`
  const [sandboxMap, setSandboxMap] = useState({});

  const currentUser = useMemo(() => {
    try { return JSON.parse(localStorage.getItem('ntro_user') || 'null'); } catch { return null; }
  }, []);
  const username = currentUser?.username || currentUser?.email || 'admin';

  const deviceList = useMemo(() => {
    const fromFindings = Object.keys(findingsByDevice);
    return fromFindings.length > 0 ? fromFindings : fixtures.map(f => f.filename);
  }, [findingsByDevice, fixtures]);

  const failedFindings = useMemo(() => {
    const list = [];
    const targets = selectedFile === 'all' ? deviceList : [selectedFile];
    for (const dev of targets) {
      for (const f of (findingsByDevice[dev] || [])) {
        if (f.status?.toLowerCase() === 'fail') {
          const meta     = rules.find(r => r.id === f.rule_id) || {};
          const knownFix = KNOWN_FIXES[f.rule_id] || f.remediation_cli || f.remediation?.cli_commands;
          list.push({
            ...f,
            deviceId:    dev,
            title:       meta.title       || f.rule_id,
            description: meta.description || '',
            severity:    meta.severity    || f.severity || 'high',
            operator:    meta.evaluation?.operator,
            expected:    meta.evaluation?.expected,
            hasKnownFix: !!knownFix,
            fixSyntax:   knownFix || null,
          });
        }
      }
    }
    return list;
  }, [findingsByDevice, rules, selectedFile, deviceList]);

  // ── Copy static fix ──────────────────────────────────────────────────────
  const handleCopyRemediation = (finding) => {
    const txt = finding.fixSyntax || `# Fix for ${finding.baseline_field_path}`;
    navigator.clipboard.writeText(txt);
    setCopiedId(finding.rule_id + finding.deviceId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // ── Sandbox helpers ───────────────────────────────────────────────────────
  const setSandbox = useCallback((key, patch) =>
    setSandboxMap(prev => ({ ...prev, [key]: { ...(prev[key] || {}), ...patch } })),
  []);

  const handleTestFix = useCallback(async (finding) => {
    const key = `${finding.deviceId}_${finding.rule_id}`;
    setSandbox(key, { phase: 'proposing', error: null, fixes: null, validation: null, promotion: null, diff: null });

    try {
      // STEP 1 — propose (also creates the sandbox session)
      const proposeRes = await api.remediationPropose(finding.deviceId, username);

      if (!proposeRes.success) {
        setSandbox(key, { phase: 'failed', error: proposeRes.message || 'Propose failed' });
        return;
      }

      if (!proposeRes.session_id) {
        // No violations found or config not audited yet
        setSandbox(key, { phase: 'failed', error: proposeRes.message || 'No session created — run an audit first' });
        return;
      }

      setSandbox(key, {
        phase:      'testing',
        session_id: proposeRes.session_id,
        fixes:      proposeRes.proposed_fixes || [],
      });

      // STEP 2 — sandbox test (4-gate validation)
      const testRes = await api.remediationSandboxTest(proposeRes.session_id);

      // Fetch diff
      let diff = testRes.diff || null;
      if (!diff) {
        try {
          const det = await api.remediationGetSession(proposeRes.session_id);
          diff = det.diff || null;
        } catch (_) {}
      }

      setSandbox(key, {
        phase:      'done',
        validation: testRes.validation || testRes.validation_result,
        diff,
      });

    } catch (err) {
      setSandbox(key, {
        phase: 'failed',
        error: err?.response?.data?.detail || err?.message || 'Unknown error',
      });
    }
  }, [username, setSandbox]);

  const handlePromote = useCallback(async (finding) => {
    const key = `${finding.deviceId}_${finding.rule_id}`;
    const { session_id } = sandboxMap[key] || {};
    if (!session_id) return;

    setSandbox(key, { phase: 'promoting' });
    try {
      const res = await api.remediationPromote(session_id, username);
      if (res.success) {
        setSandbox(key, { phase: 'promoted', promotion: res });
      } else if (res.decision === 'DEFERRED') {
        // Critical change — ask user to force-approve
        const ok = window.confirm(
          `⚠ Human review required:\n${res.rationale}\n\nApprove anyway?`
        );
        if (ok) {
          const res2 = await api.remediationPromote(session_id, username, true);
          setSandbox(key, { phase: res2.success ? 'promoted' : 'done', promotion: res2 });
        } else {
          setSandbox(key, { phase: 'done' });
        }
      } else {
        setSandbox(key, {
          phase: 'done',
          error: res.rationale || 'Promotion blocked',
        });
      }
    } catch (err) {
      setSandbox(key, {
        phase: 'done',
        error: err?.response?.data?.detail || err?.message || 'Promotion failed',
      });
    }
  }, [sandboxMap, username, setSandbox]);

  const handleDiscard = useCallback(async (finding) => {
    const key = `${finding.deviceId}_${finding.rule_id}`;
    const { session_id } = sandboxMap[key] || {};
    if (session_id) {
      try { await api.remediationDeleteSession(session_id); } catch (_) {}
    }
    setSandboxMap(prev => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }, [sandboxMap]);

  // ── Submit vendor solution ────────────────────────────────────────────────
  const handleSubmitVendorSolution = async (finding) => {
    const key = `${finding.deviceId}_${finding.rule_id}`;
    const solutionText = vendorSolutions[key];
    if (!solutionText?.trim()) return;
    setSubmittingSolution(key);
    try {
      const res = await api.submitVendorSolution({
        device_id:   finding.deviceId,
        rule_id:     finding.rule_id,
        command_raw: String(finding.evidence?.value ?? finding.baseline_field_path),
        solution_text: solutionText.trim(),
        vendor_name: `${finding.deviceId.split('_')[1] || 'Vendor'} Support`,
        provider:    currentUser?.full_name || username,
        username,
      });
      setSubmissionFeedback(prev => ({
        ...prev,
        [key]: { type: 'success', text: `✓ Learned via Federated Learning Round #${res.federated_round?.round_id || 1}` },
      }));
    } catch (err) {
      setSubmissionFeedback(prev => ({
        ...prev,
        [key]: { type: 'error', text: err?.response?.data?.detail || 'Submission failed.' },
      }));
    } finally {
      setSubmittingSolution(null);
    }
  };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6 max-w-6xl mx-auto font-sans">

      {/* Header */}
      <div className="glass-panel p-6 rounded-2xl border border-rose-500/30 bg-gradient-to-r from-[#12070e] via-[#0d111d] to-[#070b14] shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-rose-950/80 border border-rose-500/40 flex items-center justify-center text-rose-400 shadow-lg shadow-rose-500/20">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-rose-950 border border-rose-500/40 text-[10px] font-mono text-rose-300 font-bold mb-1">
                NON-COMPLIANT FINDINGS &amp; REMEDIATION
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
              </div>
              <h2 className="text-xl font-black font-mono text-white tracking-wide">
                FAILED COMMANDS &amp; REMEDIATION WORKBENCH
              </h2>
              <p className="text-xs text-slate-400">
                Click <span className="text-brand-400 font-semibold">Test Fix in Sandbox</span> to validate any fix through 4 gates before promoting to your configuration.
              </p>
            </div>
          </div>

          {/* File filter */}
          <div className="flex items-center gap-2 bg-[#050811] px-3.5 py-2 rounded-xl border border-slate-700">
            <Filter className="w-4 h-4 text-brand-400 shrink-0" />
            <span className="text-xs font-mono text-slate-400">Config:</span>
            <select
              value={selectedFile}
              onChange={e => setSelectedFile(e.target.value)}
              className="bg-transparent text-xs font-mono text-white font-bold focus:outline-none cursor-pointer"
            >
              <option value="all" className="bg-[#0c1222]">All ({deviceList.length})</option>
              {deviceList.map(dev => {
                const n = (findingsByDevice[dev] || []).filter(f => f.status?.toLowerCase() === 'fail').length;
                return <option key={dev} value={dev} className="bg-[#0c1222]">{dev} ({n} failed)</option>;
              })}
            </select>
          </div>
        </div>
      </div>

      {/* Metrics strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: 'TOTAL FAILED', value: failedFindings.length, color: 'text-rose-400', sub: 'Strict CIS Failures' },
          { label: 'KNOWN FIXES',  value: failedFindings.filter(f => f.hasKnownFix).length, color: 'text-emerald-400', sub: '1-Click CLI Payloads' },
          { label: 'SANDBOX READY', value: Object.values(sandboxMap).filter(s => s.phase === 'done' || s.phase === 'promoted').length, color: 'text-brand-400', sub: 'Validated Sessions' },
        ].map(m => (
          <div key={m.label} className="glass-panel p-4 rounded-xl border border-slate-800 bg-[#0c1222]/80 font-mono text-xs">
            <div className="text-slate-400 uppercase text-[10px]">{m.label}</div>
            <div className={`text-2xl font-black mt-1 ${m.color}`}>{m.value}</div>
            <div className="text-[10px] text-slate-500 mt-0.5">{m.sub}</div>
          </div>
        ))}
      </div>

      {/* Finding cards */}
      {failedFindings.length === 0 ? (
        <div className="glass-panel p-12 rounded-2xl border border-slate-800 text-center space-y-3 font-mono">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
          <h3 className="text-base font-bold text-white">No Failed Directives</h3>
          <p className="text-xs text-slate-400">All checks passed or require human review.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {failedFindings.map((finding, idx) => {
            const cardKey   = `${finding.deviceId}_${finding.rule_id}`;
            const sbState   = sandboxMap[cardKey] || { phase: 'idle' };
            const isCopied  = copiedId === cardKey;
            const feedback  = submissionFeedback[cardKey];

            return (
              <div key={idx} className="glass-panel p-5 rounded-2xl border border-rose-500/30 bg-[#090e18] shadow-lg space-y-4">

                {/* Card header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 font-mono font-bold text-xs border border-rose-500/40">
                      {finding.rule_id}
                    </span>
                    <span className="font-mono text-sm font-bold text-white">{finding.title}</span>
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300 text-[11px] font-mono">
                      {finding.deviceId}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 font-mono shrink-0">
                    <span className="px-2 py-0.5 rounded bg-rose-900/40 text-rose-300 border border-rose-700/50 text-[10px] font-bold">FAIL</span>
                    <span className="text-slate-400 text-[10px]">
                      Severity: <span className="text-amber-400 uppercase font-bold">{finding.severity}</span>
                    </span>
                  </div>
                </div>

                {/* Body: root cause + fix side-by-side */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">

                  {/* Left: Root cause */}
                  <div className="space-y-2 bg-[#050811] p-3.5 rounded-xl border border-slate-800">
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                      <XCircle className="w-3.5 h-3.5 text-rose-400" /> FAILURE ROOT CAUSE
                    </div>
                    <div className="space-y-1 text-slate-300">
                      <div><span className="text-slate-500">Path: </span><span className="text-brand-300">{finding.baseline_field_path}</span></div>
                      <div><span className="text-slate-500">Expected: </span><span className="text-emerald-400 font-bold">{JSON.stringify(finding.expected)}</span></div>
                      <div><span className="text-slate-500">Observed: </span><span className="text-rose-400 font-bold">{String(finding.evidence?.value ?? 'insecure_default')}</span></div>
                    </div>
                    {finding.description && (
                      <p className="text-[11px] text-slate-400 font-sans pt-1 border-t border-slate-800/80">{finding.description}</p>
                    )}
                  </div>

                  {/* Right: CLI fix (static) or vendor input */}
                  <div className="space-y-3 bg-[#050811] p-3.5 rounded-xl border border-slate-800">
                    {finding.hasKnownFix ? (
                      <>
                        <div className="flex items-center justify-between">
                          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                            <Wrench className="w-3.5 h-3.5 text-emerald-400" /> CLI FIX PAYLOAD
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
                            {isCopied ? 'COPIED!' : 'COPY'}
                          </button>
                        </div>
                        <div className="text-[11px] text-slate-400 font-sans space-y-0.5">
                          <div>1. Enter privileged config mode (<code>configure terminal</code>).</div>
                          <div>2. Paste payload below and commit changes.</div>
                        </div>
                        <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-[11px] text-emerald-300 font-mono overflow-x-auto whitespace-pre">
                          <code>{finding.fixSyntax}</code>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="p-2.5 rounded-lg bg-amber-950/60 border border-amber-500/40 flex items-start gap-2 text-xs font-mono text-amber-200">
                          <PhoneCall className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                          <div>
                            <div className="font-bold text-amber-300">No automated fix indexed.</div>
                            <div className="text-[11px] text-amber-300/80 font-sans mt-0.5">Contact vendor or paste a fix below to train the agent.</div>
                          </div>
                        </div>
                        <label className="block text-[11px] font-mono font-bold text-slate-300">PROVIDE VENDOR FIX:</label>
                        <textarea
                          rows={2}
                          value={vendorSolutions[cardKey] || ''}
                          onChange={e => setVendorSolutions(p => ({ ...p, [cardKey]: e.target.value }))}
                          placeholder="Paste vendor CLI fix here…"
                          className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                        />
                        <button
                          type="button"
                          disabled={submittingSolution === cardKey || !vendorSolutions[cardKey]?.trim()}
                          onClick={() => handleSubmitVendorSolution(finding)}
                          className="w-full py-2 px-3 rounded-lg bg-gradient-to-r from-brand-600 to-cyan-600 hover:from-brand-500 hover:to-cyan-500 text-white font-mono font-bold text-xs flex items-center justify-center gap-1.5 shadow-md shadow-brand-500/20 transition disabled:opacity-50 cursor-pointer"
                        >
                          <Send className="w-3.5 h-3.5" />
                          {submittingSolution === cardKey ? 'Training via Federated Learning…' : 'Submit & Train Agent'}
                        </button>
                        {feedback && (
                          <div className={`p-2 rounded-lg text-[11px] font-mono ${
                            feedback.type === 'success' ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40' : 'bg-rose-950 text-rose-300'
                          }`}>{feedback.text}</div>
                        )}
                      </>
                    )}
                  </div>
                </div>

                {/* ── Sandbox panel (spans full width below the two columns) ── */}
                <SandboxPanel
                  sandboxState={sbState}
                  finding={finding}
                  username={username}
                  onTestFix={() => handleTestFix(finding)}
                  onPromote={() => handlePromote(finding)}
                  onDiscard={() => handleDiscard(finding)}
                />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
