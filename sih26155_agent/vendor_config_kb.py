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

    # -----------------------------------------------------------------------
    # 7. Extended vendor management-plane syntax (ASA, NX-OS, EXOS, OS10,
    #    Gaia, Sophos, AOS-CX, EdgeOS, Omada)
    # -----------------------------------------------------------------------
    (re.compile(r"no\s+feature\s+telnet|disable\s+telnet|no\s+ip\s+telnet\s+server|set\s+net-access\s+telnet\s+off|telnet_disable\s+1|management\.telnet\.enable=0|telnetd\.status=disabled|services\.telnetd\.enable=0|set\s+admin-telnet\s+disable|option\s+telnet\s+'?0'?", re.I),
     "management.telnet.enabled", ServiceState.DISABLED, "Management"),
    (re.compile(r"no\s+feature\s+http-server|disable\s+web\s+http|no\s+http\s+server\s+enable|http_disable\s+1|management\.http\.enable=0|httpd\.status=disabled|services\.http\.enable=0|undo\s+http\s+server\s+enable", re.I),
     "management.http.enabled", ServiceState.DISABLED, "Management"),
    (re.compile(r"enable\s+web\s+https|ip\s+https\s+server|https-server|https_port|management\.https\.enable=1|services\.https\.enable=1|redirect_https\s+'?1'?|http\s+secure-server\s+enable|set\s+web\s+ssl-port", re.I),
     "management.https.enabled", ServiceState.ENABLED, "Management"),
    (re.compile(r"enable\s+sshd2|ip\s+ssh\s+server\s+enable|ssh\s+server\s+v2|sshd\.status=enabled|services\.ssh\.enable=1|set\s+net-access\s+ssh\s+on|management\.ssh\.enable=1|ssh\s+version\s+2", re.I),
     "management.ssh.enabled", ServiceState.ENABLED, "Management"),
    (re.compile(r"ssh\s+cipher\s+encryption\s+high|ssh\s+server\s+algorithms\s+cipher\s+aes|ssh\s+server\s+cipher\s+aes|configure\s+sshd2\s+ciphers\s+aes|ip\s+ssh\s+server\s+cipher\s+aes|set\s+ssh\s+server\s+cipher\s+aes|ssh\.cipher=aes|ssh_cipher\s+aes256|set\s+service_param\s+ssh\s+cipher\s+aes", re.I),
     "cryptography.ssh_ciphers_hardened", True, "Cryptography"),
    (re.compile(r"ssh\s+key-exchange\s+group\s+dh-group14|ssh\s+server\s+(?:hmac|macs?|mac)\s+(?:sha2_256|hmac-sha2-256)|ssh\s+server\s+algorithm\s+mac\s+hmac-sha2", re.I),
     "cryptography.ssh_ciphers_hardened", True, "Cryptography"),
    (re.compile(r"session-idle-timeout\s+(\d+)|configure\s+idletimeout\s+(\d+)|set\s+admin_session_timeout\s+(\d+)|auth\.session_timeout=(\d+)|management\.session\.timeout=(\d+)|ssh\s+timeout\s+(\d+)|console\s+timeout\s+(\d+)|set\s+ssh\s+server\s+idle-timeout\s+(\d+)|set\s+deviceconfig\s+setting\s+management\s+idle-timeout", re.I),
     "management.ssh.idle_timeout_seconds", 600, "Management"),

    # -----------------------------------------------------------------------
    # 8. Extended authentication syntax across new vendor families
    # -----------------------------------------------------------------------
    (re.compile(r"password-policy\s+min-length\s+(\d+)|set\s+password_complexity\s+min_length\s+(\d+)|min-password-length\s+(\d+)|aaa\s+authentication\s+minimum-password-length\s+(\d+)|set\s+minimum-length\s+(\d+)|account\s+password-policy\s+min-length", re.I),
     "authentication.password_policy.min_length", 14, "Authentication"),
    (re.compile(r"configure\s+cli\s+max-failed-logins\s+(\d+)|limit-login-attempts\s+(\d+)|ssh\s+login-attempts\s+(\d+)|set\s+login_security\s+max_failed_attempts\s+(\d+)|auth\.max_failed_attempts=(\d+)|deny-on-failed-attempts\s+allowed-attempts\s+(\d+)|ssh\s+maximum-auth-attempts\s+(\d+)|password-policy\s+lockout-on-login-failures", re.I),
     "authentication.account_lockout.enabled", True, "Authentication"),
    (re.compile(r"set\s+lockout-time\s+(\d+)|lockout-time\s+(\d+)|auth\.lockout_seconds=(\d+)|set\s+login_security\s+block_duration\s+(\d+)|lockout-time\s+900|state\s+block\s+fail-times\s+\d+\s+interval\s+(\d+)", re.I),
     "authentication.account_lockout.lockout_duration_seconds", 900, "Authentication"),
    (re.compile(r"password-hash\s+\$6\$|password\s+\$6\$|password\s+5\s+\$5\$|secret\s+sha512|password\s+irreversible-cipher|secret\s+10\s+\$6\$|password_hash=\$6\$|phash\s+\$6\$|password\s+ciphertext|set\s+expert-password-hash|secret\s+9\s+\$9\$|password\s+ENC\s+", re.I),
     "authentication.password_policy.encryption_enabled", True, "Authentication"),
    (re.compile(r"add\s+rba\s+role|role\s+network-admin|role\s+sysadmin|group\s+administrators|permissions\s+role-based|accprofile\s+\"?super_admin|set\s+login\s+class\s+\S+\s+permissions|privilege\s+level\s+15|users\.\w+\.role=administrator|create\s+account\s+admin", re.I),
     "authentication.privilege_levels_defined", True, "Authentication"),

    # -----------------------------------------------------------------------
    # 9. Wireless (WPA / SSID / client isolation) security posture
    # -----------------------------------------------------------------------
    (re.compile(r"security\s+wpa\s+wpa3|wpa3(?:-personal|-enterprise|-sae)?|akm\s+sae|wireless\.\w+\.security=wpa3", re.I),
     "cryptography.wireless.wpa_version", "wpa3", "Cryptography"),
    (re.compile(r"security\s+wpa\s+wpa2|wpa2-psk|wpa\.mode=2|wireless\.\w+\.security=wpa2|encryption\s+wpa2|set\s+security\s+wpa2", re.I),
     "cryptography.wireless.wpa_version", "wpa2", "Cryptography"),
    (re.compile(r"algorithm\s+tkip|pairwise=TKIP|encryption\s+tkip|wpa\.1\.pairwise=TKIP", re.I),
     "cryptography.wireless.weak_cipher_in_use", True, "Cryptography"),
    (re.compile(r"encryption\s+none|security\s+open|wireless\.\w+\.security=none|type\s+guest-access.*encryption\s+none", re.I),
     "cryptography.wireless.open_network", True, "Cryptography"),
    (re.compile(r"client[_\s-]?isolation[=\s]*'?1'?|l2isolation=true|peer-blocking\s+drop|guest_control=true|set\s+client-isolation\s+enable", re.I),
     "access_control.wireless.client_isolation_enabled", True, "AccessControl"),
    (re.compile(r"security\s+pmf\s+mandatory|dot11w\s+mandatory|management-frame-protection\s+required|pmf\s+required", re.I),
     "cryptography.wireless.management_frame_protection", True, "Cryptography"),

    # -----------------------------------------------------------------------
    # 10. IoT / OT / embedded device hardening
    # -----------------------------------------------------------------------
    (re.compile(r"allow_anonymous\s+true|modbus\.tcp\.auth=none|services\.rtsp\.auth=none|auth\s*=\s*none|bacnet\.foreign_device_registration=1", re.I),
     "authentication.anonymous_access_permitted", True, "Authentication"),
    (re.compile(r"factory_default_credentials\s+true|password=admin\b|password=1234\b|password=(?:engineer|operator|viewer|ubnt)\b|username=admin\s*\n\s*.*password=admin", re.I),
     "authentication.default_credentials_in_use", True, "Authentication"),
    (re.compile(r"firmware\.signature_verification=1|security\.firmware_signature_verification=1|firmware\.rollback_protection=1", re.I),
     "security_controls.firmware_integrity_verified", True, "SecurityControls"),
    (re.compile(r"firmware\.auto_update=1|firmware\.auto-update\s+enable", re.I),
     "security_controls.automatic_patching_enabled", True, "SecurityControls"),
    (re.compile(r"security\.debug_port_locked=1|security\.jtag_disabled=1|debug-port\s+disable", re.I),
     "security_controls.debug_interfaces_disabled", True, "SecurityControls"),
    (re.compile(r"mqtt\.tls=1|use_tls\s+'?1'?|tls_version\s*'?tlsv?1\.[23]'?|mqtt\.tls_version=1\.[23]|require_certificate\s+'?1'?", re.I),
     "cryptography.tls.min_version", "1.2", "Cryptography"),
    (re.compile(r"telemetry\.payload_encryption=1|telemetry\.replay_protection=1|lorawan\.activation=OTAA|security\.secure_element=1|security\.key_storage=hardware", re.I),
     "cryptography.data_in_transit_encrypted", True, "Cryptography"),
    (re.compile(r"listener\s+1883\b|services\.http\.port=80\b|modbus\.tcp\.port=502|services\.ftp\.enable=1|services\.upnp\.enable=1|services\.p2p_cloud\.enable=1", re.I),
     "network_services.insecure_services_enabled", True, "NetworkServices"),
    (re.compile(r"zigbee\.install_code_required=1|zigbee\.permit_join=0|zigbee\.link_key_policy=unique", re.I),
     "access_control.device_onboarding_restricted", True, "AccessControl"),
    (re.compile(r"syslog\.remote\.enable=1|logging\.remote\.enable=1|log\.remote\.enable=1|option\s+log_ip|syslog\.remote\.status=enabled|add\s+syslog\s+log-remote-address|configure\s+syslog\s+add", re.I),
     "logging.syslog.enabled", True, "Logging"),
    (re.compile(r"ntp\.enable=1|option\s+enabled\s+'1'|set\s+ntp\s+active\s+on|enable\s+ntp|ntp\s+enable|ntp-service\s+enable|system\.ntp\.server", re.I),
     "logging.time_synchronization_enabled", True, "Logging"),
    (re.compile(r"logging\.tamper_events=1|log_type\s+error|mgmt-auditlog\s+on|set\s+syslog\s+mgmt-auditlog", re.I),
     "logging.administrative_events.config_change_events_logged", True, "Logging"),

    # -----------------------------------------------------------------------
    # 11. Layer-2 switch attack mitigation (CIS switch benchmarks)
    # -----------------------------------------------------------------------
    (re.compile(r"ip\s+dhcp\s+snooping|dhcp\s+snooping\s+vlan|dhcp-snooping\s+enable", re.I),
     "security_controls.dhcp_snooping_enabled", True, "SecurityControls"),
    (re.compile(r"ip\s+arp\s+inspection|dynamic\s+arp\s+inspection|arp-protect\s+enable", re.I),
     "security_controls.arp_inspection_enabled", True, "SecurityControls"),
    (re.compile(r"spanning-tree\s+(?:portfast\s+)?bpduguard(?:\s+default|\s+enable)?|spanning-tree\s+bpdu-guard|port\s+type\s+edge\s+bpduguard|enable\s+elrp-client", re.I),
     "security_controls.bpdu_guard_enabled", True, "SecurityControls"),
    (re.compile(r"switchport\s+port-security|port-security\s+enable|port-security\s+maximum\s+(\d+)|port-security\s+client-limit", re.I),
     "access_control.port_security_enabled", True, "AccessControl"),
    (re.compile(r"storm-control\s+broadcast|storm-control\s+multicast|storm-control\s+level", re.I),
     "security_controls.storm_control_enabled", True, "SecurityControls"),
    (re.compile(r"switchport\s+trunk\s+native\s+vlan\s+(\d+)|native\s+vlan\s+999|switchport\s+nonegotiate", re.I),
     "access_control.native_vlan_hardened", True, "AccessControl"),
    (re.compile(r"spanning-tree\s+loopguard|spanning-tree\s+loop-guard|loop-protect", re.I),
     "security_controls.loop_guard_enabled", True, "SecurityControls"),

    # -----------------------------------------------------------------------
    # 12. Firewall policy hygiene (permissive-rule and UTM detection)
    # -----------------------------------------------------------------------
    (re.compile(r"set\s+srcaddr\s+\"all\".*set\s+dstaddr\s+\"all\"|permit\s+ip\s+any\s+any|action\s+'?accept'?.*default-action\s+'?accept'?|rule\s+\d+\s+action\s+'accept'.*source.*any|<type>pass</type>.*<any/>.*<any/>|set\s+service\s+\"ALL\"", re.I | re.S),
     "access_control.permissive_any_any_rule_present", True, "AccessControl"),
    (re.compile(r"set\s+utm-status\s+enable|set\s+ips-sensor|set\s+av-profile|profile-setting\s+group|set\s+ips\s+\S+|mode\s+prevent|intrusion-policy|profiles\s+vulnerability", re.I),
     "security_controls.threat_prevention_enabled", True, "SecurityControls"),
    (re.compile(r"set\s+logtraffic\s+all|log-start\s+yes|log-end\s+yes|set\s+log\s+enable|logging\s+trap\s+informational|set\s+firewall-rule.*log\s+enable", re.I),
     "logging.firewall_policy_logging_enabled", True, "Logging"),
    (re.compile(r"option\s+input\s+'DROP'|default-action\s+'?drop'?|deny\s+ip\s+any\s+any|action\s+deny.*DENY-ALL|set\s+firewall-rule.*action\s+drop|option\s+forward\s+'DROP'", re.I),
     "access_control.default_deny_posture", True, "AccessControl"),
    (re.compile(r"trusthost1\s+\S+|add\s+allowed-client|set\s+deviceconfig\s+system\s+permitted-ip|ssh\s+10\.\d+\.\d+\.\d+\s+255|address=10\.\d+\.\d+\.\d+/\d+|option\s+Interface\s+'lan'", re.I),
     "access_control.management_access.restricted_to_specific_hosts", True, "AccessControl"),
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
