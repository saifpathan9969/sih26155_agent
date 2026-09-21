"""
Core — High-Level Agent Wrapper
GAACA v2.0

The top-level API for creating, configuring, and running the autonomous agent.
Assembles all subsystems into a single coherent agent instance.

Usage:
    agent = AutonomousAgent(project_root=Path("."))
    agent.register_all_capabilities()
    result = agent.run("Audit network device configurations for CIS compliance")
    print(result.terminal_state)
"""

from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional

from agent_v2.core.executive import AgentExecutive
from agent_v2.core.runtime import AgentRuntime
from agent_v2.core.state import AgentState, TerminalState
from agent_v2.capabilities.registry import CapabilityRegistry
from agent_v2.capabilities.web import register_web_capabilities
from agent_v2.capabilities.filesystem import register_filesystem_capabilities
from agent_v2.capabilities.coding import register_coding_capabilities
from agent_v2.capabilities.shell import register_shell_capabilities
from agent_v2.capabilities.git import register_git_capabilities
from agent_v2.capabilities.documents import register_document_capabilities
from agent_v2.capabilities.data import register_data_capabilities
from agent_v2.capabilities.communication import register_communication_capabilities
from agent_v2.core.task_registry import register_task_capabilities, GLOBAL_TASK_REGISTRY
from agent_v2.memory.working import WorkingMemory
from agent_v2.memory.episodic import EpisodicMemory
from agent_v2.memory.semantic import SemanticMemory
from agent_v2.memory.procedural import ProceduralMemory
from agent_v2.mind.learning import LearningEngine


