"""
Mind — Hypothesis Engine
GAACA v2.0

Scientific Problem Solving:
For diagnostic goals or unexpected observations, the agent enumerates competing
hypotheses (H1, H2, ...), tracks priors/posteriors, and scores candidate
actions by expected information gain: (OPEN hypotheses settled) / (cost * risk).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional
import uuid


HypothesisStatus = Literal["OPEN", "SUPPORTED", "REFUTED", "INCONCLUSIVE"]


@dataclass
class ActionSketch:
    objective: str
    required_capability: str
    expected_discrimination: float  # 0.0 - 1.0 (how well it separates hypotheses)
    estimated_cost: float = 1.0     # resource units
    estimated_risk: float = 1.0     # 1.0 (NONE) to 5.0 (CRITICAL)

    @property
    def score(self) -> float:
        """Expected information gain / (cost * risk)"""
        denom = max(0.1, self.estimated_cost * self.estimated_risk)
        return round(self.expected_discrimination / denom, 4)

    def to_dict(self) -> dict:
        return {
            "objective": self.objective,
            "required_capability": self.required_capability,
            "expected_discrimination": self.expected_discrimination,
            "score": self.score,
        }


@dataclass
class Hypothesis:
    id: str
    statement: str
    prior: float = 0.5
    posterior: float = 0.5
    supporting: List[str] = field(default_factory=list)  # belief IDs
    refuting: List[str] = field(default_factory=list)    # belief IDs
    status: HypothesisStatus = "OPEN"
    discriminating_actions: List[ActionSketch] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "statement": self.statement,
            "prior": round(self.prior, 4),
            "posterior": round(self.posterior, 4),
            "supporting": self.supporting,
            "refuting": self.refuting,
            "status": self.status,
            "discriminating_actions": [a.to_dict() for a in self.discriminating_actions],
        }


class HypothesisEngine:
    def __init__(self):
        self.hypotheses: Dict[str, Hypothesis] = {}

    def form_hypothesis(self, statement: str, prior: float = 0.5,
                        actions: Optional[List[ActionSketch]] = None) -> Hypothesis:
        h_id = f"h_{uuid.uuid4().hex[:6]}"
        h = Hypothesis(
            id=h_id,
            statement=statement,
            prior=prior,
            posterior=prior,
            status="OPEN",
            discriminating_actions=actions or [],
        )
        self.hypotheses[h_id] = h
        return h

    def add_evidence(self, h_id: str, belief_id: str, supports: bool, weight: float = 0.3):
        h = self.hypotheses.get(h_id)
        if not h:
            return
        if supports:
            h.supporting.append(belief_id)
            h.posterior = min(0.99, round(h.posterior + weight * (1.0 - h.posterior), 4))
            if h.posterior >= 0.85:
                h.status = "SUPPORTED"
        else:
            h.refuting.append(belief_id)
            h.posterior = max(0.01, round(h.posterior - weight * h.posterior, 4))
            if h.posterior <= 0.15:
                h.status = "REFUTED"

    def open_hypotheses(self) -> List[Hypothesis]:
        return [h for h in self.hypotheses.values() if h.status == "OPEN"]

    def best_discriminating_action(self) -> Optional[ActionSketch]:
        candidates: List[ActionSketch] = []
        for h in self.open_hypotheses():
            candidates.extend(h.discriminating_actions)
        if not candidates:
            return None
        return max(candidates, key=lambda a: a.score)

    def to_dict(self) -> dict:
        return {h_id: h.to_dict() for h_id, h in self.hypotheses.items()}
