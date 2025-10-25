"""
Simplified Chat Service for Persona Interactions
- Loads personas directly from Supabase
- Uses ALL Supabase data (nothing hardcoded)
- Session-based MI technique adaptations
- Reset adaptations per new session
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.services.llm_service import LLMService
from src.config.settings import get_settings
from src.models.schemas import Message, MessageRole
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class ChatService:
    """Simplified service for persona chat interactions"""

    def __init__(self):
        self.settings = get_settings()
        self.supabase: Client = create_client(
            self.settings.SUPABASE_URL,
            self.settings.SUPABASE_SERVICE_ROLE_KEY
        )
        self.llm_service = LLMService()
        self.session_adaptations: Dict[str, Dict[str, Any]] = {}  # session_id -> adaptations
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}  # session_id -> messages

    async def get_personas(self) -> List[Dict[str, Any]]:
        """Get all personas from Supabase"""
        try:
            result = self.supabase.table('personas').select('*').execute()

            personas = []
            for row in result.data:
                # Extract all data from Supabase (nothing hardcoded)
                persona_data = self._extract_persona_data(row)
                personas.append(persona_data)

            return personas
        except Exception as e:
            logger.error(f"Failed to get personas: {e}")
            return []

    async def chat_with_persona(
        self,
        persona_id: str,
        message: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Chat with a persona using ALL Supabase data"""

        # 1. Get complete persona data from Supabase
        persona_data = await self._get_persona_data(persona_id)
        if not persona_data:
            raise ValueError(f"Persona {persona_id} not found")

        # 2. Initialize/reset session adaptations and conversation history for new sessions
        if session_id not in self.session_adaptations:
            self.session_adaptations[session_id] = self._get_base_adaptations(persona_data)
            self.conversation_history[session_id] = []

        # 3. Detect MI techniques in user message
        technique_data = self._detect_mi_techniques(message)

        # 4. Apply session adaptations based on techniques
        adapted_data = self._apply_session_adaptations(persona_data, session_id, technique_data)

        # 5. Generate system prompt using ALL Supabase data
        system_prompt = self._build_system_prompt(adapted_data)

        # 6. Add user message to conversation history
        user_message = Message(
            role=MessageRole.USER,
            content=message
        )
        self.conversation_history[session_id].append(user_message)

        # 7. Generate response using LLM with conversation history
        response_text = await self.llm_service.generate_response(
            prompt=message,
            system_prompt=system_prompt,
            model=self.settings.DEFAULT_MODEL,
            temperature=adapted_data.get('temperature', 0.7),
            max_tokens=adapted_data.get('max_tokens', 400),
            conversation_history=self.conversation_history[session_id][:-1]  # Exclude current message
        )

        # 8. Add AI response to conversation history
        ai_message = Message(
            role=MessageRole.ASSISTANT,
            content=response_text
        )
        self.conversation_history[session_id].append(ai_message)

        # 9. Update session adaptations based on interaction
        self._update_session_adaptations(session_id, technique_data, adapted_data)

        # 10. Store conversation (optional)
        await self._store_conversation(persona_id, session_id, message, response_text)

        return {
            "response": response_text,
            "technique_detected": technique_data,
            "adaptations_applied": self.session_adaptations[session_id].copy(),
            "session_id": session_id
        }

    def _extract_persona_data(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Extract ALL data from Supabase row (nothing hardcoded)"""
        # Parse metadata
        metadata = row.get('metadata', {})
        if isinstance(metadata, str):
            import json
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {}

        # Extract system prompt (handle JSON-escaped strings)
        system_prompt = None
        if 'system_prompt' in row and row['system_prompt']:
            system_prompt = row['system_prompt']
            if isinstance(system_prompt, str) and system_prompt.startswith('"'):
                try:
                    import json
                    system_prompt = json.loads(system_prompt)
                except json.JSONDecodeError:
                    if system_prompt.startswith('"') and system_prompt.endswith('"'):
                        system_prompt = system_prompt[1:-1]
                    system_prompt = system_prompt.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')

        return {
            # Direct fields from personas table
            'persona_id': row['persona_id'],
            'name': row['name'],
            'description': row['description'],
            'persona_type': row['persona_type'],
            'max_tokens': row['max_tokens'],
            'temperature': 0.7,  # Default, can be overridden

            # Trait values (ALL from Supabase)
            'defensiveness_level': row.get('defensiveness_level'),
            'resistance_sophistication': row.get('resistance_sophistication'),
            'tone_intensity': row.get('tone_intensity'),
            'passive_aggression': row.get('passive_aggression'),
            'emotional_manipulation': row.get('emotional_manipulation'),
            'intellectual_superiority': row.get('intellectual_superiority'),

            # Complex data from metadata
            'system_prompt': system_prompt,
            'language_markers': row.get('language_markers'),
            'communication_style': row.get('communication_style'),
            'workplace_context': row.get('company_id') or metadata.get('workplace_context'),
            'traits': row.get('traits') or metadata.get('traits'),
            'specific_traits': metadata.get('traits') or metadata.get('specific_traits'),

            # MI practice data from metadata
            'practice_scenarios': metadata.get('practice_scenarios', []),
            'character_strengths': metadata.get('character_strengths', []),
            'character_challenges': metadata.get('character_challenges', []),
            'response_adaptability': metadata.get('response_adaptability', {}),
            'custom_opening_statement': metadata.get('custom_opening_statement'),
            'mi_practice_opportunities': metadata.get('mi_practice_opportunities', []),

            # Guardrails and safety
            'guardrails': metadata.get('guardrails', {}),
            'mi_response_patterns': row.get('mi_response_patterns'),
            'value_lip_service': row.get('value_lip_service'),
            'value_genuine_alignment': row.get('value_genuine_alignment'),
            'value_manipulation_tactics': row.get('value_manipulation_tactics'),

            # Raw metadata for completeness
            'metadata': metadata
        }

    async def _get_persona_data(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Get complete persona data from Supabase"""
        try:
            result = self.supabase.table('personas').select('*').eq('persona_id', persona_id).execute()

            if result.data and len(result.data) > 0:
                return self._extract_persona_data(result.data[0])

            return None
        except Exception as e:
            logger.error(f"Failed to get persona data for {persona_id}: {e}")
            return None

    def _get_base_adaptations(self, persona_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get base adaptation values from Supabase data (resets per session)"""
        return {
            'defensiveness_level': persona_data.get('defensiveness_level', 0.5),
            'resistance_sophistication': persona_data.get('resistance_sophistication', 0.5),
            'tone_intensity': persona_data.get('tone_intensity', 0.5),
            'passive_aggression': persona_data.get('passive_aggression', 0.2),
            'emotional_manipulation': persona_data.get('emotional_manipulation', 0.1),
            'intellectual_superiority': persona_data.get('intellectual_superiority', 0.3),
            'mi_techniques_detected': [],
            'adaptation_triggers': []
        }

    def _detect_mi_techniques(self, message: str) -> Dict[str, Any]:
        """Detect MI techniques in user message"""
        message_lower = message.lower()
        techniques = []

        # Open questions
        if "?" in message and not any(word in message_lower for word in ["why", "don't you", "shouldn't you"]):
            techniques.append("open_question")

        # Reflections
        reflection_markers = ["sounds like", "seems like", "i hear", "what i'm hearing", "so you"]
        if any(marker in message_lower for marker in reflection_markers):
            techniques.append("reflection")

        # Affirmations
        affirmation_words = ["strength", "courage", "important", "valuable", "appreciate", "admire"]
        if any(word in message_lower for word in affirmation_words):
            techniques.append("affirmation")

        # Summaries
        if any(word in message_lower for word in ["overall", "so far", "put together", "in summary"]):
            techniques.append("summary")

        # Negative techniques (arguing)
        if any(phrase in message_lower for phrase in ["you should", "you need to", "you have to", "that's not right"]):
            techniques.append("arguing")

        quality = "good" if techniques else "neutral"
        if "arguing" in techniques:
            quality = "poor"

        return {
            "techniques": techniques,
            "quality": quality,
            "message": message
        }

    def _apply_session_adaptations(
        self,
        persona_data: Dict[str, Any],
        session_id: str,
        technique_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply session adaptations to persona data"""
        adapted = persona_data.copy()
        adaptations = self.session_adaptations[session_id]

        # Apply current session adaptations
        for key, value in adaptations.items():
            if key in adapted and isinstance(value, (int, float)):
                adapted[key] = value

        return adapted

    def _build_system_prompt(self, persona_data: Dict[str, Any]) -> str:
        """Build system prompt using ALL Supabase data"""

        # Use the complete system_prompt from Supabase if available
        if persona_data.get('system_prompt'):
            base_prompt = persona_data['system_prompt']

            # Add current session adaptations as prompt injection
            adaptations = []
            if persona_data.get('defensiveness_level') is not None:
                adaptations.append(f"Current defensiveness level: {persona_data['defensiveness_level']:.1f}")
            if persona_data.get('resistance_sophistication') is not None:
                adaptations.append(f"Current resistance sophistication: {persona_data['resistance_sophistication']:.1f}")
            if persona_data.get('tone_intensity') is not None:
                adaptations.append(f"Current tone intensity: {persona_data['tone_intensity']:.1f}")

            if adaptations:
                base_prompt += "\n\nCURRENT SESSION ADAPTATIONS:\n" + "\n".join(adaptations)
                base_prompt += "\n\nAdjust your behavior based on these current adaptation values."

            return base_prompt

        # NO fallback prompts - everything must come from Supabase
        if not system_prompt:
            raise ValueError(
                f"Persona '{persona_data['name']}' missing system_prompt in Supabase metadata. "
                "Add system_prompt to personas table metadata."
            )
                style_parts = []
                for key, value in comm_style.items():
                    style_parts.append(f"{key}: {value}")
                parts.append("Communication style:\n" + "\n".join(style_parts))

        return "\n\n".join(parts)

    def _update_session_adaptations(
        self,
        session_id: str,
        technique_data: Dict[str, Any],
        persona_data: Dict[str, Any]
    ) -> None:
        """Update session adaptations based on MI techniques used"""
        adaptations = self.session_adaptations[session_id]
        techniques = technique_data.get('techniques', [])
        quality = technique_data.get('quality', 'neutral')

        # Track techniques used
        adaptations['mi_techniques_detected'].extend(techniques)

        # Apply adaptation rules based on techniques
        if quality == "good":
            # Good MI techniques reduce defensiveness
            if 'reflection' in techniques or 'affirmation' in techniques:
                adaptations['defensiveness_level'] = max(0.1, adaptations['defensiveness_level'] - 0.2)
                adaptations['adaptation_triggers'].append('good_mi_technique')

            if 'open_question' in techniques:
                adaptations['resistance_sophistication'] = max(0.1, adaptations['resistance_sophistication'] - 0.1)
                adaptations['adaptation_triggers'].append('open_question')

        elif quality == "poor":
            # Poor techniques increase defensiveness
            if 'arguing' in techniques:
                adaptations['defensiveness_level'] = min(0.9, adaptations['defensiveness_level'] + 0.3)
                adaptations['tone_intensity'] = min(0.9, adaptations['tone_intensity'] + 0.2)
                adaptations['adaptation_triggers'].append('poor_mi_technique')

    async def _store_conversation(
        self,
        persona_id: str,
        session_id: str,
        user_message: str,
        ai_response: str
    ) -> None:
        """Store conversation in Supabase (optional)"""
        try:
            conversation_data = {
                'session_id': session_id,
                'persona_id': persona_id,
                'user_message': user_message,
                'ai_response': ai_response,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Store in conversations table if it exists
            self.supabase.table('conversations').insert(conversation_data).execute()

        except Exception as e:
            # Don't fail if conversation storage fails
            logger.warning(f"Failed to store conversation: {e}")

    def reset_session(self, session_id: str) -> None:
        """Reset session adaptations and conversation history (call when starting new session)"""
        if session_id in self.session_adaptations:
            del self.session_adaptations[session_id]
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]