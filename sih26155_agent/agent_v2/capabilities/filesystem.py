"""
Capabilities — Filesystem (Read-Only & Search)
GAACA v2.0

Path-allowlisted inspection of project files with claw-code safety guards:
- Binary file detection (NUL-byte inspection in 8KB chunk)
- Canonical workspace boundary validation (symlink escape defense)
- File size guard limits (10MB MAX_READ_SIZE)
"""

from pathlib import Path
from typing import Any, Dict, Tuple

from agent_v2.capabilities.base import ImplementationSpec, Observation, ExecContext, CostModel
from agent_v2.capabilities.registry import CapabilityRegistry


# Maximum file size allowed for reading (10 MB)
MAX_READ_SIZE: int = 10 * 1024 * 1024

# Maximum file size allowed for writing (10 MB)
MAX_WRITE_SIZE: int = 10 * 1024 * 1024


def is_binary_file(path: Path) -> bool:
    """
    Examines the first 8KB of a file for NUL bytes to detect binary content
    (ported from claw-code file_ops.rs).
    """
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
            return b"\x00" in chunk
    except Exception:
        return False


def validate_workspace_boundary(target: Path, context: ExecContext) -> Tuple[bool, str]:
    """
    Canonicalizes path and validates that it remains strictly inside
    the project root or scratch sandbox, preventing symlink escapes.
    """
    try:
        canonical_target = target.resolve()
        canonical_root = context.project_root.resolve()
        canonical_scratch = context.scratch_dir.resolve()

        if canonical_target.is_relative_to(canonical_root) or canonical_target.is_relative_to(canonical_scratch):
            return True, ""
        return False, f"Access denied: path '{target}' escapes workspace boundary via traversal or symlink."
    except Exception as ex:
        return False, f"Path resolution error: {str(ex)}"


def handle_read_file(params: Dict[str, Any], context: ExecContext) -> Observation:
    path_str = params.get("path")
    if not path_str:
        return Observation(ok=False, output=None, error="Missing required parameter 'path'.")

    target = Path(path_str)
    if not target.is_absolute():
        target = context.project_root / target

    # Canonical workspace boundary validation (symlink escape defense)
    valid, err_msg = validate_workspace_boundary(target, context)
    if not valid:
        return Observation(ok=False, output=None, error=err_msg)

    if not target.exists() or not target.is_file():
        return Observation(ok=False, output=None, error=f"File not found: '{path_str}'")

    file_size = target.stat().st_size

    # Guard: Max read size limit
    if file_size > MAX_READ_SIZE:
        return Observation(
            ok=False,
            output=None,
            error=f"File size ({file_size} bytes) exceeds maximum allowable read limit of 10MB.",
            metadata={"size_bytes": file_size, "limit_bytes": MAX_READ_SIZE},
        )

    # Guard: Binary file detection
    if is_binary_file(target):
        return Observation(
            ok=True,
            output=f"[BINARY_FILE] '{target.name}' ({file_size} bytes). Binary content suppressed to preserve context.",
            metadata={"is_binary": True, "size_bytes": file_size, "path": str(target)},
        )

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        return Observation(
            ok=True,
            output=content[:10_000],
            raw_evidence=content[:1000],
            metadata={"size_bytes": len(content), "path": str(target), "is_binary": False},
        )
    except Exception as ex:
        return Observation(ok=False, output=None, error=f"Error reading file: {str(ex)}")


def handle_list_dir(params: Dict[str, Any], context: ExecContext) -> Observation:
    path_str = params.get("path", "")
    target = (context.project_root / path_str) if path_str else context.project_root

    valid, err_msg = validate_workspace_boundary(target, context)
    if not valid:
        return Observation(ok=False, output=None, error=err_msg)

    if not target.exists() or not target.is_dir():
        return Observation(ok=False, output=None, error=f"Directory not found: '{path_str}'")

    entries = [p.name for p in target.iterdir()][:50]
    return Observation(ok=True, output={"directory": str(target.resolve()), "entries": entries})


def register_filesystem_capabilities(registry: CapabilityRegistry):
    registry.register_implementation(ImplementationSpec(
        name="read_file",
        description="Reads plain text content of an authorized file with binary detection and size guards",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        output_schema={"type": "string"},
        autonomy_action="read_file",
        risk="LOW",
        cost=CostModel(estimated_seconds=0.1),
        handler=handle_read_file,
    ))

    registry.register_implementation(ImplementationSpec(
        name="list_dir",
        description="Lists entries inside an authorized directory with workspace boundary validation",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        output_schema={"type": "object"},
        autonomy_action="list_dir",
        risk="NONE",
        cost=CostModel(estimated_seconds=0.1),
        handler=handle_list_dir,
    ))
