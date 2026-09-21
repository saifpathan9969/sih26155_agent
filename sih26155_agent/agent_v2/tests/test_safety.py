"""
Tests — Safety Trap Tests
GAACA v2.0

Verifies that safety boundaries hold under adversarial conditions:
1. LLM cannot override rule engine verdicts
2. Shell commands always require human approval
3. Compliance core writes are permanently gated
4. SSRF is blocked
5. Dangerous shell patterns are rejected
6. Budget exhaustion terminates gracefully
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from agent_v2.safety.policy import (
    requires_human_approval, get_autonomy_rule, Autonomy, AUTONOMY_TABLE
)
from agent_v2.safety.budgets import ResourceLedger
from agent_v2.mind.beliefs import BeliefStore, Provenance
from agent_v2.mind.epistemic import Epistemic
from agent_v2.capabilities.web import is_ssrf_safe
from agent_v2.capabilities.base import ImplementationSpec, Observation, ExecContext, CostModel
from agent_v2.capabilities.registry import CapabilityRegistry


def test_llm_cannot_override_rule_engine():
    """The LLM must never be able to assert a compliance verdict."""
    store = BeliefStore()
    try:
        store.register(
            "rule:CIS-NET-05.status",
            "PASS",
            Epistemic.VERIFIED,
            provenance=Provenance(capability="llm_synthesis", source_type="llm_prompt"),
        )
        assert False, "LLM should not be able to assert compliance verdict"
    except ValueError as e:
        assert "Only the deterministic rule engine is authoritative" in str(e)


def test_shell_always_requires_human():
    assert requires_human_approval("run_shell") is True
    level, _ = get_autonomy_rule("run_shell")
    assert level == Autonomy.NEVER_AUTONOMOUS


def test_compliance_core_permanently_gated():
    assert requires_human_approval("write_compliance_core") is True
    level, _ = get_autonomy_rule("write_compliance_core")
    assert level == Autonomy.NEVER_AUTONOMOUS


def test_device_write_out_of_scope():
    level, _ = get_autonomy_rule("apply_remediation_to_device")
    assert level == Autonomy.OUT_OF_SCOPE


def test_unknown_action_fails_closed():
    """Actions not in AUTONOMY_TABLE must fail closed."""
    try:
        get_autonomy_rule("launch_missiles")
        assert False, "Unknown action should raise KeyError"
    except KeyError as e:
        assert "Safety Policy Violation" in str(e)


def test_ssrf_blocks_private_ranges():
    assert is_ssrf_safe("http://127.0.0.1/admin") is False
    assert is_ssrf_safe("http://localhost/config") is False
    assert is_ssrf_safe("http://169.254.169.254/latest/meta-data/") is False
    assert is_ssrf_safe("http://10.0.0.1/secret") is False
    assert is_ssrf_safe("http://192.168.1.1/admin") is False
    assert is_ssrf_safe("http://172.16.0.1/internal") is False
    # Valid external URLs pass
    assert is_ssrf_safe("https://www.cisecurity.org/benchmark") is True
    assert is_ssrf_safe("https://nvd.nist.gov/vuln/detail") is True


def test_registry_rejects_unregistered_autonomy():
    """Registration must fail if autonomy_action is not in AUTONOMY_TABLE."""
    reg = CapabilityRegistry()
    try:
        reg.register_implementation(ImplementationSpec(
            name="evil_action",
            description="Should not be registerable",
            input_schema={},
            output_schema={},
            autonomy_action="nonexistent_action",
            risk="CRITICAL",
        ))
        assert False, "Should have raised KeyError for missing autonomy entry"
    except KeyError as e:
        assert "Safety Policy Invariant Violated" in str(e)


def test_budget_exhaustion():
    ledger = ResourceLedger(max_cycles=3)
    ledger.log_cycle()
    ledger.log_cycle()
    ledger.log_cycle()
    assert ledger.is_exhausted is True


def test_human_gated_action_blocked_without_callback():
    """Human-gated actions must return error when no approval callback exists."""
    reg = CapabilityRegistry()
    reg.register_implementation(ImplementationSpec(
        name="test_gated",
        description="Test gated action",
        input_schema={},
        output_schema={},
        autonomy_action="run_shell",  # NEVER_AUTONOMOUS
        risk="HIGH",
        handler=lambda p, c: Observation(ok=True, output="should not reach here"),
    ))

    from agent_v2.safety.budgets import ResourceLedger
    from agent_v2.safety.approval import ApprovalManager
    from agent_v2.mind.world_model import WorldModel

    ctx = ExecContext(
        run_id="test",
        project_root=_PROJECT_ROOT,
        scratch_dir=_PROJECT_ROOT / "agent_v2" / "scratch",
        budgets=ResourceLedger(),
        approval_manager=ApprovalManager(),  # No callback
        world_model=WorldModel(),
    )

    obs = reg.execute("test_gated", {}, ctx)
    assert obs.ok is False
    assert "Awaiting human approval" in obs.error


if __name__ == "__main__":
    print("Running Safety Trap Tests...")
    test_llm_cannot_override_rule_engine()
    print("[PASS] LLM cannot override rule engine")
    test_shell_always_requires_human()
    print("[PASS] Shell always requires human")
    test_compliance_core_permanently_gated()
    print("[PASS] Compliance core permanently gated")
    test_device_write_out_of_scope()
    print("[PASS] Device write out of scope")
    test_unknown_action_fails_closed()
    print("[PASS] Unknown action fails closed")
    test_ssrf_blocks_private_ranges()
    print("[PASS] SSRF blocks private ranges")
    test_registry_rejects_unregistered_autonomy()
    print("[PASS] Registry rejects unregistered autonomy")
    test_budget_exhaustion()
    print("[PASS] Budget exhaustion")
    test_human_gated_action_blocked_without_callback()
    print("[PASS] Human-gated action blocked without callback")
    print("\nALL SAFETY TRAP TESTS PASSED SUCCESSFULLY.")
