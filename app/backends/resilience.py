"""
resilience.py — Retry, Circuit Breaker, and Dead Letter Queue utilities.

Provides drop-in wrappers for external service calls (Ollama, ComfyUI, F5-TTS,
Whisper, search APIs) to handle transient failures gracefully and prevent
cascade failures when a downstream service is down.

Usage:
    from app.backends.resilience import resilient_call, circuit_ollama

    # Automatic retry + circuit breaker on any async callable
    result = await resilient_call(
        client.post, f"{ollama_url}/api/chat", json=payload,
        circuit=circuit_ollama, retries=3, base_delay=1.0
    )

    # Or use the decorator form
    @with_retry(retries=3, base_delay=2.0)
    async def fetch_model_list(ollama_url): ...
"""

import asyncio
import functools
import hashlib
import json
import logging
import os
import time
from typing import Any, Callable, Optional

import httpx

logger = logging.getLogger("spark.backend.resilience")

# ─── Circuit Breaker ───────────────────────────────────────────────────────

class CircuitBreaker:
    """
    Tracks the health of a single downstream service.

    States:
      - CLOSED:   Requests flow normally. Failures increment the counter.
      - OPEN:     Service is considered down. All calls fail-fast for
                  `recovery_timeout` seconds before transitioning to HALF_OPEN.
      - HALF_OPEN: A single trial request is allowed. Success → CLOSED,
                   failure → back to OPEN.

    This prevents the pipeline from wasting 120s timeouts on a service that
    has been unreachable for the last 10 calls.
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._state = self.CLOSED
        self._opened_at: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> str:
        if self._state == self.OPEN:
            # Check if recovery period has elapsed
            if time.time() - self._opened_at >= self.recovery_timeout:
                return self.HALF_OPEN
        return self._state

    async def record_success(self):
        async with self._lock:
            if self._state != self.CLOSED:
                logger.info(f"Circuit [{self.name}] recovered → CLOSED")
            self._failure_count = 0
            self._state = self.CLOSED

    async def record_failure(self):
        async with self._lock:
            self._failure_count += 1
            if self._state == self.HALF_OPEN:
                logger.warning(f"Circuit [{self.name}] trial failed → OPEN")
                self._state = self.OPEN
                self._opened_at = time.time()
            elif self._failure_count >= self.failure_threshold:
                logger.warning(
                    f"Circuit [{self.name}] OPEN after {self._failure_count} failures"
                )
                self._state = self.OPEN
                self._opened_at = time.time()

    async def can_execute(self) -> bool:
        """Return True if a call is allowed, False if circuit is OPEN."""
        current = self.state
        if current == self.OPEN:
            return False
        return True


# Pre-instantiated circuit breakers for each external service.
# These are module-level singletons so state is shared across all callers.
circuit_ollama = CircuitBreaker("ollama", failure_threshold=5, recovery_timeout=30.0)
circuit_comfyui = CircuitBreaker("comfyui", failure_threshold=4, recovery_timeout=60.0)
circuit_f5tts = CircuitBreaker("f5-tts", failure_threshold=4, recovery_timeout=30.0)
circuit_whisper = CircuitBreaker("whisper", failure_threshold=4, recovery_timeout=30.0)
circuit_qdrant = CircuitBreaker("qdrant", failure_threshold=5, recovery_timeout=20.0)
circuit_vllm = CircuitBreaker("vllm", failure_threshold=5, recovery_timeout=30.0)
circuit_deepseek = CircuitBreaker("deepseek", failure_threshold=3, recovery_timeout=60.0)

# Registry for dynamic lookup by service name
CIRCUITS: dict[str, CircuitBreaker] = {
    "ollama": circuit_ollama,
    "comfyui": circuit_comfyui,
    "f5-tts": circuit_f5tts,
    "f5tts": circuit_f5tts,
    "whisper": circuit_whisper,
    "qdrant": circuit_qdrant,
    "vllm": circuit_vllm,
    "deepseek": circuit_deepseek,
}


class CircuitOpenError(Exception):
    """Raised when a circuit breaker is OPEN and the call is rejected."""

    def __init__(self, service: str):
        self.service = service
        super().__init__(
            f"Circuit breaker [{service}] is OPEN — service appears to be down. "
            f"Call rejected to prevent cascade timeout."
        )


# ─── Retry with Exponential Backoff ────────────────────────────────────────

# Exceptions that indicate a transient/network issue worth retrying
_RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.ConnectTimeout,
    ConnectionError,
    asyncio.TimeoutError,
)

# HTTP status codes that indicate a transient server issue
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_retryable(exc: Exception) -> bool:
    """Check if an exception represents a transient failure worth retrying."""
    if isinstance(exc, _RETRYABLE_EXCEPTIONS):
        return True
    # Check for httpx HTTPStatusError with retryable status
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in _RETRYABLE_STATUS_CODES
    return False


def with_retry(
    retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
):
    """
    Decorator: retry an async function on transient failures with
    exponential backoff + optional jitter.

    Args:
        retries:        Maximum number of retry attempts (not counting the initial call).
        base_delay:     Initial delay in seconds before the first retry.
        max_delay:      Cap on the delay between retries.
        backoff_factor: Multiplier applied to delay after each failure.
        jitter:         If True, add up to 25% random jitter to each delay.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc: Optional[Exception] = None
            for attempt in range(retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as exc:
                    last_exc = exc
                    if not _is_retryable(exc):
                        raise
                    if attempt >= retries:
                        logger.error(
                            f"{func.__name__} exhausted {retries} retries: {exc}"
                        )
                        raise
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    if jitter:
                        import random
                        delay *= (0.75 + random.random() * 0.5)
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{retries + 1} failed: {exc}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


# ─── Combined Resilient Call ───────────────────────────────────────────────

async def resilient_call(
    func: Callable,
    *args,
    circuit: Optional[CircuitBreaker] = None,
    retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    **kwargs,
) -> Any:
    """
    Execute an async callable with retry + circuit breaker protection.

    This is the primary entry point for wrapping external service calls.
    It checks the circuit breaker first (fail-fast if OPEN), then retries
    on transient failures, and records success/failure back to the circuit.

    Args:
        func:        The async callable to execute.
        circuit:     Optional CircuitBreaker to consult. If None, only retry is applied.
        retries:     Max retry attempts on transient failures.
        base_delay:  Initial backoff delay in seconds.
        max_delay:   Maximum backoff delay cap.
        **kwargs:    Passed through to func.

    Returns:
        The return value of func(*args, **kwargs).

    Raises:
        CircuitOpenError: If the circuit breaker is OPEN.
        Last exception:   If all retries are exhausted.
    """
    # 1. Check circuit breaker
    if circuit is not None:
        if not await circuit.can_execute():
            raise CircuitOpenError(circuit.name)

    # 2. Retry loop
    last_exc: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            result = await func(*args, **kwargs)
            # Success — reset circuit
            if circuit is not None:
                await circuit.record_success()
            return result
        except Exception as exc:
            last_exc = exc
            # Non-retryable: record failure and re-raise immediately
            if not _is_retryable(exc):
                if circuit is not None:
                    await circuit.record_failure()
                raise
            # Last attempt: record failure and re-raise
            if attempt >= retries:
                if circuit is not None:
                    await circuit.record_failure()
                logger.error(
                    f"resilient_call exhausted {retries} retries: {exc}"
                )
                raise
            # Backoff and retry
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            if jitter:
                import random
                delay *= (0.75 + random.random() * 0.5)
            logger.warning(
                f"resilient_call attempt {attempt + 1}/{retries + 1} failed: {exc}. "
                f"Retrying in {delay:.1f}s..."
            )
            await asyncio.sleep(delay)

    raise last_exc  # type: ignore[misc]


async def resilient_httpx_request(
    method: str,
    url: str,
    *,
    circuit: Optional[CircuitBreaker] = None,
    retries: int = 3,
    base_delay: float = 1.0,
    timeout: float = 120.0,
    **kwargs,
) -> httpx.Response:
    """
    Convenience wrapper for httpx.AsyncClient requests with resilience.

    Handles client creation, timeout, retry, and circuit breaker in one call.

    Args:
        method:  HTTP method ("GET", "POST", etc.)
        url:     Target URL.
        circuit: Optional circuit breaker for the target service.
        retries: Max retry attempts.
        timeout: httpx timeout in seconds.

    Returns:
        httpx.Response on success (status 2xx).

    Raises:
        CircuitOpenError: If circuit is OPEN.
        httpx.HTTPStatusError: On non-retryable HTTP error status.
        Last exception: On exhausted retries.
    """
    async def _do_request() -> httpx.Response:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.request(method, url, **kwargs)
            # Raise for retryable status codes so resilient_call can catch them
            if resp.status_code in _RETRYABLE_STATUS_CODES:
                raise httpx.HTTPStatusError(
                    f"HTTP {resp.status_code}", request=resp.request, response=resp
                )
            resp.raise_for_status()
            return resp

    return await resilient_call(
        _do_request, circuit=circuit, retries=retries, base_delay=base_delay
    )


# ─── Dead Letter Queue ────────────────────────────────────────────────────

class DeadLetterEntry:
    """A single entry in the dead letter queue."""
    def __init__(
        self,
        job_id: str,
        step: str,
        service: str,
        payload: dict,
        error: str,
        timestamp: float = None,
    ):
        self.job_id = job_id
        self.step = step
        self.service = service
        self.payload = payload
        self.error = error
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "step": self.step,
            "service": self.service,
            "payload": self.payload,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class DeadLetterQueue:
    """
    In-memory dead letter queue for permanently failed pipeline tasks.

    When a step exhausts all retries and the circuit is tripped, the task
    details are stored here so they can be inspected and manually retried
    later via the REST API.
    """

    MAX_ENTRIES = 500

    def __init__(self):
        self._entries: list[DeadLetterEntry] = []
        self._lock = asyncio.Lock()

    async def add(self, entry: DeadLetterEntry):
        async with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self.MAX_ENTRIES:
                self._entries = self._entries[-self.MAX_ENTRIES:]
            logger.error(
                f"DLQ added: job={entry.job_id} step={entry.step} service={entry.service} "
                f"error={entry.error[:200]}"
            )

    async def list(self, limit: int = 50) -> list[dict]:
        async with self._lock:
            return [e.to_dict() for e in self._entries[-limit:]]

    async def retry(self, index: int) -> Optional[DeadLetterEntry]:
        """Remove and return an entry for manual retry."""
        async with self._lock:
            if 0 <= index < len(self._entries):
                return self._entries.pop(index)
            return None

    async def clear(self):
        async with self._lock:
            self._entries.clear()


# Singleton DLQ instance
dlq = DeadLetterQueue()


# ─── Service Health Status ────────────────────────────────────────────────

async def get_service_health() -> dict:
    """
    Return a snapshot of all circuit breaker states for the health endpoint.
    """
    return {
        name: {
            "state": cb.state,
            "failures": cb._failure_count,
            "threshold": cb.failure_threshold,
        }
        for name, cb in CIRCUITS.items()
    }
