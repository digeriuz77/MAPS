"""
Security utilities for input validation and sanitization
"""
import re
import html
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import wraps
import hashlib

from src.core.constants import (
    MAX_MESSAGE_LENGTH, MIN_MESSAGE_LENGTH, 
    MAX_CONTEXT_SIZE, RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS
)
from src.exceptions import SafetyViolationError

class InputValidator:
    """Validates and sanitizes user inputs"""
    
    # Pre-compiled patterns for better performance
    # Patterns that might indicate prompt injection attempts
    _INJECTION_PATTERNS_RAW = [
        r'ignore\s+(?:previous|all|above)',
        r'disregard\s+(?:instructions|rules|guidelines)',
        r'pretend\s+you\s+are',
        r'act\s+as\s+if',
        r'new\s+instructions:',
        r'system\s*:',
        r'<\|.*?\|>',  # Special tokens
        r'\[\[.*?\]\]',  # Instruction markers
        r'###\s*(?:INSTRUCTION|SYSTEM|PROMPT)',
    ]
    
    # HTML/Script injection patterns
    _SCRIPT_PATTERNS_RAW = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',  # Event handlers
        r'<iframe.*?>',
        r'<object.*?>',
        r'<embed.*?>',
    ]
    
    # Compile patterns at class level for reuse
    INJECTION_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in _INJECTION_PATTERNS_RAW]
    SCRIPT_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in _SCRIPT_PATTERNS_RAW]
    HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
    
    @classmethod
    def validate_message(cls, message: str) -> str:
        """
        Validate and sanitize user message
        
        Args:
            message: Raw user input
            
        Returns:
            Sanitized message
            
        Raises:
            SafetyViolationError: If message fails validation
        """
        if not message or not isinstance(message, str):
            raise SafetyViolationError("Message must be a non-empty string")
        
        # Check length constraints
        message = message.strip()
        if len(message) < MIN_MESSAGE_LENGTH:
            raise SafetyViolationError(
                f"Message too short (minimum {MIN_MESSAGE_LENGTH} characters)"
            )
        
        if len(message) > MAX_MESSAGE_LENGTH:
            raise SafetyViolationError(
                f"Message too long (maximum {MAX_MESSAGE_LENGTH} characters)"
            )
        
        # Check for prompt injection attempts
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(message):
                raise SafetyViolationError(
                    "Message contains potentially unsafe patterns",
                    ["prompt_injection_attempt"]
                )
        
        # Sanitize HTML/scripts
        sanitized = cls.sanitize_html(message)
        
        # Check for script injection after sanitization
        for pattern in cls.SCRIPT_PATTERNS:
            if pattern.search(sanitized):
                raise SafetyViolationError(
                    "Message contains script or HTML elements",
                    ["script_injection_attempt"]
                )
        
        return sanitized
    
    @classmethod
    def sanitize_html(cls, text: str) -> str:
        """
        Sanitize HTML entities and remove dangerous elements
        
        Args:
            text: Raw text input
            
        Returns:
            Sanitized text
        """
        # Escape HTML entities
        text = html.escape(text)
        
        # Remove any remaining suspicious patterns
        text = cls.HTML_TAG_PATTERN.sub('', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    @classmethod
    def validate_context(cls, context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Validate context dictionary
        
        Args:
            context: Context dictionary
            
        Returns:
            Validated context or None
            
        Raises:
            SafetyViolationError: If context is invalid
        """
        if context is None:
            return None
        
        if not isinstance(context, dict):
            raise SafetyViolationError("Context must be a dictionary")
        
        # Check context size
        context_str = str(context)
        if len(context_str) > MAX_CONTEXT_SIZE:
            raise SafetyViolationError(
                f"Context too large (maximum {MAX_CONTEXT_SIZE} characters)"
            )
        
        # Validate each value in context
        validated_context = {}
        for key, value in context.items():
            if not isinstance(key, str) or not key.isidentifier():
                raise SafetyViolationError(f"Invalid context key: {key}")
            
            # Sanitize string values
            if isinstance(value, str):
                validated_context[key] = cls.sanitize_html(value)
            elif isinstance(value, (int, float, bool, type(None))):
                validated_context[key] = value
            elif isinstance(value, (list, dict)):
                # Limit nested structure depth
                if cls._get_nested_structure_depth(value) > 3:
                    raise SafetyViolationError("Context structure too deeply nested")
                validated_context[key] = value
            else:
                raise SafetyViolationError(f"Invalid context value type for key: {key}")
        
        return validated_context
    
    @staticmethod
    def _get_nested_structure_depth(obj: Any, current_depth: int = 0) -> int:
        """Calculate the maximum nesting depth of a dictionary or list structure"""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(InputValidator._get_nested_structure_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(InputValidator._get_nested_structure_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self._requests: Dict[str, List[datetime]] = {}
        self._lock = asyncio.Lock()
    
    async def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if request is within rate limit
        
        Args:
            identifier: Unique identifier (e.g., user ID, IP address)
            
        Returns:
            True if within limit, False otherwise
        """
        async with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW_SECONDS)
            
            # Get or create request list for identifier
            if identifier not in self._requests:
                self._requests[identifier] = []
            
            # Remove old requests
            self._requests[identifier] = [
                req_time for req_time in self._requests[identifier]
                if req_time > cutoff
            ]
            
            # Check if within limit
            if len(self._requests[identifier]) >= RATE_LIMIT_REQUESTS:
                return False
            
            # Add current request
            self._requests[identifier].append(now)
            return True
    
    async def cleanup_old_entries(self):
        """Clean up old rate limit entries"""
        async with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW_SECONDS * 2)
            
            # Remove identifiers with no recent requests
            identifiers_to_remove = []
            for identifier, requests in self._requests.items():
                if not requests or max(requests) < cutoff:
                    identifiers_to_remove.append(identifier)
            
            for identifier in identifiers_to_remove:
                del self._requests[identifier]


