"""
Mind — Reasoning Subsystem
GAACA v2.0

Causal inference, belief revision, and contradiction resolution.
Provides the agent with structured reasoning chains:
- Deductive: If A implies B, and A is verified, then B is known.
- Abductive: Observation O is best explained by hypothesis H.
- Analogical: Pattern P worked in context C1, may apply to C2.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum

from agent_v2.mind.epistemic import Epistemic
from agent_v2.mind.beliefs import BeliefStore, Belief


class ReasoningType(str, Enum):
    DEDUCTIVE = "DEDUCTIVE"
    ABDUCTIVE = "ABDUCTIVE"
    ANALOGICAL = "ANALOGICAL"
    CAUSAL = "CAUSAL"


@dataclass
class ReasoningStep:
    type: ReasoningType
    premise_ids: List[str]
    conclusion_subject: str
    conclusion_value: Any
    confidence: float
    justification: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "premise_ids": self.premise_ids,
            "conclusion_subject": self.conclusion_subject,
            "conclusion_value": self.conclusion_value,
            "confidence": round(self.confidence, 4),
            "justification": self.justification,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class BeliefRevision:
    belief_id: str
    old_epistemic: Epistemic
    new_epistemic: Epistemic
    old_confidence: float
    new_confidence: float
    reason: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "belief_id": self.belief_id,
            "old_epistemic": self.old_epistemic.value,
            "new_epistemic": self.new_epistemic.value,
            "old_confidence": self.old_confidence,
            "new_confidence": self.new_confidence,
            "reason": self.reason,
        }


class ReasoningEngine:
    def __init__(self, beliefs: BeliefStore):
        self.beliefs = beliefs
        self.reasoning_trace: List[ReasoningStep] = []
        self.revisions: List[BeliefRevision] = []

    def deduce(self, premise_ids: List[str], conclusion_subject: str,
               conclusion_value: Any, justification: str) -> ReasoningStep:
        """Deductive reasoning: if all premises are KNOWN/VERIFIED, conclusion is KNOWN."""
        premises = [self.beliefs.get(pid) for pid in premise_ids]
        valid_premises = [p for p in premises if p is not None]

        if not valid_premises:
            confidence = 0.0
        else:
            min_conf = min(p.confidence for p in valid_premises)
            all_verified = all(
                p.epistemic in (Epistemic.KNOWN, Epistemic.VERIFIED, Epistemic.HUMAN_CONFIRMED)
                for p in valid_premises
            )
            confidence = min_conf if all_verified else min_conf * 0.6

        step = ReasoningStep(
            type=ReasoningType.DEDUCTIVE,
            premise_ids=premise_ids,
            conclusion_subject=conclusion_subject,
            conclusion_value=conclusion_value,
            confidence=confidence,
            justification=justification,
        )
        self.reasoning_trace.append(step)
        return step

    def abduce(self, observation_subject: str, hypothesis_value: Any,
               supporting_belief_ids: List[str], justification: str) -> ReasoningStep:
        """Abductive reasoning: best explanation for an observation."""
        supports = [self.beliefs.get(sid) for sid in supporting_belief_ids]
        valid = [s for s in supports if s is not None]
        confidence = (sum(s.confidence for s in valid) / len(valid) * 0.7) if valid else 0.3

        step = ReasoningStep(
            type=ReasoningType.ABDUCTIVE,
            premise_ids=supporting_belief_ids,
            conclusion_subject=observation_subject,
            conclusion_value=hypothesis_value,
            confidence=confidence,
            justification=justification,
        )
        self.reasoning_trace.append(step)
        return step

    def revise_belief(self, belief_id: str, new_epistemic: Epistemic,
                      new_confidence: float, reason: str) -> Optional[BeliefRevision]:
        """Revises a belief's epistemic status and confidence based on new evidence."""
        belief = self.beliefs.get(belief_id)
        if not belief:
            return None

        revision = BeliefRevision(
            belief_id=belief_id,
            old_epistemic=belief.epistemic,
            new_epistemic=new_epistemic,
            old_confidence=belief.confidence,
            new_confidence=new_confidence,
            reason=reason,
        )

        belief.epistemic = new_epistemic
        belief.confidence = max(0.0, min(1.0, new_confidence))
        belief.last_updated = datetime.now(timezone.utc)

        self.revisions.append(revision)
        return revision

    def resolve_contradiction(self, subject: str) -> Optional[str]:
        """
        Attempts to resolve contradictions on a subject by promoting the
        highest-confidence belief and demoting others.
        Returns the winning belief ID or None.
        """
        beliefs = self.beliefs.get_by_subject(subject)
        contradicted = [b for b in beliefs if b.epistemic == Epistemic.CONTRADICTED]

        if len(contradicted) < 2:
            return None

        def score(b: Belief) -> float:
            base = b.confidence
            if any(p.source_type == "rule_engine" for p in b.provenance):
                base += 0.5
            if any(p.source_type in ("file", "internal") for p in b.provenance):
                base += 0.2
            return base

        ranked = sorted(contradicted, key=score, reverse=True)
        winner = ranked[0]

        self.revise_belief(winner.id, Epistemic.KNOWN, winner.confidence,
                           f"Promoted as winner in contradiction resolution for '{subject}'")

        for loser in ranked[1:]:
            self.revise_belief(loser.id, Epistemic.CONTRADICTED, loser.confidence * 0.5,
                               f"Demoted in contradiction resolution for '{subject}'")

        return winner.id
