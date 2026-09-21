"""
Universal Security Baseline Schema
===================================
SIH26155 — AI-Driven Multi-Vendor Network Security Compliance Auditor
Organization: NTRO

PURPOSE
-------
This is the single source of truth every cell (team) codes against.

    Cell 1 (Parser/Vendor Engine)  -> produces EvidenceField values via
                                       InterpretationMethod.DETERMINISTIC_PARSER
    Cell 2 (AI/ML Engine)          -> produces EvidenceField values via
                                       InterpretationMethod.AI_SEMANTIC_MAPPING,
                                       or HUMAN_ANNOTATED after a training-loop
                                       correction
    Cell 3 (Compliance Engine)     -> reads ONLY validated SecurityBaseline
                                       instances. It NEVER talks to an LLM and
                                       NEVER trusts raw config text.
    Cell 4 (Attack/Risk Engine)    -> reads SecurityBaseline + Findings
    Cell 5 (Remediation Engine)    -> reads Findings + Device.vendor/firmware
    Cell 6 (Platform/UI)           -> renders everything below, including the
                                       Interactive Training Interface

DESIGN PRINCIPLES
------------------
1. The LLM is NEVER authoritative for compliance. It only ever produces a
   normalized, evidenced, confidence-scored VALUE. Pass/Fail is decided
   later, deterministically, by Cell 3's rule engine against this schema.

2. Every leaf security-relevant field is wrapped in `EvidenceField`, which
   carries:
     - the value itself
     - where it came from (file/line/raw CLI text) -> provenance
     - HOW it was derived (parser vs AI vs human-corrected) -> interpretation
     - a calibrated confidence score (NOT LLM self-reported — see
       `Interpretation.confidence` docstring)
     - whether it was explicitly present in the config, or is an assumed
       vendor default (critical: "telnet absent from config" often means
       "telnet is ON by default" on some platforms — silence is not safety)

3. Absence of evidence is itself evidence. `explicitly_configured=False`
   plus a `default_assumed` interpretation method forces the compliance
   engine (and a human) to treat vendor defaults deliberately rather than
   silently passing an unconfigured device.

4. Nothing here is vendor-specific. Cisco/Juniper/Fortinet/Palo Alto/SONiC/
   AWS all normalize INTO this same tree. Vendor-specific knowledge lives in
   Cell 1's parser table and Cell 2's knowledge base / few-shot store, never
   in this schema.

Run this file directly to print the JSON Schema and a populated example.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Generic, List, Optional, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator, ConfigDict

T = TypeVar("T")

SCHEMA_VERSION = "1.0.0"

# Below this calibrated-confidence threshold, a finding derived from this
# field MUST be routed to the Interactive Training Interface for human
# confirmation before it can contribute to a Pass/Fail compliance result.
HUMAN_REVIEW_CONFIDENCE_THRESHOLD = 0.75


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class VendorFamily(str, Enum):
    CISCO_IOS = "cisco_ios"
    CISCO_NXOS = "cisco_nxos"
    CISCO_FIREPOWER = "cisco_firepower"
    JUNIPER_JUNOS = "juniper_junos"
    PALO_ALTO_PANOS = "palo_alto_panos"
    FORTINET_FORTIOS = "fortinet_fortios"
    ARISTA_EOS = "arista_eos"
    SONIC = "sonic"
    AWS_SECURITY_GROUP = "aws_security_group"
    AZURE_NSG = "azure_nsg"
    GCP_FIREWALL = "gcp_firewall"
    HUAWEI_VRP = "huawei_vrp"
    MIKROTIK_ROUTEROS = "mikrotik_routeros"
    ARUBA_AOSCX = "aruba_aoscx"
    VYOS = "vyos"
    UNKNOWN = "unknown"  # triggers the training loop


class DeviceCategory(str, Enum):
    FIREWALL = "firewall"
    ROUTER = "router"
    SWITCH = "switch"
    SASE_CLOUD_GATEWAY = "sase_cloud_gateway"
    LOAD_BALANCER = "load_balancer"
    WHITE_BOX = "white_box"
    OTHER = "other"


class InterpretationMethod(str, Enum):
    DETERMINISTIC_PARSER = "deterministic_parser"   # Layer 1, known syntax
    AI_SEMANTIC_MAPPING = "ai_semantic_mapping"      # Layer 2, unseen syntax
    HUMAN_ANNOTATED = "human_annotated"              # training-loop correction
    DEFAULT_ASSUMED = "default_assumed"              # field absent from config
    KNOWLEDGE_BASE_LOOKUP = "knowledge_base_lookup"  # matched a stored
                                                      # few-shot example from a
                                                      # prior training session


class ServiceState(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceFramework(str, Enum):
    CIS = "cis"
    NIST_800_53 = "nist_800_53"
    DISA_STIG = "disa_stig"
    ISO_27001 = "iso_27001"


class FindingStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"
    NEEDS_HUMAN_REVIEW = "needs_human_review"  # confidence below threshold


# ---------------------------------------------------------------------------
# Provenance / Evidence — the mechanism that lets you answer "why?" on stage
# ---------------------------------------------------------------------------

class ProvenanceSource(BaseModel):
    """Exactly where this value came from in the original config file."""

    file: str
    line: Optional[int] = Field(
        default=None, description="1-indexed line number in the source file"
    )
    raw: str = Field(description="The literal, unmodified CLI/config text")


class Interpretation(BaseModel):
    """
    HOW a value was derived, and how much to trust it.

    `confidence` is NEVER an LLM self-report. It must be computed
    deterministically upstream from one or more of:
      - embedding/RAG cosine similarity between the raw line and the nearest
        matched knowledge-base example (primary signal)
      - deterministic-parser certainty (=1.0, grammar matched exactly)
      - schema validation success (type/enum matched expected shape)
      - vendor/OS fingerprint match confidence (do we even trust that we
        identified the vendor correctly?)

    See `compute_calibrated_confidence()` at the bottom of this file for the
    reference formula Cell 2 should implement.
    """

    method: InterpretationMethod
    confidence: float = Field(ge=0.0, le=1.0)
    knowledge_base_match: Optional[str] = Field(
        default=None,
        description="Identifier of the matched KB/few-shot example, e.g. "
        "'juniper_junos.ssh.protocol-version'",
    )
    requires_human_validation: bool = Field(default=False)

    @model_validator(mode="after")
    def _flag_low_confidence(self) -> "Interpretation":
        if self.confidence < HUMAN_REVIEW_CONFIDENCE_THRESHOLD:
            self.requires_human_validation = True
        return self


class EvidenceField(BaseModel, Generic[T]):
    """
    Generic wrapper around every security-relevant leaf value in the schema.

    explicitly_configured=False + method=DEFAULT_ASSUMED means: this field
    was NOT found in the config, and `value` reflects the vendor's documented
    default for this device/OS/firmware. The compliance engine must be able
    to fail a device on an assumed-insecure default, not just on explicit
    misconfiguration.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    value: Optional[T] = None
    explicitly_configured: bool = True
    source: Optional[ProvenanceSource] = None
    interpretation: Interpretation

    @classmethod
    def unknown(cls) -> "EvidenceField[T]":
        """Placeholder for a field that could not be determined at all."""
        return cls(
            value=None,
            explicitly_configured=False,
            source=None,
            interpretation=Interpretation(
                method=InterpretationMethod.DEFAULT_ASSUMED,
                confidence=0.0,
                requires_human_validation=True,
            ),
        )


