"""
Core — Structured Audit Trace Subsystem
GAACA v2.0

Emits immutable, replayable CycleRecords suitable for NTRO-grade audits.
Every conclusion, hypothesis revision, belief provenance, and budget delta
is recorded chronologically.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional

from agent_v2.core.state import AgentState, CycleRecord


class AuditTrace:
    def __init__(self, run_id: str, log_to_console: bool = True):
        self.run_id = run_id
        self.log_to_console = log_to_console
        self.records = []

    def emit_cycle(self, cycle: CycleRecord):
        self.records.append(cycle)
        if self.log_to_console:
            print(f"\n{'='*70}")
            print(f"[CYCLE {cycle.cycle_index}] {datetime.now(timezone.utc).strftime('%H:%M:%S')}")
            print(f"{'='*70}")
            print(f"[WHAT I KNOW]: {cycle.what_i_know}")
            print(f"[WHAT I NEED]: {cycle.what_i_need}")
            if cycle.action_decided:
                print(f"[DECISION]    : {cycle.action_decided}")
                print(f"  Rationale   : {cycle.decision_rationale}")
            if cycle.observation_summary:
                print(f"[OBSERVATION] : {cycle.observation_summary}")
            if cycle.epistemic_delta:
                print(f"[BELIEF UPDATE]: {', '.join(cycle.epistemic_delta)}")
            print(f"[BUDGETS]     : {cycle.budgets_remaining}")

    def export_json(self, target_file: Optional[Path] = None) -> str:
        data = [r.to_dict() for r in self.records]
        serialized = json.dumps(data, indent=2)
        if target_file:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(serialized, encoding="utf-8")
        return serialized
