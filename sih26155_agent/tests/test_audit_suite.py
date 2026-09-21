"""
Automated Test Suite — SIH26155 Live Judge Demo
===============================================
Covers the 20 requirements specified in the project build contract:
 1. Cisco parsing
 2. Juniper parsing
 3. Unsupported vendor handling (FortiOS graceful degradation)
 4. Universal Security Baseline validation
 5. Deterministic rule evaluation
 6. Unknown syntax detection
 7. Cold-start retrieval (similarity 0.00)
 8. Human training flow
 9. Invalid type rejection (e.g. "yes-please" -> rejected)
10. Knowledge reuse on future devices (~0.82 similarity)
11. Re-evaluation (before vs after finding flip)
12. Reflection & cross-device clustering
13. Rule creation
14. Rule modification
15. Rule versioning (v1 preserved, v2 created)
16. Semantic conflict detection
17. Two-person approval state machine
18. Report generation
19. Cryptographic SHA-256 hash calculation & on-chain verification
20. Tamper detection verification
"""

import sys
from pathlib import Path

# Set up paths
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "agent"))
sys.path.insert(1, str(_ROOT))

import pytest
from blockchain_integrity import BlockchainLedger, compute_data_hash
from fixtures import DEVICE_CONFIGS
from memory.knowledge_base import (
    KnowledgeBaseEntry,
    VendorKnowledgeBase,
    validate_mapping,
)
from reflection import cluster_unknowns
from rule_engine import evaluate_baseline, load_rules, resolve_evidence_field
from rule_manager import ApprovalStatus, RuleManager
from security_baseline_schema import (
    EvidenceField,
    FindingStatus,
    InterpretationMethod,
    SecurityBaseline,
    ServiceState,
    VendorFamily,
)
from tools.discovery import discover_configs
from tools.fingerprint import fingerprint_vendor
from tools.parsing import parse_config
from tools.reporting import generate_report


# 1. Cisco parsing
def test_01_cisco_parsing():
    raw = DEVICE_CONFIGS["dev01_cisco.conf"]
    vendor, conf = fingerprint_vendor(raw)
    assert vendor == VendorFamily.CISCO_IOS
    assert conf >= 0.75

    baseline, unknowns = parse_config(vendor, raw, "dev01_cisco.conf")
    assert isinstance(baseline, SecurityBaseline)
    assert baseline.management.ssh.protocol_version.value == 2
    assert baseline.management.telnet.enabled.value == ServiceState.DISABLED
    assert baseline.authentication.password_policy.min_length.value == 14


# 2. Juniper parsing
def test_02_juniper_parsing():
    raw = DEVICE_CONFIGS["dev03_juniper.conf"]
    vendor, conf = fingerprint_vendor(raw)
    assert vendor == VendorFamily.JUNIPER_JUNOS
    assert conf >= 0.75

    baseline, unknowns = parse_config(vendor, raw, "dev03_juniper.conf")
    assert isinstance(baseline, SecurityBaseline)
    assert baseline.management.ssh.protocol_version.value == 2
    assert baseline.management.telnet.enabled.value == ServiceState.DISABLED
    assert baseline.management.http.enabled.value == ServiceState.DISABLED


# 3. Unsupported vendor handling (FortiOS graceful degradation)
def test_03_unsupported_vendor_graceful_degradation():
    raw = DEVICE_CONFIGS["dev06_fortinet.conf"]
    vendor, conf = fingerprint_vendor(raw)
    assert vendor == VendorFamily.FORTINET_FORTIOS

    baseline, unknowns = parse_config(vendor, raw, "dev06_fortinet.conf")
    # All security fields must remain unknown rather than being guessed
    assert baseline.management.ssh.protocol_version.explicitly_configured is False
    assert baseline.management.ssh.protocol_version.interpretation.method == InterpretationMethod.DEFAULT_ASSUMED
    # Unknown commands flagged for review
    assert len(unknowns) >= 2


