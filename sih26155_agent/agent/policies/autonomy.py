"""
Autonomy policy — the enforced version of the boundary table from the
architecture document. This is the single source of truth for what the
agent may do on its own vs. what always stops for a human.

Nothing about compliance evaluation is a "judgment call" that could ever
move from AUTONOMOUS to something looser — that boundary is fixed by
design, not configuration.
"""

from enum import Enum


class Autonomy(str, Enum):
    AUTONOMOUS = "autonomous"
    AUTONOMOUS_ABOVE_THRESHOLD = "autonomous_above_threshold"
    REQUIRES_HUMAN = "requires_human"
    NEVER_AUTONOMOUS = "never_autonomous"
    OUT_OF_SCOPE = "out_of_scope"


# action_name -> (autonomy level, rationale)
AUTONOMY_TABLE = {
    "discover_configs": (Autonomy.AUTONOMOUS, "No ambiguity — deterministic file discovery"),
    "fingerprint_vendor": (Autonomy.AUTONOMOUS, "Reversible, low-stakes classification"),
    "parse_config": (Autonomy.AUTONOMOUS, "Deterministic grammar, no judgment involved"),
    "retrieve_candidate": (Autonomy.AUTONOMOUS, "Produces a candidate only, never asserted as fact"),
    "auto_normalize_field": (Autonomy.AUTONOMOUS_ABOVE_THRESHOLD, "Below threshold, always escalates to human mapping"),
    "map_unknown_syntax": (Autonomy.NEVER_AUTONOMOUS, "Core safety boundary — always requires human confirmation"),
    "evaluate_compliance": (Autonomy.AUTONOMOUS, "Purely computed from validated evidence — not a judgment call"),
    "persist_kb_entry": (Autonomy.REQUIRES_HUMAN, "Only after schema validation AND explicit human confirmation"),
    "select_remediation": (Autonomy.AUTONOMOUS, "Selected from a verified knowledge base, never generated freely"),
    "apply_remediation_to_device": (Autonomy.OUT_OF_SCOPE, "Not implemented — report-only by design"),
    "prioritize_findings": (Autonomy.AUTONOMOUS, "Ranking by severity, not a security determination"),
    "detect_recurring_pattern": (Autonomy.AUTONOMOUS, "Reflection over evidence, not a new fact"),
    "send_external_report": (Autonomy.REQUIRES_HUMAN, "Unless explicitly configured for scheduled auto-distribution"),
}


def autonomy_level(action: str) -> Autonomy:
    if action not in AUTONOMY_TABLE:
        raise KeyError(
            f"Unknown action '{action}' has no autonomy policy defined. "
            "Fail closed: add it to AUTONOMY_TABLE before the agent can perform it."
        )
    return AUTONOMY_TABLE[action][0]


def requires_human(action: str, confidence: float | None = None,
                    threshold: float = 0.75) -> bool:
    """The single gate the agent loop calls before doing anything."""
    level = autonomy_level(action)
    if level in (Autonomy.NEVER_AUTONOMOUS, Autonomy.REQUIRES_HUMAN, Autonomy.OUT_OF_SCOPE):
        return True
    if level is Autonomy.AUTONOMOUS_ABOVE_THRESHOLD:
        return confidence is None or confidence < threshold
    return False
