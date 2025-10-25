"""
Memory Scoring System
Intelligent scoring and retrieval of memories using relevance, recency, and importance
"""

import logging
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from src.services.short_term_memory_service import short_term_memory
from src.services.memory_summarization_service import memory_summarization_service, ConversationSummary
from src.services.character_vector_service import character_vector_service, CharacterMemory

logger = logging.getLogger(__name__)

@dataclass
class ScoredMemory:
    """Memory item with calculated relevance score"""
    memory_id: str
    content: str
    memory_type: str  # 'short_term', 'summary', 'character_knowledge'
    relevance_score: float  # 0.0-1.0
    recency_score: float    # 0.0-1.0  
    importance_score: float # 0.0-1.0
    final_score: float      # Weighted combination
    source_data: Dict      # Original data
    created_at: datetime
    
@dataclass
class RetrievalContext:
    """Context for memory retrieval"""
    user_input: str
    session_id: str
    persona_id: str
    trust_level: float
    interaction_quality: str
    max_memories: int = 10

class MemoryScoringService:
    """
    Service for scoring and retrieving memories based on relevance, recency, and importance
    Implements weighted scoring: Relevance (60%), Recency (25%), Importance (15%)
    """
    
    def __init__(self):
        # Scoring weights
        self.relevance_weight = 0.60
        self.recency_weight = 0.25
        self.importance_weight = 0.15
        
        # Recency decay parameters
        self.recency_half_life_hours = 24  # Hours for recency to decay to 50%
        
        logger.info("🧮 Memory Scoring Service initialized")
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text for relevance matching
        
        Args:
            text: Input text
            
        Returns:
            List of keywords
        """
        # Remove punctuation and convert to lowercase
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Split into words and filter out common words
        words = clean_text.split()
        
        # Simple stopword filtering
        stopwords = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 
            'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him',
            'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
            'itself', 'they', 'them', 'their', 'theirs', 'themselves',
            'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
            'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
            'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while',
            'of', 'at', 'by', 'for', 'with', 'through', 'during', 'before',
            'after', 'above', 'below', 'up', 'down', 'in', 'out', 'on', 'off',
            'over', 'under', 'again', 'further', 'then', 'once'
        }
        
        keywords = [word for word in words if len(word) > 2 and word not in stopwords]
        
        # Return unique keywords, preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:20]  # Limit to top 20 keywords
    
    def calculate_relevance_score(self, memory_content: str, user_input: str, 
                                context_keywords: List[str] = None) -> float:
        """
        Calculate relevance score between memory content and user input
        
        Args:
            memory_content: Content of the memory
            user_input: Current user input
            context_keywords: Additional context keywords
            
        Returns:
            Relevance score (0.0-1.0)
        """
        # Extract keywords from both texts
        memory_keywords = set(self.extract_keywords(memory_content))
        input_keywords = set(self.extract_keywords(user_input))
        
        # Add context keywords if provided
        if context_keywords:
            input_keywords.update(keyword.lower() for keyword in context_keywords)
        
        if not memory_keywords or not input_keywords:
            return 0.0
        
        # Calculate keyword overlap
        overlap = memory_keywords.intersection(input_keywords)
        keyword_score = len(overlap) / max(len(memory_keywords), len(input_keywords))
        
        # Calculate semantic similarity using sequence matching
        similarity = SequenceMatcher(None, memory_content.lower(), user_input.lower()).ratio()
        
        # Combine scores with weights
        final_relevance = (keyword_score * 0.7) + (similarity * 0.3)
        
        return min(1.0, final_relevance)
    
    def calculate_recency_score(self, created_at: datetime) -> float:
        """
        Calculate recency score with exponential decay
        
        Args:
            created_at: When the memory was created
            
        Returns:
            Recency score (0.0-1.0)
        """
        now = datetime.utcnow()
        hours_ago = (now - created_at).total_seconds() / 3600
        
        # Exponential decay: score = e^(-λt) where λ = ln(2) / half_life
        decay_constant = math.log(2) / self.recency_half_life_hours
        recency_score = math.exp(-decay_constant * hours_ago)
        
        return min(1.0, recency_score)
    
    def score_memory(self, memory_content: str, memory_type: str, created_at: datetime,
                    importance: float, user_input: str, context_keywords: List[str] = None) -> float:
        """
        Calculate final weighted score for a memory
        
        Args:
            memory_content: Content of the memory
            memory_type: Type of memory
            created_at: When memory was created  
            importance: Importance score (0.0-1.0)
            user_input: Current user input
            context_keywords: Additional context keywords
            
        Returns:
            Final weighted score (0.0-1.0)
        """
        relevance = self.calculate_relevance_score(memory_content, user_input, context_keywords)
        recency = self.calculate_recency_score(created_at)
        
        # Apply memory type adjustments
        type_multipliers = {
            'short_term': 1.0,      # No adjustment
            'summary': 0.9,         # Slightly lower as summaries are less specific
            'character_knowledge': 1.1  # Slightly higher as character knowledge is important
        }
        type_multiplier = type_multipliers.get(memory_type, 1.0)
        
        # Calculate weighted final score
        final_score = (
            (relevance * self.relevance_weight) +
            (recency * self.recency_weight) +
            (importance * self.importance_weight)
        ) * type_multiplier
        
        return min(1.0, final_score)
    
    async def retrieve_relevant_memories(self, context: RetrievalContext) -> List[ScoredMemory]:
        """
        Retrieve and score memories from all sources based on relevance
        
        Args:
            context: Retrieval context with user input and session info
            
        Returns:
            List of scored memories, sorted by relevance
        """
        scored_memories = []
        
        # Extract keywords from user input for context
        context_keywords = self.extract_keywords(context.user_input)
        
        # 1. Get short-term memories
        short_term_memories = self._get_short_term_memories(context, context_keywords)
        scored_memories.extend(short_term_memories)
        
        # 2. Get conversation summaries
        summary_memories = self._get_summary_memories(context, context_keywords)
        scored_memories.extend(summary_memories)
        
        # 3. Get character knowledge
        character_memories = self._get_character_memories(context, context_keywords)
        scored_memories.extend(character_memories)
        
        # Sort by final score (highest first)
        scored_memories.sort(key=lambda x: x.final_score, reverse=True)
        
        # Return top N memories
        top_memories = scored_memories[:context.max_memories]
        
        if top_memories:
            logger.info(f"🎯 Retrieved {len(top_memories)} relevant memories " +
                       f"(avg score: {sum(m.final_score for m in top_memories)/len(top_memories):.3f})")
        
        return top_memories
    
    def _get_short_term_memories(self, context: RetrievalContext, 
                               context_keywords: List[str]) -> List[ScoredMemory]:
        """Get and score short-term memories"""
        scored_memories = []
        
        # Get recent messages from short-term memory
        recent_messages = short_term_memory.get_recent_messages(context.session_id)
        
        for msg in recent_messages:
            # Only score messages from the persona (not user messages)
            if msg['role'] != 'user':
                content = msg['content']
                created_at = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                
                final_score = self.score_memory(
                    memory_content=content,
                    memory_type='short_term',
                    created_at=created_at,
                    importance=0.5,  # Default importance for short-term
                    user_input=context.user_input,
                    context_keywords=context_keywords
                )
                
                if final_score > 0.1:  # Only include if somewhat relevant
                    scored_memories.append(ScoredMemory(
                        memory_id=f"short_term_{msg['turn_number']}",
                        content=content,
                        memory_type='short_term',
                        relevance_score=self.calculate_relevance_score(content, context.user_input, context_keywords),
                        recency_score=self.calculate_recency_score(created_at),
                        importance_score=0.5,
                        final_score=final_score,
                        source_data=msg,
                        created_at=created_at
                    ))
        
        return scored_memories
    
    def _get_summary_memories(self, context: RetrievalContext,
                            context_keywords: List[str]) -> List[ScoredMemory]:
        """Get and score conversation summaries"""
        scored_memories = []
        
        # Get conversation summaries
        summaries = memory_summarization_service.get_session_summaries(context.session_id)
        
        for summary in summaries:
            # Score the summary text
            final_score = self.score_memory(
                memory_content=summary.summary_text,
                memory_type='summary', 
                created_at=summary.created_at,
                importance=summary.importance_score,
                user_input=context.user_input,
                context_keywords=context_keywords
            )
            
            # Also check key topics for relevance
            topics_text = ' '.join(summary.key_topics)
            topic_relevance = self.calculate_relevance_score(topics_text, context.user_input, context_keywords)
            
            # Use higher of summary or topic relevance
            if topic_relevance > final_score:
                final_score = topic_relevance * 0.8  # Slight discount for topic-only relevance
            
            if final_score > 0.1:  # Only include if somewhat relevant
                scored_memories.append(ScoredMemory(
                    memory_id=summary.summary_id,
                    content=summary.summary_text,
                    memory_type='summary',
                    relevance_score=self.calculate_relevance_score(summary.summary_text, context.user_input, context_keywords),
                    recency_score=self.calculate_recency_score(summary.created_at),
                    importance_score=summary.importance_score,
                    final_score=final_score,
                    source_data=summary,
                    created_at=summary.created_at
                ))
        
        return scored_memories
    
    def _get_character_memories(self, context: RetrievalContext,
                              context_keywords: List[str]) -> List[ScoredMemory]:
        """Get and score character knowledge memories"""
        scored_memories = []
        
        # Get character memories from vector service
        character_memories = character_vector_service.get_relevant_memories(
            persona_id=context.persona_id,
            context_tags=context_keywords,
            trust_level=context.trust_level,
            limit=15  # Get more candidates for scoring
        )
        
        for memory in character_memories:
            # Character memories don't have timestamps, use current time with offset
            created_at = datetime.utcnow() - timedelta(hours=1)  # Treat as recent but not immediate
            
            final_score = self.score_memory(
                memory_content=memory.content,
                memory_type='character_knowledge',
                created_at=created_at,
                importance=memory.emotional_weight,  # Use emotional weight as importance
                user_input=context.user_input,
                context_keywords=context_keywords
            )
            
            if final_score > 0.1:  # Only include if somewhat relevant
                scored_memories.append(ScoredMemory(
                    memory_id=memory.memory_id,
                    content=memory.content,
                    memory_type='character_knowledge',
                    relevance_score=self.calculate_relevance_score(memory.content, context.user_input, context_keywords),
                    recency_score=self.calculate_recency_score(created_at),
                    importance_score=memory.emotional_weight,
                    final_score=final_score,
                    source_data=memory,
                    created_at=created_at
                ))
        
        return scored_memories
    
    def format_memories_for_prompt(self, memories: List[ScoredMemory], max_length: int = 500) -> str:
        """
        Format scored memories for inclusion in LLM prompts
        
        Args:
            memories: List of scored memories
            max_length: Maximum character length for output
            
        Returns:
            Formatted memory context string
        """
        if not memories:
            return "(No relevant memories found)"
        
        context_lines = []
        current_length = 0
        
        for memory in memories:
            # Format memory with score indicator
            if memory.final_score >= 0.7:
                relevance_indicator = "🔥"  # High relevance
            elif memory.final_score >= 0.4:
                relevance_indicator = "💡"  # Medium relevance  
            else:
                relevance_indicator = "💭"  # Lower relevance
            
            memory_line = f"{relevance_indicator} {memory.content}"
            
            if current_length + len(memory_line) > max_length:
                break
            
            context_lines.append(memory_line)
            current_length += len(memory_line)
        
        if context_lines:
            return "RELEVANT MEMORIES:\n" + "\n".join(context_lines)
        else:
            return "(No relevant memories within context limit)"
    
    def get_scoring_stats(self) -> Dict:
        """
        Get memory scoring system statistics
        
        Returns:
            Dictionary with scoring configuration and stats
        """
        return {
            'scoring_weights': {
                'relevance': self.relevance_weight,
                'recency': self.recency_weight,
                'importance': self.importance_weight
            },
            'recency_half_life_hours': self.recency_half_life_hours,
            'memory_sources': ['short_term', 'summaries', 'character_knowledge'],
            'relevance_methods': ['keyword_overlap', 'semantic_similarity']
        }
    
    async def debug_scoring(self, context: RetrievalContext) -> Dict:
        """
        Debug function to show detailed scoring breakdown
        
        Args:
            context: Retrieval context
            
        Returns:
            Detailed scoring information
        """
        memories = await self.retrieve_relevant_memories(context)
        
        debug_info = {
            'user_input': context.user_input,
            'extracted_keywords': self.extract_keywords(context.user_input),
            'total_memories_scored': len(memories),
            'scoring_breakdown': []
        }
        
        for memory in memories[:5]:  # Top 5 for debugging
            debug_info['scoring_breakdown'].append({
                'memory_id': memory.memory_id,
                'content': memory.content[:100] + "..." if len(memory.content) > 100 else memory.content,
                'memory_type': memory.memory_type,
                'scores': {
                    'relevance': round(memory.relevance_score, 3),
                    'recency': round(memory.recency_score, 3),
                    'importance': round(memory.importance_score, 3),
                    'final': round(memory.final_score, 3)
                }
            })
        
        return debug_info

# Global instance
memory_scoring_service = MemoryScoringService()