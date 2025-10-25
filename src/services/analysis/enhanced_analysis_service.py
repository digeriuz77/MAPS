"""
Enhanced Analysis Service with database integration
"""
import logging
from typing import List, Optional, Callable, Dict, Any
from .analysis_service import AnalysisService as BaseAnalysisService
from .database_service import get_database_service
from .enhanced_gemini_service import get_enhanced_gemini_service
from .types import CompleteAnalysisResult, ConversationContext, SpeakerIdentifierHints

logger = logging.getLogger(__name__)

class DatabaseIntegratedAnalysisService(BaseAnalysisService):
    """Analysis service with database integration for enhanced MITI analysis"""
    
    def __init__(self):
        super().__init__()
        self.db_service = get_database_service()
        self.enhanced_gemini_service = get_enhanced_gemini_service()  # Use enhanced version
        self.miti_definitions = self.db_service.get_miti_code_definitions()
        logger.info("Database-integrated analysis service initialized")
    
    async def analyze_transcript_with_examples(
        self,
        raw_transcript: str,
        context: Optional[ConversationContext] = None,
        speaker_hints: Optional[SpeakerIdentifierHints] = None,
        progress_callback: Optional[Callable] = None,
        include_learning_examples: bool = True
    ) -> CompleteAnalysisResult:
        """
        Enhanced analysis that includes relevant learning examples.
        """
        # Perform standard analysis but use enhanced Gemini service
        original_gemini_service = self.gemini_service
        self.gemini_service = self.enhanced_gemini_service
        
        try:
            result = await self.analyze_transcript(
                raw_transcript, context, speaker_hints, progress_callback
            )
            
            if include_learning_examples:
                # Add learning examples based on analysis results
                result.learning_examples = self._get_relevant_learning_examples(result)
            
            return result
        finally:
            # Restore original service
            self.gemini_service = original_gemini_service
    
    def _get_relevant_learning_examples(
        self, 
        analysis_result: CompleteAnalysisResult
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get learning examples relevant to the analysis results"""
        
        # Identify areas for improvement
        stats = analysis_result.statistics
        examples = {}
        
        # Get examples based on performance areas
        if self._needs_question_examples(stats):
            examples['question_techniques'] = self.db_service.get_examples_for_codes([
                'Q'  # Use string instead of MitiCode enum
            ])
        
        if self._needs_reflection_examples(stats):
            examples['reflection_techniques'] = self.db_service.get_examples_for_codes([
                'CR', 'SR'  # Use strings instead of MitiCode enums
            ])
        
        if self._needs_affirmation_examples(stats):
            examples['affirmation_techniques'] = self.db_service.get_examples_for_codes([
                'AF'  # Use string instead of MitiCode enum
            ])
        
        if self._has_problematic_behaviors(stats):
            examples['avoiding_roadblocks'] = self.db_service.get_poor_examples(limit=3)
        
        # Always include some excellent examples for inspiration
        examples['excellent_examples'] = self.db_service.get_excellent_examples(limit=2)
        
        return examples
    
    def _needs_question_examples(self, stats) -> bool:
        """Check if user needs examples of good questioning technique"""
        q_count = stats.code_counts.get('Q', 0)
        total_turns = stats.practitioner_turns
        return total_turns > 0 and (q_count / total_turns) < 0.3  # Less than 30% questions
    
    def _needs_reflection_examples(self, stats) -> bool:
        """Check if user needs examples of reflective listening"""
        try:
            ratio_parts = stats.reflection_to_question_ratio.split(':')
            if len(ratio_parts) == 2 and ratio_parts[1] != '0':
                ratio = float(ratio_parts[0]) / float(ratio_parts[1])
                return ratio < 1.0  # Less than 1:1 ratio
        except:
            pass
        return True
    
    def _needs_affirmation_examples(self, stats) -> bool:
        """Check if user needs examples of affirmations"""
        af_count = stats.code_counts.get('AF', 0)
        return af_count == 0  # No affirmations used
    
    def _has_problematic_behaviors(self, stats) -> bool:
        """Check if user showed problematic MI behaviors"""
        per_count = stats.code_counts.get('Per', 0)
        c_count = stats.code_counts.get('C', 0)
        return per_count > 0 or c_count > 0
    
    def get_code_definition(self, code: str) -> Optional[Dict[str, Any]]:
        """Get detailed definition for a specific MITI code"""
        return self.miti_definitions.get(code)
    
    def search_learning_resources(self, query: str) -> List[Dict[str, Any]]:
        """Search for learning examples and resources"""
        return self.db_service.search_examples(query)
    
    def get_examples_by_difficulty(self, difficulty: str) -> List[Dict[str, Any]]:
        """Get examples filtered by difficulty level"""
        return self.db_service.get_examples_by_difficulty(difficulty)
    
    def get_coaching_examples(self, focus_area: str) -> List[Dict[str, Any]]:
        """Get examples for specific coaching focus areas"""
        focus_mapping = {
            'questioning': ['Q'],
            'reflecting': ['SR', 'CR'],
            'affirmations': ['AF'],
            'autonomy': ['EA'],
            'collaboration': ['Seek'],
            'avoiding_persuasion': ['Per'],
            'avoiding_confrontation': ['C']
        }
        
        if focus_area.lower() in focus_mapping:
            codes = focus_mapping[focus_area.lower()]
            return self.db_service.get_training_examples(focus_codes=codes)
        
        return []

# Usage example functions
def create_enhanced_analysis_service():
    """Factory function to create the enhanced analysis service"""
    return DatabaseIntegratedAnalysisService()

def get_analysis_service_with_database():
    """Get analysis service with database integration"""
    return DatabaseIntegratedAnalysisService()