# 4. Universal Security Baseline validation
def test_04_schema_validation():
    raw = DEVICE_CONFIGS["dev01_cisco.conf"]
    vendor, _ = fingerprint_vendor(raw)
    baseline, _ = parse_config(vendor, raw, "dev01_cisco.conf")
    dumped = baseline.model_dump()
    reloaded = SecurityBaseline.model_validate(dumped)
    assert reloaded.device.hostname == baseline.device.hostname


# 5. Deterministic rule evaluation
def test_05_deterministic_compliance():
    raw = DEVICE_CONFIGS["dev02_cisco.conf"]
    vendor, _ = fingerprint_vendor(raw)
    baseline, _ = parse_config(vendor, raw, "dev02_cisco.conf")
    findings = evaluate_baseline(baseline)

    # dev02 has Telnet enabled -> CIS-MGMT-01 MUST FAIL
    telnet_finding = next((f for f in findings if f.rule_id == "CIS-MGMT-01"), None)
    assert telnet_finding is not None
    assert telnet_finding.status == FindingStatus.FAIL

    # dev02 has min_length 8 -> CIS-AUTH-02 (>= 14) MUST FAIL
    pwd_finding = next((f for f in findings if f.rule_id == "CIS-AUTH-02"), None)
    assert pwd_finding is not None
    assert pwd_finding.status == FindingStatus.FAIL


# 6. Unknown syntax detection
def test_06_unknown_syntax_detection():
    raw = DEVICE_CONFIGS["dev03_juniper.conf"]
    vendor, _ = fingerprint_vendor(raw)
    _, unknowns = parse_config(vendor, raw, "dev03_juniper.conf")
    lockout_unknown = next((u for u in unknowns if "retry-options" in u.raw), None)
    assert lockout_unknown is not None
    assert "tries-before-disconnect" in lockout_unknown.raw


# 7. Cold-start retrieval (similarity 0.00)
def test_07_cold_start_retrieval():
    kb = VendorKnowledgeBase()
    cmd = "set system login retry-options tries-before-disconnect 5"
    candidate = kb.retrieve(cmd, VendorFamily.JUNIPER_JUNOS)
    assert candidate.similarity == 0.0
    assert candidate.is_confident is False
    assert candidate.matched_entry is None


# 8. Human training flow
def test_08_human_training_flow():
    kb = VendorKnowledgeBase()
    entry = KnowledgeBaseEntry(
        vendor=VendorFamily.JUNIPER_JUNOS,
        raw_pattern="set system login retry-options tries-before-disconnect 5",
        security_category="Authentication",
        baseline_field_path="authentication.account_lockout.enabled",
        value_type_hint="bool",
        added_by="security_admin",
    )
    kb.add(entry)
    assert len(kb.entries_for_vendor(VendorFamily.JUNIPER_JUNOS)) == 1


# 9. Invalid type rejection
def test_09_invalid_type_rejection():
    # Trying to assign string 'yes-please' to boolean field
    res = validate_mapping("authentication.account_lockout.enabled", "yes-please")
    assert res.valid is False
    assert "bool" in res.expected_type

    # Valid boolean assignment
    res_valid = validate_mapping("authentication.account_lockout.enabled", True)
    assert res_valid.valid is True


# 10. Knowledge reuse on future devices (~0.82 similarity)
def test_10_knowledge_reuse():
    kb = VendorKnowledgeBase()
    # Learned pattern:
    kb.add(KnowledgeBaseEntry(
        vendor=VendorFamily.JUNIPER_JUNOS,
        raw_pattern="set system login retry-options tries-before-disconnect 5 lockout-period 15",
        security_category="Authentication",
        baseline_field_path="authentication.account_lockout.enabled",
        value_type_hint="bool",
        added_by="security_admin",
    ))

    # New command on future device:
    query = "set system login retry-options tries-before-disconnect 6"
    candidate = kb.retrieve(query, VendorFamily.JUNIPER_JUNOS)
    assert candidate.matched_entry is not None
    assert candidate.similarity > 0.70  # Actual TF-IDF produces ~0.82
    assert candidate.is_confident is True


