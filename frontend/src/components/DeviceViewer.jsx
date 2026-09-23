import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Server, FileText, Cpu, Code, Trash2, Lock, Filter, Loader2 } from 'lucide-react';
import api from '../api';

// Coarse asset classes surfaced as filter pills. Labels mirror the backend's
// device_class_display so the two can never drift apart.
const CLASS_FILTERS = [
  { id: 'all', label: 'All Assets' },
  { id: 'network', label: 'Network Configs' },
  { id: 'firewall', label: 'Firewall Configs' },
  { id: 'iot', label: 'IoT Device Configs' },
];

const CLASS_STYLES = {
  network: 'bg-brand-950/70 text-brand-300 border-brand-500/40',
  firewall: 'bg-rose-950/70 text-rose-300 border-rose-500/40',
  iot: 'bg-purple-950/70 text-purple-300 border-purple-500/40',
  unknown: 'bg-slate-900 text-slate-400 border-slate-700',
};

export default function DeviceViewer({
  fixtures = [],
  onSelectDevice,
  selectedDeviceId,
  onDeviceRemoved,
  currentUser,
}) {
  const [activeDevice, setActiveDevice] = useState(selectedDeviceId || (fixtures[0]?.filename || null));
  const [baselineData, setBaselineData] = useState(null);
  const [loadingBaseline, setLoadingBaseline] = useState(false);
  const [viewMode, setViewMode] = useState('both'); // 'both' | 'raw' | 'normalized'
  const [classFilter, setClassFilter] = useState('all');
  const [deletingFile, setDeletingFile] = useState(null);
  const [deleteError, setDeleteError] = useState(null);

  const visibleFixtures = useMemo(
    () => (classFilter === 'all'
      ? fixtures
      : fixtures.filter(f => (f.device_class || 'unknown') === classFilter)),
    [fixtures, classFilter]
  );

  const classCounts = useMemo(() => {
    const counts = { all: fixtures.length };
    for (const f of fixtures) {
      const k = f.device_class || 'unknown';
      counts[k] = (counts[k] || 0) + 1;
    }
    return counts;
  }, [fixtures]);

  const currentDevice = fixtures.find(d => d.filename === activeDevice) || visibleFixtures[0] || fixtures[0];

  useEffect(() => {
    if (selectedDeviceId) setActiveDevice(selectedDeviceId);
  }, [selectedDeviceId]);

  // Keep the selection valid when the filter hides the active device
  useEffect(() => {
    if (visibleFixtures.length && !visibleFixtures.some(f => f.filename === activeDevice)) {
      setActiveDevice(visibleFixtures[0].filename);
    }
  }, [visibleFixtures, activeDevice]);

  useEffect(() => {
    if (!activeDevice) {
      setBaselineData(null);
      return;
    }
    setLoadingBaseline(true);
    api.getDeviceBaseline(activeDevice)
      .then(data => setBaselineData(data.baseline))
      .catch(err => {
        console.error('Failed to load baseline:', err);
        setBaselineData(null);
      })
      .finally(() => setLoadingBaseline(false));
  }, [activeDevice]);

  const handleRemoveDevice = async (dev, event) => {
    event.stopPropagation();
    setDeleteError(null);

    const ok = window.confirm(
      `Remove "${dev.filename}" from the audited inventory?\n\n` +
      `This deletes the stored configuration and any recorded review verdicts for it.`
    );
    if (!ok) return;

    setDeletingFile(dev.filename);
    try {
      await api.deleteConfiguration(dev.filename, currentUser?.username || currentUser?.email);
      if (dev.filename === activeDevice) {
        const next = fixtures.find(f => f.filename !== dev.filename);
        setActiveDevice(next ? next.filename : null);
      }
      if (onDeviceRemoved) await onDeviceRemoved(dev.filename);
    } catch (err) {
      setDeleteError(
        err.response?.data?.detail || `Could not remove ${dev.filename}. Please try again.`
      );
    } finally {
      setDeletingFile(null);
    }
  };

  const renderEvidenceTree = (data, prefix = '') => {
    if (!data) return null;
    const items = [];
    for (const [key, val] of Object.entries(data)) {
      const fullPath = prefix ? `${prefix}.${key}` : key;
      if (val && typeof val === 'object') {
        if ('value' in val && 'explicitly_configured' in val) {
          const method = val.interpretation?.method || 'unknown';
          const conf = val.interpretation?.confidence ?? 0.0;
          const raw = val.source?.raw;
          const line = val.source?.line;
          items.push(
            <div key={fullPath} className="py-1.5 px-2 rounded hover:bg-slate-800/50 text-xs font-mono border-b border-slate-800/40">
              <div className="flex items-center justify-between gap-2">
                <span className="text-brand-300">{fullPath}</span>
                <span className="text-white font-semibold bg-slate-900 px-1.5 py-0.5 rounded border border-slate-700">
                  {val.value === null ? 'null' : String(val.value)}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-2 mt-1 text-[10px] text-slate-400">
                <span className={`px-1 rounded ${val.explicitly_configured ? 'bg-emerald-950/80 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}>
                  {val.explicitly_configured ? 'EXPLICIT' : 'DEFAULT/ASSUMED'}
                </span>
                <span className="text-slate-500">method: {method}</span>
                <span className="text-slate-500">conf: {(conf * 100).toFixed(0)}%</span>
                {raw && (
                  <span className="text-brand-400 truncate max-w-[280px]" title={raw}>
                    src: L{line} "{raw}"
                  </span>
                )}
              </div>
            </div>
          );
        } else if (!Array.isArray(val)) {
          items.push(
            <div key={fullPath} className="mt-2">
              <div className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 bg-slate-900/60 px-2 py-1 rounded">
                {key}
              </div>
              <div className="pl-2 border-l border-slate-800 ml-1">
                {renderEvidenceTree(val, fullPath)}
              </div>
            </div>
          );
        }
      }
    }
    return items;
  };

  return (
    <div className="space-y-6">
      {/* Asset class filter pills */}
      {fixtures.length > 0 && (
        <div className="glass-panel rounded-2xl p-4 border border-slate-800 flex flex-col sm:flex-row sm:items-center gap-3">
          <span className="text-xs font-mono font-semibold text-slate-400 flex items-center gap-1.5 shrink-0">
            <Filter className="w-3.5 h-3.5 text-brand-400" />
            ASSET TYPE
          </span>
          <div className="flex flex-wrap gap-2">
            {CLASS_FILTERS.map(cf => {
              const count = classCounts[cf.id] || 0;
              const isActive = classFilter === cf.id;
              return (
                <button
                  key={cf.id}
                  type="button"
                  onClick={() => setClassFilter(cf.id)}
                  disabled={cf.id !== 'all' && count === 0}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold border transition disabled:opacity-40 disabled:cursor-not-allowed ${
                    isActive
                      ? 'bg-brand-600 text-white border-brand-400 shadow-md shadow-brand-500/20'
                      : 'bg-[#050811] text-slate-400 border-slate-800 hover:border-slate-600'
                  }`}
                >
                  {cf.label} ({count})
                </button>
              );
            })}
          </div>
        </div>
      )}

      {deleteError && (
        <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-500/50 text-rose-300 text-xs font-mono">
          {deleteError}
        </div>
      )}

      {/* Device selection strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {visibleFixtures.map((dev) => {
          const isSelected = dev.filename === activeDevice;
          const isRemoving = deletingFile === dev.filename;
          const klass = dev.device_class || 'unknown';

          return (
            <motion.div
              key={dev.filename}
              whileHover={{ scale: 1.02 }}
              onClick={() => {
                setActiveDevice(dev.filename);
                if (onSelectDevice) onSelectDevice(dev.filename);
              }}
              className={`group p-3 rounded-xl text-left border transition-all relative overflow-hidden cursor-pointer ${
                isSelected
                  ? 'bg-brand-950/70 border-brand-500 shadow-md shadow-brand-500/20'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-1.5 text-xs font-mono font-medium text-slate-200 min-w-0">
                  <span className="text-sm shrink-0" aria-hidden="true">
                    {dev.device_type_icon || '\u2753'}
                  </span>
                  <span className="truncate" title={dev.filename}>{dev.filename}</span>
                </div>

                {/* Remove control. Built-in reference fixtures are protected
                    server-side, so show a lock instead of a dead button. */}
                {dev.is_custom === false ? (
                  <span
                    className="shrink-0 p-1 text-slate-600"
                    title="Built-in reference fixture — cannot be removed"
                  >
                    <Lock className="w-3.5 h-3.5" />
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={(e) => handleRemoveDevice(dev, e)}
                    disabled={isRemoving}
                    aria-label={`Remove ${dev.filename}`}
                    title={`Remove ${dev.filename}`}
                    className="shrink-0 p-1 rounded text-slate-500 opacity-0 group-hover:opacity-100 focus:opacity-100 hover:bg-rose-950/60 hover:text-rose-400 transition disabled:opacity-100"
                  >
                    {isRemoving
                      ? <Loader2 className="w-3.5 h-3.5 animate-spin text-rose-400" />
                      : <Trash2 className="w-3.5 h-3.5" />}
                  </button>
                )}
              </div>

              <div className="mt-2 flex items-center gap-1.5 flex-wrap">
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold border ${CLASS_STYLES[klass]}`}>
                  {dev.device_type_display || 'Unclassified'}
                </span>
              </div>

              <div className="mt-1.5 flex items-center justify-between text-[11px] gap-2">
                <span className="text-slate-400 truncate" title={dev.vendor_display}>
                  {dev.vendor_display}
                </span>
                <span className="font-mono text-[10px] text-slate-500 shrink-0">
                  {(dev.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {visibleFixtures.length === 0 && fixtures.length > 0 && (
        <div className="glass-panel rounded-2xl p-10 border border-dashed border-slate-800 text-center font-mono text-xs text-slate-500">
          No configurations match the <span className="text-brand-300">{classFilter}</span> filter.
        </div>
      )}

      {/* Device details */}
      {currentDevice && (
        <div className="glass-panel rounded-2xl p-6 border border-slate-800">
          <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
            <div>
              <div className="flex items-center gap-3 flex-wrap">
                <h2 className="text-xl font-bold text-white font-mono flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-brand-400" />
                  {currentDevice.filename}
                </h2>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-brand-300 font-mono border border-slate-700">
                  {currentDevice.vendor_display}
                </span>
                <span className={`text-xs px-2.5 py-0.5 rounded-full font-mono border ${CLASS_STYLES[currentDevice.device_class || 'unknown']}`}>
                  {currentDevice.device_type_icon} {currentDevice.device_type_display}
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-900 text-slate-400 font-mono border border-slate-700">
                  {currentDevice.device_class_display}
                </span>
              </div>
              {/* Layered identity: platform / model / role are separate facts */}
              <div className="flex items-center gap-2 flex-wrap mt-2">
                {currentDevice.platform && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
                    OS: {currentDevice.platform}
                  </span>
                )}
                {currentDevice.model && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
                    Model: {currentDevice.model}
                  </span>
                )}
                {currentDevice.network_role && currentDevice.network_role !== 'unknown' && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950/70 border border-indigo-500/40 text-indigo-300">
                    Role: {currentDevice.network_role_display}
                    {' '}({((currentDevice.network_role_confidence || 0) * 100).toFixed(0)}%)
                  </span>
                )}
                {currentDevice.ambiguity && (
                  <span
                    className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/70 border border-amber-500/50 text-amber-300"
                    title={currentDevice.ambiguity_reason}
                  >
                    ⚠ AMBIGUOUS
                  </span>
                )}
              </div>

              <p className="text-xs text-slate-400 mt-2">
                Vendor fingerprint {(currentDevice.confidence * 100).toFixed(0)}%
                {' · '}
                Hardware class {((currentDevice.device_type_confidence || 0) * 100).toFixed(0)}%
                {' · '}
                {currentDevice.line_count} source lines
                {currentDevice.l2_capable && ' · L2'}
                {currentDevice.routing_capable && ' · L3 routing'}
              </p>

              {currentDevice.device_class_basis && (
                <p className="text-[11px] text-slate-500 mt-1 font-mono truncate max-w-xl"
                   title={currentDevice.device_class_basis}>
                  Classified via {currentDevice.device_class_basis}
                </p>
              )}

              {currentDevice.capabilities?.length > 0 && (
                <div className="flex items-center gap-1 flex-wrap mt-2 max-w-2xl">
                  <span className="text-[10px] font-mono text-slate-500 mr-1">CAPABILITIES:</span>
                  {currentDevice.capabilities.slice(0, 12).map(cap => (
                    <span
                      key={cap}
                      className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#050811] border border-slate-800 text-emerald-300"
                    >
                      {cap}
                    </span>
                  ))}
                  {currentDevice.capabilities.length > 12 && (
                    <span className="text-[9px] font-mono text-slate-500">
                      +{currentDevice.capabilities.length - 12} more
                    </span>
                  )}
                </div>
              )}

              {currentDevice.ambiguity && currentDevice.ambiguity_reason && (
                <p className="text-[11px] text-amber-400/90 mt-2 max-w-xl font-sans">
                  {currentDevice.ambiguity_reason}
                </p>
              )}
            </div>

            <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 self-start md:self-auto">
              {[
                { id: 'both', label: 'Split View' },
                { id: 'raw', label: 'Raw CLI' },
                { id: 'normalized', label: 'Normalized Schema' },
              ].map(m => (
                <button
                  key={m.id}
                  onClick={() => setViewMode(m.id)}
                  className={`px-3 py-1 text-xs rounded font-medium transition ${
                    viewMode === m.id ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            {(viewMode === 'both' || viewMode === 'raw') && (
              <div className={`space-y-2 ${viewMode === 'raw' ? 'lg:col-span-2' : ''}`}>
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span className="flex items-center gap-1.5 font-semibold text-slate-300">
                    <FileText className="w-3.5 h-3.5 text-brand-400" />
                    RAW CONFIGURATION EVIDENCE
                  </span>
                  <span>{currentDevice.filename}</span>
                </div>
                <div className="glass-panel-subtle rounded-xl p-4 bg-[#050811] font-mono text-xs text-slate-300 max-h-[550px] overflow-y-auto terminal-scroll leading-relaxed border border-slate-800/80">
                  <pre className="whitespace-pre-wrap">{currentDevice.raw}</pre>
                </div>
              </div>
            )}

            {(viewMode === 'both' || viewMode === 'normalized') && (
              <div className={`space-y-2 ${viewMode === 'normalized' ? 'lg:col-span-2' : ''}`}>
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span className="flex items-center gap-1.5 font-semibold text-slate-300">
                    <Code className="w-3.5 h-3.5 text-emerald-400" />
                    UNIVERSAL SECURITY BASELINE (NORMALIZED)
                  </span>
                  <span className="text-[11px] text-slate-500">Pydantic v2 Schema</span>
                </div>
                <div className="glass-panel-subtle rounded-xl p-4 bg-[#050811] text-xs max-h-[550px] overflow-y-auto terminal-scroll border border-slate-800/80">
                  {loadingBaseline ? (
                    <div className="p-4 space-y-3 font-mono">
                      <div className="flex items-center gap-2 text-xs text-brand-300 font-semibold mb-3">
                        <Cpu className="w-4 h-4 animate-spin text-brand-400" />
                        <span>NORMALIZING EVIDENCE INTO PYDANTIC V2 SCHEMA...</span>
                      </div>
                      {[...Array(5)].map((_, i) => <div key={i} className="h-10 rounded-lg shimmer" />)}
                    </div>
                  ) : baselineData ? (
                    <div className="space-y-1">{renderEvidenceTree(baselineData)}</div>
                  ) : (
                    <div className="py-20 text-center text-slate-500 font-mono">
                      Run mission to populate baseline evidence
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {fixtures.length === 0 && (
        <div className="glass-panel rounded-2xl p-12 border border-dashed border-slate-800 text-center font-mono space-y-3">
          <Server className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="text-white text-sm font-bold">NO DEVICE CONFIGURATIONS</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Upload your device configurations (.conf, .cfg, .rsc, .txt, .xml, .json) in the
            Configuration Manager to fingerprint the vendor, classify the asset type and
            normalize them into the universal security baseline.
          </p>
        </div>
      )}
    </div>
  );
}
