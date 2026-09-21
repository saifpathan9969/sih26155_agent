/* ═══════════════════════════════════════════════════════════════
   GAACA v2.0 — 3D Web Interface — Frontend Logic
   ═══════════════════════════════════════════════════════════════ */

// ── 3D Animated Background ─────────────────────────────────────
(function initBackground() {
    const canvas = document.getElementById('bgCanvas');
    const ctx = canvas.getContext('2d');
    let w, h;
    const particles = [];
    const PARTICLE_COUNT = 60;

    function resize() {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push({
            x: Math.random() * w,
            y: Math.random() * h,
            z: Math.random() * 1000,
            vx: (Math.random() - 0.5) * 0.3,
            vy: (Math.random() - 0.5) * 0.3,
            vz: -Math.random() * 0.8 - 0.2,
        });
    }

    function draw() {
        ctx.clearRect(0, 0, w, h);

        // Draw grid
        ctx.strokeStyle = 'rgba(0, 212, 255, 0.03)';
        ctx.lineWidth = 0.5;
        const gridSize = 60;
        for (let x = 0; x < w; x += gridSize) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
        }
        for (let y = 0; y < h; y += gridSize) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
        }

        // Draw particles
        for (const p of particles) {
            p.x += p.vx;
            p.y += p.vy;
            p.z += p.vz;

            if (p.z < 1) { p.z = 1000; p.x = Math.random() * w; p.y = Math.random() * h; }
            if (p.x < 0) p.x = w;
            if (p.x > w) p.x = 0;
            if (p.y < 0) p.y = h;
            if (p.y > h) p.y = 0;

            const scale = 800 / (800 + p.z);
            const sx = (p.x - w / 2) * scale + w / 2;
            const sy = (p.y - h / 2) * scale + h / 2;
            const radius = Math.max(0.5, 2 * scale);
            const alpha = Math.min(0.6, scale * 0.8);

            ctx.beginPath();
            ctx.arc(sx, sy, radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 212, 255, ${alpha})`;
            ctx.fill();
        }

        // Connect nearby particles
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const a = particles[i], b = particles[j];
                const dx = a.x - b.x, dy = a.y - b.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 150 && Math.abs(a.z - b.z) < 300) {
                    const alpha = (1 - dist / 150) * 0.08;
                    ctx.beginPath();
                    const sA = 800 / (800 + a.z), sB = 800 / (800 + b.z);
                    ctx.moveTo((a.x - w/2) * sA + w/2, (a.y - h/2) * sA + h/2);
                    ctx.lineTo((b.x - w/2) * sB + w/2, (b.y - h/2) * sB + h/2);
                    ctx.strokeStyle = `rgba(0, 212, 255, ${alpha})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }

        requestAnimationFrame(draw);
    }
    draw();
})();


// ── State ──────────────────────────────────────────────────────
let isWaiting = false;
const uploadedFiles = [];

// ── DOM refs ───────────────────────────────────────────────────
const chatInput     = document.getElementById('chatInput');
const sendBtn       = document.getElementById('sendBtn');
const uploadBtn     = document.getElementById('uploadBtn');
const fileInput     = document.getElementById('fileInput');
const messagesDiv   = document.getElementById('messagesContainer');
const clearChatBtn  = document.getElementById('clearChat');
const toggleLeft    = document.getElementById('toggleLeftSidebar');
const toggleRight   = document.getElementById('toggleRightSidebar');
const sidebarLeft   = document.getElementById('sidebarLeft');
const sidebarRight  = document.getElementById('sidebarRight');
const statusPill    = document.getElementById('agentStatusPill');
const statusText    = document.getElementById('agentStatusText');

// ── Sidebar toggles ────────────────────────────────────────────
toggleLeft.addEventListener('click', () => sidebarLeft.classList.toggle('hidden'));
toggleRight.addEventListener('click', () => sidebarRight.classList.toggle('hidden'));

// ── Auto-resize textarea ───────────────────────────────────────
chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
});

// ── Send on Enter ──────────────────────────────────────────────
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);

// ── Upload button ──────────────────────────────────────────────
uploadBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileUpload);

// ── Clear chat ─────────────────────────────────────────────────
clearChatBtn.addEventListener('click', () => {
    messagesDiv.innerHTML = '';
    addWelcome();
});

