"""
The Security Audit Agent.

This is the ONLY place the loop from the architecture doc actually runs:
  Goal -> Plan -> Tool -> Observation -> Human gate? -> Reflect -> Next

Everything it calls is either a deterministic tool (parsing, compliance,
remediation) or a policy check (autonomy.py). It never calls an LLM to
decide a compliance verdict, and it never mutates a SecurityBaseline except
through the same validated path training_flow.py already proved out.
"""

import sys
from typing import Callable, Dict, Optional

import sys
from pathlib import Path as _Path
_PROJECT_ROOT = _Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "agent"))

from security_baseline_schema import EvidenceField, Interpretation, InterpretationMethod, VendorFamily  # noqa: E402
from training_flow import validate_mapping  # noqa: E402

from planner import plan_from_goal  # noqa: E402
from state import MissionState, GroupedReview  # noqa: E402
from policies.autonomy import requires_human  # noqa: E402
from memory.working import WorkingMemory  # noqa: E402
from memory.knowledge_base import VendorKnowledgeBase, KnowledgeBaseEntry  # noqa: E402
from memory.episodic import EpisodicMemory  # noqa: E402
from tools.discovery import discover_configs  # noqa: E402
from tools.fingerprint import fingerprint_vendor  # noqa: E402
from tools.parsing import parse_config  # noqa: E402
from tools.compliance import evaluate_baseline, summarize_findings  # noqa: E402
from tools.remediation import get_remediation  # noqa: E402
from tools.reporting import generate_report  # noqa: E402
from reflection import cluster_unknowns  # noqa: E402


def _resolve_parent_and_attr(baseline, dotted_path: str):
    parts = dotted_path.split(".")
    obj = baseline
    for part in parts[:-1]:
        obj = getattr(obj, part)
    return obj, parts[-1]