# ---------------------------------------------------------------------------
# Device identity
# ---------------------------------------------------------------------------

class DeviceIdentity(BaseModel):
    device_id: str = Field(default_factory=lambda: str(uuid4()))
    hostname: Optional[str] = None
    serial_number: Optional[str] = None
    vendor: VendorFamily
    vendor_raw_string: Optional[str] = Field(
        default=None,
        description="Raw fingerprint text used to identify the vendor, kept "
        "for audit trail even when vendor enum resolves to UNKNOWN",
    )
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    category: DeviceCategory = DeviceCategory.OTHER
    config_file_name: str
    config_ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ---------------------------------------------------------------------------
# Management plane
# ---------------------------------------------------------------------------

class SSHConfig(BaseModel):
    enabled: EvidenceField[ServiceState]
    protocol_version: EvidenceField[int]
    ciphers: EvidenceField[List[str]] = Field(default_factory=EvidenceField.unknown)
    macs: EvidenceField[List[str]] = Field(default_factory=EvidenceField.unknown)
    key_exchange_algorithms: EvidenceField[List[str]] = Field(
        default_factory=EvidenceField.unknown
    )
    idle_timeout_seconds: EvidenceField[int] = Field(
        default_factory=EvidenceField.unknown
    )


class TelnetConfig(BaseModel):
    enabled: EvidenceField[ServiceState]


class HTTPConfig(BaseModel):
    enabled: EvidenceField[ServiceState]


class HTTPSConfig(BaseModel):
    enabled: EvidenceField[ServiceState]
    tls_min_version: EvidenceField[str] = Field(default_factory=EvidenceField.unknown)


