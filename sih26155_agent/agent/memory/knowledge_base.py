"""
Long-term memory = the same VendorKnowledgeBase already built and proven in
training_flow.py. Not re-implemented here — re-exported, so the agent and
the single-device training flow share one knowledge base rather than two
drifting copies.
"""

from training_flow import (  # noqa: F401
    VendorKnowledgeBase,
    KnowledgeBaseEntry,
    CandidateMapping,
    UnknownCommandDetection,
    validate_mapping,
    resolve_expected_type,
    SIMILARITY_CONFIDENCE_THRESHOLD,
)