def sanitize_for_prompt(text: str) -> str:
    """
    Sanitize text for safe inclusion in prompts
    
    Args:
        text: Raw text
        
    Returns:
        Sanitized text safe for prompts
    """
    # Remove potential prompt injection patterns
    sanitized = text
    
    # Replace system-like tokens
    sanitized = re.sub(r'<\|.*?\|>', '[REDACTED]', sanitized)
    sanitized = re.sub(r'\[\[.*?\]\]', '[REDACTED]', sanitized)
    
    # Replace instruction-like patterns
    sanitized = re.sub(
        r'(?:system|instruction|prompt)\s*:', 
        '[REDACTED]:', 
        sanitized, 
        flags=re.IGNORECASE
    )
    
    # Escape quotes and backslashes
    sanitized = sanitized.replace('\\', '\\\\')
    sanitized = sanitized.replace('"', '\\"')
    sanitized = sanitized.replace("'", "\\'")
    
    return sanitized


def hash_session_id(session_id: str) -> str:
    """
    Hash session ID for privacy
    
    Args:
        session_id: Raw session ID
        
    Returns:
        Hashed session ID
    """
    return hashlib.sha256(session_id.encode()).hexdigest()[:16]


def rate_limit(identifier_func):
    """
    Decorator for rate limiting async functions
    
    Args:
        identifier_func: Function that extracts identifier from arguments
    """
    rate_limiter = RateLimiter()
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract identifier
            identifier = identifier_func(*args, **kwargs)
            
            # Check rate limit
            if not await rate_limiter.check_rate_limit(identifier):
                raise SafetyViolationError(
                    "Rate limit exceeded. Please try again later.",
                    ["rate_limit_exceeded"]
                )
            
            # Call original function
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Example usage of rate limit decorator:
# @rate_limit(lambda request: request.client.host)
# async def api_endpoint(request: Request):
#     pass
