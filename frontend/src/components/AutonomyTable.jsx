import React, { useState, useEffect, useMemo } from 'react';
import {
  ShieldCheck, Lock, UserCheck, AlertTriangle, Filter,
  CheckCircle2, XCircle, ChevronRight, Server, Terminal, Eye
} from 'lucide-react';
import api from '../api';
import StatusBadge from './StatusBadge';

export default function AutonomyTable({ fixtures = [], findingsByDevice = {}, onOpenHumanReview }) {
  const [autonomyData, setAutonomyData] = useState({});
  const [selectedFile, setSelectedFile] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    api.getAutonomy().then(data => {
      setAutonomyData(data.actions || {});
    }).catch(console.error);
  }, []);

  const deviceList = Object.keys(findingsByDevice).length > 0
    ? Object.keys(findingsByDevice)
    : fixtures.map(f => f.filename);

  // Group commands by file and filter
  const deviceCommands = useMemo(() => {
    const targetDevices = selectedFile === 'all' ? deviceList : [selectedFile];
    const results = [];

    for (const dev of targetDevices) {
      const findings = findingsByDevice[dev] || [];
      for (const f of findings) {
        const st = f.status?.toLowerCase() || 'not_applicable';
        if (statusFilter !== 'all' && st !== statusFilter) {
          continue;
        }

        results.push({
          ...f,
          deviceId: dev,
          statusLower: st,
          rawCommand: f.evidence?.source?.raw || `Rule ${f.rule_id} check`,
          line: f.evidence?.source?.line || 'N/A',
        });
      }
    }
    return results;
  }, [findingsByDevice, deviceList, selectedFile, statusFilter]);

  // Statistics for selected view
  const stats = useMemo(() => {
    let p = 0, fl = 0, h = 0;
    const targetDevices = selectedFile === 'all' ? deviceList : [selectedFile];
    for (const dev of targetDevices) {
      const findings = findingsByDevice[dev] || [];
      for (const f of findings) {
        const st = f.status?.toLowerCase();
        if (st === 'pass') p++;
        else if (st === 'fail') fl++;
        else if (st === 'needs_human_review') h++;
      }
    }
    return { pass: p, fail: fl, human: h, total: p + fl + h };
  }, [findingsByDevice, deviceList, selectedFile]);

  const getLevelBadge = (level) => {
    const configs = {
      autonomous: {
        bg: 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40',
        label: 'AUTONOMOUS',
      },
      autonomous_above_threshold: {
        bg: 'bg-blue-950/80 text-blue-300 border-blue-500/40',
        label: 'AUTONOMOUS ABOVE THRESHOLD',
      },
      requires_human: {
        bg: 'bg-amber-950/80 text-amber-300 border-amber-500/40',
        label: 'REQUIRES HUMAN',
      },
      never_autonomous: {
        bg: 'bg-rose-950/80 text-rose-300 border-rose-500/40',
        label: 'NEVER AUTONOMOUS',
      },
      out_of_scope: {
        bg: 'bg-slate-900 text-slate-400 border-slate-700',
        label: 'OUT OF SCOPE',
      },
    }[level] || {
      bg: 'bg-slate-800 text-slate-300 border-slate-700',
      label: level.toUpperCase(),
    };

    return (
      <span className={`px-2.5 py-1 text-[11px] font-mono font-bold rounded-full border ${configs.bg}`}>
        {configs.label}
      </span>
    );
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Configuration Command Autonomy Explorer */}
      <div className="glass-panel p-6 rounded-2xl border border-brand-500/30 bg-gradient-to-r from-[#0a1020] via-[#0d1326] to-[#070b14] shadow-xl space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-brand-950/80 border border-brand-500/40 flex items-center justify-center text-brand-400 shadow-lg shadow-brand-500/20">
              <Terminal className="w-6 h-6" />
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-brand-950 border border-brand-500/40 text-[10px] font-mono text-brand-300 font-bold mb-1">
                <span>CONFIG-SCOPED AUTONOMY & VERDICTS</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              </div>
              <h2 className="text-xl font-black font-mono text-white tracking-wide">
                CONFIGURATION AUDIT VERDICTS & COMMANDS
              </h2>
              <p className="text-xs text-slate-400">
                Filter by configuration file to inspect all passed, failed, and human-gated commands
              </p>
            </div>
          </div>

          {/* Config Filter Selector */}
          <div className="flex items-center gap-2 bg-[#050811] px-3.5 py-2 rounded-xl border border-slate-700">
            <Filter className="w-4 h-4 text-brand-400 shrink-0" />
            <span className="text-xs font-mono text-slate-400">Config:</span>
            <select
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              className="bg-transparent text-xs font-mono text-white font-bold focus:outline-none cursor-pointer"
            >
              <option value="all" className="bg-[#0c1222] text-white">All Config Files ({deviceList.length})</option>
              {deviceList.map(dev => (
                <option key={dev} value={dev} className="bg-[#0c1222] text-white">
                  {dev}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Verdict Filters & Counters */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <button
            type="button"
            onClick={() => setStatusFilter('all')}
            className={`p-3 rounded-xl border text-left font-mono transition ${
              statusFilter === 'all'
                ? 'bg-slate-800 border-brand-400 text-white shadow-md shadow-brand-500/20'
                : 'bg-[#050811] border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="text-[10px] uppercase text-slate-400">All Commands</div>
            <div className="text-lg font-black text-white mt-0.5">{stats.total}</div>
          </button>

          <button
            type="button"
            onClick={() => setStatusFilter('pass')}
            className={`p-3 rounded-xl border text-left font-mono transition ${
              statusFilter === 'pass'
                ? 'bg-emerald-950/60 border-emerald-400 text-white shadow-md shadow-emerald-500/20'
                : 'bg-[#050811] border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="text-[10px] uppercase text-emerald-400">Passed ({stats.pass})</div>
            <div className="text-lg font-black text-emerald-400 mt-0.5">{stats.pass}</div>
          </button>

          <button
            type="button"
            onClick={() => setStatusFilter('fail')}
            className={`p-3 rounded-xl border text-left font-mono transition ${
              statusFilter === 'fail'
                ? 'bg-rose-950/60 border-rose-400 text-white shadow-md shadow-rose-500/20'
                : 'bg-[#050811] border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="text-[10px] uppercase text-rose-400">Failed ({stats.fail})</div>
            <div className="text-lg font-black text-rose-400 mt-0.5">{stats.fail}</div>
          </button>

          <button
            type="button"
            onClick={() => setStatusFilter('needs_human_review')}
            className={`p-3 rounded-xl border text-left font-mono transition ${
              statusFilter === 'needs_human_review'
                ? 'bg-amber-950/60 border-amber-400 text-white shadow-md shadow-amber-500/20'
                : 'bg-[#050811] border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="text-[10px] uppercase text-amber-400">Needs Human ({stats.human})</div>
            <div className="text-lg font-black text-amber-400 mt-0.5">{stats.human}</div>
          </button>
        </div>

        {/* Command Verdicts Table */}
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs border-collapse font-mono">
            <thead>
              <tr className="bg-slate-900/90 text-slate-400 border-b border-slate-800">
                <th className="py-3 px-4">CONFIG FILE</th>
                <th className="py-3 px-4">RULE ID</th>
                <th className="py-3 px-4">VERDICT</th>
                <th className="py-3 px-4">EVIDENCE / COMMAND</th>
                <th className="py-3 px-4">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {deviceCommands.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-500">
                    No commands matched the current filter. Run an audit in Mission Control first to view live verdicts.
                  </td>
                </tr>
              ) : (
                deviceCommands.map((cmd, idx) => {
                  const isHumanNeeded = cmd.statusLower === 'needs_human_review';
                  const isFailed = cmd.statusLower === 'fail';

                  return (
                    <tr key={`${cmd.deviceId}-${cmd.rule_id}-${idx}`} className="hover:bg-slate-800/40 transition">
                      <td className="py-2.5 px-4 font-bold text-slate-200">{cmd.deviceId}</td>
                      <td className="py-2.5 px-4 text-brand-300 font-semibold">{cmd.rule_id}</td>
                      <td className="py-2.5 px-4">
                        {isHumanNeeded ? (
                          <span className="px-2 py-0.5 rounded bg-amber-950/80 border border-amber-500/50 text-amber-300 text-[10px] font-bold">
                            NEEDS HUMAN
                          </span>
                        ) : isFailed ? (
                          <span className="px-2 py-0.5 rounded bg-rose-950/80 border border-rose-500/50 text-rose-300 text-[10px] font-bold">
                            FAIL
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 text-[10px] font-bold">
                            PASS
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-4 text-slate-300 max-w-md truncate">
                        <span className="text-slate-500">L{cmd.line}: </span>
                        <span>{cmd.rawCommand}</span>
                      </td>
                      <td className="py-2.5 px-4">
                        {isHumanNeeded && (
                          <button
                            type="button"
                            onClick={() => onOpenHumanReview && onOpenHumanReview(cmd)}
                            className="px-2.5 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-[10px] font-bold flex items-center gap-1 transition"
                          >
                            <span>Resolve</span>
                            <ChevronRight className="w-3 h-3" />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Static Enforced Autonomy Table Definition */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <h2 className="text-lg font-bold text-white font-mono flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-brand-400" />
          ENFORCED AUTONOMY BOUNDARY POLICY MATRIX
        </h2>
        <p className="text-xs text-slate-400">
          This boundary matrix is enforced in code (<code className="text-brand-300">policies/autonomy.py</code>),
          guaranteeing that high-stakes security actions strictly halt for human confirmation.
        </p>

        <div className="overflow-hidden rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-900/90 text-slate-400 font-mono border-b border-slate-800">
                <th className="py-3 px-4">ACTION</th>
                <th className="py-3 px-4">AUTONOMY LEVEL</th>
                <th className="py-3 px-4">ENFORCED RATIONALE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {Object.entries(autonomyData).map(([action, meta]) => (
                <tr key={action} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-4 font-bold text-brand-300">{action}</td>
                  <td className="py-3 px-4">{getLevelBadge(meta.level)}</td>
                  <td className="py-3 px-4 text-slate-300 font-sans text-xs">{meta.rationale}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
