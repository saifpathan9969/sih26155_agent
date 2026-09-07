import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Server, FileText, CheckCircle, ShieldAlert, Cpu, Eye, Code, Search } from 'lucide-react';
import api from '../api';

export default function DeviceViewer({ fixtures = [], onSelectDevice, selectedDeviceId }) {
  const [activeDevice, setActiveDevice] = useState(selectedDeviceId || (fixtures[0]?.filename || 'dev01_cisco.conf'));
  const [baselineData, setBaselineData] = useState(null);
  const [loadingBaseline, setLoadingBaseline] = useState(false);
  const [viewMode, setViewMode] = useState('both'); // 'both' | 'raw' | 'normalized'

  const currentDevice = fixtures.find(d => d.filename === activeDevice) || fixtures[0];

  useEffect(() => {
    if (selectedDeviceId) {
      setActiveDevice(selectedDeviceId);
    }
  }, [selectedDeviceId]);

  useEffect(() => {
    if (activeDevice) {
      setLoadingBaseline(true);
      api.getDeviceBaseline(activeDevice)
        .then(data => {
          setBaselineData(data.baseline);
        })
        .catch(err => {
          console.error("Failed to load baseline:", err);
          setBaselineData(null);
        })
        .finally(() => setLoadingBaseline(false));
    }
  }, [activeDevice]);

  const renderEvidenceTree = (data, prefix = '') => {
    if (!data) return null;

    const items = [];
    for (const [key, val] of Object.entries(data)) {
      const fullPath = prefix ? `${prefix}.${key}` : key;

      if (val && typeof val === 'object') {
        if ('value' in val && 'explicitly_configured' in val) {
          // This is an EvidenceField
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
      {/* Device Selection Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {fixtures.map((dev) => {
          const isSelected = dev.filename === activeDevice;
          const isUnsupported = dev.vendor === 'fortinet_fortios';

          return (
            <motion.button
              key={dev.filename}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                setActiveDevice(dev.filename);
                if (onSelectDevice) onSelectDevice(dev.filename);
              }}
              className={`p-3 rounded-xl text-left border transition-all relative overflow-hidden ${
                isSelected
                  ? 'bg-brand-950/70 border-brand-500 shadow-md shadow-brand-500/20'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              {isSelected && (
                <div className="absolute top-0 right-0 w-8 h-8 bg-brand-500/20 rounded-bl-xl flex items-center justify-center">
                  <div className="w-2 h-2 rounded-full bg-brand-400" />
                </div>
              )}
              <div className="flex items-center gap-1.5 text-xs font-mono font-medium text-slate-200">
                <Server className={`w-3.5 h-3.5 ${isSelected ? 'text-brand-400' : 'text-slate-400'}`} />
                <span className="truncate">{dev.filename}</span>
              </div>
              <div className="mt-1.5 flex items-center justify-between text-[11px]">
                <span className={isUnsupported ? 'text-amber-400 font-medium' : 'text-slate-400'}>
                  {dev.vendor_display}
                </span>
                <span className="font-mono text-[10px] text-slate-500">
                  {(dev.confidence * 100).toFixed(0)}% conf
                </span>
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* Device Details Card */}
      {currentDevice && (
        <div className="glass-panel rounded-2xl p-6 border border-slate-800">
          <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-bold text-white font-mono flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-brand-400" />
                  {currentDevice.filename}
                </h2>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-brand-300 font-mono border border-slate-700">
                  {currentDevice.vendor_display}
                </span>
                {currentDevice.vendor === 'fortinet_fortios' && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-amber-950/80 text-amber-300 border border-amber-500/40">
                    Graceful Degradation Demo (Unsupported Vendor)
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Vendor Fingerprint Confidence: {(currentDevice.confidence * 100).toFixed(1)}% | 
                Source Lines: {currentDevice.line_count}
              </p>
            </div>

            {/* View Mode Switcher */}
            <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 self-start md:self-auto">
              <button
                onClick={() => setViewMode('both')}
                className={`px-3 py-1 text-xs rounded font-medium transition ${
                  viewMode === 'both' ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Split View
              </button>
              <button
                onClick={() => setViewMode('raw')}
                className={`px-3 py-1 text-xs rounded font-medium transition ${
                  viewMode === 'raw' ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Raw CLI
              </button>
              <button
                onClick={() => setViewMode('normalized')}
                className={`px-3 py-1 text-xs rounded font-medium transition ${
                  viewMode === 'normalized' ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Normalized Schema
              </button>
            </div>
          </div>

          {/* Split / Single View Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            {/* Left: Raw CLI Config */}
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

            {/* Right: Normalized Universal Baseline */}
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
                      <div className="h-5 w-40 rounded shimmer mb-2" />
                      <div className="h-10 rounded-lg shimmer" />
                      <div className="h-10 rounded-lg shimmer" />
                      <div className="h-10 rounded-lg shimmer" />
                      <div className="h-10 rounded-lg shimmer" />
                      <div className="h-10 rounded-lg shimmer" />
                    </div>
                  ) : baselineData ? (
                    <div className="space-y-1">
                      {renderEvidenceTree(baselineData)}
                    </div>
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
    </div>
  );
}
