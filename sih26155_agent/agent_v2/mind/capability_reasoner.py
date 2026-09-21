"""
Mind — Capability Reasoner & Synthesis Layer
GAACA v2.0

The mind does not think "I have 15 tools."
It reasons: "What operation is necessary to advance this objective?"
Translates semantic intents into required capabilities and preferred implementation options.
"""

from typing import List, Tuple
from agent_v2.capabilities.registry import CapabilityRegistry
from agent_v2.capabilities.base import ImplementationSpec


class CapabilityReasoner:
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry

    def reason_required_operations(self, objective: str) -> List[str]:
        """
        Determines the sequence of semantic operations needed for an objective.
        """
        obj_lower = objective.lower()
        operations = []

        if "discover" in obj_lower or "find" in obj_lower:
            operations.append("FILESYSTEM")
        if "research" in obj_lower or "search" in obj_lower or "online" in obj_lower:
            operations.append("WEB_RESEARCH")
        if "audit" in obj_lower or "compliance" in obj_lower or "baseline" in obj_lower:
            operations.append("SECURITY")
        if "code" in obj_lower or "python" in obj_lower or "test" in obj_lower:
            operations.append("CODE")
        if "report" in obj_lower or "document" in obj_lower:
            operations.append("DOCUMENTS")

        if not operations:
            operations.append("ENVIRONMENT")

        return operations

    def select_candidate_implementations(self, capability_name: str) -> List[ImplementationSpec]:
        """Resolves semantic capability to candidate implementations."""
        return self.registry.resolve_implementations_for_capability(capability_name)
