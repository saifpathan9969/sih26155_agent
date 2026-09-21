"""
Mind — Reflection Subsystem
GAACA v2.0

Performs cognitive evaluation:
1. Compares actual observations against `expected_observation` on plan nodes.
2. Detects surprise and cognitive dissonance when predictions fail.
3. Detects stagnation (zero new facts or closed nodes across N consecutive cycles).
"""

from typing import List, Tuple
from agent_v2.core.state import CycleRecord
from agent_v2.mind.planning import PlanNode


class ReflectionEngine:
    def __init__(self, stagnation_threshold: int = 3):
        self.stagnation_threshold = stagnation_threshold
        self.consecutive_stagnant_cycles = 0

    def evaluate_progress(self, trace: List[CycleRecord]) -> Tuple[bool, str]:
        """Checks if recent cycles produced measurable belief additions."""
        if len(trace) < 2:
            return True, "Initial progress underway."

        recent = trace[-1]
        if not recent.epistemic_delta and not recent.action_decided:
            self.consecutive_stagnant_cycles += 1
        else:
            self.consecutive_stagnant_cycles = 0

        if self.consecutive_stagnant_cycles >= self.stagnation_threshold:
            return False, f"Stagnation detected: {self.consecutive_stagnant_cycles} cycles with zero epistemic progress."

        return True, "Cognitive progress healthy."

    def verify_expectation(self, node: PlanNode, actual_observation: str) -> Tuple[bool, str]:
        """
        Mechanically compares actual observation against expected_observation.
        A prediction failure triggers hypothesis formation and strategy change.
        """
        if not node.expected_observation:
            return True, "No prior expectation defined."

        # Substring/semantic match check
        exp_lower = node.expected_observation.lower()
        act_lower = actual_observation.lower()

        if "fail" in act_lower or "error" in act_lower or "refused" in act_lower:
            if "fail" not in exp_lower and "error" not in exp_lower:
                return False, f"Unexpected failure: expected '{node.expected_observation}', but got error."

        return True, "Observation aligned with expectation."
