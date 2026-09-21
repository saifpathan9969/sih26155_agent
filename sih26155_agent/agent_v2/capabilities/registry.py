"""
Capabilities — Capability & Implementation Registry
GAACA v2.0

Enforces registration-time validation against the Autonomy Policy.
No implementation can exist or be executed without an explicit entry in AUTONOMY_TABLE.
"""

from __future__ import annotations
from typing import Dict, List, Optional

from agent_v2.capabilities.base import CapabilitySpec, ImplementationSpec, Observation, ExecContext
from agent_v2.safety.policy import AUTONOMY_TABLE, requires_human_approval


class CapabilityRegistry:
    def __init__(self):
        self._capabilities: Dict[str, CapabilitySpec] = {}
        self._implementations: Dict[str, ImplementationSpec] = {}

    def register_implementation(self, impl: ImplementationSpec):
        """Hard safety check: Registration fails if autonomy_action is not in AUTONOMY_TABLE."""
        if impl.autonomy_action not in AUTONOMY_TABLE:
            raise KeyError(
                f"Safety Policy Invariant Violated: Implementation '{impl.name}' specifies "
                f"autonomy_action='{impl.autonomy_action}', which does NOT exist in AUTONOMY_TABLE. "
                "Every capability must have an explicit policy decision."
            )
        self._implementations[impl.name] = impl

    def register_capability(self, cap: CapabilitySpec):
        self._capabilities[cap.name] = cap

    def get_capability(self, name: str) -> Optional[CapabilitySpec]:
        return self._capabilities.get(name)

    def get_implementation(self, name: str) -> Optional[ImplementationSpec]:
        return self._implementations.get(name)

    def resolve_implementations_for_capability(self, cap_name: str) -> List[ImplementationSpec]:
        cap = self._capabilities.get(cap_name)
        if not cap:
            return []
        return [self._implementations[impl_name] for impl_name in cap.implementations if impl_name in self._implementations]

    def all_capabilities(self) -> List[CapabilitySpec]:
        return list(self._capabilities.values())

    def all_implementations(self) -> List[ImplementationSpec]:
        return list(self._implementations.values())

    def execute(self, impl_name: str, params: dict, context: ExecContext) -> Observation:
        impl = self.get_implementation(impl_name)
        if not impl:
            return Observation(ok=False, output=None, error=f"Implementation '{impl_name}' not found.")

        # Autonomy check
        confidence = params.get("confidence", 0.85)
        if requires_human_approval(impl.autonomy_action, confidence=confidence):
            # Must pause for human approval
            req = context.approval_manager.request_approval(
                action=impl.autonomy_action,
                input_data=params,
                rationale=f"Gated execution of '{impl.name}' requires explicit sign-off",
                risk_level=impl.risk,
            )
            # If auto-callback exists and approves:
            if context.approval_manager.callback:
                approved = context.approval_manager.callback(req)
                context.approval_manager.resolve(req.id, approved)
                if not approved:
                    return Observation(ok=False, output=None, error="Action rejected by human approval gate.")
            else:
                return Observation(
                    ok=False,
                    output=None,
                    error=f"Awaiting human approval: ApprovalRequest ID {req.id}",
                    metadata={"pending_approval_id": req.id},
                )

        if not impl.handler:
            return Observation(ok=False, output=None, error=f"Implementation '{impl_name}' has no handler defined.")

        try:
            obs = impl.handler(params, context)
            context.budgets.log_risk(impl.cost.risk_weight * 0.1)
            return obs
        except Exception as ex:
            return Observation(ok=False, output=None, error=f"Unhandled exception in '{impl_name}': {str(ex)}")
