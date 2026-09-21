"""
Capabilities — Communication
GAACA v2.0

Enables the agent to ask questions to the operator or generate user-facing reports.
"""

from typing import Any, Dict
from agent_v2.capabilities.base import ImplementationSpec, Observation, ExecContext, CostModel
from agent_v2.capabilities.registry import CapabilityRegistry


def handle_ask_human(params: Dict[str, Any], context: ExecContext) -> Observation:
    question = params.get("question", "")
    return Observation(
        ok=True,
        output=f"[OPERATOR_INPUT_REQUESTED] {question}",
        metadata={"question": question},
    )


def handle_converse(params: Dict[str, Any], context: ExecContext) -> Observation:
    message = params.get("message", "").strip()
    msg_lower = message.lower()

    if any(w in msg_lower for w in ("hi", "hello", "hey", "greetings", "good morning", "good afternoon", "howdy")):
        reply = "Hello! I am GAACA v2.0, your autonomous cognitive agent. I am standing by to help with security audits, compliance evaluations, sandboxed code execution, data analysis, or investigating technical problems. What would you like to achieve?"
    elif any(phrase in msg_lower for phrase in ("who are you", "what are you", "identity")):
        reply = "I am GAACA v2.0 (General Autonomous Agent Cognitive Architecture). Unlike simple ReAct tool wrappers, I operate an internal 10-step cognitive loop with dynamic hierarchical planning, scientific hypothesis testing, deterministic rule-engine governance, and multi-tiered memory."
    elif any(phrase in msg_lower for phrase in ("what can you do", "capabilities", "features", "help")):
        reply = "My internal capabilities include: 1) Deterministic CIS network security auditing and remediation, 2) Sandboxed Python execution and test running, 3) Structured dataset analysis (CSV/JSON/YAML), 4) Automated Markdown report generation, 5) Web and document research with SSRF defense, 6) Scientific problem solving with Bayesian hypothesis tracking, 7) Multi-tiered memory (Working, Episodic, Semantic, Procedural, SQLite)."
    elif any(w in msg_lower for w in ("thank", "thanks", "great", "awesome")):
        reply = "You're welcome! Let me know whenever you'd like to run an audit, investigate a system, or analyze data."
    else:
        reply = f"Acknowledged: '{message}'. How would you like me to assist you?"

    return Observation(ok=True, output=reply, metadata={"reply": reply})


def register_communication_capabilities(registry: CapabilityRegistry):
    registry.register_implementation(ImplementationSpec(
        name="ask_human",
        description="Asks a clarifying question to the human operator",
        input_schema={"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]},
        output_schema={"type": "string"},
        autonomy_action="ask_human",
        risk="NONE",
        cost=CostModel(estimated_seconds=0.1),
        handler=handle_ask_human,
    ))

    registry.register_implementation(ImplementationSpec(
        name="converse",
        description="Provides conversational responses and identity/capability explanations",
        input_schema={"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]},
        output_schema={"type": "string"},
        autonomy_action="converse",
        risk="NONE",
        cost=CostModel(estimated_seconds=0.1),
        handler=handle_converse,
    ))
