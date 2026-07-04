from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio
import time
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import tenacity
from circuitbreaker import circuit

from ..config.settings import Settings
from ..config.logging_config import get_logger


@dataclass
class APIResponse:
    """Standard API response wrapper"""
    status_code: int
    data: Any
    headers: Dict[str, str]
    elapsed_time: float
    request_id: Optional[str] = None


@dataclass
class RateLimitInfo:
    """Rate limit information"""
    limit: int
    remaining: int
    reset_time: datetime
    window_seconds: int


class BaseAPIClient(ABC):
    """Abstract base class for API clients with common functionality"""
    
    def __init__(self, settings: Settings, name: str):
        self.settings = settings
        self.name = name
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.session = self._create_session()
        self.rate_limit_info: Optional[RateLimitInfo] = None
        self._last_request_time = 0.0
        self._request_count = 0
        
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry configuration"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.settings.retry_max_attempts,
            backoff_factor=self.settings.retry_backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    @abstractmethod
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        pass
    
    @abstractmethod
    def get_base_url(self) -> str:
        """Get base URL for API requests"""
        pass
    
    def _get_rate_limit_info(self, response: requests.Response) -> Optional[RateLimitInfo]:
        """Extract rate limit information from response headers"""
        try:
            limit = int(response.headers.get('X-RateLimit-Limit', 0))
            remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            reset = int(response.headers.get('X-RateLimit-Reset', 0))
            
            if limit > 0:
                return RateLimitInfo(
                    limit=limit,
                    remaining=remaining,
                    reset_time=datetime.fromtimestamp(reset),
                    window_seconds=3600  # Default 1 hour window
                )
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting based on API limits"""
        if not self.rate_limit_info:
            return
            
        # Wait if we're approaching rate limit
        if self.rate_limit_info.remaining < 10:  # Buffer of 10 requests
            sleep_time = max(0, (self.rate_limit_info.reset_time - datetime.now()).total_seconds())
            if sleep_time > 0:
                self.logger.warning(
                    f"Rate limit approaching for {self.name}, sleeping for {sleep_time:.2f} seconds"
                )
                time.sleep(sleep_time)
                return
        
        # Enforce minimum delay between requests
        min_delay = 1.0 / (self.rate_limit_info.limit / self.rate_limit_info.window_seconds)
        time_since_last = time.time() - self._last_request_time
        if time_since_last < min_delay:
            sleep_time = min_delay - time_since_last
            time.sleep(sleep_time)
    
    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        retry=tenacity.retry_if_exception_type((requests.RequestException, ConnectionError)),
        reraise=True
    )
    @circuit(
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=(requests.RequestException, ConnectionError)
    )
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None
    ) -> APIResponse:
        """Make HTTP request with retry and circuit breaker"""
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        url = f"{self.get_base_url()}{endpoint}"
        request_headers = self.get_auth_headers()
        if headers:
            request_headers.update(headers)
        
        start_time = time.time()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json,
                headers=request_headers,
                timeout=timeout or 30
            )
            
            elapsed_time = time.time() - start_time
            self._last_request_time = time.time()
            self._request_count += 1
            
            # Update rate limit info
            self.rate_limit_info = self._get_rate_limit_info(response)
            
            # Log request
            self.logger.info(
                f"API request completed",
                method=method,
                url=url,
                status_code=response.status_code,
                elapsed_time=elapsed_time,
                rate_limit_remaining=self.rate_limit_info.remaining if self.rate_limit_info else None
            )
            
            # Handle different status codes
            if response.status_code >= 400:
                self.logger.error(
                    f"API request failed",
                    method=method,
                    url=url,
                    status_code=response.status_code,
                    response_text=response.text[:200]  # First 200 chars
                )
                
                if response.status_code == 429:  # Rate limited
                    raise requests.exceptions.RetryError("Rate limit exceeded")
                elif response.status_code >= 500:  # Server error
                    raise requests.exceptions.ConnectionError("Server error")
            
            return APIResponse(
                status_code=response.status_code,
                data=response.json() if response.content else None,
                headers=dict(response.headers),
                elapsed_time=elapsed_time,
                request_id=response.headers.get('X-Request-ID')
            )
            
        except requests.exceptions.RequestException as e:
            elapsed_time = time.time() - start_time
            self.logger.error(
                f"API request failed with exception",
                method=method,
                url=url,
                error=str(e),
                elapsed_time=elapsed_time
            )
            raise
    
    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> APIResponse:
        """Make GET request"""
        return self._make_request("GET", endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None, **kwargs) -> APIResponse:
        """Make POST request"""
        return self._make_request("POST", endpoint, data=data, json=json, **kwargs)
    
    def put(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None, **kwargs) -> APIResponse:
        """Make PUT request"""
        return self._make_request("PUT", endpoint, data=data, json=json, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> APIResponse:
        """Make DELETE request"""
        return self._make_request("DELETE", endpoint, **kwargs)
    
    def patch(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None, **kwargs) -> APIResponse:
        """Make PATCH request"""
        return self._make_request("PATCH", endpoint, data=data, json=json, **kwargs)
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if the API is healthy and accessible"""
        pass
    
    def get_request_stats(self) -> Dict[str, Any]:
        """Get request statistics"""
        return {
            "client_name": self.name,
            "request_count": self._request_count,
            "last_request_time": self._last_request_time,
            "rate_limit_info": {
                "limit": self.rate_limit_info.limit if self.rate_limit_info else None,
                "remaining": self.rate_limit_info.remaining if self.rate_limit_info else None,
                "reset_time": self.rate_limit_info.reset_time.isoformat() if self.rate_limit_info else None
            } if self.rate_limit_info else None
        }
    
    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()