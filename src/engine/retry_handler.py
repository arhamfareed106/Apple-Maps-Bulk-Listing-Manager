from typing import Any, Optional, Dict, List, Callable, Coroutine
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import time
import random
from enum import Enum
import json

from tenacity import (
    retry, stop_after_attempt, wait_exponential, retry_if_exception_type,
    RetryCallState
)

from ..config.settings import Settings
from ..config.logging_config import get_logger


class RetryReason(Enum):
    """Reason for retrying an operation"""
    RATE_LIMITED = "rate_limited"
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    UNAUTHORIZED = "unauthorized"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class RetryAttempt:
    """Information about a retry attempt"""
    attempt_number: int
    error: Exception
    error_type: str
    retry_reason: RetryReason
    wait_time: float
    next_attempt_at: datetime
    context: Optional[Dict[str, Any]] = None


class RetryHandler:
    """Handles retry logic with exponential backoff and jitter"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.max_attempts = settings.retry_max_attempts
        self.backoff_factor = settings.retry_backoff_factor
        
        # Error type to retry reason mapping
        self.error_mapping = {
            'ConnectionError': RetryReason.CONNECTION_ERROR,
            'TimeoutError': RetryReason.TIMEOUT_ERROR,
            'ConnectTimeout': RetryReason.TIMEOUT_ERROR,
            'ReadTimeout': RetryReason.TIMEOUT_ERROR,
            'TooManyRedirects': RetryReason.NETWORK_ERROR,
            'HTTPError': RetryReason.SERVER_ERROR,
            'Unauthorized': RetryReason.UNAUTHORIZED,
            'RateLimitError': RetryReason.RATE_LIMITED,
        }
    
    def classify_error(self, error: Exception) -> RetryReason:
        """Classify error to determine retry strategy"""
        error_type = type(error).__name__
        
        # Direct mapping
        if error_type in self.error_mapping:
            return self.error_mapping[error_type]
        
        # Check error message for common patterns
        error_str = str(error).lower()
        
        if 'rate limit' in error_str or '429' in error_str:
            return RetryReason.RATE_LIMITED
        elif 'timeout' in error_str or 'timed out' in error_str:
            return RetryReason.TIMEOUT_ERROR
        elif 'connection' in error_str or 'connect' in error_str:
            return RetryReason.CONNECTION_ERROR
        elif 'unauthorized' in error_str or '401' in error_str:
            return RetryReason.UNAUTHORIZED
        elif '500' in error_str or '502' in error_str or '503' in error_str:
            return RetryReason.SERVER_ERROR
        else:
            return RetryReason.UNKNOWN_ERROR
    
    def calculate_wait_time(self, attempt_number: int, retry_reason: RetryReason) -> float:
        """Calculate wait time with exponential backoff and jitter"""
        # Base exponential backoff
        base_wait = self.backoff_factor ** (attempt_number - 1)
        
        # Apply reason-specific multipliers
        reason_multipliers = {
            RetryReason.RATE_LIMITED: 2.0,      # Longer wait for rate limits
            RetryReason.TIMEOUT_ERROR: 1.5,      # Medium wait for timeouts
            RetryReason.CONNECTION_ERROR: 1.0,   # Standard wait for connection issues
            RetryReason.SERVER_ERROR: 1.2,      # Slightly longer for server issues
            RetryReason.UNAUTHORIZED: 0.1,       # Very short for auth issues (likely won't help)
            RetryReason.UNKNOWN_ERROR: 1.0,     # Standard wait for unknown errors
        }
        
        multiplier = reason_multipliers.get(retry_reason, 1.0)
        base_wait *= multiplier
        
        # Add jitter (±25%)
        jitter = random.uniform(0.75, 1.25)
        wait_time = base_wait * jitter
        
        # Apply maximum wait time
        max_wait = 300.0  # 5 minutes maximum
        return min(wait_time, max_wait)
    
    async def execute_with_retry(
        self,
        operation: Callable[[], Any],
        operation_name: str = "operation",
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute operation with retry logic"""
        attempt_number = 0
        last_error = None
        
        while attempt_number < self.max_attempts:
            attempt_number += 1
            
            try:
                self.logger.debug(f"Executing {operation_name}, attempt {attempt_number}")
                result = operation()
                
                # Handle async operations
                if asyncio.iscoroutine(result):
                    result = await result
                
                if attempt_number > 1:
                    self.logger.info(f"{operation_name} succeeded on attempt {attempt_number}")
                
                return result
                
            except Exception as e:
                last_error = e
                retry_reason = self.classify_error(e)
                
                if attempt_number >= self.max_attempts:
                    self.logger.error(
                        f"{operation_name} failed after {self.max_attempts} attempts: {str(e)}"
                    )
                    raise
                
                wait_time = self.calculate_wait_time(attempt_number, retry_reason)
                next_attempt_at = datetime.utcnow() + timedelta(seconds=wait_time)
                
                retry_attempt = RetryAttempt(
                    attempt_number=attempt_number,
                    error=e,
                    error_type=type(e).__name__,
                    retry_reason=retry_reason,
                    wait_time=wait_time,
                    next_attempt_at=next_attempt_at,
                    context=context
                )
                
                self.logger.warning(
                    f"{operation_name} failed (attempt {attempt_number}/{self.max_attempts}), "
                    f"retrying in {wait_time:.2f}s due to {retry_reason.value}: {str(e)}"
                )
                
                # Wait before retry
                await asyncio.sleep(wait_time)
        
        # This should never be reached due to the raise above
        raise last_error
    
    def create_retry_decorator(self, operation_name: str = "operation"):
        """Create a retry decorator for functions"""
        def retry_decorator(func):
            async def wrapper(*args, **kwargs):
                async def operation():
                    return func(*args, **kwargs)
                
                return await self.execute_with_retry(
                    operation,
                    operation_name,
                    {'args': args, 'kwargs': kwargs}
                )
            
            return wrapper
        return retry_decorator
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get retry statistics"""
        # In a production implementation, this would track retry metrics
        # For now, return basic configuration
        return {
            'max_attempts': self.max_attempts,
            'backoff_factor': self.backoff_factor,
            'supported_error_types': list(self.error_mapping.keys()),
            'reason_multipliers': {
                reason.value: multiplier 
                for reason, multiplier in {
                    RetryReason.RATE_LIMITED: 2.0,
                    RetryReason.TIMEOUT_ERROR: 1.5,
                    RetryReason.CONNECTION_ERROR: 1.0,
                    RetryReason.SERVER_ERROR: 1.2,
                    RetryReason.UNAUTHORIZED: 0.1,
                    RetryReason.UNKNOWN_ERROR: 1.0,
                }.items()
            }
        }
    
    def should_retry_immediately(self, error: Exception) -> bool:
        """Check if error should be retried immediately (no wait)"""
        retry_reason = self.classify_error(error)
        return retry_reason == RetryReason.UNAUTHORIZED  # Auth errors might be fixed quickly
    
    def get_retry_delay_info(self, attempt_number: int, error: Exception) -> Dict[str, Any]:
        """Get detailed information about retry delay"""
        retry_reason = self.classify_error(error)
        wait_time = self.calculate_wait_time(attempt_number, retry_reason)
        next_attempt_at = datetime.utcnow() + timedelta(seconds=wait_time)
        
        return {
            'attempt_number': attempt_number,
            'retry_reason': retry_reason.value,
            'wait_time_seconds': round(wait_time, 2),
            'next_attempt_at': next_attempt_at.isoformat(),
            'base_backoff': round(self.backoff_factor ** (attempt_number - 1), 2),
            'reason_multiplier': {
                RetryReason.RATE_LIMITED: 2.0,
                RetryReason.TIMEOUT_ERROR: 1.5,
                RetryReason.CONNECTION_ERROR: 1.0,
                RetryReason.SERVER_ERROR: 1.2,
                RetryReason.UNAUTHORIZED: 0.1,
                RetryReason.UNKNOWN_ERROR: 1.0,
            }.get(retry_reason, 1.0)
        }


# Global retry handler instance
retry_handler: Optional[RetryHandler] = None


def get_retry_handler(settings: Settings) -> RetryHandler:
    """Get or create global retry handler instance"""
    global retry_handler
    if retry_handler is None:
        retry_handler = RetryHandler(settings)
    return retry_handler


def retry_operation(operation_name: str = "operation"):
    """Decorator for retrying operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be used in synchronous contexts
            # For async operations, use RetryHandler directly
            raise NotImplementedError("Use RetryHandler.execute_with_retry for async operations")
        return wrapper
    return decorator