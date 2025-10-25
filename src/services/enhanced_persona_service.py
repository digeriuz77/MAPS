"""
Enhanced Persona Service - Natural Staged Character Interactions

Features:
- Natural empathy assessment instead of mechanistic scoring
- Staged knowledge revelation based on trust levels
- Contextual behavioral adjustments and micro-context management
- Integrated emotional state tracking
- Single enhanced LLM call with rich context

This service provides a unified, natural approach to persona interactions
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from src.services.llm_service import LLMService
from src.models.conversation_state import ConversationStateManager, ConversationState
from src.config.settings import get_settings
from src.dependencies import get_supabase_client
from src.services.llm_interaction_analyzer import llm_interaction_analyzer, InteractionContext
from src.services.behavioral_tier_service import behavioral_tier_service

logger = logging.getLogger(__name__)

# InteractionContext now imported from llm_interaction_analyzer

@dataclass
class PersonaResponse:
    """Enhanced response with rich context"""
    response: str
    trust_level: float
    interaction_context: InteractionContext
    knowledge_tier_used: str
    emotional_state: str
    stage: str
    character_notes: str  # Internal notes about character's mindset

# EmotionalStateTracker replaced with LLM-powered analyzer
# All pattern matching logic moved to llm_interaction_analyzer.py

class MicroContextManager:
    """Manages persona behavior based on user empathy/pressure patterns"""
    
    def get_behavioral_adjustments(self, interaction_context: InteractionContext, 
                                  trust_level: float, conversation_state: ConversationState) -> Dict[str, Any]:
        """Get micro-adjustments to persona behavior based on interaction context"""
        
        adjustments = {
            "response_length": "normal",
            "emotional_availability": "guarded",
            "information_sharing": "minimal",
            "tone_adjustment": "neutral",
            "defensiveness_level": "moderate"
        }
        
        # Adjust based on interaction quality
        if interaction_context.interaction_quality == "excellent":
            adjustments.update({
                "emotional_availability": "open",
                "information_sharing": "generous",
                "tone_adjustment": "warm",
                "defensiveness_level": "minimal"
            })
        elif interaction_context.interaction_quality == "poor":
            adjustments.update({
                "emotional_availability": "closed",
                "information_sharing": "resistant",
                "tone_adjustment": "cold",
                "defensiveness_level": "high",
                "response_length": "brief"
            })
        
        # Adjust based on trust trajectory
        if interaction_context.trust_trajectory == "declining":
            adjustments["defensiveness_level"] = "high"
            adjustments["information_sharing"] = "resistant"
        elif interaction_context.trust_trajectory == "breakthrough":
            adjustments["emotional_availability"] = "very_open"
            adjustments["information_sharing"] = "vulnerable"
        
        # Adjust based on user approach
        if interaction_context.user_approach == "directive":
            adjustments["defensiveness_level"] = "high"
        elif interaction_context.user_approach == "collaborative":
            adjustments["tone_adjustment"] = "engaged"
        
        return adjustments

class CharacterConsistencyEngine:
    """Ensures AI stays in character throughout conversations"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def validate_character_response(self, persona_data: Dict, response_draft: str, 
                                   trust_level: float, interaction_context: InteractionContext) -> str:
        """Validate and adjust response to maintain character consistency"""
        
        # Get character traits and patterns
        traits = persona_data.get('traits', '')
        system_context = persona_data.get('system_context', '')
        trust_behaviors = persona_data.get('trust_behaviors', {})
        
        # Extract key character rules from system context
        character_rules = self._extract_character_rules(system_context)
        
        # Check for character violations
        violations = self._detect_violations(response_draft, character_rules, trust_level)
        
        if violations:
            logger.info(f"Character consistency violations detected: {violations}")
            # In a production system, you might use an LLM to rewrite the response
            # For now, we'll log the issues
        
        return response_draft
    
    def _extract_character_rules(self, system_context: str) -> List[str]:
        """Extract key character consistency rules from system context"""
        rules = []
        
        # Look for explicit personality patterns
        lines = system_context.split('\n')
        for line in lines:
            if 'PERSONALITY PATTERNS:' in line.upper():
                # Extract subsequent bullet points
                continue
            if line.strip().startswith('-') and any(word in line.lower() for word in 
                ['never', 'always', 'tends to', 'avoids', 'prefers']):
                rules.append(line.strip())
        
        return rules
    
    def _detect_violations(self, response: str, rules: List[str], trust_level: float) -> List[str]:
        """Detect potential character consistency violations"""
        violations = []
        response_lower = response.lower()
        
        # Example violation checks (can be expanded) - using 0.0-1.0 scale
        if trust_level < 0.5 and any(phrase in response_lower for phrase in [
            "let me tell you about", "my son", "my sister", "i'm really struggling"
        ]):
            violations.append("Sharing personal details too early given trust level")
        
        if trust_level > 0.8 and any(phrase in response_lower for phrase in [
            "i don't want to talk about", "that's none of your business", "i don't see why"
        ]):
            violations.append("Being defensive when trust level is high")
        
        return violations

