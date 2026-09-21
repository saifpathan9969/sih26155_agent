from __future__ import annotations
import subprocess
import sys
import shlex
from enum import Enum
from typing import Dict, Any, Tuple, List

from agent_v2.capabilities.base import (
    ImplementationSpec, CostModel, Observation, ExecContext
)


class CommandIntent(str, Enum):
    READ_ONLY = "read_only"
    WRITE = "write"
    DESTRUCTIVE = "destructive"
    NETWORK = "network"
    PROCESS_MANAGEMENT = "process_management"
    PACKAGE_MANAGEMENT = "package_management"
    SYSTEM_ADMIN = "system_admin"
    UNKNOWN = "unknown"


class ValidationResult(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"


# Commands mapping to read-only intent
_READ_ONLY_CMDS = {
    "ls", "dir", "cat", "type", "head", "tail", "more", "less",
    "grep", "findstr", "find", "awk", "sed", "wc", "sort", "uniq",
    "pwd", "cd", "echo", "printf", "diff", "fc", "file", "which", "where",
    "git status", "git diff", "git log", "git show", "stat", "env", "printenv",
}

# Commands mapping to write intent
_WRITE_CMDS = {
    "cp", "copy", "mv", "move", "mkdir", "md", "touch", "tee",
    "ln", "tar", "zip", "unzip", "gzip", "gunzip",
}

# Commands mapping to destructive intent
_DESTRUCTIVE_CMDS = {
    "rm", "del", "erase", "rmdir", "rd", "shred", "truncate", "mkfs", "format", "dd",
}

# Commands mapping to network intent
_NETWORK_CMDS = {
    "curl", "wget", "ssh", "scp", "sftp", "ftp", "nc", "netcat",
    "nmap", "ping", "traceroute", "tracert", "telnet", "nslookup", "dig",
}

# Commands mapping to process management
_PROCESS_CMDS = {
    "kill", "pkill", "killall", "taskkill", "ps", "tasklist", "top", "htop",
}

# Commands mapping to package management
_PACKAGE_CMDS = {
    "pip", "pip3", "npm", "npx", "yarn", "pnpm", "cargo", "apt", "apt-get",
    "dpkg", "yum", "dnf", "pacman", "brew", "choco", "winget",
}

# Commands mapping to system administration
_ADMIN_CMDS = {
    "sudo", "su", "chmod", "chown", "chgrp", "mount", "umount",
    "systemctl", "service", "init", "reboot", "shutdown", "iptables",
}


def classify_command_intent(command: str) -> CommandIntent:
    """
    Semantically classifies command intent (inspired by claw-code bash_validation).
    """
    cmd_strip = command.strip()
    cmd_lower = cmd_strip.lower()

    # Check composite prefixes (e.g. git status, git diff)
    for prefix in ("git status", "git diff", "git log", "git show"):
        if cmd_lower.startswith(prefix):
            return CommandIntent.READ_ONLY

    # Extract primary command token
    tokens = cmd_lower.split()
    if not tokens:
        return CommandIntent.UNKNOWN

    primary = tokens[0]
    # Remove path prefixes if any (e.g. /bin/ls -> ls)
    if "/" in primary:
        primary = primary.split("/")[-1]
    if "\\" in primary:
        primary = primary.split("\\")[-1]

    if primary in _READ_ONLY_CMDS:
        return CommandIntent.READ_ONLY
    if primary in _WRITE_CMDS:
        return CommandIntent.WRITE
    if primary in _DESTRUCTIVE_CMDS:
        return CommandIntent.DESTRUCTIVE
    if primary in _NETWORK_CMDS:
        return CommandIntent.NETWORK
    if primary in _PROCESS_CMDS:
        return CommandIntent.PROCESS_MANAGEMENT
    if primary in _PACKAGE_CMDS:
        return CommandIntent.PACKAGE_MANAGEMENT
    if primary in _ADMIN_CMDS:
        return CommandIntent.SYSTEM_ADMIN

    return CommandIntent.UNKNOWN


def validate_command(command: str) -> Tuple[ValidationResult, str, CommandIntent]:
    """
    Validates a command against safety boundaries and dangerous patterns.
    """
    cmd_lower = command.strip().lower()
    intent = classify_command_intent(command)

    # 1. Critical destructive and attack vectors - ALWAYS BLOCKED
    blocked_patterns = [
        ("rm -rf /", "Recursive root deletion"),
        ("format ", "Disk format command"),
        ("del /s /q", "Silent recursive file deletion"),
        ("shutdown", "System shutdown"),
        ("reboot", "System reboot"),
        ("mkfs", "Filesystem creation/wipe"),
        (":(){", "Fork bomb pattern"),
        ("dd if=", "Direct drive/block write"),
        ("wget | sh", "Unverified remote script execution"),
        ("curl | bash", "Unverified remote script execution"),
        ("> /dev/sda", "Raw block device overwrite"),
        ("shred ", "Permanent file shredding"),
    ]

    for pattern, rationale in blocked_patterns:
        if pattern in cmd_lower:
            return ValidationResult.BLOCK, f"dangerous pattern '{pattern}' ({rationale})", CommandIntent.DESTRUCTIVE

    # 2. Destructive or high-impact commands - WARNING
    if intent in (CommandIntent.DESTRUCTIVE, CommandIntent.SYSTEM_ADMIN):
        return ValidationResult.WARN, f"Command has {intent.value} intent", intent

    if intent == CommandIntent.NETWORK:
        return ValidationResult.WARN, "Command initiates external network activity", intent

    return ValidationResult.ALLOW, "", intent


def _run_shell_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    """Executes a shell command. ALWAYS gated by human approval via policy."""
    command = params.get("command", "")
    timeout = min(params.get("timeout", 30), 60)
    cwd = params.get("cwd", str(ctx.project_root))

    if not command.strip():
        return Observation(ok=False, output=None, error="No command provided.")

    # Run semantic command validation (claw-code pattern)
    val_result, val_reason, intent = validate_command(command)
    if val_result == ValidationResult.BLOCK:
        return Observation(
            ok=False,
            output=None,
            error=f"Command blocked: contains dangerous pattern '{val_reason}'.",
            metadata={"blocked": True, "reason": val_reason, "intent": intent.value},
        )

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )

        return Observation(
            ok=result.returncode == 0,
            output=result.stdout[:5000],
            error=result.stderr[:2000] if result.returncode != 0 else None,
            metadata={
                "returncode": result.returncode,
                "command": command,
                "intent": intent.value,
                "validation": val_result.value,
            },
        )
    except subprocess.TimeoutExpired:
        return Observation(ok=False, output=None, error=f"Shell command timed out after {timeout}s.")
    except Exception as ex:
        return Observation(ok=False, output=None, error=f"Shell error: {str(ex)}")


def register_shell_capabilities(registry) -> None:
    """Registers shell execution capability (NEVER_AUTONOMOUS)."""
    registry.register_implementation(ImplementationSpec(
        name="run_shell",
        description="Execute arbitrary shell command with semantic intent validation (ALWAYS requires human approval)",
        input_schema={"command": "str", "timeout": "int (optional, max 60)", "cwd": "str (optional)"},
        output_schema={"stdout": "str", "returncode": "int"},
        autonomy_action="run_shell",
        risk="HIGH",
        cost=CostModel(estimated_seconds=5.0, risk_weight=4.0),
        failure_modes=["timeout", "permission_denied", "command_not_found", "dangerous_pattern"],
        handler=_run_shell_handler,
    ))
