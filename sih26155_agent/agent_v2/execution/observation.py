"""
Execution — Observation Dataclass
GAACA v2.0

Raw observation capture with metadata enrichment.
Re-exports from capabilities.base for convenience.
"""

from agent_v2.capabilities.base import Observation

# Re-export — the canonical Observation lives in capabilities.base
__all__ = ["Observation"]
