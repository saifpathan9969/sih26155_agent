"""
GAACA Dataset Generator — Master Orchestration Script
=====================================================
Generates 5,000 configurations across 106 vendor/product families in 5 categories:
- Firewall: 21 vendors × 50 configs = 1,050
- Routers:  20 vendors × 50 configs = 1,000
- Switches: 20 vendors × 50 configs = 1,000
- WiFi:     20 vendors × 50 configs = 1,000
- IoT:      25 vendors × 38 configs =   950
Total:      5,000 configs (.conf/.xml/.json/.rsc + matching .meta.json sidecars)

Also generates manifest.json with full counts and summary stats.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

# Add parent directory of generators to Python path if running standalone
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from generators.firewall_generators import FIREWALL_GENERATORS
from generators.router_generators import ROUTER_GENERATORS
from generators.switch_generators import SWITCH_GENERATORS
from generators.wifi_generators import WIFI_GENERATORS
from generators.iot_generators import IOT_GENERATORS


def run_generation(output_root: Path) -> dict:
    start_time = time.time()
    print(f"[*] Starting GAACA Dataset generation into: {output_root}")

    manifest_stats = {
        "dataset_version": "1.0.0",
        "generation_date": date.today().isoformat(),
        "total_configs": 0,
        "total_sidecars": 0,
        "categories": {},
        "security_state_distribution": {
            "secure": 0,
            "misconfigured": 0,
            "edge_case": 0
        },
        "vendors_total": 0
    }

    categories_plan = [
        ("firewall", FIREWALL_GENERATORS, 20, 20, 10),
        ("routers", ROUTER_GENERATORS, 20, 20, 10),
        ("switches", SWITCH_GENERATORS, 20, 20, 10),
        ("wifi", WIFI_GENERATORS, 20, 20, 10),
        ("iot", IOT_GENERATORS, 15, 15, 8),
    ]

    for cat_name, generator_classes, n_sec, n_misc, n_edge in categories_plan:
        cat_dir = output_root / cat_name
        cat_stats = {
            "vendors": len(generator_classes),
            "configs": 0,
            "secure": 0,
            "misconfigured": 0,
            "edge_cases": 0,
            "vendor_list": []
        }
        print(f"\n[+] Generating {cat_name.upper()} ({len(generator_classes)} vendors)...")

        for gen_cls in generator_classes:
            generator = gen_cls()
            vendor_dir = cat_dir / generator.vendor_dir_name
            count = generator.generate_all(vendor_dir, n_secure=n_sec, n_misconfig=n_misc, n_edge=n_edge)
            
            cat_stats["configs"] += count
            cat_stats["secure"] += n_sec
            cat_stats["misconfigured"] += n_misc
            cat_stats["edge_cases"] += n_edge
            cat_stats["vendor_list"].append(generator.vendor_dir_name)

            manifest_stats["security_state_distribution"]["secure"] += n_sec
            manifest_stats["security_state_distribution"]["misconfigured"] += n_misc
            manifest_stats["security_state_distribution"]["edge_case"] += n_edge

            print(f"    - {generator.vendor_dir_name}: {count} configs generated")

        manifest_stats["categories"][cat_name] = cat_stats
        manifest_stats["total_configs"] += cat_stats["configs"]
        manifest_stats["vendors_total"] += cat_stats["vendors"]

    manifest_stats["total_sidecars"] = manifest_stats["total_configs"]
    manifest_stats["elapsed_seconds"] = round(time.time() - start_time, 2)

    # Write manifest.json
    manifest_path = output_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] Manifest written to {manifest_path}")
    print(f"[OK] Successfully generated {manifest_stats['total_configs']} configurations across {manifest_stats['vendors_total']} vendor families in {manifest_stats['elapsed_seconds']}s")

    return manifest_stats


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent
    run_generation(out_dir)
