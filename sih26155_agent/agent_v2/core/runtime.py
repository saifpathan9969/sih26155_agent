"""
Core — Runtime Lifecycle Manager
GAACA v2.0

Manages the agent's lifecycle:
- Initialization with all subsystems
- Pause/resume for human gates
- State serialization for persistence
- Graceful shutdown
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import json

from agent_v2.core.state import AgentState, TerminalState
from agent_v2.memory.store import MemoryStore


class AgentRuntime:
    """Manages the complete lifecycle of an autonomous agent session."""

    def __init__(
        self,
        project_root: Path,
        scratch_dir: Optional[Path] = None,
        db_path: Optional[Path] = None,
    ):
        self.project_root = project_root.resolve()
        self.scratch_dir = (scratch_dir or project_root / "agent_v2" / "scratch").resolve()
        self.scratch_dir.mkdir(parents=True, exist_ok=True)

        self.store = MemoryStore(db_path or self.scratch_dir / "agent_memory.db")
        self._paused: bool = False
        self._pause_reason: Optional[str] = None
        self._started_at: Optional[datetime] = None
        self._ended_at: Optional[datetime] = None

    def start(self):
        """Marks the runtime as started."""
        self._started_at = datetime.now(timezone.utc)
        self._paused = False

    def pause(self, reason: str = "Awaiting human approval"):
        """Pauses the runtime (e.g., for human gate)."""
        self._paused = True
        self._pause_reason = reason

    def resume(self):
        """Resumes the runtime after pause."""
        self._paused = False
        self._pause_reason = None

    def stop(self):
        """Marks the runtime as stopped."""
        self._ended_at = datetime.now(timezone.utc)

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def is_running(self) -> bool:
        return self._started_at is not None and self._ended_at is None and not self._paused

    def save_state(self, state: AgentState):
        """Persists the current agent state to SQLite."""
        self.store.save_state_snapshot(state.run_id, state.to_dict())

    def load_state(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Loads the latest state snapshot for a run."""
        snapshot = self.store.load_latest_snapshot(run_id)
        if snapshot:
            return snapshot.get("state_json")
        return None

    def export_trace(self, state: AgentState, output_path: Optional[Path] = None) -> Path:
        """Exports the full audit trace to a JSON file."""
        path = output_path or self.scratch_dir / f"trace_{state.run_id}.json"
        trace_data = {
            "run_id": state.run_id,
            "goal": state.goal.to_dict(),
            "terminal_state": state.terminal_state.value if state.terminal_state else None,
            "terminal_justification": state.terminal_justification,
            "trace": [c.to_dict() for c in state.trace],
            "completed_actions": [a.to_dict() for a in state.completed_actions],
            "failed_actions": [f.to_dict() for f in state.failed_actions],
            "world_model": state.world.to_dict(),
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }
        path.write_text(json.dumps(trace_data, indent=2, default=str), encoding="utf-8")
        return path

    def status(self) -> Dict[str, Any]:
        return {
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "ended_at": self._ended_at.isoformat() if self._ended_at else None,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "pause_reason": self._pause_reason,
            "project_root": str(self.project_root),
            "scratch_dir": str(self.scratch_dir),
        }

    def cleanup(self):
        """Closes database connections and cleans up."""
        self.store.close()
