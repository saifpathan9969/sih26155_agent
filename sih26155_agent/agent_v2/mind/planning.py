"""
Mind — Dynamic Hierarchical Planning
GAACA v2.0

Plans are mutable trees of PlanNodes, not static pipelines.
Crucial Improvement: Every plan node includes `expected_observation`.
Comparing actual observations against expectations mechanically detects surprises
and triggers hypothesis formation and strategic self-correction (banning bare retries).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional
import uuid

from agent_v2.core.state import Goal


PlanStatus = Literal["PENDING", "ACTIVE", "DONE", "FAILED", "ABANDONED", "BLOCKED"]


@dataclass
class PlanNode:
    id: str
    objective: str
    required_capability: str
    expected_observation: str                     # What the agent predicts will happen
    preconditions: List[str] = field(default_factory=list)
    success_criteria: str = ""
    status: PlanStatus = "PENDING"
    attempts: List[Dict] = field(default_factory=list)
    children: List["PlanNode"] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "objective": self.objective,
            "required_capability": self.required_capability,
            "expected_observation": self.expected_observation,
            "preconditions": self.preconditions,
            "success_criteria": self.success_criteria,
            "status": self.status,
            "attempts_count": len(self.attempts),
            "children": [c.to_dict() for c in self.children],
        }


class Planner:
    def __init__(self):
        self.root: Optional[PlanNode] = None

    def construct_plan(self, goal: Goal) -> PlanNode:
        root = PlanNode(
            id=f"plan_{uuid.uuid4().hex[:6]}",
            objective=goal.intent,
            required_capability="COGNITION",
            expected_observation="Subgoals executed to satisfaction",
            status="ACTIVE",
        )

        for subgoal in goal.subgoals:
            # Dynamically infer required capability and expected observation
            cap = "ENVIRONMENT"
            expected = "Observation obtained"

            if "converse" in subgoal or "operator" in subgoal or "respond" in subgoal:
                cap = "COMMUNICATION"
                expected = "Conversational response delivered"
            elif "search" in subgoal or "research" in subgoal:
                cap = "WEB_RESEARCH"
                expected = "Relevant authoritative sources returned"
            elif "discover" in subgoal:
                cap = "FILESYSTEM"
                expected = "Files discovered in target path"
            elif "baseline" in subgoal or "security" in subgoal or "audit" in subgoal:
                cap = "SECURITY"
                expected = "Deterministic compliance evaluation returned"
            elif "synthesize" in subgoal or "report" in subgoal:
                cap = "DOCUMENTS"
                expected = "Advisory report generated"

            node = PlanNode(
                id=f"node_{uuid.uuid4().hex[:6]}",
                objective=subgoal,
                required_capability=cap,
                expected_observation=expected,
                success_criteria=f"Verified evidence supports completion of {subgoal}",
                status="PENDING",
            )
            root.children.append(node)

        self.root = root
        return root

    def get_next_pending_node(self) -> Optional[PlanNode]:
        if not self.root:
            return None
        for child in self.root.children:
            if child.status == "PENDING":
                return child
        return None

    def mark_completed(self, node_id: str, observation: str):
        if not self.root:
            return
        for child in self.root.children:
            if child.id == node_id:
                child.status = "DONE"
                child.attempts.append({"status": "DONE", "observation": observation})
                break

    def mark_failed(self, node_id: str, error: str):
        if not self.root:
            return
        for child in self.root.children:
            if child.id == node_id:
                child.status = "FAILED"
                child.attempts.append({"status": "FAILED", "error": error})
                break