// ── Intel tabs ─────────────────────────────────────────────────
document.querySelectorAll('.intel-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.intel-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('tab-' + tab.dataset.tab).classList.add('active');

        // Fetch data for selected tab
        if (tab.dataset.tab === 'beliefs') fetchBeliefs();
        if (tab.dataset.tab === 'hypotheses') fetchHypotheses();
        if (tab.dataset.tab === 'memory') fetchMemory();
        if (tab.dataset.tab === 'tasks') fetchTasks();
    });
});


// ═══ Core Functions ═══════════════════════════════════════════

function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || isWaiting) return;

    // Remove welcome
    const welcome = messagesDiv.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    // Add user bubble
    addMessage('user', text);
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Show thinking
    const thinkingEl = addThinking();
    setStatus('THINKING', 'running');
    isWaiting = true;
    sendBtn.disabled = true;

    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
    })
    .then(r => r.json())
    .then(data => {
        thinkingEl.remove();

        if (data.ok) {
            const reply = data.reply || data.justification || 'Task completed.';
            addAgentMessage(reply, data);
            updateCyclesPanel(data.cycles || []);
            setStatus(data.terminal_state || 'SUCCESS', 'default');
        } else {
            addMessage('agent', `❌ Error: ${data.error || 'Unknown error'}`);
            setStatus('ERROR', 'error');
        }

        // Refresh health
        fetchStatus();
    })
    .catch(err => {
        thinkingEl.remove();
        addMessage('agent', `❌ Network error: ${err.message}`);
        setStatus('ERROR', 'error');
    })
    .finally(() => {
        isWaiting = false;
        sendBtn.disabled = false;
        chatInput.focus();
    });
}


function sendQuickAction(text) {
    chatInput.value = text;
    sendMessage();
}


// ── Message helpers ────────────────────────────────────────────

function addMessage(role, text) {
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `
        <div class="msg-header">
            <div class="msg-avatar">${role === 'user' ? '👤' : '🤖'}</div>
            <span class="msg-name">${role === 'user' ? 'You' : 'GAACA'}</span>
            <span class="msg-time">${now}</span>
        </div>
        <div class="msg-body">${escapeHtml(text)}</div>
    `;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}


function addAgentMessage(reply, data) {
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const div = document.createElement('div');
    div.className = 'message agent';

    let cycleHtml = '';
    if (data.cycles && data.cycles.length > 0) {
        const rows = data.cycles.map(c =>
            `<div class="cycle-row">
                <span class="cycle-num">${c.cycle}</span>
                <span class="cycle-action">${escapeHtml(c.action || '—')}</span>
                <span class="cycle-subgoal">${escapeHtml(c.subgoal || '')}</span>
            </div>`
        ).join('');
        cycleHtml = `<div class="cycle-trace">${rows}</div>`;
    }

    const badgeClass = (data.terminal_state === 'SUCCESS' || data.terminal_state === 'PARTIAL_SUCCESS') ? 'success' : 'failure';
    const badgeIcon = badgeClass === 'success' ? '✓' : '✗';

    div.innerHTML = `
        <div class="msg-header">
            <div class="msg-avatar">🤖</div>
            <span class="msg-name">GAACA</span>
            <span class="msg-time">${now}</span>
        </div>
        <div class="msg-body">
            ${escapeHtml(reply)}
            ${cycleHtml}
            <div class="result-badge ${badgeClass}">${badgeIcon} ${data.terminal_state} · ${data.completed_actions} actions</div>
        </div>
    `;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}


function addThinking() {
    const div = document.createElement('div');
    div.className = 'message agent';
    div.innerHTML = `
        <div class="msg-header">
            <div class="msg-avatar">🤖</div>
            <span class="msg-name">GAACA</span>
        </div>
        <div class="thinking">
            <div class="thinking-dots"><span></span><span></span><span></span></div>
            <span>Running cognitive cycles...</span>
        </div>
    `;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return div;
}

function addWelcome() {
    messagesDiv.innerHTML = document.querySelector('.welcome-message') ? '' : `
        <div class="welcome-message">
            <div class="welcome-cube-wrapper">
                <div class="welcome-cube">
                    <div class="cube-face front">🧠</div>
                    <div class="cube-face back">🛡️</div>
                    <div class="cube-face left">📊</div>
                    <div class="cube-face right">🔬</div>
                </div>
            </div>
            <h2>GAACA v2.0</h2>
            <p>General Autonomous Agent Cognitive Architecture</p>
            <div class="welcome-features">
                <div class="feature-chip" onclick="sendQuickAction('audit compliance configurations')">🛡️ Security Audit</div>
                <div class="feature-chip" onclick="sendQuickAction('what can you do')">🧠 Capabilities</div>
                <div class="feature-chip" onclick="sendQuickAction('who are you')">🤖 Identity</div>
                <div class="feature-chip" onclick="sendQuickAction('analyze project structure')">📂 Analyze</div>
            </div>
        </div>
    `;
}


