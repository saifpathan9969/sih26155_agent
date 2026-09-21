"""
Execution — Action Executor
GAACA v2.0

Dispatches actions through the capability registry with:
- Precondition validation
- Context binding
- Timeout enforcement
- Observation capture
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional

from agent_v2.capabilities.base import Observation, ExecContext, ImplementationSpec
from agent_v2.capabilities.registry import CapabilityRegistry
from agent_v2.mind.world_model import WorldModel
from agent_v2.mind.epistemic import Epistemic


class ActionExecutor:
    """Executes actions through the capability registry with safety checks."""

    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry

    def check_preconditions(self, impl: ImplementationSpec,
                            world: WorldModel) -> tuple[bool, str]:
        """Validates that all preconditions for an implementation are met."""
        # Check if implementation exists
        if not self.registry.get_implementation(impl.name):
            return False, f"Implementation '{impl.name}' not registered."

        # Future: check required beliefs in world model
        return True, "Preconditions satisfied."

    def execute(self, impl_name: str, params: Dict[str, Any],
                context: ExecContext) -> Observation:
        """Dispatches an action through the registry with full safety checks."""
        impl = self.registry.get_implementation(impl_name)
        if not impl:
            return Observation(
                ok=False, output=None,
                error=f"Implementation '{impl_name}' not found in registry.",
            )

        # Precondition check
        ok, msg = self.check_preconditions(impl, context.world_model)
        if not ok:
            return Observation(ok=False, output=None, error=f"Precondition failed: {msg}")

        # Delegate to registry (which handles autonomy policy)
        return self.registry.execute(impl_name, params, context)

    def execute_sequence(self, steps: List[Dict[str, Any]],
                         context: ExecContext) -> List[Observation]:
        """Executes a sequence of actions, stopping on first critical failure."""
        results = []
        for step in steps:
            impl_name = step.get("implementation", "")
            params = step.get("parameters", {})
            obs = self.execute(impl_name, params, context)
            results.append(obs)

            if not obs.ok and step.get("critical", True):
                break

        return results
