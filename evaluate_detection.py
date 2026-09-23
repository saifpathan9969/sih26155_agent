"""
Per-Layer Detection Evaluation
==============================
Scores each layer of the device profile independently against the labelled
corpus, instead of collapsing everything into one "device-type accuracy"
number that mixed together questions of different difficulty.

Reported layers:
    Vendor identification     — did we name the manufacturer?
    Platform identification   — did we name the OS?
    Model identification      — did we name the hardware (coverage + precision)?
    Device class              — router / switch / firewall / AP / IoT class
    Network role              — core / access / edge / perimeter / ...
    Capability detection      — per-capability precision, recall, F1
    Ambiguity behaviour       — do we flag uncertainty where it exists?

Usage:
    python evaluate_detection.py [--dataset PATH] [--limit N] [--verbose]

This is a validation harness, not a runtime component. The corpus it reads is
never served to operators.
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT / "sih26155_agent"))
sys.path.insert(0, str(_ROOT / "sih26155_agent" / "agent"))

from device_profile import DeviceClass, build_device_profile  # noqa: E402
from tools.fingerprint import fingerprint_vendor  # noqa: E402

DEFAULT_DATASET = _ROOT / "GAACA-Network-Config-Dataset"

# Dataset device_type vocabulary -> device_class vocabulary.
CLASS_MAP = {
    "firewall": DeviceClass.FIREWALL,
    "router": DeviceClass.ROUTER,
    "switch": DeviceClass.NETWORK_SWITCH,
    "wifi_controller": DeviceClass.WIRELESS_CONTROLLER,
    "wifi_access_point": DeviceClass.WIRELESS_AP,
    "iot_plc": DeviceClass.IOT_CONTROLLER,
    "iot_building_automation": DeviceClass.IOT_CONTROLLER,
    "iot_camera": DeviceClass.IOT_ENDPOINT,
    "iot_sensor": DeviceClass.IOT_ENDPOINT,
    "iot_gateway": DeviceClass.IOT_GATEWAY,
    "load_balancer": DeviceClass.LOAD_BALANCER,
    "sase_gateway": DeviceClass.FIREWALL,
}

# Classes that are legitimately interchangeable, so scoring them as outright
# errors would be measuring directory-label agreement rather than correctness.
# An L3 switch performing a core role and a router are the canonical example.
EQUIVALENT_CLASSES = [
    {DeviceClass.ROUTER, DeviceClass.NETWORK_SWITCH},
    {DeviceClass.WIRELESS_AP, DeviceClass.WIRELESS_CONTROLLER},
    {DeviceClass.IOT_CONTROLLER, DeviceClass.IOT_ENDPOINT, DeviceClass.IOT_GATEWAY},
    {DeviceClass.FIREWALL, DeviceClass.SECURITY_APPLIANCE},
]

# Dataset control vocabulary -> capability names we emit.
# The corpus labels management-plane controls (ssh_v2, syslog, ntp, ...), not
# protocol capabilities, so capability recall is largely unmeasurable against it.
#
# `default_deny_policy` is deliberately NOT mapped to STATEFUL_POLICY: the corpus
# asserts it for all 1,995 hardened samples including switches and IoT endpoints,
# where it means an ACL or a firewall zone default rather than a stateful
# inspection policy. Mapping it produced a meaningless 11% "recall" that measured
# vocabulary mismatch, not detection failure.
CONTROL_TO_CAPABILITY = {
    "bgp": "BGP",
    "ospf": "OSPF",
    "vlan_segmentation": "VLAN",
    "stp_protection": "STP",
    "port_security": "PORT_SECURITY",
    "dhcp_snooping": "DHCP_SNOOPING",
    "nat": "NAT",
    "ipsec_vpn": "IPSEC_VPN",
    "threat_prevention": "THREAT_PREVENTION",
    "wpa3": "WPA_ENTERPRISE",
    "wpa2_enterprise": "WPA_ENTERPRISE",
    "modbus_restricted": "MODBUS",
}


def _same_or_equivalent(expected: str, got: str) -> bool:
    if expected == got:
        return True
    return any(expected in group and got in group for group in EQUIVALENT_CLASSES)


def _vendor_matches(meta_vendor: str, detected: str, meta_product: str = "") -> bool:
    """
    Compare a corpus vendor label against a detected vendor family.

    Must consider the PRODUCT name too, not just the vendor: the corpus records
    the manufacturer ("Netgate", "Linux", "Open Source / Linux Foundation")
    while our enum is named after the product family ("pfsense", "iptables",
    "sonic"). Comparing vendor alone scored 250 correct detections as failures.
    """
    if not detected or detected == "unknown":
        return False

    def norm(s: str) -> str:
        return s.lower().replace("/", " ").replace("-", " ").replace("_", " ")

    # Two-character brands are real (F5, HP), so keep short tokens here and rely
    # on the alias table rather than a length filter.
    mv_tokens = {t for t in norm(meta_vendor).split() if len(t) > 1}
    prod_tokens = {t for t in norm(meta_product).split() if len(t) > 1}
    det_tokens = {t for t in norm(detected).split() if len(t) > 1}

    if (mv_tokens | prod_tokens) & det_tokens:
        return True
    mv = norm(meta_vendor)
    det = norm(detected)
    aliases = {
        "aruba": {"aruba", "hpe"}, "hpe": {"aruba"},
        "juniper": {"juniper", "mist"}, "cisco": {"cisco", "meraki"},
        "brocade": {"brocade", "ruckus"}, "ruckus": {"ruckus", "brocade"},
        "tp": {"tplink"}, "d": {"dlink"}, "ge": {"ge", "vernova"},
        "tasmota": {"tasmota"}, "particle": {"particle"},
        "phoenix": {"phoenix"}, "johnson": {"johnson"},
        "espressif": {"espressif"}, "hanwha": {"hanwha"},
        "allied": {"allied"}, "extreme": {"extreme"}, "netgear": {"netgear"},
        "watchguard": {"watchguard"}, "forcepoint": {"forcepoint"},
        "sangfor": {"sangfor"}, "hillstone": {"hillstone"},
        "barracuda": {"barracuda"}, "sonicwall": {"sonicwall"},
        "nokia": {"nokia"}, "h3c": {"h3c"}, "dell": {"dell"},
        "ubiquiti": {"ubiquiti"}, "mikrotik": {"mikrotik"},
        "huawei": {"huawei"}, "arista": {"arista"}, "fortinet": {"fortinet"},
        "palo": {"palo"}, "check": {"checkpoint"}, "sophos": {"sophos"},
        "siemens": {"siemens"}, "schneider": {"schneider"},
        "rockwell": {"rockwell"}, "mitsubishi": {"mitsubishi"},
        "omron": {"omron"}, "beckhoff": {"beckhoff"}, "wago": {"wago"},
        "abb": {"abb"}, "emerson": {"emerson"}, "honeywell": {"honeywell"},
        "axis": {"axis"}, "hikvision": {"hikvision"}, "dahua": {"dahua"},
        "teltonika": {"teltonika"}, "quectel": {"quectel"}, "moxa": {"moxa"},
        "advantech": {"advantech"}, "shelly": {"shelly"},
        "cambium": {"cambium"}, "grandstream": {"grandstream"},
        "draytek": {"draytek"}, "zyxel": {"zyxel"}, "ruijie": {"ruijie"},
        "f5": {"f5"}, "kerio": {"kerio"}, "engenius": {"engenius"},
    }
    for token in mv_tokens | {t for t in mv.split()}:
        if aliases.get(token, set()) & det_tokens:
            return True
    return False


def load_samples(dataset: Path, limit: int | None = None):
    metas = sorted(glob.glob(str(dataset / "**" / "*.meta.json"), recursive=True))
    if limit:
        metas = metas[:limit]
    for meta_path in metas:
        try:
            meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        stem = meta_path[: -len(".meta.json")]
        config = None
        for ext in (".conf", ".cfg", ".json", ".xml", ".rsc", ".ini", ".txt"):
            if os.path.isfile(stem + ext):
                config = stem + ext
                break
        if not config:
            continue
        try:
            raw = Path(config).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        yield meta, os.path.basename(config), raw


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=str(DEFAULT_DATASET))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    dataset = Path(args.dataset)
    if not dataset.is_dir():
        print(f"Dataset not found: {dataset}")
        return 2

    n = 0
    vendor_ok = platform_ok = abstained = 0
    model_named = model_attempted = model_correct = model_checked = 0
    status_counts: collections.Counter = collections.Counter()
    class_exact = class_equiv = 0
    role_determined = 0
    ambiguous = 0
    class_confusion: collections.Counter = collections.Counter()
    cap_tp: collections.Counter = collections.Counter()
    cap_fn: collections.Counter = collections.Counter()
    by_state: collections.Counter = collections.Counter()
    real_class_exact = real_n = 0

    for meta, filename, raw in load_samples(dataset, args.limit):
        n += 1
        state = meta.get("security_state", "unknown")
        by_state[state] += 1

        vendor, vconf = fingerprint_vendor(raw)
        profile = build_device_profile(raw, filename=filename, vendor=vendor.value)

        status_counts[profile.get("classification_status", "UNSPECIFIED")] += 1

        if _vendor_matches(meta.get("vendor", ""), vendor.value, meta.get("product", "")):
            vendor_ok += 1
        elif vendor.value == "unknown":
            abstained += 1
        if profile.get("platform"):
            platform_ok += 1

        claimed_model = profile.get("model")
        if claimed_model:
            model_named += 1
            corpus_product = str(meta.get("product", "")).lower()
            if corpus_product:
                model_checked += 1
                claim_tokens = {t for t in claimed_model.lower().replace("/", " ").split() if len(t) > 2}
                prod_tokens = {t for t in corpus_product.replace("/", " ").split() if len(t) > 2}
                if claim_tokens & prod_tokens:
                    model_correct += 1
        model_attempted += 1

        # Prefer the separated device_class label; fall back to the legacy
        # single label only for sidecars that have not been relabelled.
        # Score against the ORIGINAL independent label, not the relabelled one.
        # Relabelling was performed by this same classifier, so evaluating
        # against `device_class` would be tautological and would report a
        # meaningless 100%. `legacy_device_type` is the label that was assigned
        # independently of this code, which makes it the only honest baseline.
        legacy = meta.get("legacy_device_type") or meta.get("device_type", "")
        expected = CLASS_MAP.get(legacy, DeviceClass.UNKNOWN)
        got = profile["device_class"]
        if expected == got:
            class_exact += 1
            class_equiv += 1
        elif _same_or_equivalent(expected, got):
            class_equiv += 1
            class_confusion[f"{expected} ~ {got} (equivalent)"] += 1
        else:
            class_confusion[f"{expected} -> {got}"] += 1

        if state != "edge_case":
            real_n += 1
            if expected == got:
                real_class_exact += 1

        if profile["network_role"] != "unknown":
            role_determined += 1
        if profile["ambiguity"]:
            ambiguous += 1

        detected_caps = set(profile["capabilities"])
        for control in (meta.get("controls_present") or []):
            cap = CONTROL_TO_CAPABILITY.get(control)
            if not cap:
                continue
            if cap in detected_caps:
                cap_tp[cap] += 1
            else:
                cap_fn[cap] += 1

    if not n:
        print("No samples loaded.")
        return 2

    def pct(a: int, b: int) -> str:
        return f"{100.0 * a / b:5.1f}%" if b else "  n/a"

    print("=" * 74)
    print(f"PER-LAYER DETECTION EVALUATION   ({n} samples)")
    print(f"corpus state mix: {dict(by_state)}")
    print("=" * 74)
    wrong_vendor = n - vendor_ok - abstained
    print(f"  Vendor identification      {pct(vendor_ok, n)}   ({vendor_ok}/{n})")
    print(f"    wrong vendor             {pct(wrong_vendor, n)}   ({wrong_vendor}/{n}) "
          f"<- the number that matters")
    print(f"    abstained (no guess)     {pct(abstained, n)}   ({abstained}/{n}) "
          f"<- correct refusals, not misses")
    print(f"  Platform identification    {pct(platform_ok, n)}   ({platform_ok}/{n})")
    print(f"  Model coverage             {pct(model_named, model_attempted)}   "
          f"({model_named}/{model_attempted} claimed)")
    print(f"    model precision          {pct(model_correct, model_checked)}   "
          f"({model_correct}/{model_checked} claims verifiable against corpus product)")
    print(f"  Device class (exact)       {pct(class_exact, n)}   ({class_exact}/{n})")
    print(f"  Device class (+equivalent) {pct(class_equiv, n)}   ({class_equiv}/{n})")
    print(f"  Device class, real configs {pct(real_class_exact, real_n)}   "
          f"({real_class_exact}/{real_n}, edge cases excluded)")
    print(f"  Network role determined    {pct(role_determined, n)}   ({role_determined}/{n})")
    print(f"  Flagged ambiguous          {pct(ambiguous, n)}   ({ambiguous}/{n})")

    print("\n  Capability detection recall (labelled controls only):")
    for cap in sorted(set(cap_tp) | set(cap_fn)):
        tp, fn = cap_tp[cap], cap_fn[cap]
        print(f"    {cap:22} {pct(tp, tp + fn)}   ({tp}/{tp + fn})")

    if class_confusion:
        print("\n  Device-class disagreements (top 12):")
        for label, count in class_confusion.most_common(12):
            print(f"    {count:5}  {label}")

    print("\n  Classification status distribution:")
    for status, count in status_counts.most_common():
        print(f"    {status:24} {pct(count, n)}   ({count}/{n})")

    print("\n  Reading these numbers:")
    print("  - Model COVERAGE and model PRECISION are reported separately and")
    print("    deliberately. Coverage is low because a plausibility gate abstains")
    print("    from naming a model on ambiguous evidence: a vendor name inside an")
    print("    SSID string ('Sophos-Open') must not become a hardware claim.")
    print("  - Abstentions are correct refusals, not failures. Insufficient")
    print("    evidence and wrong classification are different outcomes, so the")
    print("    headline number to judge is the WRONG-VENDOR rate, not accuracy.")
    print("  - Device class is scored against `legacy_device_type`, the label")
    print("    assigned independently of this code. Scoring against the relabelled")
    print("    `device_class` would be circular, since this classifier produced it.")
    print("  - 'equivalent' pairs are classes that legitimately overlap, e.g. an L3")
    print("    switch in a core role versus a router. Counting those as errors")
    print("    measures directory-label agreement, not device identification.")
    print("  - Network role and model are reported as COVERAGE, not accuracy: the")
    print("    corpus carries no independent ground truth for either.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
