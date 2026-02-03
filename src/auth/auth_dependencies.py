"""
Authentication Dependencies - DISABLED
All functions return anonymous user - no authentication required
"""
import logging
from typing import Optional
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

class AuthenticatedUser:
    """Represents a user (always anonymous since auth is disabled)"""
    def __init__(self, user_id: str = "anonymous", email: str = "anonymous@example.com", role: str = "FULL"):
        self.user_id = user_id
        self.email = email
        self.role = role

    def is_admin(self) -> bool:
        return True

    def is_full_access(self) -> bool:
        return True

    def is_control_only(self) -> bool:
        return False


# Anonymous user instance
ANONYMOUS_USER = AuthenticatedUser()


async def get_current_user(
    authorization: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> AuthenticatedUser:
    """
    Returns anonymous user - no authentication required
    """
    logger.debug("Auth disabled - returning anonymous user")
    return ANONYMOUS_USER


async def require_full_access(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """
    Always passes - auth is disabled
    """
    return ANONYMOUS_USER


async def require_admin_access(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """
    Always passes - auth is disabled
    """
    return ANONYMOUS_USER


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[AuthenticatedUser]:
    """
    Returns anonymous user - no authentication required
    """
    return ANONYMOUS_USER
