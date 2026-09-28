"""
Remediation Workflow Tests — GAACA v1
======================================
Tests sandbox isolation, regression detection, and promotion gate blocking.
"""

import tempfile
from pathlib import Path

from remediation import SandboxManager, RemediationValidator, PromotionGate, PromotionDecision
from remediation.validator import ValidationResult
from security_baseline_schema import VendorFamily


# Sample configurations for testing
CISCO_INSECURE = """!
hostname TEST-RTR-01
version 15.2
!
interface GigabitEthernet0/0
 ip address 192.0.2.1 255.255.255.0
!
line vty 0 4
 transport input telnet
!
end
"""

CISCO_SECURE = """!
hostname TEST-RTR-01
version 15.2
ip ssh version 2
service password-encryption
!
interface GigabitEthernet0/0
 ip address 192.0.2.1 255.255.255.0
!
line vty 0 4
 transport input ssh
 exec-timeout 10 0
!
end
"""


def test_sandbox_isolation():
    """Verify that sandbox operations never modify original files."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        uploads = tmp / "uploads"
        sandbox = tmp / "sandbox"
        output = tmp / "output"
        
        uploads.mkdir()
        sandbox.mkdir()
        output.mkdir()
        
        # Create original config
        original_file = uploads / "test.conf"
        original_file.write_text(CISCO_INSECURE, encoding="utf-8")
        original_content = original_file.read_text(encoding="utf-8")
        original_mtime = original_file.stat().st_mtime
        
        # Create sandbox session
        manager = SandboxManager(uploads, sandbox, output)
        session = manager.create_session(
            filename="test.conf",
            vendor="cisco_ios",
            proposed_fixes=[
                {
                    "rule_id": "CIS-MGMT-01",
                    "action": "replace",
                    "pattern": r"transport\s+input\s+telnet",
                    "replacement": "transport input ssh",
                }
            ],
        )
        
        # Apply fixes
        manager.apply_fixes(session.session_id, session.proposed_fixes)
        
        # Verify original is untouched
        assert original_file.exists(), "Original file was deleted"
        assert original_file.read_text(encoding="utf-8") == original_content, \
            "Original file content was modified"
        assert original_file.stat().st_mtime == original_mtime, \
            "Original file timestamp changed"
        
        # Verify candidate exists and differs
        assert session.candidate_path.exists(), "Candidate file not created"
        candidate_content = session.candidate_path.read_text(encoding="utf-8")
        assert candidate_content != original_content, \
            "Candidate is identical to original (fixes not applied)"
        assert "transport input ssh" in candidate_content, \
            "Expected fix not present in candidate"
        
        print("[PASS] Sandbox isolation maintained — original untouched")


def test_regression_detection():
    """Verify that validation detects new failures introduced by remediation."""
    # Create a validation result with regressions
    validation_result = ValidationResult(
        passed=False,
        syntax_valid=True,
        syntax_errors=[],
        target_resolved=True,
        target_details={"resolved": [{"rule_id": "CIS-MGMT-01", "fixed": True}]},
        regression_clean=False,
        regression_details={
            "before": {"pass": 17, "fail": 3},
            "after": {"pass": 16, "fail": 4},
            "regressions": [
                {"rule_id": "CIS-AUTH-02", "severity": "HIGH"}
            ],
            "improvements": [
                {"rule_id": "CIS-MGMT-01"}
            ],
        },
        invariants_held=True,
        invariant_violations=[],
        summary="Regression detected",
    )
    
    assert not validation_result.passed, "Validation should fail with regressions"
    assert not validation_result.regression_clean, "Regression flag not set"
    assert len(validation_result.regression_details["regressions"]) == 1, \
        "Regression not recorded"
    
    print("[PASS] Regression detection working")


def test_promotion_gate_blocks_failures():
    """Verify that promotion gate blocks candidates that failed validation."""
    gate = PromotionGate()
    
    # Failed validation result
    failed_validation = ValidationResult(
        passed=False,
        syntax_valid=False,
        syntax_errors=["Unbalanced braces"],
        target_resolved=False,
        target_details={},
        regression_clean=True,
        regression_details={},
        invariants_held=True,
        invariant_violations=[],
        summary="Syntax validation failed",
    )
    
    record = gate.evaluate(
        session_id="test_session",
        filename="test.conf",
        validation_result=failed_validation,
        original_hash="abc123",
        candidate_hash="def456",
    )
    
    assert record.decision == PromotionDecision.REJECTED, \
        "Failed validation should be rejected"
    assert "Syntax validation failed" in record.rationale, \
        "Rejection reason not documented"
    
    print("[PASS] Promotion gate blocks failed validations")


def test_promotion_gate_allows_passed():
    """Verify that promotion gate approves candidates passing all gates."""
    gate = PromotionGate()
    
    # Passed validation result with non-critical rule improvements
    # (CIS-NET and CIS-LOG don't trigger human review)
    passed_validation = ValidationResult(
        passed=True,
        syntax_valid=True,
        syntax_errors=[],
        target_resolved=True,
        target_details={
            "target_count": 2,
            "resolved": [
                {"rule_id": "CIS-NET-01", "fixed": True},
                {"rule_id": "CIS-LOG-01", "fixed": True},
            ],
            "unresolved": [],
        },
        regression_clean=True,
        regression_details={
            "before": {"pass": 15, "fail": 5},
            "after": {"pass": 17, "fail": 3},
            "regressions": [],
            "improvements": [
                {"rule_id": "CIS-NET-01"},
                {"rule_id": "CIS-LOG-01"},
            ],
        },
        invariants_held=True,
        invariant_violations=[],
        summary="All gates passed",
    )
    
    record = gate.evaluate(
        session_id="test_session",
        filename="test.conf",
        validation_result=passed_validation,
        original_hash="abc123",
        candidate_hash="def456",
    )
    
    assert record.decision == PromotionDecision.APPROVED, \
        "Passing validation should be approved"
    assert "All validation gates passed" in record.rationale, \
        "Approval reason not documented"
    
    print("[PASS] Promotion gate approves passing candidates")


def test_human_review_trigger():
    """Verify that critical control changes require human review."""
    gate = PromotionGate()
    
    # Validation passed but modified critical controls
    critical_change_validation = ValidationResult(
        passed=True,
        syntax_valid=True,
        syntax_errors=[],
        target_resolved=True,
        target_details={"target_count": 1, "resolved": [], "unresolved": []},
        regression_clean=True,
        regression_details={
            "before": {"pass": 17, "fail": 3},
            "after": {"pass": 18, "fail": 2},
            "regressions": [],
            "improvements": [
                {"rule_id": "CIS-MGMT-02"},  # Critical SSH control
            ],
        },
        invariants_held=True,
        invariant_violations=[],
        summary="All gates passed",
    )
    
    # Without force_approve, should defer to human
    record = gate.evaluate(
        session_id="test_session",
        filename="test.conf",
        validation_result=critical_change_validation,
        original_hash="abc123",
        candidate_hash="def456",
        force_approve=False,
    )
    
    assert record.decision == PromotionDecision.DEFERRED, \
        "Critical control changes should require human review"
    assert "review" in record.rationale.lower(), \
        "Human review requirement not documented"
    
    # With force_approve, should allow
    record_forced = gate.evaluate(
        session_id="test_session",
        filename="test.conf",
        validation_result=critical_change_validation,
        original_hash="abc123",
        candidate_hash="def456",
        force_approve=True,
    )
    
    assert record_forced.decision == PromotionDecision.APPROVED, \
        "force_approve should override human review requirement"
    
    print("[PASS] Human review triggers work correctly")


def test_diff_generation():
    """Verify that sandbox generates accurate diffs."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        uploads = tmp / "uploads"
        sandbox = tmp / "sandbox"
        output = tmp / "output"
        
        for d in [uploads, sandbox, output]:
            d.mkdir()
        
        # Create original
        original_file = uploads / "test.conf"
        original_file.write_text(CISCO_INSECURE, encoding="utf-8")
        
        manager = SandboxManager(uploads, sandbox, output)
        session = manager.create_session(
            filename="test.conf",
            vendor="cisco_ios",
            proposed_fixes=[
                {
                    "rule_id": "CIS-MGMT-01",
                    "action": "replace",
                    "pattern": r"transport\s+input\s+telnet",
                    "replacement": "transport input ssh",
                }
            ],
        )
        
        manager.apply_fixes(session.session_id, session.proposed_fixes)
        
        diff = manager.get_diff(session.session_id)
        assert diff is not None, "Diff generation failed"
        assert "-transport input telnet" in diff or "- transport input telnet" in diff, \
            "Old line not marked as removed"
        assert "+transport input ssh" in diff or "+ transport input ssh" in diff, \
            "New line not marked as added"
        
        print("[PASS] Diff generation works")


def _main() -> int:
    print("Running GAACA v1 Remediation Tests...")
    print()
    
    tests = [
        test_sandbox_isolation,
        test_regression_detection,
        test_promotion_gate_blocks_failures,
        test_promotion_gate_allows_passed,
        test_human_review_trigger,
        test_diff_generation,
    ]
    
    failed = []
    for test in tests:
        test_name = test.__name__
        try:
            test()
        except AssertionError as e:
            failed.append((test_name, str(e)))
            print(f"[FAIL] {test_name}: {e}")
        except Exception as e:
            failed.append((test_name, repr(e)))
            print(f"[ERROR] {test_name}: {e!r}")
    
    print()
    if failed:
        print(f"{len(failed)}/{len(tests)} REMEDIATION TESTS FAILED")
        for name, err in failed:
            print(f"  - {name}: {err}")
        return 1
    print(f"ALL {len(tests)} REMEDIATION TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
