"""
Advanced caching service for MITI analysis results
"""
import hashlib
import json
import logging
from typing import Dict, Optional
from .types import (
    ParsedTurn, ConversationContext, CompleteAnalysisResult, 
    SpeakerIdentifierHints
)

logger = logging.getLogger(__name__)

class AnalysisCache:
    """
    In-memory cache for analysis results with intelligent cache key generation.
    In production, this should be replaced with Redis or similar persistent cache.
    """
    
    def __init__(self, max_size: int = 100):
        self._cache: Dict[str, CompleteAnalysisResult] = {}
        self.max_size = max_size
        logger.info(f"Analysis cache initialized with max size: {max_size}")
    
    def _generate_cache_key(
        self, 
        parsed_turns: list[ParsedTurn], 
        context: ConversationContext, 
        speaker_identifiers: SpeakerIdentifierHints
    ) -> str:
        """Generate a unique cache key based on turns, context, and speaker IDs"""
        # Create turn content hash
        turn_content = "||".join([
            f"{turn.speaker.value}:{turn.text}" 
            for turn in parsed_turns
        ])
        
        # Create context content
        context_content = (
            f"{context.practitioner_role}|"
            f"{context.client_role}|"
            f"{context.scenario_description}"
        )
        
        # Create speaker identifier content
        speaker_id_content = (
            f"P:{speaker_identifiers.practitioner_identifier_hint or 'null'}|"
            f"C:{speaker_identifiers.client_identifier_hint or 'null'}"
        )
        
        # Combine all components
        full_content = f"turns[{turn_content}]context[{context_content}]ids[{speaker_id_content}]"
        
        # Generate SHA-256 hash for consistent key length
        return hashlib.sha256(full_content.encode('utf-8')).hexdigest()[:32]
    
    def get(
        self, 
        parsed_turns: list[ParsedTurn], 
        context: ConversationContext, 
        speaker_identifiers: SpeakerIdentifierHints
    ) -> Optional[CompleteAnalysisResult]:
        """Retrieve cached analysis result"""
        cache_key = self._generate_cache_key(parsed_turns, context, speaker_identifiers)
        
        result = self._cache.get(cache_key)
        if result:
            logger.info(f"Cache hit for key: {cache_key[:16]}...")
            # Return a deep copy to prevent mutation
            return self._deep_copy_result(result)
        
        logger.debug(f"Cache miss for key: {cache_key[:16]}...")
        return None
    
    def set(
        self, 
        parsed_turns: list[ParsedTurn], 
        context: ConversationContext, 
        speaker_identifiers: SpeakerIdentifierHints,
        result: CompleteAnalysisResult
    ) -> None:
        """Store analysis result in cache"""
        cache_key = self._generate_cache_key(parsed_turns, context, speaker_identifiers)
        
        # Implement cache size limit
        if len(self._cache) >= self.max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Cache limit reached, removed oldest item: {oldest_key[:16]}...")
        
        # Store deep copy to prevent mutation
        self._cache[cache_key] = self._deep_copy_result(result)
        logger.info(f"Cached result for key: {cache_key[:16]}...")
    
    def clear(self) -> None:
        """Clear all cached results"""
        self._cache.clear()
        logger.info("Analysis cache cleared")
    
    def force_clear_all(self) -> None:
        """Force clear all cached results and reset cache completely"""
        self._cache.clear()
        logger.info("Analysis cache force cleared - all cached results removed")
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)
    
    def _deep_copy_result(self, result: CompleteAnalysisResult) -> CompleteAnalysisResult:
        """Create a deep copy of the analysis result"""
        try:
            # Use JSON serialization for deep copy
            result_dict = result.dict()
            return CompleteAnalysisResult.parse_obj(result_dict)
        except Exception as e:
            logger.error(f"Failed to deep copy result: {e}")
            return result

# Global cache instance
_analysis_cache = None

def get_analysis_cache() -> AnalysisCache:
    """Get the global analysis cache instance"""
    global _analysis_cache
    if _analysis_cache is None:
        _analysis_cache = AnalysisCache()
    return _analysis_cache