# 11. Re-evaluation (before vs after finding flip)
def test_11_reevaluation_flip():
    raw = DEVICE_CONFIGS["dev03_juniper.conf"]
    vendor, _ = fingerprint_vendor(raw)
    baseline, _ = parse_config(vendor, raw, "dev03_juniper.conf")

    # Before human training: lockout field is unconfigured -> CIS-AUTH-03 is NEEDS_HUMAN_REVIEW
    finding_before = next((f for f in evaluate_baseline(baseline) if f.rule_id == "CIS-AUTH-03"), None)
    assert finding_before.status == FindingStatus.NEEDS_HUMAN_REVIEW

    # Apply confirmed mapping
    baseline.authentication.account_lockout.enabled = EvidenceField(
        value=True,
        explicitly_configured=True,
        interpretation=EvidenceField.unknown().interpretation,
    )
    baseline.authentication.account_lockout.enabled.interpretation.confidence = 1.0

    # After human training: CIS-AUTH-03 flips to PASS
    finding_after = next((f for f in evaluate_baseline(baseline) if f.rule_id == "CIS-AUTH-03"), None)
    assert finding_after.status == FindingStatus.PASS


# 12. Reflection & cross-device clustering
def test_12_reflection_clustering():
    raw3 = DEVICE_CONFIGS["dev03_juniper.conf"]
    raw4 = DEVICE_CONFIGS["dev04_juniper.conf"]
    raw5 = DEVICE_CONFIGS["dev05_juniper.conf"]

    _, unknowns3 = parse_config(VendorFamily.JUNIPER_JUNOS, raw3, "dev03_juniper.conf")
    _, unknowns4 = parse_config(VendorFamily.JUNIPER_JUNOS, raw4, "dev04_juniper.conf")
    _, unknowns5 = parse_config(VendorFamily.JUNIPER_JUNOS, raw5, "dev05_juniper.conf")

    all_unknowns = unknowns3 + unknowns4 + unknowns5
    file_map = {u.file: u.file for u in all_unknowns}

    groups = cluster_unknowns(all_unknowns, file_map)
    lockout_group = next((g for g in groups if "retry-options" in g.representative_raw), None)
    assert lockout_group is not None
    # 3 Juniper devices clustered into ONE review group
    assert len(lockout_group.device_ids) == 3


# 13. Rule creation & 14. Rule modification & 15. Rule versioning
def test_13_14_15_rule_versioning():
    rm = RuleManager()
    active = rm.get_active_rules()
    assert len(active) == 20

    # Propose modification to CIS-AUTH-02: min_length >= 16
    success, new_v, err = rm.propose_rule_change(
        rule_id="CIS-AUTH-02",
        updates={"evaluation": {"expected": 16}},
        proposed_by="alice_lead",
        rationale="Upgrade minimum password length to 16 characters",
    )
    assert success is True
    assert new_v["version"] == 2
    assert new_v["evaluation"]["expected"] == 16
    assert new_v["status"] == ApprovalStatus.PENDING_APPROVAL.value

    # Check that v1 is preserved in history
    history = rm.get_rule_history("CIS-AUTH-02")
    assert len(history) == 2
    assert history[0]["version"] == 1
    assert history[0]["evaluation"]["expected"] == 14
    assert history[1]["version"] == 2


# 16. Semantic conflict detection
def test_16_conflict_detection():
    rm = RuleManager()
    # Try proposing a conflicting rule targeting the same field
    conflicting = {
        "id": "CUSTOM-CONFLICT-01",
        "title": "Conflicting password length rule",
        "framework": "custom",
        "severity": "high",
        "baseline_field_path": "authentication.password_policy.min_length",
        "evaluation": {"operator": "greater_than_or_equal", "expected": 20},
    }
    conflicts = rm.detect_conflicts(conflicting)
    assert len(conflicts) > 0
    assert "CIS-AUTH-02" in conflicts[0]


