"""
Persona Response Engine - Generates contextual, in-character responses

This is the creative heart of the scenario-based system. It generates
authentic persona responses based on:
- Persona configuration (personality, triggers, patterns)
- Manager's actual message
- Conversation history
- Current persona state (trust, openness, resistance)
"""

import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

from src.services.llm_service import LLMService

logger = logging.getLogger(__name__)


@dataclass
class PersonaState:
    """Tracks the current state of a persona in a scenario"""
    trust_level: int        # 1-10, higher = more trusting
    openness_level: int     # 1-10, higher = more open
    resistance_active: bool  # Whether resistance patterns are triggered
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PersonaState':
        return cls(
            trust_level=data.get('trust_level', 4),
            openness_level=data.get('openness_level', 3),
            resistance_active=data.get('resistance_active', True)
        )


@dataclass
class PersonaResponse:
    """Response from persona with updated state"""
    message: str
    updated_state: PersonaState
    reasoning: Optional[str] = None  # For debugging/analysis


class PersonaResponseEngine:
    """
    Generates contextual, in-character responses for personas.
    
    The persona isn't following a script - they're:
    1. Embodying a character (defined in config)
    2. Responding to actual input (not predefined branches)
    3. Evolving based on manager behavior (trust changes)
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
    
    async def generate_response(
        self,
        persona_config: Dict[str, Any],
        manager_message: str,
        conversation_history: List[Dict[str, Any]],
        current_state: PersonaState
    ) -> PersonaResponse:
        """
        Generate an authentic persona response.
        
        Args:
            persona_config: Full persona configuration from scenario
            manager_message: What the manager just said
            conversation_history: Previous turns in this scenario
            current_state: Current trust/openness/resistance levels
            
        Returns:
            PersonaResponse with message and updated state
        """
        # Build dynamic prompt
        prompt = self._build_persona_prompt(
            persona_config, manager_message, conversation_history, current_state
        )
        
        # Single LLM call for persona response
        try:
            response_obj = await self.llm.complete(
                prompt=prompt,
                temperature=0.7,  # Slightly creative for natural responses
                max_tokens=300,
                use_case="persona_response"
            )
            response_text = response_obj.content
        except Exception as e:
            logger.error(f"LLM persona response failed: {e}")
            response_text = "I'm not sure what to say about that."
        
        # Update state based on interaction
        new_state = self._update_state(
            manager_message,
            response_text,
            current_state,
            persona_config.get("triggers", {})
        )
        
        return PersonaResponse(
            message=response_text,
            updated_state=new_state
        )
    
    def _build_persona_prompt(
        self,
        persona_config: Dict[str, Any],
        manager_message: str,
        conversation_history: List[Dict[str, Any]],
        state: PersonaState
    ) -> str:
        """Construct rich, contextual prompt for persona"""
        
        name = persona_config.get("name", "Persona")
        role = persona_config.get("role", "Team member")
        situation = persona_config.get("situation", "")
        personality = persona_config.get("personality", "")
        mindset = persona_config.get("current_mindset", "")
        response_patterns = persona_config.get("response_patterns", {})
        triggers = persona_config.get("triggers", {})
        
        # Format response patterns for the prompt
        patterns_text = self._format_response_patterns(response_patterns)
        
        # Format conversation history
        history_text = self._format_history(conversation_history)
        
        # Build the prompt
        prompt = f"""You are {name}, {role}.

=== CURRENT SITUATION ===
{situation}

=== YOUR PERSONALITY & MINDSET ===
{personality}
Current mindset: {mindset}

=== HOW YOU RESPOND TO DIFFERENT APPROACHES ===
{patterns_text}

=== TRUST & OPENNESS ===
Your current state with this manager:
- Trust level: {state.trust_level}/10 (higher = more trusting)
- Openness to discussion: {state.openness_level}/10
- Currently showing resistance: {state.resistance_active}

