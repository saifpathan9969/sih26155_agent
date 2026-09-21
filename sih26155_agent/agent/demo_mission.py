"""
Run: python3 demo_mission.py

Prints the full Mission Mode trace and then a before/after comparison for
the three Juniper devices that share the unknown lockout-command pattern,
proving the grouped-review claim rather than just asserting it.
"""

import sys
import sys
from pathlib import Path as _Path
_PROJECT_ROOT = _Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "agent"))

from agent import SecurityAuditAgent  # noqa: E402
from fixtures import DEVICE_CONFIGS  # noqa: E402


def main():
    agent = SecurityAuditAgent()

    print("\n" + "#" * 70)
    print("# BEFORE — running compliance without the training loop")
    print("#" * 70)
    from tools.fingerprint import fingerprint_vendor
    from tools.parsing import parse_config
    from tools.compliance import evaluate_baseline

    before_findings = {}
    for filename, raw_text in DEVICE_CONFIGS.items():
        vendor, _ = fingerprint_vendor(raw_text)
        baseline, _ = parse_config(vendor, raw_text, filename)
        findings = evaluate_baseline(baseline)
        lockout_finding = next((f for f in findings if f.rule_id == "CIS-AUTH-03"), None)
        if lockout_finding:
            before_findings[filename] = lockout_finding.status.value

    for f, status in before_findings.items():
        print(f"  {f}: CIS-AUTH-03 = {status}")

    print("\n" + "#" * 70)
    print("# MISSION RUN")
    print("#" * 70 + "\n")

    mission = agent.run_mission(
        goal="Audit all configurations in /uploads and report critical security findings.",
        source=DEVICE_CONFIGS,
    )

    print("\n" + "#" * 70)
    print("# AFTER — same rule, same devices, post grouped-training")
    print("#" * 70)
    for filename in before_findings:
        findings = mission.findings_by_device[filename]
        after = next(f for f in findings if f.rule_id == "CIS-AUTH-03")
        print(f"  {filename}: CIS-AUTH-03  {before_findings[filename].upper()} -> {after.status.value.upper()}")

    print("\n" + "#" * 70)
    print("# FINAL REPORT")
    print("#" * 70)
    print(mission.final_report)


if __name__ == "__main__":
    main()
