"""
MI Quality Analyzer Service - From Original Design
GPT-4o-mini-based technique analysis for production performance
"""
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from openai import AsyncOpenAI
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

@dataclass
class MIAnalysisResult:
    """Clean MI analysis result matching original spec"""
    technique: str
    quality_score: float  # 1-10
    empathy_score: float  # 1-10
    neutrality: bool
    triggers_resistance: bool
    specific_issues: List[str]

class MIAnalyzerService:
    """
    GPT-4o-mini-based MI technique analyzer for production performance
    Implements the clean analysis system with faster model
    """

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)

    async def analyze_mi_technique(
        self,
        message: str,
        recent_history: Optional[List[Dict[str, str]]] = None
    ) -> MIAnalysisResult:
        """
        Analyze MI technique quality using GPT-4o-mini for performance
        Maintains analysis accuracy with faster response times
        """
        try:
            # Build context from recent history
            context_text = ""
            if recent_history:
                context_text = "\n".join([
                    f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                    for msg in recent_history[-6:]  # Last 6 messages for context
                ])

            # GPT-4o analysis prompt (from original spec)
            analysis_prompt = """Analyze this message for MI technique quality.

Evaluate:
- Technique type (open question, reflection, affirmation, summary)
- Empathy level (1-10)
- Neutrality (maintained/broken)
- Potential resistance triggers

Return JSON with:
{
  "technique": string,
  "quality_score": number,
  "empathy_score": number,
  "neutrality": boolean,
  "triggers_resistance": boolean,
  "specific_issues": string[]
}"""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": analysis_prompt
                    },
                    {
                        "role": "user",
                        "content": f"Current message: {message}\nRecent context: {context_text}"
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # Consistent analysis
                max_tokens=500    # Keep under original 500 token target
            )

            # Parse GPT-4o response
            analysis_data = json.loads(response.choices[0].message.content)

            # Convert to clean result object
            result = MIAnalysisResult(
                technique=analysis_data.get("technique", "unknown"),
                quality_score=float(analysis_data.get("quality_score", 0)),
                empathy_score=float(analysis_data.get("empathy_score", 0)),
                neutrality=bool(analysis_data.get("neutrality", True)),
                triggers_resistance=bool(analysis_data.get("triggers_resistance", False)),
                specific_issues=analysis_data.get("specific_issues", [])
            )

            logger.info(f"MI analysis completed - technique: {result.technique}, quality: {result.quality_score}")
            return result

        except Exception as e:
            logger.error(f"GPT-4o-mini MI analysis failed: {e}", exc_info=True)
            # Return safe fallback
            return MIAnalysisResult(
                technique="unknown",
                quality_score=5.0,
                empathy_score=5.0,
                neutrality=True,
                triggers_resistance=False,
                specific_issues=["Analysis service temporarily unavailable"]
            )

    def to_dict(self, result: MIAnalysisResult) -> Dict[str, Any]:
        """Convert analysis result to dictionary for API responses"""
        return {
            "technique": result.technique,
            "quality_score": result.quality_score,
            "empathy_score": result.empathy_score,
            "neutrality_maintained": result.neutrality,
            "resistance_triggered": result.triggers_resistance,
            "specific_issues": result.specific_issues
        }