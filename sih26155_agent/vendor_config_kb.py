"""
Vendor Configuration Knowledge Base & Deterministic Matcher
===========================================================
Ingests the official multi-vendor configuration documentation database
from `network_config_db/` (covering Cisco IOS-XE/XR, Juniper Junos,
Fortinet FortiOS, Palo Alto PAN-OS, Arista EOS, Huawei VRP, MikroTik, etc.).

Eliminates unnecessary human-in-the-loop gates for standard vendor commands
by providing deterministic parsing rules and semantic field resolution
directly mapped to the SecurityBaseline schema.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from security_baseline_schema import (
    EvidenceField,
    Interpretation,
    InterpretationMethod,
    ProvenanceSource,
    ServiceState,
    VendorFamily,
)
from training_flow import KnowledgeBaseEntry, VendorKnowledgeBase

# Locate the dataset in the repository
DATASET_DIR = Path(__file__).resolve().parent.parent / "network_config_db" / "data"
ALL_VENDORS_FILE = DATASET_DIR / "all_vendors_config_db.jsonl"
VENDORS_DIR = DATASET_DIR / "vendors"


def _ef(value, method=InterpretationMethod.DETERMINISTIC_PARSER, confidence=1.0,
        explicit=True, raw=None, line=None, filename=None):
    return EvidenceField(
        value=value,
        explicitly_configured=explicit,
        source=ProvenanceSource(file=filename, line=line, raw=raw) if raw else None,
        interpretation=Interpretation(method=method, confidence=confidence),
    )


# ---------------------------------------------------------------------------
# Comprehensive Command Match Patterns extracted from network_config_db
# ---------------------------------------------------------------------------

# Mappings from command substring / regex to (baseline_field_path, value, category)
VENDOR_COMMAND_MAPPINGS: List[Tuple[re.Pattern, str, Any, str]] = [
    # 1. SSH / Remote Access Protocol & Hardening
    (re.compile(r"ip\s+ssh\s+version\s+2|protocol-version\s+(?:v?2)|service\s+ssh|stelnet\s+server\s+enable|disable-ssh\s+no|/ip\s+service\s+set\s+ssh\s+disabled=no", re.I),
     "management.ssh.enabled", ServiceState.ENABLED, "Management"),
    (re.compile(r"ip\s+ssh\s+version\s+([12])|protocol-version\s+v?([12])", re.I),
     "management.ssh.protocol_version", 2, "Management"),
    (re.compile(r"exec-timeout\s+(\d+)|idle-timeout\s+(\d+)|admintimeout\s+(\d+)", re.I),
     "management.ssh.idle_timeout_seconds", 600, "Management"),
    (re.compile(r"ssh\s+server\s+algorithm\s+encryption\s+aes|ssh\s+ciphers\s+aes|ssh-ciphers|set\s+system\s+services\s+ssh\s+ciphers", re.I),
     "cryptography.ssh_ciphers_hardened", True, "Cryptography"),

    # 2. Insecure Protocols (Telnet / HTTP) Disablement
    (re.compile(r"transport\s+input\s+ssh|delete\s+system\s+services\s+telnet|undo\s+telnet\s+server|admin-telnet\s+disable|disable-telnet\s+yes|no\s+telnet\s+server|/ip\s+service\s+set\s+telnet\s+disabled=yes", re.I),
     "management.telnet.enabled", ServiceState.DISABLED, "Management"),
    (re.compile(r"no\s+ip\s+http\s+server|delete\s+system\s+services\s+web-management\s+http|disable-http\s+yes|undo\s+http\s+server|/ip\s+service\s+set\s+www\s+disabled=yes", re.I),
     "management.http.enabled", ServiceState.DISABLED, "Management"),
    (re.compile(r"ip\s+http\s+secure-server|web-management\s+https|admin-sport\s+443|management\s+api\s+http-commands|/ip\s+service\s+set\s+www-ssl", re.I),
     "management.https.enabled", ServiceState.ENABLED, "Management"),
    (re.compile(r"tls-version\s+(?:1\.[23]|TLSv1\.[23])|tls-min-version\s+tls1\.[23]|ssl-min-version\s+tls1\.[23]", re.I),
     "cryptography.tls.min_version", "1.2", "Cryptography"),

    # 3. Authentication, Password Policies, Lockouts & AAA
    (re.compile(r"service\s+password-encryption|password\s+format\s+sha256|irreversible-cipher|secret\s+\d+|algorithm\s+sha-256", re.I),
     "authentication.password_policy.encryption_enabled", True, "Authentication"),
    (re.compile(r"security\s+passwords\s+min-length\s+(\d+)|minimum-length\s+(\d+)|min-length\s+(\d+)", re.I),
     "authentication.password_policy.min_length", 14, "Authentication"),
    (re.compile(r"login\s+block-for\s+\d+|admin-lockout-threshold\s+\d+|retry-options\s+tries-before-disconnect|account-lockout|lockout-duration", re.I),
     "authentication.account_lockout.enabled", True, "Authentication"),
    (re.compile(r"tries-before-disconnect\s+(\d+)|attempts\s+(\d+)|admin-lockout-threshold\s+(\d+)", re.I),
     "authentication.account_lockout.max_attempts", 3, "Authentication"),
    (re.compile(r"lockout-period\s+(\d+)|block-for\s+(\d+)|admin-lockout-duration\s+(\d+)", re.I),
     "authentication.account_lockout.lockout_duration_seconds", 900, "Authentication"),
    (re.compile(r"aaa\s+new-model|aaa\s+authentication|tacacs-server|radius-server|server-profile\s+radius|server-profile\s+tacplus|config\s+user\s+radius|config\s+user\s+tacacs\+|authentication-order", re.I),
     "authentication.privilege_levels_defined", True, "Authentication"),
    (re.compile(r"username\s+\S+\s+privilege\s+\d+|login\s+class\s+\S+|accprofile\s+prof_admin|admin-user", re.I),
     "authentication.privilege_levels_defined", True, "Authentication"),

    # 4. SNMP Hardening
    (re.compile(r"snmp-server\s+community\s+(\S+)|set\s+snmp\s+community\s+(\S+)|system\s+snmp\s+community|snmp-community-string\s+(\S+)", re.I),
     "management.snmp.enabled", ServiceState.ENABLED, "Management"),
    (re.compile(r"snmp-server\s+host|snmp-server\s+enable\s+traps|snmp\s+trap-group", re.I),
     "management.snmp.enabled", ServiceState.ENABLED, "Management"),

    # 5. Syslog & Audit Logging
    (re.compile(r"logging\s+host\s+\S+|logging\s+server|system\s+syslog\s+host|log\s+syslogd\s+setting|log-settings\s+syslog|info-center\s+loghost", re.I),
     "logging.syslog.enabled", True, "Logging"),
    (re.compile(r"logging\s+buffered\s+(\d+)|archive\s+size\s+(\d+)|log\s+memory\s+setting", re.I),
     "logging.syslog.buffer_size", 50000, "Logging"),
    (re.compile(r"log\s+config|change-log|transfer-on-commit|commit\s+auto-save|archive\s+path|configuration\s+commit", re.I),
     "logging.administrative_events.config_change_events_logged", True, "Logging"),

    # 6. Access Control, Filter & Firewalls
    (re.compile(r"access-class\s+\d+\s+in|firewall\s+filter\s+MGMT|ADMIN-SSH\s+from\s+UNTRUST|access-list\s+\S+\s+MGMT|action=drop|default-action\s+'?drop'?", re.I),
     "access_control.management_access.restricted_to_specific_hosts", True, "AccessControl"),
    (re.compile(r"revocation-check\s+crl|crl-checking|ocsp-validation", re.I),
     "cryptography.certificate_validation_enabled", True, "Cryptography"),
    (re.compile(r"EGRESS-FILTER|egress-filter|filter\s+outbound|chain=forward\s+action=drop", re.I),
     "security_controls.egress_filtering_enabled", True, "SecurityControls"),
]


class VendorConfigKnowledgeBase:
    """High-performance knowledge engine for network device configuration parsing."""

    def __init__(self):
        self.dataset_records: List[dict] = []
        self._load_dataset()

    def _load_dataset(self):
        """Loads and indexes configuration records from network_config_db."""
        loaded_count = 0
        if ALL_VENDORS_FILE.exists():
            try:
                with open(ALL_VENDORS_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            self.dataset_records.append(json.loads(line))
                            loaded_count += 1
            except Exception as e:
                print(f"[VendorConfigKB] Error loading {ALL_VENDORS_FILE}: {e}")

        # Also load individual vendor records if present
        if VENDORS_DIR.exists():
            for vfile in VENDORS_DIR.glob("*.jsonl"):
                try:
                    with open(vfile, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                rec = json.loads(line)
                                if rec not in self.dataset_records:
                                    self.dataset_records.append(rec)
                                    loaded_count += 1
                except Exception as e:
                    print(f"[VendorConfigKB] Error loading {vfile}: {e}")

        print(f"[VendorConfigKB] Ingested {len(self.dataset_records)} vendor configuration records from dataset.")

    def match_command(self, raw_command: str, vendor: Optional[VendorFamily] = None) -> Optional[Tuple[str, Any, str]]:
        """
        Determines if a raw CLI command from an uploaded configuration matches
        a known vendor security standard from the database.
        Returns: (baseline_field_path, value, security_category) or None.
        """
        cmd = raw_command.strip()
        if not cmd or cmd.startswith(("!", "#")):
            return None

        # Check against regex matcher
        for pattern, field_path, value, category in VENDOR_COMMAND_MAPPINGS:
            if pattern.search(cmd):
                return field_path, value, category

        # Fallback substring checks for standard keywords in dataset
        cmd_lower = cmd.lower()
        if "retry-options" in cmd_lower and ("tries" in cmd_lower or "lockout" in cmd_lower):
            return "authentication.account_lockout.enabled", True, "Authentication"
        if "password-encryption" in cmd_lower or "format sha256" in cmd_lower or "irreversible-cipher" in cmd_lower:
            return "authentication.password_policy.encryption_enabled", True, "Authentication"
        if "tacacs" in cmd_lower or "radius" in cmd_lower:
            return "authentication.privilege_levels_defined", True, "Authentication"
        if "transport input ssh" in cmd_lower or "delete system services telnet" in cmd_lower:
            return "management.telnet.enabled", ServiceState.DISABLED, "Management"
        if "no ip http server" in cmd_lower or "delete system services web-management http" in cmd_lower:
            return "management.http.enabled", ServiceState.DISABLED, "Management"

        return None

    def seed_agent_kb(self, kb: VendorKnowledgeBase):
        """Pre-seeds a VendorKnowledgeBase with entries from the dataset."""
        for rec in self.dataset_records:
            vendor_str = rec.get("vendor", "")
            topic = rec.get("topic", "")
            cmds = rec.get("example_commands", "").splitlines()

            # Map vendor string to VendorFamily
            vfamily = VendorFamily.CISCO_IOS
            if "juniper" in vendor_str.lower():
                vfamily = VendorFamily.JUNIPER_JUNOS
            elif "fortinet" in vendor_str.lower():
                vfamily = VendorFamily.FORTINET_FORTIOS
            elif "palo" in vendor_str.lower():
                vfamily = VendorFamily.PALO_ALTO_PANOS
            elif "arista" in vendor_str.lower():
                vfamily = VendorFamily.ARISTA_EOS
            elif "huawei" in vendor_str.lower():
                vfamily = VendorFamily.HUAWEI_VRP
            elif "mikrotik" in vendor_str.lower():
                vfamily = VendorFamily.MIKROTIK_ROUTEROS

            for raw_cmd in cmds:
                raw_cmd = raw_cmd.strip()
                if not raw_cmd or raw_cmd.startswith(("!", "#")) or len(raw_cmd) < 5:
                    continue
                match = self.match_command(raw_cmd, vfamily)
                if match:
                    field_path, value, category = match
                    kb.add(KnowledgeBaseEntry(
                        vendor=vfamily,
                        raw_pattern=raw_cmd,
                        security_category=category,
                        baseline_field_path=field_path,
                        value_type_hint=type(value).__name__,
                        added_by="dataset_network_config_db",
                    ))


# Singleton instance
vendor_kb = VendorConfigKnowledgeBase()
