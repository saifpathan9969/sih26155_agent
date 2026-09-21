"""
Memory — Procedural Memory
GAACA v2.0

Stores and retrieves verified KnowledgePatterns.
Acts as the interface between the LearningEngine and persistent storage.
Only citable patterns (validated, non-retired) can influence reasoning.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from agent_v2.mind.learning import KnowledgePattern, LearningEngine, ValidationMethod


class ProceduralMemory:
    """
    Procedural memory: stores verified workflows, syntax mappings,
    remediation templates, and vendor behaviors learned from experience.
    """

    def __init__(self, learning_engine: Optional[LearningEngine] = None):
        self.learning = learning_engine or LearningEngine()

    def store_pattern(
        self,
        pattern_type: str,
        description: str,
        content: Dict[str, Any],
        validation_method: ValidationMethod,
        applicability_conditions: List[str],
        source_run_id: str,
    ) -> KnowledgePattern:
        """Stores a new knowledge pattern through the learning engine."""
        return self.learning.extract_pattern(
            pattern_type=pattern_type,
            description=description,
            content=content,
            validation_method=validation_method,
            applicability_conditions=applicability_conditions,
            source_run_id=source_run_id,
        )

    def recall(self, pattern_type: Optional[str] = None,
               context_keywords: Optional[List[str]] = None) -> List[KnowledgePattern]:
        """Recalls applicable, non-retired patterns matching the query."""
        return self.learning.find_applicable_patterns(
            pattern_type=pattern_type,
            context_keywords=context_keywords,
        )

    def recall_citable(self) -> List[KnowledgePattern]:
        """Returns only patterns that can be cited as evidence."""
        return self.learning.citable_patterns()

    def record_use(self, pattern_id: str, succeeded: bool):
        """Records whether a pattern application succeeded or failed."""
        self.learning.record_application(pattern_id, succeeded)

    def record_contradiction(self, pattern_id: str):
        """Records a contradiction against a pattern (may retire it)."""
        self.learning.record_contradiction(pattern_id)

    def get(self, pattern_id: str) -> Optional[KnowledgePattern]:
        return self.learning.get_pattern(pattern_id)

    def all_patterns(self) -> List[KnowledgePattern]:
        return self.learning.all_patterns()

    def export_all(self) -> List[dict]:
        return self.learning.export_all()
