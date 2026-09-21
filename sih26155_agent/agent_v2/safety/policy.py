"""
Safety & Governance — Autonomy Policy Engine
GAACA v2.0

The enforced boundary table. Surrounds the entire agent runtime.
No capability implementation or cognitive action can execute without passing
this policy check.
"""

from enum import Enum
from typing import Optional, Tuple


class Autonomy(str, Enum):
    AUTONOMOUS = "autonomous"                                   # Runs with no approval
    AUTONOMOUS_ABOVE_THRESHOLD = "autonomous_above_threshold"   # Runs if confidence >= threshold, else gates
    REQUIRES_HUMAN = "requires_human"                           # Always pauses for human sign-off
    NEVER_AUTONOMOUS = "never_autonomous"                       # Core safety boundary — permanent human gate
    OUT_OF_SCOPE = "out_of_scope"                               # Permanently prohibited


AUTONOMY_TABLE = {
    # -------------------------------------------------------------
    # 1. Existing Proven Boundaries (Preserved Verbatim)
    # -------------------------------------------------------------
    "discover_configs": (Autonomy.AUTONOMOUS, "Deterministic file discovery"),
    "fingerprint_vendor": (Autonomy.AUTONOMOUS, "Low-stakes classifier"),
    "parse_config": (Autonomy.AUTONOMOUS, "Deterministic grammar parser"),
    "evaluate_compliance": (Autonomy.AUTONOMOUS, "Pure deterministic calculation from evidence"),
    "cluster_unknown_syntax": (Autonomy.AUTONOMOUS, "TF-IDF reflection across evidence"),
    "select_remediation": (Autonomy.AUTONOMOUS, "Verified lookup in declarative rules"),
    "map_unknown_syntax": (Autonomy.NEVER_AUTONOMOUS, "Human must confirm every syntax mapping"),
    "apply_remediation_to_device": (Autonomy.OUT_OF_SCOPE, "Permanently out of scope — no live device writes"),

    # -------------------------------------------------------------
    # 2. Research & Web Capabilities
    # -------------------------------------------------------------
    "web_search": (Autonomy.AUTONOMOUS, "Read-only, no side effects"),
    "web_fetch": (Autonomy.AUTONOMOUS, "Read-only; fetched content is untrusted data"),
    "synthesize_research": (Autonomy.AUTONOMOUS, "Advisory cognitive synthesis"),

    # -------------------------------------------------------------
    # 3. Filesystem & Code Capabilities
    # -------------------------------------------------------------
    "read_file": (Autonomy.AUTONOMOUS, "Read-only, path-allowlisted"),
    "list_dir": (Autonomy.AUTONOMOUS, "Read-only, path-allowlisted"),
    "search_files": (Autonomy.AUTONOMOUS, "Read-only, path-allowlisted"),
    "inspect_project": (Autonomy.AUTONOMOUS, "Read-only environment discovery"),
    "write_scratch": (Autonomy.AUTONOMOUS, "Sandbox scratch paths only"),
    "write_file": (Autonomy.AUTONOMOUS_ABOVE_THRESHOLD, "Project paths; never compliance core"),
    "write_compliance_core": (Autonomy.NEVER_AUTONOMOUS, "cis_rules.yaml / schema / rule_engine.py — permanent gate"),
    "modify_code": (Autonomy.REQUIRES_HUMAN, "Source code modifications require human review"),
    "run_python": (Autonomy.AUTONOMOUS_ABOVE_THRESHOLD, "Sandboxed in scratch dir with timeout"),
    "run_tests": (Autonomy.AUTONOMOUS, "Sandboxed test execution"),
    "run_shell": (Autonomy.NEVER_AUTONOMOUS, "Strictly more dangerous than run_python; always confirm"),
    "git_status": (Autonomy.AUTONOMOUS, "Read-only repository state"),
    "git_diff": (Autonomy.AUTONOMOUS, "Read-only change comparison"),
    "git_commit": (Autonomy.REQUIRES_HUMAN, "Never auto-commit to version control"),

    # -------------------------------------------------------------
    # 4. Cognition, Learning & Communication
    # -------------------------------------------------------------
    "adopt_learned_pattern": (Autonomy.AUTONOMOUS_ABOVE_THRESHOLD, "Confidence >= 0.85; else gates"),
    "promote_to_human_confirmed": (Autonomy.NEVER_AUTONOMOUS, "Only a human can promote to HUMAN_CONFIRMED"),
    "generate_report": (Autonomy.AUTONOMOUS, "Reports are advisory outputs"),
    "converse": (Autonomy.AUTONOMOUS, "Conversational responses are always allowed"),
    "ask_human": (Autonomy.AUTONOMOUS, "Asking questions is always allowed"),
    "request_approval": (Autonomy.AUTONOMOUS, "Escalating to human gate is always allowed"),
    "create_task": (Autonomy.AUTONOMOUS, "Task lifecycle registration is allowed"),
    "list_tasks": (Autonomy.AUTONOMOUS, "Listing registered tasks is read-only"),
    "stop_task": (Autonomy.AUTONOMOUS, "Stopping a task is allowed"),
}


def get_autonomy_rule(action: str) -> Tuple[Autonomy, str]:
    if action not in AUTONOMY_TABLE:
        raise KeyError(
            f"Safety Policy Violation: Action '{action}' has no entry in AUTONOMY_TABLE. "
            "Fail closed: add explicit policy before execution."
        )
    return AUTONOMY_TABLE[action]


def requires_human_approval(action: str, confidence: Optional[float] = None,
                            threshold: float = 0.75) -> bool:
    """
    Evaluates whether an action requires human approval before proceeding.
    """
    level, _ = get_autonomy_rule(action)
    if level in (Autonomy.NEVER_AUTONOMOUS, Autonomy.REQUIRES_HUMAN, Autonomy.OUT_OF_SCOPE):
        return True
    if level is Autonomy.AUTONOMOUS_ABOVE_THRESHOLD:
        return confidence is None or confidence < threshold
    return False
