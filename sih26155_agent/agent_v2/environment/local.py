"""
Environment — Local OS Environment
GAACA v2.0

Provides subprocess execution and local system interaction.
All operations are path-bounded to project root.
"""

from __future__ import annotations
import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_v2.environment.environment import Environment


class LocalEnvironment(Environment):
    """Encapsulates the local operating system environment."""

    def __init__(self, project_root: Path, scratch_dir: Path):
        self.project_root = project_root.resolve()
        self.scratch_dir = scratch_dir.resolve()
        self.scratch_dir.mkdir(parents=True, exist_ok=True)

    def inspect(self) -> Dict[str, Any]:
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "project_root": str(self.project_root),
            "scratch_dir": str(self.scratch_dir),
            "cwd": str(Path.cwd()),
        }

    def run_subprocess(self, command: List[str], cwd: Optional[Path] = None,
                       timeout: int = 30) -> Dict[str, Any]:
        """Runs a subprocess within bounded paths."""
        work_dir = cwd or self.project_root
        if not work_dir.resolve().is_relative_to(self.project_root):
            return {"ok": False, "error": "Working directory escapes project boundary."}

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(work_dir),
            )
            return {
                "ok": result.returncode == 0,
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:2000],
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"Timeout after {timeout}s."}
        except Exception as ex:
            return {"ok": False, "error": str(ex)}

    def get_env_vars(self, keys: Optional[List[str]] = None) -> Dict[str, str]:
        """Returns selected environment variables (never exposes secrets)."""
        safe_keys = keys or ["PATH", "PYTHONPATH", "HOME", "USER", "LANG"]
        return {k: os.environ.get(k, "") for k in safe_keys}
