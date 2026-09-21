"""
Environment — Network Device Environment
GAACA v2.0

Provides read-only access to network device configurations.
Actual device write-back is OUT_OF_SCOPE (permanently prohibited).
This environment handles:
- Loading configuration files from disk
- Simulated device inventory
- Configuration content retrieval
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_v2.environment.environment import Environment


class NetworkEnvironment(Environment):
    """
    Represents the network device environment.
    In production, this would interface with SNMP/SSH/API.
    For SIH26155, it loads configuration files from disk.
    """

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir.resolve()
        self._devices: Dict[str, Dict[str, Any]] = {}
        self._discover_devices()

    def _discover_devices(self):
        """Scans config directory for device configuration files."""
        if not self.config_dir.exists():
            return

        config_extensions = {".conf", ".cfg", ".txt", ".config"}
        for f in self.config_dir.iterdir():
            if f.is_file() and f.suffix in config_extensions:
                device_id = f.stem
                self._devices[device_id] = {
                    "id": device_id,
                    "config_path": str(f),
                    "config_size": f.stat().st_size,
                    "vendor": "unknown",  # Will be fingerprinted by capability
                }

    def inspect(self) -> Dict[str, Any]:
        return {
            "config_dir": str(self.config_dir),
            "devices_found": len(self._devices),
            "device_ids": list(self._devices.keys()),
        }

    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        return self._devices.get(device_id)

    def get_config_content(self, device_id: str) -> Optional[str]:
        """Reads the raw configuration file content for a device."""
        device = self._devices.get(device_id)
        if not device:
            return None

        config_path = Path(device["config_path"])
        if config_path.exists():
            return config_path.read_text(encoding="utf-8", errors="replace")
        return None

    def list_devices(self) -> List[Dict[str, Any]]:
        return list(self._devices.values())

    def update_vendor(self, device_id: str, vendor: str):
        """Updates the fingerprinted vendor for a device."""
        if device_id in self._devices:
            self._devices[device_id]["vendor"] = vendor
