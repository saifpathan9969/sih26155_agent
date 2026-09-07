"""Tool 2 — Vendor Fingerprinting. v1: rule-based signature matching.

Per the ML training plan: this ships day one with zero training data. v2
(a small trained text classifier) only becomes worthwhile once 200-500
labeled config files per vendor exist — not needed for the MVP.
"""

import sys
import sys
from pathlib import Path as _Path
_PROJECT_ROOT = _Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "agent"))
from security_baseline_schema import VendorFamily  # noqa: E402

SIGNATURES = [
    (VendorFamily.CISCO_IOS, ("building configuration", "ip ssh version", "line vty")),
    (VendorFamily.JUNIPER_JUNOS, ("set system", "set security", "set firewall filter")),
    (VendorFamily.FORTINET_FORTIOS, ("config system global", "config firewall", "end")),
    (VendorFamily.PALO_ALTO_PANOS, ("set deviceconfig", "set rulebase", "pan-os")),
    (VendorFamily.ARISTA_EOS, ("! device: arista", "management api", "arista eos", "management api http-commands")),
    (VendorFamily.ARUBA_AOSCX, ("aoscx", "aruba aoscx", "ssh server vrf")),
    (VendorFamily.HUAWEI_VRP, ("sysname", "stelnet server", "huawei vrp", "local-user")),
    (VendorFamily.MIKROTIK_ROUTEROS, ("/system identity", "/ip service", "/ip firewall", "routeros")),
    (VendorFamily.VYOS, ("set service ssh", "vyos", "set system host-name")),
]


def fingerprint_vendor(raw_text: str):
    """Returns (VendorFamily, confidence). UNKNOWN with low confidence when
    no signature matches — this is the honest, undramatic failure mode that
    triggers vendor onboarding rather than a wrong guess."""
    text_lower = raw_text.lower()
    best_vendor, best_score = VendorFamily.UNKNOWN, 0.0

    for vendor, markers in SIGNATURES:
        hits = sum(1 for m in markers if m in text_lower)
        score = hits / len(markers)
        if score > best_score:
            best_vendor, best_score = vendor, score

    if best_score == 0.0:
        return VendorFamily.UNKNOWN, 0.0
    # Rule-based match: confident once at least one strong marker hit.
    confidence = min(0.97, 0.55 + 0.42 * best_score)
    return best_vendor, round(confidence, 2)
