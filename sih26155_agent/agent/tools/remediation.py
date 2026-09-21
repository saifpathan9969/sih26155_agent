"""Tool 8 — Remediation Lookup. Always a lookup into the verified YAML,
never free generation — this is an explicit autonomy-table item."""

import sys
import sys
from pathlib import Path as _Path
_PROJECT_ROOT = _Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "agent"))
from rule_engine import load_rules  # noqa: E402

_RULES_BY_ID = {r["id"]: r for r in load_rules()}


def get_remediation(rule_id: str, vendor: str):
    rule = _RULES_BY_ID.get(rule_id)
    if not rule:
        return None
    return rule.get("remediation", {}).get(vendor)
