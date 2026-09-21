import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ShieldAlert, CheckCircle2, UserCheck, Lock, Plus, ArrowRight,
  History, AlertOctagon, RotateCw, GitCompare
} from 'lucide-react';
import api from '../api';
import StatusBadge from './StatusBadge';

export default function RuleManagement({ onRuleActivated }) {
  const [rules, setRules] = useState([]);
  const [selectedRuleId, setSelectedRuleId] = useState('CIS-AUTH-02');
  const [ruleHistory, setRuleHistory] = useState([]);
  const [newExpected, setNewExpected] = useState('16');
  const [rationale, setRationale] = useState('Upgrade password policy to require minimum 16 characters (CIS 2.0)');
  const [reviewerName, setReviewerName] = useState('Reviewer_A (Lead Auditor)');
  const [loading, setLoading] = useState(false);
  const [reAuditDiffs, setReAuditDiffs] = useState(null);
  const [notification, setNotification] = useState(null);

  const fetchRulesAndHistory = async () => {
    try {
      const data = await api.getRules();
      setRules(data.rules || []);
      if (selectedRuleId) {
        const hist = await api.getRuleHistory(selectedRuleId);
        setRuleHistory(hist.versions || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchRulesAndHistory();
  }, [selectedRuleId]);

  const activeVersion = ruleHistory.find(v => v.status === 'active') || ruleHistory[0];
  const pendingVersion = ruleHistory.find(v => v.status === 'pending_approval' || v.status === 'approved_by_one' || v.status === 'approved');

  // 1. Propose Rule Change
  const handlePropose = async () => {
    setLoading(true);
    try {
      const updates = {
        evaluation: {
          operator: 'greater_than_or_equal',
          expected: parseInt(newExpected, 10),
        },
      };
      await api.proposeRule(selectedRuleId, updates, 'alice_security_architect', rationale);
      setNotification({ type: 'success', msg: `Proposed ${selectedRuleId} v2. Awaiting two-person approval.` });
      await fetchRulesAndHistory();
    } catch (err) {
      setNotification({ type: 'error', msg: err.response?.data?.detail || err.message });
    } finally {
      setLoading(false);
    }
  };

  // 2. Two-Person Approval
  const handleApprove = async (version, name, role) => {
    setLoading(true);
    try {
      await api.approveRule(selectedRuleId, version, name, role);
      setNotification({ type: 'success', msg: `${name} approved ${selectedRuleId} v${version}.` });
      await fetchRulesAndHistory();
    } catch (err) {
      setNotification({ type: 'error', msg: err.response?.data?.detail || err.message });
    } finally {
      setLoading(false);
    }
  };

  // 3. Activate Rule
  const handleActivate = async (version) => {
    setLoading(true);
    try {
      await api.activateRule(selectedRuleId, version);
      setNotification({ type: 'success', msg: `Rule ${selectedRuleId} v${version} ACTIVATED and recorded on Blockchain!` });
      await fetchRulesAndHistory();

      // Trigger re-audit diff
      const reAudit = await api.reAuditRule(selectedRuleId, version);
      setReAuditDiffs(reAudit.diffs || []);
      if (onRuleActivated) onRuleActivated();
    } catch (err) {
      setNotification({ type: 'error', msg: err.response?.data?.detail || err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header Notification */}
      {notification && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className={`p-4 rounded-xl border text-xs font-mono flex items-center justify-between ${
            notification.type === 'success'
              ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300'
              : 'bg-rose-950/60 border-rose-500/40 text-rose-300'
          }`}
        >
          <span>{notification.msg}</span>
          <button onClick={() => setNotification(null)} className="text-slate-400 hover:text-white">✕</button>
        </motion.div>
      )}

      {/* Top Banner / Explanation */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white font-mono flex items-center gap-2">
            <Lock className="w-5 h-5 text-brand-400" />
            RULE GOVERNANCE & TWO-PERSON APPROVAL
          </h2>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Important policy changes cannot be made arbitrarily by a single person.
            Rule updates create immutable versions (v1 is preserved), require two distinct authorized reviewers,
            and automatically re-audit all affected devices.
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="text-slate-400">Rule to Modify:</span>
          <select
            value={selectedRuleId}
            onChange={(e) => {
              setSelectedRuleId(e.target.value);
              setReAuditDiffs(null);
            }}
            className="bg-slate-900 border border-slate-700 text-brand-300 rounded-lg px-3 py-1.5 focus:outline-none focus:border-brand-500"
          >
            <option value="CIS-AUTH-02">CIS-AUTH-02 (Password Min Length)</option>
            <option value="CIS-MGMT-01">CIS-MGMT-01 (Telnet Access Disabled)</option>
            <option value="CIS-AUTH-03">CIS-AUTH-03 (Account Lockout)</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Rule Proposal & Approval State Machine */}
        <div className="space-y-6">
          {/* Active Version Card */}
          {activeVersion && (
            <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider">
                  CURRENT ACTIVE POLICY (V{activeVersion.version})
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 font-mono font-bold">
                  ACTIVE
                </span>
              </div>
              <div className="bg-[#050811] p-3 rounded-lg border border-slate-800 text-xs font-mono space-y-1">
                <div>Rule ID: <span className="text-white font-bold">{activeVersion.rule_id}</span></div>
                <div>Condition: <span className="text-brand-300">{activeVersion.baseline_field_path} &gt;= {activeVersion.evaluation?.expected}</span></div>
                <div>SHA-256 Hash: <span className="text-slate-500 text-[10px] truncate block">{activeVersion.sha256_hash}</span></div>
              </div>
            </div>
          )}

          {/* Propose Modification Card */}
          <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold font-mono text-white flex items-center gap-1.5">
              <Plus className="w-4 h-4 text-brand-400" />
              PROPOSE RULE CHANGE (CREATE V2)
            </h3>
            <p className="text-xs text-slate-400">
              Change minimum password length threshold from 14 to 16 characters. Notice that v1 will not be overwritten.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">New Expected Threshold:</label>
                <input
                  type="number"
                  value={newExpected}
                  onChange={(e) => setNewExpected(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Audit Rationale:</label>
                <input
                  type="text"
                  value={rationale}
                  onChange={(e) => setRationale(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-slate-300 focus:outline-none focus:border-brand-500"
                />
              </div>

              <button
                onClick={handlePropose}
                disabled={loading || (pendingVersion && pendingVersion.version >= 2)}
                className="w-full py-2 rounded-lg bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-mono font-semibold transition flex items-center justify-center gap-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                Submit Proposal for Multi-Person Review
              </button>
            </div>
          </div>

          {/* Two-Person Approval Controls */}
          {pendingVersion && pendingVersion.status !== 'active' && (
            <div className="glass-panel p-5 rounded-xl border border-amber-500/30 bg-amber-950/10 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold font-mono text-amber-300 flex items-center gap-1.5">
                  <UserCheck className="w-4 h-4" />
                  TWO-PERSON APPROVAL REQUIRED (V{pendingVersion.version})
                </h3>
                <span className="text-xs font-mono font-bold text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-500/40">
                  {pendingVersion.status.toUpperCase()}
                </span>
              </div>

              <div className="text-xs text-slate-300 space-y-2 font-mono bg-slate-900 p-3 rounded-lg border border-slate-800">
                <div className="flex items-center justify-between">
                  <span>Reviewer A (Security Lead):</span>
                  {pendingVersion.approvals.some(a => a.reviewer.includes('Reviewer_A')) ? (
                    <span className="text-emerald-400 font-bold">✓ APPROVED</span>
                  ) : (
                    <button
                      onClick={() => handleApprove(pendingVersion.version, 'Reviewer_A (Lead Auditor)', 'Lead Auditor')}
                      disabled={loading}
                      className="px-2.5 py-1 rounded bg-brand-600 hover:bg-brand-500 text-white text-[11px]"
                    >
                      Approve as Reviewer A
                    </button>
                  )}
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                  <span>Reviewer B (CISO / NTRO):</span>
                  {pendingVersion.approvals.some(a => a.reviewer.includes('Reviewer_B')) ? (
                    <span className="text-emerald-400 font-bold">✓ APPROVED</span>
                  ) : (
                    <button
                      onClick={() => handleApprove(pendingVersion.version, 'Reviewer_B (CISO Delegate)', 'CISO Delegate')}
                      disabled={loading || pendingVersion.approvals.length === 0}
                      className="px-2.5 py-1 rounded bg-purple-600 hover:bg-purple-500 disabled:opacity-40 text-white text-[11px]"
                    >
                      Approve as Reviewer B
                    </button>
                  )}
                </div>
              </div>

              {/* Activation Button */}
              {pendingVersion.approvals.length >= 2 ? (
                <button
                  onClick={() => handleActivate(pendingVersion.version)}
                  disabled={loading}
                  className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-bold transition shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-1.5"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Both Approved ➔ ACTIVATE RULE V{pendingVersion.version}
                </button>
              ) : (
                <div className="text-[11px] text-amber-400/90 font-mono text-center flex items-center justify-center gap-1.5">
                  <AlertOctagon className="w-3.5 h-3.5" />
                  Policy cannot be activated with only {pendingVersion.approvals.length}/2 approvals.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: Version History & Re-audit Diff */}
        <div className="space-y-6">
          {/* Preserved History View */}
          <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold font-mono text-white flex items-center gap-1.5">
              <History className="w-4 h-4 text-brand-400" />
              IMMUTABLE RULE VERSION HISTORY
            </h3>
            <div className="space-y-2 max-h-[220px] overflow-y-auto terminal-scroll pr-1">
              {ruleHistory.map((ver) => (
                <div
                  key={ver.version}
                  className={`p-3 rounded-lg border text-xs font-mono ${
                    ver.status === 'active'
                      ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
                      : ver.status === 'superseded'
                        ? 'bg-slate-900/50 border-slate-800 text-slate-500'
                        : 'bg-amber-950/30 border-amber-500/40 text-amber-200'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold">v{ver.version} — {ver.rule_id}</span>
                    <span className="text-[10px] uppercase font-bold">{ver.status}</span>
                  </div>
                  <div className="text-[11px] text-slate-300">
                    Threshold: &gt;= {ver.evaluation?.expected} | By: {ver.created_by}
                  </div>
                  <div className="text-[10px] text-slate-500 truncate mt-1">
                    SHA-256: {ver.sha256_hash}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Re-Audit Findings Diff View (STEP 15) */}
          <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold font-mono text-white flex items-center gap-1.5">
              <GitCompare className="w-4 h-4 text-brand-400" />
              STEP 15 — AUTOMATED RE-AUDIT FINDINGS DIFF
            </h3>
            <p className="text-xs text-slate-400">
              When a rule changes, the system immediately audits affected devices against the new policy.
            </p>

            {reAuditDiffs ? (
              <div className="space-y-2">
                {reAuditDiffs.map(diff => (
                  <div
                    key={diff.device_id}
                    className={`p-3 rounded-lg border text-xs font-mono flex items-center justify-between ${
                      diff.changed
                        ? 'bg-rose-950/30 border-rose-500/40 text-rose-300'
                        : 'bg-slate-900 border-slate-800 text-slate-400'
                    }`}
                  >
                    <div>
                      <span className="font-bold text-white">{diff.device_id}</span>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        v1 expected &gt;= {diff.before_expected} ➔ v2 expected &gt;= {diff.after_expected}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <StatusBadge status={diff.before_status} size="sm" />
                      <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                      <StatusBadge status={diff.after_status} size="sm" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500 font-mono text-xs border border-dashed border-slate-800 rounded-lg">
                Activate Rule v2 above to observe live before/after compliance transition
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
