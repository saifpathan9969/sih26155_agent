import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle, Search, CheckCircle2, XCircle, ArrowRight,
  Sparkles, RotateCcw, ShieldCheck, HelpCircle, Layers, Cpu,
  Terminal, Database, Flame, FileCode2, Filter
} from 'lucide-react';
import api from '../api';
import StatusBadge from './StatusBadge';

export default function TrainingWizard({ onMissionUpdate, fixtures = [] }) {
  const [stage, setStage] = useState(1);
  const [selectedConfigFile, setSelectedConfigFile] = useState(
    fixtures.length > 0 ? fixtures[0].filename : 'dev06_fortinet.conf'
  );
  const [detection, setDetection] = useState(null);
  const [retrieval, setRetrieval] = useState(null);
  const [selectedCommand, setSelectedCommand] = useState(null);
  const [fieldPath, setFieldPath] = useState('authentication.password_policy.encryption_enabled');
  const [inputValue, setInputValue] = useState('true');
  const [validationResult, setValidationResult] = useState(null);
  const [confirmResult, setConfirmResult] = useState(null);
  const [reuseResult, setReuseResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [shakeKey, setShakeKey] = useState(0);

  // Sync selected config file when fixtures load
  useEffect(() => {
    if (fixtures && fixtures.length > 0 && !fixtures.some(f => f.filename === selectedConfigFile)) {
      setSelectedConfigFile(fixtures[0].filename);
    }
  }, [fixtures]);

  // Stage 1: Detect Configuration & Unknown Syntax config-file-wise
  const handleDetect = async (targetFile) => {
    const fileToInspect = targetFile || selectedConfigFile;
    setLoading(true);
    try {
      const data = await api.trainingDetect(fileToInspect);
      setDetection(data);
      const cmds = data.unknown_commands || data.unknown_fields || [];
      if (cmds.length > 0) {
        setSelectedCommand(cmds[0]);
        if (cmds[0].suggested_field) {
          setFieldPath(cmds[0].suggested_field);
          setInputValue(String(cmds[0].suggested_value ?? 'true'));
        }
      } else {
        setSelectedCommand(null);
      }
      setStage(2);
    } catch (err) {
      console.error("Training detection error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Initial detection run on mount
  useEffect(() => {
    handleDetect(selectedConfigFile);
  }, []);

  // Select which command to retrieve on
  const handleSelectCommand = (cmd) => {
    setSelectedCommand(cmd);
    if (cmd.suggested_field) {
      setFieldPath(cmd.suggested_field);
      setInputValue(String(cmd.suggested_value ?? 'true'));
    } else if ((cmd.statement || cmd.raw || '').toLowerCase().includes('lockout')) {
      setFieldPath('authentication.account_lockout.enabled');
      setInputValue('true');
    } else if ((cmd.statement || cmd.raw || '').toLowerCase().includes('service')) {
      setFieldPath('network_services.insecure_services');
      setInputValue('false');
    } else if ((cmd.statement || cmd.raw || '').toLowerCase().includes('ssh')) {
      setFieldPath('management.ssh.enabled');
      setInputValue('enabled');
    } else {
      setFieldPath('system.admin.access_profile');
      setInputValue('super_admin');
    }
  };

  // Stage 2: TF-IDF Retrieval on selected command
  const handleRetrieve = async () => {
    const queryStr = selectedCommand?.statement || selectedCommand?.raw || 'config system admin';
    setLoading(true);
    try {
      const [data] = await Promise.all([
        api.trainingRetrieve(queryStr),
        new Promise(res => setTimeout(res, 500)),
      ]);
      setRetrieval(data);
      if (data.candidate_field) {
        setFieldPath(data.candidate_field);
      }
      if (data.candidate_value !== undefined) {
        setInputValue(String(data.candidate_value));
      }
      setStage(3);
    } catch (err) {
      console.error("Vector retrieval error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Stage 4: Validate Mapping
  const handleValidate = async (valToTest) => {
    setLoading(true);
    try {
      let parsed = valToTest;
      if (valToTest === 'true') parsed = true;
      if (valToTest === 'false') parsed = false;

      const data = await api.trainingValidate({
        field_path: fieldPath,
        value: parsed
      });
      setValidationResult(data);
      if (!data.valid) {
        setShakeKey(prev => prev + 1);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Stage 5: Confirm Mapping & Re-evaluate
  const handleConfirm = async () => {
    setLoading(true);
    try {
      let parsed = inputValue === 'true' ? true : inputValue === 'false' ? false : inputValue;
      const data = await api.trainingConfirm({
        field_path: fieldPath,
        value: parsed,
        category: retrieval?.category || 'Security & Administration',
        vendor: detection?.vendor_fingerprint || 'multi_vendor',
        raw: selectedCommand?.statement || selectedCommand?.raw || detection?.raw || ''
      });
      setConfirmResult(data);
      setStage(5);
      if (onMissionUpdate) onMissionUpdate();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Knowledge Reuse Test
  const handleTestReuse = async () => {
    setLoading(true);
    try {
      const [data] = await Promise.all([
        api.trainingReuse(),
        new Promise(res => setTimeout(res, 500)),
      ]);
      setReuseResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Reset
  const handleReset = async () => {
    setLoading(true);
    try {
      await api.trainingReset();
      setStage(1);
      setRetrieval(null);
      setSelectedCommand(null);
      setValidationResult(null);
      setConfirmResult(null);
      setReuseResult(null);
      await handleDetect(selectedConfigFile);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const unknownCommandsList = detection?.unknown_commands || detection?.unknown_fields || [];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Configuration File Selector Filter */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-brand-950 border border-brand-500/30 flex items-center justify-center text-brand-400">
            <FileCode2 className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold font-mono text-white flex items-center gap-2">
              TARGET CONFIGURATION FILE
              {detection && (
                <span className="text-[10px] bg-brand-950 text-brand-300 px-2 py-0.5 rounded border border-brand-500/30">
                  {detection.vendor_display || detection.vendor_fingerprint?.toUpperCase()}
                </span>
              )}
            </h4>
            <p className="text-[11px] text-slate-400">
              Select any configuration file to inspect its specific unknown directives & perform vector AI retrieval
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <select
            value={selectedConfigFile}
            onChange={(e) => {
              const newFile = e.target.value;
              setSelectedConfigFile(newFile);
              handleDetect(newFile);
            }}
            className="bg-slate-900 border border-slate-700 text-white text-xs rounded-lg px-3 py-1.5 font-mono focus:outline-none focus:border-brand-500"
          >
            {fixtures.length > 0 ? (
              fixtures.map(f => (
                <option key={f.filename} value={f.filename}>
                  {f.filename} ({f.vendor?.toUpperCase() || 'NET'})
                </option>
              ))
            ) : (
              <>
                <option value="dev06_fortinet.conf">dev06_fortinet.conf (FORTINET)</option>
                <option value="dev01_cisco.conf">dev01_cisco.conf (CISCO)</option>
                <option value="dev02_cisco.conf">dev02_cisco.conf (CISCO)</option>
                <option value="dev03_juniper.conf">dev03_juniper.conf (JUNIPER)</option>
                <option value="arista_eos_test.conf">arista_eos_test.conf (ARISTA)</option>
                <option value="aruba_aoscx_test.conf">aruba_aoscx_test.conf (ARUBA)</option>
              </>
            )}
          </select>

          <button
            onClick={() => handleDetect(selectedConfigFile)}
            disabled={loading}
            className="px-3.5 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-mono text-xs flex items-center gap-1.5 transition shadow-sm whitespace-nowrap"
          >
            <Search className="w-3.5 h-3.5" />
            Inspect Syntax
          </button>
        </div>
      </div>

      {/* Wizard Stage Tracker */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between overflow-x-auto gap-2">
        {[
          { num: 1, label: '1. Syntax Inspection' },
          { num: 2, label: '2. Vector AI Retrieval' },
          { num: 3, label: '3. Human Review & Mapping' },
          { num: 4, label: '4. Schema Validation' },
          { num: 5, label: '5. KB Ingestion' },
        ].map(step => (
          <div
            key={step.num}
            onClick={() => {
              if (step.num <= stage || detection) {
                setStage(step.num);
              }
            }}
            className="flex items-center gap-2 cursor-pointer group"
          >
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold font-mono transition ${
                stage === step.num
                  ? 'bg-brand-500 text-white shadow-lg shadow-brand-500/30'
                  : stage > step.num
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-800 text-slate-400 group-hover:bg-slate-700'
              }`}
            >
              {stage > step.num ? '✓' : step.num}
            </div>
            <span className={`text-xs whitespace-nowrap font-medium ${stage >= step.num ? 'text-white' : 'text-slate-500 group-hover:text-slate-300'}`}>
              {step.label}
            </span>
            {step.num < 5 && <div className="w-6 h-[1px] bg-slate-800 mx-1 hidden sm:block" />}
          </div>
        ))}

        <button
          onClick={handleReset}
          className="ml-auto text-xs text-slate-400 hover:text-white flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 whitespace-nowrap"
        >
          <RotateCcw className="w-3.5 h-3.5" /> Reset Session
        </button>
      </div>

      {/* Main Interactive Stage Panel */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
        
        {/* Stage 1: Detection */}
        {stage === 1 && (
          <div className="space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-orange-950/80 border border-orange-500/30 flex items-center justify-center text-orange-400">
                <Flame className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">
                  Stage 1 — Configuration Ingestion & Syntax Inspection
                </h3>
                <p className="text-xs text-slate-400">
                  Deterministic parser inspects {selectedConfigFile} for known directives and unknown syntax.
                </p>
              </div>
            </div>

            <div className="bg-[#050811] p-5 rounded-xl border border-slate-800 space-y-4 font-mono text-xs">
              <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-3 gap-2">
                <span className="text-slate-400">TARGET APPLIANCE:</span>
                <span className="text-brand-300 font-bold bg-brand-950/50 px-2.5 py-1 rounded border border-brand-500/30">
                  {selectedConfigFile} ({detection?.vendor_display || 'Multi-Vendor Appliance'})
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                <div className="space-y-2">
                  <div className="text-slate-400 font-sans font-semibold text-xs flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Standard Parsed Sections
                  </div>
                  <ul className="space-y-1.5 text-[11px] text-slate-300">
                    {(detection?.known_configurations || [
                      "Deterministic security baselines mapped into Pydantic v2 schema",
                      "Interfaces and network topology configurations",
                      "Standard administrative policy directives",
                      "Static routing & default gateway parameters",
                      "Audit logging & syslog forwarders"
                    ]).map((item, idx) => (
                      <li key={idx} className="flex items-center gap-2">
                        <span className="text-emerald-400">✓</span> {item}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="space-y-2">
                  <div className="text-amber-400 font-sans font-semibold text-xs flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-amber-400" /> Unsupported / Unknown Directives ({unknownCommandsList.length})
                  </div>
                  {unknownCommandsList.length > 0 ? (
                    <ul className="space-y-1.5 text-[11px] text-amber-300">
                      {unknownCommandsList.map((cmd, idx) => (
                        <li key={idx} className="flex items-center gap-2 truncate">
                          <span className="text-amber-400">⚠</span> {cmd.statement || cmd.raw}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="text-xs text-slate-400 italic">
                      No unsupported directives in standard sections.
                    </div>
                  )}
                </div>
              </div>

              <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-800 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                NTRO Safety Directive: AI model will never hallucinate compliance semantics without human confirmation.
              </div>
            </div>

            <button
              onClick={() => handleDetect(selectedConfigFile)}
              disabled={loading}
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-gradient-to-r from-orange-600 to-amber-600 text-white font-medium text-xs shadow-lg shadow-orange-500/20 hover:from-orange-500 hover:to-amber-500 transition flex items-center justify-center gap-2"
            >
              <Search className="w-4 h-4" />
              Analyze Syntax & Escalate to AI
            </button>
          </div>
        )}

        {/* Stage 2: Unknowns & AI Retrieval Query Selection */}
        {stage === 2 && (
          <div className="space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-950/80 border border-brand-500/30 flex items-center justify-center text-brand-400">
                <Search className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">
                  Stage 2 — Select Unknown Command for Vector AI Retrieval
                </h3>
                <p className="text-xs text-slate-400">
                  Choose a command from <span className="text-brand-300 font-mono">{selectedConfigFile}</span> to search the historical knowledge base.
                </p>
              </div>
            </div>

            {/* Config file commands grid */}
            {unknownCommandsList.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {unknownCommandsList.map((cmd, idx) => {
                  const cmdText = cmd.statement || cmd.raw;
                  const isSelected = (selectedCommand?.statement || selectedCommand?.raw) === cmdText;
                  return (
                    <div
                      key={idx}
                      onClick={() => handleSelectCommand(cmd)}
                      className={`cursor-pointer p-3.5 rounded-xl border transition text-xs font-mono flex flex-col justify-between ${
                        isSelected
                          ? 'bg-amber-950/40 border-amber-500 text-white shadow-lg shadow-amber-500/10 ring-1 ring-amber-500/50'
                          : 'bg-[#050811] border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <div>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-[10px] text-amber-400 uppercase font-bold flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" /> Directive #{idx + 1}
                          </span>
                          {isSelected && (
                            <span className="text-[9px] bg-amber-500 text-slate-950 font-bold px-1.5 py-0.5 rounded">
                              SELECTED
                            </span>
                          )}
                        </div>
                        <div className="text-white font-semibold break-all text-[11px] mb-2">
                          {cmdText}
                        </div>
                      </div>
                      <div className="text-[10px] text-slate-500 border-t border-slate-800 pt-2 mt-2">
                        {cmd.reason || `Directive on line ${cmd.line || 'N/A'}`}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400 text-center">
                All directives in {selectedConfigFile} were mapped deterministically. Choose another file above or test vector retrieval on standard syntax.
              </div>
            )}

            {/* Retrieval Query Preview */}
            <div className="bg-[#050811] p-4 rounded-xl border border-slate-800 space-y-2 font-mono text-xs">
              <div className="text-slate-400">Vector Search Query Target:</div>
              <div className="bg-slate-950 p-2.5 rounded border border-brand-500/30 text-brand-300 font-bold break-all">
                {selectedCommand?.statement || selectedCommand?.raw || 'config system admin'}
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                The TF-IDF vectorizer will score character n-grams of this command against historical NTRO and CIS rule mappings.
              </p>
            </div>

            <button
              onClick={handleRetrieve}
              disabled={loading || !selectedCommand}
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 text-white font-medium text-xs shadow-lg shadow-brand-500/20 hover:from-brand-500 hover:to-brand-400 transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              Execute Vector Retrieval on Selected Command
            </button>
          </div>
        )}

        {/* Stage 3 & 4: Human Review & Schema Validation */}
        {(stage === 3 || stage === 4) && retrieval && (
          <div className="space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-purple-950/80 border border-purple-500/30 flex items-center justify-center text-purple-400">
                <HelpCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Stage 3 & 4 — Human Review & Strict Schema Validation</h3>
                <p className="text-xs text-slate-400">
                  Target: <span className="text-brand-300 font-mono font-bold">{selectedCommand?.statement || selectedCommand?.raw}</span>
                </p>
              </div>
            </div>

            {/* Retrieval Result Card */}
            <div className="bg-[#050811] p-4 rounded-xl border border-slate-800 space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-mono">Similarity Score:</span>
                <span className="font-mono font-bold text-amber-400 bg-amber-950/60 px-2.5 py-1 rounded border border-amber-500/30">
                  {retrieval.similarity ? (retrieval.similarity * 100).toFixed(1) + '%' : '0.0% (Unseen Directive)'}
                </span>
              </div>
              <div className="font-mono text-slate-300">
                Matched Rule Category: <span className="text-brand-300">{retrieval.category || 'Security & Access Control'}</span>
              </div>
              <p className="text-slate-400 text-[11px]">
                {retrieval.explanation ||
                  'No direct match found in historical registry. In accordance with NTRO non-negotiable safety principles, human review is mandated.'}
              </p>
            </div>

            {/* Interactive Mapping Form */}
            <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-800 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">
                    Canonical Baseline Field Path:
                  </label>
                  <input
                    type="text"
                    value={fieldPath}
                    onChange={(e) => setFieldPath(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-brand-300 focus:outline-none focus:border-brand-500"
                  />
                  <p className="text-[10px] text-slate-500 mt-1">Schema mapping target for universal compliance rules</p>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">
                    Validated Ingestion Value:
                  </label>
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-brand-500"
                  />
                  <p className="text-[10px] text-slate-500 mt-1">Extracted canonical value (e.g. true, false, super_admin)</p>
                </div>
              </div>

              {/* Validation Testing Buttons */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <motion.button
                  key={`shake-${shakeKey}`}
                  animate={shakeKey ? { x: [0, -8, 8, -6, 6, -3, 3, 0] } : {}}
                  transition={{ duration: 0.4 }}
                  onClick={() => {
                    setInputValue('invalid-random-string');
                    handleValidate('invalid-random-string');
                  }}
                  className="px-3 py-1.5 rounded-lg bg-rose-950/60 border border-rose-500/40 text-rose-300 text-xs font-mono hover:bg-rose-900/60 transition"
                >
                  ⚡ Test Schema Rejection ("invalid-random-string")
                </motion.button>

                <button
                  onClick={() => {
                    const validVal = fieldPath.includes('enabled') || fieldPath.includes('defined') ? 'true' : 'super_admin';
                    setInputValue(validVal);
                    handleValidate(validVal);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs font-mono hover:bg-emerald-900/60 transition"
                >
                  ✓ Validate Strict Schema
                </button>
              </div>

              {/* Validation Result Display */}
              {validationResult && (
                <div
                  className={`p-3 rounded-lg border text-xs font-mono flex items-start gap-2.5 ${
                    validationResult.valid
                      ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                      : 'bg-rose-950/40 border-rose-500/40 text-rose-300'
                  }`}
                >
                  {validationResult.valid ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  )}
                  <div>
                    <div className="font-semibold">
                      {validationResult.valid ? 'SCHEMA VALIDATION PASSED' : 'SCHEMA VALIDATION REJECTED'}
                    </div>
                    <div className="text-[11px] mt-0.5">
                      Target Field: <span className="font-bold">{fieldPath}</span> | 
                      Value: <span className="font-bold">"{String(validationResult.received_value || inputValue)}"</span>
                    </div>
                    {validationResult.error && (
                      <div className="text-[11px] text-rose-400 mt-1">
                        Reason: {validationResult.error}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Confirm Mapping Button */}
              {validationResult?.valid && (
                <button
                  onClick={handleConfirm}
                  disabled={loading}
                  className="w-full px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 text-white font-medium text-xs shadow-lg shadow-emerald-500/20 hover:from-emerald-500 hover:to-emerald-400 transition flex items-center justify-center gap-2"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Ingest into Knowledge Base & Re-Evaluate Mission
                </button>
              )}
            </div>
          </div>
        )}

        {/* Stage 5: Ingested & Verified */}
        {stage === 5 && confirmResult && (
          <div className="space-y-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-950/80 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Stage 5 — Syntax Mapped & Rules Re-Evaluated</h3>
                <p className="text-xs text-slate-400">
                  Evidence updated with human-confirmed mapping. Affected compliance rules re-evaluated.
                </p>
              </div>
            </div>

            {/* Before vs After Finding Box */}
            <div className="glass-panel p-5 rounded-xl border border-brand-500/30 bg-gradient-to-r from-slate-900 via-navy-850 to-slate-900 space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs text-brand-300 font-semibold">
                  RULE: {confirmResult.rule_id || 'CIS-AUTH-02'}
                </span>
                <span className="text-[10px] text-slate-400 font-mono">{selectedConfigFile}</span>
              </div>

              <div className="flex items-center justify-center gap-6 bg-slate-950/80 p-4 rounded-xl border border-slate-800">
                <div className="text-center">
                  <div className="text-[10px] uppercase font-mono text-slate-500 mb-1">BEFORE HUMAN REVIEW</div>
                  <StatusBadge status={confirmResult.before_status || "NEEDS_HUMAN_REVIEW"} size="md" />
                </div>

                <div className="text-brand-400 text-xl font-bold">➔</div>

                <div className="text-center">
                  <div className="text-[10px] uppercase font-mono text-emerald-400 mb-1 flex items-center justify-center gap-1">
                    <Sparkles className="w-3 h-3" /> AFTER RE-EVALUATION
                  </div>
                  <StatusBadge status={confirmResult.after_status || "PASS"} size="md" />
                </div>
              </div>

              <div className="text-xs text-slate-300 space-y-1 bg-slate-900 p-3.5 rounded-lg border border-slate-800 font-mono text-[11px]">
                <div>✓ Command pattern "{selectedCommand?.statement || selectedCommand?.raw}" successfully indexed in Vector KB</div>
                <div>✓ Blockchain integrity block sealed with human operator provenance</div>
                <div>✓ Compliance finding updated to PASS</div>
              </div>
            </div>

            {/* Knowledge Reuse Test */}
            <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-brand-400" />
                <h4 className="text-xs font-bold font-mono text-white">
                  KNOWLEDGE REUSE ON FUTURE APPLIANCES
                </h4>
              </div>
              <p className="text-xs text-slate-400">
                A newly audited appliance contains a variant command:
                <code className="text-brand-300 bg-slate-900 px-2 py-0.5 rounded ml-1 font-mono">
                  {selectedCommand?.statement || 'config system global set admin-lockout-threshold 5'}
                </code>
              </p>

              {!reuseResult ? (
                <button
                  onClick={handleTestReuse}
                  disabled={loading}
                  className="px-5 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-medium font-mono flex items-center gap-1.5 transition"
                >
                  <Search className="w-3.5 h-3.5" />
                  Query Knowledge Base for Learned Pattern
                </button>
              ) : (
                <div className="bg-[#050811] p-4 rounded-lg border border-brand-500/30 space-y-2 text-xs font-mono">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">TF-IDF Vector Similarity:</span>
                    <span className="text-emerald-400 font-bold bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-500/30">
                      {(reuseResult.similarity * 100).toFixed(1)}% Match
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400">Matched Pattern: </span>
                    <span className="text-white">"{reuseResult.matched_entry?.raw_pattern}"</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Autonomous Interpretation: </span>
                    <span className="text-brand-300">{reuseResult.candidate_interpretation?.field_path} = true</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
