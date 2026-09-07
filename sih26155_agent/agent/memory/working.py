"""Working memory — scoped to a single mission run, discarded after."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class WorkingMemory:
    total_devices: int = 0
    processed: int = 0
    unknown_detections: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    per_device_summary: Dict[str, dict] = field(default_factory=dict)
    log: List[str] = field(default_factory=list)

    def note(self, message: str) -> None:
        self.log.append(message)

    def as_status_block(self) -> str:
        return (
            f"Processed {self.processed}/{self.total_devices} devices | "
            f"Unknown patterns: {self.unknown_detections} | "
            f"Critical: {self.critical_findings}  High: {self.high_findings}  "
            f"Medium: {self.medium_findings}  Low: {self.low_findings}"
        )
