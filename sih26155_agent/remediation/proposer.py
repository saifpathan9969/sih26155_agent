"""
Remediation Proposer — GAACA v1
================================
Generates vendor-specific fix commands from compliance findings using the
vendor_config_kb knowledge base.

Takes a ComplianceFinding and produces concrete CLI commands that would resolve
the violation, syntax-aware per vendor family.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from security_baseline_schema import ComplianceFinding, ServiceState, VendorFamily
from vendor_config_kb import VENDOR_COMMAND_MAPPINGS


def _is_fail(status) -> bool:
    """Normalize FindingStatus enum or string to bool for FAIL checks."""
    return str(status).lower() in ("fail", "findingstatus.fail")


def _is_pass(status) -> bool:
    """Normalize FindingStatus enum or string to bool for PASS checks."""
    return str(status).lower() in ("pass", "findingstatus.pass")


class RemediationProposer:
    """
    Proposes concrete remediation commands for compliance violations.

    Uses the vendor KB's command patterns in reverse: given a failing control
    and target state, generates the vendor-specific syntax that achieves it.
    """

    def __init__(self):
        # Build reverse index: baseline_field → (value, commands_by_vendor)
        self._remediation_index: Dict[str, Dict] = {}
        self._build_remediation_index()
        # Pre-build fix table once (avoids rebuilding on every propose call)
        self._fix_table = self.__class__._FIX_TABLE

    def _build_remediation_index(self) -> None:
        """
        Invert VENDOR_COMMAND_MAPPINGS to enable lookup by baseline field.

        Structure: {baseline_field: {desired_value: {vendor: [commands]}}}
        """
        for pattern, field_path, expected_value, category in VENDOR_COMMAND_MAPPINGS:
            if field_path not in self._remediation_index:
                self._remediation_index[field_path] = {}

            value_key = str(expected_value)
            if value_key not in self._remediation_index[field_path]:
                self._remediation_index[field_path][value_key] = {}

            # Extract representative command from pattern (first alternative)
            # Pattern is a compiled regex, get the pattern string
            pattern_str = pattern.pattern
            # Take first alternative, strip anchors and whitespace patterns
            cmd_sample = pattern_str.split("|")[0]
            cmd_sample = re.sub(r"\\[bsS]|\(\?[^)]*\)|\s\+|\s\*|\s\?|[\[\]\(\)\{\}]", " ", cmd_sample)
            cmd_sample = re.sub(r"\s+", " ", cmd_sample).strip()

            # Infer vendor from command syntax
            vendors = self._infer_vendors(cmd_sample)
            for vendor in vendors:
                if vendor not in self._remediation_index[field_path][value_key]:
                    self._remediation_index[field_path][value_key][vendor] = []
                self._remediation_index[field_path][value_key][vendor].append(cmd_sample)

    def _infer_vendors(self, command: str) -> List[str]:
        """
        Infer which vendor families use this command syntax.

        Returns vendor family names as strings for indexing.
        """
        cmd_lower = command.lower()
        vendors = []

        # Cisco IOS/XE/XR syntax
        if any(k in cmd_lower for k in ["ip ssh", "no telnet", "service password", "aaa", "line vty", "transport input"]):
            vendors.extend(["cisco_ios", "cisco_iosxe", "cisco_iosxr", "cisco_nxos"])

        # Juniper Junos
        if any(k in cmd_lower for k in ["set system", "delete system", "set security", "protocol-version v2"]):
            vendors.append("juniper_junos")

        # Fortinet FortiOS
        if any(k in cmd_lower for k in ["config system", "set admin-sport", "set ssl-min-version", "set trusthost"]):
            vendors.append("fortinet_fortios")

        # Palo Alto PAN-OS
        if any(k in cmd_lower for k in ["set deviceconfig", "set service", "set mgt-config"]):
            vendors.append("palo_alto_panos")

        # Arista EOS
        if any(k in cmd_lower for k in ["management api", "no feature telnet"]):
            vendors.append("arista_eos")

        # Huawei VRP
        if any(k in cmd_lower for k in ["stelnet server", "undo telnet", "undo http server"]):
            vendors.append("huawei_vrp")

        # MikroTik RouterOS
        if any(k in cmd_lower for k in ["/ip service", "/user", "disabled=yes", "disabled=no"]):
            vendors.append("mikrotik_routeros")

        # Aruba AOS-CX
        if any(k in cmd_lower for k in ["ssh server", "no telnet", "https-server"]):
            vendors.append("aruba_aoscx")

        # If no specific vendor matched, mark as generic (works across multiple)
        if not vendors:
            vendors = ["generic"]

        return vendors

    def propose_fixes(
        self,
        finding: ComplianceFinding,
        vendor: VendorFamily,
        filename: str,
    ) -> List[Dict]:
        """
        Generate remediation fixes for a compliance finding.

        Returns a list of fix dictionaries, each containing:
            {
                "rule_id": "CIS-MGMT-01",
                "finding_status": "FAIL",
                "description": "Enable SSH version 2",
                "action": "replace" | "append" | "delete",
                "pattern": "...",
                "replacement": "...",
                "confidence": 0.0-1.0,
                "vendor_specific": True/False,
            }
        """
        if not _is_fail(finding.status):
            return []

        fixes = []
        rule_id     = finding.rule_id
        failed_field = finding.baseline_field_path
        vendor_name  = vendor.value if hasattr(vendor, 'value') else str(vendor)

        # ── Primary path: semantic fix from field path (reliable, vendor-aware) ──
        semantic_fix = self._generate_semantic_fix(
            rule_id=rule_id,
            failed_field=failed_field or rule_id,
            expected_value=None,
            current_value=None,
            vendor=vendor,
        )
        if semantic_fix:
            fixes.append(semantic_fix)
            return fixes

        # ── Fallback: KB index (regex-derived, lower confidence) ──
        field_fixes   = self._remediation_index.get(failed_field or "", {})
        vendor_commands = []
        for _val_key, _vendor_map in field_fixes.items():
            cmds = _vendor_map.get(vendor_name, []) or _vendor_map.get("generic", [])
            if cmds:
                vendor_commands = cmds
                break

        for cmd in vendor_commands[:2]:
            fix = self._command_to_fix(
                rule_id=rule_id,
                command=cmd,
                failed_field=failed_field or rule_id,
                expected_value=None,
                current_value=None,
                vendor=vendor,
            )
            if fix:
                fixes.append(fix)

        return fixes

    def _command_to_fix(
        self,
        rule_id: str,
        command: str,
        failed_field: str,
        expected_value,
        current_value,
        vendor: VendorFamily,
    ) -> Optional[Dict]:
        """
        Convert a KB command template into a fix action.

        Determines whether this is a replacement, append, or delete operation.
        """
        cmd_clean = command.strip()
        if not cmd_clean:
            return None

        # Determine action based on command structure
        action = "append"  # Default: add the secure config
        pattern = None
        description = f"Apply {rule_id}: {cmd_clean}"

        # If it's a negation command (no/undo/delete), it's a delete
        if any(cmd_clean.lower().startswith(neg) for neg in ["no ", "undo ", "delete ", "disable "]):
            action = "delete"
            # Pattern to find the insecure config being disabled
            pattern = self._insecure_pattern_for_field(failed_field, current_value, vendor)
            description = f"Remove insecure configuration for {rule_id}"
        else:
            # It's an enabling command — may need to replace existing config
            pattern = self._existing_pattern_for_field(failed_field, vendor)
            if pattern:
                action = "replace"
                description = f"Replace configuration for {rule_id}"

        return {
            "rule_id": rule_id,
            "finding_status": "FAIL",
            "description": description,
            "action": action,
            "pattern": pattern,
            "replacement": cmd_clean,
            "confidence": 0.85,
            "vendor_specific": True,
        }

    # ── Complete rule fix table — covers all 20 CIS rules ────────────────────
    # Structure: rule_id -> vendor_family_substring -> (description, action, pattern, replacement)
    # "cisco" matches cisco_ios / cisco_nxos / cisco_iosxr / cisco_asa
    # "juniper" matches juniper_junos
    # "fortinet" matches fortinet_fortios
    # "palo" matches palo_alto_panos
    # "arista" matches arista_eos
    # "generic" is the fallback for all other vendors
    _FIX_TABLE: Dict[str, Dict[str, tuple]] = {
        # ── Management ───────────────────────────────────────────────────────
        "CIS-MGMT-01": {
            "cisco":   ("Disable Telnet — enforce SSH-only VTY access",
                        "replace", r"transport\s+input\s+telnet",
                        "line vty 0 4\n transport input ssh"),
            "juniper": ("Delete Telnet service",
                        "delete", r"set\s+system\s+services\s+telnet",
                        "delete system services telnet"),
            "fortinet":("Disable Telnet admin access",
                        "append", None,
                        "config system global\n    set admin-telnet disable\nend"),
            "palo":    ("Disable Telnet management",
                        "append", None,
                        "set deviceconfig system permitted-ip"),
            "arista":  ("Disable Telnet",
                        "append", None,
                        "management telnet\n   shutdown"),
            "generic": ("Disable Telnet — enforce SSH",
                        "append", None,
                        "no telnet"),
        },
        "CIS-MGMT-02": {
            "cisco":   ("Enforce SSH version 2",
                        "replace", r"ip\s+ssh\s+version\s+\d+",
                        "ip ssh version 2"),
            "juniper": ("Enforce SSH protocol version v2",
                        "replace", r"set\s+system\s+services\s+ssh\s+protocol-version.*",
                        "set system services ssh protocol-version v2"),
            "fortinet":("Set SSH to version 2 only",
                        "append", None,
                        "config system global\n    set ssh-enc-algo aes256-ctr aes128-ctr\nend"),
            "palo":    ("Enforce SSHv2",
                        "append", None,
                        "set deviceconfig system service disable-telnet yes"),
            "arista":  ("Enforce SSH version 2",
                        "append", None,
                        "management ssh\n   no shutdown"),
            "generic": ("Enforce SSH version 2",
                        "append", None,
                        "ip ssh version 2"),
        },
        "CIS-MGMT-03": {
            "cisco":   ("Disable HTTP management server",
                        "delete", r"ip\s+http\s+server",
                        "no ip http server"),
            "juniper": ("Disable HTTP web management",
                        "delete", r"set\s+system\s+services\s+web-management\s+http",
                        "delete system services web-management http"),
            "fortinet":("Disable HTTP admin access",
                        "append", None,
                        "config system global\n    set admin-port 0\nend"),
            "arista":  ("Disable HTTP management",
                        "append", None,
                        "no management api http-commands"),
            "generic": ("Disable HTTP server",
                        "append", None,
                        "no ip http server"),
        },
        "CIS-MGMT-04": {
            "cisco":   ("Enable HTTPS management server",
                        "append", None,
                        "ip http secure-server"),
            "juniper": ("Enable HTTPS web management",
                        "append", None,
                        "set system services web-management https system-generated-certificate"),
            "fortinet":("Enable HTTPS admin access only",
                        "append", None,
                        "config system global\n    set admin-https-ssl-versions tlsv1-2 tlsv1-3\nend"),
            "arista":  ("Enable HTTPS management",
                        "append", None,
                        "management api http-commands\n   protocol https\n   no shutdown"),
            "generic": ("Enable HTTPS server",
                        "append", None,
                        "ip http secure-server"),
        },
        "CIS-MGMT-05": {
            "cisco":   ("Remove default SNMP community strings",
                        "delete", r"snmp-server\s+community\s+(public|private)\s",
                        "no snmp-server community public\nno snmp-server community private\nsnmp-server community <CHANGE_ME> RO"),
            "juniper": ("Remove default SNMP community strings",
                        "delete", r"set\s+snmp\s+community\s+(public|private)",
                        "delete snmp community public\ndelete snmp community private"),
            "fortinet":("Disable SNMP v1/v2 communities",
                        "append", None,
                        "config system snmp community\n    delete 1\nend"),
            "generic": ("Remove default SNMP community strings",
                        "append", None,
                        "no snmp-server community public\nno snmp-server community private"),
        },
        "CIS-MGMT-06": {
            "cisco":   ("Upgrade SNMP to version 3",
                        "append", None,
                        "snmp-server group NTRO-GROUP v3 priv\nsnmp-server user NTRO-USER NTRO-GROUP v3 auth sha <AUTH_PASS> priv aes 128 <PRIV_PASS>"),
            "juniper": ("Configure SNMP version 3",
                        "append", None,
                        "set snmp v3 usm local-engine user NTRO-USER authentication-md5 authentication-password <AUTH_PASS>"),
            "fortinet":("Enable SNMPv3",
                        "append", None,
                        "config system snmp user\n    edit NTRO-USER\n    set security-level auth-priv\nend"),
            "generic": ("Enable SNMPv3",
                        "append", None,
                        "snmp-server group NTRO-GROUP v3 priv"),
        },
        "CIS-MGMT-07": {
            "cisco":   ("Set SSH idle timeout to 10 minutes",
                        "replace", r"exec-timeout\s+\d+\s+\d+",
                        "line vty 0 4\n exec-timeout 10 0"),
            "juniper": ("Set SSH idle timeout",
                        "replace", r"set\s+system\s+services\s+ssh\s+idle-timeout\s+\d+",
                        "set system services ssh idle-timeout 600"),
            "fortinet":("Set admin idle timeout",
                        "replace", r"set\s+admintimeout\s+\d+",
                        "config system global\n    set admintimeout 10\nend"),
            "arista":  ("Set VTY exec timeout",
                        "append", None,
                        "line vty 0 4\n exec-timeout 10 0"),
            "generic": ("Set session idle timeout",
                        "append", None,
                        "line vty 0 4\n exec-timeout 10 0"),
        },
        "CIS-MGMT-08": {
            "cisco":   ("Restrict management access to specific hosts",
                        "append", None,
                        "ip access-list standard MGMT-ACL\n permit 10.0.0.0 0.0.0.255\n deny   any log\nline vty 0 4\n access-class MGMT-ACL in"),
            "juniper": ("Restrict management to specific prefixes",
                        "append", None,
                        "set system login class MGMT-CLASS allow-commands \".*\"\nset firewall filter MGMT-FILTER term ALLOW-MGMT from source-address 10.0.0.0/24"),
            "fortinet":("Set trusted hosts for admin",
                        "append", None,
                        "config system admin\n    edit admin\n    set trusthost1 10.0.0.0 255.255.255.0\nend"),
            "generic": ("Restrict management to trusted hosts",
                        "append", None,
                        "ip access-list standard MGMT-ACL\n permit 10.0.0.0 0.0.0.255\n deny   any log"),
        },
        # ── Authentication ────────────────────────────────────────────────────
        "CIS-AUTH-01": {
            "cisco":   ("Enable password encryption",
                        "append", None,
                        "service password-encryption"),
            "juniper": ("Enable encrypted password storage",
                        "append", None,
                        "set system login password format sha512"),
            "fortinet":("Use strong password hashing",
                        "append", None,
                        "config system password-policy\n    set status enable\n    set encrypt-algorithm sha256\nend"),
            "generic": ("Enable password encryption",
                        "append", None,
                        "service password-encryption"),
        },
        "CIS-AUTH-02": {
            "cisco":   ("Set minimum password length to 14",
                        "replace", r"security\s+passwords\s+min-length\s+\d+",
                        "security passwords min-length 14"),
            "juniper": ("Set minimum password length",
                        "replace", r"set\s+system\s+login\s+password\s+minimum-length\s+\d+",
                        "set system login password minimum-length 14"),
            "fortinet":("Set minimum password length",
                        "replace", r"set\s+min-length\s+\d+",
                        "config system password-policy\n    set status enable\n    set min-length 14\nend"),
            "arista":  ("Set minimum password length",
                        "append", None,
                        "aaa authorization serial-console\naaa authentication login default local"),
            "generic": ("Set minimum password length to 14",
                        "append", None,
                        "security passwords min-length 14"),
        },
        "CIS-AUTH-03": {
            "cisco":   ("Enable account lockout after failed attempts",
                        "append", None,
                        "login block-for 900 attempts 5 within 300"),
            "juniper": ("Enable lockout on failed login attempts",
                        "append", None,
                        "set system login retry-options tries-before-disconnect 5\nset system login retry-options lockout-period 15"),
            "fortinet":("Enable admin lockout policy",
                        "append", None,
                        "config system global\n    set admin-lockout-duration 900\n    set admin-lockout-threshold 5\nend"),
            "palo":    ("Enable account lockout",
                        "append", None,
                        "set mgt-config password-complexity enabled yes\nset mgt-config password-complexity block-username-inclusion yes"),
            "generic": ("Enable account lockout policy",
                        "append", None,
                        "login block-for 900 attempts 5 within 300"),
        },
        "CIS-AUTH-04": {
            "cisco":   ("Define privilege levels for accounts",
                        "append", None,
                        "username admin privilege 15 secret <ADMIN_PASSWORD>\nusername auditor privilege 5 secret <AUDIT_PASSWORD>"),
            "juniper": ("Configure role-based access levels",
                        "append", None,
                        "set system login class AUDITOR permissions view\nset system login class ADMIN permissions all"),
            "generic": ("Define privilege levels",
                        "append", None,
                        "username admin privilege 15 secret <ADMIN_PASSWORD>"),
        },
        # ── Logging ───────────────────────────────────────────────────────────
        "CIS-LOG-01": {
            "cisco":   ("Enable syslog to remote server",
                        "append", None,
                        "logging host 10.0.0.100\nlogging trap notifications\nlogging on"),
            "juniper": ("Enable syslog to remote server",
                        "append", None,
                        "set system syslog host 10.0.0.100 any notice\nset system syslog host 10.0.0.100 interactive-commands any"),
            "fortinet":("Enable syslog to remote server",
                        "append", None,
                        "config log syslogd setting\n    set status enable\n    set server 10.0.0.100\nend"),
            "palo":    ("Enable syslog profile",
                        "append", None,
                        "set shared log-settings syslog NTRO-SYSLOG server address 10.0.0.100"),
            "arista":  ("Enable syslog",
                        "append", None,
                        "logging host 10.0.0.100\nlogging on"),
            "generic": ("Enable syslog",
                        "append", None,
                        "logging host 10.0.0.100"),
        },
        "CIS-LOG-02": {
            "cisco":   ("Set logging buffer size to 16384 bytes",
                        "replace", r"logging\s+buffered\s+\d+",
                        "logging buffered 16384"),
            "juniper": ("Set syslog archive size",
                        "replace", r"set\s+system\s+syslog\s+archive\s+size\s+\d+",
                        "set system syslog archive size 16384000"),
            "fortinet":("Set log buffer size",
                        "append", None,
                        "config log setting\n    set resolve-ip enable\n    set log-user-in-upper enable\nend"),
            "arista":  ("Set logging buffer size",
                        "replace", r"logging\s+buffered\s+\d+",
                        "logging buffered 16384"),
            "generic": ("Set logging buffer size",
                        "replace", r"logging\s+buffered\s+\d+",
                        "logging buffered 16384"),
        },
        "CIS-LOG-03": {
            "cisco":   ("Enable configuration change logging",
                        "append", None,
                        "archive\n log config\n  logging enable\n  notify syslog"),
            "juniper": ("Enable configuration change logging",
                        "append", None,
                        "set system syslog file config-changes change-log any"),
            "fortinet":("Enable configuration event logging",
                        "append", None,
                        "config log setting\n    set log-user-in-upper enable\nend"),
            "generic": ("Enable config change logging",
                        "append", None,
                        "archive\n log config\n  logging enable"),
        },
        # ── Cryptography ──────────────────────────────────────────────────────
        "CIS-CRYPTO-01": {
            "cisco":   ("Harden SSH cipher suite",
                        "append", None,
                        "ip ssh version 2\nip ssh dh-group-exchange min 2048 max 4096 optimal 4096\nip ssh server algorithm encryption aes256-ctr aes192-ctr aes128-ctr"),
            "juniper": ("Harden SSH ciphers",
                        "append", None,
                        "set system services ssh ciphers aes256-ctr\nset system services ssh ciphers aes128-ctr"),
            "fortinet":("Harden SSH encryption",
                        "append", None,
                        "config system global\n    set ssh-enc-algo aes256-ctr aes128-ctr\nend"),
            "palo":    ("Enable strong SSH ciphers",
                        "append", None,
                        "set deviceconfig system ssh algorithm"),
            "generic": ("Harden SSH cipher suite",
                        "append", None,
                        "ip ssh version 2\nip ssh dh-group-exchange min 2048 max 4096 optimal 4096"),
        },
        "CIS-CRYPTO-02": {
            "cisco":   ("Set minimum TLS version to 1.2",
                        "replace", r"ip\s+http\s+tls-version\s+\S+",
                        "ip http tls-version TLSv1.2"),
            "juniper": ("Enforce TLS 1.2 minimum",
                        "append", None,
                        "set system services web-management https system-generated-certificate\nset system services web-management https ssl-protocols TLSv1.2 TLSv1.3"),
            "fortinet":("Set minimum SSL/TLS version",
                        "append", None,
                        "config system global\n    set ssl-min-proto-version TLSv1-2\nend"),
            "palo":    ("Set minimum TLS version",
                        "append", None,
                        "set deviceconfig system service disable-sslv3 yes"),
            "generic": ("Set minimum TLS to 1.2",
                        "append", None,
                        "ip http tls-version TLSv1.2"),
        },
        "CIS-CRYPTO-03": {
            "cisco":   ("Enable certificate validation for HTTPS",
                        "append", None,
                        "ip http secure-server\nip http authentication certificate"),
            "juniper": ("Enable certificate validation",
                        "append", None,
                        "set security pki ca-profile ROOT-CA ca-identity root-ca"),
            "fortinet":("Enable certificate inspection",
                        "append", None,
                        "config vpn certificate ca\n    edit \"Fortinet_CA\"\nend"),
            "generic": ("Enable certificate validation",
                        "append", None,
                        "ip http secure-server"),
        },
        # ── ACL / Segmentation ────────────────────────────────────────────────
        "CIS-ACL-01": {
            "cisco":   ("Remove any-any permit ACL rules",
                        "delete", r"permit\s+any\s+any",
                        "no access-list <ACL_NUMBER> permit any any"),
            "juniper": ("Remove permit-all firewall rules",
                        "delete", r"set\s+firewall.*permit.*any",
                        "delete firewall filter <FILTER_NAME> term PERMIT-ALL"),
            "fortinet":("Remove permissive firewall policies",
                        "append", None,
                        "config firewall policy\n    edit <POLICY_ID>\n    set action deny\nend"),
            "generic": ("Remove any-any permit rules",
                        "append", None,
                        "no access-list 100 permit any any"),
        },
        "CIS-ACL-02": {
            "cisco":   ("Enable egress filtering",
                        "append", None,
                        "ip access-list extended EGRESS-FILTER\n deny   ip any any log\ninterface GigabitEthernet0/0\n ip access-group EGRESS-FILTER out"),
            "juniper": ("Enable egress firewall filter",
                        "append", None,
                        "set interfaces ge-0/0/0 unit 0 family inet filter output EGRESS-FILTER"),
            "fortinet":("Enable egress firewall policy",
                        "append", None,
                        "config firewall policy\n    edit 0\n    set srcintf \"internal\"\n    set dstintf \"wan1\"\n    set action deny\nend"),
            "generic": ("Enable egress filtering",
                        "append", None,
                        "ip access-list extended EGRESS-FILTER\n deny ip any any log"),
        },
    }

    def _generate_semantic_fix(
        self,
        rule_id: str,
        failed_field: str,
        expected_value,
        current_value,
        vendor: VendorFamily,
    ) -> Optional[Dict]:
        """
        Generate a concrete, vendor-specific remediation fix.

        Uses the _FIX_TABLE keyed by rule_id first, then falls back to
        field-path heuristics for any unmapped rules.
        """
        vendor_name = vendor.value if hasattr(vendor, 'value') else str(vendor)
        vkey = vendor_name.lower()

        # ── Primary: look up the fix table by rule_id ──────────────────────
        rule_entry = self._fix_table.get(rule_id)
        if rule_entry:
            # Find the best matching vendor key
            fix_data = None
            for vendor_key in ["cisco", "juniper", "fortinet", "palo", "arista", "huawei", "mikrotik"]:
                if vendor_key in vkey:
                    fix_data = rule_entry.get(vendor_key)
                    break
            if fix_data is None:
                fix_data = rule_entry.get("generic")
            if fix_data:
                description, action, pattern, replacement = fix_data
                return {
                    "rule_id":        rule_id,
                    "finding_status": "FAIL",
                    "description":    description,
                    "action":         action,
                    "pattern":        pattern,
                    "replacement":    replacement,
                    "command":        replacement,
                    "confidence":     0.88,
                    "vendor_specific": True,
                    "severity":       "HIGH",
                }

        # ── Fallback: field-path heuristics for unmapped rules ─────────────
        cmd = None
        action = "append"
        pattern = None

        if "ssh.protocol_version" in failed_field:
            if "cisco" in vkey:
                cmd = "ip ssh version 2"
                pattern = r"ip\s+ssh\s+version\s+\d+"
                action = "replace"
        elif "telnet.enabled" in failed_field:
            if "cisco" in vkey:
                cmd = "line vty 0 4\n transport input ssh"
                pattern = r"transport\s+input\s+telnet"
                action = "replace"
        elif "http.enabled" in failed_field:
            if "cisco" in vkey:
                cmd = "no ip http server"
                pattern = r"ip\s+http\s+server"
                action = "delete"
        elif "https.enabled" in failed_field:
            if "cisco" in vkey:
                cmd = "ip http secure-server"
        elif "password_policy.encryption_enabled" in failed_field:
            if "cisco" in vkey:
                cmd = "service password-encryption"
        elif "syslog.enabled" in failed_field:
            if "cisco" in vkey:
                cmd = "logging host 10.0.0.100\nlogging on"
        elif "syslog.buffer_size" in failed_field:
            if "cisco" in vkey:
                cmd = "logging buffered 16384"
                pattern = r"logging\s+buffered\s+\d+"
                action = "replace"

        if not cmd:
            return None

        return {
            "rule_id":        rule_id,
            "finding_status": "FAIL",
            "description":    f"Fix for {rule_id}: {failed_field}",
            "action":         action,
            "pattern":        pattern,
            "replacement":    cmd,
            "command":        cmd,
            "confidence":     0.75,
            "vendor_specific": True,
            "severity":       "HIGH",
        }

    def _insecure_pattern_for_field(
        self, field: str, current_value, vendor: VendorFamily
    ) -> Optional[str]:
        """
        Generate a regex pattern to find the insecure configuration being disabled.
        """
        vendor_name = vendor.value if hasattr(vendor, 'value') else str(vendor)

        if "telnet" in field:
            if "cisco" in vendor_name.lower():
                return r"transport\s+input\s+.*telnet"
            elif "juniper" in vendor_name.lower():
                return r"set\s+system\s+services\s+telnet"
            return r"telnet"

        if "http.enabled" in field:
            if "cisco" in vendor_name.lower():
                return r"ip\s+http\s+server"
            elif "juniper" in vendor_name.lower():
                return r"set\s+system\s+services\s+web-management\s+http"
            return r"http\s+server"

        return None

    def _existing_pattern_for_field(
        self, field: str, vendor: VendorFamily
    ) -> Optional[str]:
        """
        Generate a regex pattern to find existing configuration for this field.

        Used for replace operations where we need to update, not append.
        """
        vendor_name = vendor.value if hasattr(vendor, 'value') else str(vendor)

        if "ssh.protocol_version" in field or "ssh.enabled" in field:
            if "cisco" in vendor_name.lower():
                return r"ip\s+ssh\s+version\s+\d+"
            elif "juniper" in vendor_name.lower():
                return r"set\s+system\s+services\s+ssh\s+protocol-version.*"

        if "ssh.idle_timeout" in field:
            if "cisco" in vendor_name.lower():
                return r"exec-timeout\s+\d+\s+\d+"
            elif "juniper" in vendor_name.lower():
                return r"set\s+system\s+services\s+ssh\s+idle-timeout\s+\d+"

        if "tls.min_version" in field:
            if "cisco" in vendor_name.lower():
                return r"ip\s+http\s+tls-version\s+\S+"
            return r"tls[-_]version\s+\S+"

        return None

    def batch_propose(
        self,
        findings: List[ComplianceFinding],
        vendor: VendorFamily,
        filename: str,
    ) -> Dict[str, List[Dict]]:
        """
        Propose fixes for multiple findings, grouped by rule_id.

        Returns: {rule_id: [fix1, fix2, ...]}
        """
        fixes_by_rule: Dict[str, List[Dict]] = {}

        for finding in findings:
            if not _is_fail(finding.status):
                continue

            rule_fixes = self.propose_fixes(finding, vendor, filename)
            rule_id = finding.rule_id

            if rule_id not in fixes_by_rule:
                fixes_by_rule[rule_id] = []

            fixes_by_rule[rule_id].extend(rule_fixes)

        return fixes_by_rule

    def estimate_fix_confidence(self, fixes: List[Dict]) -> float:
        """
        Compute aggregate confidence across a set of proposed fixes.

        Returns average confidence, weighted by whether fixes are vendor-specific.
        """
        if not fixes:
            return 0.0

        total = 0.0
        for fix in fixes:
            confidence = fix.get("confidence", 0.5)
            if fix.get("vendor_specific"):
                confidence *= 1.1  # Slight boost for vendor-matched fixes
            total += min(confidence, 1.0)

        return round(total / len(fixes), 3)