class SNMPConfig(BaseModel):
    enabled: EvidenceField[ServiceState]
    version: EvidenceField[str] = Field(default_factory=EvidenceField.unknown)
    community_strings_default: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown,
        description="True if a default/well-known community string "
        "(e.g. 'public', 'private') is in use",
    )


class ManagementPlane(BaseModel):
    ssh: SSHConfig
    telnet: TelnetConfig
    http: HTTPConfig
    https: HTTPSConfig
    snmp: SNMPConfig


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class PasswordPolicy(BaseModel):
    encryption_enabled: EvidenceField[bool]
    min_length: EvidenceField[int] = Field(default_factory=EvidenceField.unknown)
    complexity_required: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )
    max_age_days: EvidenceField[int] = Field(default_factory=EvidenceField.unknown)


class MFAConfig(BaseModel):
    enabled: EvidenceField[bool] = Field(default_factory=EvidenceField.unknown)
    method: EvidenceField[str] = Field(default_factory=EvidenceField.unknown)


class AccountLockout(BaseModel):
    enabled: EvidenceField[bool] = Field(default_factory=EvidenceField.unknown)
    max_attempts: EvidenceField[int] = Field(default_factory=EvidenceField.unknown)
    lockout_duration_seconds: EvidenceField[int] = Field(
        default_factory=EvidenceField.unknown
    )


class AuthenticationConfig(BaseModel):
    method: EvidenceField[str] = Field(
        default_factory=EvidenceField.unknown,
        description="e.g. local, radius, tacacs+, ldap",
    )
    password_policy: PasswordPolicy
    mfa: MFAConfig
    account_lockout: AccountLockout
    privilege_levels_defined: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )


# ---------------------------------------------------------------------------
# Cryptography
# ---------------------------------------------------------------------------

class TLSConfig(BaseModel):
    min_version: EvidenceField[str] = Field(default_factory=EvidenceField.unknown)
    weak_ciphers_disabled: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )


class CryptographyConfig(BaseModel):
    tls: TLSConfig
    ssh_ciphers_hardened: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )
    key_exchange_hardened: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )
    certificate_validation_enabled: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

class ACLRule(BaseModel):
    rule_id: Optional[str] = None
    action: EvidenceField[str]  # permit / deny
    source: EvidenceField[str] = Field(default_factory=EvidenceField.unknown)
    destination: EvidenceField[str] = Field(default_factory=EvidenceField.unknown)
    service: EvidenceField[str] = Field(default_factory=EvidenceField.unknown)
    is_any_any_permit: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown,
        description="Flags overly permissive 'any-any-permit' rules for the "
        "risk/attack-path engine (Cell 4)",
    )


class ManagementAccessConfig(BaseModel):
    restricted_to_specific_hosts: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )
    allowed_management_sources: EvidenceField[List[str]] = Field(
        default_factory=EvidenceField.unknown
    )


class AccessControlConfig(BaseModel):
    acl_rules: List[ACLRule] = Field(default_factory=list)
    management_access: ManagementAccessConfig


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

class SyslogConfig(BaseModel):
    enabled: EvidenceField[bool]
    server_addresses: EvidenceField[List[str]] = Field(
        default_factory=EvidenceField.unknown
    )
    buffer_size: EvidenceField[int] = Field(default_factory=EvidenceField.unknown)


class AuditConfig(BaseModel):
    command_auditing_enabled: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )


class AdminEventLogging(BaseModel):
    login_events_logged: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )
    config_change_events_logged: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )


class LoggingConfig(BaseModel):
    syslog: SyslogConfig
    audit: AuditConfig
    administrative_events: AdminEventLogging


# ---------------------------------------------------------------------------
# Network services
# ---------------------------------------------------------------------------

class InsecureServicesConfig(BaseModel):
    """Catch-all for legacy/insecure services beyond telnet/http (finger,
    small-servers, cdp/lldp broadcast where inappropriate, etc.)."""

    finger_enabled: EvidenceField[bool] = Field(default_factory=EvidenceField.unknown)
    small_servers_enabled: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )
    proxy_arp_enabled: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )


class NetworkServicesConfig(BaseModel):
    dns_servers: EvidenceField[List[str]] = Field(default_factory=EvidenceField.unknown)
    ntp_configured: EvidenceField[bool] = Field(default_factory=EvidenceField.unknown)
    ntp_authenticated: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )
    dhcp_snooping_enabled: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )
    insecure_services: InsecureServicesConfig


