"""
Mind — World Model Subsystem
GAACA v2.0

Maintains the agent's internal, evolving representation of the environment:
entities, relationships, properties, states, evidence, and open questions.
The world model is typed and queryable in Python, not a static prose block.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agent_v2.mind.epistemic import Epistemic
from agent_v2.mind.beliefs import BeliefStore, Belief, Provenance


@dataclass
class Entity:
    id: str
    type: str                     # "device", "file", "rule", "vendor", "service", "document"
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "attributes": self.attributes,
        }


@dataclass
class Relation:
    subject: str                  # entity_id or subject
    predicate: str                # "has_config", "evaluated_by", "depends_on", "targets_vendor"
    object: str                   # entity_id or value
    epistemic: Epistemic = Epistemic.KNOWN

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "epistemic": self.epistemic.value,
        }


@dataclass
class Contradiction:
    subject: str
    belief_ids: List[str]
    description: str
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "belief_ids": self.belief_ids,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
        }


class WorldModel:
    def __init__(self, beliefs: Optional[BeliefStore] = None):
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        self.beliefs: BeliefStore = beliefs or BeliefStore()
        self.open_questions: List[str] = []
        self.contradictions: List[Contradiction] = []

    def register_entity(self, entity_id: str, type: str, name: str,
                        attributes: Optional[Dict[str, Any]] = None) -> Entity:
        entity = Entity(id=entity_id, type=type, name=name, attributes=attributes or {})
        self.entities[entity_id] = entity
        return entity

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)

    def add_relation(self, subject: str, predicate: str, object_: str,
                     epistemic: Epistemic = Epistemic.KNOWN) -> Relation:
        rel = Relation(subject=subject, predicate=predicate, object=object_, epistemic=epistemic)
        self.relations.append(rel)
        return rel

    def assert_fact(self, subject: str, value: Any, epistemic: Epistemic,
                    confidence: float = 1.0, provenance: Optional[Provenance] = None) -> Belief:
        """Updates belief store and checks for world model contradictions."""
        belief = self.beliefs.register(
            subject=subject,
            statement=value,
            epistemic=epistemic,
            confidence=confidence,
            provenance=provenance,
        )
        if belief.epistemic == Epistemic.CONTRADICTED:
            self.contradictions.append(Contradiction(
                subject=subject,
                belief_ids=[belief.id] + belief.contradicts,
                description=f"Conflicting statements detected for '{subject}'",
            ))
            if subject not in self.open_questions:
                self.open_questions.append(subject)
        elif subject in self.open_questions:
            self.open_questions.remove(subject)

        return belief

    def add_open_question(self, question: str):
        if question not in self.open_questions:
            self.open_questions.append(question)

    def resolve_open_question(self, question: str):
        if question in self.open_questions:
            self.open_questions.remove(question)

    def get_state_summary(self) -> str:
        lines = []
        lines.append(f"Entities: {len(self.entities)}")
        for e in list(self.entities.values())[:10]:
            lines.append(f"  - [{e.type.upper()}] {e.name} (id={e.id})")
        
        lines.append(f"Beliefs: {len(self.beliefs.all())}")
        for b in self.beliefs.all()[:15]:
            lines.append(f"  - {b.subject} = {b.statement} [{b.epistemic.value}, conf={b.confidence}]")

        if self.contradictions:
            lines.append(f"CONTRADICTIONS ({len(self.contradictions)}):")
            for c in self.contradictions:
                lines.append(f"  ! {c.subject}: {c.description}")

        if self.open_questions:
            lines.append(f"OPEN QUESTIONS ({len(self.open_questions)}):")
            for q in self.open_questions[:5]:
                lines.append(f"  ? {q}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "entities": {k: v.to_dict() for k, v in self.entities.items()},
            "relations": [r.to_dict() for r in self.relations],
            "beliefs": self.beliefs.to_dict(),
            "open_questions": self.open_questions,
            "contradictions": [c.to_dict() for c in self.contradictions],
        }
