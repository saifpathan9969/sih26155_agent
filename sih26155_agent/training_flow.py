"""
Unknown-Vendor Interactive Training Flow — Reference Implementation
=======================================================================
SIH26155 — Cell 2 (AI) + Cell 6 (UI) interface, Cell 3 (compliance) consumer.

Implements the 5 stages from unknown_vendor_training_flow.md:
  1. Detection            -> UnknownCommandDetection
  2. Interpretation        -> retrieve_candidates() [TF-IDF cosine similarity]
  3. Human mapping          -> admin supplies category + baseline_field_path + value
  4. Validation             -> validate_mapping() [introspects the REAL schema types]
  5. Learn + Re-evaluate    -> apply_training_correction() + rule_engine.evaluate_baseline()

No LLM call is required for this reference implementation. Retrieval uses
local TF-IDF/cosine similarity (scikit-learn) rather than a hosted embedding
API, because a live demo cannot depend on reaching an external service from
the stage network. The one function that would be swapped for a production
embedding model is clearly marked below.

Run this file directly for the full before -> intervention -> after demo.
"""

from __future__ import annotations

import typing
from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, TypeAdapter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from security_baseline_schema import (
    EvidenceField,
    Interpretation,
    InterpretationMethod,
    SecurityBaseline,
    TrainingCorrection,
    VendorFamily,
)
from rule_engine import evaluate_baseline, resolve_evidence_field

SIMILARITY_CONFIDENCE_THRESHOLD = 0.55


# ---------------------------------------------------------------------------
# Data contracts (per spec)
# ---------------------------------------------------------------------------

class UnknownCommandDetection(BaseModel):
    raw: str
    vendor_fingerprint: VendorFamily
    vendor_fingerprint_confidence: float
    file: str
    line: Optional[int] = None


class KnowledgeBaseEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid4()))
    vendor: VendorFamily
    raw_pattern: str
    security_category: str
    baseline_field_path: str
    value_type_hint: str
    example_count: int = 1
    added_by: str
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CandidateMapping(BaseModel):
    matched_entry: Optional[KnowledgeBaseEntry]
    similarity: float
    is_confident: bool


class ValidationResult(BaseModel):
    valid: bool
    expected_type: str
    received_value: Any
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# In-memory knowledge base (swap for a real vector DB in production; the
# interface below — add() / retrieve() — is the seam to do that at)
# ---------------------------------------------------------------------------

class VendorKnowledgeBase:
    def __init__(self) -> None:
        self._entries: List[KnowledgeBaseEntry] = []

    def add(self, entry: KnowledgeBaseEntry) -> None:
        self._entries.append(entry)

    def entries_for_vendor(self, vendor: VendorFamily) -> List[KnowledgeBaseEntry]:
        return [e for e in self._entries if e.vendor == vendor]

    def retrieve(self, raw_command: str, vendor: VendorFamily) -> CandidateMapping:
        """
        *** SWAP POINT for a production embedding model ***
        Reference implementation uses local TF-IDF + cosine similarity so the
        demo has zero external dependency. Scoped first to same-vendor
        entries; falls back to all entries if the vendor has none yet.
        """
        pool = self.entries_for_vendor(vendor) or self._entries
        if not pool:
            return CandidateMapping(matched_entry=None, similarity=0.0, is_confident=False)

        corpus = [e.raw_pattern for e in pool] + [raw_command]
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        matrix = vectorizer.fit_transform(corpus)
        sims = cosine_similarity(matrix[-1], matrix[:-1]).flatten()

        best_idx = int(sims.argmax())
        best_score = float(sims[best_idx])
        best_entry = pool[best_idx]

        return CandidateMapping(
            matched_entry=best_entry,
            similarity=round(best_score, 4),
            is_confident=best_score >= SIMILARITY_CONFIDENCE_THRESHOLD,
        )


# ---------------------------------------------------------------------------
# Stage 4 — schema-introspected validation (no hand-maintained type table)
# ---------------------------------------------------------------------------

