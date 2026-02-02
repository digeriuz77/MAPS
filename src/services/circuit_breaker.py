"""
Circuit Breaker Pattern Implementation for LLM Resilience

Provides fault tolerance for LLM provider calls by preventing cascade failures
and enabling graceful degradation during provider outages.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Provider failing, requests fail fast
- HALF_OPEN: Testing if provider has recovered
"""

from __future__ import annotations

import logging
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, reject fast
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5           # Failures before opening
    recovery_timeout: int = 60           # Seconds before half-open
    half_open_max_calls: int = 3         # Test calls in half-open
    success_threshold: int = 2           # Successes to close circuit
    timeout_seconds: int = 30            # Request timeout
    
    # Exponential backoff for retries
    retry_attempts: int = 3
    retry_delay_base: float = 1.0


@dataclass
class CircuitStats:
    """Statistics for circuit breaker monitoring"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0  # Fast-fail when open
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    
    def record_success(self):
        self.total_calls += 1
        self.successful_calls += 1
        self.last_success_time = datetime.utcnow()
        self.consecutive_failures = 0
        self.consecutive_successes += 1
    
    def record_failure(self):
        self.total_calls += 1
        self.failed_calls += 1
        self.last_failure_time = datetime.utcnow()
        self.consecutive_failures += 1
        self.consecutive_successes = 0
    
    def record_rejection(self):
        self.total_calls += 1
        self.rejected_calls += 1


class CircuitBreaker:
    """
    Circuit breaker for LLM provider resilience.
    
    Usage:
        breaker = CircuitBreaker("openai", CircuitBreakerConfig())
        
        if breaker.can_execute():
            try:
                result = await llm_call()
                breaker.record_success()
            except Exception as e:
                breaker.record_failure()
                raise
        else:
            raise CircuitBreakerOpenError("OpenAI circuit is open")
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self._lock = asyncio.Lock()
        self._opened_at: Optional[datetime] = None
        self._half_open_calls = 0
        
        logger.info(f"🔄 Circuit breaker initialized for {name}")
    
    async def can_execute(self) -> bool:
        """Check if execution is allowed based on circuit state"""
        async with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            elif self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(f"🔓 Circuit {self.name} entering HALF_OPEN state")
                    return True
                else:
                    self.stats.record_rejection()
                    return False
            
            elif self.state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                else:
                    self.stats.record_rejection()
                    return False
            
            return False
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery"""
        if self._opened_at is None:
            return True
        elapsed = (datetime.utcnow() - self._opened_at).total_seconds()
        return elapsed >= self.config.recovery_timeout
    
    async def record_success(self):
        """Record a successful call"""
        async with self._lock:
            self.stats.record_success()
            
            if self.state == CircuitState.HALF_OPEN:
                if self.stats.consecutive_successes >= self.config.success_threshold:
                    self._close_circuit()
    
    async def record_failure(self, error: Exception = None):
        """Record a failed call"""
        async with self._lock:
            self.stats.record_failure()
            
            if self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open returns to open
                self._open_circuit()
            elif self.state == CircuitState.CLOSED:
                if self.stats.consecutive_failures >= self.config.failure_threshold:
                    self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit"""
        self.state = CircuitState.OPEN
        self._opened_at = datetime.utcnow()
        self._half_open_calls = 0
        logger.warning(
            f"🔴 Circuit {self.name} OPENED after {self.stats.consecutive_failures} failures"
        )
    
    def _close_circuit(self):
        """Close the circuit"""
        self.state = CircuitState.CLOSED
        self._opened_at = None
        self._half_open_calls = 0
        self.stats.consecutive_failures = 0
        logger.info(f"🟢 Circuit {self.name} CLOSED - service recovered")
    
    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        return self.state
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.state.value,
            "stats": {
                "total_calls": self.stats.total_calls,
                "successful_calls": self.stats.successful_calls,
                "failed_calls": self.stats.failed_calls,
                "rejected_calls": self.stats.rejected_calls,
                "consecutive_failures": self.stats.consecutive_failures,
                "consecutive_successes": self.stats.consecutive_successes,
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "half_open_max_calls": self.config.half_open_max_calls,
            }
        }
    
    async def reset(self):
        """Manually reset the circuit to CLOSED"""
        async with self._lock:
            self._close_circuit()
            self.stats = CircuitStats()
            logger.info(f"🔄 Circuit {self.name} manually reset")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.
    Provides centralized management for all LLM provider circuits.
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._breakers: Dict[str, CircuitBreaker] = {}
            cls._instance._initialized = False
        return cls._instance
    
    async def initialize(self):
        """Initialize default circuit breakers for LLM providers"""
        if self._initialized:
            return
        
        async with self._lock:
            # Default circuit breakers for each provider
            default_config = CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60,
                half_open_max_calls=3,
                success_threshold=2,
                timeout_seconds=30
            )
            
            providers = ["openai", "anthropic", "gemini"]
            for provider in providers:
                if provider not in self._breakers:
                    self._breakers[provider] = CircuitBreaker(provider, default_config)
            
            self._initialized = True
            logger.info(f"🔄 Circuit breaker registry initialized with {len(providers)} providers")
    
    def get_breaker(self, name: str) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name)
        return self._breakers[name]
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all circuit breakers"""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}
    
    async def reset_all(self):
        """Reset all circuit breakers"""
        async with self._lock:
            for breaker in self._breakers.values():
                await breaker.reset()
    
    async def health_check(self) -> Dict[str, str]:
        """Get health status of all circuits"""
        return {name: breaker.state.value for name, breaker in self._breakers.items()}


# Global registry instance
circuit_registry = CircuitBreakerRegistry()


def with_circuit_breaker(breaker_name: str):
    """
    Decorator to wrap function with circuit breaker logic.
    
    Usage:
        @with_circuit_breaker("openai")
        async def call_openai(prompt: str) -> str:
            # Make LLM call
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            breaker = circuit_registry.get_breaker(breaker_name)
            
            if not await breaker.can_execute():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker for {breaker_name} is OPEN"
                )
            
            try:
                result = await func(*args, **kwargs)
                await breaker.record_success()
                return result
            except Exception as e:
                await breaker.record_failure(e)
                raise
        
        return wrapper
    return decorator


# Convenience functions for common providers
async def get_openai_breaker() -> CircuitBreaker:
    """Get the OpenAI circuit breaker"""
    await circuit_registry.initialize()
    return circuit_registry.get_breaker("openai")


async def get_anthropic_breaker() -> CircuitBreaker:
    """Get the Anthropic circuit breaker"""
    await circuit_registry.initialize()
    return circuit_registry.get_breaker("anthropic")


async def get_gemini_breaker() -> CircuitBreaker:
    """Get the Gemini circuit breaker"""
    await circuit_registry.initialize()
    return circuit_registry.get_breaker("gemini")
