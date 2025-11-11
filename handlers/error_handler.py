"""
Centralized error handling and retry logic for LaunchBot.
Provides graceful degradation and proper logging.
"""

import logging
import time
import functools
from typing import Callable, Any, Optional
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple token bucket rate limiter"""
    
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.tokens = calls_per_minute
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait until a token is available"""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Replenish tokens based on time elapsed
            self.tokens = min(
                self.calls_per_minute,
                self.tokens + elapsed * (self.calls_per_minute / 60)
            )
            self.last_update = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) * (60 / self.calls_per_minute)
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class APIError(Exception):
    """Custom exception for API-related errors"""
    pass


class DataValidationError(Exception):
    """Custom exception for data validation failures"""
    pass


# Rate limiters for different services
RATE_LIMITERS = {
    'yahoo_finance': RateLimiter(calls_per_minute=30),
    'coingecko': RateLimiter(calls_per_minute=50),
    'twitter': RateLimiter(calls_per_minute=15),
    'dex': RateLimiter(calls_per_minute=100),
}


def get_rate_limiter(service: str) -> RateLimiter:
    """Get rate limiter for a specific service"""
    return RATE_LIMITERS.get(service, RateLimiter(calls_per_minute=60))


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential: bool = True,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential: Use exponential backoff if True, linear otherwise
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        if exponential:
                            delay = min(base_delay * (2 ** attempt), max_delay)
                        else:
                            delay = min(base_delay * (attempt + 1), max_delay)
                        
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries} retries failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        if exponential:
                            delay = min(base_delay * (2 ** attempt), max_delay)
                        else:
                            delay = min(base_delay * (attempt + 1), max_delay)
                        
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries} retries failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def safe_api_call(
    service: str,
    fallback_value: Any = None,
    log_errors: bool = True
):
    """
    Decorator for safe API calls with rate limiting and error handling.
    
    Args:
        service: Service name for rate limiting
        fallback_value: Value to return on failure
        log_errors: Whether to log errors
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            rate_limiter = get_rate_limiter(service)
            
            try:
                # Wait for rate limit
                await rate_limiter.acquire()
                
                # Execute function
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                if log_errors:
                    logger.error(
                        f"API call to {service} failed in {func.__name__}: {e}",
                        exc_info=True
                    )
                return fallback_value
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                if log_errors:
                    logger.error(
                        f"API call to {service} failed in {func.__name__}: {e}",
                        exc_info=True
                    )
                return fallback_value
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def validate_input(
    ticker: Optional[str] = None,
    price: Optional[float] = None,
    quantity: Optional[float] = None,
    user_id: Optional[int] = None
):
    """
    Validate common input types.
    
    Raises:
        DataValidationError: If validation fails
    """
    if ticker is not None:
        ticker = ticker.strip().upper()
        if not ticker or len(ticker) > 10 or not ticker.replace('-', '').isalnum():
            raise DataValidationError(f"Invalid ticker format: {ticker}")
    
    if price is not None:
        if price <= 0 or price > 1e12:
            raise DataValidationError(f"Invalid price: {price}")
    
    if quantity is not None:
        if quantity <= 0 or quantity > 1e12:
            raise DataValidationError(f"Invalid quantity: {quantity}")
    
    if user_id is not None:
        if not isinstance(user_id, int) or user_id <= 0:
            raise DataValidationError(f"Invalid user_id: {user_id}")


class CircuitBreaker:
    """
    Circuit breaker pattern for external services.
    Prevents cascading failures by temporarily disabling failing services.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == 'open':
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = 'half_open'
                logger.info(f"Circuit breaker entering half-open state for {func.__name__}")
            else:
                raise APIError(
                    f"Circuit breaker is OPEN for {func.__name__}. "
                    f"Service temporarily unavailable."
                )
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Success - reset failure count if in half-open state
            if self.state == 'half_open':
                self.state = 'closed'
                self.failure_count = 0
                logger.info(f"Circuit breaker closed for {func.__name__}")
            
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
                logger.error(
                    f"Circuit breaker OPENED for {func.__name__} after "
                    f"{self.failure_count} failures"
                )
            
            raise e


# Global circuit breakers for external services
CIRCUIT_BREAKERS = {
    'yahoo_finance': CircuitBreaker(failure_threshold=5, recovery_timeout=60),
    'coingecko': CircuitBreaker(failure_threshold=5, recovery_timeout=60),
    'twitter': CircuitBreaker(failure_threshold=3, recovery_timeout=300),
    'dex': CircuitBreaker(failure_threshold=10, recovery_timeout=30),
}


def get_circuit_breaker(service: str) -> CircuitBreaker:
    """Get circuit breaker for a specific service"""
    return CIRCUIT_BREAKERS.get(
        service,
        CircuitBreaker(failure_threshold=5, recovery_timeout=60)
    )


class HealthCheck:
    """System health monitoring"""
    
    def __init__(self):
        self.services = {}
        self.last_check = {}
    
    def register_service(self, name: str):
        """Register a service for health monitoring"""
        self.services[name] = {'status': 'unknown', 'last_success': None, 'failures': 0}
    
    def mark_success(self, service: str):
        """Mark successful service call"""
        if service in self.services:
            self.services[service]['status'] = 'healthy'
            self.services[service]['last_success'] = datetime.now()
            self.services[service]['failures'] = 0
    
    def mark_failure(self, service: str):
        """Mark failed service call"""
        if service in self.services:
            self.services[service]['failures'] += 1
            if self.services[service]['failures'] >= 3:
                self.services[service]['status'] = 'unhealthy'
    
    def get_status(self) -> dict:
        """Get overall system health status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'services': self.services,
            'overall': 'healthy' if all(
                s['status'] == 'healthy' for s in self.services.values()
            ) else 'degraded'
        }


# Global health check instance
health_check = HealthCheck()

# Register services
health_check.register_service('yahoo_finance')
health_check.register_service('coingecko')
health_check.register_service('twitter')
health_check.register_service('database')
health_check.register_service('bot_api')