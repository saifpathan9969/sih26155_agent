"""
Mind — Verification & Contradiction Precedence Engine
GAACA v2.0

Invariant:
No conclusion is accepted on the strength of the reasoning that produced it.

Contradiction Precedence Rule:
If the deterministic rule engine evaluates PASS, but an external source claims the
configuration is unsafe, the agent's only permitted determination is:
"PASS against our rule set; an external source suggests our rule set may be incomplete;
that's a gap in the rules, not a verdict, and needs a human."
The LLM never emits a verdict or overrides the rule engine.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import yaml

from agent_v2.mind.epistemic import Epistemic
from agent_v2.mind.world_model import WorldModel


@dataclass
class VerificationResult:
    verified: bool
    epistemic_status: Epistemic
    method_used: str                          # "deterministic_rule_engine", "mechanical_yaml_parser", "consistency_check"
    justification: str
    requires_human_escalation: bool = False


class VerificationEngine:
    def __init__(self, world: WorldModel):
        self.world = world

    def verify_yaml_syntax(self, yaml_content: str) -> Tuple[bool, str]:
        """Mechanically verifies that proposed YAML can parse without errors."""
        try:
            parsed = yaml.safe_load(yaml_content)
            if not isinstance(parsed, (dict, list)):
                return False, "YAML root must be a dict or list."
            return True, "Valid YAML structure."
        except Exception as ex:
            return False, f"YAML Syntax Error: {str(ex)}"

    def resolve_compliance_contradiction(
        self,
        rule_engine_verdict: str,
        external_source_claim: str,
        rule_id: str,
    ) -> VerificationResult:
        """
        Enforces Contradiction Precedence:
        Deterministic rule engine has absolute authority on compliance verdict.
        External disagreements are treated as potential gaps in the benchmark rules,
        never as grounds for the LLM to issue a PASS/FAIL verdict.
        """
        if rule_engine_verdict == "PASS" and "unsafe" in external_source_claim.lower():
            return VerificationResult(
                verified=True,
                epistemic_status=Epistemic.VERIFIED,
                method_used="deterministic_rule_engine",
                justification=(
                    f"PASS against our verified CIS rule set for '{rule_id}'; "
                    f"an external source suggests our rule set may be incomplete; "
                    "that's a gap in the rules, not a verdict, and needs a human."
                ),
                requires_human_escalation=True,
            )

        return VerificationResult(
            verified=True,
            epistemic_status=Epistemic.VERIFIED,
            method_used="deterministic_rule_engine",
            justification=f"Rule {rule_id} verdict={rule_engine_verdict}",
            requires_human_escalation=False,
        )
