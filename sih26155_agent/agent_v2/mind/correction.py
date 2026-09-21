"""
Mind — Strategic Self-Correction Subsystem
GAACA v2.0

Diagnosis-first recovery:
When an action fails or returns an unexpected observation:
1. Classifies failure mode (transient, precondition, capability_mismatch, etc.)
2. Diagnoses root cause (why expectation failed)
3. Modifies strategy (switches capability, shifts abstraction, or asks human)
4. Registers failed strategy in DecisionEngine so it is permanently excluded from bare retries.
"""

from typing import Dict, List, Optional
from agent_v2.execution.failures import FailureClass
from agent_v2.core.state import FailureRecord


class SelfCorrectionEngine:
    def diagnose_and_adapt(
        self,
        failed_action: str,
        error_message: str,
        current_objective: str,
    ) -> FailureRecord:
        error_lower = error_message.lower()

        # 1. Classification
        if "timeout" in error_lower or "connection reset" in error_lower:
            f_class = FailureClass.TRANSIENT
            diag = "Network glitch or timeout encountered; transient retry permitted."
        elif "unknown vendor" in error_lower or "unrecognized syntax" in error_lower:
            f_class = FailureClass.UNSUPPORTED
            diag = "Configuration syntax not in grammar; requires reflection clustering and human mapping."
        elif "outside authorized" in error_lower or "ssrf" in error_lower or "blocked" in error_lower:
            f_class = FailureClass.POLICY_BLOCKED
            diag = "Operation violated safety boundary; rerouting via permissible capabilities."
        else:
            f_class = FailureClass.CAPABILITY_MISMATCH
            diag = f"Implementation '{failed_action}' failed to advance objective '{current_objective}'."

        return FailureRecord(
            cycle=0,
            action=failed_action,
            error=error_message,
            failure_class=f_class.value,
            diagnosis=diag,
        )

    def suggest_alternative_capability(self, current_capability: str, failure_class: str) -> str:
        """Determines the next best capability shift upon failure."""
        if failure_class == FailureClass.UNSUPPORTED.value:
            return "SECURITY"  # triggers reflection/unknown syntax handling
        if current_capability == "FILESYSTEM":
            return "WEB_RESEARCH"
        if current_capability == "WEB_RESEARCH":
            return "COMMUNICATION"  # ask human when web is paywalled
        return "ENVIRONMENT"
