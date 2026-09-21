"""
Capabilities — Base Specifications
GAACA v2.0

Two-Level Capability Model:
1. Semantic Capability (what the agent can do: e.g. "WEB_RESEARCH", "FILESYSTEM", "SECURITY")
2. Concrete Implementation (how it is done: e.g. "web_search", "read_file", "parse_config")

Invariant: Registration fails at import/load time if autonomy_action is missing
or not defined in AUTONOMY_TABLE.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agent_v2.safety.budgets import ResourceLedger
from agent_v2.safety.approval import ApprovalManager
from agent_v2.mind.world_model import WorldModel


@dataclass
class Observation:
    """The raw and structured output resulting from an action in the environment."""
    ok: bool
    output: Any
    error: Optional[str] = None
    raw_evidence: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "output": self.output,
            "error": self.error,
            "raw_evidence": self.raw_evidence,
            "metadata": self.metadata,
        }


@dataclass
class ExecContext:
    """Contextual handles passed to an action execution."""
    run_id: str
    project_root: Path
    scratch_dir: Path
    budgets: ResourceLedger
    approval_manager: ApprovalManager
    world_model: WorldModel


@dataclass
class CostModel:
    estimated_tokens: int = 0
    estimated_seconds: float = 0.5
    network_calls: int = 0
    risk_weight: float = 1.0  # 1.0 (NONE) to 5.0 (CRITICAL)


@dataclass
class ImplementationSpec:
    """Mechanical details of an action execution."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    autonomy_action: str                      # Mandatory key in AUTONOMY_TABLE
    risk: str                                 # "NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"
    cost: CostModel = field(default_factory=CostModel)
    failure_modes: List[str] = field(default_factory=list)
    handler: Optional[Callable[[Dict[str, Any], ExecContext], Observation]] = None


@dataclass
class CapabilitySpec:
    """Semantic capability description representing what the agent can achieve."""
    name: str                                 # e.g. "WEB_RESEARCH", "FILESYSTEM", "SECURITY"
    description: str
    produces: List[str] = field(default_factory=list)        # belief subjects it can establish
    requires: List[str] = field(default_factory=list)        # preconditions / required beliefs
    implementations: List[str] = field(default_factory=list) # names of ImplementationSpec instances
