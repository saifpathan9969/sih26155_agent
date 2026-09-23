"""
Device Classification — compatibility shim over the layered profiler.
=====================================================================

The real logic now lives in ``device_profile.py``, which models a device as a
hierarchy (vendor -> platform -> model -> device class -> capabilities ->
network role) instead of a single flat ``device_type`` string.

This module is retained so existing callers keep working, and it maps the
layered profile back onto the old key names:

    device_type   <- device_class        (router / network_switch / firewall / ...)
    device_class  <- asset_group         (network / security / iot)

Note the deliberate rename: ``device_class`` previously meant the coarse
three-way UI grouping, but in standard usage a device's *class* is its hardware
family. The grouping is now called ``asset_group``.

New code should import ``build_device_profile`` from ``device_profile`` directly.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from device_profile import (  # noqa: F401  (re-exported for callers)
    ASSET_GROUP_DISPLAY,
    DEVICE_CLASS_DISPLAY,
    DEVICE_CLASS_ICON,
    NETWORK_ROLE_DISPLAY,
    AssetGroup,
    DeviceClass,
    NetworkRole,
    build_device_profile,
    detect_capabilities,
    extract_hostname,
    summarize_profiles,
)

# Legacy aliases. The old vocabulary used "switch"/"iot_device"; the profiler
# uses "network_switch"/"iot_controller"/"iot_endpoint"/"iot_gateway".
_LEGACY_TYPE_ALIAS: Dict[str, str] = {
    DeviceClass.NETWORK_SWITCH: "switch",
    DeviceClass.IOT_CONTROLLER: "iot_device",
    DeviceClass.IOT_ENDPOINT: "iot_device",
    DeviceClass.IOT_GATEWAY: "iot_device",
    DeviceClass.WIRELESS_CONTROLLER: "wireless_ap",
}


def legacy_device_type(device_class: str) -> str:
    """Collapse a device class onto the older coarse vocabulary."""
    return _LEGACY_TYPE_ALIAS.get(device_class, device_class)


def classify_device(
    raw_text: str,
    filename: Optional[str] = None,
    vendor: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build the layered profile and expose it under both new and legacy keys.

    Returns every ``device_profile`` field, plus:
      device_type / device_type_display / device_type_icon / device_type_confidence
      device_class (legacy meaning: the coarse asset group)
      device_class_display (legacy meaning: the asset-group label)
    """
    profile = build_device_profile(raw_text, filename=filename, vendor=vendor)

    legacy_type = legacy_device_type(profile["device_class"])
    result: Dict[str, Any] = dict(profile)

    # Preserve the layered values under unambiguous names before the legacy
    # aliases shadow them.
    result["hardware_class"] = profile["device_class"]
    result["hardware_class_display"] = profile["device_class_display"]

    result.update({
        "device_type": legacy_type,
        "device_type_display": profile["device_class_display"],
        "device_type_icon": profile["device_class_icon"],
        "device_type_confidence": profile["device_class_confidence"],
        "device_type_signals": profile["network_role_reasons"],
        # Legacy: device_class meant the coarse grouping
        "device_class": profile["asset_group"],
        "device_class_display": profile["asset_group_display"],
    })
    return result


def summarize_asset_mix(devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Asset-mix counters for Mission Control, keyed on the legacy ``device_type``
    vocabulary so existing UI code continues to resolve.
    """
    buckets: Dict[str, Dict[str, Any]] = {}
    for dev in devices:
        hardware = dev.get("hardware_class") or dev.get("device_class") or DeviceClass.UNKNOWN
        dtype = dev.get("device_type") or legacy_device_type(hardware)
        entry = buckets.setdefault(dtype, {
            "device_type": dtype,
            "device_type_display": dev.get("device_type_display")
            or DEVICE_CLASS_DISPLAY.get(hardware, dtype),
            "device_type_icon": dev.get("device_type_icon")
            or DEVICE_CLASS_ICON.get(hardware, "\u2753"),
            "device_class": dev.get("asset_group", AssetGroup.UNKNOWN),
            "count": 0,
            "filenames": [],
        })
        entry["count"] += 1
        entry["filenames"].append(dev.get("filename"))

    return sorted(buckets.values(), key=lambda e: -e["count"])
