"""
Deterministic Compliance Rule Engine — SIH26155 (Cell 3)
===========================================================

This module NEVER imports an LLM client and NEVER makes a network call.
It consumes:
  - a validated SecurityBaseline instance (produced by Cell 1 / Cell 2)
  - cis_rules.yaml (declarative rule definitions, no PASS/FAIL logic inside)

and produces ComplianceFinding objects with a strictly deterministic status,
per this decision table:

    explicitly_configured=True  + confidence >= min_confidence + matches expected  -> PASS
    explicitly_configured=True  + confidence >= min_confidence + fails expected    -> FAIL
    explicitly_configured=False + vendor's default for this field is KNOWN insecure -> FAIL
    explicitly_configured=False + vendor's default is unknown/not listed           -> NEEDS_HUMAN_REVIEW
    confidence <  min_confidence  (regardless of the above)                        -> NEEDS_HUMAN_REVIEW

Run this file directly to evaluate the example SecurityBaseline from
security_baseline_schema.py against cis_rules.yaml and print a findings table.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

import yaml

from security_baseline_schema import (
    ComplianceFinding,
    ComplianceFramework,
    EvidenceField,
    FindingStatus,
    SecurityBaseline,
    Severity,
    VendorFamily,
)

RULES_FILE = Path(__file__).parent / "cis_rules.yaml"


# ---------------------------------------------------------------------------
# Field resolver
# ---------------------------------------------------------------------------

def resolve_evidence_field(baseline: SecurityBaseline, dotted_path: str) -> EvidenceField:
    """
    Resolves a scalar dotted path (e.g. 'management.telnet.enabled') to the
    EvidenceField object itself — never to just its .value — so the engine
    can separately inspect .value, .explicitly_configured, .source, and
    .interpretation.confidence.
    """
    obj: Any = baseline
    for part in dotted_path.split("."):
        obj = getattr(obj, part)
    if not isinstance(obj, EvidenceField):
        raise TypeError(
            f"Path '{dotted_path}' resolved to {type(obj)}, expected EvidenceField. "
            "Check the rule's baseline_field_path against the schema."
        )
    return obj


def resolve_list_evidence_fields(baseline: SecurityBaseline, list_path: str) -> List[EvidenceField]:
    """
    Resolves paths of the form 'access_control.acl_rules[].is_any_any_permit'
    to a list of EvidenceField objects, one per item in the list.
    """
    assert list_path.count("[]") == 1, "Only single-level list paths are supported"
    container_path, leaf_attr = list_path.split("[].")
    obj: Any = baseline
    for part in container_path.split("."):
        obj = getattr(obj, part)
    if not isinstance(obj, list):
        raise TypeError(f"Path '{container_path}' did not resolve to a list")
    return [getattr(item, leaf_attr) for item in obj]


# ---------------------------------------------------------------------------
# Predicate evaluation
# ---------------------------------------------------------------------------

def _normalize(value: Any) -> Any:
    """Enums compare by .value; everything else passes through."""
    return getattr(value, "value", value)


def evaluate_predicate(value: Any, operator: str, expected: Any) -> bool:
    value = _normalize(value)
    if isinstance(expected, list):
        expected = [_normalize(e) for e in expected]

    if operator == "equals":
        return value == expected
    if operator == "not_equals":
        return value != expected
    if operator == "in":
        return value in expected
    if operator == "not_in":
        return value not in expected
    if operator == "greater_than_or_equal":
        return value is not None and value >= expected
    if operator == "less_than_or_equal":
        return value is not None and value <= expected
    raise ValueError(f"Unsupported scalar operator: {operator}")


def evaluate_list_predicate(values: List[Any], operator: str, expected: Any) -> bool:
    values = [_normalize(v) for v in values]
    if operator == "list_none_true":
        return not any(v is True for v in values)
    if operator == "list_all_true":
        return all(v is True for v in values) if values else True
    raise ValueError(f"Unsupported list operator: {operator}")


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------

def evaluate_rule(baseline: SecurityBaseline, rule: dict) -> ComplianceFinding:
    field_path: str = rule["baseline_field_path"]
    min_confidence: float = rule["evidence"].get("minimum_confidence", 0.75)
    require_explicit: bool = rule["evidence"].get("require_explicit_configuration", True)
    vendor = baseline.device.vendor
    known_defaults = rule.get("known_insecure_defaults", {}) or {}

    if "[]" in field_path:
        fields = resolve_list_evidence_fields(baseline, field_path)
        if not fields:
            return _finding(baseline, rule, FindingStatus.NOT_APPLICABLE, evidence_field=None)

        min_conf = min((f.interpretation.confidence for f in fields), default=0.0)
        all_explicit = all(f.explicitly_configured for f in fields)

        if min_conf < min_confidence:
            return _finding(baseline, rule, FindingStatus.NEEDS_HUMAN_REVIEW, evidence_field=fields[0])

        if require_explicit and not all_explicit:
            return _finding(baseline, rule, FindingStatus.NEEDS_HUMAN_REVIEW, evidence_field=fields[0])

        compliant = evaluate_list_predicate(
            [f.value for f in fields], rule["evaluation"]["operator"], rule["evaluation"]["expected"]
        )
        status = FindingStatus.PASS if compliant else FindingStatus.FAIL
        return _finding(baseline, rule, status, evidence_field=fields[0])

    ef = resolve_evidence_field(baseline, field_path)
    confidence = ef.interpretation.confidence

    if confidence < min_confidence:
        return _finding(baseline, rule, FindingStatus.NEEDS_HUMAN_REVIEW, evidence_field=ef)

    if require_explicit and not ef.explicitly_configured:
        vendor_key = vendor.value if isinstance(vendor, VendorFamily) else str(vendor)
        if vendor_key in known_defaults:
            status = FindingStatus.FAIL if known_defaults[vendor_key] else FindingStatus.PASS
        else:
            status = FindingStatus.NEEDS_HUMAN_REVIEW
        return _finding(baseline, rule, status, evidence_field=ef)

    compliant = evaluate_predicate(ef.value, rule["evaluation"]["operator"], rule["evaluation"]["expected"])
    status = FindingStatus.PASS if compliant else FindingStatus.FAIL
    return _finding(baseline, rule, status, evidence_field=ef)


def _finding(
    baseline: SecurityBaseline,
    rule: dict,
    status: FindingStatus,
    evidence_field: Optional[EvidenceField],
) -> ComplianceFinding:
    return ComplianceFinding(
        device_id=baseline.device.device_id,
        framework=ComplianceFramework(rule["framework"]),
        rule_id=rule["id"],
        baseline_field_path=rule["baseline_field_path"],
        status=status,
        severity=Severity(rule["severity"]),
        evidence=evidence_field if evidence_field is not None else EvidenceField.unknown(),
    )


def load_rules(path: Path = RULES_FILE) -> List[dict]:
    with open(path) as f:
        doc = yaml.safe_load(f)
    return doc["rules"]


def evaluate_baseline(baseline: SecurityBaseline, rules: Optional[List[dict]] = None) -> List[ComplianceFinding]:
    rules = rules if rules is not None else load_rules()
    return [evaluate_rule(baseline, rule) for rule in rules]


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from security_baseline_schema import (
        AccessControlConfig, ACLRule, AdminEventLogging, AuditConfig,
        AuthenticationConfig, CryptographyConfig, DeviceCategory, DeviceIdentity,
        HTTPConfig, HTTPSConfig, InsecureServicesConfig, Interpretation,
        InterpretationMethod, LoggingConfig, ManagementAccessConfig,
        ManagementPlane, MFAConfig, AccountLockout, NetworkServicesConfig,
        PasswordPolicy, ProvenanceSource, SecurityBaselineMetadata,
        SecurityControlsConfig, ServiceState, SNMPConfig, SSHConfig,
        SyslogConfig, TelnetConfig, TLSConfig,
    )

    def ef(value, method=InterpretationMethod.DETERMINISTIC_PARSER, confidence=1.0,
           explicit=True, raw=None, line=None):
        return EvidenceField(
            value=value,
            explicitly_configured=explicit,
            source=ProvenanceSource(file="device01.conf", line=line, raw=raw) if raw else None,
            interpretation=Interpretation(method=method, confidence=confidence),
        )

    baseline = SecurityBaseline(
        device=DeviceIdentity(
            hostname="edge-fw-01", vendor=VendorFamily.CISCO_IOS, model="ISR4331",
            firmware_version="17.3", category=DeviceCategory.ROUTER,
            config_file_name="device01.conf",
        ),
        management=ManagementPlane(
            ssh=SSHConfig(
                enabled=ef(ServiceState.ENABLED, raw="ip ssh version 2", line=10),
                protocol_version=ef(2, raw="ip ssh version 2", line=10),
                idle_timeout_seconds=ef(300, raw="exec-timeout 5 0", line=15),
            ),
            telnet=TelnetConfig(enabled=ef(ServiceState.ENABLED, explicit=False, confidence=0.6)),
            http=HTTPConfig(enabled=ef(ServiceState.DISABLED, raw="no ip http server", line=20)),
            https=HTTPSConfig(enabled=ef(ServiceState.ENABLED, raw="ip http secure-server", line=21)),
            snmp=SNMPConfig(
                enabled=ef(ServiceState.ENABLED, raw="snmp-server community public RO", line=30),
                version=ef("2c", raw="snmp-server community public RO", line=30),
                community_strings_default=ef(True, raw="snmp-server community public RO", line=30),
            ),
        ),
        authentication=AuthenticationConfig(
            password_policy=PasswordPolicy(
                encryption_enabled=ef(True, raw="service password-encryption", line=5),
                min_length=ef(8, raw="security passwords min-length 8", line=6),
            ),
            mfa=MFAConfig(),
            account_lockout=AccountLockout(enabled=ef(False, explicit=False, confidence=0.5)),
            privilege_levels_defined=ef(False, explicit=False, confidence=0.5),
        ),
        cryptography=CryptographyConfig(
            tls=TLSConfig(min_version=ef("1.0", raw="ip http tls-version TLSv1.0", line=22)),
            ssh_ciphers_hardened=ef(False, explicit=False, confidence=0.5),
            certificate_validation_enabled=ef(False, explicit=False, confidence=0.5),
        ),
        access_control=AccessControlConfig(
            acl_rules=[
                ACLRule(rule_id="101", action=ef("permit"), is_any_any_permit=ef(True, raw="access-list 101 permit ip any any", line=40)),
            ],
            management_access=ManagementAccessConfig(
                restricted_to_specific_hosts=ef(False, explicit=False, confidence=0.5),
            ),
        ),
        logging=LoggingConfig(
            syslog=SyslogConfig(
                enabled=ef(True, raw="logging host 10.0.0.5", line=50),
                buffer_size=ef(32768, raw="logging buffered 32768", line=51),
            ),
            audit=AuditConfig(),
            administrative_events=AdminEventLogging(
                config_change_events_logged=ef(False, explicit=False, confidence=0.5),
            ),
        ),
        network_services=NetworkServicesConfig(insecure_services=InsecureServicesConfig()),
        security_controls=SecurityControlsConfig(
            egress_filtering_enabled=ef(False, explicit=False, confidence=0.5),
        ),
        metadata=SecurityBaselineMetadata(overall_confidence=0.78),
    )

    findings = evaluate_baseline(baseline)

    print(f"{'RULE ID':<16}{'STATUS':<20}{'SEVERITY':<10}FIELD")
    print("-" * 90)
    for f in findings:
        print(f"{f.rule_id:<16}{f.status.value:<20}{f.severity.value:<10}{f.baseline_field_path}")

    summary = {}
    for f in findings:
        summary[f.status.value] = summary.get(f.status.value, 0) + 1
    print("\nSummary:", summary)
