"""
Safety & Governance — Resource Ledger Subsystem
GAACA v2.0

Tracks token budgets, time, execution steps, web requests, and risk budget.
Exposes remaining budgets to the agent mind as first-class metrics so the
agent reasons about its resources and terminates intelligently before hard caps hit.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import time
from typing import Dict, Any


@dataclass
class ResourceLedger:
    max_cycles: int = 40
    max_wall_clock_s: float = 900.0        # 15 minutes max
    max_web_fetches: int = 15
    max_actions_per_cycle: int = 5
    max_tokens: int = 100_000
    max_risk_score: float = 10.0           # Cumulative risk budget

    # Consumed counters
    cycles_used: int = 0
    tokens_used: int = 0
    web_fetches_used: int = 0
    risk_score_used: float = 0.0
    start_time: float = field(default_factory=time.time)

    @property
    def elapsed_time_s(self) -> float:
        return round(time.time() - self.start_time, 2)

    @property
    def time_remaining_s(self) -> float:
        return max(0.0, round(self.max_wall_clock_s - self.elapsed_time_s, 2))

    @property
    def cycles_remaining(self) -> int:
        return max(0, self.max_cycles - self.cycles_used)

    @property
    def web_fetches_remaining(self) -> int:
        return max(0, self.max_web_fetches - self.web_fetches_used)

    @property
    def is_exhausted(self) -> bool:
        """Returns True if any hard resource floor is breached."""
        if self.cycles_used >= self.max_cycles:
            return True
        if self.elapsed_time_s >= self.max_wall_clock_s:
            return True
        if self.web_fetches_used >= self.max_web_fetches:
            return True
        if self.tokens_used >= self.max_tokens:
            return True
        if self.risk_score_used >= self.max_risk_score:
            return True
        return False

    def log_cycle(self):
        self.cycles_used += 1

    def log_web_fetch(self):
        self.web_fetches_used += 1

    def log_tokens(self, count: int):
        self.tokens_used += count

    def log_risk(self, amount: float):
        self.risk_score_used = round(self.risk_score_used + amount, 2)

    def summary(self) -> Dict[str, Any]:
        return {
            "cycles": f"{self.cycles_used}/{self.max_cycles}",
            "time_elapsed_s": self.elapsed_time_s,
            "time_remaining_s": self.time_remaining_s,
            "web_fetches": f"{self.web_fetches_used}/{self.max_web_fetches}",
            "tokens": f"{self.tokens_used}/{self.max_tokens}",
            "risk_used": f"{self.risk_score_used}/{self.max_risk_score}",
            "exhausted": self.is_exhausted,
        }
