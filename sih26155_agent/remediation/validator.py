"""
Remediation Validator — GAACA v1
=================================
Multi-gate validation of candidate configurations before promotion.

Validation pipeline:
    1. Syntax validation — config must parse without errors
    2. Target resolution — the violation that triggered remediation must be fixed
    3. Regression audit — no new failures introduced
    4. Security invariants — critical controls must not weaken

Only candidates passing all four gates proceed to promotion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from device_classifier import classify_device
from rule_engine import evaluate_baseline, load_rules
from security_baseline_schema import ComplianceFinding, VendorFamily
from tools.fingerprint import fingerprint_vendor
from tools.parsing import parse_config


def _is_fail(status) -> bool:
    """Normalize FindingStatus enum or string."""
    return str(status).lower() in ("fail", "findingstatus.fail")


def _is_pass(status) -> bool:
    """Normalize FindingStatus enum or string."""
    return str(status).lower() in ("pass", "findingstatus.pass")


@dataclass
class ValidationResult:
    """
    Outcome of validating a candidate configuration.

    Each gate reports pass/fail plus details. Only if all gates pass does
    the overall validation pass.
    """

    passed: bool
    syntax_valid: bool
    syntax_errors: List[str]
    target_resolved: bool
    target_details: Dict
    regression_clean: bool
    regression_details: Dict
    invariants_held: bool
    invariant_violations: List[str]
    summary: str

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "gates": {
                "syntax_validation": {
                    "passed": self.syntax_valid,
                    "errors": self.syntax_errors,
                },
                "target_resolution": {
                    "passed": self.target_resolved,
                    "details": self.target_details,
                },
                "regression_audit": {
                    "passed": self.regression_clean,
                    "details": self.regression_details,
                },
                "security_invariants": {
                    "passed": self.invariants_held,
                    "violations": self.invariant_violations,
                },
            },
            "summary": self.summary,
        }


class RemediationValidator:
    """
    Validates candidate configurations across four gates.

    Takes an original config, a candidate with proposed fixes, and the target
    findings. Returns a ValidationResult indicating whether the candidate can
    be promoted.
    """

    def __init__(self):
        self.rules = load_rules()
        # Critical controls that must never regress
        self._critical_rules = {
            "CIS-MGMT-01",  # Telnet disabled
            "CIS-MGMT-02",  # SSH v2 enabled
            "CIS-AUTH-01",  # Password encryption
            "CIS-AUTH-02",  # Account lockout
            "CIS-CRYPTO-01",  # Strong ciphers
        }

    def validate(
        self,
        original_text: str,
        candidate_text: str,
        original_filename: str,
        target_rule_ids: List[str],
        vendor: VendorFamily,
    ) -> ValidationResult:
        """
        Run the full validation pipeline on a candidate config.

        Args:
            original_text: Original configuration content
            candidate_text: Modified candidate configuration
            original_filename: Filename for classifier hints
            target_rule_ids: Rule IDs that remediation intended to fix
            vendor: Vendor family

        Returns:
            ValidationResult with pass/fail status for each gate
        """
        # Gate 1: Syntax validation
        syntax_valid, syntax_errors = self._validate_syntax(
            candidate_text, original_filename, vendor
        )
        if not syntax_valid:
            return ValidationResult(
                passed=False,
                syntax_valid=False,
                syntax_errors=syntax_errors,
                target_resolved=False,
                target_details={},
                regression_clean=False,
                regression_details={},
                invariants_held=False,
                invariant_violations=[],
                summary="Candidate failed syntax validation",
            )

        # Build baselines for comparison
        try:
            vendor_orig, _ = fingerprint_vendor(original_text)
            vendor_cand, _ = fingerprint_vendor(candidate_text)
            original_baseline, _ = parse_config(vendor_orig, original_text, original_filename)
            candidate_baseline, _ = parse_config(vendor_cand, candidate_text, original_filename)
        except Exception as e:
            return ValidationResult(
                passed=False,
                syntax_valid=True,
                syntax_errors=[],
                target_resolved=False,
                target_details={},
                regression_clean=False,
                regression_details={},
                invariants_held=False,
                invariant_violations=[],
                summary=f"Baseline construction failed: {e}",
            )

        # Evaluate both baselines
        original_findings = evaluate_baseline(original_baseline, self.rules)
        candidate_findings = evaluate_baseline(candidate_baseline, self.rules)

        # Gate 2: Target resolution
        target_resolved, target_details = self._check_target_resolution(
            original_findings, candidate_findings, target_rule_ids
        )

        # Gate 3: Regression audit
        regression_clean, regression_details = self._check_regressions(
            original_findings, candidate_findings
        )

        # Gate 4: Security invariants
        invariants_held, invariant_violations = self._check_invariants(
            original_findings, candidate_findings
        )

        # Overall pass requires all gates to pass
        passed = syntax_valid and target_resolved and regression_clean and invariants_held

        summary = self._build_summary(
            passed=passed,
            target_resolved=target_resolved,
            regression_clean=regression_clean,
            invariants_held=invariants_held,
            target_details=target_details,
            regression_details=regression_details,
        )

        return ValidationResult(
            passed=passed,
            syntax_valid=syntax_valid,
            syntax_errors=syntax_errors,
            target_resolved=target_resolved,
            target_details=target_details,
            regression_clean=regression_clean,
            regression_details=regression_details,
            invariants_held=invariants_held,
            invariant_violations=invariant_violations,
            summary=summary,
        )

    def _validate_syntax(
        self, config_text: str, filename: str, vendor: VendorFamily
    ) -> tuple[bool, List[str]]:
        """
        Gate 1: Verify the candidate config is syntactically valid.

        Currently uses the device classifier as a proxy — if it can parse the
        config and extract a profile, syntax is likely valid. A real deployment
        would invoke vendor-specific linters.
        """
        errors = []

        # Basic structural checks
        if not config_text.strip():
            errors.append("Configuration is empty")
            return False, errors

        # Attempt to classify — if it fails completely, syntax is broken
        try:
            profile = classify_device(config_text, filename)
            if profile.get("vendor") == "unknown" and len(config_text) > 100:
                # Large config that didn't parse suggests syntax issues
                errors.append("Configuration structure not recognized by parser")
                return False, errors
        except Exception as e:
            errors.append(f"Parse error: {str(e)}")
            return False, errors

        # Vendor-specific syntax checks
        vendor_name = vendor.value if hasattr(vendor, "value") else str(vendor)

        if "cisco" in vendor_name.lower():
            # Check for common Cisco syntax errors
            if "end" not in config_text.lower():
                errors.append("Cisco config missing 'end' statement")
            if config_text.count("{") != config_text.count("}"):
                errors.append("Unbalanced braces in config")

        elif "juniper" in vendor_name.lower():
            # Junos requires balanced braces
            if config_text.count("{") != config_text.count("}"):
                errors.append("Unbalanced braces in Junos config")
            if config_text.count("[") != config_text.count("]"):
                errors.append("Unbalanced brackets in Junos config")

        elif "fortinet" in vendor_name.lower():
            # FortiOS config/end blocks
            if "config " in config_text.lower():
                config_count = config_text.lower().count("config ")
                end_count = config_text.lower().count("\nend")
                if config_count > end_count:
                    errors.append("FortiOS config block missing 'end' statement")

        if errors:
            return False, errors

        return True, []

    def _check_target_resolution(
        self,
        original_findings: List[ComplianceFinding],
        candidate_findings: List[ComplianceFinding],
        target_rule_ids: List[str],
    ) -> tuple[bool, Dict]:
        """
        Gate 2: Verify that the violations remediation intended to fix are now resolved.

        A target finding must transition from FAIL → PASS (or at least to NOT_APPLICABLE
        if the control is no longer relevant). If any target remains FAIL, gate fails.
        """
        original_by_rule = {f.rule_id: f for f in original_findings}
        candidate_by_rule = {f.rule_id: f for f in candidate_findings}

        resolved = []
        unresolved = []

        for rule_id in target_rule_ids:
            original = original_by_rule.get(rule_id)
            candidate = candidate_by_rule.get(rule_id)

            if not original:
                # Target rule wasn't in original findings (shouldn't happen)
                unresolved.append(
                    {
                        "rule_id": rule_id,
                        "reason": "Target rule not found in original findings",
                    }
                )
                continue

            if not _is_fail(original.status):
                # Original wasn't failing (also shouldn't happen)
                resolved.append(
                    {
                        "rule_id": rule_id,
                        "original_status": str(original.status),
                        "candidate_status": str(candidate.status) if candidate else "MISSING",
                        "note": "Original was not failing",
                    }
                )
                continue

            # Original was FAIL — check if candidate fixed it
            if not candidate:
                unresolved.append(
                    {
                        "rule_id": rule_id,
                        "reason": "Rule not evaluated in candidate (baseline construction issue)",
                    }
                )
                continue

            if _is_pass(candidate.status):
                resolved.append(
                    {
                        "rule_id": rule_id,
                        "original_status": "FAIL",
                        "candidate_status": "PASS",
                        "fixed": True,
                    }
                )
            elif candidate.status == "NOT_APPLICABLE":
                # Control no longer applies — acceptable outcome
                resolved.append(
                    {
                        "rule_id": rule_id,
                        "original_status": "FAIL",
                        "candidate_status": "NOT_APPLICABLE",
                        "note": "Control no longer applicable",
                    }
                )
            else:
                unresolved.append(
                    {
                        "rule_id": rule_id,
                        "original_status": "FAIL",
                        "candidate_status": candidate.status,
                        "reason": "Violation still present after remediation",
                    }
                )

        details = {
            "target_count": len(target_rule_ids),
            "resolved": resolved,
            "unresolved": unresolved,
        }

        passed = len(unresolved) == 0

        return passed, details

    def _check_regressions(
        self,
        original_findings: List[ComplianceFinding],
        candidate_findings: List[ComplianceFinding],
    ) -> tuple[bool, Dict]:
        """
        Gate 3: Verify that no new failures were introduced.

        A regression is any rule that was PASS in original but became FAIL in
        candidate. The candidate may fix some controls, but must not break others.
        """
        original_by_rule = {f.rule_id: f for f in original_findings}
        candidate_by_rule = {f.rule_id: f for f in candidate_findings}

        regressions = []
        improvements = []

        for rule_id in set(original_by_rule.keys()) | set(candidate_by_rule.keys()):
            original = original_by_rule.get(rule_id)
            candidate = candidate_by_rule.get(rule_id)

            if not original or not candidate:
                continue

            # Check for regression: PASS → FAIL
            if _is_pass(original.status) and _is_fail(candidate.status):
                regressions.append(
                    {
                        "rule_id": rule_id,
                        "original_status": "PASS",
                        "candidate_status": "FAIL",
                        "severity": candidate.severity,
                    }
                )

            # Track improvements: FAIL → PASS
            elif _is_fail(original.status) and _is_pass(candidate.status):
                improvements.append(
                    {
                        "rule_id": rule_id,
                        "original_status": "FAIL",
                        "candidate_status": "PASS",
                    }
                )

        # Count summary
        original_pass = sum(1 for f in original_findings if _is_pass(f.status))
        original_fail = sum(1 for f in original_findings if _is_fail(f.status))
        candidate_pass = sum(1 for f in candidate_findings if _is_pass(f.status))
        candidate_fail = sum(1 for f in candidate_findings if _is_fail(f.status))

        details = {
            "before": {"pass": original_pass, "fail": original_fail},
            "after": {"pass": candidate_pass, "fail": candidate_fail},
            "regressions": regressions,
            "improvements": improvements,
        }

        passed = len(regressions) == 0

        return passed, details

    def _check_invariants(
        self,
        original_findings: List[ComplianceFinding],
        candidate_findings: List[ComplianceFinding],
    ) -> tuple[bool, List[str]]:
        """
        Gate 4: Verify that critical security controls were not weakened.

        Even if no regression occurred (PASS→FAIL), we check that critical
        controls like "telnet disabled" and "SSH v2 enabled" remain satisfied.
        This catches cases where a fix accidentally re-enables an insecure service.
        """
        violations = []

        candidate_by_rule = {f.rule_id: f for f in candidate_findings}

        for rule_id in self._critical_rules:
            finding = candidate_by_rule.get(rule_id)
            if not finding:
                # Critical rule not evaluated — treat as violation
                violations.append(
                    f"{rule_id}: Critical control not evaluated in candidate"
                )
                continue

            if _is_fail(finding.status):
                violations.append(
                    f"{rule_id}: Critical control failed in candidate "
                    f"(expected {finding.expected_value}, observed {finding.observed_value})"
                )

        passed = len(violations) == 0

        return passed, violations

    def _build_summary(
        self,
        passed: bool,
        target_resolved: bool,
        regression_clean: bool,
        invariants_held: bool,
        target_details: Dict,
        regression_details: Dict,
    ) -> str:
        """Generate a human-readable summary of validation outcome."""
        if passed:
            resolved_count = len(target_details.get("resolved", []))
            improved_count = len(regression_details.get("improvements", []))
            return (
                f"Validation passed. Resolved {resolved_count} target violation(s), "
                f"{improved_count} total improvement(s), no regressions."
            )

        parts = ["Validation failed:"]
        if not target_resolved:
            unresolved = target_details.get("unresolved", [])
            parts.append(f"  • {len(unresolved)} target violation(s) remain unfixed")
        if not regression_clean:
            regressions = regression_details.get("regressions", [])
            parts.append(f"  • {len(regressions)} new failure(s) introduced (regressions)")
        if not invariants_held:
            parts.append("  • Critical security invariants violated")

        return "\n".join(parts)
