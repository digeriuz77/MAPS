"""
Rate Limiting Middleware

Provides request rate limiting based on IP address and user ID.
Helps prevent abuse and ensures fair usage of API resources.

Features:
- Per-IP rate limiting
- Per-user rate limiting (for authenticated users)
- Different limits for different endpoint types
- Configurable window sizes and request counts
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10  # Allow short bursts
    window_seconds: int = 60
    
    # Different limits for different endpoint types
    api_limits: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        "default": {"rpm": 60, "burst": 10},
        "chat": {"rpm": 30, "burst": 5},  # More restrictive for expensive endpoints
        "voice": {"rpm": 20, "burst": 3},
        "analysis": {"rpm": 10, "burst": 2},
        "auth": {"rpm": 10, "burst": 5},  # Strict for auth endpoints
    })


@dataclass
class RequestRecord:
    """Record of requests for a client"""
    timestamps: List[float] = field(default_factory=list)
    blocked_until: Optional[float] = None
    
    def clean_old_requests(self, window_seconds: int):
        """Remove requests outside the time window"""
        cutoff = time.time() - window_seconds
        self.timestamps = [ts for ts in self.timestamps if ts > cutoff]
    
    def is_blocked(self) -> bool:
        """Check if client is currently blocked"""
        if self.blocked_until is None:
            return False
        return time.time() < self.blocked_until
    
    def block(self, duration_seconds: int):
        """Block client for specified duration"""
        self.blocked_until = time.time() + duration_seconds
    
    def add_request(self):
        """Record a new request"""
        self.timestamps.append(time.time())


class RateLimiter:
    """
    In-memory rate limiter with sliding window.
    
    For production use, consider using Redis for distributed rate limiting.
    """
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self._storage: Dict[str, RequestRecord] = defaultdict(RequestRecord)
        self._cleanup_interval = 300  # Cleanup every 5 minutes
        self._last_cleanup = time.time()
    
    def is_allowed(self, client_id: str, endpoint_type: str = "default") -> Tuple[bool, Dict]:
        """
        Check if request is allowed and return rate limit info.
        
        Returns:
            Tuple of (allowed: bool, headers: dict)
        """
        # Periodic cleanup
        self._cleanup_if_needed()
        
        # Get limits for endpoint type
        limits = self.config.api_limits.get(endpoint_type, self.config.api_limits["default"])
        rpm = limits.get("rpm", self.config.requests_per_minute)
        burst = limits.get("burst", self.config.burst_size)
        
        record = self._storage[client_id]
        record.clean_old_requests(self.config.window_seconds)
        
        # Check if blocked
        if record.is_blocked():
            reset_time = int(record.blocked_until)
            return False, {
                "X-RateLimit-Limit": str(rpm),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(int(record.blocked_until - time.time()))
            }
        
        # Check rate limit (with burst allowance)
        current_count = len(record.timestamps)
        
        if current_count >= rpm:
            # Rate limit exceeded - block client
            block_duration = self.config.window_seconds
            record.block(block_duration)
            logger.warning(f"Rate limit exceeded for {client_id}, blocking for {block_duration}s")
            
            return False, {
                "X-RateLimit-Limit": str(rpm),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + block_duration)),
                "Retry-After": str(block_duration)
            }
        
        # Check burst limit
        recent_requests = len([ts for ts in record.timestamps 
                              if ts > time.time() - 1])  # Last second
        
        if recent_requests >= burst:
            # Burst limit exceeded
            return False, {
                "X-RateLimit-Limit": str(rpm),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + 1)),
                "Retry-After": "1"
            }
        
        # Record the request
        record.add_request()
        remaining = rpm - len(record.timestamps)
        
        return True, {
            "X-RateLimit-Limit": str(rpm),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(time.time() + self.config.window_seconds))
        }
    
    def _cleanup_if_needed(self):
        """Clean up old entries periodically"""
        if time.time() - self._last_cleanup > self._cleanup_interval:
            cutoff = time.time() - self.config.window_seconds * 2
            to_remove = [
                client_id for client_id, record in self._storage.items()
                if record.timestamps and all(ts < cutoff for ts in record.timestamps)
            ]
            for client_id in to_remove:
                del self._storage[client_id]
            self._last_cleanup = time.time()
            if to_remove:
                logger.debug(f"Cleaned up {len(to_remove)} rate limit entries")
    
    def reset(self, client_id: str):
        """Reset rate limit for a client"""
        if client_id in self._storage:
            del self._storage[client_id]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting on API requests.
    
    Limits are applied per IP address and optionally per user ID.
    """
    
    def __init__(self, app, config: RateLimitConfig = None):
        super().__init__(app)
        self.limiter = RateLimiter(config)
        
        # Paths that are exempt from rate limiting
        self.exempt_paths = {
            "/health",
            "/metrics",
            "/static/",
        }
    
    async def dispatch(self, request: Request, call_next):
        # Check if path is exempt
        path = request.url.path
        if any(path.startswith(exempt) or path == exempt for exempt in self.exempt_paths):
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Determine endpoint type for specific limits
        endpoint_type = self._get_endpoint_type(path)
        
        # Check rate limit
        allowed, headers = self.limiter.is_allowed(client_id, endpoint_type)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_id} on {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": "Rate limit exceeded. Please try again later."
                },
                headers=headers
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        for header, value in headers.items():
            response.headers[header] = value
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get unique identifier for the client.
        
        Tries to use user ID from auth, falls back to IP address.
        """
        # Try to get user ID from auth header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # Could decode JWT to get user ID
            # For now, use token hash as identifier
            token = auth_header.replace("Bearer ", "")
            return f"user:{hash(token) % 1000000}"
        
        # Fall back to IP address
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    def _get_endpoint_type(self, path: str) -> str:
        """Determine endpoint type for specific rate limits"""
        if "/chat" in path or "/conversation" in path:
            return "chat"
        elif "/voice" in path:
            return "voice"
        elif "/analysis" in path:
            return "analysis"
        elif "/auth" in path:
            return "auth"
        return "default"


# Global rate limiter instance for use across the app
rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    return rate_limiter
