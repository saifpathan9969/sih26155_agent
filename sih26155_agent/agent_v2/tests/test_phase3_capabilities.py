"""
Tests — Phase 3 Capabilities Verification Suite
GAACA v2.0

Verifies all internal agent capabilities:
- Coding: Sandboxed Python execution and test running
- Shell: Safety gating (NEVER_AUTONOMOUS) and dangerous pattern blocking
- Git: Read-only autonomous inspection vs gated commit
- Documents: Markdown and report generation
- Data: CSV/JSON/YAML dataset loading, statistical analysis, and summarization
- Communication: Human inquiry and approval requests
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "agent_v2"))

from agent_v2.capabilities.base import ExecContext
from agent_v2.capabilities.registry import CapabilityRegistry
from agent_v2.capabilities.coding import register_coding_capabilities
from agent_v2.capabilities.shell import register_shell_capabilities
from agent_v2.capabilities.git import register_git_capabilities
from agent_v2.capabilities.documents import register_document_capabilities
from agent_v2.capabilities.data import register_data_capabilities
from agent_v2.capabilities.communication import register_communication_capabilities
from agent_v2.safety.budgets import ResourceLedger
from agent_v2.safety.approval import ApprovalManager
from agent_v2.mind.world_model import WorldModel


def _build_test_context(project_root: Path, scratch_dir: Path) -> ExecContext:
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return ExecContext(
        run_id="test_phase3_run",
        project_root=project_root,
        scratch_dir=scratch_dir,
        budgets=ResourceLedger(max_cycles=10),
        approval_manager=ApprovalManager(),
        world_model=WorldModel(),
    )


def test_coding_capabilities():
    reg = CapabilityRegistry()
    register_coding_capabilities(reg)
    ctx = _build_test_context(_PROJECT_ROOT, _PROJECT_ROOT / "agent_v2" / "scratch")

    # 1. Run Python code in sandbox
    code = "x = [i**2 for i in range(5)]\nprint('RESULT:', sum(x))"
    obs = reg.execute("run_python", {"code": code, "timeout": 5}, ctx)
    assert obs.ok is True
    assert "RESULT: 30" in str(obs.output)

    # 2. Timeout protection
    infinite_loop = "while True: pass"
    obs_timeout = reg.execute("run_python", {"code": infinite_loop, "timeout": 1}, ctx)
    assert obs_timeout.ok is False
    assert "timed out" in str(obs_timeout.error).lower() or obs_timeout.metadata.get("timeout") is True


def test_shell_safety_and_blocking():
    reg = CapabilityRegistry()
    register_shell_capabilities(reg)
    ctx = _build_test_context(_PROJECT_ROOT, _PROJECT_ROOT / "agent_v2" / "scratch")

    # Shell requires human approval by default
    # Without approval callback, it must fail cleanly
    obs = reg.execute("run_shell", {"command": "echo 'hello'"}, ctx)
    assert obs.ok is False
    assert "human approval" in str(obs.error).lower()

    # Dangerous command blocking
    # Even if approved, dangerous patterns are blocked
    ctx_approved = ExecContext(
        run_id="test_phase3_run",
        project_root=_PROJECT_ROOT,
        scratch_dir=_PROJECT_ROOT / "agent_v2" / "scratch",
        budgets=ResourceLedger(max_cycles=10),
        approval_manager=ApprovalManager(callback=lambda req: True),
        world_model=WorldModel(),
    )
    obs_dangerous = reg.execute("run_shell", {"command": "rm -rf /"}, ctx_approved)
    assert obs_dangerous.ok is False
    assert "command blocked" in str(obs_dangerous.error).lower() and "dangerous" in str(obs_dangerous.error).lower()


def test_git_operations():
    reg = CapabilityRegistry()
    register_git_capabilities(reg)
    test_repo_dir = _PROJECT_ROOT / "agent_v2" / "scratch" / "test_git_repo"
    test_repo_dir.mkdir(parents=True, exist_ok=True)
    import subprocess
    subprocess.run(["git", "init"], cwd=str(test_repo_dir), capture_output=True)

    ctx_git = ExecContext(
        run_id="test_git_run",
        project_root=test_repo_dir,
        scratch_dir=test_repo_dir,
        budgets=ResourceLedger(max_cycles=10),
        approval_manager=ApprovalManager(),
        world_model=WorldModel(),
    )

    # git_status (autonomous read-only)
    obs_status = reg.execute("git_status", {}, ctx_git)
    assert obs_status.ok is True

    # git_commit (requires human approval)
    obs_commit = reg.execute("git_commit", {"message": "auto commit test"}, ctx_git)
    assert obs_commit.ok is False
    assert "human approval" in str(obs_commit.error).lower()


def test_document_generation():
    reg = CapabilityRegistry()
    register_document_capabilities(reg)
    ctx = _build_test_context(_PROJECT_ROOT, _PROJECT_ROOT / "agent_v2" / "scratch")

    obs = reg.execute("generate_markdown", {
        "title": "CIS Compliance Audit Report",
        "sections": [
            {"heading": "Executive Summary", "content": "12 devices evaluated."},
            {"heading": "Recommendations", "content": "Enforce SSHv2 and disable Telnet."},
        ],
        "filename": "audit_summary_test.md",
    }, ctx)

    assert obs.ok is True
    assert "CIS Compliance Audit Report" in str(obs.output)
    output_file = ctx.scratch_dir / "audit_summary_test.md"
    assert output_file.exists()
    assert "Enforce SSHv2" in output_file.read_text(encoding="utf-8")


def test_data_analysis():
    reg = CapabilityRegistry()
    register_data_capabilities(reg)
    ctx = _build_test_context(_PROJECT_ROOT, _PROJECT_ROOT / "agent_v2" / "scratch")

    # Load dataset (YAML)
    obs_load = reg.execute("load_dataset", {"path": "cis_rules.yaml"}, ctx)
    assert obs_load.ok is True
    assert obs_load.metadata.get("records") is not None

    # Analyze data
    sample_data = [
        {"vendor": "cisco_ios", "score": 90},
        {"vendor": "cisco_ios", "score": 80},
        {"vendor": "fortigate", "score": 95},
    ]
    obs_analysis = reg.execute("analyze_data", {"data": sample_data, "field": "score"}, ctx)
    assert obs_analysis.ok is True
    stats = obs_analysis.output.get("score_stats", {})
    assert stats.get("count") == 3
    assert stats.get("mean") == 88.3333

    # Summarize stats
    obs_summary = reg.execute("summarize_stats", {"data": stats, "title": "Score Analysis"}, ctx)
    assert obs_summary.ok is True
    assert "Score Analysis" in str(obs_summary.output)


def test_communication_capabilities():
    reg = CapabilityRegistry()
    register_communication_capabilities(reg)
    ctx = _build_test_context(_PROJECT_ROOT, _PROJECT_ROOT / "agent_v2" / "scratch")

    # ask_human
    obs_ask = reg.execute("ask_human", {"question": "Confirm remediation action?", "urgency": "NORMAL"}, ctx)
    assert obs_ask.ok is True
    assert "[OPERATOR_INPUT_REQUESTED]" in str(obs_ask.output)


if __name__ == "__main__":
    print("Running Phase 3 Capabilities Verification Suite...")
    test_coding_capabilities()
    print("[PASS] Coding capabilities passed")
    test_shell_safety_and_blocking()
    print("[PASS] Shell safety and dangerous command blocking passed")
    test_git_operations()
    print("[PASS] Git operations (autonomous vs human-gated) passed")
    test_document_generation()
    print("[PASS] Document generation passed")
    test_data_analysis()
    print("[PASS] Data analysis capabilities passed")
    test_communication_capabilities()
    print("[PASS] Communication capabilities passed")
    print("\nALL PHASE 3 CAPABILITIES TESTS PASSED SUCCESSFULLY.")
