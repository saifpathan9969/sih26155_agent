# SIH26155 — Security Audit Agent (Reference Implementation)

This is a working reference implementation of the agent architecture: an
orchestration layer that sequences the already-proven deterministic
components (schema, rule engine, training flow) rather than replacing them.

## Run it

```bash
pip install pydantic pyyaml scikit-learn --break-system-packages
cd agent
python3 demo_mission.py
```

This runs a full mission against 6 synthetic devices and prints:
1. The BEFORE state (3 Juniper devices stuck on `NEEDS_HUMAN_REVIEW`)
2. The live Mission Mode trace (discovery → fingerprint → parse → cluster →
   human gate → compliance → report)
3. The AFTER state — all 3 devices flip to `PASS` from ONE human
   confirmation, because reflection grouped them into a single review
4. The final mission report

## Layout

```
security_baseline_schema.py   # Universal Security Baseline (unchanged)
rule_engine.py                 # Deterministic 20-rule compliance engine (unchanged)
training_flow.py               # Single-device training loop (unchanged)
cis_rules.yaml                  # The 20 CIS-subset rules (unchanged)

agent/
├── agent.py           # SecurityAuditAgent — the orchestration loop
├── planner.py          # Goal → plan. Deterministic v1; LLM swap-point marked
├── state.py             # PlanStep / GroupedReview / MissionState dataclasses
├── reflection.py        # Clusters repeated unknown syntax across devices
├── fixtures.py           # 6 synthetic devices designed to exercise every path
├── demo_mission.py       # Runnable end-to-end demo
│
├── tools/
│   ├── discovery.py       # Tool 1 — file discovery
│   ├── fingerprint.py      # Tool 2 — vendor ID (v1: rule-based signatures)
│   ├── parsing.py           # Tool 3 — mini Cisco IOS / Juniper Junos parsers
│   ├── compliance.py        # Tool 7 — wraps rule_engine.evaluate_baseline
│   ├── remediation.py       # Tool 8 — verified-command lookup, never generated
│   └── reporting.py         # Tool 9 — assembles the mission report
│
├── memory/
│   ├── working.py            # This mission's live counters
│   ├── knowledge_base.py      # Re-exports training_flow.VendorKnowledgeBase
│   └── episodic.py             # History of past corrections/sessions
│
└── policies/
    └── autonomy.py             # The enforced autonomy boundary table
```

## What's real vs. what's a stand-in

**Real, tested, and running:**
- The 6-device mission end to end
- Cross-device clustering (3 Juniper devices → 1 review request)
- Applying one human confirmation across an entire cluster at once
- Graceful degradation for an unsupported vendor (FortiOS here) — no
  parser exists, so every relevant line correctly surfaces as needing
  review rather than being silently guessed at
- The autonomy policy is enforced in code (`policies/autonomy.py`), not
  just described in a document

**Deliberate stand-ins, clearly marked in the code:**
- `planner.py` — a deterministic keyword-based planner, not a live LLM call
  (marked as the swap-point; a demo should not depend on reaching an
  external API on stage)
- `agent._infer_demo_mapping()` — stands in for the real Interactive
  Training UI from `training_flow.py`; it maps the ONE pattern this fixture
  set intentionally introduces, rather than taking live human input
- Retrieval/clustering similarity uses local TF-IDF, not a hosted
  embedding model — same reasoning as `training_flow.py`

## What is NOT built here

- The Mission Mode dashboard UI (console trace only)
- A real LLM-based planner
- Live device write-back (out of scope by design, not an oversight)
- The v2 ML components (trained fingerprint classifier, fine-tuned
  retrieval embeddings, calibrated confidence model) — see the ML
  training plan document for when these become worthwhile
