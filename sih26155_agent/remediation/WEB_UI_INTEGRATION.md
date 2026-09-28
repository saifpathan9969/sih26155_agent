# Remediation Workflow — Web UI Integration Guide

## Overview

This guide documents the API endpoints and UI components needed to integrate the GAACA v1 verified remediation workflow into the existing web interface.

The workflow implements: **PROPOSE → SANDBOX → VALIDATE → AUDIT → VERIFY → PROMOTE → REPORT**

All original configurations remain immutable. Fixes are tested in isolation before promotion.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web UI (Frontend)                         │
│  • Remediation Panel                                             │
│  • Sandbox Status Display                                        │
│  • Validation Results Viewer                                     │
│  • Promotion Confirmation Dialog                                 │
│  • Download Fixed Config + Diff                                  │
└─────────────────────────────────────────────────────────────────┘
                                ↓ HTTP REST API
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (main.py)                         │
│  • /api/remediation/propose          [POST]                     │
│  • /api/remediation/sandbox/test     [POST]                     │
│  • /api/remediation/promote          [POST]                     │
│  • /api/remediation/sessions         [GET]                      │
│  • /api/remediation/session/{id}     [GET, DELETE]              │
│  • /api/remediation/report/{id}      [GET]                      │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Remediation Module (Python)                     │
│  • SandboxManager        (sandbox.py)                           │
│  • RemediationProposer   (proposer.py)                          │
│  • RemediationValidator  (validator.py)                         │
│  • PromotionGate         (promotion.py)                         │
│  • ReportBuilder         (report_builder.py)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### 1. Propose Remediation

**Endpoint:** `POST /api/remediation/propose`

**Purpose:** Generate fix proposals for a configuration with violations.

**Request Body:**
```json
{
  "filename": "router01_cisco.conf",
  "username": "admin@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "20260921_143022_abc123",
  "filename": "router01_cisco.conf",
  "vendor": "cisco_ios",
  "violations": 5,
  "proposed_fixes": [
    {
      "rule_id": "CIS-MGMT-01",
      "description": "Enable SSH version 2",
      "command": "ip ssh version 2",
      "action": "add",
      "confidence": 0.95,
      "severity": "HIGH"
    }
  ],
  "fix_confidence": 0.89,
  "message": "Proposed 5 fix(es) for 5 violation(s). Ready for sandbox testing."
}
```

---

### 2. Test in Sandbox

**Endpoint:** `POST /api/remediation/sandbox/test`

**Purpose:** Apply proposed fixes in isolated sandbox and validate through 4-gate pipeline.

**Request Body:**
```json
{
  "session_id": "20260921_143022_abc123"
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "20260921_143022_abc123",
  "validation_result": {
    "passed": true,
    "gates": {
      "syntax_validation": {
        "passed": true,
        "errors": []
      },
      "target_resolution": {
        "passed": true,
        "details": {
          "target_count": 5,
          "resolved": [
            {
              "rule_id": "CIS-MGMT-01",
              "original_status": "FAIL",
              "candidate_status": "PASS"
            }
          ],
          "unresolved": []
        }
      },
      "regression_audit": {
        "passed": true,
        "details": {
          "before": {"pass": 15, "fail": 5},
          "after": {"pass": 20, "fail": 0},
          "regressions": [],
          "improvements": [
            {"rule_id": "CIS-MGMT-01"},
            {"rule_id": "CIS-MGMT-02"}
          ]
        }
      },
      "security_invariants": {
        "passed": true,
        "violations": []
      }
    },
    "summary": "All validation gates passed. 5 violations resolved, no regressions."
  },
  "message": "Sandbox validation complete. Candidate ready for promotion."
}
```

**Validation Failure Example:**
```json
{
  "success": true,
  "validation_result": {
    "passed": false,
    "gates": {
      "syntax_validation": {"passed": true},
      "target_resolution": {"passed": true},
      "regression_audit": {
        "passed": false,
        "details": {
          "regressions": [
            {"rule_id": "CIS-AUTH-02", "severity": "HIGH"}
          ]
        }
      },
      "security_invariants": {"passed": true}
    },
    "summary": "Regression detected: 1 new failure introduced."
  },
  "can_promote": false
}
```

---

### 3. Promote Configuration

**Endpoint:** `POST /api/remediation/promote`

**Purpose:** Graduate validated candidate to `output/fixed/` for deployment.

**Request Body:**
```json
{
  "session_id": "20260921_143022_abc123",
  "approved_by": "security_admin@example.com",
  "force_approve": false
}
```

