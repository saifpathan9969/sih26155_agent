"""
Memory — Working Memory
GAACA v2.0

Active scratchpad for the current cognitive cycle:
- Attention focus: what the agent is currently working on
- Active counters: cycles, actions, failures in the current run
- Scratch notes: ephemeral observations not yet committed to beliefs
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class AttentionFocus:
    """What the agent is currently attending to."""
    current_objective: str = ""
    current_plan_node_id: Optional[str] = None
    active_hypothesis_id: Optional[str] = None
    pending_question: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "current_objective": self.current_objective,
            "current_plan_node_id": self.current_plan_node_id,
            "active_hypothesis_id": self.active_hypothesis_id,
            "pending_question": self.pending_question,
        }


@dataclass
class ScratchNote:
    content: str
    source: str
    relevance: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "content": self.content[:500],
            "source": self.source,
            "relevance": self.relevance,
            "created_at": self.created_at.isoformat(),
        }


class WorkingMemory:
    """Short-term, volatile memory for the active cognitive cycle."""

    def __init__(self, max_notes: int = 50):
        self.focus = AttentionFocus()
        self.scratch_notes: List[ScratchNote] = []
        self.max_notes = max_notes
        self.cycle_count: int = 0
        self.action_count: int = 0
        self.failure_count: int = 0
        self.last_action: Optional[str] = None
        self.last_observation_summary: Optional[str] = None

    def set_focus(self, objective: str, plan_node_id: Optional[str] = None,
                  hypothesis_id: Optional[str] = None):
        self.focus.current_objective = objective
        self.focus.current_plan_node_id = plan_node_id
        self.focus.active_hypothesis_id = hypothesis_id

    def add_note(self, content: str, source: str, relevance: float = 1.0):
        """Add a scratch note; evicts lowest-relevance note if full."""
        note = ScratchNote(content=content, source=source, relevance=relevance)
        self.scratch_notes.append(note)

        if len(self.scratch_notes) > self.max_notes:
            self.scratch_notes.sort(key=lambda n: n.relevance)
            self.scratch_notes.pop(0)

    def record_action(self, action_name: str, observation_summary: str, success: bool):
        self.action_count += 1
        self.last_action = action_name
        self.last_observation_summary = observation_summary
        if not success:
            self.failure_count += 1

    def tick_cycle(self):
        self.cycle_count += 1

    def get_recent_notes(self, n: int = 10) -> List[ScratchNote]:
        return self.scratch_notes[-n:]

    def clear(self):
        """Reset working memory for a new run."""
        self.focus = AttentionFocus()
        self.scratch_notes.clear()
        self.cycle_count = 0
        self.action_count = 0
        self.failure_count = 0
        self.last_action = None
        self.last_observation_summary = None

    def summary(self) -> Dict[str, Any]:
        return {
            "focus": self.focus.to_dict(),
            "cycles": self.cycle_count,
            "actions": self.action_count,
            "failures": self.failure_count,
            "scratch_notes": len(self.scratch_notes),
            "last_action": self.last_action,
        }

    def to_dict(self) -> dict:
        return {
            "focus": self.focus.to_dict(),
            "scratch_notes": [n.to_dict() for n in self.scratch_notes[-20:]],
            "counters": {
                "cycles": self.cycle_count,
                "actions": self.action_count,
                "failures": self.failure_count,
            },
            "last_action": self.last_action,
            "last_observation_summary": self.last_observation_summary,
        }
