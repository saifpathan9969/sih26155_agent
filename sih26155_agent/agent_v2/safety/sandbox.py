"""
Safety & Governance — Sandbox & Filesystem Confinement
GAACA v2.0

Enforces path containment, prevents path traversal, isolates scratch directories,
and detects writes directed at the immutable compliance core.
"""

from pathlib import Path
from typing import Tuple

COMPLIANCE_CORE_FILES = {
    "cis_rules.yaml",
    "security_baseline_schema.py",
    "rule_engine.py",
}


class SandboxManager:
    def __init__(self, project_root: Path, scratch_dir: Path):
        self.project_root = project_root.resolve()
        self.scratch_dir = scratch_dir.resolve()
        self.scratch_dir.mkdir(parents=True, exist_ok=True)

    def is_path_safe(self, target_path: str | Path) -> Tuple[bool, str]:
        """
        Validates whether target path is within project root or scratch dir.
        Returns (is_safe, error_reason).
        """
        resolved = Path(target_path).resolve()
        # Allow inside project root or scratch dir
        if not (resolved.is_relative_to(self.project_root) or resolved.is_relative_to(self.scratch_dir)):
            return False, f"Path '{target_path}' is outside the authorized project root or sandbox."
        return True, ""

    def is_compliance_core(self, target_path: str | Path) -> bool:
        """Checks whether the file is part of the protected compliance core."""
        filename = Path(target_path).name.lower()
        return filename in COMPLIANCE_CORE_FILES

    def classify_write_action(self, target_path: str | Path) -> str:
        """
        Determines the appropriate autonomy action string for a file write:
        - 'write_compliance_core' if targeting compliance engine files (NEVER_AUTONOMOUS)
        - 'write_scratch' if inside the scratch sandbox (AUTONOMOUS)
        - 'write_file' if targeting normal project files (AUTONOMOUS_ABOVE_THRESHOLD)
        """
        resolved = Path(target_path).resolve()
        if self.is_compliance_core(resolved):
            return "write_compliance_core"
        if resolved.is_relative_to(self.scratch_dir):
            return "write_scratch"
        return "write_file"