**Response (Success):**
```json
{
  "success": true,
  "session_id": "20260921_143022_abc123",
  "promoted_path": "output/fixed/router01_cisco.conf",
  "decision": "APPROVED",
  "rationale": "All validation gates passed. Resolved 5 target violation(s). 5 total control(s) improved. No regressions detected.",
  "blockchain_recorded": true,
  "message": "Configuration promoted successfully"
}
```

**Response (Blocked):**
```json
{
  "success": false,
  "decision": "REJECTED",
  "rationale": "Regressions detected (2 new failure(s) introduced)",
  "message": "Promotion blocked: validation failed"
}
```

**Response (Needs Human Review):**
```json
{
  "success": false,
  "decision": "DEFERRED",
  "rationale": "Critical management/authentication controls modified (2 rule(s)). Human review required.",
  "message": "Promotion deferred: human approval needed",
  "hint": "Use force_approve=true to override after manual review"
}
```

---

### 4. List Sessions

**Endpoint:** `GET /api/remediation/sessions`

**Purpose:** List all active sandbox sessions.

**Response:**
```json
{
  "success": true,
  "sessions": [
    {
      "session_id": "20260921_143022_abc123",
      "filename": "router01_cisco.conf",
      "vendor": "cisco_ios",
      "status": "passed",
      "created_at": "2026-09-21T14:30:22",
      "created_by": "admin@example.com",
      "promoted": false,
      "fix_count": 5
    }
  ]
}
```

---

### 5. Get Session Details

**Endpoint:** `GET /api/remediation/session/{session_id}`

**Purpose:** Retrieve session details including diff.

**Response:**
```json
{
  "success": true,
  "session": {
    "session_id": "20260921_143022_abc123",
    "filename": "router01_cisco.conf",
    "status": "passed",
    "proposed_fixes": [...],
    "validation_result": {...},
    "promoted_path": null,
    "promoted_at": null
  },
  "diff": "--- original\n+++ candidate\n@@ -10,1 +10,2 @@\n-transport input telnet\n+transport input ssh\n+ip ssh version 2"
}
```

---

### 6. Delete Session

**Endpoint:** `DELETE /api/remediation/session/{session_id}`

**Purpose:** Clean up sandbox session and candidate file.

**Response:**
```json
{
  "success": true,
  "message": "Session 20260921_143022_abc123 deleted"
}
```

---

### 7. Generate Enhanced Report

**Endpoint:** `GET /api/remediation/report/{session_id}`

**Purpose:** Get detailed markdown report with sandbox validation results.

**Response:**
```json
{
  "success": true,
  "session_id": "20260921_143022_abc123",
  "filename": "router01_cisco.conf",
  "report_markdown": "## Remediation & Verification\n\n**Configuration:** router01_cisco.conf...",
  "report_format": "markdown"
}
```

---

## UI Components

### Component 1: Remediation Panel

**Location:** Audit Results Page (below findings table)

**Purpose:** Primary entry point for remediation workflow

**Features:**
- Shows when violations are detected
- Displays "Test Fix" button
- Shows sandbox status indicator

**Mockup:**
```
┌─────────────────────────────────────────────────────────────┐
│ Remediation Available                                        │
│                                                              │
│ 5 violations detected with automated fixes available        │
│                                                              │
│ [Generate & Test Fixes]  [View Previous Sessions]          │
└─────────────────────────────────────────────────────────────┘
```

**Implementation:**
```javascript
// After audit results loaded
if (auditData.failing_count > 0) {
  showRemediationPanel(auditData.filename, auditData.failing_count);
}

function generateAndTestFixes(filename) {
  // Step 1: Propose
  const proposeResp = await fetch('/api/remediation/propose', {
    method: 'POST',
    body: JSON.stringify({ filename, username: currentUser })
  });
  const { session_id, proposed_fixes } = await proposeResp.json();
  
  // Show fixes preview
  showFixesPreview(proposed_fixes);
  
  // Step 2: Test in sandbox
  const testResp = await fetch('/api/remediation/sandbox/test', {
    method: 'POST',
    body: JSON.stringify({ session_id })
  });
  const { validation_result } = await testResp.json();
  
  // Show validation results
  showValidationResults(session_id, validation_result);
}
```

---

### Component 2: Sandbox Status Display

**Purpose:** Real-time validation gate status