// ── File upload ────────────────────────────────────────────────

function handleFileUpload() {
    const files = fileInput.files;
    if (!files.length) return;

    for (const file of files) {
        const form = new FormData();
        form.append('file', file);

        fetch('/api/upload', { method: 'POST', body: form })
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                uploadedFiles.push(data);
                renderUploadedFiles();
                // Notify in chat
                addMessage('agent', `📎 Config file uploaded: <code>${escapeHtml(data.filename)}</code> (${formatBytes(data.size_bytes)})`);
            } else {
                addMessage('agent', `❌ Upload failed: ${data.error}`);
            }
        })
        .catch(err => addMessage('agent', `❌ Upload error: ${err.message}`));
    }
    fileInput.value = '';
}

function renderUploadedFiles() {
    const container = document.getElementById('uploadedFiles');
    if (uploadedFiles.length === 0) {
        container.innerHTML = '<p class="empty-state">No files uploaded yet</p>';
        return;
    }
    container.innerHTML = uploadedFiles.map((f, idx) => `
        <div class="file-item" data-idx="${idx}">
            <div class="file-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </div>
            <span class="file-name">${escapeHtml(f.filename)}</span>
            <span class="file-size">${formatBytes(f.size_bytes)}</span>
            <button class="file-delete-btn" title="Delete ${escapeHtml(f.filename)}" onclick="deleteFile(${idx})">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
        </div>
    `).join('');
}

