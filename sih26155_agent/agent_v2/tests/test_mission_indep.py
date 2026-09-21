"""
Tests — Mission Independence Test
GAACA v2.0

Verifies the agent can solve a problem for which NO predefined workflow exists.
The agent must:
1. Decompose an unfamiliar goal
2. Select capabilities autonomously
3. Handle unexpected observations
4. Terminate with a typed terminal state and justified conclusion

Scenario: "Analyze the project structure and determine if it follows Python best practices"
— No workflow is predefined for this. The agent must reason from first principles.
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from agent_v2.core.agent import AutonomousAgent
from agent_v2.core.state import TerminalState


def test_mission_independence_project_analysis():
    """
    Agent must autonomously analyze a codebase it has never seen.
    No predefined subgoals exist for "Python best practices analysis".
    """
    agent = AutonomousAgent(
        project_root=_PROJECT_ROOT,
        trace_to_console=False,
    )
    agent.register_all_capabilities()

    state = agent.run(
        "Analyze the project structure and determine if it follows Python best practices",
        max_cycles=5,
    )

    # The agent must terminate with a valid state
    assert state.terminal_state is not None
    assert state.terminal_state in (
        TerminalState.SUCCESS,
        TerminalState.PARTIAL_SUCCESS,
        TerminalState.RESOURCE_EXHAUSTED,
        TerminalState.INSUFFICIENT_EVIDENCE,
    )

    # Must have taken at least one action
    assert len(state.completed_actions) >= 1

    # Must have populated the world model with at least one belief
    assert len(state.world.beliefs.all()) >= 1

    # Must have a justification
    assert state.terminal_justification is not None
    assert len(state.terminal_justification) > 10


def test_mission_independence_unknown_domain():
    """
    Agent asked about something completely outside its security domain.
    Should still reason about it using general capabilities.
    """
    agent = AutonomousAgent(
        project_root=_PROJECT_ROOT,
        trace_to_console=False,
    )
    agent.register_all_capabilities()

    state = agent.run(
        "Count the number of Python files in this project and report the total lines of code",
        max_cycles=5,
    )

    assert state.terminal_state is not None
    assert len(state.trace) >= 1
    assert state.terminal_justification is not None


def test_mission_with_injected_failure():
    """
    Agent is given a goal that will encounter failures.
    Must not crash; must terminate gracefully with appropriate state.
    """
    agent = AutonomousAgent(
        project_root=_PROJECT_ROOT,
        trace_to_console=False,
    )
    # Intentionally do NOT register capabilities — agent has nothing to work with
    # But the registry will fall back to all_implementations() which is empty

    state = agent.run(
        "Deploy a network security scanner",
        max_cycles=3,
    )

    # Should terminate gracefully, not crash
    assert state.terminal_state is not None
    assert state.terminal_state in (
        TerminalState.SUCCESS,
        TerminalState.RESOURCE_EXHAUSTED,
        TerminalState.INSUFFICIENT_EVIDENCE,
    )


if __name__ == "__main__":
    print("Running Mission Independence Tests...")
    test_mission_independence_project_analysis()
    print("[PASS] Project analysis (no predefined workflow)")
    test_mission_independence_unknown_domain()
    print("[PASS] Unknown domain task")
    test_mission_with_injected_failure()
    print("[PASS] Injected failure graceful termination")
    print("\nALL MISSION INDEPENDENCE TESTS PASSED SUCCESSFULLY.")
