"""Tool 7 — Compliance Rule Engine. Thin wrapper: the agent NEVER
reimplements or bypasses this — it calls it and treats the result as
opaque structured data, never as something to second-guess."""

import sys
import sys
from pathlib import Path as _Path
_PROJECT_ROOT = _Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "agent"))
from rule_engine import evaluate_baseline, load_rules  # noqa: E402,F401


def summarize_findings(findings) -> dict:
    summary = {"pass": 0, "fail": 0, "needs_human_review": 0, "not_applicable": 0}
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        summary[f.status.value] = summary.get(f.status.value, 0) + 1
        if f.status.value == "fail":
            by_severity[f.severity.value] = by_severity.get(f.severity.value, 0) + 1
    return {"by_status": summary, "fail_by_severity": by_severity}
