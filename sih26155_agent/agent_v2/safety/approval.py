"""
Safety & Governance — Human Approval Manager
GAACA v2.0

Manages human approval gates. When a high-stakes or permanently gated action
is decided, this subsystem pauses execution, emits an ApprovalRequest,
and resumes upon authorized human confirmation or rejection.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Callable, Dict, Optional
import uuid

from agent_v2.core.state import ApprovalRequest


class ApprovalManager:
    def __init__(self, callback: Optional[Callable[[ApprovalRequest], bool]] = None):
        """
        `callback`: Function invoked when an approval is needed.
        Returns True if approved, False if rejected.
        In an interactive/API deployment, this pauses the run until an endpoint is called.
        """
        self.callback = callback
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.history: Dict[str, ApprovalRequest] = {}

    def request_approval(self, action: str, input_data: dict,
                         rationale: str, risk_level: str = "HIGH") -> ApprovalRequest:
        req_id = f"appr_{uuid.uuid4().hex[:8]}"
        req = ApprovalRequest(
            id=req_id,
            action=action,
            input_data=input_data,
            rationale=rationale,
            risk_level=risk_level,
            status="PENDING",
        )
        self.pending_requests[req_id] = req
        return req

    def resolve(self, req_id: str, approved: bool) -> Optional[ApprovalRequest]:
        req = self.pending_requests.pop(req_id, None)
        if not req:
            return None
        req.status = "APPROVED" if approved else "REJECTED"
        req.resolved_at = datetime.now(timezone.utc)
        self.history[req_id] = req
        return req
