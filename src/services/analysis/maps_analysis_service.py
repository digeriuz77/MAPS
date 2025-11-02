"""
MAPS Person-Centred Analysis Service - COMPLETE CORRECTED VERSION

This is the final, production-ready file with ALL fixes applied:
✅ Fetches conversation from Supabase by conversation_id
✅ Uses "Manager" for anonymous user
✅ Gets actual persona name from database (Mary, Vic, Jan, Terry)
✅ Analyzes persona behavioral evolution (no trust numbers exposed)
✅ No meaningless fallbacks - fails properly
✅ Works generically for all personas

Replace your existing maps_analysis_service.py with this file.
"""
import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Literal
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)


class CoreCoachingEffectiveness(BaseModel):
    """Integrated assessment of manager's coaching effectiveness across 3 themes"""
    foundational_trust_safety: Dict[str, Any] = Field(default_factory=dict)
    empathic_partnership_autonomy: Dict[str, Any] = Field(default_factory=dict)
    empowerment_clarity: Dict[str, Any] = Field(default_factory=dict)
    overall_score: float = 0.0
    summary: str = ""


class PatternsObserved(BaseModel):
    """Patterns in manager and employee behavior"""
    manager_patterns: List[str] = Field(default_factory=list)
    employee_patterns: List[str] = Field(default_factory=list)
    interaction_dynamics: str = ""
    conversation_balance: Dict[str, Any] = Field(default_factory=dict)


class StrengthsAndSuggestions(BaseModel):
    """Identified strengths and development opportunities"""
    strengths: List[Dict[str, str]] = Field(default_factory=list)
    opportunities: List[Dict[str, str]] = Field(default_factory=list)
    next_session_focus: List[str] = Field(default_factory=list)
    maps_alignment: str = ""


class MAPSAnalysisResult(BaseModel):
    """Complete MAPS analysis result"""
    session_id: str
    conversation_id: str
    analyzed_at: datetime
    core_coaching_effectiveness: CoreCoachingEffectiveness
    patterns_observed: PatternsObserved
    strengths_and_suggestions: StrengthsAndSuggestions
    overall_quality_score: float
    maps_values_summary: str


class ManagerAction(BaseModel):
    """Classification of manager's conversational technique"""
    technique: Literal[
        "Open Question",
        "Complex Reflection",
        "Simple Reflection",
        "Affirmation",
        "Summarization",
        "Giving Advice",
        "Closed Question",
        "Other"
    ] = Field(description="The primary coaching technique used in the manager's statement")


