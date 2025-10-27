"""
Mid-Term Memory Summarization Service
Automatically summarizes conversation segments to preserve context without token bloat
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from src.services.llm_service import LLMService
from src.services.short_term_memory_service import short_term_memory
from src.dependencies import get_supabase_client
from src.utils.logging import track_step

logger = logging.getLogger(__name__)

@dataclass
class ConversationSummary:
    """Represents a summarized conversation segment"""
    summary_id: str
    session_id: str
    persona_id: str
    start_turn: int
    end_turn: int
    message_count: int
    summary_text: str
    key_topics: List[str]
    user_preferences: List[str]
    emotional_moments: List[str]
    trust_progression: str
    created_at: datetime
    importance_score: float = 0.5

@dataclass
class MemoryInsight:
    """Key insight extracted from conversation"""
    insight_type: str  # 'preference', 'emotional_moment', 'topic', 'pattern'
    content: str
    confidence: float
    context: str

class MemorySummarizationService:
    """
    Service for automatically summarizing conversation segments
    Preserves context while reducing token usage for longer conversations
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        self.supabase = get_supabase_client()
        self.summarization_threshold = 10  # Messages before summarization
        self.summary_storage: Dict[str, List[ConversationSummary]] = {}
        
        logger.info("📝 Memory Summarization Service initialized")
    
    async def check_and_summarize(self, session_id: str, persona_id: str) -> Optional[ConversationSummary]:
        """
        Check if session needs summarization and create summary if needed
        
        Args:
            session_id: Session identifier
            persona_id: Persona being conversed with
            
        Returns:
            New summary if created, None otherwise
        """
        # Get current message count from short-term memory
        session_stats = short_term_memory.get_session_stats(session_id)
        if not session_stats or session_stats['message_count'] < self.summarization_threshold:
            return None
        
        # Check if we already have recent summaries
        recent_summaries = await self._get_recent_summaries(session_id)
        
        # Calculate messages since last summary
        last_summary_end = 0
        if recent_summaries:
            last_summary_end = max(s.end_turn for s in recent_summaries)
        
        current_turn = session_stats['message_count'] // 2  # Rough estimate (user + assistant pairs)
        messages_since_summary = current_turn - last_summary_end
        
        if messages_since_summary >= self.summarization_threshold:
            logger.info(f"🔄 Creating summary for session {session_id} ({messages_since_summary} messages since last summary)")
            return await self._create_summary(session_id, persona_id, last_summary_end + 1, current_turn)
        
        return None
    
    async def _get_recent_summaries(self, session_id: str) -> List[ConversationSummary]:
        """Get recent summaries for a session"""
        if session_id in self.summary_storage:
            return self.summary_storage[session_id]
        
        # In production, this would query the database
        # For now, return empty list
        return []
    
    async def _create_summary(self, session_id: str, persona_id: str, 
                            start_turn: int, end_turn: int) -> ConversationSummary:
        """
        Create a conversation summary for the specified turn range
        
        Args:
            session_id: Session identifier
            persona_id: Persona identifier
            start_turn: Starting turn number
            end_turn: Ending turn number
            
        Returns:
            Generated conversation summary
        """
        # Get conversation messages for the range
        async with track_step("fetch_conversation_range", {"session_id": session_id}):
            messages = await self._get_conversation_range(session_id, start_turn, end_turn)
        
        if not messages:
            logger.warning(f"No messages found for session {session_id} range {start_turn}-{end_turn}")
            return None
        
        # Generate summary using LLM
        async with track_step("summarization_llm", {"persona_id": persona_id}):
            summary_data = await self._generate_summary(messages, persona_id)
        
        # Create summary object
        summary = ConversationSummary(
            summary_id=f"{session_id}_{start_turn}_{end_turn}",
            session_id=session_id,
            persona_id=persona_id,
            start_turn=start_turn,
            end_turn=end_turn,
            message_count=len(messages),
            summary_text=summary_data["summary"],
            key_topics=summary_data["topics"],
            user_preferences=summary_data["preferences"],
            emotional_moments=summary_data["emotional_moments"],
            trust_progression=summary_data["trust_progression"],
            created_at=datetime.utcnow(),
            importance_score=summary_data.get("importance_score", 0.5)
        )
        
        # Store summary
        await self._store_summary(summary)

        # Metrics
        try:
            from src.services.metrics_service import metrics
            metrics.record_summary_created()
        except Exception:
            pass
        
        logger.info(f"✅ Created summary for {session_id}: {len(summary.key_topics)} topics, " +
                   f"{len(summary.user_preferences)} preferences, {len(summary.emotional_moments)} emotional moments")
        
        return summary
    
    async def _get_conversation_range(self, session_id: str, start_turn: int, end_turn: int) -> List[Dict]:
        """
        Get conversation messages for a specific turn range
        
        Args:
            session_id: Session identifier
            start_turn: Starting turn number
            end_turn: Ending turn number
            
        Returns:
            List of conversation messages
        """
        # First try short-term memory
        recent_messages = short_term_memory.get_recent_messages(session_id)
        
        if recent_messages:
            # Filter messages by turn range
            relevant_messages = [
                msg for msg in recent_messages
                if start_turn <= msg.get('turn_number', 0) <= end_turn
            ]
            if relevant_messages:
                return relevant_messages
        
        # Fallback to database
        try:
            result = self.supabase.table('conversation_transcripts').select('*').eq(
                'conversation_id', session_id
            ).gte('turn_number', start_turn).lte('turn_number', end_turn).order('turn_number').execute()
            
            if result.data:
                return [
                    {
                        'role': msg['role'],
                        'content': msg['message'],
                        'turn_number': msg['turn_number'],
                        'timestamp': msg['timestamp']
                    }
                    for msg in result.data
                ]
        except Exception as e:
            logger.error(f"Failed to get conversation range from database: {e}")
        
        return []
    
    async def _generate_summary(self, messages: List[Dict], persona_id: str) -> Dict:
        """
        Generate comprehensive summary of conversation messages
        
        Args:
            messages: List of conversation messages
            persona_id: Persona identifier for context
            
        Returns:
            Dictionary with summary components
        """
        # Format messages for LLM
        conversation_text = ""
        for msg in messages:
            role = "User" if msg['role'] == 'user' else f"Character ({persona_id})"
            conversation_text += f"{role}: {msg['content']}\n"
        
        # Create summarization prompt
        summary_prompt = f"""Analyze this conversation segment and create a comprehensive summary.

CONVERSATION:
{conversation_text}

Please provide a structured analysis with:

1. SUMMARY: A brief 2-3 sentence summary of what happened in this conversation segment.

2. KEY_TOPICS: List the main topics discussed (3-5 topics maximum).

3. USER_PREFERENCES: Any preferences, likes, dislikes, or personal information the user revealed.

4. EMOTIONAL_MOMENTS: Significant emotional moments, breakthroughs, or relationship changes.

5. TRUST_PROGRESSION: How did the trust/rapport change during this segment? (building, declining, stable, breakthrough)

6. IMPORTANCE_SCORE: Rate the overall importance of this segment (0.0-1.0) based on:
   - Emotional significance
   - Information revealed  
   - Relationship progression
   - Problem-solving breakthroughs

Format your response as JSON:
{{
  "summary": "Brief summary text...",
  "topics": ["topic1", "topic2", "topic3"],
  "preferences": ["preference1", "preference2"],
  "emotional_moments": ["moment1", "moment2"],
  "trust_progression": "building/declining/stable/breakthrough",
  "importance_score": 0.7
}}"""
        
        try:
            response = await self.llm_service.generate_response(
                prompt=summary_prompt,
                model="gpt-4o-mini",
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=400
            )
            
            # Parse JSON response
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:-3]
            elif response_clean.startswith('```'):
                response_clean = response_clean[3:-3]
            
            summary_data = json.loads(response_clean)
            
            # Validate and set defaults
            required_keys = ['summary', 'topics', 'preferences', 'emotional_moments', 'trust_progression']
            for key in required_keys:
                if key not in summary_data:
                    summary_data[key] = [] if key != 'summary' and key != 'trust_progression' else ""
            
            if 'importance_score' not in summary_data:
                summary_data['importance_score'] = 0.5
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Failed to generate conversation summary: {e}")
            # Return fallback summary
            return {
                "summary": f"Conversation segment with {len(messages)} messages",
                "topics": [],
                "preferences": [],
                "emotional_moments": [],
                "trust_progression": "stable",
                "importance_score": 0.3
            }
    
    async def _store_summary(self, summary: ConversationSummary) -> None:
        """
        Store conversation summary
        
        Args:
            summary: Summary to store
        """
        # Store in memory for immediate use
        if summary.session_id not in self.summary_storage:
            self.summary_storage[summary.session_id] = []
        
        self.summary_storage[summary.session_id].append(summary)
        
        # Keep only last 20 summaries per session
        if len(self.summary_storage[summary.session_id]) > 20:
            self.summary_storage[summary.session_id] = self.summary_storage[summary.session_id][-20:]
        
        # In production, also store in database
        try:
            summary_data = {
                'session_id': summary.session_id,
                'persona_id': summary.persona_id,
                'summary_id': summary.summary_id,
                'start_turn': summary.start_turn,
                'end_turn': summary.end_turn,
                'message_count': summary.message_count,
                'summary_text': summary.summary_text,
                'key_topics': json.dumps(summary.key_topics),
                'user_preferences': json.dumps(summary.user_preferences),
                'emotional_moments': json.dumps(summary.emotional_moments),
                'trust_progression': summary.trust_progression,
                'importance_score': summary.importance_score,
                'created_at': summary.created_at.isoformat()
            }
            
            # Store in conversation_summaries table (would need to create this table)
            logger.debug(f"Would store summary in database: {summary.summary_id}")
            
        except Exception as e:
            logger.error(f"Failed to store summary in database: {e}")
    
    def get_session_summaries(self, session_id: str, limit: int = 10) -> List[ConversationSummary]:
        """
        Get recent summaries for a session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of summaries to return
            
        Returns:
            List of conversation summaries
        """
        if session_id not in self.summary_storage:
            return []
        
        summaries = self.summary_storage[session_id]
        return summaries[-limit:] if limit else summaries
    
    def get_summary_context(self, session_id: str, max_summaries: int = 5) -> str:
        """
        Get formatted summary context for LLM prompts
        
        Args:
            session_id: Session identifier
            max_summaries: Maximum number of summaries to include
            
        Returns:
            Formatted context string
        """
        summaries = self.get_session_summaries(session_id, max_summaries)
        
        if not summaries:
            return "(No conversation history summaries available)"
        
        context_lines = ["CONVERSATION HISTORY SUMMARIES:"]
        
        for summary in summaries:
            context_lines.append(f"\nTurns {summary.start_turn}-{summary.end_turn}:")
            context_lines.append(f"- {summary.summary_text}")
            
            if summary.key_topics:
                context_lines.append(f"- Topics: {', '.join(summary.key_topics)}")
            
            if summary.user_preferences:
                context_lines.append(f"- User preferences: {', '.join(summary.user_preferences)}")
            
            if summary.emotional_moments:
                context_lines.append(f"- Emotional moments: {', '.join(summary.emotional_moments)}")
            
            context_lines.append(f"- Trust progression: {summary.trust_progression}")
        
        return "\n".join(context_lines)
    
    def get_insights_by_type(self, session_id: str, insight_type: str) -> List[str]:
        """
        Get specific type of insights from all summaries
        
        Args:
            session_id: Session identifier
            insight_type: Type of insight ('preferences', 'topics', 'emotional_moments')
            
        Returns:
            List of insights of the specified type
        """
        summaries = self.get_session_summaries(session_id)
        insights = []
        
        for summary in summaries:
            if insight_type == 'preferences':
                insights.extend(summary.user_preferences)
            elif insight_type == 'topics':
                insights.extend(summary.key_topics)
            elif insight_type == 'emotional_moments':
                insights.extend(summary.emotional_moments)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_insights = []
        for insight in insights:
            if insight not in seen:
                seen.add(insight)
                unique_insights.append(insight)
        
        return unique_insights
    
    def get_memory_stats(self) -> Dict:
        """
        Get memory summarization statistics
        
        Returns:
            Dictionary with statistics
        """
        total_sessions = len(self.summary_storage)
        total_summaries = sum(len(summaries) for summaries in self.summary_storage.values())
        
        avg_summaries_per_session = round(total_summaries / total_sessions, 2) if total_sessions > 0 else 0
        
        return {
            'total_sessions_with_summaries': total_sessions,
            'total_summaries_created': total_summaries,
            'avg_summaries_per_session': avg_summaries_per_session,
            'summarization_threshold': self.summarization_threshold
        }
    
    async def create_manual_summary(self, session_id: str, persona_id: str, 
                                  start_turn: int = None, end_turn: int = None) -> Optional[ConversationSummary]:
        """
        Manually create a summary for testing or specific needs
        
        Args:
            session_id: Session identifier
            persona_id: Persona identifier
            start_turn: Starting turn (default: 1)
            end_turn: Ending turn (default: current turn)
            
        Returns:
            Created summary or None if failed
        """
        if start_turn is None:
            start_turn = 1
        
        if end_turn is None:
            session_stats = short_term_memory.get_session_stats(session_id)
            end_turn = session_stats.get('message_count', 10) // 2 if session_stats else 5
        
        return await self._create_summary(session_id, persona_id, start_turn, end_turn)

# Global instance
memory_summarization_service = MemorySummarizationService()