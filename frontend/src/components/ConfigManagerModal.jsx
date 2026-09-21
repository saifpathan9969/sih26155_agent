import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, FileText, Server, X, CheckCircle2, AlertCircle,
  Trash2, Plus, Sparkles, RefreshCw, Layers, Shield
} from 'lucide-react';
import api from '../api';

export default function ConfigManagerModal({ isOpen, onClose, onConfigurationsChanged, currentUser }) {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'manage'
  const [filename, setFilename] = useState('');
  const [content, setContent] = useState('');
  const [vendor, setVendor] = useState('auto');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [configs, setConfigs] = useState([]);
  const [fetchingConfigs, setFetchingConfigs] = useState(false);

  const uname = currentUser?.username || currentUser?.email;

  const fetchAllConfigs = async () => {
    setFetchingConfigs(true);
    try {
      const data = await api.getConfigurations(null, uname);
      setConfigs(data.configurations || []);
    } catch (err) {
      console.error("Failed to load configurations:", err);
    } finally {
      setFetchingConfigs(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchAllConfigs();
      setError(null);
      setSuccess(null);
    }
  }, [isOpen, uname]);

  if (!isOpen) return null;

  // File drag & drop or file picker
  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFilename(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result;
      if (typeof text === 'string') {
        setContent(text);
        // Auto-detect vendor suggestion
        const lower = text.toLowerCase();
        if (lower.includes('cisco') || lower.includes('service password-encryption') || lower.includes('line vty')) {
          setVendor('cisco_ios');
        } else if (lower.includes('juniper') || lower.includes('set system login') || lower.includes('set system services')) {
          setVendor('juniper_junos');
        } else if (lower.includes('fortigate') || lower.includes('config system')) {
          setVendor('fortinet_fortios');
        }
      }
    };
    reader.readAsText(file);
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!filename.trim()) {
      setError("Please specify a configuration filename (e.g. router_edge01.conf).");
      return;
    }
    if (!content.trim()) {
      setError("Configuration content cannot be empty.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await api.uploadConfiguration(filename, content, vendor, uname);
      setSuccess(`Configuration "${res.filename}" ingested! Vendor: ${res.vendor_display} (${res.line_count} lines).`);
      setFilename('');
      setContent('');
      await fetchAllConfigs();
      if (onConfigurationsChanged) onConfigurationsChanged();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to upload configuration.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (fname) => {
    if (!window.confirm(`Remove configuration "${fname}"?`)) return;
    try {
      await api.deleteConfiguration(fname);
      await fetchAllConfigs();
      if (onConfigurationsChanged) onConfigurationsChanged();
    } catch (err) {
      alert(err.response?.data?.detail || "Delete failed.");
    }
  };

  // Sample templates to quickly load
  const loadSampleConfig = (type) => {
    if (type === 'cisco') {
      setFilename('edge_cisco_asr1001.conf');
      setVendor('cisco_ios');
      setContent(
`Building configuration...
!
service password-encryption
security passwords min-length 14
login block-for 900 attempts 5 within 600
ip ssh version 2
line vty 0 4
 exec-timeout 10 0
 transport input ssh
 access-class 10 in
no ip http server
ip http secure-server
ip http tls-version TLSv1.2
snmp-server community SecCorpV2 RO
logging host 10.0.0.5
logging buffered 65536
archive
 log config
ip ssh server algorithm encryption aes256-ctr`
      );
    } else if (type === 'juniper') {
      setFilename('core_juniper_mx480.conf');
      setVendor('juniper_junos');
      setContent(
`set system login password format sha256
set system login password minimum-length 14
set system services ssh protocol-version v2
set system login idle-timeout 10
delete system services telnet
delete system services web-management http
set system services web-management https
set system services web-management https tls-min-version tls1.2
set system login retry-options tries-before-disconnect 5
set snmp community ProtectedSNMP authorization read-only
set system syslog host 10.0.0.5 any info`
      );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 15 }}
        className="w-full max-w-2xl glass-panel p-6 sm:p-8 rounded-2xl border border-brand-500/30 bg-[#0c1222] shadow-2xl relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-72 h-72 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-brand-500/25">
            <Upload className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold font-mono text-white flex items-center gap-2">
              CONFIGURATION MANAGEMENT
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-950 text-brand-300 font-mono border border-brand-500/40">
                Multi-Vendor
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Upload raw router/firewall configurations or select device inventory for audit missions
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex rounded-xl bg-[#050811] p-1 border border-slate-800 my-4">
          <button
            type="button"
            onClick={() => setActiveTab('upload')}
            className={`flex-1 py-2 text-xs font-mono font-semibold rounded-lg flex items-center justify-center gap-2 transition ${
              activeTab === 'upload'
                ? 'bg-brand-600 text-white shadow-md shadow-brand-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Plus className="w-3.5 h-3.5" />
            Upload New Config
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('manage')}
            className={`flex-1 py-2 text-xs font-mono font-semibold rounded-lg flex items-center justify-center gap-2 transition ${
              activeTab === 'manage'
                ? 'bg-brand-600 text-white shadow-md shadow-brand-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Active Device Pool ({configs.length})
          </button>
        </div>

        {/* Feedback Alerts */}
        {error && (
          <div className="p-3 mb-4 rounded-xl bg-rose-950/50 border border-rose-500/40 flex items-start gap-2.5 text-xs text-rose-300 font-mono">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
        {success && (
          <div className="p-3 mb-4 rounded-xl bg-emerald-950/50 border border-emerald-500/40 flex items-start gap-2.5 text-xs text-emerald-300 font-mono">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>{success}</span>
          </div>
        )}

        {/* Tab 1: Upload */}
        {activeTab === 'upload' && (
          <form onSubmit={handleUploadSubmit} className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">Quick Fill Templates:</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => loadSampleConfig('cisco')}
                  className="px-2.5 py-1 text-[11px] font-mono rounded bg-slate-900 hover:bg-slate-800 text-blue-300 border border-blue-500/30"
                >
                  + Cisco Sample
                </button>
                <button
                  type="button"
                  onClick={() => loadSampleConfig('juniper')}
                  className="px-2.5 py-1 text-[11px] font-mono rounded bg-slate-900 hover:bg-slate-800 text-emerald-300 border border-emerald-500/30"
                >
                  + Juniper Sample
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">
                  CONFIGURATION FILENAME:
                </label>
                <input
                  type="text"
                  required
                  value={filename}
                  onChange={(e) => setFilename(e.target.value)}
                  placeholder="e.g. edge_router_cisco.conf"
                  className="w-full bg-[#050811] border border-slate-700 rounded-xl px-3.5 py-2 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">
                  VENDOR FAMILY OVERRIDE:
                </label>
                <select
                  value={vendor}
                  onChange={(e) => setVendor(e.target.value)}
                  className="w-full bg-[#050811] border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-brand-500"
                >
                  <option value="auto">✨ Auto-Detect (Heuristic Fingerprinting)</option>
                  <option value="cisco_ios">Cisco IOS</option>
                  <option value="juniper_junos">Juniper Junos</option>
                  <option value="fortinet_fortios">Fortinet FortiOS</option>
                </select>
              </div>
            </div>

            {/* File dropzone / file upload input */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-[11px] font-mono text-slate-400">
                  PASTE RUNNING-CONFIG OR UPLOAD FILE:
                </label>
                <label className="cursor-pointer text-[11px] font-mono text-brand-400 hover:text-brand-300 flex items-center gap-1">
                  <Upload className="w-3 h-3" />
                  <span>Choose File (.conf, .cfg, .txt)</span>
                  <input
                    type="file"
                    accept=".conf,.cfg,.txt"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>
              </div>
              <textarea
                rows={6}
                required
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Paste raw CLI configuration text here... (e.g. 'service password-encryption', 'ip ssh version 2', etc.)"
                className="w-full bg-[#050811] border border-slate-700 rounded-xl p-3 text-xs font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-brand-500 resize-none font-mono terminal-scroll"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-brand-600 to-cyan-600 hover:from-brand-500 hover:to-cyan-500 text-white font-mono font-bold text-xs tracking-wide shadow-lg shadow-brand-500/25 transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>INGESTING & FINGERPRINTING...</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>INGEST CONFIGURATION INTO AUDITOR</span>
                </>
              )}
            </button>
          </form>
        )}

        {/* Tab 2: Manage Active Pool */}
        {activeTab === 'manage' && (
          <div className="space-y-3 max-h-80 overflow-y-auto terminal-scroll pr-1">
            {fetchingConfigs ? (
              <div className="py-8 text-center text-xs font-mono text-slate-500">
                Loading configuration pool...
              </div>
            ) : configs.length === 0 ? (
              <div className="py-8 text-center text-xs font-mono text-slate-500">
                No configurations found.
              </div>
            ) : (
              configs.map((c) => (
                <div
                  key={c.filename}
                  className="p-3 rounded-xl bg-[#050811] border border-slate-800 flex items-center justify-between gap-3 hover:border-slate-700 transition"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-brand-400">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-white">
                          {c.filename}
                        </span>
                        {c.is_custom ? (
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-500/30">
                            Custom Upload
                          </span>
                        ) : (
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                            Fixture
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                        Vendor: <span className="text-slate-200">{c.vendor_display}</span> • {c.line_count} lines
                      </div>
                    </div>
                  </div>

                  <div>
                    {c.is_custom && (
                      <button
                        type="button"
                        onClick={() => handleDelete(c.filename)}
                        title="Delete custom configuration"
                        className="p-1.5 rounded-lg text-rose-400 hover:text-white hover:bg-rose-950/60 transition"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
}
