"""
Application dependencies and shared resources
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass
from supabase import create_client, Client
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

@dataclass
class AppState:
    """Application state container"""
    is_initialized: bool = False
    supabase_client: Optional[Client] = None

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
    supabase_url = os.getenv("SUPABASE_URL") or settings.SUPABASE_URL
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or settings.SUPABASE_ANON_KEY
    
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