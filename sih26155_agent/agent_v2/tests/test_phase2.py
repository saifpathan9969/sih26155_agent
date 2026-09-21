"""
Tests — Phase 2 Verification Suite
GAACA v2.0

Verifies:
- Scientific problem solving (HypothesisEngine)
- Bayesian evidence tracking and status progression
- Diagnosis-first self-correction (SelfCorrectionEngine)
- Strategy-change recovery (RecoveryEngine) banning bare retries
- KnowledgePattern extraction, validation methods, and retirement upon contradictions
- Reasoning chains and belief revision
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "agent_v2"))

from agent_v2.mind.hypothesis import HypothesisEngine, ActionSketch
from agent_v2.mind.correction import SelfCorrectionEngine
from agent_v2.execution.recovery import RecoveryEngine, RecoveryAction
from agent_v2.mind.decision import DecisionEngine
from agent_v2.mind.learning import LearningEngine, ValidationMethod, KnowledgePattern
from agent_v2.mind.reasoning import ReasoningEngine, ReasoningType
from agent_v2.mind.beliefs import BeliefStore
from agent_v2.mind.epistemic import Epistemic


def test_hypothesis_engine_full_lifecycle():
    engine = HypothesisEngine()
    a1 = ActionSketch(objective="Check SSH Port 22", required_capability="SECURITY", expected_discrimination=0.8)
    a2 = ActionSketch(objective="Query Firewall Logs", required_capability="SECURITY", expected_discrimination=0.9, estimated_cost=2.0)
    
    h1 = engine.form_hypothesis("Firewall drops SSH packets", prior=0.4, actions=[a1, a2])
    h2 = engine.form_hypothesis("SSH daemon not running", prior=0.3)
    
    assert len(engine.open_hypotheses()) == 2
    best_action = engine.best_discriminating_action()
    assert best_action is not None
    assert best_action.objective == "Check SSH Port 22"  # 0.8 / 1.0 > 0.9 / 2.0
    
    # Add supporting evidence
    engine.add_evidence(h1.id, "belief_fw_drop_log", supports=True, weight=0.6)
    assert h1.posterior > 0.7
    assert h1.status == "OPEN"
    
    # Add further supporting evidence to reach SUPPORTED threshold (>= 0.85)
    engine.add_evidence(h1.id, "belief_wireshark_rst", supports=True, weight=0.6)
    assert h1.posterior >= 0.85
    assert h1.status == "SUPPORTED"
    
    # Add refuting evidence to h2 to reach REFUTED threshold (<= 0.15)
    engine.add_evidence(h2.id, "belief_systemctl_active", supports=False, weight=0.6)
    assert h2.posterior <= 0.15
    assert h2.status == "REFUTED"


def test_self_correction_diagnosis():
    correction = SelfCorrectionEngine()
    
    # Transient timeout failure
    rec1 = correction.diagnose_and_adapt("web_fetch", "HTTPConnectionPool: timeout error after 10s", "Fetch FortiGate docs")
    assert rec1.failure_class == "TRANSIENT"
    assert "timeout" in rec1.diagnosis.lower()
    
    # Policy boundary blocked
    rec2 = correction.diagnose_and_adapt("web_fetch", "SSRF blocked: IP 127.0.0.1 outside authorized boundary", "Read internal metadata")
    assert rec2.failure_class == "POLICY_BLOCKED"
    assert "safety boundary" in rec2.diagnosis.lower()
    
    # Unsupported vendor syntax
    rec3 = correction.diagnose_and_adapt("parse_config", "unknown vendor grammar detected: Juniper JunOS", "Parse device config")
    assert rec3.failure_class == "UNSUPPORTED"
    assert "grammar" in rec3.diagnosis.lower()


def test_recovery_bans_bare_retries():
    correction = SelfCorrectionEngine()
    decision = DecisionEngine()
    recovery = RecoveryEngine(correction, decision)
    
    # Non-transient failure must NOT suggest bare retry
    rec_action = recovery.recover(
        failed_action="read_file",
        error_message="FileNotFoundError: cis_rules_missing.yaml",
        objective="Read benchmark rules",
        current_capability="FILESYSTEM",
    )
    assert rec_action.recovery_type == "alternative_capability"
    assert rec_action.alternative_action == "WEB_RESEARCH"
    
    # Strategy was registered as failed in DecisionEngine
    assert decision.is_strategy_failed("Read benchmark rules", "read_file", {}) is True


def test_knowledge_pattern_extraction_and_retirement():
    learning = LearningEngine()
    
    pattern = learning.extract_pattern(
        pattern_type="syntax_mapping",
        description="Map set system login to standard user account grammar",
        content={"token": "set system login", "target": "aaa_user"},
        validation_method=ValidationMethod.DETERMINISTIC,
        applicability_conditions=["juniper_junos", "user_auth"],
        source_run_id="run_test_01",
    )
    
    assert pattern.is_citable is True
    assert pattern.times_applied == 0
    
    # Successful application
    learning.record_application(pattern.id, succeeded=True)
    assert pattern.times_applied == 1
    assert pattern.success_rate == 1.0
    
    # Accumulate contradictions up to threshold (3)
    learning.record_contradiction(pattern.id)
    assert pattern.contradiction_count == 1
    assert pattern.is_citable is True
    
    learning.record_contradiction(pattern.id)
    learning.record_contradiction(pattern.id)
    assert pattern.contradiction_count == 3
    assert pattern.retired is True
    assert pattern.is_citable is False  # Must never be cited as evidence once retired!


def test_deductive_and_abductive_reasoning():
    beliefs = BeliefStore()
    b1 = beliefs.register("device:fw1.vendor", "fortigate", Epistemic.KNOWN)
    b2 = beliefs.register("device:fw1.firmware", "v7.2.1", Epistemic.KNOWN)
    
    reasoning = ReasoningEngine(beliefs)
    
    # Deduce os_family from vendor and firmware
    step = reasoning.deduce(
        premise_ids=[b1.id, b2.id],
        conclusion_subject="device:fw1.os_family",
        conclusion_value="FortiOS",
        justification="FortiGate devices running v7.x use FortiOS",
    )
    assert step.type == ReasoningType.DEDUCTIVE
    assert step.conclusion_value == "FortiOS"
    assert step.confidence >= 0.8
    
    # Abductive explanation
    ab_step = reasoning.abduce(
        observation_subject="network:port_22_closed",
        hypothesis_value="firewall_drop_policy",
        supporting_belief_ids=[b1.id],
        justification="FortiGate drop policy often closes port 22 by default",
    )
    assert ab_step.type == ReasoningType.ABDUCTIVE
    assert ab_step.conclusion_value == "firewall_drop_policy"
    
    # Belief revision
    rev = reasoning.revise_belief(
        b1.id,
        new_epistemic=Epistemic.VERIFIED,
        new_confidence=0.99,
        reason="Verified against device banner",
    )
    assert rev is not None
    assert rev.new_epistemic == Epistemic.VERIFIED
    assert beliefs.get(b1.id).epistemic == Epistemic.VERIFIED


if __name__ == "__main__":
    print("Running Phase 2 Verification Suite...")
    test_hypothesis_engine_full_lifecycle()
    print("[PASS] Hypothesis engine full lifecycle passed")
    test_self_correction_diagnosis()
    print("[PASS] Self-correction diagnosis passed")
    test_recovery_bans_bare_retries()
    print("[PASS] Recovery bans bare retries & switches capability passed")
    test_knowledge_pattern_extraction_and_retirement()
    print("[PASS] KnowledgePattern validation and retirement passed")
    test_deductive_and_abductive_reasoning()
    print("[PASS] Deductive/Abductive reasoning engine passed")
    print("\nALL PHASE 2 TESTS PASSED SUCCESSFULLY.")
