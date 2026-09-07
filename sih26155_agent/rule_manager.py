"""
Rule Management & Versioning Engine — SIH26155
=================================================
Manages custom security policies, versioning (v1, v2, ...), validation,
semantic conflict detection, multi-person approval gates, and automated re-audit.

CRITICAL ARCHITECTURAL BOUNDARY:
- Rules are declarative definitions evaluated ONLY by deterministic rule_engine.py.
- Version history is preserved; v1 is NEVER silently overwritten.
- Two distinct authorized reviewers must approve security-sensitive rule changes.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from rule_engine import RULES_FILE, evaluate_baseline, load_rules, resolve_evidence_field
from security_baseline_schema import ComplianceFinding, SecurityBaseline
from training_flow import resolve_expected_type


class ApprovalStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED_BY_ONE = "approved_by_one"
    APPROVED = "approved"
    ACTIVE = "active"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class RuleVersion:
    def __init__(
        self,
        rule_data: dict,
        version: int = 1,
        created_by: str = "system",
        rationale: str = "Initial baseline rule",
    ) -> None:
        self.rule_data = copy.deepcopy(rule_data)
        self.version = version
        self.created_by = created_by
        self.rationale = rationale
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.approvals: List[Dict[str, str]] = []  # [{"reviewer": name, "timestamp": iso, "role": role}]
        self.status = ApprovalStatus.ACTIVE if version == 1 else ApprovalStatus.PENDING_APPROVAL
        self.activated_at: Optional[str] = datetime.now(timezone.utc).isoformat() if version == 1 else None

    @property
    def rule_id(self) -> str:
        return self.rule_data["id"]

    def compute_hash(self) -> str:
        canonical = {
            "id": self.rule_data["id"],
            "version": self.version,
            "baseline_field_path": self.rule_data.get("baseline_field_path"),
            "evaluation": self.rule_data.get("evaluation"),
            "severity": self.rule_data.get("severity"),
            "framework": self.rule_data.get("framework"),
        }
        serialized = json.dumps(canonical, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "version": self.version,
            "title": self.rule_data.get("title", ""),
            "framework": self.rule_data.get("framework", "cis"),
            "severity": self.rule_data.get("severity", "medium"),
            "baseline_field_path": self.rule_data.get("baseline_field_path", ""),
            "evaluation": self.rule_data.get("evaluation", {}),
            "status": self.status.value,
            "created_by": self.created_by,
            "rationale": self.rationale,
            "created_at": self.created_at,
            "activated_at": self.activated_at,
            "approvals": self.approvals,
            "sha256_hash": self.compute_hash(),
            "rule_data": self.rule_data,
        }


class RuleManager:
    def __init__(self, rules_file: Path = RULES_FILE) -> None:
        self.rules_file = rules_file
        self._history: Dict[str, List[RuleVersion]] = {}
        self._load_initial_rules()

    def _load_initial_rules(self) -> None:
        initial_rules = load_rules(self.rules_file)
        for r in initial_rules:
            rv = RuleVersion(rule_data=r, version=1, created_by="system", rationale="Initial CIS Baseline")
            self._history[r["id"]] = [rv]

    def get_active_rules(self) -> List[dict]:
        """Returns the active rule dictionaries for the deterministic compliance engine."""
        active = []
        for rule_id, versions in self._history.items():
            for v in reversed(versions):
                if v.status == ApprovalStatus.ACTIVE:
                    active.append(v.rule_data)
                    break
        return active

    def get_rule_history(self, rule_id: str) -> List[dict]:
        versions = self._history.get(rule_id, [])
        return [v.to_dict() for v in versions]

    def get_all_rules_summary(self) -> List[dict]:
        summary = []
        for rule_id, versions in self._history.items():
            active_v = next((v for v in reversed(versions) if v.status == ApprovalStatus.ACTIVE), versions[-1])
            summary.append(active_v.to_dict())
        return summary

    def validate_rule(self, rule_data: dict) -> Tuple[bool, Optional[str]]:
        """Validates rule structure, baseline_field_path against the schema, and operator."""
        required_keys = ("id", "title", "framework", "severity", "baseline_field_path", "evaluation")
        for k in required_keys:
            if k not in rule_data:
                return False, f"Missing required field: {k}"

        field_path = rule_data["baseline_field_path"]
        try:
            expected_type = resolve_expected_type(field_path)
        except Exception as e:
            return False, f"Invalid baseline_field_path '{field_path}': {e}"

        eval_spec = rule_data.get("evaluation", {})
        if "operator" not in eval_spec or "expected" not in eval_spec:
            return False, "Evaluation must define 'operator' and 'expected'"

        valid_operators = (
            "equals", "not_equals", "in", "not_in",
            "greater_than_or_equal", "less_than_or_equal",
            "list_none_true", "list_all_true",
        )
        if eval_spec["operator"] not in valid_operators:
            return False, f"Unsupported operator '{eval_spec['operator']}'"

        return True, None

    def detect_conflicts(self, proposed_rule: dict) -> List[str]:
        """Checks if another active rule targets the same field with incompatible logic."""
        conflicts = []
        proposed_field = proposed_rule["baseline_field_path"]
        proposed_id = proposed_rule["id"]

        for active in self.get_active_rules():
            if active["id"] != proposed_id and active.get("baseline_field_path") == proposed_field:
                conflicts.append(
                    f"Conflict detected with active rule '{active['id']}': both evaluate '{proposed_field}'"
                )
        return conflicts

    def propose_rule_change(
        self,
        rule_id: str,
        updates: dict,
        proposed_by: str = "security_engineer",
        rationale: str = "",
    ) -> Tuple[bool, Optional[dict], Optional[str]]:
        """
        Creates a new version (e.g. v2) for rule_id without overwriting previous versions.
        """
        if rule_id not in self._history:
            return False, None, f"Rule '{rule_id}' not found"

        current_active = next(
            (v for v in reversed(self._history[rule_id]) if v.status == ApprovalStatus.ACTIVE),
            self._history[rule_id][-1],
        )

        new_rule_data = copy.deepcopy(current_active.rule_data)
        for k, v in updates.items():
            if k == "evaluation" and isinstance(v, dict):
                new_rule_data["evaluation"].update(v)
            else:
                new_rule_data[k] = v

        valid, err = self.validate_rule(new_rule_data)
        if not valid:
            return False, None, f"Rule validation failed: {err}"

        conflicts = self.detect_conflicts(new_rule_data)
        if conflicts:
            return False, None, "; ".join(conflicts)

        new_version_num = len(self._history[rule_id]) + 1
        new_v = RuleVersion(
            rule_data=new_rule_data,
            version=new_version_num,
            created_by=proposed_by,
            rationale=rationale or f"Updated policy from v{current_active.version}",
        )
        self._history[rule_id].append(new_v)
        return True, new_v.to_dict(), None

    def approve_rule(
        self,
        rule_id: str,
        version: int,
        reviewer_name: str,
        role: str = "security_lead",
    ) -> Tuple[bool, dict, Optional[str]]:
        """
        Enforces two-person approval.
        Reviewer A approves -> status becomes APPROVED_BY_ONE.
        Reviewer B (must be distinct from Reviewer A) approves -> status becomes APPROVED.
        """
        versions = self._history.get(rule_id, [])
        target_v = next((v for v in versions if v.version == version), None)
        if not target_v:
            return False, {}, f"Rule {rule_id} v{version} not found"

        if target_v.status == ApprovalStatus.ACTIVE:
            return False, target_v.to_dict(), "Rule is already active"

        # Ensure reviewer has not already approved this version
        existing_reviewers = [a["reviewer"] for a in target_v.approvals]
        if reviewer_name in existing_reviewers:
            return False, target_v.to_dict(), f"Reviewer '{reviewer_name}' has already approved this version"

        target_v.approvals.append({
            "reviewer": reviewer_name,
            "role": role,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        if len(target_v.approvals) == 1:
            target_v.status = ApprovalStatus.APPROVED_BY_ONE
        elif len(target_v.approvals) >= 2:
            target_v.status = ApprovalStatus.APPROVED

        return True, target_v.to_dict(), None

    def activate_rule(self, rule_id: str, version: int) -> Tuple[bool, dict, Optional[str]]:
        """
        Activates an approved rule.
        Fails if two approvals have not been obtained.
        Supersedes previous versions.
        """
        versions = self._history.get(rule_id, [])
        target_v = next((v for v in versions if v.version == version), None)
        if not target_v:
            return False, {}, f"Rule {rule_id} v{version} not found"

        if len(target_v.approvals) < 2:
            return (
                False,
                target_v.to_dict(),
                f"Two-person approval required. Currently has {len(target_v.approvals)}/2 approvals.",
            )

        # Supersede currently active version
        for v in versions:
            if v.status == ApprovalStatus.ACTIVE:
                v.status = ApprovalStatus.SUPERSEDED

        target_v.status = ApprovalStatus.ACTIVE
        target_v.activated_at = datetime.now(timezone.utc).isoformat()
        return True, target_v.to_dict(), None

    def re_audit_affected_devices(
        self,
        baselines: Dict[str, SecurityBaseline],
        rule_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Re-evaluates compliance of all devices against the active rules,
        returning before/after diffs for the affected rule.
        """
        active_rules = self.get_active_rules()
        rule_history = self._history.get(rule_id, [])
        if len(rule_history) < 2:
            prev_rule_data = rule_history[0].rule_data
        else:
            prev_rule_data = rule_history[-2].rule_data

        active_rule_data = next((r for r in active_rules if r["id"] == rule_id), None)
        if not active_rule_data:
            return []

        results = []
        for dev_id, baseline in baselines.items():
            finding_before = evaluate_baseline(baseline, [prev_rule_data])[0]
            finding_after = evaluate_baseline(baseline, [active_rule_data])[0]

            results.append({
                "device_id": dev_id,
                "rule_id": rule_id,
                "before_version": rule_history[-2].version if len(rule_history) >= 2 else 1,
                "before_status": finding_before.status.value,
                "before_expected": prev_rule_data["evaluation"]["expected"],
                "after_version": active_rule_data.get("version", len(rule_history)),
                "after_status": finding_after.status.value,
                "after_expected": active_rule_data["evaluation"]["expected"],
                "changed": finding_before.status != finding_after.status,
            })
        return results
