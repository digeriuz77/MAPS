"""
Application dependencies and shared resources
"""

import os
import logging
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from supabase import create_client, Client
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.services.mi_module_service import MIModuleService
    from src.services.mi_attempt_service import MIAttemptService
    from src.services.mi_progress_service import MIProgressService

@dataclass
class AppState:
    """Application state container"""
    is_initialized: bool = False
    supabase_client: Optional[Client] = None
    # MI Practice module services (initialized on demand)
    mi_module_service: Optional["MIModuleService"] = field(default=None, repr=False)
    mi_attempt_service: Optional["MIAttemptService"] = field(default=None, repr=False)
    mi_progress_service: Optional["MIProgressService"] = field(default=None, repr=False)

# Global app state
_app_state = AppState()

def get_app_state() -> AppState:
    """Get application state"""
    return _app_state

def get_supabase_client() -> Client:
    """
    Get Supabase client instance
    
    Returns:
        Configured Supabase client
    """
    if _app_state.supabase_client is not None:
        return _app_state.supabase_client
    
    settings = get_settings()
    
    # Get Supabase credentials from environment
    # Use SERVICE_ROLE_KEY for backend to bypass RLS
    supabase_url = os.getenv("SUPABASE_URL") or settings.SUPABASE_URL
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    
    if not supabase_url or not supabase_key:
        raise RuntimeError("Supabase credentials not found in environment variables")
    
    try:
        client = create_client(supabase_url, supabase_key)
        _app_state.supabase_client = client
        logger.info("Supabase client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise RuntimeError(f"Supabase client initialization failed: {e}")


# Re-export get_current_user for backward compatibility
# Other modules import this from src.dependencies
try:
    from src.auth import get_current_user
except ImportError:
    # Fallback if auth module not available
    get_current_user = None
    logger.warning("Could not import get_current_user from src.auth")


# ============================================
# MI PRACTICE MODULE DEPENDENCIES
# ============================================
# TYPE_CHECKING imports are at the top of the file

def get_mi_module_service() -> "MIModuleService":
    """
    Get MI Module Service instance.
    
    Lazily initializes the service on first call.
    """
    if _app_state.mi_module_service is None:
        from src.services.mi_module_service import MIModuleService
        _app_state.mi_module_service = MIModuleService(get_supabase_client())
        logger.info("MI Module Service initialized")
    return _app_state.mi_module_service

def get_mi_attempt_service() -> "MIAttemptService":
    """
    Get MI Attempt Service instance.
    
    Lazily initializes the service on first call.
    """
    if _app_state.mi_attempt_service is None:
        from src.services.mi_attempt_service import MIAttemptService
        _app_state.mi_attempt_service = MIAttemptService(get_supabase_client())
        logger.info("MI Attempt Service initialized")
    return _app_state.mi_attempt_service

def get_mi_progress_service() -> "MIProgressService":
    """
    Get MI Progress Service instance.
    
    Lazily initializes the service on first call.
    """
    if _app_state.mi_progress_service is None:
        from src.services.mi_progress_service import MIProgressService
        _app_state.mi_progress_service = MIProgressService(get_supabase_client())
        logger.info("MI Progress Service initialized")
    return _app_state.mi_progress_service

# ============================================
# METRICS SERVICE DEPENDENCY
# ============================================

def get_metrics_service():
    """
    Get metrics service instance with database integration.
    
    Lazily initializes the service with Supabase connection.
    """
    from src.services.metrics_service import get_metrics_service as get_metrics
    return get_metrics(get_supabase_client())