class AutonomousAgent:
    """
    The complete autonomous agent — assembles all cognitive, capability,
    memory, and safety subsystems into a single runnable system.
    """

    def __init__(
        self,
        project_root: Path,
        scratch_dir: Optional[Path] = None,
        approval_callback: Optional[Callable] = None,
        trace_to_console: bool = True,
        enable_security: bool = False,
    ):
        self.project_root = project_root.resolve()
        self.scratch_dir = (scratch_dir or self.project_root / "agent_v2" / "scratch").resolve()
        self.scratch_dir.mkdir(parents=True, exist_ok=True)

        # Registry
        self.registry = CapabilityRegistry()

        # Memory subsystems
        self.working_memory = WorkingMemory()
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.learning_engine = LearningEngine()
        self.procedural_memory = ProceduralMemory(self.learning_engine)

        # Task lifecycle registry (claw-code pattern)
        self.task_registry = GLOBAL_TASK_REGISTRY

        # Runtime
        self.runtime = AgentRuntime(
            project_root=self.project_root,
            scratch_dir=self.scratch_dir,
        )

        # Executive
        self.executive = AgentExecutive(
            project_root=self.project_root,
            scratch_dir=self.scratch_dir,
            registry=self.registry,
            approval_callback=approval_callback,
            trace_to_console=trace_to_console,
        )

        # Configuration
        self._enable_security = enable_security
        self._capabilities_registered = False

    def register_all_capabilities(self):
        """Registers all built-in capability implementations."""
        register_web_capabilities(self.registry)
        register_filesystem_capabilities(self.registry)
        register_coding_capabilities(self.registry)
        register_shell_capabilities(self.registry)
        register_git_capabilities(self.registry)
        register_document_capabilities(self.registry)
        register_data_capabilities(self.registry)
        register_communication_capabilities(self.registry)
        register_task_capabilities(self.registry)

        if self._enable_security:
            try:
                from agent_v2.capabilities.security import register_security_capabilities
                register_security_capabilities(self.registry)
            except ImportError:
                pass  # V1 tools not available

        from agent_v2.capabilities.base import CapabilitySpec
        self.registry.register_capability(CapabilitySpec(
            name="FILESYSTEM",
            description="Local file and directory access",
            implementations=["read_file", "list_dir", "search_files", "write_scratch", "write_file"],
        ))
        self.registry.register_capability(CapabilitySpec(
            name="WEB_RESEARCH",
            description="External documentation search and retrieval",
            implementations=["web_search", "web_fetch", "synthesize_research"],
        ))
        self.registry.register_capability(CapabilitySpec(
            name="SECURITY",
            description="Deterministic CIS compliance auditing and remediation",
            implementations=["discover_configs", "parse_config", "evaluate_compliance", "select_remediation", "run_mission"],
        ))
        self.registry.register_capability(CapabilitySpec(
            name="CODING",
            description="Sandboxed Python execution and test suites",
            implementations=["run_python", "run_tests"],
        ))
        self.registry.register_capability(CapabilitySpec(
            name="SHELL",
            description="Controlled shell command execution",
            implementations=["run_shell"],
        ))
        self.registry.register_capability(CapabilitySpec(
            name="GIT",
            description="Git repository state and diffs",
            implementations=["git_status", "git_diff", "git_commit"],
        ))
        self.registry.register_capability(CapabilitySpec(
            name="DOCUMENTS",
            description="Structured report generation",
            implementations=["generate_markdown", "generate_pdf"],
        ))
        self.registry.register_capability(CapabilitySpec(
            name="DATA",
            description="Dataset analysis and statistics",
            implementations=["load_dataset", "analyze_data", "summarize_stats"],
        ))
        self.registry.register_capability(CapabilitySpec(
            name="COMMUNICATION",
            description="Operator interaction and sign-offs",
            implementations=["converse", "ask_human", "request_approval"],
        ))
        self.registry.register_capability(CapabilitySpec(
            name="TASKS",
            description="Sub-agent task lifecycle and tracking (claw-code pattern)",
            implementations=["create_task", "list_tasks", "stop_task"],
        ))
        self.registry.register_capability(CapabilitySpec(
            name="ENVIRONMENT",
            description="Environment inspection and discovery",
            implementations=["inspect_project", "discover_configs", "list_dir"],
        ))

        self._capabilities_registered = True

    def run(self, goal: str, max_cycles: int = 15) -> AgentState:
        """
        Runs the autonomous agent to completion on the given goal.

        Returns the final AgentState with:
        - terminal_state: Why the agent stopped
        - terminal_justification: Human-readable explanation
        - trace: Full cognitive cycle audit trail
        - world: Updated world model with all discovered beliefs
        """
        if not self._capabilities_registered:
            self.register_all_capabilities()

        self.runtime.start()
        self.working_memory.clear()

        try:
            state = self.executive.run(goal, max_cycles=max_cycles)

            # Record episodes to episodic memory
            for action in state.completed_actions:
                self.episodic_memory.record(
                    run_id=state.run_id,
                    cycle_index=action.cycle,
                    objective=state.goal.intent,
                    action_taken=action.implementation,
                    parameters=action.parameters,
                    observation_summary=str(action.observation)[:300],
                    success=action.ok,
                )

            # Sync learned patterns from executive to agent procedural memory
            for pat in self.executive.learning_engine.all_patterns():
                if pat.id not in self.learning_engine._patterns:
                    self.learning_engine._patterns[pat.id] = pat

            # Save state
            self.runtime.save_state(state)

            # Export trace
            trace_path = self.runtime.export_trace(state)

            return state

        finally:
            self.runtime.stop()

    def inspect(self) -> dict:
        """Returns the current state of all subsystems."""
        return {
            "runtime": self.runtime.status(),
            "registry": {
                "capabilities": len(self.registry.all_capabilities()),
                "implementations": len(self.registry.all_implementations()),
            },
            "memory": {
                "working": self.working_memory.summary(),
                "episodic_episodes": self.episodic_memory.total_episodes(),
                "semantic_concepts": len(self.semantic_memory._concepts),
                "procedural_patterns": len(self.procedural_memory.all_patterns()),
            },
            "tasks": self.task_registry.summary(),
        }

    def status(self) -> str:
        """Returns a human-readable status string."""
        rt = self.runtime.status()
        if rt["is_running"]:
            return "RUNNING"
        elif rt["is_paused"]:
            return f"PAUSED: {rt['pause_reason']}"
        elif rt["ended_at"]:
            return "COMPLETED"
        else:
            return "READY"
