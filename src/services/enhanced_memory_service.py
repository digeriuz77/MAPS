"""
Enhanced Memory System for Authentic Persona Behavior
Provides rich, contextual memory that makes Mary feel like a real person
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from src.dependencies import get_supabase_client
from src.services.model_provider_service import multi_model_service

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """A single memory with context and importance"""
    content: str
    importance: float  # 1.0-10.0
    emotional_context: str
    mi_quality_context: float
    created_at: datetime
    memory_type: str  # "interaction", "insight", "relationship_change", "personal_detail"
    references: List[str] = None  # What this memory references (Tommy, work, etc.)

@dataclass
class ConversationContext:
    """Rich context about the conversation state"""
    user_mi_style: str  # "empathetic", "directive", "judgmental", etc.
    relationship_stage: str  # "initial", "building_trust", "deep_sharing", "resistant"
    topics_discussed: List[str]
    emotional_journey: List[str]  # Track Mary's emotional progression
    trust_level: float  # 1.0-10.0
    recent_triggers: List[str]  # What recently made Mary defensive/open

class EnhancedMemoryService:
    """
    Production-ready memory system that makes Mary authentically human:
    
    1. Contextual Memory: Remembers not just what was said, but emotional context
    2. Relationship Tracking: Builds understanding of user's approach over time  
    3. Personal Continuity: References Tommy, work situations naturally
    4. Emotional Progression: Tracks Mary's changing feelings toward user
    5. Cross-Session Persistence: Mary remembers previous conversations
    """

    def __init__(self):
        self.supabase_client = get_supabase_client()
        
        # Mary's core personal context that should inform memory formation
        self.personal_context = {
            "work_situation": {
                "role": "Operations manager at mid-sized logistics company",
                "recent_events": ["difficult performance review", "attention to detail feedback"],
                "concerns": ["job security", "work-life balance", "being a good employee"],
                "daily_reality": ["staying late to catch up", "feeling overwhelmed", "pressure to perform"]
            },
            "family_life": {
                "tommy": {
                    "age": 9,
                    "needs": ["homework help every night", "attention", "stability"],
                    "mary_concerns": ["being a good mother", "balancing time", "providing security"]
                },
                "single_parent_challenges": ["no backup support", "guilt about work hours", "financial pressure"]
            },
            "emotional_patterns": {
                "triggers": ["criticism", "advice-giving", "judgment about parenting"],
                "openness_cues": ["feeling heard", "non-judgmental support", "empathy"],
                "core_fears": ["failing at work", "failing as mother", "being alone", "judgment"]
            }
        }

    async def form_memory_from_interaction(
        self,
        conversation_id: str,
        user_message: str,
        mary_response: str,
        mi_analysis: Dict[str, Any],
        conversation_context: Optional[ConversationContext] = None
    ) -> List[MemoryEntry]:
        """
        Form rich, contextual memories from interaction
        Returns multiple memory entries with different importance levels
        """
        
        memories = []
        
        # 1. Interaction Memory (what happened)
        interaction_memory = await self._create_interaction_memory(
            user_message, mary_response, mi_analysis
        )
        memories.append(interaction_memory)
        
        # 2. Relationship Memory (how it affected trust/openness)
        if mi_analysis.get('empathy_score', 0) > 7 or mi_analysis.get('empathy_score', 0) < 4:
            relationship_memory = await self._create_relationship_memory(
                user_message, mi_analysis, conversation_context
            )
            memories.append(relationship_memory)
        
        # 3. Personal Insight Memory (what Mary learned about herself)
        if mi_analysis.get('openness_change') == 'increase':
            insight_memory = await self._create_insight_memory(
                user_message, mary_response, conversation_context
            )
            if insight_memory:
                memories.append(insight_memory)
        
        # Store memories in database
        await self._store_memories(conversation_id, memories)
        
        return memories

    async def _create_interaction_memory(
        self,
        user_message: str,
        mary_response: str,
        mi_analysis: Dict[str, Any]
    ) -> MemoryEntry:
        """Create memory of the actual interaction"""
        
        # Determine importance based on MI quality and emotional impact
        importance = 3.0  # Base importance
        
        empathy_score = mi_analysis.get('empathy_score', 5)
        if empathy_score >= 8:
            importance += 3.0  # High empathy = important positive memory
        elif empathy_score <= 3:
            importance += 2.0  # Low empathy = important negative memory
        
        if mi_analysis.get('resistance_triggered', False):
            importance += 2.0  # Resistance = important memory
        
        # Emotional context
        emotional_context = "neutral"
        if empathy_score >= 8:
            emotional_context = "appreciated, felt heard"
        elif empathy_score <= 3:
            emotional_context = "defensive, misunderstood"
        elif mi_analysis.get('resistance_triggered', False):
            emotional_context = "frustrated, pushed"
        
        # Extract key references
        references = self._extract_references(user_message + " " + mary_response)
        
        return MemoryEntry(
            content=f"User approach: {user_message[:100]}... My response: {mary_response[:100]}...",
            importance=min(importance, 10.0),
            emotional_context=emotional_context,
            mi_quality_context=empathy_score,
            created_at=datetime.now(),
            memory_type="interaction",
            references=references
        )

    async def _create_relationship_memory(
        self,
        user_message: str,
        mi_analysis: Dict[str, Any],
        conversation_context: Optional[ConversationContext]
    ) -> MemoryEntry:
        """Create memory about relationship progression"""
        
        empathy_score = mi_analysis.get('empathy_score', 5)
        
        if empathy_score >= 8:
            content = "This person really listens to me and tries to understand. I feel less alone when talking to them."
            emotional_context = "trusting, grateful"
            importance = 7.0
        elif empathy_score <= 3:
            content = "This person doesn't seem to get what I'm going through. They judge rather than listen."
            emotional_context = "disappointed, guarded"
            importance = 6.0
        else:
            return None  # Don't create relationship memory for neutral interactions
        
        return MemoryEntry(
            content=content,
            importance=importance,
            emotional_context=emotional_context,
            mi_quality_context=empathy_score,
            created_at=datetime.now(),
            memory_type="relationship_change",
            references=["trust", "relationship"]
        )

    async def _create_insight_memory(
        self,
        user_message: str,
        mary_response: str,
        conversation_context: Optional[ConversationContext]
    ) -> Optional[MemoryEntry]:
        """Create memory of personal insights Mary gained"""
        
        # Use AI to identify if Mary had a personal insight
        insight_prompt = f"""
        Based on this interaction, did Mary (stressed single mother, operations manager) gain any personal insight about herself, her situation, or her feelings?

        User: {user_message}
        Mary: {mary_response}

        Respond with JSON:
        {{
            "has_insight": true/false,
            "insight_content": "What Mary realized about herself",
            "importance": 1-10
        }}

        Only identify genuine personal insights, not just general conversation.
        """
        
        try:
            response = await multi_model_service.generate_response(
                prompt=insight_prompt,
                model="gpt-4.1-nano",  # Fast processing for memory tasks
                use_case="memory_formation",
                temperature=0.3,
                max_tokens=100  # Keep concise for speed
            )
            
            insight_data = json.loads(response.content)
            
            if insight_data.get('has_insight', False):
                return MemoryEntry(
                    content=insight_data['insight_content'],
                    importance=float(insight_data.get('importance', 5)),
                    emotional_context="reflective, self-aware",
                    mi_quality_context=8.0,  # Insights come from good interactions
                    created_at=datetime.now(),
                    memory_type="insight",
                    references=["self-awareness", "personal growth"]
                )
        
        except Exception as e:
            logger.warning(f"Insight generation failed: {e}")
        
        return None

    def _extract_references(self, text: str) -> List[str]:
        """Extract what this memory references (Tommy, work, etc.)"""
        references = []
        text_lower = text.lower()
        
        # Family references
        if any(word in text_lower for word in ["tommy", "son", "child", "homework", "parenting"]):
            references.append("tommy")
        
        # Work references  
        if any(word in text_lower for word in ["work", "job", "boss", "performance", "review", "company"]):
            references.append("work")
        
        # Emotional references
        if any(word in text_lower for word in ["stress", "overwhelm", "pressure", "anxiety"]):
            references.append("stress")
        
        if any(word in text_lower for word in ["trust", "listen", "understand", "support"]):
            references.append("support")
        
        return references

    async def _store_memories(self, conversation_id: str, memories: List[MemoryEntry]):
        """Store memories in Supabase with full context"""
        
        try:
            for memory in memories:
                self.supabase_client.table('enhanced_memories').insert({
                    'conversation_id': conversation_id,
                    'content': memory.content,
                    'importance': memory.importance,
                    'emotional_context': memory.emotional_context,
                    'mi_quality_context': memory.mi_quality_context,
                    'memory_type': memory.memory_type,
                    'references': memory.references,
                    'created_at': memory.created_at.isoformat()
                }).execute()
                
        except Exception as e:
            logger.error(f"Failed to store memories: {e}")

    async def get_relevant_memories(
        self,
        conversation_id: str,
        current_topic: str,
        limit: int = 5
    ) -> List[MemoryEntry]:
        """Get memories relevant to current conversation"""
        
        try:
            # Get recent high-importance memories
            result = self.supabase_client.table('enhanced_memories').select('*').eq(
                'conversation_id', conversation_id
            ).gte('importance', 5.0).order('created_at', desc=True).limit(limit).execute()
            
            memories = []
            for row in result.data:
                memories.append(MemoryEntry(
                    content=row['content'],
                    importance=row['importance'],
                    emotional_context=row['emotional_context'],
                    mi_quality_context=row['mi_quality_context'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    memory_type=row['memory_type'],
                    references=row.get('references', [])
                ))
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []

    async def get_conversation_context(self, conversation_id: str) -> ConversationContext:
        """Build rich conversation context from memory"""
        
        try:
            # Get conversation history
            result = self.supabase_client.table('mi_analysis').select(
                'empathy_score, resistance_triggered, created_at'
            ).eq('conversation_id', conversation_id).order('created_at').execute()
            
            if not result.data:
                return ConversationContext(
                    user_mi_style="unknown",
                    relationship_stage="initial",
                    topics_discussed=[],
                    emotional_journey=["cautious"],
                    trust_level=5.0,
                    recent_triggers=[]
                )
            
            # Analyze MI style pattern
            empathy_scores = [r['empathy_score'] for r in result.data]
            avg_empathy = sum(empathy_scores) / len(empathy_scores)
            
            if avg_empathy >= 8:
                user_mi_style = "empathetic"
                trust_level = 8.0
            elif avg_empathy >= 6:
                user_mi_style = "supportive"
                trust_level = 6.0
            elif avg_empathy <= 3:
                user_mi_style = "directive"
                trust_level = 3.0
            else:
                user_mi_style = "mixed"
                trust_level = 5.0
            
            # Determine relationship stage
            total_turns = len(result.data)
            recent_resistance = sum(1 for r in result.data[-3:] if r.get('resistance_triggered'))
            
            if recent_resistance >= 2:
                relationship_stage = "resistant"
            elif avg_empathy >= 7 and total_turns >= 4:
                relationship_stage = "deep_sharing"
            elif avg_empathy >= 6 and total_turns >= 2:
                relationship_stage = "building_trust"
            else:
                relationship_stage = "initial"
            
            return ConversationContext(
                user_mi_style=user_mi_style,
                relationship_stage=relationship_stage,
                topics_discussed=["work_stress", "parenting", "performance_review"],  # Would extract from content
                emotional_journey=["cautious", "warming_up"] if avg_empathy > 6 else ["cautious", "defensive"],
                trust_level=trust_level,
                recent_triggers=["criticism"] if recent_resistance > 0 else []
            )
            
        except Exception as e:
            logger.error(f"Failed to build conversation context: {e}")
            return ConversationContext(
                user_mi_style="unknown",
                relationship_stage="initial", 
                topics_discussed=[],
                emotional_journey=["cautious"],
                trust_level=5.0,
                recent_triggers=[]
            )

    async def generate_memory_informed_response_context(
        self,
        conversation_id: str,
        current_message: str
    ) -> str:
        """Generate memory context to inform Mary's response"""
        
        memories = await self.get_relevant_memories(conversation_id, current_message)
        context = await self.get_conversation_context(conversation_id)
        
        if not memories:
            # Require memories to exist in Supabase
            raise RuntimeError(
                f"No memories found for conversation {conversation_id}. "
                "Ensure Supabase persona_memories table is populated."
            )
        
        memory_context = f"Based on our conversations:\n"
        
        # Relationship context
        memory_context += f"- I feel {context.user_mi_style} when talking to this person\n"
        memory_context += f"- Our relationship stage: {context.relationship_stage}\n"
        memory_context += f"- Trust level: {context.trust_level}/10\n"
        
        # Key memories
        memory_context += "\\nKey memories:\\n"
        for memory in memories[:3]:  # Top 3 memories
            memory_context += f"- {memory.content} (felt: {memory.emotional_context})\\n"
        
        return memory_context

# Global instance
enhanced_memory_service = EnhancedMemoryService()