"""
Execution — Strategy-Change Recovery
GAACA v2.0

When a failure occurs, recovery selects an alternative strategy
rather than retrying the same action. Integrates with:
- SelfCorrectionEngine (diagnosis)
- DecisionEngine (failed strategy exclusion)
- Planner (plan revision)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from agent_v2.mind.correction import SelfCorrectionEngine
from agent_v2.mind.decision import DecisionEngine
from agent_v2.core.state import FailureRecord


@dataclass
class RecoveryAction:
    """Describes the recovery strategy chosen after a failure."""
    original_action: str
    failure_class: str
    diagnosis: str
    recovery_type: str          # "alternative_capability", "parameter_change", "human_escalation", "abandon"
    alternative_action: Optional[str] = None
    alternative_params: Optional[Dict[str, Any]] = None
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "original_action": self.original_action,
            "failure_class": self.failure_class,
            "diagnosis": self.diagnosis,
            "recovery_type": self.recovery_type,
            "alternative_action": self.alternative_action,
            "alternative_params": self.alternative_params,
            "rationale": self.rationale,
        }


class RecoveryEngine:
    def __init__(self, correction: SelfCorrectionEngine, decision: DecisionEngine):
        self.correction = correction
        self.decision = decision
        self.recovery_history: List[RecoveryAction] = []

    def recover(
        self,
        failed_action: str,
        error_message: str,
        objective: str,
        current_capability: str,
    ) -> RecoveryAction:
        """
        Diagnoses a failure and selects a recovery strategy.
        Registers the failed strategy in the decision engine to prevent bare retries.
        """
        # 1. Diagnose
        failure_rec = self.correction.diagnose_and_adapt(
            failed_action=failed_action,
            error_message=error_message,
            current_objective=objective,
        )

        # 2. Register failed strategy (ban bare retries)
        self.decision.record_failed_strategy(objective, failed_action, {})

        # 3. Determine recovery type
        f_class = failure_rec.failure_class

        if f_class == "TRANSIENT":
            recovery = RecoveryAction(
                original_action=failed_action,
                failure_class=f_class,
                diagnosis=failure_rec.diagnosis,
                recovery_type="parameter_change",
                alternative_action=failed_action,
                alternative_params={"retry_with_backoff": True},
                rationale="Transient failure; one retry with backoff permitted.",
            )
        elif f_class == "POLICY_BLOCKED":
            recovery = RecoveryAction(
                original_action=failed_action,
                failure_class=f_class,
                diagnosis=failure_rec.diagnosis,
                recovery_type="human_escalation",
                rationale="Action blocked by safety policy; escalating to human.",
            )
        elif f_class == "UNSUPPORTED":
            alt_cap = self.correction.suggest_alternative_capability(current_capability, f_class)
            recovery = RecoveryAction(
                original_action=failed_action,
                failure_class=f_class,
                diagnosis=failure_rec.diagnosis,
                recovery_type="alternative_capability",
                alternative_action=alt_cap,
                rationale=f"Unsupported operation; shifting to capability '{alt_cap}'.",
            )
        else:
            alt_cap = self.correction.suggest_alternative_capability(current_capability, f_class)
            recovery = RecoveryAction(
                original_action=failed_action,
                failure_class=f_class,
                diagnosis=failure_rec.diagnosis,
                recovery_type="alternative_capability",
                alternative_action=alt_cap,
                rationale=f"Capability mismatch; switching to '{alt_cap}'.",
            )

        self.recovery_history.append(recovery)
        return recovery
