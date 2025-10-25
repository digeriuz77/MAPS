"""
Google Gemini API service for MITI analysis with enhanced error handling
"""
import json
import logging
from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
import re
import math

from src.config.settings import get_settings
from .types import (
    AnnotatedTurn, ParsedTurn, ConversationContext,
    MitiCode, SpeakerRole, SupervisoryReportData,
    AggregatedStats, GlobalRatingItem, KeyMoment,
    PractitionerPatterns, ActionableRecommendations,
    GlobalRatings, ALL_MITI_CODES, DEFAULT_BATCH_SIZE,
    DEFAULT_PRACTITIONER_ROLE, DEFAULT_CLIENT_ROLE,
    DEFAULT_SCENARIO_DESCRIPTION
)
from .json_parser import clean_and_validate_json_response, JsonParsingError

logger = logging.getLogger(__name__)

class GeminiService:
    """Enhanced service for interacting with Google Gemini API with robust error handling"""
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.temperature = settings.GEMINI_TEMPERATURE
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.batch_size = getattr(settings, 'MITI_BATCH_SIZE', DEFAULT_BATCH_SIZE)
        
        if not self.api_key:
            logger.warning("Gemini API key not configured - using mock responses")
    
    async def code_transcript_batch(
        self, 
        batch: List[ParsedTurn], 
        context: ConversationContext,
        max_retries: int = 3
    ) -> List[AnnotatedTurn]:
        """
        Send a batch of turns to Gemini for MITI coding with enhanced error handling.
        """
        if not self.api_key:
            return self._mock_code_batch(batch)
        
        # Adaptive batch sizing for large batches
        total_turns = len(batch)
        if total_turns > 150:
            # Split into smaller chunks for very large batches
            return await self._process_large_batch(batch, context, max_retries)
        
        prompt = self._generate_improved_coding_prompt(batch, context)
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1}/{max_retries} for batch of {len(batch)} turns")
                
                response = await self._call_gemini_api(
                    prompt, 
                    max_output_tokens=max(2048, len(batch) * 250),
                    temperature=0.2  # Lower temperature for more consistent JSON
                )
                
                # Use enhanced JSON parsing
                validated_results = clean_and_validate_json_response(response, batch)
                annotated_turns = self._convert_to_annotated_turns(validated_results, batch)
                
                # Validate result completeness
                if len(annotated_turns) < len(batch) * 0.7:  # Allow some flexibility
                    logger.warning(f"Only got {len(annotated_turns)}/{len(batch)} turns, retrying...")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                
                logger.info(f"Successfully processed {len(annotated_turns)} turns on attempt {attempt + 1}")
                return annotated_turns
                
            except Exception as e:
                logger.error(f"Batch coding attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    # Final fallback: try smaller batches or return fallback coding
                    logger.warning("All retry attempts failed, trying fallback strategy")
                    return await self._fallback_batch_processing(batch, context)
    
    async def _process_large_batch(
        self, 
        batch: List[ParsedTurn], 
        context: ConversationContext, 
        max_retries: int
    ) -> List[AnnotatedTurn]:
        """Process very large batches by splitting into smaller chunks"""
        chunk_size = 8  # Smaller chunks for large batches
        all_results = []
        
        for i in range(0, len(batch), chunk_size):
            chunk = batch[i:i + chunk_size]
            logger.debug(f"Processing large batch chunk {i//chunk_size + 1}/{math.ceil(len(batch)/chunk_size)}")
            
            chunk_results = await self.code_transcript_batch(chunk, context, max_retries=2)
            all_results.extend(chunk_results)
            
            # Small delay between chunks to avoid rate limiting
            await asyncio.sleep(0.5)
        
        return all_results
    
    async def _fallback_batch_processing(
        self, 
        batch: List[ParsedTurn], 
        context: ConversationContext
    ) -> List[AnnotatedTurn]:
        """Fallback processing when main batch fails"""
        if len(batch) <= 2:
            # If batch is already small, return fallback coding
            return self._fallback_coding(batch)
        
        # Try splitting into smaller batches
        mid_point = len(batch) // 2
        first_half = batch[:mid_point]
        second_half = batch[mid_point:]
        
        try:
            logger.info(f"Trying fallback: splitting {len(batch)} turns into smaller batches")
            first_results = await self.code_transcript_batch(first_half, context, max_retries=1)
            second_results = await self.code_transcript_batch(second_half, context, max_retries=1)
            return first_results + second_results
        except Exception as e:
            logger.error(f"Fallback processing also failed: {e}")
            return self._fallback_coding(batch)
    
    async def generate_supervisory_report(
        self,
        annotated_turns: List[AnnotatedTurn],
        statistics: AggregatedStats,
        context: ConversationContext,
        include_reflection_prompts: bool = False
    ) -> SupervisoryReportData:
        """
        Generate a comprehensive supervisory report based on coded turns.
        """
        if not self.api_key:
            return self._mock_supervisory_report(include_reflection_prompts)
        
        prompt = self._generate_report_prompt(
            annotated_turns, 
            statistics, 
            context, 
            include_reflection_prompts
        )
        
        try:
            response = await self._call_gemini_api(prompt, temperature=0.7)
            return self._parse_report_response(response)
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return self._fallback_report()
    
    async def _call_gemini_api(
        self, 
        prompt: str, 
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None
    ) -> str:
        """Make API call to Gemini with enhanced configuration"""
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Enhanced generation config
        generation_config = {
            "temperature": temperature or self.temperature,
            "candidateCount": 1,
            "topK": 40,
            "topP": 0.95,
        }
        
        if max_output_tokens:
            generation_config["maxOutputTokens"] = max_output_tokens
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": generation_config,
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Gemini API error {response.status}: {error_text}")
                
                result = await response.json()
                
                if 'candidates' not in result or len(result['candidates']) == 0:
                    raise Exception(f"No candidates in Gemini response: {result}")
                
                candidate = result['candidates'][0]
                
                if 'content' not in candidate:
                    raise Exception(f"No content in Gemini candidate: {candidate}")
                
                return candidate['content']['parts'][0]['text']
    
    def _generate_improved_coding_prompt(
        self, 
        batch: List[ParsedTurn], 
        context: ConversationContext
    ) -> str:
        """Generate improved prompt for MITI coding with better structure and instructions"""
        formatted_turns = "\n".join([
            f"{turn.speaker.value} (Turn {turn.original_index + 1}): {turn.text}"
            for turn in batch
        ])
        
        context_block = f"""
---
**SESSION CONTEXT:**
The following transcript is from a conversation with the following roles and goals:
*   The "Practitioner" (semantic role) is a: {context.practitioner_role or DEFAULT_PRACTITIONER_ROLE}
*   The "Client" (semantic role) is a: {context.client_role or DEFAULT_CLIENT_ROLE}
*   The Scenario is: {context.scenario_description or DEFAULT_SCENARIO_DESCRIPTION}

The turns below are labelled based on these semantic roles.
Apply all MITI codes through the lens of this specific context.
---
"""
        
        return f"""You are a MITI 4.2.1 coder. Your ONLY task is to output valid JSON with MITI codes.

{context_block}

**CRITICAL OUTPUT REQUIREMENTS:**
1. Output MUST be a valid JSON array.
2. Each object MUST have exactly these fields: "turnIndex" (use the original 0-based turn index from the input), "speaker" ("Practitioner" or "Client"), "text" (exact text from input), "codes" (array of MITI code strings), "confidence" (a number between 0.0 and 1.0).
3. The "codes" field MUST be a JSON array of strings (e.g., ["Q", "SR"]). If no codes apply, use an empty array: [].
4. Do NOT include any text, explanations, or markdown formatting outside the main JSON array.
5. Do NOT truncate the response - complete all {len(batch)} turns.

**MITI CODING RULES (APPLY STRICTLY):**

**For Practitioner turns:**
- Maximum ONE "Q" code per turn.
- Maximum ONE reflection code per turn (either "SR" OR "CR", never both).
- "CR" TRUMPS "SR".
- Use these codes only: ["Q", "SR", "CR", "AF", "Seek", "EA", "GI", "Per", "C", "O"]

**For Client turns:**
- Use only: ["ChangeTalk", "SustainTalk", "Neutral"]
- A turn can have multiple codes if it contains both ChangeTalk and SustainTalk (e.g. ["ChangeTalk", "SustainTalk"]).

**DETAILED CODING GUIDELINES:**

PRACTITIONER CODES:
- Q: Open or closed questions
- SR: Simple Reflection (repeats/rephrases with little added meaning)
- CR: Complex Reflection (adds substantial meaning/emphasis)
- AF: Affirmation (acknowledges strengths/efforts)
- Seek: Seeking Collaboration  
- EA: Emphasizing Autonomy
- Per: Persuasion (arguing for change)
- C: Confrontation (negative/blaming)
- GI: Giving Information
- O: Other (doesn't fit other categories)

CLIENT CODES:
- ChangeTalk: Statements favoring change (desire, ability, reasons, need)
- SustainTalk: Statements favoring status quo
- Neutral: Neither change nor sustain talk

**INPUT TURNS ({len(batch)} total):**
{formatted_turns}

**OUTPUT EXACTLY THIS FORMAT:**
[
  {{
    "turnIndex": 0, 
    "speaker": "Practitioner",
    "text": "Exact text from input turn",
    "codes": ["Q"],
    "confidence": 0.9
  }}
]

Start your response with [ and end with ]. Include all {len(batch)} turns. Ensure "turnIndex" corresponds to the 0-based index from the input."""
    
    def _convert_to_annotated_turns(
        self, 
        validated_results: List[Dict[str, Any]], 
        batch_turns: List[ParsedTurn]
    ) -> List[AnnotatedTurn]:
        """Convert validated JSON results to AnnotatedTurn objects"""
        annotated_turns = []
        
        for result in validated_results:
            try:
                # Find corresponding original turn
                turn_index = result['turnIndex']
                original_turn = None
                
                for bt in batch_turns:
                    if bt.original_index == turn_index:
                        original_turn = bt
                        break
                
                if not original_turn:
                    logger.warning(f"No original turn found for index {turn_index}")
                    continue
                
                # Convert codes to MitiCode enums
                codes = []
                for code_str in result['codes']:
                    try:
                        codes.append(MitiCode(code_str))
                    except ValueError:
                        logger.warning(f"Invalid MITI code: {code_str}")
                
                # Create AnnotatedTurn
                annotated_turn = AnnotatedTurn(
                    turn_index=original_turn.original_index,
                    speaker=original_turn.speaker,  # Use original speaker
                    text=original_turn.text,  # Use original text
                    codes=codes,
                    confidence=result.get('confidence', 0.5)
                )
                
                annotated_turns.append(annotated_turn)
                
            except Exception as e:
                logger.error(f"Failed to convert result to AnnotatedTurn: {e}")
                continue
        
        # Ensure we have results for all original turns
        result_indices = {at.turn_index for at in annotated_turns}
        for turn in batch_turns:
            if turn.original_index not in result_indices:
                logger.warning(f"Creating fallback AnnotatedTurn for missing turn {turn.original_index}")
                fallback_turn = AnnotatedTurn(
                    turn_index=turn.original_index,
                    speaker=turn.speaker,
                    text=turn.text,
                    codes=[],
                    confidence=0.1
                )
                annotated_turns.append(fallback_turn)
        
        # Sort by turn index
        annotated_turns.sort(key=lambda x: x.turn_index)
        return annotated_turns
    
    def _parse_coding_response(
        self, 
        response: str, 
        batch: List[ParsedTurn]
    ) -> List[AnnotatedTurn]:
        """Legacy parsing method - now delegates to enhanced parser"""
        logger.debug("Using legacy parsing method - delegating to enhanced parser")
        
        try:
            validated_results = clean_and_validate_json_response(response, batch)
            return self._convert_to_annotated_turns(validated_results, batch)
        except Exception as e:
            logger.error(f"Enhanced parsing failed, using simple fallback: {e}")
            return self._fallback_coding(batch)
            
            return annotated_turns
            
        except Exception as e:
            logger.error(f"Failed to parse coding response: {e}")
            return self._fallback_coding(batch)
    
    def _generate_report_prompt(
        self,
        annotated_turns: List[AnnotatedTurn],
        statistics: AggregatedStats,
        context: ConversationContext,
        include_reflection_prompts: bool = False
    ) -> str:
        """Generate prompt for supervisory report"""
        # Format coded transcript
        coded_transcript = "\n".join([
            f"{turn.speaker} (Turn {turn.turn_index + 1}) [{', '.join([c.value for c in turn.codes])}]: {turn.text}"
            for turn in annotated_turns
        ])
        
        # Format statistics
        stats_summary = f"""
Total Turns: {statistics.total_turns} (Practitioner: {statistics.practitioner_turns}, Client: {statistics.client_turns})
Reflection-to-Question Ratio: {statistics.reflection_to_question_ratio}
Percentage Complex Reflections: {statistics.percentage_complex_reflections}
MI-Adherent to Non-Adherent Ratio: {statistics.mia_to_mina_ratio}

Code Counts:
{json.dumps(statistics.code_counts, indent=2)}
"""
        
        reflection_section = ""
        if include_reflection_prompts:
            reflection_section = """

**ADDITIONAL REFLECTION INTEGRATION:**
Include these additional fields in your JSON response:
- "reflectionPrompts": ["question1", "question2", "question3"] - Generate 3 open-ended questions to help the practitioner reflect on their performance
- "coachingObservations": "detailed observations" - Specific observations about MI technique usage that would be valuable for coaching
- "celebrationMoments": ["moment1", "moment2"] - Identify 1-2 specific moments worth celebrating
- "growthOpportunities": ["opportunity1", "opportunity2"] - Identify 1-2 specific opportunities for skill development
            """
        
        return f"""You are an expert MI supervisor providing a comprehensive assessment for coaching and reflection purposes.

**SESSION CONTEXT:**
{context.practitioner_role} working with {context.client_role}
Scenario: {context.scenario_description}

**STATISTICS:**
{stats_summary}

**CODED TRANSCRIPT:**
{coded_transcript}
{reflection_section}

Generate a supervisory report as a valid JSON object with this EXACT structure:

{{
  "global_ratings": {{
    "partnership": {{"score": 1-5, "rationale": "detailed explanation with specific examples"}},
    "empathy": {{"score": 1-5, "rationale": "detailed explanation with specific examples"}},
    "cultivating_change_talk": {{"score": 1-5, "rationale": "detailed explanation with specific examples"}},
    "softening_sustain_talk": {{"score": 1-5, "rationale": "detailed explanation with specific examples"}}
  }},
  "key_moments": [
    {{"turn_quote": "specific quote from conversation", "explanation": "detailed explanation of why this moment was significant for MI practice"}}
  ],
  "client_language_themes": "comprehensive summary of client's main themes, resistance patterns, and change talk evolution",
  "practitioner_patterns": {{
    "strengths": "detailed analysis of observed MI strengths with specific examples",
    "challenge_areas": "specific areas for improvement with concrete suggestions"
  }},
  "actionable_recommendations": {{
    "immediate_focus": "specific, actionable recommendation for immediate practice improvement",
    "skill_development": "longer-term skills to develop with suggested practice methods"
  }}{{",\n  \"reflectionPrompts\": [\"prompt1\", \"prompt2\", \"prompt3\"],\n  \"coachingObservations\": \"detailed observations\",\n  \"celebrationMoments\": [\"moment1\", \"moment2\"],\n  \"growthOpportunities\": [\"opportunity1\", \"opportunity2\"]" if include_reflection_prompts else "}}"}}

Base ratings on MITI criteria and the coded behaviors. Be specific and actionable in all feedback. Output ONLY the JSON."""
    
    def _parse_report_response(self, response: str) -> SupervisoryReportData:
        """Parse supervisory report response"""
        try:
            # Clean response
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("\n", 1)[0]
            
            data = json.loads(cleaned)
            
            # Convert to our models
            global_ratings = GlobalRatings(
                partnership=GlobalRatingItem(**data['global_ratings']['partnership']),
                empathy=GlobalRatingItem(**data['global_ratings']['empathy']),
                cultivating_change_talk=GlobalRatingItem(**data['global_ratings']['cultivating_change_talk']),
                softening_sustain_talk=GlobalRatingItem(**data['global_ratings']['softening_sustain_talk'])
            )
            
            # Handle field name variations in key_moments
            key_moments = []
            for km in data['key_moments']:
                if 'turnQuote' in km:
                    # Convert camelCase to snake_case
                    km_fixed = {
                        'turn_quote': km['turnQuote'],
                        'explanation': km['explanation']
                    }
                    key_moments.append(KeyMoment(**km_fixed))
                else:
                    key_moments.append(KeyMoment(**km))
            
            practitioner_patterns = PractitionerPatterns(**data['practitioner_patterns'])
            
            recommendations = ActionableRecommendations(**data['actionable_recommendations'])
            
            return SupervisoryReportData(
                global_ratings=global_ratings,
                key_moments=key_moments,
                client_language_themes=data['client_language_themes'],
                practitioner_patterns=practitioner_patterns,
                actionable_recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Failed to parse report response: {e}")
            return self._fallback_report()
    
    def _mock_code_batch(self, batch: List[ParsedTurn]) -> List[AnnotatedTurn]:
        """Mock coding for development"""
        annotated = []
        for turn in batch:
            if turn.speaker == SpeakerRole.PRACTITIONER:
                # Simple heuristic coding
                codes = []
                text_lower = turn.text.lower()
                
                if '?' in turn.text:
                    codes.append(MitiCode.Q)
                elif any(phrase in text_lower for phrase in ['sounds like', 'seems like', 'i hear']):
                    codes.append(MitiCode.CR)
                elif 'you' in text_lower and len(turn.text.split()) < 15:
                    codes.append(MitiCode.SR)
                else:
                    codes.append(MitiCode.O)
            else:
                # Client turn
                codes = [MitiCode.NEUTRAL]
                
            annotated.append(AnnotatedTurn(
                turn_index=turn.original_index,
                speaker=turn.speaker,
                text=turn.text,
                codes=codes,
                confidence=0.7
            ))
        
        return annotated
    
    def _mock_supervisory_report(self, include_reflection_prompts: bool = False) -> SupervisoryReportData:
        """Mock report for development"""
        report = SupervisoryReportData(
            global_ratings=GlobalRatings(
                partnership=GlobalRatingItem(score=3, rationale="Mock rating with detailed explanation"),
                empathy=GlobalRatingItem(score=3, rationale="Mock rating with detailed explanation"),
                cultivating_change_talk=GlobalRatingItem(score=3, rationale="Mock rating with detailed explanation"),
                softening_sustain_talk=GlobalRatingItem(score=3, rationale="Mock rating with detailed explanation")
            ),
            key_moments=[
                KeyMoment(
                    turn_quote="This is a mock quote from the conversation",
                    explanation="This moment demonstrates effective use of reflective listening"
                )
            ],
            client_language_themes="Mock themes about client change talk and resistance patterns",
            practitioner_patterns=PractitionerPatterns(
                strengths="Mock detailed analysis of observed strengths in MI practice",
                challenge_areas="Mock specific areas for improvement with concrete suggestions"
            ),
            actionable_recommendations=ActionableRecommendations(
                immediate_focus="Mock specific actionable recommendation for immediate improvement",
                skill_development="Mock longer-term skill development recommendations"
            )
        )
        
        if include_reflection_prompts:
            # Add reflection-specific data to the report
            report.reflection_prompts = [
                "How did it feel when you used reflective listening in this conversation?",
                "What would you do differently if you had this conversation again?",
                "Which moments felt most natural and effective for you?"
            ]
            report.coaching_observations = "Mock detailed coaching observations about technique usage"
            report.celebration_moments = [
                "Your use of affirmation at turn 5 was particularly effective",
                "The complex reflection at turn 12 really captured the client's ambivalence"
            ]
            report.growth_opportunities = [
                "Practice more open-ended questions to elicit change talk",
                "Work on rolling with resistance rather than correcting"
            ]
        
        return report
    
    def _fallback_coding(self, batch: List[ParsedTurn]) -> List[AnnotatedTurn]:
        """Fallback coding when API fails"""
        return [
            AnnotatedTurn(
                turn_index=turn.original_index,
                speaker=turn.speaker,
                text=turn.text,
                codes=[MitiCode.O] if turn.speaker == SpeakerRole.PRACTITIONER else [MitiCode.NEUTRAL],
                confidence=0.1
            )
            for turn in batch
        ]
    
    def _fallback_report(self) -> SupervisoryReportData:
        """Fallback report when API fails"""
        return SupervisoryReportData(
            global_ratings=GlobalRatings(
                partnership=GlobalRatingItem(score=3, rationale="Unable to generate rating"),
                empathy=GlobalRatingItem(score=3, rationale="Unable to generate rating"),
                cultivating_change_talk=GlobalRatingItem(score=3, rationale="Unable to generate rating"),
                softening_sustain_talk=GlobalRatingItem(score=3, rationale="Unable to generate rating")
            ),
            key_moments=[],
            client_language_themes="Analysis unavailable",
            practitioner_patterns=PractitionerPatterns(
                strengths="Analysis unavailable",
                challenge_areas="Analysis unavailable"
            ),
            actionable_recommendations=ActionableRecommendations(
                immediate_focus="Please retry analysis",
                skill_development="Analysis unavailable"
            )
        )
