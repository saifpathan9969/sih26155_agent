"""
Promotion Gate — GAACA v1 Remediation
======================================
Controls promotion of validated candidates to production output.

Only candidates passing all validation gates can be promoted. The gate records
the decision, rationale, and audit trail for compliance purposes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from remediation.validator import ValidationResult


class PromotionDecision(Enum):
    """Outcome of a promotion gate review."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"  # Needs human review before promotion


@dataclass
class PromotionRecord:
    """
    Audit record of a promotion decision.

    Stored alongside the promoted config for traceability.
    """

    session_id: str
    filename: str
    decision: PromotionDecision
    rationale: str
    decided_by: str  # username or "automatic"
    decided_at: str
    validation_summary: str
    original_hash: str
    candidate_hash: str
    promoted_hash: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "filename": self.filename,
            "decision": self.decision.value,
            "rationale": self.rationale,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at,
            "validation_summary": self.validation_summary,
            "original_hash": self.original_hash,
            "candidate_hash": self.candidate_hash,
            "promoted_hash": self.promoted_hash,
        }


class PromotionGate:
    """
    Decides whether a validated candidate configuration can be promoted.

    The gate implements the policy:
        - Validation must pass all four gates
        - High-severity regressions require human override
        - Critical rule failures always block promotion
    """

    def __init__(self):
        # Rules that require human approval even if validation passed
        self._human_review_triggers = {
            "critical_rule_modified",
            "high_severity_change",
            "unknown_vendor_syntax",
        }

    def evaluate(
        self,
        session_id: str,
        filename: str,
        validation_result: ValidationResult,
        original_hash: str,
        candidate_hash: str,
        requester: Optional[str] = None,
        force_approve: bool = False,
    ) -> PromotionRecord:
        """
        Evaluate whether a candidate can be promoted.

        Args:
            session_id: Sandbox session identifier
            filename: Original configuration filename
            validation_result: Outcome of validation pipeline
            original_hash: SHA-256 of original config
            candidate_hash: SHA-256 of candidate config
            requester: Username requesting promotion (None = automatic)
            force_approve: Human override to approve despite warnings

        Returns:
            PromotionRecord with decision and rationale
        """
        decided_by = requester or "automatic"
        decided_at = datetime.utcnow().isoformat()

        # If validation failed, promotion is blocked
        if not validation_result.passed:
            return PromotionRecord(
                session_id=session_id,
                filename=filename,
                decision=PromotionDecision.REJECTED,
                rationale=self._rejection_reason(validation_result),
                decided_by=decided_by,
                decided_at=decided_at,
                validation_summary=validation_result.summary,
                original_hash=original_hash,
                candidate_hash=candidate_hash,
            )

        # Check for conditions requiring human review
        needs_review, review_reason = self._check_human_review_needed(validation_result)

        if needs_review and not force_approve:
            return PromotionRecord(
                session_id=session_id,
                filename=filename,
                decision=PromotionDecision.DEFERRED,
                rationale=review_reason,
                decided_by=decided_by,
                decided_at=decided_at,
                validation_summary=validation_result.summary,
                original_hash=original_hash,
                candidate_hash=candidate_hash,
            )

        # All gates passed, approve for promotion
        rationale = self._approval_reason(validation_result, force_approve)

        return PromotionRecord(
            session_id=session_id,
            filename=filename,
            decision=PromotionDecision.APPROVED,
            rationale=rationale,
            decided_by=decided_by,
            decided_at=decided_at,
            validation_summary=validation_result.summary,
            original_hash=original_hash,
            candidate_hash=candidate_hash,
        )

    def _rejection_reason(self, validation_result: ValidationResult) -> str:
        """Generate rejection rationale from validation failures."""
        reasons = []

        if not validation_result.syntax_valid:
            error_count = len(validation_result.syntax_errors)
            reasons.append(f"Syntax validation failed ({error_count} error(s))")

        if not validation_result.target_resolved:
            unresolved = validation_result.target_details.get("unresolved", [])
            reasons.append(
                f"Target violations not resolved ({len(unresolved)} remain failing)"
            )

        if not validation_result.regression_clean:
            regressions = validation_result.regression_details.get("regressions", [])
            reasons.append(
                f"Regressions detected ({len(regressions)} new failure(s) introduced)"
            )

        if not validation_result.invariants_held:
            violations = validation_result.invariant_violations
            reasons.append(
                f"Security invariants violated ({len(violations)} critical control(s) weakened)"
            )

        return " | ".join(reasons)

    def _check_human_review_needed(
        self, validation_result: ValidationResult
    ) -> tuple[bool, str]:
        """
        Determine if human review is required despite validation passing.

        Returns (needs_review: bool, reason: str)
        """
        # Check if any critical rules were modified
        improvements = validation_result.regression_details.get("improvements", [])
        critical_changes = [
            imp
            for imp in improvements
            if imp["rule_id"].startswith("CIS-MGMT") or imp["rule_id"].startswith("CIS-AUTH")
        ]

        if critical_changes:
            return (
                True,
                f"Critical management/authentication controls modified "
                f"({len(critical_changes)} rule(s)). Human review required.",
            )

        # Check if target resolution had any notes requiring attention
        target_details = validation_result.target_details
        resolved = target_details.get("resolved", [])
        has_notes = any("note" in item for item in resolved)

        if has_notes:
            return (
                True,
                "Target resolution included edge cases. Human review recommended.",
            )

        return False, ""

    def _approval_reason(
        self, validation_result: ValidationResult, force_approve: bool
    ) -> str:
        """Generate approval rationale."""
        target_count = validation_result.target_details.get("target_count", 0)
        improvements = len(
            validation_result.regression_details.get("improvements", [])
        )

        parts = [
            f"All validation gates passed.",
            f"Resolved {target_count} target violation(s).",
            f"{improvements} total control(s) improved.",
            "No regressions detected.",
        ]

        if force_approve:
            parts.append("Human override applied.")

        return " ".join(parts)

    def can_auto_promote(self, validation_result: ValidationResult) -> bool:
        """
        Quick check: can this candidate be promoted automatically without human review?

        Returns True only if validation passed AND no human-review triggers fired.
        """
        if not validation_result.passed:
            return False

        needs_review, _ = self._check_human_review_needed(validation_result)
        return not needs_review