# ---------------------------------------------------------------------------
# Security controls
# ---------------------------------------------------------------------------

class SecurityControlsConfig(BaseModel):
    anti_spoofing_enabled: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )
    segmentation_vlans_defined: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )
    ingress_filtering_enabled: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )
    egress_filtering_enabled: EvidenceField[bool] = Field(
        default_factory=EvidenceField.unknown
    )


# ---------------------------------------------------------------------------
# Top-level Security Baseline
# ---------------------------------------------------------------------------

class SecurityBaselineMetadata(BaseModel):
    schema_version: str = SCHEMA_VERSION
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    overall_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Aggregate confidence across all EvidenceFields in this "
        "baseline — e.g. the mean of leaf-field confidences. Surfaced on the "
        "dashboard as 'AI Interpretation Confidence'.",
    )
    fields_requiring_human_review: int = Field(
        default=0,
        description="Count of EvidenceFields with requires_human_validation=True",
    )


class SecurityBaseline(BaseModel):
    """The vendor-neutral Security Baseline Model. This is what Cell 1/2
    produce and what Cell 3/4/5 consume. Nothing downstream ever touches
    raw config text again after this object exists."""

    device: DeviceIdentity
    management: ManagementPlane
    authentication: AuthenticationConfig
    cryptography: CryptographyConfig
    access_control: AccessControlConfig
    logging: LoggingConfig
    network_services: NetworkServicesConfig
    security_controls: SecurityControlsConfig
    metadata: SecurityBaselineMetadata


# ---------------------------------------------------------------------------
# Interfaces between cells
# ---------------------------------------------------------------------------

class ComplianceFinding(BaseModel):
    """Cell 3's output. One per rule evaluated per device."""

    finding_id: str = Field(default_factory=lambda: str(uuid4()))
    device_id: str
    framework: ComplianceFramework
    rule_id: str
    baseline_field_path: str = Field(
        description="Dotted path into SecurityBaseline, e.g. "
        "'management.telnet.enabled'"
    )
    status: FindingStatus
    severity: Severity
    evidence: EvidenceField
    remediation_id: Optional[str] = Field(
        default=None, description="Looked up by Cell 5 from the remediation KB"
    )


class TrainingCorrection(BaseModel):
    """Produced by the Interactive Training Interface (Cell 6 UI, Cell 2
    backend) when an administrator maps a previously unrecognized command."""

    correction_id: str = Field(default_factory=lambda: str(uuid4()))
    vendor: VendorFamily
    raw_command_pattern: str
    mapped_baseline_field_path: str
    mapped_value_hint: Optional[str] = None
    security_category: str = Field(
        description="One of: Authentication, Network Services, Cryptography, "
        "Access Control, Logging, Management, Security Controls"
    )
    submitted_by: str
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Reference confidence formula (Cell 2 implements the real version of this)
# ---------------------------------------------------------------------------

def compute_calibrated_confidence(
    embedding_similarity: float,
    parser_certainty: float,
    schema_validation_passed: bool,
    vendor_fingerprint_confidence: float,
) -> float:
    """
    Reference formula — NOT an LLM self-report.

    embedding_similarity:        cosine similarity [0,1] to nearest KB example
    parser_certainty:            1.0 if deterministic grammar matched exactly,
                                  else 0.0 (this function only meaningfully
                                  applies to the AI path)
    schema_validation_passed:    did the extracted value satisfy the expected
                                  type/enum for this field?
    vendor_fingerprint_confidence: confidence that we identified vendor/OS
                                  correctly in the first place
    """
    if parser_certainty >= 1.0:
        return 1.0  # deterministic parser match, known grammar

    schema_term = 1.0 if schema_validation_passed else 0.3
    score = (
        0.5 * embedding_similarity
        + 0.2 * schema_term
        + 0.3 * vendor_fingerprint_confidence
    )
    return round(min(max(score, 0.0), 1.0), 4)


