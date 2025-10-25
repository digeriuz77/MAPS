"""
Short-term memory service for caching recent conversation messages
Implements verbatim storage of last 10-20 messages per session
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Represents a single conversation message"""
    role: str  # 'user', 'assistant', or 'persona'
    content: str
    timestamp: datetime
    turn_number: int

class ShortTermMemoryService:
    """
    Manages short-term memory for conversations using in-memory cache
    Stores last 15 messages per session for immediate retrieval
    """
    
    def __init__(self, max_messages: int = 15):
        """
        Initialize short-term memory service
        
        Args:
            max_messages: Maximum number of messages to keep per session
        """
        self.max_messages = max_messages
        self.session_memories: Dict[str, List[Message]] = {}
        self._cleanup_interval = 3600  # Clean up every hour
        self._cleanup_task = None
        
        logger.info(f"🧠 Short-term memory initialized (max_messages={max_messages})")
    
    def _ensure_cleanup_task(self):
        """Start cleanup task if not already running"""
        if self._cleanup_task is None or self._cleanup_task.done():
            try:
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            except RuntimeError:
                # No event loop running, cleanup will be manual or on-demand
                pass
    
    async def _periodic_cleanup(self):
        """Periodically clean up old sessions"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_old_sessions()
            except Exception as e:
                logger.error(f"Error in memory cleanup: {e}")
    
    async def _cleanup_old_sessions(self):
        """Remove sessions with no activity in last 6 hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=6)
        sessions_to_remove = []
        
        for session_id, messages in self.session_memories.items():
            if not messages or (messages and messages[-1].timestamp < cutoff_time):
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.session_memories[session_id]
            
        if sessions_to_remove:
            logger.info(f"🧹 Cleaned up {len(sessions_to_remove)} inactive sessions")
    
    def add_message(self, session_id: str, role: str, content: str, turn_number: int = None) -> None:
        """
        Add a new message to session's short-term memory
        
        Args:
            session_id: Session identifier
            role: Message role ('user', 'assistant', 'persona')
            content: Message content
            turn_number: Turn number in conversation
        """
        # Ensure cleanup task is running
        self._ensure_cleanup_task()
        
        if session_id not in self.session_memories:
            self.session_memories[session_id] = []
        
        # Auto-increment turn number if not provided
        if turn_number is None:
            turn_number = len(self.session_memories[session_id]) + 1
        
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            turn_number=turn_number
        )
        
        self.session_memories[session_id].append(message)
        
        # Keep only the last N messages
        if len(self.session_memories[session_id]) > self.max_messages:
            self.session_memories[session_id] = self.session_memories[session_id][-self.max_messages:]
        
        logger.debug(f"📝 Added message to session {session_id}: {role} (turn {turn_number})")
    
    def get_recent_messages(self, session_id: str, limit: int = None) -> List[Dict]:
        """
        Get recent messages for a session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return (default: all cached)
            
        Returns:
            List of message dictionaries in conversation format
        """
        if session_id not in self.session_memories:
            return []
        
        messages = self.session_memories[session_id]
        
        if limit:
            messages = messages[-limit:]
        
        return [
            {
                'role': 'user' if msg.role == 'user' else 'assistant',
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'turn_number': msg.turn_number
            }
            for msg in messages
        ]
    
    def get_conversation_context(self, session_id: str) -> str:
        """
        Get formatted conversation context for LLM prompts
        
        Args:
            session_id: Session identifier
            
        Returns:
            Formatted conversation context string
        """
        messages = self.session_memories.get(session_id, [])
        
        if not messages:
            return "(This is the start of your conversation)"
        
        context_lines = []
        for msg in messages[-10:]:  # Last 10 messages for context
            role_display = "User" if msg.role == 'user' else "You"
            context_lines.append(f"{role_display}: {msg.content}")
        
        return "\n".join(context_lines)
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear all messages for a session
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.session_memories:
            del self.session_memories[session_id]
            logger.info(f"🗑️ Cleared short-term memory for session {session_id}")
    
    def get_session_stats(self, session_id: str) -> Dict:
        """
        Get statistics for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session statistics
        """
        messages = self.session_memories.get(session_id, [])
        
        if not messages:
            return {
                'message_count': 0,
                'user_messages': 0,
                'assistant_messages': 0,
                'first_message_time': None,
                'last_message_time': None,
                'session_duration_minutes': 0
            }
        
        user_count = len([msg for msg in messages if msg.role == 'user'])
        assistant_count = len([msg for msg in messages if msg.role in ['assistant', 'persona']])
        
        first_time = messages[0].timestamp
        last_time = messages[-1].timestamp
        duration = (last_time - first_time).total_seconds() / 60  # minutes
        
        return {
            'message_count': len(messages),
            'user_messages': user_count,
            'assistant_messages': assistant_count,
            'first_message_time': first_time.isoformat(),
            'last_message_time': last_time.isoformat(),
            'session_duration_minutes': round(duration, 2)
        }
    
    def get_all_sessions(self) -> List[str]:
        """
        Get list of all active session IDs
        
        Returns:
            List of session identifiers
        """
        return list(self.session_memories.keys())
    
    def get_memory_usage(self) -> Dict:
        """
        Get memory usage statistics
        
        Returns:
            Dictionary with memory usage stats
        """
        total_sessions = len(self.session_memories)
        total_messages = sum(len(messages) for messages in self.session_memories.values())
        
        return {
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'max_messages_per_session': self.max_messages,
            'average_messages_per_session': round(total_messages / total_sessions, 2) if total_sessions > 0 else 0
        }

# Global instance
short_term_memory = ShortTermMemoryService()
