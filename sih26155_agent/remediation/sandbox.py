"""
Sandbox Manager — GAACA v1 Remediation
=======================================
Isolated candidate configuration workspace with lineage tracking.

Original configs live in uploads/ and NEVER change. The sandbox creates candidate
copies, applies proposed fixes, and tracks the lineage. Only after validation
passes do candidates graduate to output/fixed.

Workspace layout:
    uploads/         - immutable originals
    sandbox/         - active test candidates
    output/fixed/    - verified, promoted configs
    output/archive/  - previous promotion attempts
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from security_baseline_schema import VendorFamily


@dataclass
class SandboxSession:
    """
    One remediation attempt for one configuration.

    Tracks the original, the candidate being tested, proposed changes, validation
    status, and promotion result.
    """

    session_id: str
    filename: str
    vendor: str
    original_path: Path
    candidate_path: Path
    proposed_fixes: List[Dict]
    created_at: str
    status: str  # "pending", "validating", "passed", "failed", "promoted"
    original_hash: str
    candidate_hash: Optional[str] = None
    validation_result: Optional[Dict] = None
    promoted_path: Optional[Path] = None
    promoted_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "original_path": str(self.original_path),
            "candidate_path": str(self.candidate_path),
            "promoted_path": str(self.promoted_path) if self.promoted_path else None,
        }


class SandboxManager:
    """
    Creates isolated candidate configs, applies fixes, and manages the sandbox workspace.

    The original config is never touched. All mutations happen on a copy inside
    sandbox/, and only validated candidates reach output/fixed/.
    """

    def __init__(self, uploads_dir: Path, sandbox_dir: Path, output_dir: Path):
        self.uploads_dir = uploads_dir
        self.sandbox_dir = sandbox_dir
        self.output_dir = output_dir
        self.fixed_dir = output_dir / "fixed"
        self.archive_dir = output_dir / "archive"

        # Ensure directories exist
        for d in [self.sandbox_dir, self.fixed_dir, self.archive_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Active sessions indexed by session_id
        self._sessions: Dict[str, SandboxSession] = {}
        self._load_sessions()

    def _load_sessions(self) -> None:
        """Restore session state from sandbox metadata."""
        meta_file = self.sandbox_dir / "sessions.json"
        if not meta_file.exists():
            return
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                item["original_path"] = Path(item["original_path"])
                item["candidate_path"] = Path(item["candidate_path"])
                if item.get("promoted_path"):
                    item["promoted_path"] = Path(item["promoted_path"])
                self._sessions[item["session_id"]] = SandboxSession(**item)
        except Exception as e:
            print(f"[Sandbox] Failed to load sessions: {e}")

    def _save_sessions(self) -> None:
        """Persist session state to sandbox metadata."""
        meta_file = self.sandbox_dir / "sessions.json"
        try:
            data = [s.to_dict() for s in self._sessions.values()]
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Sandbox] Failed to save sessions: {e}")

    @staticmethod
    def _hash_file(path: Path) -> str:
        """SHA-256 hash of file content."""
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def create_session(
        self,
        filename: str,
        vendor: str,
        proposed_fixes: List[Dict],
        username: Optional[str] = None,
        config_text: Optional[str] = None,
    ) -> SandboxSession:
        """
        Create a sandbox session for testing remediation on one config.

        Copies the original to sandbox/, records lineage, returns a session handle.
        The original file remains untouched.

        If the file doesn't exist on disk (uploaded in-memory only), config_text
        is written to uploads/ first so the sandbox has a stable on-disk reference.
        """
        original = self.uploads_dir / filename

        # If file isn't on disk yet but caller supplied the text, persist it
        if not original.exists():
            if config_text:
                self.uploads_dir.mkdir(parents=True, exist_ok=True)
                original.write_text(config_text, encoding="utf-8")
            else:
                raise FileNotFoundError(
                    f"Original config not found on disk: {filename}. "
                    "Ensure the config is uploaded before running remediation."
                )

        # Generate session ID from timestamp + filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        session_id = f"{timestamp}_{filename.replace('.', '_')}"
        candidate_name = f"{session_id}_candidate.conf"
        candidate_path = self.sandbox_dir / candidate_name

        # Copy original → candidate
        shutil.copy2(original, candidate_path)

        session = SandboxSession(
            session_id=session_id,
            filename=filename,
            vendor=vendor,
            original_path=original,
            candidate_path=candidate_path,
            proposed_fixes=proposed_fixes,
            created_at=datetime.utcnow().isoformat(),
            status="pending",
            original_hash=self._hash_file(original),
        )

        self._sessions[session_id] = session
        self._save_sessions()
        return session

    def get_session(self, session_id: str) -> Optional[SandboxSession]:
        """Retrieve an active sandbox session by ID."""
        return self._sessions.get(session_id)

    def list_sessions(self, status: Optional[str] = None) -> List[SandboxSession]:
        """List all sandbox sessions, optionally filtered by status."""
        sessions = list(self._sessions.values())
        if status:
            sessions = [s for s in sessions if s.status == status]
        return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    def apply_fixes(self, session_id: str, fixes: List[Dict]) -> bool:
        """
        Apply proposed remediation changes to the candidate config.

        Returns True if all fixes were successfully applied, False otherwise.
        Each fix is a dict with:
            {
                "rule_id": "CIS-MGMT-01",
                "action": "replace" | "append" | "delete",
                "pattern": "...",  # regex or literal to find
                "replacement": "...",  # new text
                "line_number": int (optional)
            }
        """
        session = self.get_session(session_id)
        if not session:
            return False

        candidate = session.candidate_path
        if not candidate.exists():
            return False

        try:
            content = candidate.read_text(encoding="utf-8")
            original_content = content

            for fix in fixes:
                action = fix.get("action", "replace")
                pattern = fix.get("pattern")
                replacement = fix.get("replacement", "")

                if action == "replace" and pattern:
                    import re
                    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                    if new_content != content:
                        content = new_content
                    else:
                        # Pattern didn't match — append as fallback so fix is still applied
                        content += "\n" + replacement + "\n"
                elif action == "append":
                    content += "\n" + replacement + "\n"
                elif action == "delete" and pattern:
                    import re
                    content = re.sub(pattern, "", content, flags=re.MULTILINE)

            # Always write candidate (even if content unchanged — caller decides)
            candidate.write_text(content, encoding="utf-8")
            session.candidate_hash = self._hash_file(candidate)
            session.status = "validating"
            self._save_sessions()
            return True
        except Exception as e:
            print(f"[Sandbox] Error applying fixes to {session_id}: {e}")
            return False

    def mark_validated(self, session_id: str, validation_result: Dict) -> None:
        """Record validation result for a sandbox session."""
        session = self.get_session(session_id)
        if not session:
            return

        session.validation_result = validation_result
        passed = validation_result.get("passed", False)
        session.status = "passed" if passed else "failed"
        self._save_sessions()

    def promote(self, session_id: str, promoted_by: Optional[str] = None) -> Optional[Path]:
        """
        Graduate a validated candidate to output/fixed/.

        Only sessions with status="passed" can be promoted. Returns the path to
        the promoted config, or None if promotion failed.
        """
        session = self.get_session(session_id)
        if not session or session.status != "passed":
            return None

        # Archive any previous promotion of this filename
        existing = self.fixed_dir / session.filename
        if existing.exists():
            archive_name = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{session.filename}"
            shutil.move(existing, self.archive_dir / archive_name)

        # Promote candidate → fixed
        promoted_path = self.fixed_dir / session.filename
        shutil.copy2(session.candidate_path, promoted_path)

        session.promoted_path = promoted_path
        session.promoted_at = datetime.utcnow().isoformat()
        session.status = "promoted"
        self._save_sessions()

        return promoted_path

    def cleanup_session(self, session_id: str) -> None:
        """Remove a sandbox session and its candidate file."""
        session = self.get_session(session_id)
        if not session:
            return

        # Delete candidate
        if session.candidate_path.exists():
            session.candidate_path.unlink()

        # Remove from registry
        del self._sessions[session_id]
        self._save_sessions()

    def get_diff(self, session_id: str) -> Optional[str]:
        """
        Generate a unified diff between original and candidate.

        Returns diff text, or None if session doesn't exist or files are missing.
        """
        session = self.get_session(session_id)
        if not session:
            return None

        if not session.original_path.exists() or not session.candidate_path.exists():
            return None

        try:
            import difflib

            original_lines = session.original_path.read_text(encoding="utf-8").splitlines(keepends=True)
            candidate_lines = session.candidate_path.read_text(encoding="utf-8").splitlines(keepends=True)

            diff = difflib.unified_diff(
                original_lines,
                candidate_lines,
                fromfile=f"original/{session.filename}",
                tofile=f"candidate/{session.filename}",
                lineterm="",
            )
            return "".join(diff)
        except Exception as e:
            print(f"[Sandbox] Error generating diff for {session_id}: {e}")
            return None
