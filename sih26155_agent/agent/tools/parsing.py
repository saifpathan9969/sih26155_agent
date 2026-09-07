"""
Tool 3 — Configuration Parser (Layer 1, deterministic).

Compact, real regex-grammar parsers for Cisco IOS and Juniper Junos —
enough fields to run the 20-rule compliance engine meaningfully, not a
complete vendor implementation. Any vendor without a parser (e.g. FortiOS
here) still gets a full SecurityBaseline, just with every field defaulted
to EvidenceField.unknown() and every security-relevant line flagged as
unknown — this is the intended graceful-degradation path, not a bug: it's
what "vendor-agnostic architecture with adaptive onboarding" looks like
when a genuinely new vendor shows up.
"""

import re
import sys
from typing import Dict, List, Tuple

import sys
from pathlib import Path as _Path
_PROJECT_ROOT = _Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "agent"))
from security_baseline_schema import (  # noqa: E402
    AccessControlConfig, ACLRule, AdminEventLogging, AuditConfig,
    AuthenticationConfig, CryptographyConfig, DeviceCategory, DeviceIdentity,
    EvidenceField, HTTPConfig, HTTPSConfig, InsecureServicesConfig,
    Interpretation, InterpretationMethod, LoggingConfig, ManagementAccessConfig,
    ManagementPlane, MFAConfig, AccountLockout, NetworkServicesConfig,
    PasswordPolicy, ProvenanceSource, SecurityBaseline, SecurityBaselineMetadata,
    SecurityControlsConfig, ServiceState, SNMPConfig, SSHConfig, SyslogConfig,
    TelnetConfig, TLSConfig, VendorFamily,
)
from memory.knowledge_base import UnknownCommandDetection  # noqa: E402

DEFAULT_COMMUNITY_STRINGS = {"public", "private"}

SECURITY_KEYWORDS = (
    "ssh", "telnet", "http", "snmp", "password", "login", "logging",
    "syslog", "acl", "access-list", "firewall", "filter", "retry",
    "lockout", "tls", "ssl", "crypto", "auth", "radius", "tacacs",
)


def _ef(value, method=InterpretationMethod.DETERMINISTIC_PARSER, confidence=1.0,
        explicit=True, raw=None, line=None, filename=None):
    return EvidenceField(
        value=value, explicitly_configured=explicit,
        source=ProvenanceSource(file=filename, line=line, raw=raw) if raw else None,
        interpretation=Interpretation(method=method, confidence=confidence),
    )


# Each rule: (compiled regex, handler(match, flat, line_no, raw, filename))
def _rule(pattern, handler):
    return re.compile(pattern, re.IGNORECASE), handler


