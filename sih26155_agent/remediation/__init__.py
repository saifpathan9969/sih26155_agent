"""
GAACA v1 Verified Remediation Module
=====================================
Trusted configuration repair with sandbox validation and promotion gates.

PROPOSE → SANDBOX → VALIDATE → AUDIT → VERIFY → PROMOTE → REPORT

Original configurations remain immutable. Fixes are tested in an isolated
sandbox, validated against syntax/security/regression checks, and only promoted
to output/ after passing all gates.
"""

from remediation.sandbox import SandboxManager, SandboxSession
from remediation.proposer import RemediationProposer
from remediation.validator import RemediationValidator, ValidationResult
from remediation.promotion import PromotionGate, PromotionDecision

__all__ = [
    "SandboxManager",
    "SandboxSession",
    "RemediationProposer",
    "RemediationValidator",
    "ValidationResult",
    "PromotionGate",
    "PromotionDecision",
]
