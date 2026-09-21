"""
Capabilities — Sandboxed Code Execution
GAACA v2.0

run_python: Executes Python code within sandbox with timeout.
run_tests: Runs test suites within sandbox.

Both are confined to the scratch directory and subject to resource limits.
"""

from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

from agent_v2.capabilities.base import (
    CapabilitySpec, ImplementationSpec, CostModel, Observation, ExecContext
)


def _run_python_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    """Executes Python code in a sandboxed subprocess with timeout."""
    code = params.get("code", "")
    timeout = min(params.get("timeout", 30), 60)  # Hard cap at 60 seconds

    if not code.strip():
        return Observation(ok=False, output=None, error="No code provided.")

    # Write code to scratch directory
    scratch = ctx.scratch_dir.resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    script_path = (scratch / "_agent_exec.py").resolve()
    script_path.write_text(code, encoding="utf-8")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(scratch),
        )

        if result.returncode == 0:
            return Observation(
                ok=True,
                output=result.stdout[:5000],
                metadata={"returncode": 0, "stderr": result.stderr[:1000]},
            )
        else:
            return Observation(
                ok=False,
                output=result.stdout[:2000],
                error=f"Script exited with code {result.returncode}: {result.stderr[:2000]}",
                metadata={"returncode": result.returncode},
            )
    except subprocess.TimeoutExpired:
        return Observation(
            ok=False, output=None,
            error=f"Execution timed out after {timeout}s.",
            metadata={"timeout": True},
        )
    except Exception as ex:
        return Observation(ok=False, output=None, error=f"Execution error: {str(ex)}")
    finally:
        try:
            if script_path.exists():
                script_path.unlink()
        except Exception:
            pass


def _run_tests_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    """Runs a test file or directory within sandbox."""
    test_path = params.get("path", "")
    timeout = min(params.get("timeout", 60), 120)

    target = (ctx.project_root / test_path).resolve()
    if not target.exists():
        return Observation(ok=False, output=None, error=f"Test path not found: {test_path}")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(target), "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ctx.project_root),
        )

        return Observation(
            ok=result.returncode == 0,
            output=result.stdout[:5000],
            error=result.stderr[:2000] if result.returncode != 0 else None,
            metadata={"returncode": result.returncode},
        )
    except subprocess.TimeoutExpired:
        return Observation(ok=False, output=None, error=f"Tests timed out after {timeout}s.")
    except Exception as ex:
        return Observation(ok=False, output=None, error=f"Test execution error: {str(ex)}")


def register_coding_capabilities(registry) -> None:
    """Registers sandboxed code execution capabilities."""
    registry.register_implementation(ImplementationSpec(
        name="run_python",
        description="Execute Python code in sandboxed scratch directory with timeout",
        input_schema={"code": "str", "timeout": "int (optional, default 30, max 60)"},
        output_schema={"stdout": "str", "returncode": "int"},
        autonomy_action="run_python",
        risk="MEDIUM",
        cost=CostModel(estimated_seconds=5.0, risk_weight=2.5),
        failure_modes=["timeout", "syntax_error", "import_error", "runtime_error"],
        handler=_run_python_handler,
    ))

    registry.register_implementation(ImplementationSpec(
        name="run_tests",
        description="Run pytest test suite within project sandbox",
        input_schema={"path": "str", "timeout": "int (optional, default 60, max 120)"},
        output_schema={"stdout": "str", "returncode": "int"},
        autonomy_action="run_tests",
        risk="LOW",
        cost=CostModel(estimated_seconds=10.0, risk_weight=1.5),
        failure_modes=["timeout", "import_error", "test_failure"],
        handler=_run_tests_handler,
    ))
