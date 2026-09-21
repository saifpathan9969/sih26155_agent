import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  BookOpen, Bot, Send, Sparkles, HelpCircle, Shield,
  Terminal, Server, Lock, Link2, FileText, Cpu, CheckCircle2,
  AlertTriangle, ArrowRight, ChevronRight, UserCheck, Upload
} from 'lucide-react';
import api from '../api';

export default function GuidePage({ onNavigateTab }) {
  const [activeSection, setActiveSection] = useState('philosophy');
  const [chatMessages, setChatMessages] = useState([
    {
      sender: 'bot',
      text: "👋 **Welcome to the SIH26155 Sentinel Assistant!**\n\nI am your interactive AI guide for the Multi-Vendor Network Security Compliance Auditor.\n\nYou can ask me anything about:\n- **Why blockchain hashes are used**\n- **How to resolve 'Human Needed' findings**\n- **How to upload and select custom network configs**\n- **The 20 CIS Benchmark Rules**\n- **The Two-Person Rule Governance protocol**\n\nClick a suggestion below or type your question!",
    },
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const guideSections = [
    {
      id: 'philosophy',
      title: '1. Architecture & Core Principle',
      icon: Shield,
      summary: 'Why AI Interprets and Deterministic Rules Decide',
    },
    {
      id: 'configs',
      title: '2. Config Upload & Multi-Vendor Ingestion',
      icon: Server,
      summary: 'Normalizing Cisco, Juniper, and FortiOS configs into universal schemas',
    },
    {
      id: 'compliance',
      title: '3. Deterministic CIS Rule Engine',
      icon: Terminal,
      summary: 'The 20 CIS security benchmarks and zero-hallucination evaluation',
    },
    {
      id: 'hitl',
      title: '4. Human-in-the-Loop & Active Learning',
      icon: UserCheck,
      summary: 'Resolving unmapped commands, uploading docs, and knowledge reuse',
    },
    {
      id: 'blockchain',
      title: '5. Blockchain Proof & Why Hashes Exist',
      icon: Link2,
      summary: 'Cryptographic SHA-256 immutability, tamper detection, and NTRO audit trust',
    },
    {
      id: 'governance',
      title: '6. Two-Person Rule Governance',
      icon: Lock,
      summary: 'Dual authorization for rule changes and automated regression re-audits',
    },
  ];

  const suggestedPrompts = [
    "Why are hashes on the blockchain page and what is their use?",
    "How do I click and resolve a 'Human Needed' finding?",
    "How do I upload custom router configs and select them?",
    "Explain the Two-Person Rule approval process",
    "What are the 20 CIS rules audited by the agent?",
  ];

  const handleSendMessage = async (textToSend) => {
    const query = textToSend || chatInput;
    if (!query.trim()) return;

    const newHistory = [...chatMessages, { sender: 'user', text: query }];
    setChatMessages(newHistory);
    setChatInput('');
    setIsTyping(true);

    try {
      const res = await api.askGuideBot(query, []);
      setChatMessages([...newHistory, { sender: 'bot', text: res.reply }]);
    } catch (err) {
      console.error(err);
      setChatMessages([
        ...newHistory,
        {
          sender: 'bot',
          text: "⚠️ Unable to reach the assistant service. Please check your backend connection.",
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="glass-panel p-6 rounded-2xl border border-brand-500/20 bg-gradient-to-r from-slate-900 via-navy-850 to-slate-900 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-950 border border-brand-500/30 text-xs font-mono text-brand-300 mb-2">
              <BookOpen className="w-3.5 h-3.5 text-brand-400" />
              <span>OFFICIAL PROCEDURES MANUAL & INTERACTIVE SENTINEL</span>
            </div>
            <h1 className="text-2xl font-black font-mono text-white tracking-tight">
              AGENT PROCEDURES GUIDE & AI COPILOT
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Master the complete operational lifecycle of the SIH26155 autonomous compliance auditor,
              from multi-vendor ingestion to blockchain cryptographic verification.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onNavigateTab && onNavigateTab('summary')}
              className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-mono text-slate-200 flex items-center gap-2 transition"
            >
              <span>View Mission Summary</span>
              <ArrowRight className="w-3.5 h-3.5 text-brand-400" />
            </button>
          </div>
        </div>
      </div>

      {/* Main 2-Column Grid: Left is Interactive Manual, Right is AI Chatbot */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Procedures Manual (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Section Navigation Pills */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {guideSections.map((sec) => {
              const Icon = sec.icon;
              const isActive = activeSection === sec.id;
              return (
                <button
                  key={sec.id}
                  onClick={() => setActiveSection(sec.id)}
                  className={`p-3 rounded-xl border text-left transition ${
                    isActive
                      ? 'bg-brand-600/90 border-brand-400 text-white shadow-lg shadow-brand-500/20'
                      : 'bg-[#090e1b] border-slate-800 hover:border-slate-700 text-slate-400'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-brand-400'}`} />
                    <span className="text-xs font-mono font-bold truncate">{sec.title}</span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Section Content Display */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
            {activeSection === 'philosophy' && (
              <div className="space-y-4 text-xs font-sans text-slate-300 leading-relaxed">
                <div className="flex items-center gap-2 text-brand-300 font-mono text-sm font-bold border-b border-slate-800 pb-2">
                  <Shield className="w-4 h-4 text-brand-400" />
                  <span>1. Architecture & The Zero-Hallucination Core</span>
                </div>
                <p>
                  In defense and national security infrastructure (NTRO), an autonomous compliance auditor cannot rely on large language models (LLMs) to issue security verdicts. LLMs are non-deterministic, prone to hallucination, and vulnerable to prompt injection attacks embedded inside configuration files.
                </p>
                <div className="p-3.5 rounded-xl bg-[#050811] border border-brand-500/30 font-mono text-[11px] text-brand-300">
                  <strong>The Golden Principle:</strong><br />
                  <span className="text-emerald-400">AI Interprets</span> (extracts and normalizes ambiguous vendor syntax)<br />
                  ➔ <span className="text-cyan-300">Deterministic Rule Engine Decides</span> (hard, immutable boolean logic evaluates compliance)<br />
                  ➔ <span className="text-purple-400">Blockchain Seals</span> (cryptographic SHA-256 non-repudiation).
                </div>
                <p>
                  All extracted network settings are enforced through rigid Pydantic v2 schemas. If an adversary attempts to inject arbitrary instructions via configuration banners or SNMP community strings, the schema validation parser instantly rejects them as type violations.
                </p>
              </div>
            )}

            {activeSection === 'configs' && (
              <div className="space-y-4 text-xs font-sans text-slate-300 leading-relaxed">
                <div className="flex items-center gap-2 text-brand-300 font-mono text-sm font-bold border-b border-slate-800 pb-2">
                  <Server className="w-4 h-4 text-brand-400" />
                  <span>2. Configuration Upload & Multi-Vendor Ingestion</span>
                </div>
                <p>
                  The system ingests raw running-configurations from heterogeneous network vendors, including <strong>Cisco IOS</strong>, <strong>Juniper Junos</strong>, and <strong>Fortinet FortiOS</strong>.
                </p>
                <div className="space-y-2">
                  <h4 className="font-mono font-bold text-white text-xs">Step-by-Step Upload & Audit Flow:</h4>
                  <ol className="list-decimal pl-5 space-y-1 text-slate-400">
                    <li>Navigate to the <strong>⚡ GET STARTED</strong> or <strong>MISSION CONTROL</strong> page.</li>
                    <li>Click <strong>'📤 Upload Config'</strong> and paste raw CLI syntax or attach a <code>.conf</code> / <code>.cfg</code> file.</li>
                    <li>The agent executes <strong>Heuristic Vendor Fingerprinting</strong> using regex signature matching, calculating a confidence percentage.</li>
                    <li>Use the <strong>Device Selection Menu</strong> on the first page to select which configurations to audit (or pick 'All Devices').</li>
                    <li>Click <strong>▶ Start Autonomous Audit</strong> to normalize lines into universal Pydantic baselines with exact line-level provenance.</li>
                  </ol>
                </div>
              </div>
            )}

            {activeSection === 'compliance' && (
              <div className="space-y-4 text-xs font-sans text-slate-300 leading-relaxed">
                <div className="flex items-center gap-2 text-brand-300 font-mono text-sm font-bold border-b border-slate-800 pb-2">
                  <Terminal className="w-4 h-4 text-brand-400" />
                  <span>3. The 20 Deterministic CIS Security Benchmarks</span>
                </div>
                <p>
                  Evaluations are executed against 20 declarative rules derived from CIS Network Device Benchmarks across 2 primary categories:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-[11px]">
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                    <span className="text-brand-300 font-bold block">Management Plane (10 Rules)</span>
                    <ul className="text-slate-400 space-y-0.5">
                      <li>• CIS-MGMT-01: SSH Transport Enforced</li>
                      <li>• CIS-MGMT-02: Telnet Disabled</li>
                      <li>• CIS-MGMT-03: HTTP Server Disabled</li>
                      <li>• CIS-MGMT-04: HTTPS TLS 1.2+ Enforced</li>
                      <li>• CIS-MGMT-05: SNMP Community String Hardening</li>
                      <li>• CIS-MGMT-06: Remote Syslog Logging</li>
                      <li>• CIS-MGMT-07: Inactivity Exec Timeout ≤ 10m</li>
                      <li>• CIS-MGMT-08: Configuration Archive Logging</li>
                      <li>• CIS-MGMT-09: Strong SSH Ciphers (AES-CTR)</li>
                      <li>• CIS-MGMT-10: VTY Access-Class ACL Filtering</li>
                    </ul>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                    <span className="text-emerald-300 font-bold block">Authentication Plane (10 Rules)</span>
                    <ul className="text-slate-400 space-y-0.5">
                      <li>• CIS-AUTH-01: Password Encryption Enabled</li>
                      <li>• CIS-AUTH-02: Min Password Length ≥ 14</li>
                      <li>• CIS-AUTH-03: Account Lockout After 5 Tries</li>
                      <li>• CIS-AUTH-04: Strong Password Hashing (SHA-256)</li>
                      <li>• CIS-AUTH-05: AAA Authentication Configured</li>
                      <li>• CIS-AUTH-06: Enable Secret Configured</li>
                      <li>• CIS-AUTH-07: Local Fallback Defined</li>
                      <li>• CIS-AUTH-08: Banner Unauthorized Warning</li>
                      <li>• CIS-AUTH-09: Dedicated Admin Usernames</li>
                      <li>• CIS-AUTH-10: No Default Vendor Passwords</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {activeSection === 'hitl' && (
              <div className="space-y-4 text-xs font-sans text-slate-300 leading-relaxed">
                <div className="flex items-center gap-2 text-brand-300 font-mono text-sm font-bold border-b border-slate-800 pb-2">
                  <UserCheck className="w-4 h-4 text-brand-400" />
                  <span>4. Interactive Human-in-the-Loop & Active Learning</span>
                </div>
                <p>
                  When the agent encounters unrecognized vendor syntax (such as newly released firmware directives), it enforces a strict boundary policy (<code className="text-brand-300">policies/autonomy.py</code>) that halts autonomous guessing.
                </p>
                <div className="p-3.5 rounded-xl bg-amber-950/30 border border-amber-500/30 space-y-1.5 font-mono text-[11px] text-amber-300">
                  <div className="font-bold flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4" />
                    <span>How to Click & Resolve "NEEDS_HUMAN_REVIEW":</span>
                  </div>
                  <p className="font-sans text-slate-300 text-xs">
                    In <strong>Mission Control</strong> or the <strong>Compliance Table</strong>, click any amber badge or row marked <em>NEEDS_HUMAN_REVIEW</em>. The interactive <strong>Human Review Modal</strong> opens!
                  </p>
                  <ul className="list-disc pl-5 font-sans text-slate-400 text-xs space-y-1">
                    <li>View the exact command and line number gathered by the agent.</li>
                    <li>Inspect the agent's preliminary analysis and TF-IDF candidate match.</li>
                    <li><strong>Upload custom notes or documentation</strong> about the command.</li>
                    <li>Click <strong>PASS</strong> (rule satisfied) or <strong>FAIL</strong> (deficient).</li>
                  </ul>
                </div>
                <p>
                  Once confirmed, the decision is learned by the Knowledge Base. When subsequent devices with the same command are audited, the agent reuses the validated mapping, flipping multiple devices simultaneously!
                </p>
              </div>
            )}

            {activeSection === 'blockchain' && (
              <div className="space-y-4 text-xs font-sans text-slate-300 leading-relaxed">
                <div className="flex items-center gap-2 text-brand-300 font-mono text-sm font-bold border-b border-slate-800 pb-2">
                  <Link2 className="w-4 h-4 text-brand-400" />
                  <span>5. Blockchain Proof: Why Hashes Are Used and Their Purpose</span>
                </div>
                <p>
                  A central question in cybersecurity compliance is: <strong>"How do we prove that an audit report was not quietly altered after the inspection took place?"</strong>
                </p>
                <div className="space-y-2">
                  <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                    <div className="text-white font-mono font-bold">Why Cryptographic Hashes Are Necessary:</div>
                    <ul className="space-y-1.5 text-slate-300">
                      <li>
                        <strong>1. Immutability & Anti-Tampering:</strong> An SHA-256 hash digests the exact characters of the report into a unique 64-character hexadecimal fingerprint. Even changing a single period or a single verdict from `FAIL` to `PASS` causes a completely different hash (the avalanche effect).
                      </li>
                      <li>
                        <strong>2. Cryptographic Block Chaining:</strong> Each block contains <code>previous_hash</code> referencing the prior block. This binds all audit records in chronological order. Tampering with an old record breaks all subsequent blocks.
                      </li>
                      <li>
                        <strong>3. Non-Repudiation for Defense Audits:</strong> In government compliance (NTRO), an organization cannot later claim that a failure was an error or that they passed an audit when they did not. The hash in the blockchain ledger serves as undeniable cryptographic proof.
                      </li>
                      <li>
                        <strong>4. Provenance of Human Decisions:</strong> Every time an operator confirms an unknown command or approves a rule change, their digital sign-off and uploaded notes are sealed into a new block.
                      </li>
                    </ul>
                  </div>
                </div>
                <p>
                  You can see this live in the <strong>REPORT / TAMPER DEMO</strong> tab. The demo modifies a single finding from FAIL to PASS, and the verification engine immediately sounds the alarm: <code>TAMPERING DETECTED</code>.
                </p>
              </div>
            )}

            {activeSection === 'governance' && (
              <div className="space-y-4 text-xs font-sans text-slate-300 leading-relaxed">
                <div className="flex items-center gap-2 text-brand-300 font-mono text-sm font-bold border-b border-slate-800 pb-2">
                  <Lock className="w-4 h-4 text-brand-400" />
                  <span>6. Two-Person Rule Governance Protocol</span>
                </div>
                <p>
                  To prevent a rogue insider from weakening security policies (such as reducing required password length), our system enforces the military-grade <strong>Two-Person Rule</strong>:
                </p>
                <ol className="list-decimal pl-5 space-y-1.5 text-slate-400">
                  <li><strong>Propose Change:</strong> A security engineer proposes a change (e.g. increasing password length in <code>CIS-AUTH-02</code> from 14 to 16). This creates an unapproved draft version v2 while keeping v1 active.</li>
                  <li><strong>Dual Sign-Off:</strong> Two distinct qualified roles (Reviewer A: Lead Auditor, Reviewer B: Compliance Officer) must both digitally sign and approve the change.</li>
                  <li><strong>Activation & Blockchain Sealing:</strong> When activated, the rule is stamped with a SHA-256 hash and sealed into a new blockchain block.</li>
                  <li><strong>Automated Regression Re-Audit:</strong> The agent automatically re-evaluates all known device configurations against the new rule version and reports compliance diffs.</li>
                </ol>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Interactive AI Sentinel Chatbot (5 cols) */}
        <div className="lg:col-span-5 flex flex-col h-[650px] glass-panel rounded-2xl border border-brand-500/30 overflow-hidden shadow-2xl bg-[#090e1b]">
          {/* Chat Header */}
          <div className="p-4 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center text-white shadow-md shadow-brand-500/25">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-mono font-bold text-white flex items-center gap-1.5">
                  <span>NTRO SENTINEL COPILOT</span>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                </div>
                <div className="text-[10px] font-mono text-slate-400">
                  Real-time Agent Knowledge & Procedure Support
                </div>
              </div>
            </div>
          </div>

          {/* Chat Messages List */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3.5 terminal-scroll text-xs">
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-2.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.sender === 'bot' && (
                  <div className="w-6 h-6 rounded-md bg-brand-600/30 border border-brand-500/40 flex items-center justify-center text-brand-300 shrink-0 mt-0.5">
                    <Sparkles className="w-3 h-3" />
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-xl p-3 leading-relaxed whitespace-pre-wrap ${
                    msg.sender === 'user'
                      ? 'bg-brand-600 text-white font-sans'
                      : 'bg-slate-900/90 text-slate-200 border border-slate-800 font-sans'
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex items-center gap-2 text-slate-500 text-xs font-mono pl-8">
                <Sparkles className="w-3.5 h-3.5 text-brand-400 animate-spin" />
                <span>Sentinel Assistant is consulting knowledge base...</span>
              </div>
            )}
          </div>

          {/* Quick Prompt Suggestions */}
          <div className="p-2.5 bg-slate-950/60 border-t border-slate-800/80 overflow-x-auto terminal-scroll">
            <div className="flex gap-1.5 min-w-max">
              {suggestedPrompts.map((p, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleSendMessage(p)}
                  className="text-[10px] font-mono px-2.5 py-1 rounded-full bg-slate-900 hover:bg-slate-800 text-brand-300 border border-slate-700 transition"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* Input Box */}
          <div className="p-3 bg-slate-900/90 border-t border-slate-800">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask about procedures, hashes, human review, configs..."
                className="flex-1 bg-[#050811] border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
              <button
                type="submit"
                disabled={!chatInput.trim() || isTyping}
                className="p-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white disabled:opacity-40 transition shadow-md shadow-brand-500/20"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
