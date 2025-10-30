"""
Authentication Dependencies for FastAPI Routes
Validates Supabase JWT tokens and checks profiles table for user roles
"""
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client

from src.dependencies import get_supabase_client

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

class AuthenticatedUser:
    """Represents an authenticated user with profile data"""
    def __init__(self, user_id: str, email: str, role: str):
        self.user_id = user_id
        self.email = email
        self.role = role

    def is_full_access(self) -> bool:
        """Check if user has FULL role"""
        return self.role == "FULL"

    def is_control_only(self) -> bool:
        """Check if user has CONTROL role (limited access)"""
        return self.role == "CONTROL"


async def get_current_user(
    authorization: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    supabase: Client = Depends(get_supabase_client)
) -> AuthenticatedUser:
    """
    Dependency to get current authenticated user from JWT token

    Validates token with Supabase and fetches user profile from profiles table

    Raises:
        HTTPException 401: If token is invalid or missing
        HTTPException 403: If user profile not found
    """
    # Extract token from Authorization header or HTTPBearer
    token = None
    
    # Debug: Log what we're receiving
    logger.info(f"Authorization header: {authorization}")
    logger.info(f"HTTPBearer credentials: {credentials}")
    
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        logger.info(f"Token extracted from Authorization header: {token[:10]}...")
    elif credentials:
        token = credentials.credentials
        logger.info(f"Token extracted from HTTPBearer: {token[:10]}...")

    if not token:
        logger.warning("No authentication token provided")
        logger.warning(f"Authorization header was: {authorization}")
        logger.warning(f"Credentials were: {credentials}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - missing token"
        )

    try:
        # Verify JWT token with Supabase
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            logger.warning("Invalid or expired token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        user = user_response.user
        user_id = user.id
        email = user.email

        # Fetch user profile from profiles table using user's JWT token
        # Create a user-authenticated client to respect RLS policies
        from supabase import create_client
        from src.config.settings import get_settings
        settings = get_settings()
        
        # Create client with anon key and set user's JWT for RLS
        user_supabase = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_ANON_KEY
        )
        
        # Set the authorization header with user's token
        user_supabase.postgrest.auth(token)
        
        profile_response = user_supabase.table('profiles').select('role').eq('id', user_id).execute()

        if not profile_response.data or len(profile_response.data) == 0:
            logger.error(f"User {user_id} authenticated but no profile found in database")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User profile not found - contact administrator"
            )

        role = profile_response.data[0].get('role', 'CONTROL')

        logger.info(f"Authenticated user: {email} (role: {role})")

        return AuthenticatedUser(user_id=user_id, email=email, role=role)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


async def require_full_access(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """
    Dependency to require FULL role access

    Raises:
        HTTPException 403: If user doesn't have FULL role
    """
    if not current_user.is_full_access():
        logger.warning(f"Access denied for user {current_user.email} with role {current_user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied - FULL role required (you have {current_user.role})"
        )

    return current_user


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    supabase: Client = Depends(get_supabase_client)
) -> Optional[AuthenticatedUser]:
    """
    Dependency to get current user if authenticated, or None if not

    Useful for endpoints that work differently for authenticated users
    but don't strictly require auth
    """
    try:
        return await get_current_user(authorization, credentials, supabase)
    except HTTPException:
        return None
