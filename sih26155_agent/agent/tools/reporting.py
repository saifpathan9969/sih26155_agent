"""Tool 9 — Report Generator. Plain text/markdown for the MVP; same data
could feed the PDF-per-device report from the original PS deliverables."""

from typing import Dict, List


def generate_report(goal: str, working_memory, findings_by_device: Dict[str, list],
                     grouped_reviews: List, remediation_lookup) -> str:
    lines = []
    lines.append(f"# Mission Report\n")
    lines.append(f"**Goal:** {goal}\n")
    lines.append(f"**Summary:** {working_memory.as_status_block()}\n")

    lines.append("\n## Findings by device\n")
    for device_id, findings in findings_by_device.items():
        fails = [f for f in findings if f.status.value == "fail"]
        lines.append(f"- **{device_id}**: {len(fails)} failing checks "
                      f"out of {len(findings)} evaluated")
        for f in fails:
            remediation = remediation_lookup(f.rule_id, None)
            lines.append(f"  - `{f.rule_id}` ({f.severity.value}) — {f.baseline_field_path}")

    if grouped_reviews:
        lines.append("\n## Human review requests (grouped)\n")
        for i, g in enumerate(grouped_reviews, 1):
            lines.append(
                f"{i}. Vendor `{g.vendor}` — pattern seen on "
                f"{len(g.device_ids)} device(s): {', '.join(g.device_ids)} "
                f"— status: {g.status}"
            )
            lines.append(f"   Raw: `{g.representative_raw}`")

    return "\n".join(lines)
