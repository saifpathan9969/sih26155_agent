# GAACA Multi-Vendor Network Configuration Dataset (5,000 Samples)

## Overview
The **GAACA Multi-Vendor Network Configuration Dataset** is a comprehensive, production-grade corpus of 5,000 network device configurations designed for training, benchmarking, and evaluating AI-driven security compliance auditing engines (specifically SIH26155 / GAACA).

The dataset spans **106 vendor/product families** across **5 distinct device categories**, with every sample carrying a structured `.meta.json` sidecar conforming to `metadata_schema.json`.

---

## Dataset Statistics

- **Total Configurations:** 5,000
- **Total Metadata Sidecars:** 5,000
- **Total Files:** 10,000
- **Vendor / Product Families:** 106
- **Categories Covered:** 5
  - **Firewalls:** 21 vendors × 50 configs = 1,050 samples
  - **Routers:** 20 vendors × 50 configs = 1,000 samples
  - **Switches:** 20 vendors × 50 configs = 1,000 samples
  - **WiFi Controllers & APs:** 20 vendors × 50 configs = 1,000 samples
  - **IoT & Industrial Devices:** 25 vendors × 38 configs = 950 samples

### Posture Distribution
- **Secure (Hardened):** 40% (2,000 samples)
  - Complies with CIS benchmarks, DISA STIGs, and vendor hardening best practices.
  - SSHv2/TLS 1.3 only, encrypted passwords, AAA (RADIUS/TACACS+), remote syslog, NTP authentication, default-deny ACLs, no insecure protocols (Telnet/HTTP disabled).
- **Misconfigured (Vulnerable):** 40% (2,000 samples)
  - Deliberately introduces realistic compliance violations for rule-engine testing.
  - Plaintext Telnet/HTTP enabled, default SNMPv2c strings (`public`/`private`), cleartext passwords, missing logging, wildcard permits (`permit ip any any`), missing STP/port-security/encryption.
- **Edge Cases:** 20% (1,000 samples)
  - Partial configurations, deprecated syntax, unreferenced objects, orphan interfaces, empty routing blocks, and conflicting rules to evaluate parser resilience and AI semantic fallback.

---

## Directory Structure

```
GAACA-Network-Config-Dataset/
├── README.md
├── manifest.json
├── metadata_schema.json
├── generate_dataset.py
├── validate_dataset.py
├── generators/
│   ├── base.py
│   ├── firewall_generators.py
│   ├── router_generators.py
│   ├── switch_generators.py
│   ├── wifi_generators.py
│   └── iot_generators.py
│
├── firewall/           (21 vendors: cisco_asa, fortinet_fortigate, paloalto_panos, checkpoint_gaia, ...)
│   └── <vendor>/
│       ├── secure/
│       ├── misconfigured/
│       └── edge_cases/
├── routers/            (20 vendors: cisco_ios, cisco_iosxe, cisco_nxos, juniper_junos, arista_eos, ...)
├── switches/           (20 vendors: cisco_ios_sw, cisco_nxos_sw, juniper_junos_sw, aruba_aoscx_sw, ...)
├── wifi/               (20 vendors: cisco_wlc, cisco_meraki, aruba_instant, juniper_mist, ...)
└── iot/                (25 vendors across industrial, cameras, gateways, smart_devices)
    ├── industrial/     (12 vendors: siemens_plc, schneider_plc, rockwell_plc, abb, ...)
    ├── cameras/        (4 vendors: axis_ipcam, hikvision_ipcam, dahua_ipcam, hanwha_ipcam)
    ├── gateways/       (4 vendors: teltonika_rutos, moxa_industrial, advantech_wise, quectel)
    └── smart_devices/  (5 vendors: tasmota, espressif_esp, particle_iot, johnson_controls, shelly)
```

---

## Privacy & Anonymization Guarantees

