"""
Response Depth Calculator - From Original Design
Implements the quality-based progression system from info.txt
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from supabase import Client
from src.services.mi_analyzer_service import MIAnalysisResult

logger = logging.getLogger(__name__)

@dataclass
class ResponseInstruction:
    """Dynamic response instruction based on MI quality"""
    instruction: str
    depth: str  # surface/middle/deep
    metrics: Dict[str, Any]

class ResponseDepthCalculator:
    """
    Calculates response depth and generates dynamic instructions
    Exactly matches the Supabase Edge Function logic from info.txt
    """

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def calculate_response_depth(
        self,
        conversation_id: str,
        mi_analysis: MIAnalysisResult
    ) -> ResponseInstruction:
        """
        Calculate response depth based on sustained MI quality
        Implements the exact logic from info.txt specification
        """
        try:
            # Get recent quality patterns (last 5 analyses)
            response = self.supabase.table('mi_analysis') \
                .select('quality_score, empathy_score, resistance_triggered') \
                .eq('conversation_id', conversation_id) \
                .order('created_at', desc=True) \
                .limit(5) \
                .execute()

            recent_analyses = response.data if response.data else []

            # Calculate sustained quality metrics
            if recent_analyses:
                quality_scores = [float(a['quality_score']) for a in recent_analyses]
                empathy_scores = [float(a['empathy_score']) for a in recent_analyses]
                resistance_count = sum(1 for a in recent_analyses if a['resistance_triggered'])

                avg_quality = sum(quality_scores) / len(quality_scores)
                avg_empathy = sum(empathy_scores) / len(empathy_scores)
                recent_resistance = resistance_count
            else:
                # First message in conversation
                avg_quality = mi_analysis.quality_score
                avg_empathy = mi_analysis.empathy_score
                recent_resistance = 1 if mi_analysis.triggers_resistance else 0

            # Generate response instruction based on quality patterns
            # (Exact logic from info.txt specification)
            instruction = ""
            depth = "surface"

            if mi_analysis.triggers_resistance:
                instruction = "Show resistance. Change topic or intellectualize."
                depth = "surface"
            elif avg_quality > 8.5 and avg_empathy > 8.5 and recent_resistance == 0:
                instruction = "You trust them. Explore your real feelings about change."
                depth = "deep"
            elif avg_quality > 7 and avg_empathy > 7 and recent_resistance == 0:
                instruction = "You feel heard. Share something deeper but maintain ambivalence."
                depth = "middle"
            elif mi_analysis.quality_score < 5:
                instruction = "You don't feel understood. Stay guarded."
                depth = "surface"
            else:
                instruction = "Respond naturally but cautiously."
                depth = "surface"

            # Quality patterns functionality removed - not needed as per requirements
            # await self._update_quality_patterns(
            #     conversation_id, avg_quality, avg_empathy, recent_resistance, depth
            # )

            result = ResponseInstruction(
                instruction=instruction,
                depth=depth,
                metrics={
                    "avgQuality": avg_quality,
                    "avgEmpathy": avg_empathy,
                    "recentResistance": recent_resistance
                }
            )

            logger.info(f"Response depth calculated - depth: {depth}, instruction: {instruction[:50]}...")
            return result

        except Exception as e:
            logger.error(f"Response depth calculation failed: {e}", exc_info=True)
            # Safe fallback
            return ResponseInstruction(
                instruction="Respond naturally but cautiously.",
                depth="surface",
                metrics={"avgQuality": 5.0, "avgEmpathy": 5.0, "recentResistance": 0}
            )

    # Quality patterns functionality removed - not needed as per requirements
    # async def _update_quality_patterns(
    #     self,
    #     conversation_id: str,
    #     avg_quality: float,
    #     avg_empathy: float,
    #     recent_resistance: int,
    #     depth: str
    # ):
    #     """Update quality patterns table for conversation tracking"""
    #     try:
    #         # Upsert quality patterns
    #         self.supabase.table('quality_patterns').upsert({
    #             'conversation_id': conversation_id,
    #             'sustained_empathy': avg_empathy,
    #             'recent_resistance': recent_resistance,
    #             'depth_achieved': depth,
    #             'last_quality_scores': [avg_quality],  # Simplified for now
    #             'updated_at': 'NOW()'
    #         }).execute()
    #
    #     except Exception as e:
    #         logger.warning(f"Failed to update quality patterns: {e}")
    #         # Non-critical, continue without failing