**Mockup:**
```
┌─────────────────────────────────────────────────────────────┐
│ Sandbox Validation                                           │
│                                                              │
│ ✓ Gate 1: Syntax Validation         PASS                   │
│ ✓ Gate 2: Target Resolution         PASS (5/5 fixed)       │
│ ✓ Gate 3: Regression Audit          PASS (no regressions)  │
│ ✓ Gate 4: Security Invariants       PASS                   │
│                                                              │
│ Status: Ready for Promotion                                 │
│                                                              │
│ [Promote to Production]  [View Diff]  [Download Report]    │
└─────────────────────────────────────────────────────────────┘
```

**Gate Status Colors:**
- Green checkmark: Gate passed
- Red X: Gate failed
- Yellow warning: Gate passed with notes

---

### Component 3: Promotion Confirmation Dialog

**Purpose:** Human review before promoting critical changes

**Mockup:**
```
┌─────────────────────────────────────────────────────────────┐
│ Confirm Promotion                                            │
│                                                              │
│ You are about to promote the following changes:             │
│                                                              │
│ • 5 violations resolved                                     │
│ • No regressions detected                                   │
│ • 2 critical controls modified (CIS-MGMT-01, CIS-AUTH-02)  │
│                                                              │
│ ⚠ Warning: Critical authentication controls were changed   │
│                                                              │
│ [View Full Diff]                                            │
│                                                              │
│ [Cancel]  [Approve & Promote]                              │
└─────────────────────────────────────────────────────────────┘
```

---

### Component 4: Diff Viewer

**Purpose:** Show side-by-side or unified diff

**Implementation:**
```javascript
function showDiff(sessionId) {
  const resp = await fetch(`/api/remediation/session/${sessionId}`);
  const { diff } = await resp.json();
  
  // Use a diff library like Monaco Diff Editor or diff2html
  renderDiff(diff);
}
```

---

### Component 5: Download Buttons

**Purpose:** Export fixed config and reports

**Features:**
- Download fixed configuration
- Download diff file
- Download enhanced PDF report

**Implementation:**
```javascript
function downloadFixed(sessionId, filename) {
  // Fixed config is at output/fixed/{filename}
  window.location.href = `/api/download/fixed/${filename}`;
}

function downloadDiff(sessionId) {
  const resp = await fetch(`/api/remediation/session/${sessionId}`);
  const { diff } = await resp.json();
  
  const blob = new Blob([diff], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${sessionId}_diff.patch`;
  a.click();
}

function downloadReport(sessionId) {
  window.location.href = `/api/remediation/report/${sessionId}`;
}
```

---

## User Workflow Example

### Step-by-Step: From Audit to Deployment

1. **User uploads config** → Audit finds 5 violations
2. **User clicks "Generate & Test Fixes"** → Backend creates sandbox session, proposes fixes
3. **Frontend shows proposed fixes** → User reviews commands to be applied
4. **User clicks "Test in Sandbox"** → Backend applies fixes to candidate, runs 4-gate validation
5. **Frontend shows validation results:**
   - ✓ Syntax: PASS
   - ✓ Target: PASS (5/5 fixed)
   - ✓ Regression: PASS
   - ✓ Invariants: PASS
6. **User clicks "Promote to Production"** → Backend checks promotion gate
7. **If critical changes:** Dialog prompts "Human review required — Approve?"
8. **User clicks "Approve & Promote"** → Config moved to `output/fixed/`
9. **User clicks "Download Fixed Config"** → Ready for deployment

---

## Error Handling

### Common Scenarios

**Scenario 1: Sandbox test fails**
- Show which gate failed
- Display detailed errors
- Offer "Try Again" or "Discard Session"

**Scenario 2: Regression detected**
- Highlight new failures in red
- Show before/after comparison
- Block promotion with clear message

**Scenario 3: Syntax errors**
- Display parser errors
- Suggest manual review
- Offer to regenerate fixes

**Scenario 4: Promotion blocked**
- Show rejection reason
- Explain why (e.g., "2 new failures introduced")
- Offer to review sandbox session or discard

---

## UI State Management

### Session Lifecycle

```
[NEW] → [PROPOSING] → [PROPOSED] → [TESTING] → [PASSED/FAILED] → [PROMOTED/DISCARDED]
```

**State Fields:**
- `session_id`: Unique identifier
- `status`: "new" | "proposed" | "testing" | "passed" | "failed" | "promoted"
- `validation_result`: Full validation object
- `can_promote`: Boolean
- `needs_review`: Boolean

---

## Security Considerations

### Access Control

- **Propose/Test:** Any authenticated user
- **Promote:** Requires `security_admin` or `lead_auditor` role
- **Force Approve:** Requires `security_admin` role only

### Audit Trail

All actions recorded in blockchain:
- Proposal created
- Sandbox test executed
- Promotion approved/rejected
- Human override applied

---

## File Paths

### Directory Structure

```
workspace/
├── uploads/              # Original configs (IMMUTABLE)
│   └── router01_cisco.conf
├── sandbox/              # Isolated test workspace
│   ├── 20260921_143022_abc123/
│   │   └── router01_cisco.conf  # Candidate with fixes applied
│   └── sessions.json     # Session metadata
└── output/
    └── fixed/            # Promoted configs (ready for deployment)
        └── router01_cisco.conf
