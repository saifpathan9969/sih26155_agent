"""
Memory — Episodic Memory
GAACA v2.0

Chronological trace of actions, observations, surprises, and decisions.
Provides the agent with autobiographical recall:
- What happened in cycle N?
- When did I last encounter this type of failure?
- What was the surprise that triggered hypothesis H?
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Episode:
    """A single episodic memory entry — one cognitive cycle's record."""
    episode_id: int
    run_id: str
    cycle_index: int
    objective: str
    action_taken: str
    parameters: Dict[str, Any]
    observation_summary: str
    success: bool
    surprise: bool = False                # Was the observation unexpected?
    surprise_description: Optional[str] = None
    beliefs_added: List[str] = field(default_factory=list)
    beliefs_contradicted: List[str] = field(default_factory=list)
    hypothesis_formed: Optional[str] = None
    correction_applied: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "run_id": self.run_id,
            "cycle_index": self.cycle_index,
            "objective": self.objective,
            "action_taken": self.action_taken,
            "observation_summary": self.observation_summary[:300],
            "success": self.success,
            "surprise": self.surprise,
            "surprise_description": self.surprise_description,
            "beliefs_added": self.beliefs_added,
            "beliefs_contradicted": self.beliefs_contradicted,
            "hypothesis_formed": self.hypothesis_formed,
            "correction_applied": self.correction_applied,
            "timestamp": self.timestamp.isoformat(),
        }


class EpisodicMemory:
    """Chronological, immutable record of the agent's experiences."""

    def __init__(self):
        self._episodes: List[Episode] = []
        self._next_id: int = 1

    def record(
        self,
        run_id: str,
        cycle_index: int,
        objective: str,
        action_taken: str,
        parameters: Dict[str, Any],
        observation_summary: str,
        success: bool,
        surprise: bool = False,
        surprise_description: Optional[str] = None,
        beliefs_added: Optional[List[str]] = None,
        beliefs_contradicted: Optional[List[str]] = None,
        hypothesis_formed: Optional[str] = None,
        correction_applied: Optional[str] = None,
    ) -> Episode:
        episode = Episode(
            episode_id=self._next_id,
            run_id=run_id,
            cycle_index=cycle_index,
            objective=objective,
            action_taken=action_taken,
            parameters=parameters,
            observation_summary=observation_summary,
            success=success,
            surprise=surprise,
            surprise_description=surprise_description,
            beliefs_added=beliefs_added or [],
            beliefs_contradicted=beliefs_contradicted or [],
            hypothesis_formed=hypothesis_formed,
            correction_applied=correction_applied,
        )
        self._episodes.append(episode)
        self._next_id += 1
        return episode

    def get_by_run(self, run_id: str) -> List[Episode]:
        return [e for e in self._episodes if e.run_id == run_id]

    def get_surprises(self, run_id: Optional[str] = None) -> List[Episode]:
        eps = self._episodes if run_id is None else self.get_by_run(run_id)
        return [e for e in eps if e.surprise]

    def get_failures(self, run_id: Optional[str] = None) -> List[Episode]:
        eps = self._episodes if run_id is None else self.get_by_run(run_id)
        return [e for e in eps if not e.success]

    def last_n(self, n: int = 10) -> List[Episode]:
        return self._episodes[-n:]

    def find_similar_action(self, action_name: str) -> List[Episode]:
        return [e for e in self._episodes if e.action_taken == action_name]

    def total_episodes(self) -> int:
        return len(self._episodes)

    def export_all(self) -> List[dict]:
        return [e.to_dict() for e in self._episodes]