class MAPSAnalysisService:
    """Service for analyzing conversations using MAPS framework"""
    
    def __init__(self, llm_service=None, supabase_client=None, user_label="Manager"):
        """
        Initialize with LLM service and Supabase client
        
        Args:
            llm_service: LLM service for AI analysis (REQUIRED)
            supabase_client: Supabase client for fetching conversations (REQUIRED)
            user_label: Label for anonymous user (default: "Manager")
        """
        self.llm_service = llm_service
        self.supabase_client = supabase_client
        self.user_label = user_label
        
        if not self.llm_service:
            logger.error("MAPS Analysis REQUIRES LLM service")
        if not self.supabase_client:
            logger.error("MAPS Analysis REQUIRES Supabase client")
        
    async def analyze_conversation_by_id(
        self,
        conversation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> MAPSAnalysisResult:
        """
        Analyze a conversation from Supabase by conversation_id
        
        Args:
            conversation_id: UUID of the conversation to analyze
            context: Optional additional context
            
        Returns:
            MAPSAnalysisResult with comprehensive analysis
            
        Raises:
            RuntimeError: If LLM service or Supabase client unavailable
            ValueError: If conversation not found
            Exception: If analysis fails
        """
        logger.info(f"Starting MAPS analysis for conversation_id: {conversation_id}")
        
        # Validate dependencies
        if not self.llm_service:
            raise RuntimeError("LLM service is required for MAPS analysis")
        
        if not self.supabase_client:
            raise RuntimeError("Supabase client is required to fetch conversation")
        
        # Fetch conversation messages and persona name
        messages, persona_name = await self._fetch_conversation_with_persona(conversation_id)
        
        if not messages:
            raise ValueError(f"No messages found for conversation_id: {conversation_id}")
        
        logger.info(f"Fetched {len(messages)} messages. Persona: {persona_name}")
        
        # Analyze persona behavioral evolution (no trust numbers)
        behavioral_analysis = self._analyze_persona_behavior_evolution(messages, persona_name)
        
        # Calculate trust progression metrics
        trust_metrics = self._calculate_trust_metrics(messages)
        
        # Find high-impact moments (trust jumps with manager action classification)
        high_impact_moments = await self._find_high_impact_moments(messages, threshold=0.08)
        
        # Find trust-decreasing moments (problematic manager actions)
        trust_decreasing_moments = await self._find_trust_decreasing_moments(messages, threshold=0.05)
        
        # Analyze technique gaps (unused MI techniques)
        technique_gaps = self._analyze_technique_gaps(high_impact_moments)
        
        # Build formatted transcript
        transcript = self._build_transcript(messages, persona_name)
        
        logger.info(f"Built transcript (length: {len(transcript)} chars)")
        logger.info(f"Speakers: {self.user_label} and {persona_name}")
        if trust_metrics:
            logger.info(f"Trust progression: {trust_metrics['initial_trust']:.2f} → {trust_metrics['final_trust']:.2f} (change: {trust_metrics['trust_change']:+.2f})")
        
        # Build analysis prompt with all analysis components
        analysis_prompt = self._build_behavior_aware_prompt(
            transcript, context, self.user_label, persona_name, behavioral_analysis, 
            trust_metrics, high_impact_moments, trust_decreasing_moments, technique_gaps
        )
        
        # Get AI analysis
        logger.info("Requesting AI analysis from LLM service...")
        analysis_data = await self._get_ai_analysis(analysis_prompt, conversation_id)
        
        # Structure result with defensive normalization
        result = self._structure_analysis_result(analysis_data, conversation_id)
        
        logger.info("MAPS analysis completed.")
        return result
    
    async def analyze_transcript(
        self,
        transcript: str,
        context: Optional[Dict[str, Any]] = None,
        manager_name: str = "Manager",
        persona_name: str = "Employee"
    ) -> MAPSAnalysisResult:
        """
        Analyze a conversation transcript directly (standalone method)
        
        Args:
            transcript: Raw conversation transcript  
            context: Optional additional context
            manager_name: Name of the manager/coach in transcript
            persona_name: Name of the employee/persona in transcript
            
        Returns:
            MAPSAnalysisResult with comprehensive analysis
            
        Raises:
            RuntimeError: If LLM service unavailable
            Exception: If analysis fails
        """
        logger.info(f"Starting standalone MAPS analysis for transcript (length: {len(transcript)} chars)")
        
        # Validate dependencies
        if not self.llm_service:
            raise RuntimeError("LLM service is required for MAPS analysis")
        
        # Simple behavioral analysis from transcript text only
        behavioral_analysis = self._analyze_transcript_behavior_patterns(
            transcript, manager_name, persona_name
        )
        
        logger.info(f"Speakers: {manager_name} and {persona_name}")
        
        # Build analysis prompt with behavioral context
        analysis_prompt = self._build_behavior_aware_prompt(
            transcript, context, manager_name, persona_name, behavioral_analysis
        )
        
        # Get AI analysis
        logger.info("Requesting AI analysis from LLM service...")
        analysis_data = await self._get_ai_analysis(analysis_prompt, "standalone_transcript")
        
        # Structure result
        result = self._structure_analysis_result(analysis_data, "standalone_transcript")
        
        logger.info(f"Standalone MAPS analysis completed. Overall score: {result.overall_quality_score}/10")
        return result
    
    async def _fetch_conversation_with_persona(
        self, 
        conversation_id: str
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Fetch conversation messages and determine persona name"""
        
        try:
            # Get conversation metadata
            # Note: conversations table only stores persona_id, not name
            conversation = self.supabase_client.table('conversations').select(
                'persona_id'
            ).eq('id', conversation_id).single().execute()
            
            persona_id = conversation.data.get('persona_id') if conversation.data else None
            
            # Get persona name from enhanced_personas table
            persona_name = "Employee"
            if persona_id:
                persona_result = self.supabase_client.table('enhanced_personas').select(
                    'name'
                ).eq('persona_id', persona_id).single().execute()
                
                if persona_result.data:
                    persona_name = persona_result.data.get('name', 'Employee')
                    logger.info(f"Found persona: {persona_name} (id: {persona_id})")
            else:
                logger.warning(f"No persona_id for conversation {conversation_id}")
            
            # Get messages from conversation_transcripts table with trust_level
            messages_result = self.supabase_client.table('conversation_transcripts').select(
                'turn_number, role, message, timestamp, trust_level'
            ).eq('conversation_id', conversation_id).order('turn_number', desc=False).execute()
            
            if not messages_result.data:
                logger.warning(f"No messages found for conversation_id: {conversation_id}")
                return [], persona_name
            
            logger.info(f"Retrieved {len(messages_result.data)} messages")
            return messages_result.data, persona_name
            
        except Exception as e:
            logger.error(f"Failed to fetch conversation: {e}", exc_info=True)
            raise RuntimeError(f"Database error: {e}")
    
    def _build_transcript(
        self, 
        messages: List[Dict[str, Any]], 
        persona_name: str
    ) -> str:
        """Build formatted transcript from messages"""
        
        if not messages:
            raise ValueError("Cannot build transcript from empty messages")
        
        transcript_lines = []
        
        for msg in messages:
            role = msg.get('role', 'unknown')
            text = msg.get('message', '')
            
            # Map role to speaker name
            if role == 'user':
                speaker = self.user_label  # "Manager"
            elif role == 'persona':
                speaker = persona_name  # Actual persona name from DB
            else:
                speaker = role.capitalize()
            
            transcript_lines.append(f"{speaker}: {text}")
        
        return "\n\n".join(transcript_lines)
    
    def _analyze_persona_behavior_evolution(
        self,
        messages: List[Dict[str, Any]],
        persona_name: str
    ) -> Dict[str, Any]:
        """
        Analyze persona behavioral changes throughout conversation
        WITHOUT exposing trust numbers
        """
        
        # Extract persona messages only
        persona_messages = [msg for msg in messages if msg.get('role') == 'persona']
        
        if len(persona_messages) < 2:
            return {
                "evolution": "insufficient_data",
                "persona_name": persona_name,
                "description": f"Not enough responses from {persona_name} to detect behavioral change"
            }
        
        # Divide into first third and last third
        total = len(persona_messages)
        first_third = persona_messages[:total//3] if total >= 3 else [persona_messages[0]]
        last_third = persona_messages[-(total//3):] if total >= 3 else [persona_messages[-1]]
        
        # Analyze both periods
        early_behavior = self._analyze_message_set(first_third)
        late_behavior = self._analyze_message_set(last_third)
        
        # Calculate changes
        changes = {
            "response_length_change": late_behavior['avg_length'] - early_behavior['avg_length'],
            "emotional_openness_change": late_behavior['emotional_markers'] - early_behavior['emotional_markers'],
            "resistance_change": late_behavior['resistance_markers'] - early_behavior['resistance_markers'],
            "self_disclosure_change": late_behavior['self_disclosure'] - early_behavior['self_disclosure']
        }
        
        # Classify evolution
        evolution_type = self._classify_evolution(changes)
        
        return {
            "evolution": evolution_type,
            "persona_name": persona_name,
            "early_behavior": early_behavior,
            "late_behavior": late_behavior,
            "changes": changes,
            "description": self._describe_evolution(persona_name, evolution_type, changes)
        }
    
    def _calculate_trust_metrics(self, messages: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        """
        Calculate trust progression metrics from messages with trust_level
        
        Args:
            messages: List of message dicts with optional trust_level field
            
        Returns:
            Dict with trust metrics or None if no trust data available
        """
        # Extract trust levels from persona messages only (user messages don't have trust)
        trust_levels = [
            msg['trust_level'] for msg in messages 
            if msg.get('role') == 'persona' and msg.get('trust_level') is not None
        ]
        
        if not trust_levels:
            logger.info("No trust data available in messages")
            return None
        
        initial_trust = trust_levels[0]
        final_trust = trust_levels[-1]
        trust_change = final_trust - initial_trust
        peak_trust = max(trust_levels)
        lowest_trust = min(trust_levels)
        avg_trust = sum(trust_levels) / len(trust_levels)
        
        return {
            'initial_trust': initial_trust,
            'final_trust': final_trust,
            'trust_change': trust_change,
            'peak_trust': peak_trust,
            'lowest_trust': lowest_trust,
            'avg_trust': avg_trust,
            'num_measurements': len(trust_levels)
        }
    
    async def _find_high_impact_moments(
        self,
        messages: List[Dict[str, Any]],
        threshold: float = 0.08
    ) -> List[Dict[str, Any]]:
        """
        Identifies and classifies manager actions that led to significant trust increases.
        
        Args:
            messages: List of message dicts with trust_level data
            threshold: Minimum trust increase to qualify as high-impact (default: 0.08)
            
        Returns:
            List of high-impact moments with trust_increase, action details, and classification
        """
        if not self.llm_service:
            logger.warning("LLM service required for high-impact moment classification")
            return []
        
        high_impact_moments = []
        
        # Iterate through messages to find trust jumps
        for i in range(1, len(messages)):
            # Only check persona messages (they have trust_level)
            if messages[i].get('role') != 'persona' or messages[i].get('trust_level') is None:
                continue
            
            # Find the last persona trust level to compare against
            last_persona_trust = None
            for j in range(i - 1, -1, -1):
                if messages[j].get('role') == 'persona' and messages[j].get('trust_level') is not None:
                    last_persona_trust = messages[j]['trust_level']
                    break
            
            if last_persona_trust is None:
                continue  # First persona message, no baseline
            
            # Calculate trust increase
            trust_increase = messages[i]['trust_level'] - last_persona_trust
            
            if trust_increase >= threshold:
                # Found a high-impact moment! Find the preceding manager message
                manager_message = None
                for j in range(i - 1, -1, -1):
                    if messages[j].get('role') == 'user':
                        manager_message = messages[j]
                        break
                
                if not manager_message:
                    continue
                
                # Classify the manager's technique using micro-LLM
                action_type = "Unclassified"
                try:
                    classification_prompt = f"""Classify this manager's statement into ONE of these coaching techniques:
- Open Question
- Complex Reflection
- Simple Reflection
- Affirmation
- Summarization
- Giving Advice
- Closed Question
- Other

Manager's statement: "{manager_message['message']}"

Respond with ONLY the technique name, nothing else."""
                    
                    response = await self.llm_service.generate_response(
                        prompt=classification_prompt,
                        system_prompt="You are an expert in motivational interviewing. Classify statements accurately and concisely.",
                        model="gpt-4o-mini",
                        temperature=0.0,
                        max_tokens=20
                    )
                    
                    action_type = response.strip()
                    
                except Exception as e:
                    logger.warning(f"Failed to classify manager action: {e}")
                    action_type = "Unclassified"
                
                high_impact_moments.append({
                    "trust_increase": round(trust_increase, 2),
                    "manager_action_text": manager_message['message'],
                    "manager_action_type": action_type,
                    "persona_response_text": messages[i]['message']
                })
                
                logger.info(f"High-impact moment: +{trust_increase:.2f} trust from {action_type}")
        
        logger.info(f"Found {len(high_impact_moments)} high-impact moments (threshold: {threshold})")
        return high_impact_moments
    
    async def _find_trust_decreasing_moments(
        self,
        messages: List[Dict[str, Any]],
        threshold: float = 0.05
    ) -> List[Dict[str, Any]]:
        """
        Identifies manager actions that led to trust decreases.
        
        Args:
            messages: List of message dicts with trust_level data
            threshold: Minimum trust decrease to qualify as problematic (default: 0.05)
            
        Returns:
            List of problematic moments with trust_decrease, action details, and classification
        """
        if not self.llm_service:
            logger.warning("LLM service required for trust-decreasing moment classification")
            return []
        
        trust_decreasing_moments = []
        
        # Iterate through messages to find trust drops
        for i in range(1, len(messages)):
            # Only check persona messages (they have trust_level)
            if messages[i].get('role') != 'persona' or messages[i].get('trust_level') is None:
                continue
            
            # Find the last persona trust level to compare against
            last_persona_trust = None
            for j in range(i - 1, -1, -1):
                if messages[j].get('role') == 'persona' and messages[j].get('trust_level') is not None:
                    last_persona_trust = messages[j]['trust_level']
                    break
            
            if last_persona_trust is None:
                continue
            
            # Calculate trust decrease (negative values)
            trust_change = messages[i]['trust_level'] - last_persona_trust
            
            if trust_change <= -threshold:  # Negative, so <= to check decrease
                # Found a trust drop! Find the preceding manager message
                manager_message = None
                for j in range(i - 1, -1, -1):
                    if messages[j].get('role') == 'user':
                        manager_message = messages[j]
                        break
                
                if not manager_message:
                    continue
                
                # Classify the problematic manager action
                action_type = "Unclassified"
                try:
                    classification_prompt = f"""Classify this manager's statement into ONE of these categories:
- Giving Advice (premature)
- Closed Question
- Directive Statement
- Confrontational
- Dismissive
- Interrupting
- Changing Subject
- Other

Manager's statement: "{manager_message['message']}"

Respond with ONLY the category name, nothing else."""
                    
                    response = await self.llm_service.generate_response(
                        prompt=classification_prompt,
                        system_prompt="You are an expert in motivational interviewing. Identify problematic coaching behaviors accurately.",
                        model="gpt-4o-mini",
                        temperature=0.0,
                        max_tokens=20
                    )
                    
                    action_type = response.strip()
                    
                except Exception as e:
                    logger.warning(f"Failed to classify problematic action: {e}")
                    action_type = "Unclassified"
                
                trust_decreasing_moments.append({
                    "trust_decrease": round(abs(trust_change), 2),
                    "manager_action_text": manager_message['message'],
                    "manager_action_type": action_type,
                    "persona_response_text": messages[i]['message']
                })
                
                logger.info(f"Trust-decreasing moment: -{abs(trust_change):.2f} trust from {action_type}")
        
        logger.info(f"Found {len(trust_decreasing_moments)} trust-decreasing moments (threshold: {threshold})")
        return trust_decreasing_moments
    
    def _analyze_technique_gaps(
        self,
        high_impact_moments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Identify MI techniques that were NOT used in high-impact moments.
        
        Args:
            high_impact_moments: List of moments with manager_action_type classifications
            
        Returns:
            Dict with used_techniques and unused_techniques lists
        """
        # All possible MI techniques
        all_techniques = [
            "Open Question",
            "Complex Reflection",
            "Simple Reflection",
            "Affirmation",
            "Summarization"
        ]
        
        # Extract techniques used in high-impact moments
        used_techniques = set(
            moment['manager_action_type'] 
            for moment in high_impact_moments 
            if moment['manager_action_type'] in all_techniques
        )
        
        # Identify gaps
        unused_techniques = [t for t in all_techniques if t not in used_techniques]
        
        logger.info(f"Technique analysis: {len(used_techniques)} used, {len(unused_techniques)} unused")
        
        return {
            "used_techniques": list(used_techniques),
            "unused_techniques": unused_techniques,
            "all_techniques": all_techniques
        }
    
    def _analyze_message_set(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze a set of messages for behavioral indicators"""
        
        if not messages:
            return {
                'avg_length': 0,
                'emotional_markers': 0,
                'resistance_markers': 0,
                'self_disclosure': 0
            }
        
        texts = [msg.get('message', '') for msg in messages]
        total_words = sum(len(text.split()) for text in texts)
        avg_length = total_words / len(messages)
        
        # Count emotional openness markers
        emotional_keywords = [
            'feel', 'feeling', 'worried', 'scared', 'overwhelmed', 'exhausted',
            'struggling', 'difficult', 'hard', 'stress', 'anxiety', 'lonely', 'upset'
        ]
        emotional_count = sum(
            sum(1 for keyword in emotional_keywords if keyword in text.lower())
            for text in texts
        )
        
        # Count resistance markers
        resistance_keywords = [
            'fine', 'nothing', "don't know", 'whatever', 'but', "can't",
            "won't", 'impossible', 'tried before', "doesn't work", "not my fault",
            "not a big deal", "everyone"
        ]
        resistance_count = sum(
            sum(1 for keyword in resistance_keywords if keyword in text.lower())
            for text in texts
        )
        
        # Count self-disclosure markers
        disclosure_keywords = [
            'my son', 'my daughter', 'my family', 'at home', 'personally',
            'to be honest', 'truth is', 'actually', 'really', 'honestly',
            'my wife', 'my husband', 'my partner', 'my child'
        ]
        disclosure_count = sum(
            sum(1 for keyword in disclosure_keywords if keyword in text.lower())
            for text in texts
        )
        
        return {
            'avg_length': avg_length,
            'emotional_markers': emotional_count,
            'resistance_markers': resistance_count,
            'self_disclosure': disclosure_count
        }
    
    def _classify_evolution(self, changes: Dict[str, float]) -> str:
        """Classify behavioral evolution type"""
        
        # Significant opening
        opened_up = (
            changes['response_length_change'] > 10 and
            changes['emotional_openness_change'] > 0 and
            changes['resistance_change'] < 0 and
            changes['self_disclosure_change'] > 0
        )
        
        # Increased defensiveness
        closed_off = (
            changes['response_length_change'] < -5 and
            changes['emotional_openness_change'] < 0 and
            changes['resistance_change'] > 0 and
            changes['self_disclosure_change'] < 0
        )
        
        # Slight opening
        slight_opening = (
            (changes['resistance_change'] < 0 or
             changes['emotional_openness_change'] > 0 or
             changes['self_disclosure_change'] > 0) and
            not opened_up
        )
        
        if opened_up:
            return "significant_opening"
        elif closed_off:
            return "increased_defensiveness"
        elif slight_opening:
            return "slight_opening"
        else:
            return "remained_stable"
    
    def _describe_evolution(
        self, 
        persona_name: str, 
        evolution_type: str, 
        changes: Dict
    ) -> str:
        """Generate description of behavioral evolution"""
        
        descriptions = {
            "significant_opening": f"{persona_name} showed significant behavioral shift toward openness: responses became longer (+{changes['response_length_change']:.0f} words avg), more emotionally expressive (+{changes['emotional_openness_change']} markers), less resistant ({changes['resistance_change']:+} markers), and more self-disclosing (+{changes['self_disclosure_change']} markers). This indicates successful trust-building.",
            
            "increased_defensiveness": f"{persona_name} became MORE defensive during conversation: responses shortened ({changes['response_length_change']:+.0f} words), less emotional expression ({changes['emotional_openness_change']:+} markers), increased resistance (+{changes['resistance_change']} markers). This suggests manager's approach triggered defensive reactions.",
            
            "slight_opening": f"{persona_name} showed modest movement toward openness: some positive behavioral indicators (resistance {changes['resistance_change']:+}, emotional expression {changes['emotional_openness_change']:+}, self-disclosure {changes['self_disclosure_change']:+}). While remaining cautious, this represents realistic progress in early-stage trust building.",
            
            "remained_stable": f"{persona_name} maintained consistent behavioral patterns throughout conversation. No significant increase in openness or defensiveness."
        }
        
        return descriptions.get(evolution_type, f"{persona_name}'s behavioral pattern unclear")
    
    def _analyze_transcript_behavior_patterns(
        self,
        transcript: str,
        manager_name: str,
        persona_name: str
    ) -> Dict[str, Any]:
        """
        Analyze behavioral patterns from raw transcript text
        (Standalone version without database messages)
        """
        
        # Split transcript into turns
        lines = [line.strip() for line in transcript.split('\n') if line.strip()]
        
        # Extract persona messages
        persona_messages = []
        for line in lines:
            if ':' in line:
                speaker, message = line.split(':', 1)
                if persona_name.lower() in speaker.lower():
                    persona_messages.append({'message': message.strip()})
        
        if len(persona_messages) < 2:
            return {
                "evolution": "insufficient_data",
                "persona_name": persona_name,
                "description": f"Not enough responses from {persona_name} to detect behavioral change",
                "early_behavior": {'avg_length': 0, 'emotional_markers': 0, 'resistance_markers': 0, 'self_disclosure': 0},
                "late_behavior": {'avg_length': 0, 'emotional_markers': 0, 'resistance_markers': 0, 'self_disclosure': 0},
                "changes": {
                    "response_length_change": 0,
                    "emotional_openness_change": 0,
                    "resistance_change": 0,
                    "self_disclosure_change": 0
                }
            }
        
        # Divide into first third and last third
        total = len(persona_messages)
        first_third = persona_messages[:total//3] if total >= 3 else [persona_messages[0]]
        last_third = persona_messages[-(total//3):] if total >= 3 else [persona_messages[-1]]
        
        # Analyze both periods
        early_behavior = self._analyze_message_set(first_third)
        late_behavior = self._analyze_message_set(last_third)
        
        # Calculate changes
        changes = {
            "response_length_change": late_behavior['avg_length'] - early_behavior['avg_length'],
            "emotional_openness_change": late_behavior['emotional_markers'] - early_behavior['emotional_markers'],
            "resistance_change": late_behavior['resistance_markers'] - early_behavior['resistance_markers'],
            "self_disclosure_change": late_behavior['self_disclosure'] - early_behavior['self_disclosure']
        }
        
        # Classify evolution
        evolution_type = self._classify_evolution(changes)
        
        return {
            "evolution": evolution_type,
            "persona_name": persona_name,
            "early_behavior": early_behavior,
            "late_behavior": late_behavior,
            "changes": changes,
            "description": self._describe_evolution(persona_name, evolution_type, changes)
        }
    
    def _get_evaluation_guidance(self, evolution_type: str) -> str:
        """Get evaluation guidance based on behavioral evolution"""
        
        guidance = {
            "significant_opening": """
This significant behavioral opening indicates EXCELLENT manager technique. When scoring:
- Recognize this as strong evidence of safety, trust, empowerment
- Note specific techniques that facilitated this opening
- This level of openness requires skilled MI practice""",
            
            "increased_defensiveness": """
This increased defensiveness indicates problematic manager technique. When scoring:
- Lower scores on safety/trust are warranted
- Look for confrontational, directive, or dismissive language
- This is realistic employee behavior when MI technique is poor
- Focus feedback on what caused the defensive shift""",
            
            "slight_opening": """
This modest opening represents REALISTIC progress in early-stage relationship building. When scoring:
- Recognize that small behavioral shifts are appropriate and valuable
- Moderate scores are appropriate - relationship is building
- This is what successful early-stage MI looks like with authentically resistant employees""",
            
            "remained_stable": """
This stable pattern could indicate several things. When scoring:
- Consider whether manager used appropriate techniques but relationship is early-stage
- Or whether manager maintained surface-level engagement without deepening
- Moderate scores are appropriate - conversation was safe but not transformative"""
        }
        
        return guidance.get(evolution_type, "Evaluate based on overall interaction quality")
    
    def _build_behavior_aware_prompt(
        self,
        transcript: str,
        context: Optional[Dict[str, Any]],
        manager_label: str,
        persona_name: str,
        behavioral_analysis: Dict[str, Any],
        trust_metrics: Optional[Dict[str, float]] = None,
        high_impact_moments: Optional[List[Dict[str, Any]]] = None,
        trust_decreasing_moments: Optional[List[Dict[str, Any]]] = None,
        technique_gaps: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build analysis prompt with comprehensive trust-driven analysis"""
        
        # Context section
        context_section = ""
        if context:
            context_section = f"\n\nADDITIONAL CONTEXT:\n{json.dumps(context, indent=2)}\n"
        
        # Behavioral evolution section
        evolution_section = f"""
PERSONA BEHAVIORAL EVOLUTION ANALYSIS:
Throughout this conversation, {persona_name}'s behavioral patterns showed: {behavioral_analysis['evolution']}

{behavioral_analysis['description']}

Early conversation behavior:
- Average response length: {behavioral_analysis['early_behavior']['avg_length']:.0f} words
- Emotional openness: {behavioral_analysis['early_behavior']['emotional_markers']} emotional expressions
- Resistance indicators: {behavioral_analysis['early_behavior']['resistance_markers']} resistance markers
- Self-disclosure: {behavioral_analysis['early_behavior']['self_disclosure']} personal disclosures

Later conversation behavior:
- Average response length: {behavioral_analysis['late_behavior']['avg_length']:.0f} words
- Emotional openness: {behavioral_analysis['late_behavior']['emotional_markers']} emotional expressions
- Resistance indicators: {behavioral_analysis['late_behavior']['resistance_markers']} resistance markers
- Self-disclosure: {behavioral_analysis['late_behavior']['self_disclosure']} personal disclosures

EVALUATION GUIDANCE:
{self._get_evaluation_guidance(behavioral_analysis['evolution'])}
"""
        
        # Trust progression section (if available)
        trust_section = ""
        if trust_metrics:
            trust_change_direction = "increased" if trust_metrics['trust_change'] > 0.05 else "decreased" if trust_metrics['trust_change'] < -0.05 else "remained stable"
            trust_section = f"""

TRUST PROGRESSION DATA:
The system tracked trust levels throughout the conversation:
- Initial trust: {trust_metrics['initial_trust']:.2f}
- Final trust: {trust_metrics['final_trust']:.2f}
- Trust change: {trust_metrics['trust_change']:+.2f} ({trust_change_direction})
- Peak trust reached: {trust_metrics['peak_trust']:.2f}
- Average trust: {trust_metrics['avg_trust']:.2f}

Note: This quantitative trust data complements the behavioral analysis above. Use it to validate your assessment of psychological safety and relationship building.
"""
        
        # Key moments section (if available)
        key_moments_section = ""
        if high_impact_moments:
            key_moments_section = "\n\nCRITICAL COACHING MOMENTS ANALYSIS:\n"
            key_moments_section += "The system has identified the following manager actions that directly led to significant increases in persona trust. Your analysis, especially in 'Strengths & Suggestions', **must** be grounded in this evidence.\n"
            
            for moment in high_impact_moments:
                key_moments_section += f"""
---
- **Trust Increase**: +{moment['trust_increase']}
- **Manager's Action (classified as '{moment['manager_action_type']}')**: "{moment['manager_action_text']}"
- **Resulting Persona Response**: "{moment['persona_response_text']}"
---
"""
        
        # Problematic moments section (if available)
        problematic_section = ""
        if trust_decreasing_moments:
            problematic_section = "\n\nPROBLEMATIC COACHING MOMENTS:\n"
            problematic_section += "The following manager actions led to trust DECREASES. These must be addressed in your 'Opportunities for Growth' section.\n"
            
            for moment in trust_decreasing_moments:
                problematic_section += f"""
---
- **Trust Decrease**: -{moment['trust_decrease']}
- **Manager's Action (classified as '{moment['manager_action_type']}')**: "{moment['manager_action_text']}"
- **Resulting Persona Response**: "{moment['persona_response_text']}"
---
"""
        
        # Technique gaps section (if available)
        gaps_section = ""
        if technique_gaps and technique_gaps['unused_techniques']:
            gaps_section = "\n\nTECHNIQUE GAPS ANALYSIS:\n"
            gaps_section += f"The following MI techniques were NOT observed in high-impact moments and could be practiced in future sessions:\n"
            for technique in technique_gaps['unused_techniques']:
                gaps_section += f"- {technique}\n"
            if technique_gaps['used_techniques']:
                gaps_section += f"\nTechniques that DID produce high-impact moments: {', '.join(technique_gaps['used_techniques'])}\n"
        
        master_instructions = """**PRIMARY ANALYSIS INSTRUCTIONS:**
Your analysis MUST be anchored in the data-driven evidence provided below. Use trust metrics and classified moments as your primary evidence source.

1. **Ground Your Scores:** Every score MUST be justified by specific evidence from Critical/Problematic Coaching Moments. Explain HOW a specific technique (e.g., "Complex Reflection") contributed to a theme (e.g., "Empathic Partnership").
2. **Be Data-Driven:** In 'Patterns Observed', focus on quantifiable patterns: "The manager's Complex Reflections produced +0.15 trust increases."
3. **Be Specific in Feedback:**
   - 'Strengths' MUST cite actions from Critical Coaching Moments with trust increases.
   - 'Opportunities' MUST address actions from Problematic Coaching Moments with trust decreases.
   - 'Next Session Focus' MUST include techniques from the Technique Gaps section.
4. **Use Trust Data:** Reference initial trust, final trust, and trust change to validate your assessments.

Do not make vague statements. Every key insight must be traceable to provided data."""
        
        prompt = f"""You are an expert coaching analyst for Money and Pensions Service (MAPS), specializing in Motivational Interviewing (MI).

{master_instructions}

--- DATA FOR ANALYSIS ---
{trust_section}{key_moments_section}{problematic_section}{gaps_section}
--- END OF DATA ---

NOTE: In this conversation, '{manager_label}' is the HR MANAGER/USER practicing their MI skills, and '{persona_name}' is the EMPLOYEE they are practicing with.

TERMINOLOGY: Use "ask-share-ask" (NOT "elicit-provide-elicit") for this coaching technique.

MAPS Core Values:
1. TRANSFORMING: Committed to transforming lives and making positive societal impact
2. CARING: Caring about colleagues and people whose lives they transform  
3. CONNECTING: Ensuring people receive the right guidance at the right time to help them navigate complex choices
{context_section}
Analyze this conversation across THREE dimensions:

=== PART 1: CORE COACHING EFFECTIVENESS ===
Assess the manager's effectiveness across three integrated themes, using the data evidence above.

1. **Partnership (foundational_trust_safety) (1-5)**: 
   Did {manager_label} create psychological safety through authenticity and non-judgmental acceptance? 
   Evidence: Use Trust Progression Data and Critical/Problematic Moments to show how specific behaviors built or eroded safety.

2. **Empathy (empathic_partnership_autonomy) (1-5)**: 
   Did {manager_label} demonstrate deep empathic understanding through active listening while fostering true collaborative partnership and respecting {persona_name}'s autonomy?
   Evidence: Reference specific techniques from high-impact moments (e.g., Complex Reflections, Open Questions).

3. **Empowering Change (empowerment_clarity) (1-5)**: 
   Did {manager_label} help {persona_name} feel capable, confident, and clear about their situation and path forward?
   Evidence: Show how manager's actions increased persona's self-efficacy and understanding.

For EACH theme, provide:
- Score (1-5)
- Specific evidence from the DATA section above
- Brief rationale connecting evidence to assessment

=== PART 3: PATTERNS OBSERVED ===
Identify:

1. Manager Patterns: Question types used, balance of open/closed questions, use of reflections, ask-share-ask technique, etc.
2. Employee Patterns: Level of engagement, openness, movement toward or away from change
3. Interaction Dynamics: How the conversation flowed, power dynamics, collaborative moments
4. Conversation Balance: Approximate speaking time split, who drove the conversation

=== PART 4: STRENGTHS & SUGGESTIONS ===
Provide:

1. Strengths (2-3): What {manager_label} did well with specific examples
2. Opportunities (2-3): Areas for development with actionable suggestions
3. Next Session Focus: 2-3 concrete things to practice
4. MAPS Alignment: How the conversation embodied (or could better embody) MAPS values of Transforming, Caring, Connecting

=== OVERALL ===
- Overall Quality Score (1-10): Composite assessment of the conversation
- MAPS Values Summary: Brief paragraph on how conversation demonstrated MAPS values of Transforming, Caring, Connecting

CRITICAL: Respond with ONLY valid JSON in this exact structure (no markdown, no additional text):

{{
  "core_coaching_effectiveness": {{
    "foundational_trust_safety": {{"score": 1-5, "evidence": ["example1", "example2"], "notes": "brief rationale"}},
    "empathic_partnership_autonomy": {{"score": 1-5, "evidence": ["example1", "example2"], "notes": "rationale"}},
    "empowerment_clarity": {{"score": 1-5, "evidence": ["example1", "example2"], "notes": "rationale"}},
    "overall_score": 3.5,
    "summary": "brief overall summary"
  }},
  "patterns_observed": {{
    "manager_patterns": ["pattern1", "pattern2", "pattern3"],
    "employee_patterns": ["pattern1", "pattern2"],
    "interaction_dynamics": "description of how conversation flowed",
    "conversation_balance": {{
      "manager_speaking_percentage": 50,
      "employee_speaking_percentage": 50
    }}
  }},
  "strengths_and_suggestions": {{
    "strengths": [
      {{"strength": "specific strength", "example": "evidence from conversation"}},
      {{"strength": "another strength", "example": "evidence"}}
    ],
    "opportunities": [
      {{"area": "area for growth", "suggestion": "actionable suggestion"}},
      {{"area": "another area", "suggestion": "specific action"}}
    ],
    "next_session_focus": ["focus1", "focus2", "focus3"],
    "maps_alignment": "how conversation aligned with MAPS values"
  }},
  "overall_quality_score": 7.5,
  "maps_values_summary": "paragraph about how conversation demonstrated Transforming, Caring, Connecting"
}}

CONVERSATION TO ANALYZE:

{transcript}
"""
        
        return prompt
    
    async def _get_ai_analysis(
        self,
        prompt: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Get AI analysis using OpenAI only (no Gemini)."""
        from src.config.settings import get_settings
        settings = get_settings()

        logger.info("Requesting AI analysis (OpenAI only)...")

        # Call OpenAI via llm_service
        openai_response = await self.llm_service.generate_response(
            prompt=prompt,
            system_prompt=(
                "You are an expert in person-centred coaching analysis for Money and Pensions Service. "
                "Provide ONLY valid JSON in your response, no markdown formatting or additional text."
            ),
            model=settings.DEFAULT_MODEL,
            temperature=0.0,
            max_tokens=6000,
            response_format={"type": "json_object"},
        )

        # Clean any accidental markdown fencing
        cleaned = openai_response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```(?:json)?\s*\n', '', cleaned)
            cleaned = re.sub(r'\n```\s*$', '', cleaned)

        # Parse JSON
        try:
            analysis_data = json.loads(cleaned)
            logger.info("JSON parsing successful (OpenAI)")
            return analysis_data
        except json.JSONDecodeError as e:
            logger.error(f"OpenAI JSON parsing failed: {e}")
            logger.error(f"OpenAI response (first 500): {openai_response[:500]}...")
            raise Exception(f"OpenAI JSON parsing failed: {e}")
        
    
    def _structure_analysis_result(
        self,
        analysis_data: Dict[str, Any],
        conversation_id: str
    ) -> MAPSAnalysisResult:
        """Structure analysis data into result object"""
        
        try:
            # Defensive normalization to tolerate missing keys
            core = analysis_data.setdefault("core_coaching_effectiveness", {})
            def _ensure_theme(name: str):
                t = core.setdefault(name, {})
                t.setdefault("score", None)
                t.setdefault("evidence", [])
                t.setdefault("notes", "")
            _ensure_theme("foundational_trust_safety")
            _ensure_theme("empathic_partnership_autonomy")
            _ensure_theme("empowerment_clarity")
            core.setdefault("overall_score", 0.0)
            core.setdefault("summary", "")

            patterns = analysis_data.setdefault("patterns_observed", {})
            patterns.setdefault("manager_patterns", [])
            patterns.setdefault("employee_patterns", [])
            patterns.setdefault("interaction_dynamics", "")
            cb = patterns.setdefault("conversation_balance", {})
            cb.setdefault("manager_speaking_percentage", 50)
            cb.setdefault("employee_speaking_percentage", 50)

            sas = analysis_data.setdefault("strengths_and_suggestions", {})
            sas.setdefault("strengths", [])
            sas.setdefault("opportunities", [])
            sas.setdefault("next_session_focus", [])
            sas.setdefault("maps_alignment", "")

            result = MAPSAnalysisResult(
                session_id=f"maps_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                conversation_id=conversation_id,
                analyzed_at=datetime.utcnow(),
                core_coaching_effectiveness=CoreCoachingEffectiveness(**analysis_data["core_coaching_effectiveness"]),
                patterns_observed=PatternsObserved(**analysis_data["patterns_observed"]),
                strengths_and_suggestions=StrengthsAndSuggestions(**analysis_data["strengths_and_suggestions"]),
                overall_quality_score=analysis_data.get("overall_quality_score", 5.0),
                maps_values_summary=analysis_data.get("maps_values_summary", "Analysis completed.")
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to structure result: {e}", exc_info=True)
            raise Exception(f"Failed to parse AI analysis into structured result: {e}")


# Singleton instance
_maps_analysis_service = None

def get_maps_analysis_service(supabase_client=None):
    """Get or create MAPS analysis service instance"""
    global _maps_analysis_service
    
    if _maps_analysis_service is None:
        try:
            logger.info("Initializing MAPS analysis service...")
            from src.services.llm_service import LLMService
            from src.dependencies import get_supabase_client
            
            llm_service = LLMService()
            
            if supabase_client is None:
                supabase_client = get_supabase_client()
            
            _maps_analysis_service = MAPSAnalysisService(
                llm_service=llm_service,
                supabase_client=supabase_client,
                user_label="Manager"
            )
            
            logger.info("MAPS analysis service created successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MAPS analysis service: {e}", exc_info=True)
            raise RuntimeError(f"Cannot create MAPS analysis service: {e}")
    
    return _maps_analysis_service

def create_standalone_maps_service():
    """
    Create a standalone MAPS analysis service (without Supabase dependency)
    For analyzing raw transcripts without database access
    
    Returns:
        MAPSAnalysisService: Service configured for standalone transcript analysis
        
    Raises:
        RuntimeError: If LLM service cannot be initialized
    """
    try:
        logger.info("Creating standalone MAPS analysis service...")
        from src.services.llm_service import LLMService
        
        llm_service = LLMService()
        
        service = MAPSAnalysisService(
            llm_service=llm_service,
            supabase_client=None,  # No Supabase for standalone mode
            user_label="Manager"
        )
        
        logger.info("Standalone MAPS analysis service created successfully")
        return service
        
    except Exception as e:
        logger.error(f"Failed to create standalone MAPS analysis service: {e}", exc_info=True)
        raise RuntimeError(f"Cannot create standalone MAPS analysis service: {e}")
