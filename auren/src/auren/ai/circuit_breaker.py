"""
Circuit breaker implementation for LLM providers.

Provides fault tolerance for LLM API calls with configurable
failure thresholds and recovery mechanisms.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, Dict
import asyncio
import logging

logger = logging.getLogger(__name__)


class CircuitBreakerState:
    """States for the circuit breaker."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls are rejected
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    success_threshold: int = 2
    failure_window: int = 300  # seconds to look back for failures
    recovery_timeout_overrides: Dict[str, float] = field(default_factory=dict)
    
    def get_recovery_timeout(self, failure_type: str) -> float:
        """Get recovery timeout for specific failure type."""
        return self.recovery_timeout_overrides.get(
            failure_type, 
            self.recovery_timeout
        )


class CircuitBreaker:
    """Circuit breaker for protecting LLM API calls."""
    
    def __init__(self, config: CircuitBreakerConfig, name: str):
        self.config = config
        self.name = name
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.failure_reasons: Dict[str, int] = {}
        self._lock = asyncio.Lock()
        
    async def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_recovery():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info(f"Circuit breaker {self.name} entering HALF_OPEN state")
                else:
                    raise Exception(
                        f"Circuit breaker {self.name} is OPEN. "
                        f"Last failure: {self.last_failure_time}"
                    )
        
        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
            
        except Exception as e:
            await self._record_failure(str(e))
            raise
            
    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True
            
        timeout = self.config.get_recovery_timeout(
            self._get_failure_type(str(self.last_failure_time))
        )
        return datetime.now() - self.last_failure_time > timedelta(seconds=timeout)
        
    async def _record_success(self):
        """Record successful call."""
        async with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._reset()
                    logger.info(f"Circuit breaker {self.name} CLOSED after recovery")
            elif self.state == CircuitBreakerState.CLOSED:
                self.failure_count = 0  # Reset on success
                
    async def _record_failure(self, reason: str):
        """Record failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            # Track failure reasons
            failure_type = self._get_failure_type(reason)
            self.failure_reasons[failure_type] = self.failure_reasons.get(failure_type, 0) + 1
            
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning(
                    f"Circuit breaker {self.name} OPENED after "
                    f"{self.failure_count} failures"
                )
                
    def _get_failure_type(self, error_message: str) -> str:
        """Categorize failure type from error message."""
        error_lower = error_message.lower()
        
        if "timeout" in error_lower or "timed out" in error_lower:
            return "timeout"
        elif "rate limit" in error_lower or "429" in error_lower:
            return "rate_limit"
        elif "authentication" in error_lower or "401" in error_lower:
            return "authentication"
        elif "network" in error_lower or "connection" in error_lower:
            return "network"
        else:
            return "other"
            
    def _reset(self):
        """Reset circuit breaker to initial state."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        
    def get_stats(self) -> Dict[str, Any]:
        """Get current circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "failure_reasons": self.failure_reasons
        }
