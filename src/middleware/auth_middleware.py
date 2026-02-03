"""
Authentication Middleware - DISABLED
All routes are public, no authentication required.
"""
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Pass-through middleware - no authentication checks.
    All routes are public.
    """

    def __init__(self, app, supabase_url: str = None, supabase_anon_key: str = None):
        super().__init__(app)
        # Accept but ignore these parameters for backwards compatibility

    async def dispatch(self, request: Request, call_next):
        # Pass through all requests without any auth check
        return await call_next(request)
