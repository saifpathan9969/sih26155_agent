"""
Memory — Semantic Memory
GAACA v2.0

Long-term fact base and domain models.
Stores structured domain knowledge:
- Vendor ontologies (Cisco IOS, Juniper, FortiOS, etc.)
- Security concepts and their relationships
- Validated facts that persist across runs
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class DomainConcept:
    """A domain concept in the semantic knowledge base."""
    id: str
    category: str            # "vendor", "protocol", "security_control", "cis_benchmark", "network_topology"
    name: str
    description: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    related_concepts: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "name": self.name,
            "description": self.description,
            "attributes": self.attributes,
            "related_concepts": self.related_concepts,
        }


@dataclass
class ValidatedFact:
    """A fact that has been verified and persists across runs."""
    id: str
    subject: str
    predicate: str
    value: Any
    source: str              # "rule_engine", "human_confirmed", "empirical"
    confidence: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subject": self.subject,
            "predicate": self.predicate,
            "value": self.value,
            "source": self.source,
            "confidence": self.confidence,
        }


class SemanticMemory:
    """Long-term structured knowledge base."""

    def __init__(self):
        self._concepts: Dict[str, DomainConcept] = {}
        self._facts: Dict[str, ValidatedFact] = {}
        self._next_fact_id: int = 1

        # Pre-load vendor ontology
        self._bootstrap_vendor_ontology()

    def _bootstrap_vendor_ontology(self):
        """Seeds the semantic memory with known vendor categories."""
        vendors = [
            ("vendor_cisco_ios", "vendor", "Cisco IOS", "Cisco IOS/IOS-XE network operating system"),
            ("vendor_juniper_junos", "vendor", "Juniper JunOS", "Juniper Networks JunOS operating system"),
            ("vendor_fortinet_fortios", "vendor", "Fortinet FortiOS", "Fortinet FortiGate operating system"),
            ("vendor_paloalto_panos", "vendor", "Palo Alto PAN-OS", "Palo Alto Networks PAN-OS"),
            ("vendor_arista_eos", "vendor", "Arista EOS", "Arista Networks EOS"),
            ("concept_cis_benchmark", "cis_benchmark", "CIS Benchmark", "Center for Internet Security configuration benchmark"),
            ("concept_ssh", "protocol", "SSH", "Secure Shell protocol for encrypted remote access"),
            ("concept_acl", "security_control", "ACL", "Access Control List for traffic filtering"),
            ("concept_aaa", "security_control", "AAA", "Authentication, Authorization, Accounting"),
        ]
        for cid, cat, name, desc in vendors:
            self._concepts[cid] = DomainConcept(id=cid, category=cat, name=name, description=desc)

    def add_concept(self, concept_id: str, category: str, name: str,
                    description: str, attributes: Optional[Dict] = None,
                    related: Optional[List[str]] = None) -> DomainConcept:
        concept = DomainConcept(
            id=concept_id, category=category, name=name,
            description=description,
            attributes=attributes or {},
            related_concepts=related or [],
        )
        self._concepts[concept_id] = concept
        return concept

    def get_concept(self, concept_id: str) -> Optional[DomainConcept]:
        return self._concepts.get(concept_id)

    def find_concepts(self, category: Optional[str] = None,
                      keyword: Optional[str] = None) -> List[DomainConcept]:
        results = list(self._concepts.values())
        if category:
            results = [c for c in results if c.category == category]
        if keyword:
            kw = keyword.lower()
            results = [c for c in results if kw in c.name.lower() or kw in c.description.lower()]
        return results

    def add_fact(self, subject: str, predicate: str, value: Any,
                 source: str, confidence: float = 1.0) -> ValidatedFact:
        fact_id = f"sf_{self._next_fact_id}"
        self._next_fact_id += 1
        fact = ValidatedFact(
            id=fact_id, subject=subject, predicate=predicate,
            value=value, source=source, confidence=confidence,
        )
        self._facts[fact_id] = fact
        return fact

    def get_facts_about(self, subject: str) -> List[ValidatedFact]:
        return [f for f in self._facts.values() if f.subject == subject]

    def all_facts(self) -> List[ValidatedFact]:
        return list(self._facts.values())

    def export_all(self) -> Dict[str, Any]:
        return {
            "concepts": {k: v.to_dict() for k, v in self._concepts.items()},
            "facts": {k: v.to_dict() for k, v in self._facts.items()},
        }
