# SIH26155 — Autonomous Security & General Cognitive Agent

This repository contains two complete architectural implementations:
1. **`agent_v2/` — GAACA v2.0 (General Autonomous Agent Cognitive Architecture)**: A full, standalone, true autonomous agent cognitive architecture where capabilities, multi-tiered memory, scientific hypothesis testing, deterministic rule engine governance, and self-correction are native internal systems rather than a simple ReAct tool framework.
2. **`agent/` — v1 Reference Implementation**: The baseline deterministic compliance orchestrator with reflection clustering for network device CIS benchmarks.

---

## GAACA v2.0 — True Autonomous Cognitive Agent

### 1. Architectural Philosophy
The agent **is the system**. Tools, memory, reasoning, planning, execution, verification, learning, and environment interaction are internal capabilities of that system:

```text
Goal -> Perception -> World Model -> Reasoning -> Planning -> Decision
     -> Action -> Observation -> Verification -> Reflection -> Learning -> Replanning
```

### 2. Core Subsystems in `agent_v2/`

- **`agent_v2/core/`**:
  - `agent.py`: `AutonomousAgent` top-level orchestrator.
  - `executive.py`: `AgentExecutive` 10-step cognitive cycle loop.
  - `state.py`: Rich persistent state (`AgentState`, `Goal`, `ActionRecord`, `FailureRecord`, `CycleRecord`, `TerminalState`).
  - `runtime.py`: Safe execution runtime with state snapshotting and trace export.
- **`agent_v2/mind/`**:
  - `goal_engine.py`: Intent extraction and recursive decomposition.
  - `planning.py`: Hierarchical planning with `expected_observation` prediction before action.
  - `decision.py`: Utility-driven decision engine with strict failed-strategy exclusion (bare retries permanently banned).
  - `hypothesis.py`: Scientific problem solving (`ActionSketch`, Bayesian prior/posterior tracking, status progression).
  - `correction.py`: Diagnosis-first self-correction (identifies root cause across 7 failure classes).
  - `reasoning.py`: Deductive, abductive, and causal inference chains with belief revision.
  - `learning.py`: `KnowledgePattern` extraction with validation methods and contradiction-based retirement.
  - `world_model.py` & `beliefs.py`: Epistemic belief store (`KNOWN`, `INFERRED`, `VERIFIED`, `CONTRADICTED`, `HUMAN_CONFIRMED`).
  - `verification.py`: Mechanical verification and contradiction precedence (deterministic rule engine has absolute authority).
- **`agent_v2/capabilities/`**:
  - `registry.py`: Hard safety-checked capability registry.
  - `filesystem.py`, `coding.py`, `shell.py`, `git.py`, `documents.py`, `data.py`, `web.py`, `communication.py`.
  - `security.py`: Domain capability wrapping deterministic CIS compliance auditing, vendor parsing, and remediation lookup.
- **`agent_v2/memory/`**:
  - `working.py`: Scratchpad with attention focus and cycle counters.
  - `episodic.py`: Chronological trace with unpredicted outcome / surprise detection.
  - `semantic.py`: Long-term fact base and preloaded vendor ontology.
  - `procedural.py`: Indexed knowledge patterns with citable filtering.
  - `store.py`: Durable SQLite persistence across runs.
- **`agent_v2/safety/`**:
  - `policy.py`: Inviolable `AUTONOMY_TABLE` (`AUTONOMOUS`, `AUTONOMOUS_ABOVE_THRESHOLD`, `REQUIRES_HUMAN`, `NEVER_AUTONOMOUS`, `OUT_OF_SCOPE`).
  - `budgets.py`: `ResourceLedger` (cycles, network, risk caps).
  - `sandbox.py`: Scratch directory boundary isolation and path containment.
  - `approval.py`: `ApprovalManager` for human-in-the-loop gates.

---

## Running the Verification Test Suites

All test suites verify cognitive layers, safety gates, and capabilities deterministically:

```bash
# Run all Phase verification suites
python -m agent_v2.tests.test_phase0               # Foundational runtime & epistemic authority
python -m agent_v2.tests.test_phase1               # Dynamic planning & expected_observation
python -m agent_v2.tests.test_phase2               # Hypotheses, self-correction, & pattern retirement
python -m agent_v2.tests.test_phase3_capabilities  # Coding, shell safety, git, docs, data, comms
python -m agent_v2.tests.test_phase4_security      # CIS rule engine integration & verdict invariance
python -m agent_v2.tests.test_phase5_memory        # Working, episodic, semantic, procedural, SQLite
python -m agent_v2.tests.test_safety               # Safety trap suite (adversarial policy checks)
python -m agent_v2.tests.test_mission_indep        # Mission independence (general goals)
```

---

## Running the GAACA v2.0 Demo

```bash
python -m agent_v2.demo
```

Runs a 2-scenario cognitive demonstration:
1. **Scenario 1**: General Autonomous Investigation & Scientific Reasoning (hypotheses, Bayesian evidence updates, self-correction).
2. **Scenario 2**: Specialized Security Domain Audit & Markdown Report Generation (deterministic CIS compliance evaluation, remediation selection, artifact creation).
3. **Memory & Introspection**: Inspects working memory, episodic recall, semantic ontology, and learned procedural patterns.