1. **Zero Real Credentials:** All passwords, pre-shared keys, and SNMP communities use placeholder tokens (e.g. `P@ssw0rd_PLACEHOLDER`, `REDACTED_COMMUNITY`).
2. **Safe IP Ranges:** All IPv4 addresses are strictly drawn from RFC 5737 documentation blocks (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`) and private RFC 1918 space.
3. **No Proprietary Topologies:** Network hostnames and topologies are procedurally generated and completely disconnected from real-world corporate infrastructures.

---

## How to Regenerate and Validate

### Generation
```bash
python generate_dataset.py
```

### Validation
```bash
python validate_dataset.py
```
Validates JSON schema adherence for all sidecars, ensures 1:1 config-to-metadata file matching, and verifies compliance with safety constraints.

---

## Integration with the VigilNet / GAACA Auditor

This dataset is consumed by `sih26155_agent/device_config_corpus.py`, which
presents it and the 31 hand-authored curated configs through one merged API.

### Merge model

| Source | Count | `source` tag | Body storage |
|---|---|---|---|
| Curated inline configs | 31 | `builtin` | Embedded in the Python module |
| This dataset | 5,000 | `gaaca_dataset` | Read from disk on demand |
| **Merged total** | **5,031** | — | — |

The two sets are merged in code rather than by copying files, for three reasons:

1. **No duplication.** A single `source` discriminator keeps the sets distinct,
   so statistics and filters never double-count.
2. **The tool still works without this directory.** The 31 inline configs are a
   zero-dependency fallback, so a bare container has multi-vendor coverage even
   if the dataset is not shipped alongside it.
3. **Bounded memory.** Only the 5,000 `.meta.json` sidecars are indexed at
   import. Configuration bodies are read lazily via `get_config_content()`,
   because an auditor examines a handful of devices at a time, not all 5,000.

If the directory is absent the loader logs nothing and silently falls back to
the 31 curated entries. Discovery order is
`../GAACA-Network-Config-Dataset` → `./GAACA-Network-Config-Dataset` → `$CWD`.

### API surface

| Endpoint | Purpose |
|---|---|
| `GET /api/corpus/stats` | Totals by vendor, device type, posture, format, vulnerability tag |
| `GET /api/corpus/list` | Paginated, facet-filtered browse (`limit`/`offset`, default 200) |
| `POST /api/corpus/load` | Copy a bounded, optionally random sample into an account |

`POST /api/corpus/load` defaults to `limit=25, sample=True`. The cap is
deliberate: loading thousands of configs into one account makes every
downstream page unusable. `sample=True` draws a random subset so the selection
spans vendors instead of whatever sorts first alphabetically.

Filters accepted by both `list` and `load`: `device_type`, `vendor`, `posture`,
`configuration_format`, `vulnerability_tag`, `source`.

### Ground-truth labels are preserved

`controls_present`, `controls_absent` and `vulnerability_tags` travel with each
config into `_custom_metadata` as `expected_controls_present`,
`expected_controls_absent` and `expected_vulnerability_tags`. This is the most
valuable part of the dataset for this project: it turns the corpus from sample
input into a **scoring harness**, because the rule engine's findings can be
compared against known-correct labels rather than eyeballed.

### Vocabulary mapping

The dataset's 12-value `device_type` vocabulary is mapped onto the classifier's
coarser types, and `security_state` onto the corpus posture vocabulary:

```
wifi_controller, wifi_access_point                    -> wireless_ap
iot_plc, iot_camera, iot_gateway, iot_sensor,
  iot_building_automation                             -> iot_device
sase_gateway                                          -> firewall
firewall, router, switch, load_balancer               -> unchanged

secure -> hardened     misconfigured -> weak     edge_case -> edge_case
```

### What this dataset found

Cross-validating the auditor's detection layers against the 5,000 labels
exposed real defects, all since fixed:

| Metric | Before | After |
|---|---|---|
| Vendor fingerprint `UNKNOWN` | 15.1% (756) | **1.7% (84)** |
| Device-type accuracy (all samples) | 80.5% | **93.6%** |
| Device-type accuracy (excl. edge cases) | — | **93.5%** |

All 84 remaining `UNKNOWN` results are `edge_case` samples, which are
deliberately truncated or corrupted. On the 3,990 `secure` and `misconfigured`
configs, vendor identification is **100%**.

Specific defects the dataset surfaced:

- **Junos hierarchical format was undetectable.** Signatures only covered the
  flat `set ...` form, so every native `show configuration` dump (the
  `junos_hierarchy` format) fell through to `UNKNOWN`.
- **47 vendor families had no signatures**, concentrated in industrial/OT XML
  and JSON formats (Siemens, Rockwell, Schneider, Beckhoff, ABB, Emerson, GE,
  Honeywell, Johnson Controls, Mitsubishi, Omron, WAGO, Phoenix Contact), IP
  cameras (Axis, Hikvision, Dahua, Hanwha), smart devices (Tasmota, Espressif,
  Particle, Shelly) and several CLI dialects (Forcepoint, WatchGuard, Ruijie,
  D-Link, Brocade, Allied Telesis, Sangfor, Nokia SR OS, H3C).
- **Over-eager wireless detection.** A lone `wlan`/`ssid` mention scored as
  strongly as a real radio stanza, so wired switches carrying a VLAN named
  after a wireless network were classified as access points.
- **`virtual server` over-weighted.** Several firewall vendors use the term for
  destination NAT, so firewalls were being classified as load balancers.

Residual ~6% device-type error is dominated by switch↔router confusion, which
is inherent rather than a defect: this dataset files Aruba CX under both
`routers/` (CX 8325/8400 "Core Router") and `switches/` (CX 6200/6300) with
near-identical syntax, and L3 switches running BGP are genuinely both.

### Regenerating

Signature markers were derived from this corpus, not guessed — for each vendor
group, tokens present in at least 55% of that group's samples and in at most
two groups overall. If you regenerate with different templates, re-run the
cross-validation before trusting the detection rates above.