function deleteFile(idx) {
    const file = uploadedFiles[idx];
    if (!file) return;

    const savedName = file.saved_as;
    if (!confirm(`Delete "${file.filename}"?`)) return;

    fetch('/api/upload/' + encodeURIComponent(savedName), { method: 'DELETE' })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            uploadedFiles.splice(idx, 1);
            renderUploadedFiles();
            addMessage('agent', `🗑️ File deleted: <code>${escapeHtml(file.filename)}</code>`);
        } else {
            addMessage('agent', `❌ Delete failed: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(err => addMessage('agent', `❌ Delete error: ${err.message}`));
}

function loadUploadedFiles() {
    fetch('/api/uploads')
    .then(r => r.json())
    .then(files => {
        uploadedFiles.length = 0;
        files.forEach(f => uploadedFiles.push(f));
        renderUploadedFiles();
    })
    .catch(() => {});
}


// ── Status ─────────────────────────────────────────────────────

function setStatus(text, type) {
    statusText.textContent = text;
    statusPill.className = 'status-pill';
    if (type === 'running') statusPill.classList.add('running');
    if (type === 'error') statusPill.classList.add('error');
}


// ── Fetch APIs ─────────────────────────────────────────────────

function fetchStatus() {
    fetch('/api/status').then(r => r.json()).then(data => {
        document.getElementById('hCapabilities').textContent = data.capabilities || 0;
        document.getElementById('hImplementations').textContent = data.implementations || 0;
        document.getElementById('hEpisodes').textContent = data.episodic_episodes || 0;
        document.getElementById('hPatterns').textContent = data.procedural_patterns || 0;
        setStatus(data.status || 'READY', 'default');
    }).catch(() => {});
}

function fetchCapabilities() {
    fetch('/api/capabilities').then(r => r.json()).then(caps => {
        const container = document.getElementById('capabilitiesList');
        container.innerHTML = caps.map(c => `
            <div class="cap-card">
                <div class="cap-card-header">
                    <span class="cap-name">${escapeHtml(c.name)}</span>
                    <span class="cap-badge">${c.implementations.length}</span>
                </div>
                <div class="cap-desc">${escapeHtml(c.description)}</div>
                <div class="cap-impls">
                    ${c.implementations.map(i => `<span class="impl-tag">${escapeHtml(i)}</span>`).join('')}
                </div>
            </div>
        `).join('');
    }).catch(() => {});
}

function fetchBeliefs() {
    fetch('/api/beliefs').then(r => r.json()).then(beliefs => {
        const container = document.getElementById('beliefsList');
        if (!beliefs.length) { container.innerHTML = '<p class="empty-state">No beliefs recorded yet</p>'; return; }
        container.innerHTML = beliefs.map(b => `
            <div class="belief-item">
                <div class="belief-subject">${escapeHtml(b.subject)}</div>
                <div class="belief-value">${escapeHtml(String(b.value))}</div>
                <div class="belief-meta">
                    <span>📡 ${escapeHtml(b.source || 'unknown')}</span>
                    <span>🎯 ${(b.confidence * 100).toFixed(0)}%</span>
                </div>
                <div class="conf-bar"><div class="conf-fill" style="width:${b.confidence * 100}%"></div></div>
            </div>
        `).join('');
    }).catch(() => {});
}

function fetchHypotheses() {
    fetch('/api/hypotheses').then(r => r.json()).then(hypos => {
        const container = document.getElementById('hypothesesList');
        if (!hypos.length) { container.innerHTML = '<p class="empty-state">No hypotheses formed yet</p>'; return; }
        container.innerHTML = hypos.map(h => `
            <div class="hypo-item">
                <div class="hypo-statement">${escapeHtml(h.statement)}</div>
                <span class="hypo-status ${h.status}">${h.status.toUpperCase()}</span>
                <div class="belief-meta" style="margin-top:6px">
                    <span>Prior: ${h.prior.toFixed(2)}</span>
                    <span>Posterior: ${h.posterior.toFixed(2)}</span>
                    <span>+${h.supporting} / -${h.refuting}</span>
                </div>
                <div class="conf-bar"><div class="conf-fill" style="width:${h.posterior * 100}%"></div></div>
            </div>
        `).join('');
    }).catch(() => {});
}

function fetchMemory() {
    fetch('/api/memory').then(r => r.json()).then(data => {
        const container = document.getElementById('memoryPanel');
        const wm = data.working || {};
        const focus = wm.focus || {};
        let html = `
            <div class="cycle-card">
                <div class="cycle-card-header">
                    <span class="cycle-card-title">Working Memory</span>
                </div>
                <div class="cycle-card-body">
                    Focus: ${escapeHtml(focus.current_objective || 'None')}<br>
                    Actions: ${wm.actions || 0} · Failures: ${wm.failures || 0}
                </div>
            </div>
            <div class="cycle-card">
                <div class="cycle-card-header">
                    <span class="cycle-card-title">Episodic Memory</span>
                    <span class="cycle-card-badge">${data.total_episodes || 0} episodes</span>
                </div>
            </div>
        `;
        if (data.recent_episodes && data.recent_episodes.length) {
            html += data.recent_episodes.map(e => `
                <div class="belief-item">
                    <div class="belief-subject">Cycle ${e.cycle} · ${escapeHtml(e.action)}</div>
                    <div class="belief-meta">
                        <span>${e.success ? '✅ OK' : '❌ FAIL'}</span>
                        <span>Surprise: ${e.surprise.toFixed(2)}</span>
                    </div>
                </div>
            `).join('');
        }
        container.innerHTML = html;
    }).catch(() => {});
}

function fetchTasks() {
    fetch('/api/tasks').then(r => r.json()).then(data => {
        const container = document.getElementById('tasksPanel');
        const tasks = data.tasks || [];
        if (!tasks.length) { container.innerHTML = '<p class="empty-state">No tasks registered yet</p>'; return; }
        container.innerHTML = tasks.map(t => `
            <div class="task-item">
                <div class="task-id">${escapeHtml(t.task_id)}</div>
                <div class="task-prompt">${escapeHtml(t.prompt)}</div>
                <span class="task-status ${t.status}">${t.status.toUpperCase()}</span>
            </div>
        `).join('');
    }).catch(() => {});
}

function updateCyclesPanel(cycles) {
    const container = document.getElementById('cyclesList');
    if (!cycles.length) return;
    container.innerHTML = cycles.map(c => `
        <div class="cycle-card">
            <div class="cycle-card-header">
                <span class="cycle-card-title">Cycle ${c.cycle}</span>
                <span class="cycle-card-badge">${escapeHtml(c.action || 'N/A')}</span>
            </div>
            <div class="cycle-card-body">
                <strong>Subgoal:</strong> ${escapeHtml(c.subgoal || '—')}<br>
                ${c.observation ? `<strong>Observation:</strong> ${escapeHtml(c.observation.slice(0, 200))}` : ''}
            </div>
        </div>
    `).join('');
}


// ── Utilities ──────────────────────────────────────────────────

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}


// ── Init ───────────────────────────────────────────────────────
fetchStatus();
fetchCapabilities();
loadUploadedFiles();
