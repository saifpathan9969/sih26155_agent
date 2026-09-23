"""
Targeted detection regression suite.
====================================

Pins the specific failures that were fixed, so they cannot silently return.
Each test documents the bug it guards rather than merely asserting a value.

Run:
    python regression/test_detection_regression.py
    pytest regression/test_detection_regression.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "sih26155_agent"))
sys.path.insert(0, str(_ROOT / "sih26155_agent" / "agent"))

from device_profile import DeviceClass, build_device_profile  # noqa: E402
from tools.fingerprint import (  # noqa: E402
    ClassificationStatus,
    fingerprint_vendor,
    fingerprint_vendor_ex,
)

# ---------------------------------------------------------------------------
# mikrotik_capsman — a CAPsMAN-only config has no /system or /ip stanzas, so it
# scored zero for MikroTik and was claimed by generic SMB wireless brands.
# ---------------------------------------------------------------------------

CAPSMAN = """/caps-man security add name=sec-prof authentication-types=wpa2-eap,wpa3-eap encryption=aes-ccm
/caps-man datapath add name=dp-secure client-to-client-forwarding=no local-forwarding=no
/caps-man configuration add name=cfg-secure ssid=MikroTik-Enterprise security=sec-prof datapath=dp-secure
/caps-man manager set enabled=yes
"""


def test_capsman_identified_as_mikrotik():
    vendor, _ = fingerprint_vendor(CAPSMAN)
    assert vendor.value == "mikrotik_routeros", f"got {vendor.value}"


def test_capsman_classified_as_access_point():
    vendor, _ = fingerprint_vendor(CAPSMAN)
    profile = build_device_profile(CAPSMAN, "WF-MIKROTIK_CAPSMAN.rsc", vendor.value)
    assert profile["device_class"] == DeviceClass.WIRELESS_AP, profile["device_class"]


# ---------------------------------------------------------------------------
# juniper_srx_panos — SRX and PAN-OS both express "from trust to untrust", so
# zone vocabulary alone cannot separate them. Junos constructs must now argue
# actively against the PAN-OS hypothesis.
# ---------------------------------------------------------------------------

SRX = """set system host-name HQ-SRX
set system services ssh protocol-version v2
set system services ssh ciphers aes256-ctr
delete system services telnet
set security policies from-zone trust to-zone untrust policy permit-web match application any
set security policies from-zone trust to-zone untrust policy permit-web then permit
set security zones security-zone trust interfaces ge-0/0/1.0
"""

PANOS = """set deviceconfig system hostname PA-FW
set deviceconfig system service disable-telnet yes
set mgt-config users admin permissions role-based superuser yes
set zone TRUST network layer3 ethernet1/2
set rulebase security rules ALLOW-OUT from TRUST to UNTRUST action allow
set rulebase security rules ALLOW-OUT service application-default
set network virtual-router default routing-table ip static-route DEFAULT
"""


def test_srx_not_misidentified_as_panos():
    vendor, _ = fingerprint_vendor(SRX)
    assert vendor.value != "palo_alto_panos", "SRX regressed to PAN-OS"
    assert vendor.value == "juniper_junos", f"got {vendor.value}"


def test_panos_still_identified():
    """The contradiction penalty must not break genuine PAN-OS detection."""
    vendor, _ = fingerprint_vendor(PANOS)
    assert vendor.value == "palo_alto_panos", f"got {vendor.value}"


# ---------------------------------------------------------------------------
# sophos_ssid — "Sophos-Open" in an SSID string matched a bare vendor-name
# marker and misfiled a wireless access point as a Sophos firewall.
# ---------------------------------------------------------------------------

SOPHOS_AP = """{
    "device": "WAN-APX320-DXB-09",
    "wireless_networks": [
        {"ssid": "Sophos-Open", "encryption": "None", "client_isolation": false}
    ],
    "radio": {"band": "5GHz", "channel_width": 80, "tx_power": "high"}
}
"""


def test_sophos_ssid_does_not_make_a_firewall():
    vendor, _ = fingerprint_vendor(SOPHOS_AP)
    profile = build_device_profile(SOPHOS_AP, "WF-SOPHOS_APX.json", vendor.value)
    assert profile["device_class"] != DeviceClass.FIREWALL, (
        "a vendor name inside an SSID string must not imply a firewall"
    )
    assert profile["device_class"] == DeviceClass.WIRELESS_AP, profile["device_class"]


# ---------------------------------------------------------------------------
# sparse_edge_cases — abstaining is the correct answer. These must NOT become
# confident classifications; that conversion is the regression the gate exists
# to catch.
# ---------------------------------------------------------------------------

SPARSE_CASES = [
    ("empty", ""),
    ("comment only", "# GAACA Dataset - EDGE CASE\n"),
    ("truncated xml", '<?xml version="1.0"?>\n<DeviceConfiguration/>\n'),
    ("bare json", '{\n    "name": "BR-DEVICE-01"\n}\n'),
    ("single stray token", "from trust to untrust\n"),
]


def test_sparse_configs_abstain_rather_than_guess():
    for label, cfg in SPARSE_CASES:
        result = fingerprint_vendor_ex(cfg)
        assert result["vendor"].value == "unknown", (
            f"{label!r}: named {result['vendor'].value} on insufficient evidence"
        )
        assert result["classification_status"] in (
            ClassificationStatus.UNKNOWN_EDGE_CASE,
            ClassificationStatus.LOW_EVIDENCE,
        ), f"{label!r}: status was {result['classification_status']}"


def test_abstention_is_not_flagged_as_human_required():
    """
    Classification uncertainty must stay separate from human escalation.
    An unidentifiable *device* does not itself demand operator review; only an
    unmapped *command* does, and that is decided during the audit.
    """
    profile = build_device_profile("# nothing here\n", "sparse.conf", "unknown")
    assert profile["human_required"] is False


# ---------------------------------------------------------------------------
# Layered model invariants — BGP must never imply "router".
# ---------------------------------------------------------------------------

L3_SWITCH = """hostname CORE-SW
spanning-tree mode rapid-pvst
vlan 10
interface GigabitEthernet1/0/1
 switchport mode access
 switchport access vlan 10