class EnhancedPersonaService:
    """
    Enhanced persona service with natural empathy assessment and staged knowledge revelation
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        self.settings = get_settings()
        self.supabase = get_supabase_client()
        self.state_manager = ConversationStateManager(self.supabase)
        self.emotional_tracker = llm_interaction_analyzer
        self.micro_context_manager = MicroContextManager()
        self.consistency_engine = CharacterConsistencyEngine(self.supabase)
    
    async def process_conversation(
        self,
        user_message: str,
        persona_id: str,
        session_id: str,
        conversation_history: Optional[List[Dict]] = None,
        persona_llm: str = "gpt-4o-mini"
    ) -> PersonaResponse:
        """
        Process conversation using enhanced natural approach
        
        Returns PersonaResponse with rich context and natural empathy assessment
        """
        try:
            # Get persona base data from personas table
            persona_data = await self._get_persona(persona_id)
            persona_name = persona_data.get('name', 'Unknown')
            
            # Get current conversation state (pass persona_id for persona-specific starting trust)
            conversation_state = await self.state_manager.get_conversation_state(session_id, persona_id=persona_id)
            trust_level = getattr(conversation_state, 'trust_level', 0.3)  # 0.0-1.0 scale, not 0-10!
            turn_count = getattr(conversation_state, 'turn_count', 0)
            
            logger.info(f"🎭 Processing turn {turn_count + 1} for {persona_name}, trust={trust_level:.2f}")
            
            # STEP 1: Natural interaction assessment (replaces mechanistic scoring)
            interaction_context = await self.emotional_tracker.assess_interaction_quality(
                user_message, conversation_history or []
            )
            
            logger.info(f"💡 Interaction quality: {interaction_context.interaction_quality}, " +
                       f"empathy: {interaction_context.empathy_tone}, " +
                       f"approach: {interaction_context.user_approach}")
            
            # STEP 2: Get available knowledge for current trust level
            available_knowledge, tier_name = await self._get_available_knowledge(persona_id, trust_level)
            
            # STEP 3: Get micro-behavioral adjustments
            behavioral_adjustments = self.micro_context_manager.get_behavioral_adjustments(
                interaction_context, trust_level, conversation_state
            )
            
            logger.info(f"🎯 Behavioral adjustments: {behavioral_adjustments}")
            
            # STEP 4: Determine sharing boundaries (simplified from staged approach)
            sharing_boundaries = self._determine_natural_boundaries(
                interaction_context, trust_level, behavioral_adjustments, available_knowledge
            )
            
            # STEP 5: Generate persona response with all context
            response = await self._generate_natural_response(
                persona_data=persona_data,
                sharing_boundaries=sharing_boundaries,
                user_message=user_message,
                conversation_history=conversation_history or [],
                interaction_context=interaction_context,
                behavioral_adjustments=behavioral_adjustments,
                persona_llm=persona_llm,
                trust_level=trust_level,
                session_id=session_id,
                stage=conversation_state.stage
            )
            
            # STEP 6: Character consistency validation
            validated_response = self.consistency_engine.validate_character_response(
                persona_data, response, trust_level, interaction_context
            )
            
            # STEP 7: Update conversation state with natural empathy assessment
            natural_mi_analysis = self._convert_to_mi_format(interaction_context)
            updated_state = await self.state_manager.update_conversation_state(
                session_id, natural_mi_analysis, user_message, persona_id=persona_id
            )
            
            # STEP 8: Form dynamic memory (contextual, not mechanistic)
            await self._form_natural_memory(
                session_id=session_id,
                user_message=user_message,
                interaction_context=interaction_context,
                persona_response=validated_response,
                persona_name=persona_name
            )
            
            logger.info(f"✅ Turn complete. New trust: {updated_state.trust_level:.2f}, " +
                       f"stage: {updated_state.stage}")
            
            return PersonaResponse(
                response=validated_response.strip(),
                trust_level=updated_state.trust_level,
                interaction_context=interaction_context,
                knowledge_tier_used=tier_name,
                emotional_state=updated_state.stage,
                stage=updated_state.stage,
                character_notes=f"Trust trajectory: {interaction_context.trust_trajectory}, " +
                              f"Behavioral stance: {behavioral_adjustments.get('emotional_availability', 'guarded')}"
            )
            
        except Exception as e:
            logger.error(f"❌ Enhanced persona processing failed: {e}", exc_info=True)
            raise
    
    async def _get_persona(self, persona_id: str) -> Dict:
        """Get persona base data from enhanced_personas table"""
        try:
            result = self.supabase.table('enhanced_personas').select('*').eq(
                'persona_id', persona_id
            ).maybe_single().execute()
            
            if not result.data:
                raise RuntimeError(f"Enhanced persona '{persona_id}' not found in database. Run migrations 039 & 040.")
            
            return result.data
        except Exception as e:
            raise RuntimeError(f"Failed to fetch enhanced persona '{persona_id}': {e}")
    
    async def _get_available_knowledge_behavioral(self, persona_id: str, trust_level: float, 
                                                interaction_context: InteractionContext, session_id: str = None) -> Tuple[Dict, str, str]:
        """
        Get behavioral context instead of just raw knowledge
        Returns: (knowledge_dict, tier_name, behavioral_prompt)
        """
        try:
            # Get all tiers for this persona
            result = self.supabase.table('character_knowledge_tiers').select('*').eq(
                'persona_id', persona_id
            ).order('trust_threshold', desc=False).execute()
            
            if not result.data:
                raise RuntimeError(f"No knowledge tiers found for {persona_id}")
            
            # Find appropriate tier for current trust level
            appropriate_tier = result.data[0]  # Start with lowest tier
            for tier in result.data:
                if trust_level >= tier['trust_threshold']:
                    appropriate_tier = tier
                else:
                    break
            
            # Get core identity and current situation from persona data
            persona_data = await self._get_persona(persona_id)
            core_identity = persona_data.get('core_identity', '')
            current_situation = persona_data.get('current_situation', '')
            
            # Transform to behavioral context
            behavioral_context = behavioral_tier_service.transform_tier_to_behavioral_context(
                tier_data=appropriate_tier,
                current_trust=trust_level,
                core_identity=core_identity,
                current_situation=current_situation
            )
            
            # Get dynamic action guidance based on user's approach
            recent_actions = await self._get_recent_persona_actions(session_id) if session_id else []
            action_guidance = behavioral_tier_service.get_action_selection_guidance(
                tier_name=behavioral_context.tier_name,
                trainee_approach=interaction_context.user_approach,
                recent_actions=recent_actions
            )
            
            # Combine behavioral prompt with action guidance
            complete_behavioral_prompt = behavioral_context.behavioral_prompt + "\n" + action_guidance
            
            logger.info(f"🎭 Using behavioral tier '{behavioral_context.tier_name}' with {len(recent_actions)} recent actions")
            
            return behavioral_context.available_knowledge, behavioral_context.tier_name, complete_behavioral_prompt
            
        except Exception as e:
            logger.error(f"Failed to get behavioral context: {e}")
            return {}, "error", "Respond naturally based on your character."
    
    # Keep original method as fallback
    async def _get_available_knowledge(self, persona_id: str, trust_level: float) -> Tuple[Dict, str]:
        """
        Original knowledge method - kept for compatibility
        """
        knowledge, tier_name, _ = await self._get_available_knowledge_behavioral(
            persona_id, trust_level, 
            InteractionContext("neutral", "adequate", True, "neutral", "stable")
        )
        return knowledge, tier_name
    
    def _determine_natural_boundaries(self, interaction_context: InteractionContext, 
                                    trust_level: float, behavioral_adjustments: Dict,
                                    available_knowledge: Dict) -> Dict[str, Any]:
        """Determine what character would naturally share based on context"""
        
        boundaries = {
            "willing_to_mention": [],
            "emotional_stance": behavioral_adjustments.get('emotional_availability', 'guarded'),
            "sharing_depth": "surface",
            "defensive_responses": False
        }
        
        # Determine sharing depth based on trust and interaction quality (0.0-1.0 scale!)
        if trust_level >= 0.80 and interaction_context.interaction_quality == "excellent":
            boundaries["sharing_depth"] = "deep"
        elif trust_level >= 0.60 and interaction_context.interaction_quality in ["good", "excellent"]:
            boundaries["sharing_depth"] = "moderate"
        elif trust_level >= 0.40 and interaction_context.interaction_quality != "poor":
            boundaries["sharing_depth"] = "surface"
        else:
            boundaries["sharing_depth"] = "minimal"
        
        # Determine what to mention based on available knowledge and comfort level
        if available_knowledge:
            all_topics = list(available_knowledge.keys())
            
            if boundaries["sharing_depth"] == "deep":
                boundaries["willing_to_mention"] = all_topics
            elif boundaries["sharing_depth"] == "moderate":
                # Share half the available topics
                boundaries["willing_to_mention"] = all_topics[:len(all_topics)//2]
            elif boundaries["sharing_depth"] == "surface":
                # Share only basic topics
                safe_topics = [topic for topic in all_topics if 
                              topic in ['job_title', 'employer', 'tenure', 'current_status']]
                boundaries["willing_to_mention"] = safe_topics[:2]
        
        # Adjust for defensive responses
        if (interaction_context.interaction_quality == "poor" or 
            interaction_context.trust_trajectory == "declining"):
            boundaries["defensive_responses"] = True
            boundaries["willing_to_mention"] = []
        
        return boundaries
    
    async def _generate_natural_response(
        self,
        persona_data: Dict,
        sharing_boundaries: Dict,
        user_message: str,
        conversation_history: List[Dict],
        interaction_context: InteractionContext,
        behavioral_adjustments: Dict,
        persona_llm: str,
        trust_level: float,
        session_id: str = None,
        stage: str = "cautious"
    ) -> str:
        """Generate elegant persona response using enhanced persona structure"""
        
        persona_name = persona_data.get('name', 'Person')
        persona_id = persona_data.get('persona_id', '')
        
        # Retrieve what's been shared so far (dynamic progression)
        recent_memories = await self._get_recent_memories(session_id)
        
        # Get behavioral context (includes core_identity modulated by trust)
        knowledge, tier_name, behavioral_prompt = await self._get_available_knowledge_behavioral(
            persona_id, trust_level, interaction_context, session_id
        )
        
        # Stage-specific guidance for natural progression
        stage_guidance = self._get_stage_guidance(stage, trust_level)
        
        # Streamlined prompt: behavioral context + memories + stage guidance
        response_prompt = f"""═══ CONVERSATION CONTEXT ═══