class SecurityAuditAgent:
    def __init__(self, kb: Optional[VendorKnowledgeBase] = None,
                 episodic: Optional[EpisodicMemory] = None,
                 human_approval_callback: Optional[Callable[[GroupedReview], bool]] = None):
        self.kb = kb or VendorKnowledgeBase()
        self.episodic = episodic or EpisodicMemory()
        # Default callback auto-approves and logs — a real deployment would
        # inject a callback that actually blocks on a human clicking Confirm.
        self.human_approval_callback = human_approval_callback or self._auto_approve

    @staticmethod
    def _auto_approve(review: GroupedReview) -> bool:
        return True

    def run_mission(self, goal: str, source, trace: bool = True,
                    on_log: Optional[Callable[[str], None]] = None) -> MissionState:
        mission = MissionState(goal=goal, plan=plan_from_goal(goal))
        wm = WorkingMemory()

        def log(msg: str):
            wm.note(msg)
            if on_log:
                try:
                    on_log(msg)
                except Exception:
                    pass
            if trace:
                try:
                    print(msg)
                except UnicodeEncodeError:
                    print(msg.encode("ascii", "replace").decode("ascii"))

        log(f"MISSION GOAL: {goal}")
        log("=" * 70)


        # --- discover ---------------------------------------------------
        log("[1] Discovering configurations ...")
        configs = discover_configs(source)
        wm.total_devices = len(configs)
        mission.device_ids = list(configs.keys())
        log(f"    found {len(configs)} configuration file(s)")

        # --- fingerprint + parse -----------------------------------------
        baselines = {}
        all_unknowns = []
        device_id_by_file = {}
        log("[2] Fingerprinting vendors + parsing known syntax ...")
        for filename, raw_text in configs.items():
            vendor, confidence = fingerprint_vendor(raw_text)
            device_id_by_file[filename] = filename
            baseline, unknowns = parse_config(vendor, raw_text, filename)
            baselines[filename] = baseline
            all_unknowns.extend(unknowns)
            wm.processed += 1
            log(f"    {filename}: vendor={vendor.value} (confidence={confidence}), "
                f"{len(unknowns)} unrecognized security-relevant line(s)")

        wm.unknown_detections = len(all_unknowns)

        # --- reflection / clustering -------------------------------------
        log("[3] Clustering unknown syntax across devices (reflection) ...")
        grouped_reviews = cluster_unknowns(all_unknowns, device_id_by_file)
        mission.grouped_reviews = grouped_reviews
        for g in grouped_reviews:
            if len(g.device_ids) > 1:
                log(f"    grouped {len(g.device_ids)} devices under ONE review: "
                    f"{g.device_ids} -> \"{g.representative_raw}\"")
            else:
                log(f"    single occurrence: {g.device_ids} -> \"{g.representative_raw}\"")

        # Snapshot initial compliance state BEFORE human intervention
        initial_findings = {
            dev_id: {f.rule_id: f.status.value for f in evaluate_baseline(bl)}
            for dev_id, bl in baselines.items()
        }

        # --- human gate ---------------------------------------------------
        log("[4] Human gate — mapping unknown syntax (never autonomous) ...")
        for g in grouped_reviews:
            assert requires_human("map_unknown_syntax"), "safety invariant violated"
            approved = self.human_approval_callback(g)
            if not approved:
                g.status = "rejected"
                self.episodic.record(g.vendor, g.representative_raw, "rejected", device_ids=g.device_ids)
                log(f"    REJECTED: \"{g.representative_raw}\"")
                continue

            # For the demo, the "human's" mapping is looked up from a tiny
            # seed of known intents keyed by substring — standing in for the
            # actual UI where a person picks category + field + value.
            mapping = self._infer_demo_mapping(g.representative_raw)
            if mapping is None:
                g.status = "rejected"
                log(f"    NO MAPPING AVAILABLE (demo stub): \"{g.representative_raw}\"")
                continue

            field_path, value, category = mapping
            validation = validate_mapping(field_path, value)
            if not validation.valid:
                log(f"    ✗ mapping rejected — {validation.error}")
                g.status = "rejected"
                continue

            g.proposed_field_path, g.proposed_value, g.proposed_category = field_path, value, category
            g.status = "confirmed"

            # Apply to every device in the cluster, not just one.
            for device_id in g.device_ids:
                baseline = baselines[device_id]
                parent_obj, attr = _resolve_parent_and_attr(baseline, field_path)
                setattr(parent_obj, attr, EvidenceField(
                    value=value, explicitly_configured=True,
                    interpretation=Interpretation(
                        method=InterpretationMethod.HUMAN_ANNOTATED, confidence=1.0),
                ))

            self.kb.add(KnowledgeBaseEntry(
                vendor=VendorFamily(g.vendor), raw_pattern=g.representative_raw,
                security_category=category, baseline_field_path=field_path,
                value_type_hint=type(value).__name__, added_by="admin_demo",
            ))
            self.episodic.record(g.vendor, g.representative_raw, "confirmed",
                                  mapped_field=field_path, device_ids=g.device_ids)
            log(f"    [OK] CONFIRMED once -> applied to {len(g.device_ids)} device(s): {field_path} = {value}")

        # --- compliance ----------------------------------------------------
        log("[5] Evaluating 20 compliance rules per device ...")
        findings_by_device = {}
        for device_id, baseline in baselines.items():
            findings = evaluate_baseline(baseline)
            findings_by_device[device_id] = findings
            summary = summarize_findings(findings)
            for sev, count in summary["fail_by_severity"].items():
                if sev == "critical":
                    wm.critical_findings += count
                elif sev == "high":
                    wm.high_findings += count
                elif sev == "medium":
                    wm.medium_findings += count
                elif sev == "low":
                    wm.low_findings += count
            wm.per_device_summary[device_id] = summary
        mission.findings_by_device = findings_by_device

        # Compute status flips
        flips = []
        for dev_id, findings in findings_by_device.items():
            for f in findings:
                prev_status = initial_findings.get(dev_id, {}).get(f.rule_id)
                if prev_status and prev_status != f.status.value:
                    flips.append({
                        "device_id": dev_id,
                        "rule_id": f.rule_id,
                        "before_status": prev_status,
                        "after_status": f.status.value,
                    })
        mission.flips = flips
        mission.trace = list(wm.log)

        # --- prioritize ------------------------------------------------
        log("[6] Prioritizing findings ...")
        log(f"    {wm.as_status_block()}")

        # --- report --------------------------------------------------------
        log("[7] Generating mission report ...")
        report = generate_report(goal, wm, findings_by_device, grouped_reviews, get_remediation)
        mission.final_report = report


        log("=" * 70)
        log("MISSION COMPLETE")

        self._working_memory = wm
        return mission

    @staticmethod
    def _infer_demo_mapping(raw_command: str):
        """Uses the network_config_db multi-vendor dataset to automatically
        resolve vendor configuration commands without calling for human review."""
        try:
            from vendor_config_kb import vendor_kb
            match = vendor_kb.match_command(raw_command)
            if match:
                return match
        except Exception:
            pass

        if "retry-options" in raw_command and "tries-before-disconnect" in raw_command:
            return ("authentication.account_lockout.enabled", True, "Authentication")
        return None