# 17. Two-person approval state machine
def test_17_two_person_approval():
    rm = RuleManager()
    rm.propose_rule_change(
        rule_id="CIS-AUTH-02",
        updates={"evaluation": {"expected": 16}},
        proposed_by="alice",
    )

    # Try activating before approvals -> MUST FAIL
    act_ok, _, err = rm.activate_rule("CIS-AUTH-02", version=2)
    assert act_ok is False
    assert "Two-person approval required" in err

    # Reviewer A approves
    app1_ok, v_state, _ = rm.approve_rule("CIS-AUTH-02", version=2, reviewer_name="Reviewer_A")
    assert app1_ok is True
    assert v_state["status"] == ApprovalStatus.APPROVED_BY_ONE.value

    # Reviewer A cannot approve a second time
    dup_ok, _, dup_err = rm.approve_rule("CIS-AUTH-02", version=2, reviewer_name="Reviewer_A")
    assert dup_ok is False
    assert "already approved" in dup_err

    # Still cannot activate with only 1 approval
    act_ok2, _, _ = rm.activate_rule("CIS-AUTH-02", version=2)
    assert act_ok2 is False

    # Reviewer B approves
    app2_ok, v_state2, _ = rm.approve_rule("CIS-AUTH-02", version=2, reviewer_name="Reviewer_B")
    assert app2_ok is True
    assert v_state2["status"] == ApprovalStatus.APPROVED.value

    # Now activation succeeds
    act_ok3, active_v, _ = rm.activate_rule("CIS-AUTH-02", version=2)
    assert act_ok3 is True
    assert active_v["status"] == ApprovalStatus.ACTIVE.value


# 18. Report generation
def test_18_report_generation():
    raw1 = DEVICE_CONFIGS["dev01_cisco.conf"]
    raw2 = DEVICE_CONFIGS["dev02_cisco.conf"]
    bl1, _ = parse_config(VendorFamily.CISCO_IOS, raw1, "dev01_cisco.conf")
    bl2, _ = parse_config(VendorFamily.CISCO_IOS, raw2, "dev02_cisco.conf")

    findings_map = {
        "dev01_cisco.conf": evaluate_baseline(bl1),
        "dev02_cisco.conf": evaluate_baseline(bl2),
    }
    from memory.working import WorkingMemory
    wm = WorkingMemory()
    wm.total_devices = 2
    wm.processed = 2

    report = generate_report("Audit network", wm, findings_map, [], lambda r, v: "N/A")
    assert "# Mission Report" in report
    assert "dev01_cisco.conf" in report
    assert "dev02_cisco.conf" in report


# 19. Cryptographic SHA-256 hash calculation & on-chain verification
def test_19_blockchain_integrity():
    ledger = BlockchainLedger()
    block, rep_hash = ledger.record_report_integrity(
        report_id="REP-001",
        report_text="# Test Report Content",
        goal="Audit goal",
        summary={"devices": 6},
    )
    assert rep_hash == compute_data_hash("# Test Report Content")
    assert block.index == 1

    valid, err = ledger.verify_chain()
    assert valid is True
    assert err is None


# 20. Tamper detection verification
def test_20_tamper_detection():
    ledger = BlockchainLedger()
    original_report = "# Mission Report\n- `CIS-MGMT-01` (critical) — FAIL"
    _, rep_hash = ledger.record_report_integrity("REP-002", original_report, "Goal", {})

    # Simulate unauthorized modification (e.g. changing FAIL to PASS)
    tamper_result = ledger.simulate_tamper(original_report, target_rule="CIS-MGMT-01", fake_status="PASS")
    assert tamper_result["tamper_detected"] is True
    assert tamper_result["status"] == "TAMPER DETECTED"
    assert tamper_result["stored_hash"] != tamper_result["current_hash"]
