"""
Mind — Goal Engine
GAACA v2.0

Parses natural-language objectives into structured Goals:
intent, hard constraints, implicit constraints, definition of done, and subgoals.
Detects critical ambiguities rather than making blind assumptions.
"""

from typing import List, Tuple
from agent_v2.core.state import Goal


class GoalEngine:
    def interpret_goal(self, raw_text: str) -> Goal:
        text_lower = raw_text.lower()

        # Intent detection
        intent = raw_text.strip()
        constraints: List[str] = []
        subgoals: List[str] = []

        # Extract constraints
        if "critical" in text_lower:
            constraints.append("focus_critical_findings_only")
        if "no report" in text_lower:
            constraints.append("suppress_final_report")
        if "offline" in text_lower or "air-gap" in text_lower:
            constraints.append("air_gapped_only")

        # Check for conversational greeting or identity query without heavy task
        words = [w.strip(".,!?:;'\"") for w in text_lower.split()]
        is_greeting = any(w in ("hi", "hello", "hey", "greetings", "howdy", "sup", "yo", "hola") for w in words)
        is_identity = any(phrase in text_lower for phrase in ("who are you", "what are you", "what can you do", "help me", "introduce yourself", "identity"))
        has_task_keyword = any(k in text_lower for k in ("audit", "compliance", "config", "research", "investigate", "test", "run", "analyze", "find", "check"))

        if (is_greeting or is_identity) and not has_task_keyword:
            subgoals.append("converse_with_operator")
            definition_of_done = "Conversational response delivered to operator."
            return Goal(
                raw_text=raw_text,
                intent=intent,
                constraints=constraints,
                definition_of_done=definition_of_done,
                subgoals=subgoals,
            )

        # Decompose initial subgoals based on semantic keywords
        if "audit" in text_lower or "compliance" in text_lower or "config" in text_lower:
            subgoals.extend([
                "discover_environment_configs",
                "identify_vendor_and_syntax",
                "evaluate_security_baselines",
                "resolve_unknown_patterns",
                "compile_audit_evidence",
            ])
        elif "research" in text_lower or "investigate" in text_lower:
            subgoals.extend([
                "formulate_research_questions",
                "search_authoritative_sources",
                "extract_evidence",
                "verify_source_authenticity",
                "synthesize_findings",
            ])
        else:
            subgoals.append("understand_problem_and_gather_evidence")

        definition_of_done = (
            "All subgoals satisfied with verified evidence in the World Model, "
            "with zero unaddressed contradictions or open critical questions."
        )

        return Goal(
            raw_text=raw_text,
            intent=intent,
            constraints=constraints,
            definition_of_done=definition_of_done,
            subgoals=subgoals,
        )

    def detect_ambiguity(self, goal: Goal) -> Tuple[bool, str]:
        """Detects whether goal requires clarification before spending budget."""
        raw = goal.raw_text.strip().lower()
        if raw in ("hi", "hey", "yo", "hello", "help", "who are you"):
            return False, ""
        if len(goal.raw_text.strip()) < 5:
            return True, "Goal description is too brief to formulate a plan."
        return False, ""
