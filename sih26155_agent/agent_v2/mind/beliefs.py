"""
Mind — Beliefs Subsystem
GAACA v2.0

Promotes the proven EvidenceField concept (provenance, confidence, method)
to a system-wide invariant across all beliefs the agent maintains.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from agent_v2.mind.epistemic import Epistemic


@dataclass
class Provenance:
    """Detailed audit provenance for every belief."""
    capability: str
    file: Optional[str] = None
    line: Optional[int] = None
    raw_text: Optional[str] = None
    source_type: str = "internal"  # "file", "rule_engine", "web", "user", "untrusted_web"
    run_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "capability": self.capability,
            "file": self.file,
            "line": self.line,
            "raw_text": self.raw_text,
            "source_type": self.source_type,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Belief:
    id: str
    subject: str                  # e.g. "device:core-sw-01.ssh.version", "rule:CIS-AUTH-03.status"
    statement: Any                # The value or assertion, e.g. 2, "PASS", True
    epistemic: Epistemic
    confidence: float             # 0.0 - 1.0
    provenance: List[Provenance] = field(default_factory=list)
    supports: List[str] = field(default_factory=list)        # belief / hypothesis IDs
    contradicts: List[str] = field(default_factory=list)     # belief / hypothesis IDs
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subject": self.subject,
            "statement": self.statement,
            "epistemic": self.epistemic.value,
            "confidence": round(self.confidence, 4),
            "provenance": [p.to_dict() for p in self.provenance],
            "supports": self.supports,
            "contradicts": self.contradicts,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }


class BeliefStore:
    """
    Typed, queryable repository of the agent's beliefs.
    Enforces provenance invariants and contradiction detection.
    """
    def __init__(self):
        self._beliefs_by_id: Dict[str, Belief] = {}
        self._beliefs_by_subject: Dict[str, List[str]] = {}

    def register(self, subject: str, statement: Any, epistemic: Epistemic,
                 confidence: float = 1.0, provenance: Optional[Provenance] = None,
                 supports: Optional[List[str]] = None) -> Belief:
        """
        Creates or updates a belief under architectural constraints:
        - Inviolable rule: Any belief about a compliance verdict ('rule:*.status')
          MUST have provenance from the deterministic rule engine.
        """
        if subject.endswith(".status") and "rule:" in subject:
            if provenance and provenance.source_type != "rule_engine":
                raise ValueError(
                    f"Architectural Safety Violation: Compliance verdict for '{subject}' "
                    f"cannot be asserted by source '{provenance.source_type}'. "
                    "Only the deterministic rule engine is authoritative."
                )

        belief_id = f"b_{uuid.uuid4().hex[:8]}"
        prov_list = [provenance] if provenance else []

        contradicting_ids = []
        if subject in self._beliefs_by_subject:
            for existing_id in self._beliefs_by_subject[subject]:
                existing = self._beliefs_by_id[existing_id]
                if existing.statement != statement:
                    contradicting_ids.append(existing_id)
                    existing.contradicts.append(belief_id)
                    existing.epistemic = Epistemic.CONTRADICTED

        final_epistemic = Epistemic.CONTRADICTED if contradicting_ids else epistemic

        belief = Belief(
            id=belief_id,
            subject=subject,
            statement=statement,
            epistemic=final_epistemic,
            confidence=max(0.0, min(1.0, confidence)),
            provenance=prov_list,
            supports=supports or [],
            contradicts=contradicting_ids,
        )

        self._beliefs_by_id[belief_id] = belief
        if subject not in self._beliefs_by_subject:
            self._beliefs_by_subject[subject] = []
        self._beliefs_by_subject[subject].append(belief_id)

        return belief

    def get(self, belief_id: str) -> Optional[Belief]:
        return self._beliefs_by_id.get(belief_id)

    def get_by_subject(self, subject: str) -> List[Belief]:
        ids = self._beliefs_by_subject.get(subject, [])
        return [self._beliefs_by_id[i] for i in ids]

    def all(self) -> List[Belief]:
        return list(self._beliefs_by_id.values())

    def decay_assumptions(self, decay_factor: float = 0.85):
        for belief in self._beliefs_by_id.values():
            if belief.epistemic == Epistemic.ASSUMED:
                belief.confidence = max(0.05, round(belief.confidence * decay_factor, 4))
                belief.last_updated = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {b_id: b.to_dict() for b_id, b in self._beliefs_by_id.items()}
