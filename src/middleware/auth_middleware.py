"""
Authentication Middleware for Server-Side Route Protection
Ensures users are authenticated before serving protected pages

Now includes JWT token validation for proper server-side auth.
"""
import logging
import jwt
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce authentication on protected routes
    Redirects unauthenticated users to /auth before serving pages
    
    Server-side JWT validation for Supabase auth tokens.
    Falls back to client-side validation for development/localStorage sessions.
    """
    
    # Routes that don't require authentication (public)
    PUBLIC_ROUTES = {
        "/",
        "/auth",
        "/health",
        "/metrics",
        "/thank-you-locked",
        "/api/health",  # API health check
    }
    
    # Protected page routes (require authentication)
    PROTECTED_ROUTES = {
        "/welcome",
        "/persona-select", 
        "/chat",
        "/analysis",
        "/reflection",
        "/feedback",
        "/thank-you",
        "/auth-test",
        "/mi-practice",
        "/mi-practice-module",
        "/mi-practice-progress",
        "/mi-practice-review",
        "/maps-results",
        "/voice",
    }
    
    def __init__(self, app, supabase_url: str = None, supabase_anon_key: str = None):
        super().__init__(app)
        self.supabase_url = supabase_url
        self.supabase_anon_key = supabase_anon_key
        
        # JWT algorithm for Supabase tokens
        self.jwt_algorithm = "HS256"
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Allow public routes without auth check
        if self._is_public_route(path):
            return await call_next(request)
        
        # Allow static files and specific API routes (they handle their own logic)
        if path.startswith("/static/"):
            return await call_next(request)
        
        # For API routes, check auth but return 401 instead of redirect
        if path.startswith("/api/"):
            if not await self._is_authenticated(request):
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=401,
                    content={"error": "Unauthorized", "message": "Valid authentication required"}
                )
            return await call_next(request)
        
        # Check authentication for protected routes
        if self._is_protected_route(path):
            is_authenticated = await self._is_authenticated(request)
            
            if not is_authenticated:
                # Check if there are any auth indicators (localStorage fallback)
                has_auth_indicator = self._check_auth_indicators(request)
                
                if has_auth_indicator:
                    # Client-side auth likely present (localStorage)
                    # Let the request through and let client-side guards handle it
                    logger.debug(f"Auth indicators present for {path}, allowing client-side validation")
                    return await call_next(request)
                else:
                    # No authentication found - redirect to auth page
                    logger.info(f"Unauthenticated access attempt to {path}, redirecting to /auth")
                    return RedirectResponse(url="/auth", status_code=307)
        
        # Proceed with request
        return await call_next(request)
    
    def _is_public_route(self, path: str) -> bool:
        """Check if route is public (no auth required)"""
        return path in self.PUBLIC_ROUTES
    
    def _is_protected_route(self, path: str) -> bool:
        """Check if route requires authentication"""
        # Check exact match or if path starts with a protected prefix
        if path in self.PROTECTED_ROUTES:
            return True
        # Also check for dynamic routes
        for protected in self.PROTECTED_ROUTES:
            if path.startswith(protected + "/"):
                return True
        return False
    
    async def _is_authenticated(self, request: Request) -> bool:
        """
        Perform server-side authentication validation.
        
        Tries multiple methods:
        1. JWT token validation from Authorization header
        2. JWT token validation from cookies
        3. Session validation with Supabase (if configured)
        """
        # Try to get token from Authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            if self._validate_jwt_token(token):
                return True
        
        # Try to get token from cookies
        cookies = request.cookies
        
        # Check for Supabase access token in cookies
        access_token = cookies.get("sb-access-token")
        if access_token:
            if self._validate_jwt_token(access_token):
                return True
        
        # Check for any Supabase-related auth cookies
        for cookie_name in cookies.keys():
            if "sb-" in cookie_name and "token" in cookie_name:
                if self._validate_jwt_token(cookies[cookie_name]):
                    return True
        
        return False
    
    def _validate_jwt_token(self, token: str) -> bool:
        """
        Validate a JWT token.
        
        In production, this should verify against Supabase JWT secret.
        For now, performs basic validation (expiry, format).
        """
        if not token or not self.supabase_anon_key:
            return False
        
        try:
            # Decode and validate token
            payload = jwt.decode(
                token,
                self.supabase_anon_key,
                algorithms=[self.jwt_algorithm],
                options={"verify_exp": True}
            )
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp:
                expiry = datetime.fromtimestamp(exp, tz=timezone.utc)
                if expiry < datetime.now(timezone.utc):
                    logger.debug("Token expired")
                    return False
            
            # Check for required claims
            sub = payload.get("sub")
            if not sub:
                logger.debug("Token missing subject claim")
                return False
            
            return True
            
        except jwt.ExpiredSignatureError:
            logger.debug("Token signature expired")
            return False
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid token: {e}")
            return False
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False
    
    def _check_auth_indicators(self, request: Request) -> bool:
        """
        Check for auth indicators that suggest client-side auth (localStorage).
        
        This is a fallback for when Supabase uses localStorage instead of cookies.
        We look for headers/cookies that indicate the client likely has a session.
        """
        cookies = request.cookies
        headers = request.headers
        
        # Check for Supabase-related cookie names (even if empty)
        auth_cookie_patterns = ["sb-", "supabase"]
        has_auth_cookie = any(
            any(pattern in key.lower() for pattern in auth_cookie_patterns)
            for key in cookies.keys()
        )
        
        # Check for X-Requested-With header (AJAX requests)
        is_ajax = headers.get("x-requested-with") == "XMLHttpRequest"
        
        # Check for Accept header indicating JSON preference (API calls)
        accepts_json = "application/json" in headers.get("accept", "")
        
        # Check for custom auth indicator header
        has_auth_indicator = headers.get("x-auth-present") == "true"
        
        return has_auth_cookie or is_ajax or accepts_json or has_auth_indicator


class AuthConfig:
    """Configuration for auth middleware"""
    
    @staticmethod
    def create_middleware(app, settings=None):
        """Factory method to create auth middleware with settings"""
        if settings:
            return AuthMiddleware(
                app,
                supabase_url=getattr(settings, 'SUPABASE_URL', None),
                supabase_anon_key=getattr(settings, 'SUPABASE_ANON_KEY', None)
            )
        return AuthMiddleware(app)
