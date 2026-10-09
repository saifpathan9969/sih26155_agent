import axios from 'axios';

// Resolve Backend API URL — production-safe for Railway + same-origin deployments.
//
// Priority:
//   1. ?backend= or ?api= query param (judge sharing links)
//   2. VITE_API_BASE_URL build-time env var (set in Railway variables)
//   3. Same-origin empty string — works when frontend + backend are on the same domain
//   4. localStorage override — ONLY used if it matches current origin (prevents stale URLs)
//   5. localhost:8000 for local dev (port 5173 only)
export function resolveApiBaseUrl() {
  if (typeof window !== 'undefined') {
    try {
      // 1. Explicit query param override — always wins, updates localStorage
      const params = new URLSearchParams(window.location.search);
      const queryBackend = params.get('backend') || params.get('api');
      if (queryBackend) {
        const cleanUrl = queryBackend.replace(/\/+$/, '');
        localStorage.setItem('ntro_backend_url', cleanUrl);
        return cleanUrl;
      }
    } catch (e) { /* ignore */ }
  }

  // 2. Build-time env var set in Railway / Vercel dashboard
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && envUrl.trim()) {
    return envUrl.trim().replace(/\/+$/, '');
  }

  if (typeof window !== 'undefined') {
    // 3. Local dev fallback
    if (window.location.port === '5173') {
      return 'http://localhost:8000';
    }

    // 4. Same-origin production deployment (Railway, Vercel, etc.)
    // Frontend and backend on the same domain — use relative paths.
    // Also auto-clears any stale localStorage URL from previous deployments
    // so judges / new visitors never see the offline banner.
    try {
      const saved = localStorage.getItem('ntro_backend_url');
      if (saved && saved.trim()) {
        // Only trust the saved URL if it points to the same origin as current page.
        // If it's a different origin (stale old Railway URL) — clear it silently.
        const savedOrigin = new URL(saved.trim()).origin;
        if (savedOrigin === window.location.origin) {
          return saved.trim().replace(/\/+$/, '');
        } else {
          localStorage.removeItem('ntro_backend_url');
        }
      }
    } catch (e) {
      // Malformed saved URL — clear it
      try { localStorage.removeItem('ntro_backend_url'); } catch (_) {}
    }

    // Same-origin: return empty string so all /api/* calls hit current domain
    return '';
  }

  return 'http://localhost:8000';
}

const client = axios.create({
  baseURL: resolveApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000,
});

// Dynamic interceptor to ensure requests always use current active backend URL
client.interceptors.request.use((config) => {
  config.baseURL = resolveApiBaseUrl();
  return config;
});

