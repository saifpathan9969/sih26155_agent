"""
Environment — Abstract Environment Interface
GAACA v2.0

Separates Mind (decides) from Reality (Environment).
Capabilities interact with the external world through this explicit interface.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional


class Environment(ABC):
    """Abstract interface for all environments the agent operates in."""
    @abstractmethod
    def inspect(self) -> Dict[str, Any]:
        """Returns metadata about the environment state."""
        pass


class ProjectEnvironment(Environment):
    """Encapsulates the local project directory and files."""
    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve()

    def inspect(self) -> Dict[str, Any]:
        files = [f.name for f in self.root_path.glob("*") if f.is_file()]
        dirs = [d.name for d in self.root_path.glob("*") if d.is_dir()]
        return {
            "root": str(self.root_path),
            "files_count": len(files),
            "files": files[:15],
            "dirs": dirs,
        }

    def list_files(self, pattern: str = "*") -> List[Path]:
        return list(self.root_path.glob(pattern))

    def read_text(self, relative_path: str) -> Optional[str]:
        p = (self.root_path / relative_path).resolve()
        if p.is_relative_to(self.root_path) and p.exists():
            return p.read_text(encoding="utf-8", errors="replace")
        return None