# ---------------------------------------------------------------------------
# Self-test / example — run: python security_baseline_schema.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    example = SecurityBaseline(
        device=DeviceIdentity(
            hostname="edge-fw-01",
            serial_number="FGT60F1234567890",
            vendor=VendorFamily.JUNIPER_JUNOS,
            model="SRX340",
            firmware_version="21.4R3",
            category=DeviceCategory.FIREWALL,
            config_file_name="device01.conf",
        ),
        management=ManagementPlane(
            ssh=SSHConfig(
                enabled=EvidenceField(
                    value=ServiceState.ENABLED,
                    source=ProvenanceSource(
                        file="device01.conf",
                        line=47,
                        raw="set system services ssh protocol-version v2",
                    ),
                    interpretation=Interpretation(
                        method=InterpretationMethod.AI_SEMANTIC_MAPPING,
                        confidence=0.94,
                        knowledge_base_match="juniper_junos.ssh.protocol-version",
                    ),
                ),
                protocol_version=EvidenceField(
                    value=2,
                    source=ProvenanceSource(
                        file="device01.conf",
                        line=47,
                        raw="set system services ssh protocol-version v2",
                    ),
                    interpretation=Interpretation(
                        method=InterpretationMethod.AI_SEMANTIC_MAPPING,
                        confidence=0.94,
                        knowledge_base_match="juniper_junos.ssh.protocol-version",
                    ),
                ),
            ),
            telnet=TelnetConfig(
                enabled=EvidenceField(
                    value=ServiceState.ENABLED,
                    explicitly_configured=False,
                    interpretation=Interpretation(
                        method=InterpretationMethod.DEFAULT_ASSUMED,
                        confidence=0.6,
                    ),
                )
            ),
            http=HTTPConfig(
                enabled=EvidenceField(
                    value=ServiceState.DISABLED,
                    source=ProvenanceSource(
                        file="device01.conf", line=52, raw="no ip http server"
                    ),
                    interpretation=Interpretation(
                        method=InterpretationMethod.DETERMINISTIC_PARSER,
                        confidence=1.0,
                    ),
                )
            ),
            https=HTTPSConfig(
                enabled=EvidenceField(
                    value=ServiceState.UNKNOWN,
                    interpretation=Interpretation(
                        method=InterpretationMethod.DEFAULT_ASSUMED, confidence=0.2
                    ),
                )
            ),
            snmp=SNMPConfig(
                enabled=EvidenceField(
                    value=ServiceState.UNKNOWN,
                    interpretation=Interpretation(
                        method=InterpretationMethod.DEFAULT_ASSUMED, confidence=0.2
                    ),
                )
            ),
        ),
        authentication=AuthenticationConfig(
            password_policy=PasswordPolicy(
                encryption_enabled=EvidenceField(
                    value=True,
                    source=ProvenanceSource(
                        file="device01.conf",
                        line=12,
                        raw="service password-encryption",
                    ),
                    interpretation=Interpretation(
                        method=InterpretationMethod.DETERMINISTIC_PARSER,
                        confidence=1.0,
                    ),
                )
            ),
            mfa=MFAConfig(),
            account_lockout=AccountLockout(),
        ),
        cryptography=CryptographyConfig(tls=TLSConfig()),
        access_control=AccessControlConfig(
            management_access=ManagementAccessConfig()
        ),
        logging=LoggingConfig(
            syslog=SyslogConfig(
                enabled=EvidenceField(
                    value=True,
                    source=ProvenanceSource(
                        file="device01.conf",
                        line=61,
                        raw="logging buffered 64000",
                    ),
                    interpretation=Interpretation(
                        method=InterpretationMethod.DETERMINISTIC_PARSER,
                        confidence=1.0,
                    ),
                ),
                buffer_size=EvidenceField(
                    value=64000,
                    source=ProvenanceSource(
                        file="device01.conf",
                        line=61,
                        raw="logging buffered 64000",
                    ),
                    interpretation=Interpretation(
                        method=InterpretationMethod.DETERMINISTIC_PARSER,
                        confidence=1.0,
                    ),
                ),
            ),
            audit=AuditConfig(),
            administrative_events=AdminEventLogging(),
        ),
        network_services=NetworkServicesConfig(
            insecure_services=InsecureServicesConfig()
        ),
        security_controls=SecurityControlsConfig(),
        metadata=SecurityBaselineMetadata(overall_confidence=0.82),
    )

    print("=== Populated example (excerpt) ===")
    print(
        json.dumps(
            json.loads(example.model_dump_json())["management"]["ssh"], indent=2
        )
    )

    print("\n=== Full JSON Schema written to security_baseline.schema.json ===")
    with open("security_baseline.schema.json", "w") as f:
        json.dump(SecurityBaseline.model_json_schema(), f, indent=2)

    print("\n=== Reference confidence example ===")
    print(
        "Confidence for an AI-mapped field with 0.9 embedding similarity, "
        "schema valid, high vendor-fingerprint confidence:",
        compute_calibrated_confidence(
            embedding_similarity=0.91,
            parser_certainty=0.0,
            schema_validation_passed=True,
            vendor_fingerprint_confidence=0.95,
        ),
    )
