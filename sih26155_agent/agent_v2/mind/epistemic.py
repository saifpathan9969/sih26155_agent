"""
Mind — Epistemic State Engine
GAACA v2.0

Every piece of information known to the agent carries an explicit Epistemic status.
The agent distinguishes between what is verified, what is merely inferred,
what is assumed, what is unknown, and what is contradicted.
"""

from enum import Enum


class Epistemic(str, Enum):
    """
    Epistemic statuses ordered by epistemic authority.
    Rule: An action whose min_epistemic requirement exceeds the status of any belief
    it depends on is refused by the Decision layer and converted into an
    evidence-gathering action instead.
    """
    KNOWN = "KNOWN"                       # Directly observed, deterministic source (e.g. file content, parser)
    VERIFIED = "VERIFIED"                 # Confirmed by an independent mechanism (e.g. rule engine verdict)
    HUMAN_CONFIRMED = "HUMAN_CONFIRMED"   # An authorized operator signed off
    INFERRED = "INFERRED"                 # Derived by cognitive/probabilistic reasoning
    ASSUMED = "ASSUMED"                   # Hypothesized default; confidence decays each unverified cycle
    UNKNOWN = "UNKNOWN"                   # Explicitly identified information gap
    CONTRADICTED = "CONTRADICTED"         # Conflicting evidence detected in world model


EPISTEMIC_AUTHORITY_RANK = {
    Epistemic.HUMAN_CONFIRMED: 6,
    Epistemic.VERIFIED: 5,
    Epistemic.KNOWN: 4,
    Epistemic.INFERRED: 3,
    Epistemic.ASSUMED: 2,
    Epistemic.UNKNOWN: 1,
    Epistemic.CONTRADICTED: 0,
}


def has_sufficient_epistemic(current: Epistemic, required: Epistemic) -> bool:
    """Returns True if current epistemic authority meets or exceeds required authority."""
    return EPISTEMIC_AUTHORITY_RANK.get(current, 0) >= EPISTEMIC_AUTHORITY_RANK.get(required, 0)
