"""
Tests — Phase 4 Security Domain Integration Verification Suite
GAACA v2.0

Verifies:
- Wrapping of v1 security tools as GAACA capabilities
- Deterministic CIS compliance evaluation (100% deterministic, no LLM verdict)
- Configuration discovery and fingerprinting
- Parsing into normalized baseline schema
- Remediation lookup
- Composite run_mission execution
- Architectural Invariance: LLM cannot assert compliance verdict
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "agent_v2"))

from agent_v2.capabilities.base import ExecContext
from agent_v2.capabilities.registry import CapabilityRegistry
from agent_v2.capabilities.security import register_security_capabilities
from agent_v2.mind.world_model import WorldModel
from agent_v2.mind.epistemic import Epistemic
from agent_v2.mind.beliefs import BeliefStore, Provenance
from agent_v2.safety.budgets import ResourceLedger
from agent_v2.safety.approval import ApprovalManager


def _build_test_context() -> ExecContext:
    scratch_dir = _PROJECT_ROOT / "agent_v2" / "scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return ExecContext(
        run_id="test_phase4_run",
        project_root=_PROJECT_ROOT,
        scratch_dir=scratch_dir,
        budgets=ResourceLedger(max_cycles=10),
        approval_manager=ApprovalManager(),
        world_model=WorldModel(),
    )


def test_discover_configs_capability():
    reg = CapabilityRegistry()
    register_security_capabilities(reg)
    ctx = _build_test_context()

    obs = reg.execute("discover_configs", {"source": str(_PROJECT_ROOT)}, ctx)
    assert obs.ok is True
    assert "configs_found" in obs.output
    assert isinstance(obs.output["devices"], list)


def test_parse_config_capability():
    reg = CapabilityRegistry()
    register_security_capabilities(reg)
    ctx = _build_test_context()

    sample_cisco = """
    hostname Core-Switch-01
    version 15.2
    enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
    ip ssh version 2
    no service password-encryption
    """
    obs = reg.execute("parse_config", {"content": sample_cisco, "vendor": "cisco_ios"}, ctx)
    assert obs.ok is True
    baseline = obs.output
    assert isinstance(baseline, dict)
    assert baseline.get("hostname") == "Core-Switch-01" or "Core-Switch-01" in str(baseline)


def test_evaluate_compliance_capability():
    reg = CapabilityRegistry()
    register_security_capabilities(reg)
    ctx = _build_test_context()

    sample_baseline = {
        "hostname": "Core-Switch-01",
        "ssh": {"version": 2, "timeout": 60},
        "telnet": {"enabled": False},
        "snmp": {"v3_only": True},
        "aaa": {"enabled": True},
        "logging": {"buffered": True},
        "ntp": {"configured": True},
    }

    obs = reg.execute("evaluate_compliance", {
        "baseline": sample_baseline,
        "vendor": "cisco_ios",
        "rules_path": str(_PROJECT_ROOT / "cis_rules.yaml"),
    }, ctx)

    assert obs.ok is True
    summary = obs.output.get("summary", {})
    assert summary.get("total", 0) > 0
    assert summary.get("pass", 0) > 0


def test_select_remediation_capability():
    reg = CapabilityRegistry()
    register_security_capabilities(reg)
    ctx = _build_test_context()

    obs = reg.execute("select_remediation", {
        "rule_id": "CIS-SSH-01",
        "vendor": "cisco_ios",
    }, ctx)

    assert obs.ok is True
    remediation = obs.output
    assert remediation is not None


def test_deterministic_verdict_invariant():
    """Confirms that LLM source is permanently forbidden from asserting compliance verdicts in BeliefStore."""
    store = BeliefStore()
    
    # 1. Deterministic source succeeds
    det_belief = store.register(
        "rule:CIS-AUTH-01.status",
        "PASS",
        Epistemic.VERIFIED,
        provenance=Provenance(capability="rule_engine", source_type="rule_engine"),
    )
    assert det_belief.statement == "PASS"
    assert det_belief.epistemic == Epistemic.VERIFIED

    # 2. LLM or untrusted source raises ValueError
    try:
        store.register(
            "rule:CIS-AUTH-02.status",
            "PASS",
            Epistemic.VERIFIED,
            provenance=Provenance(capability="llm_agent", source_type="llm_generation"),
        )
        assert False, "Should have rejected non-deterministic verdict assertion"
    except ValueError as ex:
        assert "Only the deterministic rule engine is authoritative" in str(ex)


def test_run_mission_composite_capability():
    reg = CapabilityRegistry()
    register_security_capabilities(reg)
    ctx = _build_test_context()

    obs = reg.execute("run_mission", {
        "goal": "Audit project devices for CIS compliance",
        "source": str(_PROJECT_ROOT),
    }, ctx)

    assert obs.ok is True
    assert "status" in obs.output


if __name__ == "__main__":
    print("Running Phase 4 Security Domain Verification Suite...")
    test_discover_configs_capability()
    print("[PASS] discover_configs capability passed")
    test_parse_config_capability()
    print("[PASS] parse_config capability passed")
    test_evaluate_compliance_capability()
    print("[PASS] evaluate_compliance capability passed")
    test_select_remediation_capability()
    print("[PASS] select_remediation capability passed")
    test_deterministic_verdict_invariant()
    print("[PASS] Deterministic verdict invariant passed")
    test_run_mission_composite_capability()
    print("[PASS] run_mission composite capability passed")
    print("\nALL PHASE 4 SECURITY DOMAIN TESTS PASSED SUCCESSFULLY.")
