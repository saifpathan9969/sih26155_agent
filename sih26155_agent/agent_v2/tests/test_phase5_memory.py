"""
Tests — Phase 5 Memory Architecture Verification Suite
GAACA v2.0

Verifies all memory subsystems:
- Working Memory: active scratchpad, attention focus, counters
- Episodic Memory: chronological trace, surprise detection, autobiographical recall
- Semantic Memory: vendor ontologies, long-term facts, concept relations
- Procedural Memory: knowledge patterns, applicability conditions, citable filters
- MemoryStore: durable SQLite persistence across runs
"""

from pathlib import Path
import sys
import tempfile

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "agent_v2"))

from agent_v2.memory.working import WorkingMemory
from agent_v2.memory.episodic import EpisodicMemory, Episode
from agent_v2.memory.semantic import SemanticMemory
from agent_v2.memory.procedural import ProceduralMemory
from agent_v2.memory.store import MemoryStore
from agent_v2.mind.learning import LearningEngine, ValidationMethod


def test_working_memory():
    wm = WorkingMemory()
    wm.set_focus("Audit FortiGate admin access")
    assert wm.focus.current_objective == "Audit FortiGate admin access"

    wm.record_action("web_search", "Search results found", success=True)
    wm.record_action("web_fetch", "401 Unauthorized", success=False)

    summary = wm.summary()
    assert summary["actions"] == 2
    assert summary["failures"] == 1
    assert summary["focus"]["current_objective"] == "Audit FortiGate admin access"

    wm.add_note("FortiGate benchmark requires account login", source="web_fetch")
    assert len(wm.get_recent_notes()) == 1

    wm.tick_cycle()
    assert wm.cycle_count == 1
    assert wm.focus.current_objective == "Audit FortiGate admin access"


def test_episodic_memory_and_surprise():
    em = EpisodicMemory()
    ep1 = em.record(
        run_id="run_101",
        cycle_index=1,
        objective="Inspect device configs",
        action_taken="discover_configs",
        parameters={"source": "tests"},
        observation_summary="Found 5 configs",
        success=True,
    )
    assert ep1.surprise is False

    # Episode with surprise: unpredicted observation
    ep2 = em.record(
        run_id="run_101",
        cycle_index=2,
        objective="Fetch vendor benchmark",
        action_taken="web_fetch",
        parameters={"url": "https://cisecurity.org/auth"},
        observation_summary="HTTP 401 Unauthorized: login required",
        success=False,
        surprise=True,
        surprise_description="Expected public document; hit authentication paywall.",
    )
    assert ep2.surprise is True
    assert len(em.get_surprises()) == 1

    # Autobiographical recall
    episodes_101 = em.get_by_run(run_id="run_101")
    assert len(episodes_101) == 2
    failed_episodes = em.get_failures()
    assert len(failed_episodes) == 1
    assert failed_episodes[0].action_taken == "web_fetch"


def test_semantic_memory_and_ontology():
    sm = SemanticMemory()
    # Pre-seeded vendor concepts
    cisco = sm.get_concept("vendor_cisco_ios")
    assert cisco is not None
    assert cisco.name == "Cisco IOS"

    fortinet = sm.get_concept("vendor_fortinet_fortios")
    assert fortinet is not None
    assert "FortiGate" in fortinet.description

    # Add custom fact
    fact = sm.add_fact(
        subject="device:cisco_core_01.ssh_version",
        predicate="is_hardened",
        value=True,
        source="rule_engine",
        confidence=1.0,
    )
    assert fact.id.startswith("sf_")
    facts = sm.get_facts_about("device:cisco_core_01.ssh_version")
    assert len(facts) == 1
    assert facts[0].value is True


def test_procedural_memory_and_citable_filter():
    learning = LearningEngine()
    pm = ProceduralMemory(learning)

    # Store pattern
    pat = pm.store_pattern(
        pattern_type="workflow",
        description="Standard CIS network audit procedure",
        content={"steps": ["discover", "parse", "evaluate", "remediate"]},
        validation_method=ValidationMethod.DETERMINISTIC,
        applicability_conditions=["cis_benchmark", "network_devices"],
        source_run_id="run_100",
    )
    assert pat.is_citable is True

    # Recall by keywords
    recalled = pm.recall(context_keywords=["cis_benchmark"])
    assert len(recalled) == 1
    assert recalled[0].id == pat.id

    # Record uses
    pm.record_use(pat.id, succeeded=True)
    assert pat.success_rate == 1.0

    # Accumulate contradictions -> retirement
    pm.record_contradiction(pat.id)
    pm.record_contradiction(pat.id)
    pm.record_contradiction(pat.id)
    assert pat.retired is True
    assert len(pm.recall_citable()) == 0  # Retired patterns are never citable


def test_sqlite_memory_store_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test_memory.db"
        store = MemoryStore(db_file)
        try:
            # 1. Save and reload episode
            ep = Episode(
                episode_id=1,
                run_id="run_persisted_01",
                cycle_index=1,
                objective="Test persistence",
                action_taken="run_python",
                parameters={"code": "x=1"},
                observation_summary="OK",
                success=True,
                surprise=False,
            )
            store.save_episode(ep.to_dict())
            loaded_eps = store.load_episodes(run_id="run_persisted_01")
            assert len(loaded_eps) == 1
            assert loaded_eps[0]["action_taken"] == "run_python"

            # 2. Save and reload concept
            sm = SemanticMemory()
            c = sm.get_concept("vendor_cisco_ios")
            assert c is not None
            store.save_concept(c.to_dict())
            loaded_concepts = store.load_concepts(category="vendor")
            assert len(loaded_concepts) >= 1
            assert loaded_concepts[0]["name"] == "Cisco IOS"

            # 3. Save and reload fact
            fact = sm.add_fact("net.gw", "is_active", True, "rule_engine")
            store.save_fact(fact.to_dict())
            loaded_facts = store.load_facts(subject="net.gw")
            assert len(loaded_facts) == 1
            assert "true" in str(loaded_facts[0]["value"]).lower()
        finally:
            store.close()


if __name__ == "__main__":
    print("Running Phase 5 Memory Architecture Verification Suite...")
    test_working_memory()
    print("[PASS] Working memory passed")
    test_episodic_memory_and_surprise()
    print("[PASS] Episodic memory & surprise detection passed")
    test_semantic_memory_and_ontology()
    print("[PASS] Semantic memory & vendor ontology passed")
    test_procedural_memory_and_citable_filter()
    print("[PASS] Procedural memory & citable filter passed")
    test_sqlite_memory_store_persistence()
    print("[PASS] SQLite durable memory store passed")
    print("\nALL PHASE 5 MEMORY ARCHITECTURE TESTS PASSED SUCCESSFULLY.")