interface Vlan10
 ip address 10.1.1.1 255.255.255.0
router bgp 65001
 neighbor 10.0.0.1 remote-as 65000
router ospf 1
 network 10.1.1.0 0.0.0.255 area 0
"""


def test_l3_switch_is_a_switch_not_a_router():
    vendor, _ = fingerprint_vendor(L3_SWITCH)
    profile = build_device_profile(L3_SWITCH, "core-sw.conf", vendor.value)
    assert profile["device_class"] == DeviceClass.NETWORK_SWITCH, profile["device_class"]
    assert "BGP" in profile["capabilities"], "BGP must be recorded as a capability"
    assert profile["routing_capable"] is True
    assert profile["l2_capable"] is True
    assert profile["network_role"] in ("core", "distribution", "edge", "access"), (
        profile["network_role"]
    )


def test_short_markers_are_boundary_matched():
    """
    Three-letter product prefixes were matched as bare substrings, so "ews"
    (EnGenius) hit inside words like "reviews" and handed configs to the wrong
    vendor. Prose mentioning such a word must not name a vendor.
    """
    prose = "These are the reviews of the network. Nothing here is a config.\n" * 3
    vendor, _ = fingerprint_vendor(prose)
    assert vendor.value != "engenius", "bare substring match on 'ews' regressed"


def _main() -> int:
    tests = [(name, obj) for name, obj in sorted(globals().items())
             if name.startswith("test_") and callable(obj)]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print(f"  [PASS] {name}")
        except AssertionError as exc:
            failed.append((name, str(exc)))
            print(f"  [FAIL] {name}: {exc}")
        except Exception as exc:  # pragma: no cover
            failed.append((name, repr(exc)))
            print(f"  [ERROR] {name}: {exc!r}")

    print()
    if failed:
        print(f"{len(failed)}/{len(tests)} REGRESSION TESTS FAILED")
        return 1
    print(f"ALL {len(tests)} DETECTION REGRESSION TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
