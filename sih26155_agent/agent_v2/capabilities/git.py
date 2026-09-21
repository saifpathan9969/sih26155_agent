"""
Capabilities — Git Operations
GAACA v2.0

git_status: Read-only (AUTONOMOUS)
git_diff: Read-only (AUTONOMOUS)
git_commit: REQUIRES_HUMAN — never auto-commit
"""

from __future__ import annotations
import subprocess
from typing import Dict, Any

from agent_v2.capabilities.base import (
    ImplementationSpec, CostModel, Observation, ExecContext
)


def _run_git(args: list, ctx: ExecContext, timeout: int = 15) -> Observation:
    """Helper: runs a git subcommand within the project root."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ctx.project_root),
        )
        return Observation(
            ok=result.returncode == 0,
            output=result.stdout[:5000],
            error=result.stderr[:1000] if result.returncode != 0 else None,
            metadata={"returncode": result.returncode, "git_args": args},
        )
    except FileNotFoundError:
        return Observation(ok=False, output=None, error="Git is not installed or not in PATH.")
    except subprocess.TimeoutExpired:
        return Observation(ok=False, output=None, error=f"Git command timed out after {timeout}s.")
    except Exception as ex:
        return Observation(ok=False, output=None, error=f"Git error: {str(ex)}")


def _git_status_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    return _run_git(["status", "--porcelain"], ctx)


def _git_diff_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    target = params.get("target", "HEAD")
    return _run_git(["diff", target, "--stat"], ctx)


def _git_commit_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    """Commits staged changes. REQUIRES_HUMAN approval via policy."""
    message = params.get("message", "Agent commit")
    add_all = params.get("add_all", False)

    if add_all:
        obs = _run_git(["add", "-A"], ctx)
        if not obs.ok:
            return obs

    return _run_git(["commit", "-m", message], ctx)


def register_git_capabilities(registry) -> None:
    """Registers git operations with appropriate autonomy levels."""
    registry.register_implementation(ImplementationSpec(
        name="git_status",
        description="Show working tree status (read-only)",
        input_schema={},
        output_schema={"status": "str"},
        autonomy_action="git_status",
        risk="NONE",
        cost=CostModel(estimated_seconds=0.5),
        handler=_git_status_handler,
    ))

    registry.register_implementation(ImplementationSpec(
        name="git_diff",
        description="Show changes between commits/working tree (read-only)",
        input_schema={"target": "str (optional, default HEAD)"},
        output_schema={"diff": "str"},
        autonomy_action="git_diff",
        risk="NONE",
        cost=CostModel(estimated_seconds=0.5),
        handler=_git_diff_handler,
    ))

    registry.register_implementation(ImplementationSpec(
        name="git_commit",
        description="Commit staged changes (REQUIRES human approval)",
        input_schema={"message": "str", "add_all": "bool (optional)"},
        output_schema={"commit_output": "str"},
        autonomy_action="git_commit",
        risk="MEDIUM",
        cost=CostModel(estimated_seconds=1.0, risk_weight=3.0),
        failure_modes=["nothing_to_commit", "merge_conflict"],
        handler=_git_commit_handler,
    ))
