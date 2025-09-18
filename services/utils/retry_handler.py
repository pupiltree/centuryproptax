"""
Retry handler utility for robust database and API operations.
Handles transient failures with exponential backoff and specific error handling.
"""

import asyncio
import random
from functools import wraps
from typing import Type, Tuple, Callable, Any, Optional, Union, List
from datetime import datetime
import structlog

logger = structlog.get_logger()

class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass

class RetryableError(Exception):
    """Base class for errors that should trigger retry logic."""
    pass

class DatabaseRetryableError(RetryableError):
    """Database-specific retryable errors."""
    pass

class APIRetryableError(RetryableError):
    """API-specific retryable errors."""
    pass

def is_retryable_exception(exception: Exception) -> bool:
    """
    Determine if an exception should trigger retry logic.
    
    Args:
        exception: The exception to check
        
    Returns:
        True if the exception should trigger retry, False otherwise
    """
    # Database connection errors
    if "connection" in str(exception).lower():
        return True
    
    # Timeout errors  
    if "timeout" in str(exception).lower():
        return True
        
    # Lock errors
    if "lock" in str(exception).lower():
        return True
    
    # Temporary unavailable
    if "unavailable" in str(exception).lower():
        return True
        
    # SQLAlchemy specific errors
    if hasattr(exception, '__class__'):
        error_name = exception.__class__.__name__
        retryable_errors = [
            'OperationalError',
            'DisconnectionError', 
            'TimeoutError',
            'DatabaseError',
            'InterfaceError'
        ]
        if any(err in error_name for err in retryable_errors):
            return True
    
    # Explicitly marked retryable errors
    if isinstance(exception, RetryableError):
        return True
        
    return False

def async_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = None,
    non_retryable_exceptions: Tuple[Type[Exception], ...] = None
):
    """
    Async retry decorator with exponential backoff and jitter.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Exponential backoff multiplier (default: 2.0)
        jitter: Add random jitter to delay (default: True)
        retryable_exceptions: Specific exceptions to retry on
        non_retryable_exceptions: Exceptions to never retry on
    
    Returns:
        Decorated async function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(
                            "Retry successful",
                            function=func.__name__,
                            attempt=attempt + 1,
                            total_attempts=max_retries + 1
                        )
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if this is the last attempt
                    if attempt == max_retries:
                        logger.error(
                            "All retry attempts exhausted",
                            function=func.__name__,
                            max_retries=max_retries,
                            final_error=str(e),
                            error_type=type(e).__name__
                        )
                        raise RetryExhaustedError(
                            f"Function {func.__name__} failed after {max_retries + 1} attempts. "
                            f"Final error: {str(e)}"
                        ) from e
                    
                    # Check if we should retry this exception
                    should_retry = False
                    
                    if non_retryable_exceptions and isinstance(e, non_retryable_exceptions):
                        logger.warning(
                            "Non-retryable exception encountered",
                            function=func.__name__,
                            error=str(e),
                            error_type=type(e).__name__
                        )
                        raise e
                    
                    if retryable_exceptions:
                        should_retry = isinstance(e, retryable_exceptions)
                    else:
                        should_retry = is_retryable_exception(e)
                    
                    if not should_retry:
                        logger.warning(
                            "Non-retryable exception, failing immediately",
                            function=func.__name__,
                            error=str(e),
                            error_type=type(e).__name__
                        )
                        raise e
                    
                    # Calculate delay
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        "Retrying after error",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries + 1,
                        error=str(e),
                        error_type=type(e).__name__,
                        retry_delay=f"{delay:.2f}s"
                    )
                    
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator

def sync_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = None,
    non_retryable_exceptions: Tuple[Type[Exception], ...] = None
):
    """
    Synchronous retry decorator with exponential backoff and jitter.
    Same parameters as async_retry but for synchronous functions.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(
                            "Retry successful",
                            function=func.__name__,
                            attempt=attempt + 1,
                            total_attempts=max_retries + 1
                        )
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if this is the last attempt
                    if attempt == max_retries:
                        logger.error(
                            "All retry attempts exhausted",
                            function=func.__name__,
                            max_retries=max_retries,
                            final_error=str(e),
                            error_type=type(e).__name__
                        )
                        raise RetryExhaustedError(
                            f"Function {func.__name__} failed after {max_retries + 1} attempts. "
                            f"Final error: {str(e)}"
                        ) from e
                    
                    # Check if we should retry this exception
                    should_retry = False
                    
                    if non_retryable_exceptions and isinstance(e, non_retryable_exceptions):
                        logger.warning(
                            "Non-retryable exception encountered",
                            function=func.__name__,
                            error=str(e),
                            error_type=type(e).__name__
                        )
                        raise e
                    
                    if retryable_exceptions:
                        should_retry = isinstance(e, retryable_exceptions)
                    else:
                        should_retry = is_retryable_exception(e)
                    
                    if not should_retry:
                        logger.warning(
                            "Non-retryable exception, failing immediately",
                            function=func.__name__,
                            error=str(e),
                            error_type=type(e).__name__
                        )
                        raise e
                    
                    # Calculate delay
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        "Retrying after error",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries + 1,
                        error=str(e),
                        error_type=type(e).__name__,
                        retry_delay=f"{delay:.2f}s"
                    )
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator

class CircuitBreaker:
    """
    Circuit breaker pattern implementation for preventing cascading failures.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def call(self, func: Callable, *args, **kwargs):
        """Execute a function with circuit breaker protection."""
        
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception(f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    async def acall(self, func: Callable, *args, **kwargs):
        """Execute an async function with circuit breaker protection."""
        
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception(f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt a reset."""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful execution."""
        self.failure_count = 0
        self.state = "CLOSED"
        logger.info("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(
                "Circuit breaker opened due to failures",
                failure_count=self.failure_count,
                threshold=self.failure_threshold
            )

# Global circuit breakers for common operations
database_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
payment_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)