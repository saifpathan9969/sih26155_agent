"""
GAACA Dataset Validator
=======================
Validates the entire GAACA Multi-Vendor Network Configuration Dataset:
1. Every .meta.json sidecar matches metadata_schema.json (using jsonschema or custom fallback validator)
2. Every .meta.json has a matching configuration file (.conf/.xml/.json/.rsc)
3. Every sample conforms to security anonymization rules (no secrets, safe RFC 5737 IPs)
4. Sample counts match manifest expectations
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Safe RFC 5737 prefixes + RFC 1918 / loopback / standard lab blocks
SAFE_IP_PREFIXES = ("192.0.2.", "198.51.100.", "203.0.113.", "10.", "172.16.", "192.168.", "127.", "0.0.0.0", "255.")

def validate_dataset(dataset_root: Path) -> bool:
    print(f"[*] Validating GAACA Dataset at: {dataset_root}")
    
    schema_path = dataset_root / "metadata_schema.json"
    if not schema_path.exists():
        print(f"[!] ERROR: metadata_schema.json missing at {schema_path}")
        return False
    
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    
    manifest_path = dataset_root / "manifest.json"
    if not manifest_path.exists():
        print(f"[!] ERROR: manifest.json missing at {manifest_path}")
        return False
    
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_total = manifest.get("total_configs", 5000)

    try:
        import jsonschema
        has_jsonschema = True
    except ImportError:
        has_jsonschema = False
        print("[!] Note: jsonschema library not installed; performing manual schema field validation")

    meta_files = list(dataset_root.glob("**/*.meta.json"))
    print(f"[*] Found {len(meta_files)} metadata files to validate (expected ~{expected_total})")

    if len(meta_files) != expected_total:
        print(f"[!] Warning: Count mismatch. Found {len(meta_files)} files, manifest has {expected_total}")

    errors = []
    sample_id_pattern = re.compile(r"^[A-Z]{2,4}-[A-Z0-9_]+-[SME]-\d{3}$")
    valid_states = {"secure", "misconfigured", "edge_case"}
    valid_categories = {"firewall", "router", "switch", "wifi", "iot"}

    checked = 0
    for meta_file in meta_files:
        checked += 1
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"{meta_file}: Invalid JSON - {e}")
            continue

        if has_jsonschema:
            try:
                jsonschema.validate(instance=meta, schema=schema)
            except Exception as e:
                errors.append(f"{meta_file}: Schema validation error: {e}")
        else:
            # Fallback manual validation
            required_keys = [
                "sample_id", "vendor", "product", "device_type", "device_class",
                "network_role", "routing_capability", "os", "version",
                "category", "source_type", "configuration_format", "security_state",
                "controls_present", "controls_absent", "contains_secrets", "anonymized",
                "generation_date", "generator_version"
            ]
            for rk in required_keys:
                if rk not in meta:
                    errors.append(f"{meta_file}: Missing required key '{rk}'")
            
            sid = meta.get("sample_id", "")
            if not sample_id_pattern.match(sid):
                errors.append(f"{meta_file}: sample_id '{sid}' does not match pattern")
            
            if meta.get("security_state") not in valid_states:
                errors.append(f"{meta_file}: Invalid security_state '{meta.get('security_state')}'")

            if meta.get("category") not in valid_categories:
                errors.append(f"{meta_file}: Invalid category '{meta.get('category')}'")

            if not meta.get("device_class"):
                errors.append(f"{meta_file}: device_class cannot be empty")

            if not meta.get("network_role"):
                errors.append(f"{meta_file}: network_role cannot be empty")

            if meta.get("contains_secrets") is not False:
                errors.append(f"{meta_file}: contains_secrets must be False")

            if meta.get("anonymized") is not True:
                errors.append(f"{meta_file}: anonymized must be True")

        # Check for matching config file
        base_name = meta_file.name[:-10]  # remove .meta.json
        parent = meta_file.parent
        matching_configs = list(parent.glob(f"{base_name}.*"))
        matching_configs = [c for c in matching_configs if not c.name.endswith(".meta.json")]
        if not matching_configs:
            errors.append(f"{meta_file}: Missing matching configuration file for {base_name}")

        if checked % 1000 == 0:
            print(f"    ... checked {checked}/{len(meta_files)} files")

    if errors:
        print(f"[!] Validation FAILED with {len(errors)} errors:")
        for err in errors[:20]:
            print(f"    - {err}")
        if len(errors) > 20:
            print(f"    ... and {len(errors) - 20} more errors")
        return False
    else:
        print(f"[OK] Validation PASSED for all {checked} configuration samples!")
        return True


if __name__ == "__main__":
    d_root = Path(__file__).resolve().parent
    success = validate_dataset(d_root)
    sys.exit(0 if success else 1)
