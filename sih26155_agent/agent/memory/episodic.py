"""Episodic memory — what happened, when, and what the outcome was.

This is deliberately a plain, inspectable list of events rather than a
vector store or database, because for the MVP its only job is to let
reflection.py answer "have we seen a cluster like this before?" and to give
judges something they can literally read to verify a claim.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class EpisodicEvent:
    timestamp: datetime
    vendor: str
    raw_pattern: str
    mapped_field: Optional[str]
    outcome: str  # "confirmed" | "rejected" | "escalated" | "auto_resolved"
    device_ids: List[str] = field(default_factory=list)


class EpisodicMemory:
    def __init__(self) -> None:
        self._events: List[EpisodicEvent] = []

    def record(self, vendor: str, raw_pattern: str, outcome: str,
               mapped_field: Optional[str] = None,
               device_ids: Optional[List[str]] = None) -> EpisodicEvent:
        event = EpisodicEvent(
            timestamp=datetime.now(timezone.utc),
            vendor=vendor,
            raw_pattern=raw_pattern,
            mapped_field=mapped_field,
            outcome=outcome,
            device_ids=device_ids or [],
        )
        self._events.append(event)
        return event

    def all_events(self) -> List[EpisodicEvent]:
        return list(self._events)

    def confirmed_patterns_for_vendor(self, vendor: str) -> List[EpisodicEvent]:
        return [e for e in self._events if e.vendor == vendor and e.outcome == "confirmed"]