This affects how you respond:
- Low trust (1-3): Guarded, minimal sharing, deflects responsibility
- Medium trust (4-6): Cautiously engaged, surface-level sharing
- High trust (7-10): Open, vulnerable, shares genuine concerns

=== CONVERSATION SO FAR ===
{history_text}

=== YOUR RESPONSE ===
The manager just said: "{manager_message}"

Respond naturally as {name} would, based on:
1. Your personality and current mindset
2. Your current trust level with this manager
3. How they've approached the conversation so far
4. The actual words they used (not what you expected them to say)

Stay completely in character. Don't break character with meta-commentary.
Show realistic resistance patterns when appropriate.

Respond as {name}:"""
        
        return prompt
    
    def _format_response_patterns(self, patterns: Dict[str, str]) -> str:
        """Format response patterns for the prompt"""
        if not patterns:
            return "- Respond naturally based on your personality"
        
        lines = []
        for approach, response in patterns.items():
            # Format the approach name
            approach_name = approach.replace("_", " ").title()
            lines.append(f"- To {approach_name}: {response}")
        
        return "\n".join(lines)
    
    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for the prompt"""
        if not history:
            return "(No previous conversation)"
        
        lines = []
        for turn in history[-8:]:  # Last 8 turns for context
            manager_msg = turn.get("manager_message", "")
            persona_msg = turn.get("persona_response", "")
            turn_num = turn.get("turn", len(lines) + 1)
            
            lines.append(f"Turn {turn_num}:")
            lines.append(f"  Manager: \"{manager_msg}\"")
            lines.append(f"  {turn.get('persona_name', 'Persona')}: \"{persona_msg}\"")
        
        return "\n".join(lines)
    
    def _update_state(
        self,
        manager_message: str,
        persona_response: str,
        current_state: PersonaState,
        triggers: Dict[str, List[str]]
    ) -> PersonaState:
        """
        Update persona state based on manager's approach.
        
        The persona's trust and openness evolve based on how the manager
        communicates - this is what makes the training effective.
        """
        # Get configurable resistance indicators from triggers, with defaults
        resistance_indicators = triggers.get("resistance_indicators", [
            "i don't know",
            "that's not my fault",
            "they told me",
            "the problem is",
        ])
        
        manager_lower = manager_message.lower()
        
        trust_delta = 0
        openness_delta = 0
        resistance_triggered = current_state.resistance_active
        
        # Trust increase triggers
        for trigger in triggers.get("trust_increase", []):
            if trigger.lower() in manager_lower:
                trust_delta += 1
                openness_delta += 1
        
        # Trust decrease triggers
        for trigger in triggers.get("trust_decrease", []):
            if trigger.lower() in manager_lower:
                trust_delta -= 2
                openness_delta -= 2
                resistance_triggered = True
        
        # Additional resistance triggers
        for trigger in triggers.get("resistance_increase", []):
            if trigger.lower() in manager_lower:
                resistance_triggered = True
        
        # Check for specific patterns that indicate resistance
        for indicator in resistance_indicators:
            if indicator in persona_response.lower():
                resistance_triggered = True
                break
        
        # Calculate new state (clamped to 1-10)
        new_trust = max(1, min(10, current_state.trust_level + trust_delta))
        new_openness = max(1, min(10, current_state.openness_level + openness_delta))
        
        # Resistance tends to decrease naturally when trust increases
        if new_trust >= 7 and current_state.resistance_active:
            resistance_triggered = False
        
        return PersonaState(
            trust_level=new_trust,
            openness_level=new_openness,
            resistance_active=resistance_triggered
        )


# Singleton instance
_persona_response_engine: Optional[PersonaResponseEngine] = None


def get_persona_response_engine() -> PersonaResponseEngine:
    """Get or create the singleton PersonaResponseEngine"""
    global _persona_response_engine
    if _persona_response_engine is None:
        from src.services.llm_service import get_llm_service
        llm = get_llm_service()
        _persona_response_engine = PersonaResponseEngine(llm)
    return _persona_response_engine
