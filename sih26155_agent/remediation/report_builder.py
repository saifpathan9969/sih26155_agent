"""
Remediation Report Builder — GAACA v1
======================================
Generates enhanced audit reports including sandbox validation results,
before/after comparisons, and promotion status.

Extends the standard compliance report with a dedicated Remediation & Verification
section showing the full sandbox → validation → promotion pipeline.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from remediation.sandbox import SandboxSession


def build_remediation_section(session: SandboxSession, diff: Optional[str] = None) -> str:
    """
    Generate markdown for the Remediation & Verification section.

    Returns a formatted markdown string ready to be appended to the main report.
    """
    lines = [
        "## Remediation & Verification",
        "",
        f"**Configuration:** {session.filename}",
        f"**Session ID:** {session.session_id}",
        f"**Status:** {session.status.upper()}",
        f"**Created:** {session.created_at}",
        "",
    ]

    # Proposed fixes
    lines.append("### Proposed Remediation")
    lines.append("")
    if session.proposed_fixes:
        lines.append(f"**{len(session.proposed_fixes)} fix(es) proposed:**")
        lines.append("")
        for idx, fix in enumerate(session.proposed_fixes, 1):
            rule_id = fix.get("rule_id", "N/A")
            desc = fix.get("description", "No description")
            confidence = fix.get("confidence", 0.0)
            lines.append(f"{idx}. **{rule_id}** — {desc} (confidence: {confidence:.2f})")
        lines.append("")
    else:
        lines.append("*No fixes proposed*")
        lines.append("")

    # Sandbox validation results
    if session.validation_result:
        val = session.validation_result
        lines.append("### Sandbox Validation Results")
        lines.append("")

        # Overall status
        passed = val.get("passed", False)
        status_icon = "✓" if passed else "✗"
        lines.append(f"**Overall Status:** {status_icon} {'PASSED' if passed else 'FAILED'}")
        lines.append("")

        # Gates breakdown
        gates = val.get("gates", {})
        lines.append("#### Validation Gates")
        lines.append("")

        # Gate 1: Syntax
        syntax = gates.get("syntax_validation", {})
        syntax_passed = syntax.get("passed", False)
        lines.append(f"1. **Syntax Validation:** {'✓ PASS' if syntax_passed else '✗ FAIL'}")
        if not syntax_passed:
            errors = syntax.get("errors", [])
            for err in errors:
                lines.append(f"   - {err}")
        lines.append("")

        # Gate 2: Target Resolution
        target = gates.get("target_resolution", {})
        target_passed = target.get("passed", False)
        target_details = target.get("details", {})
        lines.append(f"2. **Target Resolution:** {'✓ PASS' if target_passed else '✗ FAIL'}")
        
        resolved = target_details.get("resolved", [])
        unresolved = target_details.get("unresolved", [])
        
        if resolved:
            lines.append(f"   - Resolved: {len(resolved)} violation(s)")
            for item in resolved[:5]:  # Show first 5
                rule = item.get("rule_id", "N/A")
                lines.append(f"     - {rule}: {item.get('original_status', 'FAIL')} → {item.get('candidate_status', 'PASS')}")
        
        if unresolved:
            lines.append(f"   - Unresolved: {len(unresolved)} violation(s) remain")
            for item in unresolved[:5]:
                rule = item.get("rule_id", "N/A")
                reason = item.get("reason", "Unknown")
                lines.append(f"     - {rule}: {reason}")
        lines.append("")

        # Gate 3: Regression Audit
        regression = gates.get("regression_audit", {})
        regression_passed = regression.get("passed", False)
        regression_details = regression.get("details", {})
        lines.append(f"3. **Regression Audit:** {'✓ PASS' if regression_passed else '✗ FAIL'}")
        
        before = regression_details.get("before", {})
        after = regression_details.get("after", {})
        regressions = regression_details.get("regressions", [])
        improvements = regression_details.get("improvements", [])
        
        lines.append(f"   - Before: {before.get('pass', 0)} PASS | {before.get('fail', 0)} FAIL")
        lines.append(f"   - After:  {after.get('pass', 0)} PASS | {after.get('fail', 0)} FAIL")
        
        if improvements:
            lines.append(f"   - Improvements: {len(improvements)} control(s)")
        
        if regressions:
            lines.append(f"   - **Regressions detected:** {len(regressions)} new failure(s)")
            for reg in regressions[:3]:
                rule = reg.get("rule_id", "N/A")
                severity = reg.get("severity", "UNKNOWN")
                lines.append(f"     - {rule} ({severity})")
        lines.append("")

        # Gate 4: Security Invariants
        invariants = gates.get("security_invariants", {})
        invariants_passed = invariants.get("passed", False)
        violations = invariants.get("violations", [])
        lines.append(f"4. **Security Invariants:** {'✓ PASS' if invariants_passed else '✗ FAIL'}")
        
        if violations:
            lines.append("   - Critical control violations:")
            for v in violations:
                lines.append(f"     - {v}")
        else:
            lines.append("   - All critical controls preserved")
        lines.append("")

        # Summary
        summary = val.get("summary", "")
        if summary:
            lines.append("#### Summary")
            lines.append("")
            lines.append(summary)
            lines.append("")

    # Configuration diff
    if diff:
        lines.append("### Configuration Changes")
        lines.append("")
        lines.append("```diff")
        # Limit diff to reasonable size
        diff_lines = diff.split("\n")
        if len(diff_lines) > 50:
            lines.extend(diff_lines[:50])
            lines.append(f"... ({len(diff_lines) - 50} more lines)")
        else:
            lines.extend(diff_lines)
        lines.append("```")
        lines.append("")

    # Promotion status
    if session.promoted_path:
        lines.append("### Promotion")
        lines.append("")
        lines.append(f"**Status:** ✓ PROMOTED")
        lines.append(f"**Promoted Path:** `{session.promoted_path}`")
        lines.append(f"**Promoted At:** {session.promoted_at}")
        lines.append("")
        lines.append("**Hashes:**")
        lines.append(f"- Original: `{session.original_hash}`")
        if session.candidate_hash:
            lines.append(f"- Candidate: `{session.candidate_hash}`")
        lines.append("")
    elif session.status == "passed":
        lines.append("### Promotion")
        lines.append("")
        lines.append("**Status:** Awaiting promotion")
        lines.append("*Candidate passed all validation gates and is ready for promotion.*")
        lines.append("")
    elif session.status == "failed":
        lines.append("### Promotion")
        lines.append("")
        lines.append("**Status:** ✗ BLOCKED")
        lines.append("*Candidate failed validation and cannot be promoted.*")
        lines.append("")

    # Final verdict section
    lines.append("### Final Result")
    lines.append("")
    if session.promoted_path:
        lines.append("**Outcome:** Configuration successfully remediated and promoted")
        lines.append("")
        lines.append("The fixed configuration has been validated and is available for deployment.")
    elif session.status == "passed":
        lines.append("**Outcome:** Remediation validated, pending promotion")
    elif session.status == "failed":
        lines.append("**Outcome:** Remediation validation failed")
        lines.append("")
        lines.append("Review the validation results above to identify the blocking issues.")
    else:
        lines.append(f"**Outcome:** Session status: {session.status}")

    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def build_multi_session_report(sessions: List[SandboxSession]) -> str:
    """
    Generate a comprehensive remediation report covering multiple sessions.

    Returns markdown suitable for PDF generation.
    """
    lines = [
        "# Remediation Report",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**Sessions:** {len(sessions)}",
        "",
        "---",
        "",
    ]

    # Summary statistics
    promoted = sum(1 for s in sessions if s.promoted_path)
    passed = sum(1 for s in sessions if s.status == "passed")
    failed = sum(1 for s in sessions if s.status == "failed")
    pending = len(sessions) - promoted - passed - failed

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Promoted:** {promoted}")
    lines.append(f"- **Validated (awaiting promotion):** {passed}")
    lines.append(f"- **Failed validation:** {failed}")
    lines.append(f"- **Pending:** {pending}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Individual session details
    for idx, session in enumerate(sessions, 1):
        lines.append(f"## Session {idx}: {session.filename}")
        lines.append("")
        section = build_remediation_section(session)
        lines.append(section)

    return "\n".join(lines)


def augment_compliance_report(
    base_report: str,
    session: Optional[SandboxSession] = None,
    diff: Optional[str] = None,
) -> str:
    """
    Add remediation section to an existing compliance report.

    Args:
        base_report: Existing markdown report
        session: Sandbox session to document
        diff: Configuration diff to include

    Returns:
        Enhanced report with remediation section appended
    """
    if not session:
        return base_report

    remediation_section = build_remediation_section(session, diff)

    # Insert before the final metadata/signature section if present
    if "## Audit Trail" in base_report or "---\n**Report Hash:" in base_report:
        parts = base_report.rsplit("## Audit Trail", 1)
        if len(parts) == 2:
            return parts[0] + remediation_section + "## Audit Trail" + parts[1]
        
        parts = base_report.rsplit("---\n**Report Hash:", 1)
        if len(parts) == 2:
            return parts[0] + remediation_section + "---\n**Report Hash:" + parts[1]

    # Otherwise append to end
    return base_report + "\n\n" + remediation_section


from datetime import datetime
