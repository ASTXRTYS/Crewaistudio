import time
from typing import Any, Dict, List, Optional

import crewai
from crewai import Agent, Crew, Task
from packaging import version

CREWAI_VERSION = version.parse(crewai.__version__)


class AurenAgent(Agent):
    """Compatibility wrapper for CrewAI agents."""

    def __init__(self, **kwargs):
        # Version-specific parameter handling
        if CREWAI_VERSION >= version.parse("0.30.0"):
            # New API doesn't support memory parameter
            kwargs.pop("memory", None)
            kwargs["memory_config"] = {"provider": "local", "storage": "/auren/data/agent_memory"}

        # Handle tools conversion
        if "tools" in kwargs:
            kwargs["tools"] = self._ensure_compatible_tools(kwargs["tools"])

        super().__init__(**kwargs)

    @staticmethod
    def _ensure_compatible_tools(tools: List[Any]) -> List[Any]:
        """Convert tools to compatible format."""
        from crewai.tools import BaseTool

        compatible_tools = []
        for tool in tools:
            if hasattr(tool, "__call__") and not isinstance(tool, BaseTool):
                # Wrap function tools
                from crewai.tools import tool

                compatible_tools.append(tool(tool))
            else:
                compatible_tools.append(tool)

        return compatible_tools


class AurenCircuitBreaker:
    """Circuit breaker pattern for external API calls."""

    def __init__(self, failure_threshold=3, recovery_timeout=300):
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time > self.recovery_timeout
            ):
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise e
