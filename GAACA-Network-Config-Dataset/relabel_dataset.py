"""
Relabel the dataset with a separated device model.
==================================================

WHY
---
The original sidecars carry a single ``device_type`` that conflates three
different questions, and its value was driven by which directory the sample
landed in:

    routers/aruba_aoscx/...      -> device_type: "router"
    switches/aruba_aoscx_sw/...  -> device_type: "switch"

Those two configurations are near-identical AOS-CX syntax. An Aruba CX 8325 is
a **switch** at the hardware level performing a **core routing role** at the
network level, and it runs BGP. One label cannot express that, so any classifier
scored against it is being measured on directory agreement rather than on
device identification.

Same problem elsewhere in the corpus:
    firewall/f5_bigip/...        -> "firewall"   (F5 BIG-IP is a load balancer)
    firewall/huawei_ar/...       -> "firewall"   (AR series is a branch router)
    firewall/ubiquiti_edgeos/... -> "firewall"   (EdgeRouter is a router)

WHAT THIS DOES
--------------
Adds a separated model to every sidecar:

    device_class      hardware family      (switch / router / firewall / ...)
    network_role      deployment role      (core / access / perimeter / ...)
    model             identified hardware  (when the config names it)
    platform          OS / firmware
    capabilities      what the config proves it can do (BGP, VLAN, STP, NAT...)
    routing_capable   derived from capabilities, not from device_class
    l2_capable        derived from capabilities

The original value is preserved as ``legacy_device_type`` so nothing is lost and
the change is auditable. Where the derived class disagrees with the original
label, ``label_confidence`` is set to ``review`` and ``label_disagreement``
explains why — the script does not pretend to be certain.

Files are never moved: reorganising 10,000 paths is riskier than fixing labels,
and the labels are what any consumer should key on.

Usage:
    python relabel_dataset.py --dry-run     # report only, change nothing
    python relabel_dataset.py               # write the new fields
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import sys
from datetime import date
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJECT = _HERE.parent
sys.path.insert(0, str(_PROJECT / "sih26155_agent"))
sys.path.insert(0, str(_PROJECT / "sih26155_agent" / "agent"))

from device_profile import build_device_profile  # noqa: E402
from tools.fingerprint import fingerprint_vendor, vendor_display_name  # noqa: E402

RELABEL_VERSION = "2.0.0"

CONFIG_EXTENSIONS = (".conf", ".cfg", ".json", ".xml", ".rsc", ".ini", ".txt", ".log")


def find_config(meta_path: str) -> str | None:
    stem = meta_path[: -len(".meta.json")]
    for ext in CONFIG_EXTENSIONS:
        if os.path.isfile(stem + ext):
            return stem + ext
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report without writing")
    ap.add_argument("--dataset", default=str(_HERE))
    args = ap.parse_args()

    metas = sorted(glob.glob(str(Path(args.dataset) / "**" / "*.meta.json"), recursive=True))
    if not metas:
        print(f"No sidecars found under {args.dataset}")
        return 2

    written = skipped = disagreements = 0
    class_changes: collections.Counter = collections.Counter()
    role_dist: collections.Counter = collections.Counter()
    class_dist: collections.Counter = collections.Counter()
    model_named = 0

    for meta_path in metas:
        try:
            meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            skipped += 1
            continue

        config_path = find_config(meta_path)
        if not config_path:
            skipped += 1
            continue

        try:
            raw = Path(config_path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            skipped += 1
            continue

        vendor, vendor_conf = fingerprint_vendor(raw)
        profile = build_device_profile(
            raw, filename=os.path.basename(config_path), vendor=vendor.value
        )

        legacy = meta.get("device_type")
        derived_class = profile["device_class"]

        # Preserve the original label exactly once, so re-running is idempotent.
        if "legacy_device_type" not in meta:
            meta["legacy_device_type"] = legacy

        meta["device_class"] = derived_class
        meta["network_role"] = profile["network_role"]
        meta["platform"] = profile["platform"] or meta.get("os")
        meta["model"] = profile["model"]
        meta["capabilities"] = profile["capabilities"]
        meta["routing_protocols"] = profile["routing_protocols"]
        # Field name matches the dataset schema's existing `routing_capability`.
        meta["routing_capability"] = profile["routing_capable"]
        meta["l2_capable"] = profile["l2_capable"]
        # Drop keys written by earlier revisions of this script; the schema sets
        # additionalProperties=false, so a stale field fails validation.
        for obsolete in ("routing_capable",):
            meta.pop(obsolete, None)
        meta["detected_vendor"] = vendor.value
        meta["detected_vendor_display"] = vendor_display_name(vendor)
        meta["device_class_basis"] = profile["device_class_basis"]
        meta["relabel_version"] = RELABEL_VERSION
        meta["relabel_date"] = date.today().isoformat()

        # Honest disagreement reporting rather than silent overwrite.
        legacy_as_class = {
            "switch": "network_switch",
            "router": "router",
            "firewall": "firewall",
            "wifi_controller": "wireless_controller",
            "wifi_access_point": "wireless_ap",
            "iot_plc": "iot_controller",
            "iot_building_automation": "iot_controller",
            "iot_camera": "iot_endpoint",
            "iot_sensor": "iot_endpoint",
            "iot_gateway": "iot_gateway",
            "load_balancer": "load_balancer",
            "sase_gateway": "firewall",
        }.get(legacy or "")

        if profile["ambiguity"]:
            meta["label_confidence"] = "ambiguous"
            meta["label_disagreement"] = profile["ambiguity_reason"]
        elif legacy_as_class and legacy_as_class != derived_class:
            meta["label_confidence"] = "review"
            meta["label_disagreement"] = (
                f"Directory-derived label was '{legacy}' but the configuration "
                f"identifies as '{derived_class}' via {profile['device_class_basis']}. "
                f"Network role '{profile['network_role']}' likely explains the original "
                f"label (a routing role does not change the hardware class)."
            )
            disagreements += 1
            class_changes[f"{legacy_as_class} -> {derived_class}"] += 1
        else:
            meta["label_confidence"] = "verified"
            meta.pop("label_disagreement", None)

        class_dist[derived_class] += 1
        role_dist[profile["network_role"]] += 1
        if profile["model"]:
            model_named += 1

        if not args.dry_run:
            Path(meta_path).write_text(
                json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        written += 1

    mode = "DRY RUN — nothing written" if args.dry_run else "WRITTEN"
    print("=" * 72)
    print(f"RELABEL v{RELABEL_VERSION}   ({mode})")
    print("=" * 72)
    print(f"  sidecars processed : {written}")
    print(f"  skipped            : {skipped}")
    print(f"  model identified   : {model_named} ({100.0*model_named/max(1,written):.1f}%)")
    print(f"  label disagreements: {disagreements} ({100.0*disagreements/max(1,written):.1f}%)")
    print()
    print("  device_class distribution:")
    for k, v in class_dist.most_common():
        print(f"    {k:22} {v:5}")
    print()
    print("  network_role distribution:")
    for k, v in role_dist.most_common():
        print(f"    {k:22} {v:5}")
    if class_changes:
        print()
        print("  corrected labels (original -> derived):")
        for k, v in class_changes.most_common(15):
            print(f"    {v:5}  {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
