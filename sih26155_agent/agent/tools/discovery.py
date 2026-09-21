"""Tool 1 — File Discovery."""

from pathlib import Path
from typing import Dict


def discover_configs(source) -> Dict[str, str]:
    """
    Returns {filename: raw_text}.
    `source` is either a directory path (real files, *.conf/*.cfg/*.txt)
    or a dict already mapping filename -> raw text (used by the demo, so
    the agent runs without needing files on disk).
    """
    if isinstance(source, dict):
        return dict(source)

    directory = Path(source)
    out = {}
    for pattern in ("*.conf", "*.cfg", "*.txt"):
        for f in directory.glob(pattern):
            out[f.name] = f.read_text()
    return out