export const api = {
  // Backend Connection Management
  getBaseUrl: () => resolveApiBaseUrl(),
  setBaseUrl: (url) => {
    if (typeof window !== 'undefined') {
      if (url && url.trim()) {
        localStorage.setItem('ntro_backend_url', url.trim().replace(/\/+$/, ''));
      } else {
        localStorage.removeItem('ntro_backend_url');
      }
    }
  },

  // System Health
  health: () => client.get('/api/health').then(r => r.data),


  // Authentication
  login: (username, password) =>
    client.post('/api/auth/login', { username, password }).then(r => r.data),
  register: (data) =>
    client.post('/api/auth/register', data).then(r => r.data),
  googleLogin: (data) =>
    client.post('/api/auth/google', data).then(r => r.data),
  sendOtp: (destination, channel = 'sms') =>
    client.post('/api/auth/otp/send', { destination, channel }).then(r => r.data),
  verifyOtp: (destination, otp, password = null, full_name = null) =>
    client.post('/api/auth/otp/verify', { destination, otp, password, full_name, audience: 'enterprise' }).then(r => r.data),

  me: (username) =>
    client.get('/api/auth/me', { params: { username } }).then(r => r.data),


  // Configurations & Devices
  getFixtures: (username = null) =>
    client.get('/api/fixtures', { params: { ...(username ? { username } : {}) } }).then(r => r.data),
  getConfigurations: (username = null) =>
    client.get('/api/configurations', { params: { ...(username ? { username } : {}) } }).then(r => r.data),
  uploadConfiguration: (filename, content, vendor = 'auto', username = null) =>
    client.post('/api/configurations/upload', { filename, content, vendor, username }).then(r => r.data),
  // encodeURIComponent matters: filenames legitimately contain dots and may
  // contain spaces, which would otherwise corrupt the path segment.
  deleteConfiguration: (filename, username = null) =>
    client.delete(`/api/configurations/${encodeURIComponent(filename)}`, {
      params: { ...(username ? { username } : {}) },
    }).then(r => r.data),
  getDeviceBaseline: (deviceId) =>
    client.get(`/api/devices/${encodeURIComponent(deviceId)}/baseline`).then(r => r.data),



  // Rules & Autonomy
  getRules: () => client.get('/api/rules').then(r => r.data),
  getAutonomy: () => client.get('/api/autonomy').then(r => r.data),

  // Mission Mode (supports targeted device selection and user scoping)
  runMission: (goal, selected_devices = null, username = null) =>
    client.post('/api/mission/run', { goal, selected_devices, username }).then(r => r.data),

  // Interactive Human-in-the-Loop Decision Resolution
  resolveHumanReview: ({
    device_id,
    rule_id,
    command_raw,
    decision,
    notes = '',
    uploaded_info = '',
    baseline_field_path = null,
    value = null,
    reviewer = 'Lead Auditor',
  }) =>
    client.post('/api/human-review/resolve', {
      device_id,
      rule_id,
      command_raw,
      decision,
      notes,
      uploaded_info,
      baseline_field_path,
      value,
      reviewer,
    }).then(r => r.data),

  // Guide Assistant AI Chatbot
  askGuideBot: (message, history = []) =>
    client.post('/api/guide/chat', { message, history }).then(r => r.data),

  // Interactive Training & Dynamic Federated Learning Flow
  trainingDetect: (configFile) => client.get('/api/training/detect', { params: { config_file: configFile } }).then(r => r.data),
  trainingRetrieve: (query) => client.post('/api/training/retrieve', { query }).then(r => r.data),
  trainingValidate: (data) => client.post('/api/training/validate', data).then(r => r.data),
  trainingConfirm: (data) => client.post('/api/training/confirm', data).then(r => r.data),
  getHumanNeededByConfig: (username = null, includeResolved = true) =>
    client.get('/api/training/human-needed-by-config', {
      params: {
        ...(username ? { username } : {}),
        include_resolved: includeResolved,
      },
    }).then(r => r.data),
  resolveCommandInTraining: (payload) =>
    client.post('/api/training/resolve-command', payload).then(r => r.data),
  submitVendorSolution: (payload) =>
    client.post('/api/remediation/submit-vendor-solution', payload).then(r => r.data),
  getFederatedStatus: () =>
    client.get('/api/federated/status').then(r => r.data),

  // ── Verified Remediation Workflow ───────────────────────────────────────
  // PROPOSE → SANDBOX → VALIDATE → PROMOTE → REPORT
  remediationPropose: (filename, username) =>
    client.post('/api/remediation/propose', { filename, username }).then(r => r.data),
  remediationSandboxTest: (session_id) =>
    client.post('/api/remediation/sandbox/test', { session_id }).then(r => r.data),
  remediationPromote: (session_id, approved_by, force_approve = false) =>
    client.post('/api/remediation/promote', { session_id, approved_by, force_approve }).then(r => r.data),
  remediationGetSession: (session_id) =>
    client.get(`/api/remediation/session/${encodeURIComponent(session_id)}`).then(r => r.data),
  remediationGetSessions: () =>
    client.get('/api/remediation/sessions').then(r => r.data),
  remediationDeleteSession: (session_id) =>
    client.delete(`/api/remediation/session/${encodeURIComponent(session_id)}`).then(r => r.data),
  remediationReport: (session_id) =>
    client.get(`/api/remediation/report/${encodeURIComponent(session_id)}`).then(r => r.data),

  // ── Audit Session History ────────────────────────────────────────────────
  listAuditSessions: (username) =>
    client.get('/api/sessions', { params: username ? { username } : {} }).then(r => r.data),
  getAuditSession: (id) =>
    client.get(`/api/sessions/${id}`).then(r => r.data),
  trainingReuse: () => client.post('/api/training/reuse').then(r => r.data),
  trainingReset: () => client.post('/api/training/reset').then(r => r.data),

  // Rule Management & Two-Person Approval
  proposeRule: (rule_id, updates, proposed_by, rationale) =>
    client.post('/api/rules/propose', { rule_id, updates, proposed_by, rationale }).then(r => r.data),
  approveRule: (rule_id, version, reviewer_name, role) =>
    client.post('/api/rules/approve', { rule_id, version, reviewer_name, role }).then(r => r.data),
  activateRule: (rule_id, version) =>
    client.post('/api/rules/activate', { rule_id, version }).then(r => r.data),
  getRuleHistory: (rule_id) => client.get(`/api/rules/history/${rule_id}`).then(r => r.data),
  reAuditRule: (rule_id, version) =>
    client.post('/api/rules/re-audit', { rule_id, version }).then(r => r.data),

  // Blockchain Ledger & Verification
  getBlockchainLedger: () => client.get('/api/blockchain/ledger').then(r => r.data),
  verifyBlockchain: () => client.get('/api/blockchain/verify').then(r => r.data),

  // Report & Tamper Demo
  getCurrentReport: (username = null) =>
    client.get('/api/report/current', { params: { ...(username ? { username } : {}) } }).then(r => r.data),
  tamperReport: (target_rule = 'CIS-MGMT-01', fake_status = 'PASS') =>
    client.post('/api/report/tamper', { target_rule, fake_status }).then(r => r.data),
  downloadPdfReportUrl: (username = null) => {
    const base = resolveApiBaseUrl();
    const q = username ? `?username=${encodeURIComponent(username)}` : '';
    return `${base}/api/report/pdf${q}`;
  },
};

export default api;
