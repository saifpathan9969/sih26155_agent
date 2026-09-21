"""
GAACA v2.0 — Interactive Autonomous Agent Terminal
SIH26155 — Direct Human-Agent Interaction Interface

Allows the operator to:
1. Issue any goal in natural language
2. Observe live cognitive loop cycles (perception -> world model -> hypotheses -> planning -> execution -> reflection)
3. Interactively approve/reject human-gated actions in real time
4. Query agent memory, world model beliefs, and learned patterns with slash commands (/status, /memory, /beliefs, /hypotheses)
"""

import sys
import os
from pathlib import Path
from typing import Optional

_INNER_ROOT = Path(__file__).resolve().parent
_PROJECT_ROOT = _INNER_ROOT.parent
sys.path.insert(0, str(_INNER_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT))

from agent_v2.core.agent import AutonomousAgent
from agent_v2.core.state import ApprovalRequest, TerminalState


def interactive_approval_callback(req: ApprovalRequest) -> bool:
    """Prompts operator in terminal when a safety policy requires human authorization."""
    print("\n" + "!" * 70)
    print("  [HUMAN APPROVAL REQUIRED BY SAFETY POLICY]")
    print(f"  Action:    {req.action}")
    print(f"  Risk:      {req.risk_level}")
    print(f"  Rationale: {req.rationale}")
    print(f"  Input:     {req.input_data}")
    print("!" * 70)
    while True:
        choice = input("  Authorize this action? [y/n/details]: ").strip().lower()
        if choice in ("y", "yes"):
            print("  -> Authorized by operator.")
            return True
        elif choice in ("n", "no"):
            print("  -> Rejected by operator.")
            return False
        elif choice in ("details", "d"):
            print(f"  Raw payload: {req.input_data}")
        else:
            print("  Please answer 'y' to approve or 'n' to reject.")


def print_help():
    print("""
Available Commands & Capabilities:
  • Any natural language goal, e.g.:
      - "Audit project configuration files for CIS compliance"
      - "Diagnose authentication failures and test SSH port hypotheses"
      - "Load dataset cis_rules.yaml and analyze rules statistics"
      - "Generate markdown audit report summarizing compliance status"
      - "Inspect repository and show git status"
      - "Run sandboxed python code to verify cryptographic algorithms"

  • Built-in Interactive Commands:
      /status       - View agent runtime status & subsystem health
      /memory       - View working, episodic, and semantic memory state
      /beliefs      - View current verified & inferred epistemic beliefs
      /hypotheses   - View active hypotheses and Bayesian probabilities
      /patterns     - View learned procedural knowledge patterns
      /clear        - Clear working memory and reset cognitive focus
      /help         - Show this command reference
      /exit, /quit  - Disengage agent and exit
""")


