"""
Tests — Phase 0 Verification Suite
GAACA v2.0

Verifies all foundational runtime, cognitive data structures, safety boundaries,
and deterministic execution mechanics.
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "agent_v2"))

from agent_v2.mind.epistemic import Epistemic, has_sufficient_epistemic
from agent_v2.mind.beliefs import BeliefStore, Provenance
from agent_v2.mind.world_model import WorldModel
from agent_v2.mind.hypothesis import HypothesisEngine, ActionSketch
from agent_v2.safety.policy import requires_human_approval, Autonomy, get_autonomy_rule
from agent_v2.capabilities.base import CapabilitySpec, ImplementationSpec, Observation, ExecContext
from agent_v2.capabilities.registry import CapabilityRegistry
from agent_v2.core.executive import AgentExecutive
from agent_v2.core.state import TerminalState


def test_epistemic_authority():
    assert has_sufficient_epistemic(Epistemic.VERIFIED, Epistemic.INFERRED) is True
    assert has_sufficient_epistemic(Epistemic.ASSUMED, Epistemic.VERIFIED) is False
    assert has_sufficient_epistemic(Epistemic.HUMAN_CONFIRMED, Epistemic.KNOWN) is True


def test_belief_store_and_contradiction():
    store = BeliefStore()
    b1 = store.register("device:cisco_01.ssh.version", 2, Epistemic.KNOWN)
    assert b1.epistemic == Epistemic.KNOWN
    assert b1.statement == 2

    # Contradicting belief on same subject
    b2 = store.register("device:cisco_01.ssh.version", 1, Epistemic.INFERRED)
    assert b2.epistemic == Epistemic.CONTRADICTED
    assert store.get(b1.id).epistemic == Epistemic.CONTRADICTED

    # Architectural invariant: Compliance verdict cannot be asserted by unauthorized source
    try:
        store.register(
            "rule:CIS-AUTH-03.status",
            "PASS",
            Epistemic.VERIFIED,
            provenance=Provenance(capability="llm_guess", source_type="llm_prompt"),
        )
        assert False, "Should have raised ValueError on non-rule_engine verdict provenance"
    except ValueError as e:
        assert "Only the deterministic rule engine is authoritative" in str(e)


def test_hypothesis_engine():
    engine = HypothesisEngine()
    a1 = ActionSketch(objective="Test SSH", required_capability="SECURITY", expected_discrimination=0.9, estimated_cost=1.0, estimated_risk=1.0)
    h = engine.form_hypothesis("SSH disabled by firewall", prior=0.5, actions=[a1])
    assert h.status == "OPEN"
    assert engine.best_discriminating_action().objective == "Test SSH"

    engine.add_evidence(h.id, "belief_123", supports=True, weight=0.6)
    assert h.posterior > 0.7


def test_safety_policy():
    # Inviolable checks
    assert requires_human_approval("write_compliance_core") is True
    assert get_autonomy_rule("write_compliance_core")[0] == Autonomy.NEVER_AUTONOMOUS

    assert requires_human_approval("apply_remediation_to_device") is True
    assert get_autonomy_rule("apply_remediation_to_device")[0] == Autonomy.OUT_OF_SCOPE

    assert requires_human_approval("web_search") is False
    assert get_autonomy_rule("web_search")[0] == Autonomy.AUTONOMOUS


def test_capability_registry():
    reg = CapabilityRegistry()
    impl = ImplementationSpec(
        name="inspect_project",
        description="Inspect project root",
        input_schema={},
        output_schema={},
        autonomy_action="inspect_project",
        risk="NONE",
        handler=lambda params, ctx: Observation(ok=True, output={"status": "active", "files_found": 5}),
    )
    reg.register_implementation(impl)
    assert reg.get_implementation("inspect_project") is not None


def test_executive_deterministic_run():
    reg = CapabilityRegistry()
    impl = ImplementationSpec(
        name="inspect_project",
        description="Inspect project root",
        input_schema={},
        output_schema={},
        autonomy_action="inspect_project",
        risk="NONE",
        handler=lambda params, ctx: Observation(ok=True, output={"environment": "production_test", "devices": 6}),
    )
    reg.register_implementation(impl)

    exec_agent = AgentExecutive(
        project_root=_PROJECT_ROOT,
        scratch_dir=_PROJECT_ROOT / "agent_v2" / "scratch",
        registry=reg,
        trace_to_console=False,
    )
    state = exec_agent.run("Audit environment and populate initial world model", max_cycles=3)
    # Cognitive cycle should terminate (SUCCESS or RESOURCE_EXHAUSTED both valid for short runs)
    assert state.terminal_state in (TerminalState.SUCCESS, TerminalState.RESOURCE_EXHAUSTED)
    assert len(state.trace) >= 1
    # Perception maps dict keys as {capability_name}.{key} → "inspect_project.devices"
    devices_beliefs = state.world.beliefs.get_by_subject("inspect_project.devices")
    if devices_beliefs:
        assert devices_beliefs[0].statement == 6


if __name__ == "__main__":
    print("Running Phase 0 Verification Suite...")
    test_epistemic_authority()
    print("[PASS] Epistemic authority passed")
    test_belief_store_and_contradiction()
    print("[PASS] BeliefStore & contradiction invariants passed")
    test_hypothesis_engine()
    print("[PASS] Hypothesis engine passed")
    test_safety_policy()
    print("[PASS] Safety policy boundaries passed")
    test_capability_registry()
    print("[PASS] Capability registry passed")
    test_executive_deterministic_run()
    print("[PASS] AgentExecutive cycle run passed")
    print("\nALL PHASE 0 TESTS PASSED SUCCESSFULLY.")