def _generic_args(annotation: Any) -> tuple:
    """Pydantic v2 concretizes `EvidenceField[bool]` into an actual subclass
    of EvidenceField rather than a typing generic alias, so plain
    typing.get_args() returns nothing for it. The real type argument lives
    on __pydantic_generic_metadata__. Fall back to typing.get_args() for
    ordinary generics like List[ACLRule], which ARE plain typing aliases."""
    metadata = getattr(annotation, "__pydantic_generic_metadata__", None)
    if metadata and metadata.get("args"):
        return metadata["args"]
    return typing.get_args(annotation)


def resolve_expected_type(baseline_field_path: str) -> type:
    """Walks the REAL SecurityBaseline Pydantic model tree to find the
    expected leaf type at a dotted path, so validation can never drift out
    of sync with the schema artifact."""
    cls: Any = SecurityBaseline
    for part in baseline_field_path.split("."):
        is_list = part.endswith("[]")
        attr = part[:-2] if is_list else part
        annotation = cls.model_fields[attr].annotation
        args = _generic_args(annotation)
        cls = args[0] if args else annotation
    return cls


def validate_mapping(baseline_field_path: str, value: Any) -> ValidationResult:
    try:
        expected_type = resolve_expected_type(baseline_field_path)
    except (KeyError, AttributeError) as exc:
        return ValidationResult(
            valid=False, expected_type="unknown", received_value=value,
            error=f"baseline_field_path does not resolve against the schema: {exc}",
        )

    try:
        TypeAdapter(expected_type).validate_python(value)
    except Exception as exc:  # pydantic ValidationError, deliberately broad for demo clarity
        return ValidationResult(
            valid=False,
            expected_type=expected_type.__name__,
            received_value=value,
            error=f"expected {expected_type.__name__}, received {type(value).__name__}",
        )

    return ValidationResult(valid=True, expected_type=expected_type.__name__, received_value=value)


# ---------------------------------------------------------------------------
# Stage 5 — learn + apply to the live baseline
# ---------------------------------------------------------------------------

def apply_training_correction(
    baseline: SecurityBaseline,
    kb: VendorKnowledgeBase,
    detection: UnknownCommandDetection,
    security_category: str,
    baseline_field_path: str,
    value: Any,
    submitted_by: str,
) -> TrainingCorrection:
    """Persists the correction, updates the KB, and mutates the in-memory
    EvidenceField so the next evaluate_baseline() call reflects it."""

    validation = validate_mapping(baseline_field_path, value)
    if not validation.valid:
        raise ValueError(f"Mapping rejected — {validation.error}")

    correction = TrainingCorrection(
        vendor=detection.vendor_fingerprint,
        raw_command_pattern=detection.raw,
        mapped_baseline_field_path=baseline_field_path,
        mapped_value_hint=str(value),
        security_category=security_category,
        submitted_by=submitted_by,
    )

    kb.add(
        KnowledgeBaseEntry(
            vendor=detection.vendor_fingerprint,
            raw_pattern=detection.raw,
            security_category=security_category,
            baseline_field_path=baseline_field_path,
            value_type_hint=validation.expected_type,
            added_by=submitted_by,
        )
    )

    # Mutate the live EvidenceField in place — human-confirmed => full trust.
    target = _resolve_parent_and_attr(baseline, baseline_field_path)
    parent_obj, attr_name = target
    setattr(
        parent_obj,
        attr_name,
        EvidenceField(
            value=value,
            explicitly_configured=True,
            source=None,  # raw provenance already lives on the TrainingCorrection
            interpretation=Interpretation(
                method=InterpretationMethod.HUMAN_ANNOTATED,
                confidence=1.0,
                knowledge_base_match=None,
            ),
        ),
    )

    return correction


def _resolve_parent_and_attr(baseline: SecurityBaseline, dotted_path: str):
    """Returns (parent_object, final_attr_name) so the caller can setattr
    the updated EvidenceField onto the live baseline instance."""
    parts = dotted_path.split(".")
    obj: Any = baseline
    for part in parts[:-1]:
        obj = getattr(obj, part)
    return obj, parts[-1]


