import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Server, Terminal, Wrench, Lock, Link2, FileText,
  AlertTriangle, CheckCircle2, RefreshCw, Cpu, Zap, BookOpen,
  User, UserCheck, LogOut, BarChart3, Database, Wifi, Building2,
  XCircle, Layers, ArrowRightLeft, Home
} from 'lucide-react';
import api from './api';
import MissionControl from './components/MissionControl';
import DeviceViewer from './components/DeviceViewer';
import TrainingWizard from './components/TrainingWizard';
import FailedRulesView from './components/FailedRulesView';
import RuleManagement from './components/RuleManagement';
import BlockchainLedger from './components/BlockchainLedger';
import AuditReportView from './components/AuditReportView';
import AutonomyTable from './components/AutonomyTable';
import LandingPage from './components/LandingPage';
import CyberLoadingOverlay from './components/CyberLoadingOverlay';
import AuthModal from './components/AuthModal';
import ConfigManagerModal from './components/ConfigManagerModal';
import HumanReviewModal from './components/HumanReviewModal';
import ProfileModal from './components/ProfileModal';
import GuidePage from './components/GuidePage';
import SummaryPage from './components/SummaryPage';
import HomeSecurityHub from './components/HomeSecurityHub';

export default function App() {
  const [activeTab, setActiveTab] = useState('landing');
  const [audienceMode, setAudienceMode] = useState('enterprise'); // 'enterprise' | 'soho'
  const [fixtures, setFixtures] = useState([]);
  const [selectedDevices, setSelectedDevices] = useState([]);
  const [rules, setRules] = useState([]);
  const [missionResult, setMissionResult] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [systemHealth, setSystemHealth] = useState('checking');
  const [currentGoal, setCurrentGoal] = useState("Audit all network configurations and identify critical security compliance violations.");
  const [isBackendModalOpen, setIsBackendModalOpen] = useState(false);
  const [customBackendUrl, setCustomBackendUrl] = useState(() => api.getBaseUrl());

  // Authentication State (Null by default so user logs in, or pre-seeded to requested profile if stored)
  const [currentUser, setCurrentUser] = useState(() => {
    const saved = localStorage.getItem('ntro_user');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) { /* ignore */ }
    }
    return null;
  });

  // Modal States
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [isHumanReviewOpen, setIsHumanReviewOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [activeHumanReview, setActiveHumanReview] = useState(null);

  // Load initial data (filters to user's configs: pre-fed for saifullahpathan49@gmail.com; blank for new users until uploaded)
  const loadInitialData = async (mode = audienceMode, user = currentUser) => {
    try {
      const h = await api.health();
      setSystemHealth(h.status === 'ok' ? 'online' : 'error');
      const uname = user?.username || (user?.email);
      const f = await api.getFixtures(mode === 'soho' ? 'home' : null, uname);
      const devList = f.devices || [];
      setFixtures(devList);
      setSelectedDevices(devList.map(d => d.filename));
      const r = await api.getRules();
      setRules(r.rules || []);
    } catch (err) {
      console.error("Health check / initial load error:", err);
      setSystemHealth('offline');
    }
  };

  useEffect(() => {
    loadInitialData(audienceMode, currentUser);
  }, [audienceMode, currentUser]);

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    localStorage.setItem('ntro_user', JSON.stringify(user));
    if (user.audience === 'home' || user.audience === 'soho') {
      setAudienceMode('soho');
    } else {
      setAudienceMode('enterprise');
    }
    // As requested: Once logged in, user first lands on the Guide Page!
    setActiveTab('guide');
    loadInitialData(user.audience === 'home' ? 'soho' : 'enterprise', user);
  };

  // Switch between Enterprise and Home & SOHO panel anytime
  const handleSwitchPanel = async (newMode) => {
    const targetMode = (newMode === 'soho' || newMode === 'home') ? 'soho' : 'enterprise';
    setAudienceMode(targetMode);
    if (currentUser) {
      const updatedUser = { ...currentUser, audience: targetMode };
      setCurrentUser(updatedUser);
      localStorage.setItem('ntro_user', JSON.stringify(updatedUser));
      try {
        await api.switchAudience(currentUser.username, targetMode);
      } catch (e) {
        console.warn("Could not sync audience switch with backend:", e);
      }
    }
    setActiveTab(targetMode === 'soho' ? 'soho' : 'guide');
    loadInitialData(targetMode, currentUser);
  };

  const handleLogout = () => {
    localStorage.removeItem('ntro_user');
    setCurrentUser(null);
    setActiveTab('landing');
    setFixtures([]);
    setSelectedDevices([]);
    setMissionResult(null);
    setIsAuthModalOpen(true);
  };

  // Run Mission handler with visual cyber telemetry timing
  const handleRunMission = async (goal, devicesToAudit = null) => {
    setCurrentGoal(goal);
    setIsRunning(true);
    const targets = devicesToAudit || selectedDevices;
    const uname = currentUser?.username || currentUser?.email;

    try {
      const [result] = await Promise.all([
        api.runMission(goal, targets, uname),
        new Promise(resolve => setTimeout(resolve, 2600)),
      ]);
      setMissionResult(result);
    } catch (err) {
      console.error("Mission run error:", err);
    } finally {
      setIsRunning(false);
    }
  };

  // Callback when an unknown command or human-needed item is clicked
  const handleOpenHumanReview = (item) => {
    setActiveHumanReview(item);
    setIsHumanReviewOpen(true);
  };

  const handleHumanReviewResolved = (result) => {
    loadInitialData(audienceMode);
    if (missionResult && missionResult.findings_by_device) {
      const updatedFindings = { ...missionResult.findings_by_device };
      const devFindings = updatedFindings[result.device_id] || [];
      const idx = devFindings.findIndex(f => f.rule_id === result.rule_id);
      if (idx !== -1) {
        devFindings[idx] = {
          ...devFindings[idx],
          status: result.after_status,
        };
      }
      setMissionResult({
        ...missionResult,
        findings_by_device: updatedFindings,
      });
    }
  };

  // Navigation Items:
  // Order: Guide -> (SOHO Hub) -> Mission -> Devices -> Autonomy -> Training -> Failed -> Rules -> Blockchain -> Report -> Summary
  const navItems = audienceMode === 'soho' ? [
    { id: 'guide', label: '📖 HOME GUIDE & COPILOT', icon: BookOpen },
    { id: 'soho', label: '🏠 WI-FI SECURITY HUB', icon: Wifi },
    { id: 'mission', label: '🎯 MISSION CONTROL (3 ROUTERS)', icon: Terminal },
    { id: 'devices', label: `🖥️ ROUTERS & APs (${fixtures.length})`, icon: Server },
    { id: 'autonomy', label: '⚙️ AUTONOMY POLICY', icon: Wrench },
    { id: 'training', label: '🧠 AI RETRIEVAL / KB', icon: Cpu },
    { id: 'failed', label: '❌ FAILED COMMANDS', icon: XCircle },
    { id: 'rules', label: '⚖️ RULE GOVERNANCE', icon: Lock },
    { id: 'blockchain', label: '🔗 BLOCKCHAIN PROOF', icon: Link2 },
    { id: 'report', label: '📑 AUDIT REPORT', icon: FileText },
    { id: 'summary', label: '📊 SUMMARY & DEBRIEF', icon: BarChart3 },
  ] : [
    { id: 'guide', label: '📖 GUIDE & COPILOT', icon: BookOpen },
    { id: 'mission', label: '🎯 MISSION CONTROL', icon: Terminal },
    { id: 'devices', label: `🖥️ DEVICES (${fixtures.length})`, icon: Server },
    { id: 'autonomy', label: '⚙️ AUTONOMY POLICY', icon: Wrench },
    { id: 'training', label: '🧠 AI RETRIEVAL / KB', icon: Cpu },
    { id: 'failed', label: '❌ FAILED COMMANDS', icon: XCircle },
    { id: 'rules', label: '⚖️ RULE GOVERNANCE', icon: Lock },
    { id: 'blockchain', label: '🔗 BLOCKCHAIN PROOF', icon: Link2 },
    { id: 'report', label: '📑 AUDIT REPORT', icon: FileText },
    { id: 'summary', label: '📊 SUMMARY & DEBRIEF', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans">
      {/* Global High-Tech Cyber Mission Loading Overlay */}
      <CyberLoadingOverlay isVisible={isRunning} goal={currentGoal} />

      {/* Global Modals */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onLoginSuccess={handleLoginSuccess}
        currentUser={currentUser}
      />

      <ConfigManagerModal
        isOpen={isConfigModalOpen}
        onClose={() => setIsConfigModalOpen(false)}
        onConfigurationsChanged={() => loadInitialData(audienceMode, currentUser)}
        currentUser={currentUser}
      />

      <HumanReviewModal
        isOpen={isHumanReviewOpen}
        onClose={() => setIsHumanReviewOpen(false)}
        reviewData={activeHumanReview}
        onResolved={handleHumanReviewResolved}
        currentUser={currentUser}
      />

      <ProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        currentUser={currentUser}
        audienceMode={audienceMode}
        onSwitchPanel={handleSwitchPanel}
        onLogout={handleLogout}
      />

      {/* Top Universal App Header */}
      <header className="sticky top-0 z-40 bg-[#0b1120]/90 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-8 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xl">
        <div className="flex items-center gap-3">
          <div
            onClick={() => setActiveTab('landing')}
            className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white shadow-lg shadow-brand-500/25 cursor-pointer"
            title="Return to Get Started landing"
          >
            <Shield className="w-5 h-5 fill-current" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm font-extrabold text-white tracking-wider cursor-pointer" onClick={() => setActiveTab('landing')}>
                SIH26155
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-950 text-brand-300 font-mono border border-brand-500/30">
                NTRO
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-900 text-slate-400 font-mono border border-slate-800">
                CIS & SOHO
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              AI-Driven Multi-Vendor Network Security Compliance Auditor
            </p>
          </div>
        </div>

        {/* User Profile Pill / Login Trigger & Health */}
        <div className="flex flex-wrap items-center gap-2.5">
          {currentUser ? (
            <div className="flex items-center gap-2">
              {/* Quick Panel Mode Switcher Button */}
              <button
                type="button"
                onClick={() => handleSwitchPanel(audienceMode === 'soho' ? 'enterprise' : 'soho')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-mono font-bold transition shadow-sm cursor-pointer ${
                  audienceMode === 'soho'
                    ? 'bg-amber-950/70 border-amber-500/50 text-amber-300 hover:bg-amber-900/60'
                    : 'bg-brand-950/70 border-brand-500/50 text-brand-300 hover:bg-brand-900/60'
                }`}
                title={`Currently in ${audienceMode === 'soho' ? 'Home & SOHO' : 'Enterprise'} panel. Click to switch!`}
              >
                <ArrowRightLeft className="w-3.5 h-3.5" />
                <span>{audienceMode === 'soho' ? '🏠 Home Security' : '🏢 Enterprise Compliance'}</span>
                <span className="text-[10px] text-slate-400 font-normal hidden lg:inline">
                  (Switch to {audienceMode === 'soho' ? 'Enterprise' : 'Home'})
                </span>
              </button>

              <div className="flex items-center gap-2 bg-[#050811] px-3 py-1.5 rounded-xl border border-slate-800 font-mono text-xs">
                <button
                  onClick={() => setIsProfileModalOpen(true)}
                  className="flex items-center gap-1.5 text-slate-200 hover:text-brand-300 transition cursor-pointer"
                  title="Manage Account & Switch Audit Interface"
                >
                  <UserCheck className="w-3.5 h-3.5 text-brand-400" />
                  <span className="font-semibold">{currentUser.full_name || currentUser.username}</span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-brand-950 text-brand-300 border border-brand-500/30 hidden md:inline">
                    {currentUser.role}
                  </span>
                </button>
                <button
                  onClick={handleLogout}
                  className="text-slate-500 hover:text-rose-400 p-0.5 rounded transition"
                  title="Sign Out"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setIsAuthModalOpen(true)}
              className="px-3 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-mono font-bold text-xs flex items-center gap-1.5 transition shadow-sm"
            >
              <User className="w-3.5 h-3.5" />
              <span>Operator Login</span>
            </button>
          )}

          {/* System Health / Backend Switcher */}
          <button
            type="button"
            onClick={() => {
              setCustomBackendUrl(api.getBaseUrl());
              setIsBackendModalOpen(true);
            }}
            className="flex items-center gap-1.5 font-mono text-xs bg-slate-900 hover:bg-slate-800 px-2.5 py-1.5 rounded-xl border border-slate-800 transition cursor-pointer"
            title="Click to view or update Railway backend connection URL"
          >
            <span className={`w-2 h-2 rounded-full ${
              systemHealth === 'online' ? 'bg-emerald-400 shadow-sm shadow-emerald-400' : 'bg-rose-400'
            } animate-pulse`} />
            <span className="text-slate-300 capitalize hidden sm:inline">{systemHealth === 'online' ? 'Railway Live' : 'Backend Offline'}</span>
            <Server className="w-3 h-3 text-slate-500 ml-0.5" />
          </button>
        </div>
      </header>

      {/* Backend Disconnected Warning Banner (for Vercel deployment) */}
      {systemHealth === 'offline' && (
        <div className="bg-amber-950/90 border-b border-amber-500/40 px-4 py-2 text-xs font-mono text-amber-200 flex flex-wrap items-center justify-between gap-2 shadow-md">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 animate-bounce" />
            <span>
              Backend Disconnected: pointing to <code className="bg-black/40 px-1.5 py-0.5 rounded text-amber-300 font-bold">{api.getBaseUrl()}</code>
            </span>
          </div>
          <button
            type="button"
            onClick={() => {
              setCustomBackendUrl(api.getBaseUrl());
              setIsBackendModalOpen(true);
            }}
            className="px-2.5 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-400/50 text-amber-200 font-semibold transition text-[11px]"
          >
            Connect Railway Backend URL ↗
          </button>
        </div>
      )}

      {/* Backend URL Configuration Modal */}
      {isBackendModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-[#0c1222] border border-brand-500/40 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Server className="w-5 h-5 text-brand-400" />
                <h3 className="font-mono font-bold text-white text-sm">RAILWAY BACKEND CONNECTION</h3>
              </div>
              <button
                type="button"
                onClick={() => setIsBackendModalOpen(false)}
                className="text-slate-400 hover:text-white p-1"
              >
                ✕
              </button>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              When hosting the frontend on <span className="text-white font-bold">Vercel</span>, enter your public Railway service URL below (e.g. <span className="text-brand-300 font-mono">https://web-production-xxxx.up.railway.app</span>).
            </p>
            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">
                RAILWAY API BASE URL:
              </label>
              <input
                type="url"
                value={customBackendUrl}
                onChange={(e) => setCustomBackendUrl(e.target.value)}
                placeholder="https://sih26155-production.up.railway.app"
                className="w-full bg-[#050811] border border-slate-700 rounded-xl px-3 py-2.5 text-xs font-mono text-white placeholder-slate-600 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div className="flex items-center justify-between pt-2">
              <button
                type="button"
                onClick={() => {
                  api.setBaseUrl('');
                  setCustomBackendUrl(api.getBaseUrl());
                  loadInitialData();
                  setIsBackendModalOpen(false);
                }}
                className="text-xs text-slate-400 hover:text-slate-200 underline font-mono"
              >
                Reset Default
              </button>
              <button
                type="button"
                onClick={async () => {
                  api.setBaseUrl(customBackendUrl);
                  await loadInitialData();
                  setIsBackendModalOpen(false);
                }}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-brand-600 to-cyan-600 hover:from-brand-500 hover:to-cyan-500 text-white font-mono text-xs font-bold shadow-lg shadow-brand-500/25 transition"
              >
                Save & Connect
              </button>
            </div>
          </div>
        </div>
      )}


      {/* Navigation Tab Bar — Hidden when on initial Landing page */}
      {activeTab !== 'landing' && (
        <nav className="bg-[#090e1b] border-b border-slate-800/80 px-4 sm:px-8 py-2 overflow-x-auto terminal-scroll">
          <div className="flex items-center gap-1 min-w-max">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-mono font-medium transition-all relative ${
                    isActive
                      ? 'text-white bg-brand-600/90 shadow-md shadow-brand-500/20 font-bold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-slate-500'}`} />
                  <span>{item.label}</span>
                  {isActive && (
                    <motion.div
                      layoutId="activeTabIndicator"
                      className="absolute -bottom-2 left-2 right-2 h-0.5 bg-brand-400 rounded-full"
                    />
                  )}
                </button>
              );
            })}
          </div>
        </nav>
      )}

      {/* Main Content Area with Page Transitions */}
      <main className="flex-1 p-4 sm:p-8 max-w-7xl w-full mx-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.18 }}
          >
            {activeTab === 'landing' && (
              <LandingPage
                onGetStarted={() => {
                  if (currentUser) {
                    setActiveTab('guide');
                  } else {
                    setIsAuthModalOpen(true);
                  }
                }}
                fixtures={fixtures}
                selectedDevices={selectedDevices}
                setSelectedDevices={setSelectedDevices}
                onOpenUploadModal={() => setIsConfigModalOpen(true)}
              />
            )}

            {activeTab === 'guide' && (
              <GuidePage
                onNavigateTab={(tab) => setActiveTab(tab)}
              />
            )}

            {activeTab === 'mission' && (
              <MissionControl
                onRunMission={handleRunMission}
                missionResult={missionResult}
                isRunning={isRunning}
                fixtures={fixtures}
                selectedDevices={selectedDevices}
                setSelectedDevices={setSelectedDevices}
                onNavigateTab={(tab) => setActiveTab(tab)}
                onOpenUploadModal={() => setIsConfigModalOpen(true)}
                onOpenHumanReview={handleOpenHumanReview}
              />
            )}

            {activeTab === 'devices' && (
              <DeviceViewer fixtures={fixtures} />
            )}

            {activeTab === 'soho' && (
              <HomeSecurityHub
                fixtures={fixtures}
                onOpenUploadModal={() => setIsConfigModalOpen(true)}
              />
            )}

            {activeTab === 'autonomy' && (
              <AutonomyTable
                fixtures={fixtures}
                findingsByDevice={missionResult?.findings_by_device || {}}
                onOpenHumanReview={handleOpenHumanReview}
              />
            )}

            {activeTab === 'training' && (
              <TrainingWizard
                fixtures={fixtures}
                onMissionUpdate={() => handleRunMission("Audit all network configurations and identify critical security compliance violations.", selectedDevices)}
              />
            )}

            {activeTab === 'failed' && (
              <FailedRulesView
                fixtures={fixtures}
                findingsByDevice={missionResult?.findings_by_device || {}}
                rules={rules}
                onOpenHumanReview={handleOpenHumanReview}
              />
            )}

            {activeTab === 'rules' && (
              <RuleManagement
                onRuleActivated={() => {
                  api.getRules().then(r => setRules(r.rules || []));
                }}
              />
            )}

            {activeTab === 'blockchain' && (
              <BlockchainLedger />
            )}

            {activeTab === 'report' && (
              <AuditReportView />
            )}

            {activeTab === 'summary' && (
              <SummaryPage
                missionResult={missionResult}
                fixtures={fixtures}
                rules={rules}
                onNavigateTab={(tab) => setActiveTab(tab)}
                onOpenHumanReview={handleOpenHumanReview}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="bg-[#050811] border-t border-slate-900 py-3.5 px-6 text-center text-xs text-slate-500 font-mono flex flex-col sm:flex-row items-center justify-between gap-2">
        <span>SIH 2026 Problem Statement SIH26155 — Organization: NTRO — Theme: Blockchain & Cybersecurity</span>
        <span className="text-slate-400">Deterministic Engine & Cryptographic Provenance</span>
      </footer>
    </div>
  );
}
