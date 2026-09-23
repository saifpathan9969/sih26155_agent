"""Tool 1 — File Discovery."""

from pathlib import Path
from typing import Dict

# Extensions the uploader accepts, so discovery finds the same files a user can
# add through the UI. ``.rsc`` (MikroTik export) was previously missing, which
# meant RouterOS configs on disk were silently skipped.
CONFIG_PATTERNS = ("*.conf", "*.cfg", "*.txt", "*.rsc", "*.ini", "*.xml", "*.log")

# A NUL byte in the first chunk is the standard heuristic for "this is binary".
_BINARY_SNIFF_BYTES = 4096


def _looks_binary(path: Path) -> bool:
    try:
        with open(path, "rb") as fh:
            return b"\x00" in fh.read(_BINARY_SNIFF_BYTES)
    except OSError:
        return True


def _read_text_safely(path: Path) -> str | None:
    """
    Read a config file without letting encoding surprises abort the scan.

    ``Path.read_text()`` with no encoding uses the platform locale codec, which
    on Windows is cp1252 — a single byte outside that range (any UTF-8 config,
    or a stray binary file sitting in the directory) raised UnicodeDecodeError
    and took down discovery for every other file too.
    """
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, LookupError):
            continue
        except OSError:
            return None
    return None


def discover_configs(source) -> Dict[str, str]:
    """
    Returns {filename: raw_text}.

    `source` is either a directory path (real files matching CONFIG_PATTERNS)
    or a dict already mapping filename -> raw text (used by the demo, so the
    agent runs without needing files on disk).

    Unreadable or binary files are skipped rather than aborting the scan: a
    partial inventory is useful, a hard failure is not.
    """
    if isinstance(source, dict):
        return dict(source)

    directory = Path(source)
    out: Dict[str, str] = {}
    if not directory.is_dir():
        return out

    for pattern in CONFIG_PATTERNS:
        for f in sorted(directory.glob(pattern)):
            if not f.is_file() or f.name in out:
                continue
            if _looks_binary(f):
                continue
            text = _read_text_safely(f)
            if text is not None:
                out[f.name] = text
    return out
