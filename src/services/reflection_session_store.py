"""
Simple session store for reflection coaches
Maintains coach state between API requests
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from src.services.guided_reflection_service import GuidedReflectionService

logger = logging.getLogger(__name__)

class ReflectionSessionStore:
    """In-memory session store for reflection coaches"""
    
    def __init__(self):
        self._sessions: Dict[str, GuidedReflectionService] = {}
        self._last_cleanup = datetime.now()
        self.session_timeout = timedelta(hours=2)  # Sessions expire after 2 hours
        
    def get_or_create_session(self, session_id: str) -> GuidedReflectionService:
        """Get existing session or create new one"""
        # Clean up old sessions periodically
        if datetime.now() - self._last_cleanup > timedelta(minutes=30):
            self._cleanup_expired_sessions()
            
        if session_id in self._sessions:
            logger.info(f"Retrieved existing session: {session_id}")
            return self._sessions[session_id]
        else:
            logger.info(f"Creating new reflection session: {session_id}")
            service = GuidedReflectionService()
            self._sessions[session_id] = service
            return service
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions from memory"""
        current_time = datetime.now()
        expired = []
        
        # Note: In a real implementation, we'd track last access time
        # For now, we'll just limit total sessions
        if len(self._sessions) > 100:
            # Remove oldest sessions if we have too many
            sorted_sessions = sorted(self._sessions.items(), 
                                   key=lambda x: getattr(x[1], 'created_at', current_time))
            for session_id, _ in sorted_sessions[:50]:  # Remove 50 oldest
                del self._sessions[session_id]
                
        self._last_cleanup = current_time
        logger.info(f"Session cleanup complete. Active sessions: {len(self._sessions)}")

# Singleton instance
_session_store: Optional[ReflectionSessionStore] = None

def get_session_store() -> ReflectionSessionStore:
    """Get or create the session store singleton"""
    global _session_store
    if _session_store is None:
        _session_store = ReflectionSessionStore()
    return _session_store