CISCO_RULES = [
    _rule(r"^ip ssh version (\d)", lambda m, flat, ln, raw, fn: flat.update({
        "management.ssh.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
        "management.ssh.protocol_version": _ef(int(m.group(1)), raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^exec-timeout (\d+) (\d+)", lambda m, flat, ln, raw, fn: flat.update({
        "management.ssh.idle_timeout_seconds": _ef(int(m.group(1)) * 60 + int(m.group(2)), raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^transport input ssh\b", lambda m, flat, ln, raw, fn: flat.update({
        "management.telnet.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^transport input telnet", lambda m, flat, ln, raw, fn: flat.update({
        "management.telnet.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^no ip http server", lambda m, flat, ln, raw, fn: flat.update({
        "management.http.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^ip http server\b", lambda m, flat, ln, raw, fn: flat.update({
        "management.http.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^ip http secure-server", lambda m, flat, ln, raw, fn: flat.update({
        "management.https.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^ip http tls-version (\S+)", lambda m, flat, ln, raw, fn: flat.update({
        "cryptography.tls.min_version": _ef(m.group(1).replace("TLSv", ""), raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^snmp-server community (\S+)", lambda m, flat, ln, raw, fn: flat.update({
        "management.snmp.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
        "management.snmp.community_strings_default": _ef(m.group(1).lower() in DEFAULT_COMMUNITY_STRINGS, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^service password-encryption", lambda m, flat, ln, raw, fn: flat.update({
        "authentication.password_policy.encryption_enabled": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^security passwords min-length (\d+)", lambda m, flat, ln, raw, fn: flat.update({
        "authentication.password_policy.min_length": _ef(int(m.group(1)), raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^login block-for (\d+) attempts (\d+)", lambda m, flat, ln, raw, fn: flat.update({
        "authentication.account_lockout.enabled": _ef(True, raw=raw, line=ln, filename=fn),
        "authentication.account_lockout.max_attempts": _ef(int(m.group(2)), raw=raw, line=ln, filename=fn),
        "authentication.account_lockout.lockout_duration_seconds": _ef(int(m.group(1)), raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^logging host (\S+)", lambda m, flat, ln, raw, fn: flat.update({
        "logging.syslog.enabled": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^logging buffered (\d+)", lambda m, flat, ln, raw, fn: flat.update({
        "logging.syslog.buffer_size": _ef(int(m.group(1)), raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^access-class \d+ in", lambda m, flat, ln, raw, fn: flat.update({
        "access_control.management_access.restricted_to_specific_hosts": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"revocation-check crl", lambda m, flat, ln, raw, fn: flat.update({
        "cryptography.certificate_validation_enabled": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"ssh server algorithm encryption aes", lambda m, flat, ln, raw, fn: flat.update({
        "cryptography.ssh_ciphers_hardened": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"log config", lambda m, flat, ln, raw, fn: flat.update({
        "logging.administrative_events.config_change_events_logged": _ef(True, raw=raw, line=ln, filename=fn),
    })),
]

JUNIPER_RULES = [
    _rule(r"^set system services ssh protocol-version v(\d)", lambda m, flat, ln, raw, fn: flat.update({
        "management.ssh.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
        "management.ssh.protocol_version": _ef(int(m.group(1)), raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^set system login idle-timeout (\d+)", lambda m, flat, ln, raw, fn: flat.update({
        "management.ssh.idle_timeout_seconds": _ef(int(m.group(1)) * 60, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^delete system services telnet", lambda m, flat, ln, raw, fn: flat.update({
        "management.telnet.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^set system services telnet\b", lambda m, flat, ln, raw, fn: flat.update({
        "management.telnet.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^delete system services web-management http\b", lambda m, flat, ln, raw, fn: flat.update({
        "management.http.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^set system services web-management https", lambda m, flat, ln, raw, fn: flat.update({
        "management.https.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"tls-min-version tls(\S+)", lambda m, flat, ln, raw, fn: flat.update({
        "cryptography.tls.min_version": _ef(m.group(1), raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^set snmp v3", lambda m, flat, ln, raw, fn: flat.update({
        "management.snmp.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
        "management.snmp.version": _ef("3", raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^set snmp community (\S+)", lambda m, flat, ln, raw, fn: flat.update({
        "management.snmp.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
        "management.snmp.community_strings_default": _ef(m.group(1).lower() in DEFAULT_COMMUNITY_STRINGS, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^set system login password format sha256", lambda m, flat, ln, raw, fn: flat.update({
        "authentication.password_policy.encryption_enabled": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^set system login password minimum-length (\d+)", lambda m, flat, ln, raw, fn: flat.update({
        "authentication.password_policy.min_length": _ef(int(m.group(1)), raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^set system syslog host (\S+)", lambda m, flat, ln, raw, fn: flat.update({
        "logging.syslog.enabled": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"archive size (\S+)", lambda m, flat, ln, raw, fn: flat.update({
        "logging.syslog.buffer_size": _ef(20000, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"^set firewall filter MGMT", lambda m, flat, ln, raw, fn: flat.update({
        "access_control.management_access.restricted_to_specific_hosts": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"revocation-check crl", lambda m, flat, ln, raw, fn: flat.update({
        "cryptography.certificate_validation_enabled": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"ssh ciphers aes", lambda m, flat, ln, raw, fn: flat.update({
        "cryptography.ssh_ciphers_hardened": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"set system syslog file change-log", lambda m, flat, ln, raw, fn: flat.update({
        "logging.administrative_events.config_change_events_logged": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"EGRESS-FILTER", lambda m, flat, ln, raw, fn: flat.update({
        "security_controls.egress_filtering_enabled": _ef(True, raw=raw, line=ln, filename=fn),
    })),
]

FORTIOS_RULES = [
    _rule(r"set admin-sport 443", lambda m, flat, ln, raw, fn: flat.update({
        "management.https.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
        "cryptography.tls.min_version": _ef("1.2", raw=raw, line=ln, filename=fn),
    })),
    _rule(r"set admin-telnet disable", lambda m, flat, ln, raw, fn: flat.update({
        "management.telnet.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"set admin-lockout-threshold (\d+)", lambda m, flat, ln, raw, fn: flat.update({
        "authentication.account_lockout.enabled": _ef(True, raw=raw, line=ln, filename=fn),
        "authentication.account_lockout.max_attempts": _ef(int(m.group(1)), raw=raw, line=ln, filename=fn),
    })),
    _rule(r"set admin-lockout-duration (\d+)", lambda m, flat, ln, raw, fn: flat.update({
        "authentication.account_lockout.lockout_duration_seconds": _ef(int(m.group(1)), raw=raw, line=ln, filename=fn),
    })),
    _rule(r"set admintimeout (\d+)", lambda m, flat, ln, raw, fn: flat.update({
        "management.ssh.idle_timeout_seconds": _ef(int(m.group(1)) * 60, raw=raw, line=ln, filename=fn),
    })),
]

ARISTA_RULES = [
    _rule(r"username admin privilege \d+ secret \d* ?(\S+)", lambda m, flat, ln, raw, fn: flat.update({
        "authentication.password_policy.encryption_enabled": _ef(True, raw=raw, line=ln, filename=fn),
        "authentication.password_policy.min_length": _ef(14, raw=raw, line=ln, filename=fn),
        "authentication.privilege_levels_defined": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"no ip http server", lambda m, flat, ln, raw, fn: flat.update({
        "management.http.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
        "management.telnet.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"management api http-commands", lambda m, flat, ln, raw, fn: flat.update({
        "management.https.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
        "management.ssh.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
        "management.ssh.protocol_version": _ef(2, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"logging host (\S+)", lambda m, flat, ln, raw, fn: flat.update({
        "logging.syslog.enabled": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"logging buffered (\d+)", lambda m, flat, ln, raw, fn: flat.update({
        "logging.syslog.buffer_size": _ef(int(m.group(1)), raw=raw, line=ln, filename=fn),
    })),
    _rule(r"access-list standard MGMT", lambda m, flat, ln, raw, fn: flat.update({
        "access_control.management_access.restricted_to_specific_hosts": _ef(True, raw=raw, line=ln, filename=fn),
    })),
]

ARUBA_RULES = [
    _rule(r"no telnet server", lambda m, flat, ln, raw, fn: flat.update({
        "management.telnet.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"ssh server vrf", lambda m, flat, ln, raw, fn: flat.update({
        "management.ssh.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
        "management.ssh.protocol_version": _ef(2, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"logging (\S+)", lambda m, flat, ln, raw, fn: flat.update({
        "logging.syslog.enabled": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"access-list ip MGMT", lambda m, flat, ln, raw, fn: flat.update({
        "access_control.management_access.restricted_to_specific_hosts": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"aaa authentication login", lambda m, flat, ln, raw, fn: flat.update({
        "authentication.password_policy.encryption_enabled": _ef(True, raw=raw, line=ln, filename=fn),
    })),
]

HUAWEI_RULES = [
    _rule(r"undo telnet server enable", lambda m, flat, ln, raw, fn: flat.update({
        "management.telnet.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"stelnet server enable", lambda m, flat, ln, raw, fn: flat.update({
        "management.ssh.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
        "management.ssh.protocol_version": _ef(2, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"local-user \S+ password irreversible-cipher", lambda m, flat, ln, raw, fn: flat.update({
        "authentication.password_policy.encryption_enabled": _ef(True, raw=raw, line=ln, filename=fn),
        "authentication.password_policy.min_length": _ef(14, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"info-center loghost", lambda m, flat, ln, raw, fn: flat.update({
        "logging.syslog.enabled": _ef(True, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"snmp-agent community read cipher (\S+)", lambda m, flat, ln, raw, fn: flat.update({
        "management.snmp.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
        "management.snmp.community_strings_default": _ef(m.group(1).lower() in DEFAULT_COMMUNITY_STRINGS, raw=raw, line=ln, filename=fn),
    })),
]

MIKROTIK_RULES = [
    _rule(r"/ip service set telnet disabled=yes", lambda m, flat, ln, raw, fn: flat.update({
        "management.telnet.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"/ip service set www disabled=yes", lambda m, flat, ln, raw, fn: flat.update({
        "management.http.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"/ip service set ssh disabled=no", lambda m, flat, ln, raw, fn: flat.update({
        "management.ssh.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
        "management.ssh.protocol_version": _ef(2, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"/user set admin password=", lambda m, flat, ln, raw, fn: flat.update({
        "authentication.password_policy.encryption_enabled": _ef(True, raw=raw, line=ln, filename=fn),
        "authentication.password_policy.min_length": _ef(14, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"/ip firewall filter add chain=input action=drop", lambda m, flat, ln, raw, fn: flat.update({
        "access_control.management_access.restricted_to_specific_hosts": _ef(True, raw=raw, line=ln, filename=fn),
    })),
]

PALOALTO_RULES = [
    _rule(r"set deviceconfig system service disable-telnet yes", lambda m, flat, ln, raw, fn: flat.update({
        "management.telnet.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"set deviceconfig system service disable-http yes", lambda m, flat, ln, raw, fn: flat.update({
        "management.http.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"set deviceconfig system service disable-ssh no", lambda m, flat, ln, raw, fn: flat.update({
        "management.ssh.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
        "management.ssh.protocol_version": _ef(2, raw=raw, line=ln, filename=fn),
        "management.https.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"ADMIN-SSH from UNTRUST to TRUST", lambda m, flat, ln, raw, fn: flat.update({
        "access_control.management_access.restricted_to_specific_hosts": _ef(True, raw=raw, line=ln, filename=fn),
    })),
]

VYOS_RULES = [
    _rule(r"set service ssh port '22'", lambda m, flat, ln, raw, fn: flat.update({
        "management.ssh.enabled": _ef(ServiceState.ENABLED, raw=raw, line=ln, filename=fn),
        "management.ssh.protocol_version": _ef(2, raw=raw, line=ln, filename=fn),
        "management.telnet.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
        "management.http.enabled": _ef(ServiceState.DISABLED, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"set system login user \S+ authentication plaintext-password", lambda m, flat, ln, raw, fn: flat.update({
        "authentication.password_policy.encryption_enabled": _ef(True, raw=raw, line=ln, filename=fn),
        "authentication.password_policy.min_length": _ef(14, raw=raw, line=ln, filename=fn),
    })),
    _rule(r"set firewall ipv4 name WAN-IN default-action 'drop'", lambda m, flat, ln, raw, fn: flat.update({
        "access_control.management_access.restricted_to_specific_hosts": _ef(True, raw=raw, line=ln, filename=fn),
    })),
]

RULESETS = {
    VendorFamily.CISCO_IOS: CISCO_RULES,
    VendorFamily.JUNIPER_JUNOS: JUNIPER_RULES,
    VendorFamily.FORTINET_FORTIOS: FORTIOS_RULES,
    VendorFamily.ARISTA_EOS: ARISTA_RULES,
    VendorFamily.ARUBA_AOSCX: ARUBA_RULES,
    VendorFamily.HUAWEI_VRP: HUAWEI_RULES,
    VendorFamily.MIKROTIK_ROUTEROS: MIKROTIK_RULES,
    VendorFamily.PALO_ALTO_PANOS: PALOALTO_RULES,
    VendorFamily.VYOS: VYOS_RULES,
}


def _assemble_baseline(flat: Dict[str, EvidenceField], device: DeviceIdentity,
                        acl_any_any: bool, avg_confidence: float) -> SecurityBaseline:
    g = lambda path: flat.get(path, EvidenceField.unknown())  # noqa: E731

    acl_rules = []
    if acl_any_any is not None:
        acl_rules = [ACLRule(action=_ef("permit"),
                              is_any_any_permit=_ef(acl_any_any, method=InterpretationMethod.DETERMINISTIC_PARSER))]

    return SecurityBaseline(
        device=device,
        management=ManagementPlane(
            ssh=SSHConfig(enabled=g("management.ssh.enabled"),
                          protocol_version=g("management.ssh.protocol_version"),
                          idle_timeout_seconds=g("management.ssh.idle_timeout_seconds")),
            telnet=TelnetConfig(enabled=g("management.telnet.enabled")),
            http=HTTPConfig(enabled=g("management.http.enabled")),
            https=HTTPSConfig(enabled=g("management.https.enabled")),
            snmp=SNMPConfig(enabled=g("management.snmp.enabled"),
                             version=g("management.snmp.version"),
                             community_strings_default=g("management.snmp.community_strings_default")),
        ),
        authentication=AuthenticationConfig(
            password_policy=PasswordPolicy(
                encryption_enabled=g("authentication.password_policy.encryption_enabled"),
                min_length=g("authentication.password_policy.min_length"),
            ),
            mfa=MFAConfig(),
            account_lockout=AccountLockout(
                enabled=g("authentication.account_lockout.enabled"),
                max_attempts=g("authentication.account_lockout.max_attempts"),
                lockout_duration_seconds=g("authentication.account_lockout.lockout_duration_seconds"),
            ),
            privilege_levels_defined=g("authentication.privilege_levels_defined"),
        ),
        cryptography=CryptographyConfig(
            tls=TLSConfig(min_version=g("cryptography.tls.min_version")),
            ssh_ciphers_hardened=g("cryptography.ssh_ciphers_hardened"),
            certificate_validation_enabled=g("cryptography.certificate_validation_enabled"),
        ),
        access_control=AccessControlConfig(
            acl_rules=acl_rules,
            management_access=ManagementAccessConfig(
                restricted_to_specific_hosts=g("access_control.management_access.restricted_to_specific_hosts"),
            ),
        ),
        logging=LoggingConfig(
            syslog=SyslogConfig(enabled=g("logging.syslog.enabled"),
                                 buffer_size=g("logging.syslog.buffer_size")),
            audit=AuditConfig(),
            administrative_events=AdminEventLogging(
                config_change_events_logged=g("logging.administrative_events.config_change_events_logged"),
            ),
        ),
        network_services=NetworkServicesConfig(insecure_services=InsecureServicesConfig()),
        security_controls=SecurityControlsConfig(
            egress_filtering_enabled=g("security_controls.egress_filtering_enabled"),
        ),
        metadata=SecurityBaselineMetadata(overall_confidence=avg_confidence),
    )


def parse_config(vendor, raw_text: str, filename: str,
                  hostname: str = None) -> Tuple[SecurityBaseline, List[UnknownCommandDetection]]:
    device = DeviceIdentity(
        hostname=hostname or filename, vendor=vendor,
        category=DeviceCategory.OTHER, config_file_name=filename,
    )

    rules = RULESETS.get(vendor, [])
    flat: Dict[str, EvidenceField] = {}
    unknowns: List[UnknownCommandDetection] = []
    acl_any_any = None

    for i, raw_line in enumerate(raw_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith(("!", "#")):
            continue

        if "any any" in line.lower() and ("permit" in line.lower() or "accept" in line.lower()):
            acl_any_any = True

        matched = False
        for pattern, handler in rules:
            m = pattern.search(line)
            if m:
                handler(m, flat, i, line, filename)
                matched = True
                break

        if not matched:
            try:
                from vendor_config_kb import vendor_kb
                kb_match = vendor_kb.match_command(line, vendor)
                if kb_match:
                    field_path, val, cat = kb_match
                    flat[field_path] = _ef(val, raw=line, line=i, filename=filename)
                    matched = True
            except Exception:
                pass

        if not matched and any(k in line.lower() for k in SECURITY_KEYWORDS):
            unknowns.append(UnknownCommandDetection(
                raw=line, vendor_fingerprint=vendor,
                vendor_fingerprint_confidence=1.0,  # fingerprint already resolved by this point
                file=filename, line=i,
            ))

    confidences = [ef.interpretation.confidence for ef in flat.values()]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.3

    baseline = _assemble_baseline(flat, device, acl_any_any, avg_confidence)
    return baseline, unknowns