# ---------------------------------------------------------------------------
# Full demo — the "before -> intervention -> after" proof
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from security_baseline_schema import (
        AccessControlConfig, ACLRule, AdminEventLogging, AuditConfig,
        AuthenticationConfig, CryptographyConfig, DeviceCategory, DeviceIdentity,
        HTTPConfig, HTTPSConfig, InsecureServicesConfig, LoggingConfig,
        ManagementAccessConfig, ManagementPlane, MFAConfig, AccountLockout,
        NetworkServicesConfig, PasswordPolicy, ProvenanceSource,
        SecurityBaselineMetadata, SecurityControlsConfig, ServiceState,
        SNMPConfig, SSHConfig, SyslogConfig, TelnetConfig, TLSConfig,
    )

    def ef(value, method=InterpretationMethod.DETERMINISTIC_PARSER, confidence=1.0,
           explicit=True, raw=None, line=None):
        return EvidenceField(
            value=value, explicitly_configured=explicit,
            source=ProvenanceSource(file="device03.conf", line=line, raw=raw) if raw else None,
            interpretation=Interpretation(method=method, confidence=confidence),
        )

    # Same baseline shape as rule_engine.py's self-test, but this time on a
    # Juniper device with account_lockout genuinely unconfigured/unknown.
    baseline = SecurityBaseline(
        device=DeviceIdentity(
            hostname="edge-srx-03", vendor=VendorFamily.JUNIPER_JUNOS, model="SRX340",
            firmware_version="21.4R3", category=DeviceCategory.FIREWALL,
            config_file_name="device03.conf",
        ),
        management=ManagementPlane(
            ssh=SSHConfig(enabled=ef(ServiceState.ENABLED, raw="set system services ssh protocol-version v2", line=47),
                          protocol_version=ef(2, raw="set system services ssh protocol-version v2", line=47),
                          idle_timeout_seconds=ef(600, raw="set system login idle-timeout 10", line=48)),
            telnet=TelnetConfig(enabled=ef(ServiceState.DISABLED, raw="delete system services telnet", line=50)),
            http=HTTPConfig(enabled=ef(ServiceState.DISABLED, raw="delete system services web-management http", line=51)),
            https=HTTPSConfig(enabled=ef(ServiceState.ENABLED, raw="set system services web-management https", line=52)),
            snmp=SNMPConfig(enabled=ef(ServiceState.ENABLED, raw="set snmp community unique-str authorization read-only", line=60),
                             version=ef("3", raw="set snmp v3", line=61),
                             community_strings_default=ef(False, raw="set snmp community unique-str", line=60)),
        ),
        authentication=AuthenticationConfig(
            password_policy=PasswordPolicy(
                encryption_enabled=ef(True, raw="set system login password format sha256", line=10),
                min_length=ef(14, raw="set system login password minimum-length 14", line=11),
            ),
            mfa=MFAConfig(),
            # <-- THIS is the field our unknown command will resolve.
            account_lockout=AccountLockout(enabled=ef(False, explicit=False, confidence=0.5)),
            privilege_levels_defined=ef(True, raw="set system login class operator", line=20),
        ),
        cryptography=CryptographyConfig(
            tls=TLSConfig(min_version=ef("1.2", raw="set system services web-management https tls-min-version tls1.2", line=53)),
            ssh_ciphers_hardened=ef(True, raw="set system services ssh ciphers aes256-ctr", line=54),
            certificate_validation_enabled=ef(True, raw="set security pki ca-profile CA revocation-check crl", line=55),
        ),
        access_control=AccessControlConfig(
            acl_rules=[ACLRule(rule_id="fw-1", action=ef("permit"), is_any_any_permit=ef(False, raw="set firewall filter MGMT term allow from source-address 10.0.0.0/24", line=70))],
            management_access=ManagementAccessConfig(restricted_to_specific_hosts=ef(True, raw="set firewall filter MGMT-ACCESS term allow-mgmt from source-address 10.0.0.0/24", line=70)),
        ),
        logging=LoggingConfig(
            syslog=SyslogConfig(enabled=ef(True, raw="set system syslog host 10.0.0.5 any notice", line=80),
                                 buffer_size=ef(20000, raw="set system syslog file messages archive size 1m", line=81)),
            audit=AuditConfig(),
            administrative_events=AdminEventLogging(config_change_events_logged=ef(True, raw="set system syslog file change-log change-log any", line=82)),
        ),
        network_services=NetworkServicesConfig(insecure_services=InsecureServicesConfig()),
        security_controls=SecurityControlsConfig(egress_filtering_enabled=ef(True, raw="set firewall filter EGRESS-FILTER term allow-web from destination-port 443", line=90)),
        metadata=SecurityBaselineMetadata(overall_confidence=0.85),
    )

    print("=" * 70)
    print("BEFORE — unknown command not yet mapped")
    print("=" * 70)
    before = evaluate_baseline(baseline)
    auth03_before = next(f for f in before if f.rule_id == "CIS-AUTH-03")
    print(f"CIS-AUTH-03 (account lockout enabled): {auth03_before.status.value.upper()}")

    # --- Stage 1: Detection --------------------------------------------
    detection = UnknownCommandDetection(
        raw="set system login retry-options tries-before-disconnect 5 lockout-period 15",
        vendor_fingerprint=VendorFamily.JUNIPER_JUNOS,
        vendor_fingerprint_confidence=0.97,
        file="device03.conf",
        line=88,
    )
    print("\n" + "=" * 70)
    print("STAGE 1 — Detection")
    print("=" * 70)
    print(f"⚠ Unknown configuration syntax detected\nRaw: {detection.raw}")
    print(f"File: {detection.file}  Line: {detection.line}  Vendor: {detection.vendor_fingerprint.value}")

    # --- Stage 2: Interpretation (empty KB -> low confidence, as expected)
    kb = VendorKnowledgeBase()
    candidate = kb.retrieve(detection.raw, detection.vendor_fingerprint)
    print("\n" + "=" * 70)
    print("STAGE 2 — Interpretation")
    print("=" * 70)
    if candidate.is_confident:
        print(f"Possible meaning from KB match (similarity {candidate.similarity})")
    else:
        print(f"No confident match found (similarity {candidate.similarity}). Human review required.")

    # --- Stage 3: Human mapping -----------------------------------------
    print("\n" + "=" * 70)
    print("STAGE 3 — Human mapping (administrator input)")
    print("=" * 70)
    security_category = "Authentication"
    baseline_field_path = "authentication.account_lockout.enabled"
    extracted_value = True
    print(f"Category: {security_category}")
    print(f"Baseline field: {baseline_field_path}")
    print(f"Extracted value: {extracted_value}")

    # --- Stage 4: Validation (show one rejection, then the real accept) --
    print("\n" + "=" * 70)
    print("STAGE 4 — Validation")
    print("=" * 70)
    bad = validate_mapping(baseline_field_path, "yes-please")  # intentionally wrong type
    print(f"Attempt with wrong type -> valid={bad.valid} | {bad.error}")
    good = validate_mapping(baseline_field_path, extracted_value)
    print(f"Attempt with correct type -> valid={good.valid}")

    # --- Stage 5: Learn + re-evaluate -------------------------------------
    print("\n" + "=" * 70)
    print("STAGE 5 — Learn + Re-evaluate")
    print("=" * 70)
    apply_training_correction(
        baseline=baseline, kb=kb, detection=detection,
        security_category=security_category, baseline_field_path=baseline_field_path,
        value=extracted_value, submitted_by="admin_demo",
    )
    print("✓ Knowledge base updated")
    print("✓ Configuration re-normalized")

    after = evaluate_baseline(baseline)
    auth03_after = next(f for f in after if f.rule_id == "CIS-AUTH-03")
    print("✓ 20 compliance rules re-evaluated")

    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)
    print(f"CIS-AUTH-03 status: {auth03_before.status.value.upper()} -> {auth03_after.status.value.upper()}")

    # Bonus: prove the KB now retrieves this pattern with high confidence
    # for a near-identical command on a second device.
    similar_command = "set system login retry-options tries-before-disconnect 5"
    repeat_candidate = kb.retrieve(similar_command, VendorFamily.JUNIPER_JUNOS)
    print(f"\nRetrieval test on a near-identical command from a 2nd device:")
    print(f"  '{similar_command}'")
    print(f"  similarity={repeat_candidate.similarity}  confident={repeat_candidate.is_confident}")
