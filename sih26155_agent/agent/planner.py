"""
Goal & Planning Layer.

*** SWAP POINT FOR A REAL LLM PLANNER ***
This reference implementation is deliberately a deterministic, keyword-based
planner rather than a live LLM call, for two reasons:
  1. A demo on stage should not depend on reaching an external model API.
  2. For THIS system's scope, the plan is nearly fixed regardless of how the
     goal is phrased — the interesting variability is in what the tools
     discover at runtime (which vendors, which lines are unknown, how they
     cluster), not in how the pipeline is sequenced.
A production version would replace `plan_from_goal()` with a call to an LLM
that reads the goal and available tool descriptions and emits the same
List[str] of step names — the rest of the agent does not need to change.
"""

from typing import List

from state import PlanStep

BASE_PLAN = [
    "discover_configs",
    "fingerprint_vendor",
    "parse_config",
    "detect_unknown_syntax",
    "retrieve_candidates",
    "cluster_unknowns",
    "human_gate",
    "evaluate_compliance",
    "prioritize_findings",
    "generate_report",
]


def plan_from_goal(goal: str) -> List[PlanStep]:
    goal_lower = goal.lower()
    steps = list(BASE_PLAN)

    # Minimal goal-sensitivity — shows the planner actually reads the goal,
    # without pretending this MVP does open-ended re-planning.
    if "only critical" in goal_lower or "critical findings only" in goal_lower:
        steps.insert(steps.index("prioritize_findings") + 1, "filter_critical_only")
    if "no report" in goal_lower or "don't generate a report" in goal_lower:
        steps = [s for s in steps if s != "generate_report"]

    return [PlanStep(name=s) for s in steps]