def start_interactive_session():
    print("=" * 76)
    print("  GAACA v2.0 — AUTONOMOUS COGNITIVE AGENT INTERACTIVE SHELL")
    print("  True Autonomous Agent System | Type /help for guidance, /exit to quit")
    print("=" * 76)

    agent = AutonomousAgent(
        project_root=_PROJECT_ROOT,
        scratch_dir=_INNER_ROOT / "scratch",
        approval_callback=interactive_approval_callback,
        trace_to_console=True,
        enable_security=True,
    )
    agent.register_all_capabilities()

    print("\n[+] All internal capabilities and cognitive engines initialized.")
    print("[+] Safety boundary policy: Active (Fail-closed)")
    print("[+] Type a goal or task to dispatch to the agent.\n")

    while True:
        try:
            prompt = input("GAACA [idle] > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[!] Exiting interactive session.")
            break

        if not prompt:
            continue

        cmd = prompt.lower()
        if cmd in ("/exit", "/quit", "exit", "quit"):
            print("[+] Disengaging agent. Session closed.")
            break

        if cmd in ("/help", "help"):
            print_help()
            continue

        if cmd in ("/status", "status"):
            info = agent.inspect()
            print("\n--- Agent Health & System Introspection ---")
            print(f"  Runtime Status:               {agent.status()}")
            print(f"  Registered Capabilities:      {info['registry']['capabilities']}")
            print(f"  Registered Implementations:   {info['registry']['implementations']}")
            print(f"  Episodic Memory Episodes:     {info['memory']['episodic_episodes']}")
            print(f"  Semantic Domain Concepts:     {info['memory']['semantic_concepts']}")
            print(f"  Procedural Learned Patterns:  {info['memory']['procedural_patterns']}")
            tasks = info.get('tasks', {})
            print(f"  Task Registry Total:          {tasks.get('total_tasks', 0)}")
            if tasks.get('by_status'):
                for s, c in tasks['by_status'].items():
                    if c > 0:
                        print(f"    └─ {s}: {c}")
            print("-------------------------------------------\n")
            continue

        if cmd in ("/memory", "memory"):
            print("\n--- Working & Episodic Memory Snapshot ---")
            wm = agent.working_memory.summary()
            print(f"  Attention Focus:    {wm['focus']['current_objective'] or '(None)'}")
            print(f"  Actions Logged:     {wm['actions']} (Failures: {wm['failures']})")
            print(f"  Recent Notes:       {len(agent.working_memory.scratch_notes)}")
            for note in agent.working_memory.get_recent_notes(3):
                print(f"    • [{note.source}] {note.content[:80]}")
            print(f"  Total Episodes:     {agent.episodic_memory.total_episodes()}")
            recent_eps = agent.episodic_memory.last_n(3)
            for ep in recent_eps:
                status_str = "OK" if ep.success else "FAIL"
                print(f"    • Run {ep.run_id} | Cycle {ep.cycle_index}: {ep.action_taken} [{status_str}]")
            print("-------------------------------------------\n")
            continue

        if cmd in ("/beliefs", "beliefs"):
            print("\n--- World Model Epistemic Beliefs ---")
            beliefs = agent.executive.world_model if hasattr(agent.executive, "world_model") else None
            # Extract from executive
            all_b = agent.executive.run_id if hasattr(agent.executive, "run_id") else None
            # Retrieve beliefs from state or store
            facts = agent.semantic_memory.all_facts()
            print(f"  Persistent Semantic Facts: {len(facts)}")
            for f in facts[:10]:
                print(f"    • {f.subject} = {f.value} [{f.source}, conf={f.confidence}]")
            print("-------------------------------------\n")
            continue

        if cmd in ("/hypotheses", "hypotheses"):
            print("\n--- Active Diagnostic Hypotheses ---")
            engine = agent.executive.hypothesis_engine
            open_h = engine.open_hypotheses()
            all_h = list(engine.hypotheses.values())
            print(f"  Total Hypotheses: {len(all_h)} (Open: {len(open_h)})")
            for h in all_h:
                print(f"    • [{h.status}] \"{h.statement}\" | Posterior: {h.posterior:.2f} (Prior: {h.prior:.2f})")
                if h.supporting:
                    print(f"        Supporting Evidence IDs: {h.supporting}")
                if h.refuting:
                    print(f"        Refuting Evidence IDs:   {h.refuting}")
            print("------------------------------------\n")
            continue

        if cmd in ("/patterns", "patterns"):
            print("\n--- Learned Procedural Knowledge Patterns ---")
            patterns = agent.learning_engine.all_patterns()
            print(f"  Total Knowledge Patterns: {len(patterns)}")
            for p in patterns:
                citable_tag = "CITABLE" if p.is_citable else ("RETIRED" if p.retired else "UNVALIDATED")
                print(f"    • [{citable_tag}] {p.description}")
                print(f"        Type: {p.pattern_type} | Validation: {p.validation_method.value} | Contradictions: {p.contradiction_count}")
            print("----------------------------------------------\n")
            continue

        if cmd in ("/clear", "clear"):
            agent.working_memory.clear()
            print("[+] Working memory and attention focus cleared.\n")
            continue

        # Execute as goal
        print(f"\n[*] Engaging Cognitive Architecture on Goal: \"{prompt}\"")
        print("[-] Running cognitive cycles...\n")
        try:
            state = agent.run(prompt, max_cycles=10)

            # Surface conversational replies or direct agent outputs
            for act in state.completed_actions:
                if act.implementation == "converse":
                    print("\n" + "*" * 60)
                    print(f"Agent: {act.observation}")
                    print("*" * 60)
                elif act.implementation == "ask_human":
                    print("\n" + "*" * 60)
                    print(f"Agent Inquiry: {act.observation}")
                    print("*" * 60)

            print("\n" + "=" * 70)
            print(f"  EXECUTION OUTCOME: {state.terminal_state.value}")
            print(f"  Justification:     {state.terminal_justification}")
            print(f"  Completed Actions: {len(state.completed_actions)}")
            if state.failed_actions:
                print(f"  Diagnosed Failures: {len(state.failed_actions)}")
                for f in state.failed_actions:
                    print(f"    - Failed '{f.action}' ({f.failure_class}): {f.diagnosis}")
            print("=" * 70 + "\n")
        except Exception as ex:
            print(f"\n[!] Error during cognitive execution: {ex}\n")


if __name__ == "__main__":
    start_interactive_session()
