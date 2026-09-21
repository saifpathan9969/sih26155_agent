"""
Mind — Perception Subsystem
GAACA v2.0

Normalizes raw environmental feedback (HTTP body, stdout, JSON, CLI text)
into typed Fact objects with provenance before reaching cognitive reasoning.
Untrusted web data is explicitly tagged and isolated from direct command directives.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agent_v2.mind.beliefs import Provenance


@dataclass
class Fact:
    subject: str
    value: Any
    confidence: float
    provenance: Provenance
    is_untrusted: bool = False

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "value": self.value,
            "confidence": self.confidence,
            "provenance": self.provenance.to_dict(),
            "is_untrusted": self.is_untrusted,
        }


class PerceptionEngine:
    def process_observation(
        self,
        capability: str,
        raw_output: Any,
        source_type: str = "internal",
        metadata: Optional[Dict] = None,
    ) -> List[Fact]:
        facts: List[Fact] = []
        is_untrusted = source_type in ("web", "untrusted_web")

        if isinstance(raw_output, dict):
            for k, v in raw_output.items():
                facts.append(Fact(
                    subject=f"{capability.lower()}.{k}",
                    value=v,
                    confidence=0.8 if is_untrusted else 1.0,
                    provenance=Provenance(
                        capability=capability,
                        source_type="untrusted_web" if is_untrusted else source_type,
                    ),
                    is_untrusted=is_untrusted,
                ))
        elif isinstance(raw_output, str):
            facts.append(Fact(
                subject=f"{capability.lower()}.output",
                value=raw_output[:1000],
                confidence=0.75 if is_untrusted else 1.0,
                provenance=Provenance(
                    capability=capability,
                    raw_text=raw_output[:300],
                    source_type="untrusted_web" if is_untrusted else source_type,
                ),
                is_untrusted=is_untrusted,
            ))

        return facts
