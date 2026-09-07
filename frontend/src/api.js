import axios from 'axios';

// Resolve Backend API URL with multi-tier fallback:
// 1. URL Query parameter ?backend=... or ?api=... (instant judge link sharing)
// 2. localStorage 'ntro_backend_url' (in-app configuration modal)
// 3. import.meta.env.VITE_API_BASE_URL (standard Vercel environment variable)
// 4. Local Vite dev server fallback (port 5173 -> localhost:8000)
// 5. Default window.location.origin
export function resolveApiBaseUrl() {
  if (typeof window !== 'undefined') {
    try {
      const params = new URLSearchParams(window.location.search);
      const queryBackend = params.get('backend') || params.get('api');
      if (queryBackend) {
        const cleanUrl = queryBackend.replace(/\/+$/, '');
        localStorage.setItem('ntro_backend_url', cleanUrl);
        return cleanUrl;
      }

      const saved = localStorage.getItem('ntro_backend_url');
      if (saved && saved.trim()) {
        return saved.trim().replace(/\/+$/, '');
      }
    } catch (e) {
      // Ignore in SSR / strict mode
    }
  }

  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && envUrl.trim()) {
    return envUrl.trim().replace(/\/+$/, '');
  }

  if (typeof window !== 'undefined') {
    if (window.location.port === '5173') {
      return 'http://localhost:8000';
    }
    // In production (e.g. Vercel), return empty string so requests route to same-origin /api
    // and are handled by Vercel edge reverse proxy to Railway, bypassing any local ISP DNS blocks!
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
  verifyOtp: (destination, otp, password = null, full_name = null, audience = 'enterprise') =>
    client.post('/api/auth/otp/verify', { destination, otp, password, full_name, audience }).then(r => r.data),

  switchAudience: (username, audience) =>
    client.post('/api/auth/profile/switch-audience', { username, audience }).then(r => r.data),

  me: (username) =>
    client.get('/api/auth/me', { params: { username } }).then(r => r.data),


  // Configurations & Devices
  getFixtures: (audience = null, username = null) =>
    client.get('/api/fixtures', { params: { ...(audience ? { audience } : {}), ...(username ? { username } : {}) } }).then(r => r.data),
  getConfigurations: (audience = null, username = null) =>
    client.get('/api/configurations', { params: { ...(audience ? { audience } : {}), ...(username ? { username } : {}) } }).then(r => r.data),
  uploadConfiguration: (filename, content, vendor = 'auto', username = null) =>
    client.post('/api/configurations/upload', { filename, content, vendor, username }).then(r => r.data),
  deleteConfiguration: (filename) =>
    client.delete(`/api/configurations/${filename}`).then(r => r.data),
  getDeviceBaseline: (deviceId) => client.get(`/api/devices/${deviceId}/baseline`).then(r => r.data),

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
  getHumanNeededByConfig: (username = null) =>
    client.get('/api/training/human-needed-by-config', { params: { ...(username ? { username } : {}) } }).then(r => r.data),
  resolveCommandInTraining: (payload) =>
    client.post('/api/training/resolve-command', payload).then(r => r.data),
  submitVendorSolution: (payload) =>
    client.post('/api/remediation/submit-vendor-solution', payload).then(r => r.data),
  getFederatedStatus: () =>
    client.get('/api/federated/status').then(r => r.data),
  getSohoChecks: () => client.get('/api/soho/checks').then(r => r.data),
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
};

export default api;
