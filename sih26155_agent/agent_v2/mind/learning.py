"""
Mind — Learning & Knowledge Pattern Extraction
GAACA v2.0

Extracts validated knowledge patterns from successful action sequences.
Each KnowledgePattern has:
- validation_method: How it was verified (deterministic, empirical, human_confirmed)
- applicability_conditions: When the pattern applies
- contradiction_counter: Patterns exceeding threshold are retired, never cited as evidence
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class ValidationMethod(str, Enum):
    DETERMINISTIC = "DETERMINISTIC"        # Verified by rule engine or parser
    EMPIRICAL = "EMPIRICAL"                # Validated by repeated successful use
    HUMAN_CONFIRMED = "HUMAN_CONFIRMED"    # Explicitly approved by operator
    UNVALIDATED = "UNVALIDATED"            # Informational only; cannot be cited as evidence


@dataclass
class KnowledgePattern:
    id: str
    pattern_type: str                      # "syntax_mapping", "remediation_template", "vendor_behavior", "workflow"
    description: str
    content: Dict[str, Any]                # The actual knowledge payload
    validation_method: ValidationMethod
    applicability_conditions: List[str]    # When this pattern is relevant
    source_run_ids: List[str]              # Which runs contributed to this pattern
    times_applied: int = 0
    times_succeeded: int = 0
    times_failed: int = 0
    contradiction_count: int = 0
    max_contradictions: int = 3            # Retirement threshold
    retired: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        if self.times_applied == 0:
            return 0.0
        return self.times_succeeded / self.times_applied

    @property
    def is_citable(self) -> bool:
        """Only validated patterns with sufficient success rate can be cited as evidence."""
        return (
            not self.retired
            and self.validation_method != ValidationMethod.UNVALIDATED
            and self.contradiction_count < self.max_contradictions
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "content": self.content,
            "validation_method": self.validation_method.value,
            "applicability_conditions": self.applicability_conditions,
            "times_applied": self.times_applied,
            "times_succeeded": self.times_succeeded,
            "times_failed": self.times_failed,
            "contradiction_count": self.contradiction_count,
            "retired": self.retired,
            "is_citable": self.is_citable,
            "success_rate": round(self.success_rate, 4),
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }


class LearningEngine:
    def __init__(self):
        self._patterns: Dict[str, KnowledgePattern] = {}

    def extract_pattern(
        self,
        pattern_type: str,
        description: str,
        content: Dict[str, Any],
        validation_method: ValidationMethod,
        applicability_conditions: List[str],
        source_run_id: str,
    ) -> KnowledgePattern:
        """Extracts a new knowledge pattern from a successful action sequence."""
        pattern = KnowledgePattern(
            id=f"kp_{uuid.uuid4().hex[:8]}",
            pattern_type=pattern_type,
            description=description,
            content=content,
            validation_method=validation_method,
            applicability_conditions=applicability_conditions,
            source_run_ids=[source_run_id],
        )
        self._patterns[pattern.id] = pattern
        return pattern

    def record_application(self, pattern_id: str, succeeded: bool):
        """Records whether applying a pattern succeeded or failed."""
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return

        pattern.times_applied += 1
        pattern.last_used = datetime.now(timezone.utc)

        if succeeded:
            pattern.times_succeeded += 1
        else:
            pattern.times_failed += 1

    def record_contradiction(self, pattern_id: str):
        """Increments the contradiction counter. Retires pattern at threshold."""
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return

        pattern.contradiction_count += 1
        if pattern.contradiction_count >= pattern.max_contradictions:
            pattern.retired = True

    def find_applicable_patterns(
        self,
        pattern_type: Optional[str] = None,
        context_keywords: Optional[List[str]] = None,
    ) -> List[KnowledgePattern]:
        """Finds non-retired patterns matching type and context."""
        results = []
        for p in self._patterns.values():
            if p.retired:
                continue
            if pattern_type and p.pattern_type != pattern_type:
                continue
            if context_keywords:
                conditions_text = " ".join(p.applicability_conditions).lower()
                if not any(kw.lower() in conditions_text for kw in context_keywords):
                    continue
            results.append(p)
        return sorted(results, key=lambda p: p.success_rate, reverse=True)

    def get_pattern(self, pattern_id: str) -> Optional[KnowledgePattern]:
        return self._patterns.get(pattern_id)

    def all_patterns(self) -> List[KnowledgePattern]:
        return list(self._patterns.values())

    def citable_patterns(self) -> List[KnowledgePattern]:
        return [p for p in self._patterns.values() if p.is_citable]

    def export_all(self) -> List[dict]:
        return [p.to_dict() for p in self._patterns.values()]
