"""
Baseline capture and regression gate for the detection layers.
==============================================================

Two modes:

    python detection_baseline.py --freeze     capture current metrics to baseline/
    python detection_baseline.py --check      compare current code against baseline

The gate exists to prevent a specific failure mode: "improving" vendor accuracy
by converting legitimate abstentions into confident wrong answers. A run that
raises accuracy while also raising the wrong-vendor count is a REGRESSION, not
an improvement, and --check fails it.

Acceptance criteria enforced by --check:
    wrong-vendor count            must not increase
    CAPsMAN errors                must not increase
    SRX -> PAN-OS errors          must not increase
    Sophos SSID false positives   must remain 0
    model precision               must not decrease
    valid abstentions             must not be converted into wrong answers
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
sys.path.insert(0, str(_ROOT))

from device_profile import build_device_profile  # noqa: E402
from tools.fingerprint import fingerprint_vendor  # noqa: E402
from evaluate_detection import CLASS_MAP, _vendor_matches  # noqa: E402

DATASET = _ROOT / "GAACA-Network-Config-Dataset"
BASELINE_DIR = _ROOT / "baseline"

# Targeted failure families we are actively working on.
FAILURE_FAMILIES = {
    "mikrotik_capsman": lambda meta, got: "capsman" in str(meta.get("product", "")).lower(),
    "juniper_srx_panos": lambda meta, got: (
        "srx" in str(meta.get("product", "")).lower() and got == "palo_alto_panos"
    ),
    "sophos_ssid": lambda meta, got: (
        "sophos" in str(meta.get("vendor", "")).lower()
        and str(meta.get("device_type", "")).startswith("wifi")
        and got in ("sophos_xg", "pfsense", "opnsense")
    ),
}


def collect() -> dict:
    """Run every layer over the corpus and return a full metrics + failures dict."""
    n = 0
    vendor_ok = 0
    model_named = 0
    model_correct = 0
    model_checked = 0
    abstentions = []          # sample ids where vendor is legitimately unknown
    wrong_vendor = []         # sample ids with a confident but wrong vendor
    class_exact = 0
    family_counts: collections.Counter = collections.Counter()
    status_counts: collections.Counter = collections.Counter()

    for meta_path in sorted(glob.glob(str(DATASET / "**" / "*.meta.json"), recursive=True)):
        try:
            meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        stem = meta_path[: -len(".meta.json")]
        config = next(
            (stem + e for e in (".conf", ".cfg", ".json", ".xml", ".rsc", ".ini")
             if os.path.isfile(stem + e)),
            None,
        )
        if not config:
            continue
        raw = Path(config).read_text(encoding="utf-8", errors="replace")
        n += 1

        vendor, vconf = fingerprint_vendor(raw)
        profile = build_device_profile(raw, filename=os.path.basename(config),
                                       vendor=vendor.value)
        sample_id = meta.get("sample_id") or os.path.basename(config)
        state = meta.get("security_state", "unknown")

        status = profile.get("classification_status", "UNSPECIFIED")
        status_counts[status] += 1

        matched = _vendor_matches(meta.get("vendor", ""), vendor.value, meta.get("product", ""))
        if matched:
            vendor_ok += 1
        elif vendor.value == "unknown":
            # Abstention: the system declined rather than guessing. Tracked
            # separately because converting these into wrong answers is the
            # regression this gate exists to catch.
            abstentions.append({"sample_id": sample_id, "state": state,
                                "vendor": meta.get("vendor"), "product": meta.get("product")})
        else:
            wrong_vendor.append({"sample_id": sample_id, "state": state,
                                 "expected_vendor": meta.get("vendor"),
                                 "product": meta.get("product"),
                                 "detected": vendor.value})
            for family, predicate in FAILURE_FAMILIES.items():
                try:
                    if predicate(meta, vendor.value):
                        family_counts[family] += 1
                except Exception:
                    pass

        # Model precision: only measurable where the corpus names a model AND we
        # claimed one. Coverage alone would hide a precision collapse.
        claimed = profile.get("model")
        if claimed:
            model_named += 1
            corpus_product = str(meta.get("product", "")).lower()
            if corpus_product:
                model_checked += 1
                claim_tokens = {t for t in claimed.lower().replace("/", " ").split() if len(t) > 2}
                prod_tokens = {t for t in corpus_product.replace("/", " ").split() if len(t) > 2}
                if claim_tokens & prod_tokens:
                    model_correct += 1

        legacy = meta.get("legacy_device_type") or meta.get("device_type", "")
        if CLASS_MAP.get(legacy) == profile["device_class"]:
            class_exact += 1

    return {
        "samples": n,
        "vendor": {
            "correct": vendor_ok,
            "accuracy": round(vendor_ok / n, 4) if n else 0.0,
            "wrong_count": len(wrong_vendor),
            "wrong_rate": round(len(wrong_vendor) / n, 4) if n else 0.0,
            "abstention_count": len(abstentions),
            "abstention_rate": round(len(abstentions) / n, 4) if n else 0.0,
        },
        "model": {
            "claimed": model_named,
            "coverage": round(model_named / n, 4) if n else 0.0,
            "checked": model_checked,
            "correct": model_correct,
            "precision": round(model_correct / model_checked, 4) if model_checked else None,
        },
        "device_class": {
            "exact": class_exact,
            "accuracy": round(class_exact / n, 4) if n else 0.0,
        },
        "classification_status": dict(status_counts),
        "failure_families": dict(family_counts),
        "wrong_vendor_cases": wrong_vendor,
        "abstention_cases": abstentions,
    }


def freeze(results: dict) -> None:
    BASELINE_DIR.mkdir(exist_ok=True)
    (BASELINE_DIR / "vendor_metrics.json").write_text(
        json.dumps({"samples": results["samples"], **results["vendor"],
                    "classification_status": results["classification_status"]},
                   indent=2), encoding="utf-8")
    (BASELINE_DIR / "model_metrics.json").write_text(
        json.dumps(results["model"], indent=2), encoding="utf-8")
    (BASELINE_DIR / "failure_cases.json").write_text(
        json.dumps({"failure_families": results["failure_families"],
                    "wrong_vendor_cases": results["wrong_vendor_cases"],
                    "abstention_cases": results["abstention_cases"]},
                   indent=2), encoding="utf-8")
    print(f"Frozen baseline to {BASELINE_DIR}")
    print(f"  samples            : {results['samples']}")
    print(f"  vendor accuracy    : {results['vendor']['accuracy']:.4f}")
    print(f"  wrong-vendor count : {results['vendor']['wrong_count']}")
    print(f"  abstentions        : {results['vendor']['abstention_count']}")
    print(f"  model coverage     : {results['model']['coverage']:.4f}")
    print(f"  model precision    : {results['model']['precision']}")
    print(f"  failure families   : {results['failure_families']}")


def check(results: dict) -> int:
    if not (BASELINE_DIR / "vendor_metrics.json").is_file():
        print("No baseline found. Run --freeze first.")
        return 2

    base_v = json.loads((BASELINE_DIR / "vendor_metrics.json").read_text(encoding="utf-8"))
    base_m = json.loads((BASELINE_DIR / "model_metrics.json").read_text(encoding="utf-8"))
    base_f = json.loads((BASELINE_DIR / "failure_cases.json").read_text(encoding="utf-8"))

    cur_v, cur_m = results["vendor"], results["model"]
    failures: list[str] = []
    notes: list[str] = []

    print("=" * 74)
    print("REGRESSION GATE")
    print("=" * 74)

    def cmp_line(label: str, base, cur, better: str) -> None:
        arrow = "same" if base == cur else ("UP" if cur > base else "DOWN")
        print(f"  {label:32} {str(base):>10} -> {str(cur):<10} {arrow:<8} (better: {better})")

    cmp_line("vendor accuracy", base_v["accuracy"], cur_v["accuracy"], "higher")
    cmp_line("wrong-vendor count", base_v["wrong_count"], cur_v["wrong_count"], "lower")
    cmp_line("abstention count", base_v["abstention_count"], cur_v["abstention_count"], "stable")
    cmp_line("model coverage", base_m["coverage"], cur_m["coverage"], "higher")
    cmp_line("model precision", base_m["precision"], cur_m["precision"], "higher")

    # --- Criterion 1: wrong-vendor count must not increase -----------------
    if cur_v["wrong_count"] > base_v["wrong_count"]:
        failures.append(
            f"wrong-vendor count rose {base_v['wrong_count']} -> {cur_v['wrong_count']}"
        )

    # --- Criterion 2: abstentions must not become wrong answers ------------
    base_abstain = {c["sample_id"] for c in base_f.get("abstention_cases", [])}
    cur_wrong = {c["sample_id"] for c in results["wrong_vendor_cases"]}
    converted = base_abstain & cur_wrong
    if converted:
        failures.append(
            f"{len(converted)} legitimate abstention(s) became confident wrong answers: "
            f"{sorted(converted)[:5]}"
        )

    # --- Criterion 3: targeted failure families must not grow --------------
    for family in FAILURE_FAMILIES:
        before = base_f.get("failure_families", {}).get(family, 0)
        after = results["failure_families"].get(family, 0)
        arrow = "same" if before == after else ("improved" if after < before else "WORSE")
        print(f"  {('family: ' + family):32} {before:>10} -> {after:<10} {arrow}")
        if after > before:
            failures.append(f"failure family '{family}' grew {before} -> {after}")

    # --- Criterion 4: Sophos SSID false positives must stay at zero --------
    sophos = results["failure_families"].get("sophos_ssid", 0)
    if sophos:
        failures.append(f"sophos_ssid false positives reappeared ({sophos})")

    # --- Criterion 5: model precision must not regress ---------------------
    if base_m["precision"] is not None and cur_m["precision"] is not None:
        if cur_m["precision"] < base_m["precision"] - 1e-9:
            failures.append(
                f"model precision fell {base_m['precision']} -> {cur_m['precision']}"
            )

    # Informational: accuracy gained purely by abstaining less is suspicious.
    if (cur_v["accuracy"] > base_v["accuracy"]
            and cur_v["wrong_count"] > base_v["wrong_count"]):
        notes.append(
            "accuracy rose but so did the wrong-vendor count — the gain came at the "
            "cost of correctness, not from better evidence"
        )

    print()
    for note in notes:
        print(f"  NOTE: {note}")
    if failures:
        print("  GATE FAILED:")
        for f in failures:
            print(f"    - {f}")
        return 1
    print("  GATE PASSED — no acceptance criterion violated.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if not DATASET.is_dir():
        print(f"Dataset not found: {DATASET}")
        return 2

    results = collect()
    if args.freeze:
        freeze(results)
        return 0
    return check(results)


if __name__ == "__main__":
    raise SystemExit(main())
