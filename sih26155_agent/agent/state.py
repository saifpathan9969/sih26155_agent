"""Plan and mission state — plain dataclasses so the whole trace is
inspectable/printable, not hidden inside an opaque agent object."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PlanStep:
    name: str
    status: str = "pending"  # pending | running | done | skipped


@dataclass
class GroupedReview:
    """One human-facing review request that may represent MANY unknown
    command occurrences across MANY devices, collapsed by reflection."""
    representative_raw: str
    vendor: str
    device_ids: List[str]
    line_refs: List[str]
    proposed_category: Optional[str] = None
    proposed_field_path: Optional[str] = None
    proposed_value: Optional[Any] = None
    status: str = "awaiting_human"  # awaiting_human | confirmed | rejected


@dataclass
class MissionState:
    goal: str
    plan: List[PlanStep] = field(default_factory=list)
    device_ids: List[str] = field(default_factory=list)
    findings_by_device: Dict[str, list] = field(default_factory=dict)
    grouped_reviews: List[GroupedReview] = field(default_factory=list)
    flips: List[Dict] = field(default_factory=list)
    trace: List[str] = field(default_factory=list)
    final_report: Optional[str] = None

