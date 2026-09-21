"""
Environment — Web Environment
GAACA v2.0

Provides HTTP interaction with SSRF protection.
All fetched content is tagged as untrusted.
DNS resolution is blocked for private/loopback ranges.
"""

from __future__ import annotations
from typing import Any, Dict, Optional

from agent_v2.environment.environment import Environment
from agent_v2.capabilities.web import is_ssrf_safe


class WebEnvironment(Environment):
    """Represents the web/internet environment with SSRF boundaries."""

    def __init__(self, allow_web: bool = True):
        self.allow_web = allow_web
        self._request_count: int = 0
        self._blocked_count: int = 0

    def inspect(self) -> Dict[str, Any]:
        return {
            "web_access": self.allow_web,
            "requests_made": self._request_count,
            "requests_blocked": self._blocked_count,
        }

    def is_url_safe(self, url: str) -> bool:
        """Checks if a URL passes SSRF protection."""
        return is_ssrf_safe(url)

    def record_request(self, url: str, blocked: bool = False):
        """Tracks web requests for budget and audit purposes."""
        self._request_count += 1
        if blocked:
            self._blocked_count += 1

    def disable(self):
        """Disables web access (for air-gapped mode)."""
        self.allow_web = False

    def enable(self):
        self.allow_web = True
