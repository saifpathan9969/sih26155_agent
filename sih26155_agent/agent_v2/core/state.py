"""
Core — Agent State Data Models
GAACA v2.0

Defines the rich, persistent state of the cognitive agent.
State is not just a list of past tool outputs; it contains goals, subgoals,
beliefs, world model, hypotheses, observations, failures with diagnoses,
resource budgets, and typed terminal states.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from agent_v2.mind.world_model import WorldModel
from agent_v2.mind.hypothesis import Hypothesis


class TerminalState(str, Enum):
    """The 10 typed terminal states of the cognitive agent."""
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"   # Intelligent stop — lack of data, never hallucinate
    HUMAN_REQUIRED = "HUMAN_REQUIRED"                 # Awaiting human gate resolution
    SAFETY_BLOCKED = "SAFETY_BLOCKED"                 # Policy boundary violation
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"         # Budget floor reached
    VERIFICATION_FAILED = "VERIFICATION_FAILED"       # Failed independent validation
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE" # Irreconcilable conflict detected
    UNKNOWN = "UNKNOWN"                               # Undetermined
    USER_CANCELLED = "USER_CANCELLED"                 # Aborted by user


@dataclass
class Goal:
    raw_text: str
    intent: str
    constraints: List[str] = field(default_factory=list)
    definition_of_done: str = ""
    subgoals: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "raw_text": self.raw_text,
            "intent": self.intent,
            "constraints": self.constraints,
            "definition_of_done": self.definition_of_done,
            "subgoals": self.subgoals,
        }


@dataclass
class ActionRecord:
    cycle: int
    capability: str
    implementation: str
    parameters: Dict[str, Any]
    observation: Any
    ok: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "cycle": self.cycle,
            "capability": self.capability,
            "implementation": self.implementation,
            "parameters": self.parameters,
            "observation": str(self.observation)[:500],
            "ok": self.ok,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class FailureRecord:
    cycle: int
    action: str
    error: str
    failure_class: str                    # "transient", "precondition", "capability_mismatch", "policy", "unsupported"
    diagnosis: str                        # Root cause diagnosis: why expectation failed
    failed_assumption: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "cycle": self.cycle,
            "action": self.action,
            "error": self.error,
            "failure_class": self.failure_class,
            "diagnosis": self.diagnosis,
            "failed_assumption": self.failed_assumption,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ApprovalRequest:
    id: str
    action: str
    input_data: Dict[str, Any]
    rationale: str
    risk_level: str                       # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    status: str = "PENDING"               # "PENDING", "APPROVED", "REJECTED"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action": self.action,
            "input_data": self.input_data,
            "rationale": self.rationale,
            "risk_level": self.risk_level,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


@dataclass
class CycleRecord:
    """Immutable record of one full cognitive loop cycle."""
    cycle_index: int
    what_i_know: str                      # Executive summary of world model & verified facts
    what_i_need: str                      # Open questions or current subgoal
    action_decided: Optional[str] = None  # Selected capability implementation
    decision_rationale: str = ""
    observation_summary: str = ""
    epistemic_delta: List[str] = field(default_factory=list)
    budgets_remaining: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "cycle_index": self.cycle_index,
            "what_i_know": self.what_i_know,
            "what_i_need": self.what_i_need,
            "action_decided": self.action_decided,
            "decision_rationale": self.decision_rationale,
            "observation_summary": self.observation_summary,
            "epistemic_delta": self.epistemic_delta,
            "budgets_remaining": self.budgets_remaining,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AgentState:
    """The central persistent state of the agent."""
    run_id: str
    goal: Goal
    world: WorldModel = field(default_factory=WorldModel)
    hypotheses: List[Hypothesis] = field(default_factory=list)
    completed_actions: List[ActionRecord] = field(default_factory=list)
    failed_actions: List[FailureRecord] = field(default_factory=list)
    pending_approval: Optional[ApprovalRequest] = None
    terminal_state: Optional[TerminalState] = None
    terminal_justification: Optional[str] = None
    trace: List[CycleRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "goal": self.goal.to_dict(),
            "world": self.world.to_dict(),
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "completed_actions": [a.to_dict() for a in self.completed_actions],
            "failed_actions": [f.to_dict() for f in self.failed_actions],
            "pending_approval": self.pending_approval.to_dict() if self.pending_approval else None,
            "terminal_state": self.terminal_state.value if self.terminal_state else None,
            "terminal_justification": self.terminal_justification,
            "trace": [c.to_dict() for c in self.trace],
            "created_at": self.created_at.isoformat(),
        }