```

### Download URLs

- **Original:** `/api/download/config/{filename}` → `uploads/{filename}`
- **Candidate:** Internal only (not exposed to users)
- **Fixed:** `/api/download/fixed/{filename}` → `output/fixed/{filename}`

---

## Testing

### Manual Testing Checklist

- [ ] Upload config with violations
- [ ] Click "Generate & Test Fixes"
- [ ] Verify proposed fixes displayed
- [ ] Click "Test in Sandbox"
- [ ] Verify all 4 gates shown
- [ ] For passing validation: Click "Promote"
- [ ] For critical changes: Confirm human review dialog appears
- [ ] Approve promotion
- [ ] Verify fixed config available for download
- [ ] Download diff and verify changes
- [ ] Download enhanced report

### API Testing with curl

```bash
# 1. Propose fixes
curl -X POST http://localhost:8080/api/remediation/propose \
  -H "Content-Type: application/json" \
  -d '{"filename": "router01_cisco.conf", "username": "admin"}'

# 2. Test in sandbox
curl -X POST http://localhost:8080/api/remediation/sandbox/test \
  -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID_FROM_STEP_1"}'

# 3. Promote
curl -X POST http://localhost:8080/api/remediation/promote \
  -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID", "approved_by": "admin@example.com"}'

# 4. Get session details
curl http://localhost:8080/api/remediation/session/SESSION_ID

# 5. List all sessions
curl http://localhost:8080/api/remediation/sessions
```

---

## Frontend Framework Examples

### React Example

```jsx
function RemediationPanel({ filename, violations }) {
  const [session, setSession] = useState(null);
  const [testing, setTesting] = useState(false);
  
  async function handleGenerateAndTest() {
    setTesting(true);
    
    // Propose
    const proposeResp = await fetch('/api/remediation/propose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename, username: currentUser.email })
    });
    const proposeData = await proposeResp.json();
    
    // Test
    const testResp = await fetch('/api/remediation/sandbox/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: proposeData.session_id })
    });
    const testData = await testResp.json();
    
    setSession({
      ...proposeData,
      validation: testData.validation_result
    });
    setTesting(false);
  }
  
  return (
    <div className="remediation-panel">
      <h3>Remediation Available</h3>
      <p>{violations} violations detected</p>
      
      {!session && (
        <button onClick={handleGenerateAndTest} disabled={testing}>
          {testing ? 'Testing...' : 'Generate & Test Fixes'}
        </button>
      )}
      
      {session && (
        <ValidationResults 
          session={session}
          onPromote={() => handlePromote(session.session_id)}
        />
      )}
    </div>
  );
}
```

---

## FAQ

**Q: What happens to the original config?**  
A: Original configs in `uploads/` are **never modified**. All fixes are applied to isolated candidates in `sandbox/`.

**Q: Can I promote a config that partially fixed issues?**  
A: No. Promotion requires **all four gates** to pass:
1. Syntax valid
2. All target violations resolved
3. No regressions
4. Security invariants preserved

**Q: What if the fix introduces new failures?**  
A: The regression audit gate detects this and **blocks promotion**. The session is marked "failed" and must be discarded.

**Q: What are "critical controls"?**  
A: Rules starting with `CIS-MGMT` (management) or `CIS-AUTH` (authentication). Changes to these require human review before auto-promotion.

**Q: Can I override the promotion gate?**  
A: Yes, using `force_approve=true` in the promote request. This requires `security_admin` role and is recorded in the blockchain audit trail.

**Q: Where do promoted configs go?**  
A: `output/fixed/{filename}`. These are the validated, deployment-ready configurations.

**Q: How do I delete a failed session?**  
A: `DELETE /api/remediation/session/{session_id}`. This removes the candidate file and session metadata.

---

## Next Steps

1. Add remediation panel to audit results page
2. Implement 4-gate validation status display
3. Create promotion confirmation dialog
4. Add diff viewer component
5. Wire up download buttons
6. Test end-to-end workflow

---

**Document Version:** 1.0  
**Last Updated:** 2026-09-21  
**Maintained By:** GAACA v1 Development Team
