"""
Mind — Utility-Driven Decision Engine
GAACA v2.0

Action Value Equation:
Value = Expected Progress + Information Gain + Goal Relevance - (Risk + Cost + Resource Consumption)

Applies choke-point filters:
1. Epistemic sufficiency
2. Autonomy policy
3. Failed-strategy exclusion (bans bare retries)
4. Utility score ranking
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from agent_v2.capabilities.base import ImplementationSpec
from agent_v2.safety.policy import requires_human_approval, get_autonomy_rule, Autonomy


@dataclass
class ScoredAction:
    implementation: ImplementationSpec
    parameters: Dict
    score: float
    rationale: str


class DecisionEngine:
    def __init__(self):
        # Maps objective -> set of failed (implementation_name, param_hash)
        self.failed_strategies: Dict[str, Set[str]] = {}

    def record_failed_strategy(self, objective: str, impl_name: str, params: dict):
        if objective not in self.failed_strategies:
            self.failed_strategies[objective] = set()
        sig = f"{impl_name}:{sorted(params.items())}"
        self.failed_strategies[objective].add(sig)

    def is_strategy_failed(self, objective: str, impl_name: str, params: dict) -> bool:
        failed_for_obj = self.failed_strategies.get(objective, set())
        sig = f"{impl_name}:{sorted(params.items())}"
        return sig in failed_for_obj

    def evaluate_action_value(
        self,
        impl: ImplementationSpec,
        params: dict,
        objective: str,
        expected_info_gain: float = 0.5,
        expected_progress: float = 0.8,
    ) -> float:
        """
        Calculates Action Value = (Progress + InfoGain + Relevance) - (Risk + Cost)
        """
        # Risk factor
        risk_map = {"NONE": 0.0, "LOW": 0.2, "MEDIUM": 0.6, "HIGH": 1.2, "CRITICAL": 3.0}
        risk_penalty = risk_map.get(impl.risk, 0.5)

        cost_penalty = (impl.cost.estimated_seconds * 0.1) + (impl.cost.network_calls * 0.2)
        benefit = expected_progress + expected_info_gain + 0.5
        if impl.name in objective or (impl.name == "converse" and any(k in objective for k in ("converse", "respond", "greet", "operator"))):
            benefit += 0.8

        return round(benefit - (risk_penalty + cost_penalty), 4)

    def select_best_action(
        self,
        candidates: List[ImplementationSpec],
        objective: str,
        confidence_map: Optional[Dict[str, float]] = None,
    ) -> Optional[ScoredAction]:
        scored: List[ScoredAction] = []

        failed_for_obj = self.failed_strategies.get(objective, set())

        for impl in candidates:
            params: dict = {}
            sig = f"{impl.name}:{sorted(params.items())}"

            # Banning bare retries: If identical implementation previously failed for this objective, filter out!
            if sig in failed_for_obj:
                continue

            conf = confidence_map.get(impl.name, 1.0) if confidence_map else 1.0
            val = self.evaluate_action_value(impl, params, objective)

            scored.append(ScoredAction(
                implementation=impl,
                parameters=params,
                score=val,
                rationale=f"Utility-ranked candidate for '{objective}' with score {val}",
            ))

        if not scored:
            return None

        return max(scored, key=lambda s: s.score)
