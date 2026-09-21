"""
Execution — Failure Taxonomy
GAACA v2.0

Categorizes failure modes so self-correction can alter strategy intelligently
rather than blindly retrying identical actions.
"""

from enum import Enum


class FailureClass(str, Enum):
    TRANSIENT = "TRANSIENT"                         # Network timeout or temporary glitch (max 2 retries allowed)
    PRECONDITION_FAILED = "PRECONDITION_FAILED"     # A required belief or entity was missing
    CAPABILITY_MISMATCH = "CAPABILITY_MISMATCH"     # Selected implementation unable to produce target evidence
    POLICY_BLOCKED = "POLICY_BLOCKED"               # Action refused by AutonomyTable or human gate
    CONTRADICTION = "CONTRADICTION"                 # Action generated conflicting evidence with existing beliefs
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"       # Hard cap reached
    UNSUPPORTED = "UNSUPPORTED"                     # Vendor or grammar unknown; requires human mapping
