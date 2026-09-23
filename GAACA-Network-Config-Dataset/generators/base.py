"""
GAACA Dataset Generator — Base Classes & Utilities
====================================================
Provides abstract base class for all vendor-specific config generators,
plus shared helpers for RFC 5737 IPs, placeholder secrets, random
hostnames, interface names, and VLAN IDs.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import string
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

GENERATOR_VERSION = "1.0.0"
TODAY = date.today().isoformat()

# RFC 5737 documentation IP ranges — safe to use in examples
RFC5737_NETS = [
    ("192.0.2", 1, 254),      # TEST-NET-1
    ("198.51.100", 1, 254),    # TEST-NET-2
    ("203.0.113", 1, 254),     # TEST-NET-3
]

# Placeholder secrets — obviously fake
PLACEHOLDER_PASSWORDS = [
    "P@ssw0rd_PLACEHOLDER",
    "S3cur3_D3m0_P@ss!",
    "REDACTED_ADMIN_PASS",
    "Ch@ng3M3_N0w_2026!",
    "T3st_P@ssw0rd_Lab!",
]

PLACEHOLDER_COMMUNITIES = [
    "REDACTED_COMMUNITY",
    "DEMO_RO_COMMUNITY",
    "DEMO_RW_COMMUNITY",
    "LAB_SNMP_STRING",
]

PLACEHOLDER_PRESHARED_KEYS = [
    "REDACTED_PSK_0123456789abcdef",
    "DEMO_VPN_KEY_abcdef0123456789",
    "LAB_IPSEC_PSK_fedcba9876543210",
]

SYSLOG_SERVERS = ["198.51.100.10", "198.51.100.11", "203.0.113.50"]
NTP_SERVERS = ["198.51.100.123", "203.0.113.123", "192.0.2.123"]
RADIUS_SERVERS = ["198.51.100.20", "203.0.113.20"]
TACACS_SERVERS = ["198.51.100.21", "203.0.113.21"]
DNS_SERVERS = ["198.51.100.53", "203.0.113.53"]

HOSTNAMES_PREFIX = [
    "HQ", "DC", "BR", "EDGE", "CORE", "DIST", "ACCESS", "DMZ",
    "LAB", "STAGING", "PROD", "DR", "CAMPUS", "REMOTE", "WAN",
]

LOCATION_SUFFIXES = [
    "NYC", "LON", "SIN", "TKY", "SYD", "BER", "MUM", "DXB",
    "SFO", "CHI", "DAL", "SEA", "AMS", "FRA", "PAR",
]


class ConfigGenerator(ABC):
    """Abstract base class for vendor-specific configuration generators."""

    vendor: str = ""
    product: str = ""
    os_name: str = ""
    os_version: str = ""
    device_type: str = ""
    category: str = ""
    config_format: str = ""
    vendor_dir_name: str = ""
    device_class: str = ""
    network_role: str = ""
    platform: str = ""
    model: str = ""
    routing_capability: bool = False
    l3_capable: bool = False
    routing_protocols: List[str] = []
    capabilities: List[str] = []
    ambiguity: bool = False
    ambiguity_reason: Optional[str] = None

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.base_seed = seed

    # ---- Subclass must implement these ----

    @abstractmethod
    def generate_secure(self, index: int) -> str:
        """Generate a security-hardened configuration."""
        ...

    @abstractmethod
    def generate_misconfigured(self, index: int) -> str:
        """Generate a deliberately insecure configuration."""
        ...

    @abstractmethod
    def generate_edge_case(self, index: int) -> str:
        """Generate an edge-case configuration (partial, deprecated, conflicting)."""
        ...

    def secure_controls_present(self) -> List[str]:
        return ["ssh_v2", "https_management", "syslog", "ntp", "strong_auth",
                "password_encryption", "session_timeout", "default_deny_policy"]

    def secure_controls_absent(self) -> List[str]:
        return []

    def misconfigured_controls_present(self) -> List[str]:
        return []

    def misconfigured_controls_absent(self) -> List[str]:
        return ["ssh_hardening", "logging", "password_encryption",
                "account_lockout", "telnet_disabled"]

    def misconfigured_vuln_tags(self) -> List[str]:
        return ["telnet_enabled", "http_management", "snmpv2_default_community",
                "weak_password", "no_logging"]

    def edge_case_details(self) -> str:
        return "Partial configuration with deprecated syntax, missing sections, or conflicting rules"

    # ---- Helpers ----

    def _reseed(self, index: int):
        """Re-seed RNG for deterministic per-config generation."""
        self.rng = random.Random(self.base_seed + index * 97)

    def rand_ip(self) -> str:
        net = self.rng.choice(RFC5737_NETS)
        return f"{net[0]}.{self.rng.randint(net[1], net[2])}"

    def rand_subnet(self, prefix_len: int = 24) -> Tuple[str, str]:
        net = self.rng.choice(RFC5737_NETS)
        base = f"{net[0]}.0"
        masks = {8: "255.0.0.0", 16: "255.255.0.0", 24: "255.255.255.0",
                 25: "255.255.255.128", 28: "255.255.255.240", 30: "255.255.255.252"}
        return base, masks.get(prefix_len, "255.255.255.0")

    def rand_hostname(self) -> str:
        prefix = self.rng.choice(HOSTNAMES_PREFIX)
        suffix = self.rng.choice(LOCATION_SUFFIXES)
        num = self.rng.randint(1, 99)
        return f"{prefix}-{self.product.upper().replace(' ', '')}-{suffix}-{num:02d}"

    def rand_password(self) -> str:
        return self.rng.choice(PLACEHOLDER_PASSWORDS)

    def rand_community(self) -> str:
        return self.rng.choice(PLACEHOLDER_COMMUNITIES)

    def rand_psk(self) -> str:
        return self.rng.choice(PLACEHOLDER_PRESHARED_KEYS)

    def rand_syslog(self) -> str:
        return self.rng.choice(SYSLOG_SERVERS)

    def rand_ntp(self) -> str:
        return self.rng.choice(NTP_SERVERS)

    def rand_radius(self) -> str:
        return self.rng.choice(RADIUS_SERVERS)

    def rand_tacacs(self) -> str:
        return self.rng.choice(TACACS_SERVERS)

    def rand_dns(self) -> str:
        return self.rng.choice(DNS_SERVERS)

    def rand_vlan(self) -> int:
        return self.rng.randint(10, 4090)

    def rand_as_number(self) -> int:
        return self.rng.randint(64512, 65534)  # Private ASN range

    def rand_description(self) -> str:
        descs = ["Management", "Uplink-ISP", "Server-Farm", "User-LAN",
                 "DMZ-Segment", "Guest-WiFi", "IoT-VLAN", "Voice-VLAN",
                 "Backup-Link", "Transit-Peering", "WAN-Primary", "WAN-Secondary"]
        return self.rng.choice(descs)

    def sample_id(self, state: str, index: int) -> str:
        cat_prefix = {
            "firewall": "FW", "router": "RT", "switch": "SW",
            "wifi": "WF", "iot": "IOT"
        }.get(self.category, "XX")
        state_char = {"secure": "S", "misconfigured": "M", "edge_case": "E"}[state]
        vendor_short = self.vendor_dir_name.upper().replace("/", "_")[:15]
        return f"{cat_prefix}-{vendor_short}-{state_char}-{index:03d}"

    def build_metadata(self, state: str, index: int) -> Dict[str, Any]:
        sid = self.sample_id(state, index)
        # Determine defaults for device_class and network_role if not explicitly specified
        if self.device_class:
            dev_class = self.device_class
        else:
            class_map = {
                "firewall": "firewall",
                "router": "router",
                "switch": "switch",
                "wifi": "wireless_controller" if self.device_type == "wifi_controller" else "wireless_ap",
            }
            dev_class = class_map.get(self.category, self.device_type or "unknown")

        if self.network_role:
            net_role = self.network_role
        else:
            role_map = {
                "firewall": "perimeter",
                "router": "edge",
                "switch": "access",
                "wifi": "campus" if dev_class == "wireless_controller" else "access",
            }
            if self.category == "iot":
                if "plc" in self.device_type:
                    net_role = "industrial_control"
                elif "camera" in self.device_type:
                    net_role = "surveillance"
                elif "gateway" in self.device_type:
                    net_role = "field_gateway"
                else:
                    net_role = "smart_sensor"
            else:
                net_role = role_map.get(self.category, "unknown")

        meta = {
            "sample_id": sid,
            "vendor": self.vendor,
            "product": self.product,
            "device_type": self.device_type,
            "device_class": dev_class,
            "network_role": net_role,
            "platform": self.platform or self.os_name,
            "model": self.model or self.product,
            "routing_capability": self.routing_capability or (self.category in ("router", "firewall")),
            "l3_capable": self.l3_capable or self.routing_capability or (self.category in ("router", "firewall", "switch")),
            "routing_protocols": list(self.routing_protocols),
            "capabilities": list(self.capabilities),
            "ambiguity": self.ambiguity,
            "ambiguity_reason": self.ambiguity_reason,
            "os": self.os_name,
            "version": self.os_version,
            "category": self.category,
            "source_type": "synthetic",
            "source_url": None,
            "license": None,
            "configuration_format": self.config_format,
            "security_state": state,
            "controls_present": [],
            "controls_absent": [],
            "vulnerability_tags": [],
            "contains_secrets": False,
            "anonymized": True,
            "generation_date": TODAY,
            "generator_version": GENERATOR_VERSION,
        }
        if state == "secure":
            meta["controls_present"] = self.secure_controls_present()
            meta["controls_absent"] = self.secure_controls_absent()
            meta["security_state_details"] = "Fully hardened configuration following vendor best practices and CIS benchmark recommendations"
        elif state == "misconfigured":
            meta["controls_present"] = self.misconfigured_controls_present()
            meta["controls_absent"] = self.misconfigured_controls_absent()
            meta["vulnerability_tags"] = self.misconfigured_vuln_tags()
            meta["security_state_details"] = "Deliberately insecure configuration with common misconfigurations for compliance testing"
        else:
            meta["security_state_details"] = self.edge_case_details()
            meta["controls_present"] = ["partial"]
            meta["vulnerability_tags"] = ["ambiguous_syntax", "partial_config"]
        return meta

    def generate_all(self, output_dir: Path, n_secure: int = 20, n_misconfig: int = 20, n_edge: int = 10) -> int:
        """Generate all configs for this vendor, return total count."""
        count = 0
        for i in range(1, n_secure + 1):
            self._reseed(i)
            config = self.generate_secure(i)
            sid = self.sample_id("secure", i)
            meta = self.build_metadata("secure", i)
            self._write(output_dir / "secure", sid, config, meta)
            count += 1

        for i in range(1, n_misconfig + 1):
            self._reseed(i + 1000)
            config = self.generate_misconfigured(i)
            sid = self.sample_id("misconfigured", i)
            meta = self.build_metadata("misconfigured", i)
            self._write(output_dir / "misconfigured", sid, config, meta)
            count += 1

        for i in range(1, n_edge + 1):
            self._reseed(i + 2000)
            config = self.generate_edge_case(i)
            sid = self.sample_id("edge_case", i)
            meta = self.build_metadata("edge_case", i)
            self._write(output_dir / "edge_cases", sid, config, meta)
            count += 1

        return count

    def _write(self, subdir: Path, sid: str, config: str, meta: dict):
        subdir.mkdir(parents=True, exist_ok=True)
        ext = ".json" if self.config_format in ("json", "sonic_config_db_json") else ".xml" if self.config_format in ("xml", "panos_xml", "opnsense_xml", "pfsense_xml") else ".rsc" if self.config_format == "mikrotik_rsc" else ".conf"
        conf_path = subdir / f"{sid}{ext}"
        meta_path = subdir / f"{sid}.meta.json"
        conf_path.write_text(config, encoding="utf-8")
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