Stage: {stage.replace('_', ' ').title()} (Trust: {trust_level:.2f})

{stage_guidance}

{recent_memories}

═══ YOUR CHARACTER ═══
{behavioral_prompt}

═══ CURRENT INTERACTION ═══
User: "{user_message}"

Respond naturally as {persona_name} (1-3 sentences):"""
        
        # Generate response
        persona_model = self._normalize_model_name(persona_llm)
        response = await self.llm_service.generate_response(
            prompt=response_prompt,
            model=persona_model,
            temperature=0.8,
            max_tokens=120
        )
        
        # Remove unwanted prefixes like "You:" or persona name prefixes
        if response.startswith('You: '):
            response = response[5:]
        elif response.startswith(f'{persona_name}: '):
            response = response[len(f'{persona_name}: '):]
        
        return response.strip()
    
    def _get_stage_guidance(self, stage: str, trust_level: float) -> str:
        """Provide stage-specific guidance for natural conversation progression"""
        
        guidance = {
            "defensive": "You're guarded and protective. Keep responses brief. Don't reveal personal struggles.",
            
            "cautious": "You're testing safety. Share surface-level work facts. Acknowledge stress exists but don't elaborate.",
            
            "building_rapport": "You're starting to trust. Share work challenges and hint at external pressures. Show some vulnerability.",
            
            "opening_up": "You feel safer now. Share specific challenges about balancing responsibilities. Be candid about struggles.",
            
            "full_trust": "You trust this person. Discuss solutions openly. Be specific about needs and what would help."
        }
        
        return guidance.get(stage, "Respond naturally based on where you are in building trust.")
    
    
    async def _get_recent_memories(self, session_id: str) -> str:
        """Retrieve recent memories for character continuity and consistency"""
        try:
            # Get 7 most recent memories (recency > importance for natural progression)
            result = self.supabase.table('conversation_memories').select('key_insights').eq(
                'session_id', session_id
            ).order('created_at', desc=True).limit(7).execute()
            
            if not result.data:
                return "(This is your first conversation together)"
            
            memories = []
            for memory in result.data:
                insight = memory.get('key_insights', '')
                if insight:
                    # Extract the emotional/relationship context (after "User said: '...'")
                    if "I felt" in insight or "They seemed" in insight or "My trust" in insight:
                        # Find the part after the user quote
                        parts = insight.split("'", 2)  # Split on first two quotes
                        if len(parts) >= 3:
                            emotional_context = parts[2].strip()
                            if emotional_context:
                                memories.append(emotional_context)
                    elif "User said:" not in insight:
                        # Direct insight without user quote wrapper
                        memories.append(insight)
            
            if memories:
                return f"WHAT'S BEEN SHARED SO FAR:\n" + "\n".join(f"- {mem}" for mem in memories[:5])
            else:
                return "(First conversation - building rapport)"
                
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return "(Unable to recall previous conversation context)"
    
    
    
    def _convert_to_mi_format(self, interaction_context: InteractionContext) -> Dict[str, Any]:
        """Convert natural interaction assessment to MI analysis format for compatibility"""
        
        # Convert empathy tone to numeric scale
        empathy_mapping = {
            'hostile': 2,
            'neutral': 5,
            'supportive': 7,
            'deeply_empathetic': 9
        }
        empathy_score = empathy_mapping.get(interaction_context.empathy_tone, 5)
        
        # Convert interaction quality to techniques
        technique_mapping = {
            'poor': ['advice', 'closed_question'],
            'adequate': ['basic_question'],
            'good': ['open_question', 'reflection'],
            'excellent': ['reflection', 'affirmation', 'complex_reflection']
        }
        techniques_used = technique_mapping.get(interaction_context.interaction_quality, ['basic_question'])
        
        # Convert trust trajectory to openness change
        openness_mapping = {
            'declining': 'decrease',
            'stable': 'same',
            'building': 'increase',
            'breakthrough': 'increase'
        }
        openness_change = openness_mapping.get(interaction_context.trust_trajectory, 'same')
        
        return {
            'empathy_score': empathy_score,
            'techniques_used': techniques_used,
            'openness_change': openness_change,
            'is_safe': interaction_context.emotional_safety,
            'interaction_quality': interaction_context.interaction_quality
        }
    
    async def _form_natural_memory(self, session_id: str, user_message: str, 
                                 interaction_context: InteractionContext, persona_response: str,
                                 persona_name: str) -> None:
        """Form contextual memory based on natural interaction assessment"""
        
        try:
            # Create memory text based on interaction context
            memory_text = self._create_contextual_memory(
                user_message, interaction_context, persona_response
            )
            
            # Calculate importance based on interaction significance
            importance = self._calculate_natural_importance(interaction_context)
            
            # Store in conversation_memories table (dynamic memories)
            # Use session_id as-is - it should be a proper UUID from the routes
            memory_data = {
                'session_id': session_id,
                'key_insights': memory_text,
                'importance_score': importance,
                'created_at': datetime.now().isoformat()
            }
            
            # Check memory limits before inserting
            current_count_result = self.supabase.table('conversation_memories') \
                .select('id', count='exact') \
                .eq('session_id', session_id) \
                .execute()
            
            current_count = current_count_result.count if current_count_result.count is not None else 0
            
            # Archive oldest memory if at limit
            if current_count >= 15:  # Keep more memories since they're contextual
                oldest_result = self.supabase.table('conversation_memories') \
                    .select('id, importance_score') \
                    .eq('session_id', session_id) \
                    .order('importance_score', desc=False) \
                    .order('created_at', desc=False) \
                    .limit(1) \
                    .execute()
                
                if oldest_result.data:
                    self.supabase.table('conversation_memories') \
                        .delete() \
                        .eq('id', oldest_result.data[0]['id']) \
                        .execute()
            
            # Insert new memory
            self.supabase.table('conversation_memories').insert(memory_data).execute()
            
            logger.info(f"💭 Contextual memory formed: {memory_text[:100]}... " +
                       f"(importance: {importance:.1f})")
            
        except Exception as e:
            logger.error(f"Failed to form natural memory: {e}", exc_info=True)
    
    def _create_contextual_memory(self, user_message: str, interaction_context: InteractionContext,
                                persona_response: str) -> str:
        """Create contextual memory text based on interaction"""
        
        # Always start with what user said (factual)
        base_memory = f"User said: '{user_message[:120]}'"
        
        # Add emotional context based on interaction assessment
        if interaction_context.interaction_quality == "excellent":
            if interaction_context.empathy_tone == "deeply_empathetic":
                emotional_context = " I felt deeply understood and safe. They showed genuine empathy and care."
            else:
                emotional_context = " This felt like a really good conversation. They listened well and seemed to understand."
        
        elif interaction_context.interaction_quality == "good":
            emotional_context = " They seemed supportive and understanding. I'm starting to trust them more."
        
        elif interaction_context.interaction_quality == "poor":
            if interaction_context.empathy_tone == "hostile":
                emotional_context = " This felt hostile and unsafe. I became defensive and guarded."
            elif interaction_context.user_approach == "directive":
                emotional_context = " They were being directive and giving advice. This felt pushy and unhelpful."
            else:
                emotional_context = " Something about their approach didn't feel right. I became more cautious."
        
        else:  # adequate
            emotional_context = " This was an okay interaction, nothing special. Staying cautious for now."
        
        # Add trust trajectory context
        if interaction_context.trust_trajectory == "breakthrough":
            trust_context = " Something shifted - I feel like they might actually get it."
        elif interaction_context.trust_trajectory == "building":
            trust_context = " My trust in them is slowly growing."
        elif interaction_context.trust_trajectory == "declining":
            trust_context = " I'm feeling less trusting than before."
        else:
            trust_context = ""
        
        return base_memory + emotional_context + trust_context
    
    def _calculate_natural_importance(self, interaction_context: InteractionContext) -> float:
        """Calculate memory importance based on interaction significance"""
        
        base_importance = 6.0  # All dynamic memories start at 6.0
        
        # Boost importance for significant interactions
        if interaction_context.interaction_quality == "excellent":
            base_importance += 2.0
        elif interaction_context.interaction_quality == "poor":
            base_importance += 1.5  # Negative experiences are also important to remember
        elif interaction_context.interaction_quality == "good":
            base_importance += 1.0
        
        # Boost for trust breakthroughs or major declines
        if interaction_context.trust_trajectory == "breakthrough":
            base_importance += 1.5
        elif interaction_context.trust_trajectory == "declining":
            base_importance += 1.0
        
        # Boost for emotional safety issues
        if not interaction_context.emotional_safety:
            base_importance += 1.0
        
        return min(10.0, base_importance)
    
    # Removed: _extract_core_beliefs_from_persona_data
    # No longer needed - we use core_identity and current_situation directly from the database
    
    async def _get_recent_persona_actions(self, session_id: str, limit: int = 5) -> List[str]:
        """Get recently used action types to avoid repetition"""
        if not session_id:
            return []
            
        try:
            # Extract action types from recent memories
            result = self.supabase.table('conversation_memories').select('key_insights').eq(
                'session_id', session_id
            ).order('created_at', desc=True).limit(limit).execute()
            
            actions = []
            for memory in result.data or []:
                insight = memory.get('key_insights', '').lower()
                # Simple action type detection from memory content
                if 'denied' in insight or 'rejected' in insight:
                    actions.append('deny')
                elif 'downplayed' in insight or 'minimized' in insight:
                    actions.append('downplay')
                elif 'blamed' in insight or 'attributed to' in insight:
                    actions.append('blame')
                elif 'hesitant' in insight or 'ambivalent' in insight:
                    actions.append('hesitate')
                elif 'detailed' in insight or 'shared specifics' in insight:
                    actions.append('detailed_inform')
            
            return actions
        except Exception as e:
            logger.error(f"Failed to get recent actions: {e}")
            return []
    
    def _normalize_model_name(self, persona_llm: str) -> str:
        """Normalize LLM model name - allows user selection"""
        model_mapping = {
            "chatgpt": "gpt-4o-mini",
            "gpt": "gpt-4o-mini", 
            "openai": "gpt-4o-mini",
            "gpt-4o-mini": "gpt-4o-mini",
            "gemini": "gemini-2.5-flash",
            "google": "gemini-2.5-flash",
            "gemini-2.5-flash": "gemini-2.5-flash"
        }
        return model_mapping.get(persona_llm.lower(), "gpt-4o-mini")

# Global instance
enhanced_persona_service = EnhancedPersonaService()