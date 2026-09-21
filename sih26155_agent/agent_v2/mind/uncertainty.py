"""
Mind — Uncertainty & Confidence Calibration
GAACA v2.0

Provides epistemic bounds, confidence scoring, and calibration utilities.
Prevents the agent from over-committing to low-evidence conclusions.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from agent_v2.mind.epistemic import Epistemic
from agent_v2.mind.beliefs import BeliefStore, Belief


@dataclass
class ConfidenceAssessment:
    subject: str
    aggregated_confidence: float
    belief_count: int
    highest_epistemic: Epistemic
    assessment: str       # "HIGH_CONFIDENCE", "MODERATE", "LOW_CONFIDENCE", "UNCERTAIN", "CONTRADICTED"

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "aggregated_confidence": round(self.aggregated_confidence, 4),
            "belief_count": self.belief_count,
            "highest_epistemic": self.highest_epistemic.value,
            "assessment": self.assessment,
        }


EPISTEMIC_RANK = {
    Epistemic.HUMAN_CONFIRMED: 6,
    Epistemic.VERIFIED: 5,
    Epistemic.KNOWN: 4,
    Epistemic.INFERRED: 3,
    Epistemic.ASSUMED: 2,
    Epistemic.UNKNOWN: 1,
    Epistemic.CONTRADICTED: 0,
}


class UncertaintyEngine:
    def __init__(self, beliefs: BeliefStore):
        self.beliefs = beliefs

    def assess_confidence(self, subject: str) -> ConfidenceAssessment:
        """Aggregates confidence across all beliefs on a given subject."""
        beliefs = self.beliefs.get_by_subject(subject)

        if not beliefs:
            return ConfidenceAssessment(
                subject=subject,
                aggregated_confidence=0.0,
                belief_count=0,
                highest_epistemic=Epistemic.UNKNOWN,
                assessment="UNCERTAIN",
            )

        contradicted = any(b.epistemic == Epistemic.CONTRADICTED for b in beliefs)
        if contradicted:
            return ConfidenceAssessment(
                subject=subject,
                aggregated_confidence=0.0,
                belief_count=len(beliefs),
                highest_epistemic=Epistemic.CONTRADICTED,
                assessment="CONTRADICTED",
            )

        highest = max(beliefs, key=lambda b: EPISTEMIC_RANK.get(b.epistemic, 0))
        avg_conf = sum(b.confidence for b in beliefs) / len(beliefs)

        if avg_conf >= 0.85 and highest.epistemic in (Epistemic.VERIFIED, Epistemic.HUMAN_CONFIRMED):
            assessment = "HIGH_CONFIDENCE"
        elif avg_conf >= 0.6:
            assessment = "MODERATE"
        elif avg_conf >= 0.3:
            assessment = "LOW_CONFIDENCE"
        else:
            assessment = "UNCERTAIN"

        return ConfidenceAssessment(
            subject=subject,
            aggregated_confidence=round(avg_conf, 4),
            belief_count=len(beliefs),
            highest_epistemic=highest.epistemic,
            assessment=assessment,
        )

    def should_seek_more_evidence(self, subject: str, threshold: float = 0.7) -> Tuple[bool, str]:
        """Determines if the agent should invest more resources to gain certainty."""
        assessment = self.assess_confidence(subject)

        if assessment.assessment == "CONTRADICTED":
            return True, f"Subject '{subject}' has contradicted beliefs; resolution required."
        if assessment.aggregated_confidence < threshold:
            return True, f"Confidence {assessment.aggregated_confidence:.2f} below threshold {threshold}."
        return False, f"Confidence sufficient at {assessment.aggregated_confidence:.2f}."

    def epistemic_bounds(self, subject: str) -> Dict[str, Any]:
        """Returns the epistemic floor and ceiling for a subject."""
        beliefs = self.beliefs.get_by_subject(subject)
        if not beliefs:
            return {"floor": "UNKNOWN", "ceiling": "UNKNOWN", "spread": 0.0}

        ranks = [EPISTEMIC_RANK.get(b.epistemic, 0) for b in beliefs]
        confs = [b.confidence for b in beliefs]

        floor_rank = min(ranks)
        ceiling_rank = max(ranks)

        # Reverse lookup
        rank_to_epistemic = {v: k for k, v in EPISTEMIC_RANK.items()}

        return {
            "floor": rank_to_epistemic.get(floor_rank, Epistemic.UNKNOWN).value,
            "ceiling": rank_to_epistemic.get(ceiling_rank, Epistemic.UNKNOWN).value,
            "confidence_range": (min(confs), max(confs)),
            "spread": max(confs) - min(confs),
        }
