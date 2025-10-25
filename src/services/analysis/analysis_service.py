"""
Main MITI analysis service orchestrator with enhanced capabilities
"""
import asyncio
import logging
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime

from .types import (
    ConversationContext, SpeakerIdentifierHints, CompleteAnalysisResult,
    ProgressState, ProgressStage, ParsedTurn, AnnotatedTurn,
    DEFAULT_BATCH_SIZE
)
from .parser import parse_transcript, validate_transcript
from .gemini_service import GeminiService
from .aggregator import aggregate_miti_data
from .cache_service import get_analysis_cache
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

class AnalysisService:
    """Enhanced main service for orchestrating MITI transcript analysis"""
    
    def __init__(self):
        self.settings = get_settings()
        self.gemini_service = GeminiService()
        self.batch_size = getattr(self.settings, 'MITI_BATCH_SIZE', DEFAULT_BATCH_SIZE)
        self.enable_cache = getattr(self.settings, 'ENABLE_ANALYSIS_CACHE', True)
        self.cache = get_analysis_cache()
        self.reflection_integration = True  # Enable reflection room integration
        
        logger.info(f"AnalysisService initialized with batch_size={self.batch_size}, cache_enabled={self.enable_cache}")
    
    async def analyze_transcript(
        self,
        raw_transcript: str,
        context: Optional[ConversationContext] = None,
        speaker_hints: Optional[SpeakerIdentifierHints] = None,
        progress_callback: Optional[Callable[[ProgressState], None]] = None
    ) -> CompleteAnalysisResult:
        """
        Perform complete MITI analysis on a transcript.
        
        Args:
            raw_transcript: Raw conversation text
            context: Optional conversation context
            speaker_hints: Optional hints for speaker identification
            progress_callback: Optional callback for progress updates
            
        Returns:
            Complete analysis result with annotations, statistics, and report
        """
        # Use defaults if not provided
        if not context:
            context = ConversationContext()
        
        if not speaker_hints:
            speaker_hints = SpeakerIdentifierHints()
        
        # Progress helper
        def update_progress(stage: ProgressStage, progress: int, message: str):
            if progress_callback:
                progress_callback(ProgressState(
                    stage=stage,
                    progress=progress,
                    current_item=message
                ))
        
        try:
            # Stage 1: Parse transcript
            update_progress(ProgressStage.PARSING, 5, "Parsing transcript...")
            parsed_output = parse_transcript(raw_transcript, speaker_hints)
            
            # Validate parsing
            is_valid, issues = validate_transcript(parsed_output)
            if not is_valid:
                raise ValueError(f"Transcript validation failed: {'; '.join(issues)}")
            
            update_progress(ProgressStage.PARSING, 10, f"Parsed {len(parsed_output.parsed_turns)} turns")
            
            # Check cache with enhanced caching service
            if self.enable_cache:
                update_progress(ProgressStage.CACHING_CHECK, 12, "Checking for cached analysis...")
                cached_result = self.cache.get(parsed_output.parsed_turns, context, speaker_hints)
                if cached_result:
                    update_progress(ProgressStage.COMPLETE, 100, "Analysis loaded from cache!")
                    return cached_result
                update_progress(ProgressStage.CACHING_CHECK, 15, "No cached result found")
            
            # Stage 2: Code transcript with enhanced processing
            update_progress(ProgressStage.CODING, 18, "Starting MITI coding with enhanced batch processing...")
            annotated_turns = await self._enhanced_code_transcript(
                parsed_output.parsed_turns,
                context,
                update_progress
            )
            
            # Stage 3: Aggregate statistics
            update_progress(ProgressStage.AGGREGATING, 70, "Calculating statistics...")
            statistics = aggregate_miti_data(annotated_turns)
            
            # Stage 4: Generate supervisory report with reflection integration
            update_progress(ProgressStage.SUPERVISING, 80, "Generating supervisory report...")
            report = await self.gemini_service.generate_supervisory_report(
                annotated_turns,
                statistics,
                context,
                include_reflection_prompts=self.reflection_integration
            )
            
            # Assemble final result
            result = CompleteAnalysisResult(
                annotated_turns=annotated_turns,
                statistics=statistics,
                report=report,
                context_used=context,
                speaker_identifiers_used=SpeakerIdentifierHints(
                    practitioner_identifier_hint=parsed_output.actual_practitioner_identifier,
                    client_identifier_hint=parsed_output.actual_client_identifier
                )
            )
            
            # Cache result with enhanced caching service
            if self.enable_cache:
                update_progress(ProgressStage.AGGREGATING, 98, "Caching analysis results...")
                self.cache.set(parsed_output.parsed_turns, context, speaker_hints, result)
            
            update_progress(ProgressStage.COMPLETE, 100, "Analysis complete!")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            update_progress(
                ProgressStage.ERROR, 
                0, 
                f"Analysis failed: {str(e)}"
            )
            raise
    
    async def _enhanced_code_transcript(
        self,
        parsed_turns: List[ParsedTurn],
        context: ConversationContext,
        update_progress: Callable
    ) -> List[AnnotatedTurn]:
        """Enhanced transcript coding with better error handling and adaptive batching"""
        total_turns = len(parsed_turns)
        if total_turns == 0:
            return []
        
        logger.info(f"Starting enhanced coding for {total_turns} turns")
        
        # Adaptive batch sizing based on total turns
        if total_turns > 150:
            adaptive_batch_size = 5  # Smaller batches for very large transcripts
        elif total_turns > 80:
            adaptive_batch_size = 8
        else:
            adaptive_batch_size = self.batch_size
        
        all_annotated_turns = []
        num_batches = (total_turns + adaptive_batch_size - 1) // adaptive_batch_size
        
        logger.info(f"Processing {total_turns} turns in {num_batches} batches of ~{adaptive_batch_size} turns each")
        
        for i in range(0, total_turns, adaptive_batch_size):
            batch_start = i
            batch_end = min(i + adaptive_batch_size, total_turns)
            batch = parsed_turns[batch_start:batch_end]
            batch_num = i // adaptive_batch_size + 1
            
            # Calculate progress (18% to 65% for coding stage)
            progress_contribution = 47  # Total progress allocated to coding
            batch_progress = (i / total_turns) * progress_contribution
            current_progress = 18 + int(batch_progress)
            
            update_progress(
                ProgressStage.CODING,
                current_progress,
                f"Coding batch {batch_num}/{num_batches} (turns {batch_start + 1}-{batch_end})..."
            )
            
            try:
                # Use the enhanced Gemini service method
                batch_results = await self.gemini_service.code_transcript_batch(
                    batch,
                    context,
                    max_retries=3  # More retries for robustness
                )
                
                # Validate batch results
                if len(batch_results) < len(batch) * 0.7:
                    logger.warning(f"Batch {batch_num} returned fewer results than expected: {len(batch_results)}/{len(batch)}")
                
                all_annotated_turns.extend(batch_results)
                
                # Small delay between batches to avoid rate limiting
                if batch_end < total_turns:
                    await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Batch {batch_num} failed completely: {e}")
                # Create fallback annotations for this batch
                fallback_annotations = self._create_fallback_annotations(batch)
                all_annotated_turns.extend(fallback_annotations)
        
        # Final progress update for coding stage
        update_progress(ProgressStage.CODING, 65, f"MITI coding complete - processed {len(all_annotated_turns)} turns")
        
        # Sort by turn index to ensure proper order
        all_annotated_turns.sort(key=lambda x: x.turn_index)
        
        logger.info(f"Enhanced coding completed: {len(all_annotated_turns)} annotated turns")
        return all_annotated_turns
    
    def _create_fallback_annotations(self, batch: List[ParsedTurn]) -> List[AnnotatedTurn]:
        """Create fallback annotations when batch processing fails"""
        fallback_turns = []
        
        for turn in batch:
            # Create basic annotation with no codes
            fallback_turn = AnnotatedTurn(
                turn_index=turn.original_index,
                speaker=turn.speaker,
                text=turn.text,
                codes=[],
                confidence=0.1  # Very low confidence for fallback
            )
            fallback_turns.append(fallback_turn)
        
        logger.warning(f"Created {len(fallback_turns)} fallback annotations")
        return fallback_turns
    
    async def _code_transcript(
        self,
        parsed_turns: List[ParsedTurn],
        context: ConversationContext,
        update_progress: Callable
    ) -> List[AnnotatedTurn]:
        """Legacy code transcript method - now delegates to enhanced version"""
        logger.info("Using legacy _code_transcript - delegating to enhanced version")
        return await self._enhanced_code_transcript(parsed_turns, context, update_progress)
    
    def clear_cache(self):
        """Clear the analysis cache"""
        if self.cache:
            self.cache.clear()
            logger.info("Enhanced analysis cache cleared")
        else:
            logger.warning("No cache available to clear")
    
    def generate_reflection_prompts(self, analysis_result: CompleteAnalysisResult) -> List[str]:
        """Generate reflection prompts based on analysis results"""
        prompts = []
        
        # Extract key insights from the analysis
        statistics = analysis_result.statistics
        report = analysis_result.report
        
        # Generate prompts based on strengths
        if hasattr(report, 'practitioner_patterns'):
            strengths = getattr(report.practitioner_patterns, 'strengths', '')
            if strengths:
                prompts.append(f"Your analysis shows strengths in {strengths}. How did it feel when you were using these skills?")
        
        # Generate prompts based on challenges
        if hasattr(report, 'practitioner_patterns'):
            challenges = getattr(report.practitioner_patterns, 'challenge_areas', '')
            if challenges:
                prompts.append(f"The analysis identified some areas for growth: {challenges}. What do you think contributed to these challenges?")
        
        # Generate prompts based on MITI ratios
        if statistics.reflection_to_question_ratio < 1.0:
            prompts.append("Your reflection-to-question ratio suggests more opportunities for reflective listening. When do you find it most challenging to reflect rather than ask questions?")
        
        if statistics.percentage_complex_reflections < 50:
            prompts.append("How comfortable do you feel with complex reflections? What might help you add more meaning and emphasis to your reflective statements?")
        
        # Generate prompts based on change talk
        change_talk_count = statistics.code_counts.get('ChangeTalk', 0)
        if change_talk_count < 3:
            prompts.append("There were limited instances of change talk from your client. What strategies might help you elicit more change talk in future conversations?")
        
        return prompts
    
    def create_reflection_summary_with_analysis(
        self, 
        analysis_result: CompleteAnalysisResult,
        reflection_responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create integrated reflection summary with analysis insights"""
        
        # Base reflection summary structure
        summary = {
            "session_date": datetime.now().isoformat(),
            "analysis_integrated": True,
            "miti_statistics": {
                "total_turns": analysis_result.statistics.total_turns,
                "reflection_to_question_ratio": analysis_result.statistics.reflection_to_question_ratio,
                "percentage_complex_reflections": analysis_result.statistics.percentage_complex_reflections,
                "mia_to_mina_ratio": analysis_result.statistics.mia_to_mina_ratio
            },
            "key_insights": {},
            "analysis_strengths": [],
            "analysis_growth_areas": [],
            "reflection_insights": {},
            "integrated_recommendations": []
        }
        
        # Extract analysis insights
        if hasattr(analysis_result.report, 'practitioner_patterns'):
            patterns = analysis_result.report.practitioner_patterns
            summary["analysis_strengths"].append(getattr(patterns, 'strengths', ''))
            summary["analysis_growth_areas"].append(getattr(patterns, 'challenge_areas', ''))
        
        # Extract reflection insights
        for response in reflection_responses:
            stage = response.get("stage", "unknown")
            content = response.get("user_response", "")
            summary["reflection_insights"][stage] = content[:300]
        
        # Generate integrated recommendations
        if hasattr(analysis_result.report, 'actionable_recommendations'):
            recs = analysis_result.report.actionable_recommendations
            summary["integrated_recommendations"].append(getattr(recs, 'immediate_focus', ''))
            summary["integrated_recommendations"].append(getattr(recs, 'skill_development', ''))
        
        return summary

# Singleton instance
_analysis_service = None

def get_analysis_service() -> AnalysisService:
    """Get or create the analysis service singleton with optional database enhancement"""
    global _analysis_service
    if _analysis_service is None:
        # Check if database enhancement should be used
        from src.config.settings import get_settings
        settings = get_settings()
        
        if getattr(settings, 'USE_DATABASE_ENHANCED_ANALYSIS', False):
            try:
                # Try to import and use database-enhanced service
                from .enhanced_analysis_service import DatabaseIntegratedAnalysisService
                _analysis_service = DatabaseIntegratedAnalysisService()
                logger.info("Using database-enhanced analysis service")
            except ImportError as e:
                logger.warning(f"Database-enhanced service not available, falling back to standard service: {e}")
                _analysis_service = AnalysisService()
        else:
            _analysis_service = AnalysisService()
            
    return _analysis_service
