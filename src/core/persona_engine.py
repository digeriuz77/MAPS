"""
Central engine for managing AI personas
"""
import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.personas.base_persona import BasePersona
# Database service injected via dependency injection
from src.models.schemas import PersonaConfig, PersonaResponse, Message, PersonaType
# PersonaFactory removed - using service-based approach
from src.exceptions import PersonaNotFoundError, PersonaCreationError, PersonaTypeNotSupportedError
from src.core.constants import MAX_PERSONAS_LOAD, RECENT_HISTORY_LIMIT
from src.services.analysis.analysis_service import get_analysis_service

logger = logging.getLogger(__name__)

class PersonaEngine:
    """Central engine for managing AI personas"""
    
    def __init__(self, database_service):
        self.database_service = database_service
        # Note: Safety monitoring now handled by optimized MI service
        self.active_personas: Dict[str, BasePersona] = {}
        self.base_persona_data: Dict[str, Dict[str, Any]] = {}  # Store base persona data
        self.session_data: Dict[str, Dict[str, Any]] = {}
        self.session_adaptations: Dict[str, Dict[str, Any]] = {}  # Store session-specific adaptations
        self.analysis_service = get_analysis_service()
        
        # Conversation flow controls
        self.conversation_limits = {
            "max_messages_per_session": 50,
            "max_session_duration_minutes": 120,
            "rushing_detection_threshold": 3,  # messages per minute
            "domination_detection_threshold": 0.8  # ratio of user vs persona messages
        }
        
        # Logging for persona interactions
        self.interaction_logs: Dict[str, List[Dict[str, Any]]] = {}
        
    async def initialize(self) -> None:
        """Initialize persona engine"""
        # Load any existing personas from database storage
        await self._load_existing_personas()
        logger.info("Persona engine initialized")
        
    async def _load_existing_personas(self) -> None:
        """Load existing personas from storage"""
        try:
            # Get all stored personas from database
            results = await self.database_service.list_all_personas()
            
            for result in results:
                # Use the full result data, not just metadata
                persona_data = result
                persona_id = result.get("persona_id")
                
                if persona_id and persona_data:
                    # Store base persona data (full data needed for adaptation detection)
                    self.base_persona_data[persona_id] = persona_data.copy()
                    # Reconstruct persona from stored data
                    # Note: Using service-based approach instead of factory
                    persona = self._reconstruct_persona_from_data(persona_id, persona_data)
                    if persona:
                        self.active_personas[persona_id] = persona
                        
            logger.info(f"Loaded {len(self.active_personas)} existing personas")
            
        except Exception as e:
            logger.error(f"Failed to load existing personas: {e}")
            # Don't raise error - continue without pre-loaded personas
    
    async def _load_persona_from_db(self, persona_id: str) -> None:
        """Load a specific persona from database into active personas"""
        try:
            # Get persona data from database
            persona_data = await self.database_service.get_persona(persona_id)
            
            if persona_data:
                # Store base persona data (full data needed for adaptation detection)
                self.base_persona_data[persona_id] = persona_data.copy()
                # Reconstruct persona from stored data
                # Note: Using service-based approach instead of factory
                persona = self._reconstruct_persona_from_data(persona_id, persona_data)
                if persona:
                    self.active_personas[persona_id] = persona
                    logger.info(f"Successfully loaded persona {persona_id} from database")
                else:
                    logger.warning(f"Failed to reconstruct persona {persona_id}")
            else:
                logger.warning(f"Persona {persona_id} not found in database")
                
        except Exception as e:
            logger.error(f"Failed to load persona {persona_id} from database: {e}")
    
    async def create_persona(self, config: PersonaConfig) -> str:
        """Create a new persona instance"""
        
        persona_id = str(uuid.uuid4())
        
        try:
            # Create persona directly from config
            # Note: This method is deprecated in favor of service-based approach
            persona = self._create_persona_from_config(persona_id, config)
            
            # Store persona
            self.active_personas[persona_id] = persona
            
            # Store base persona data
            persona_dict = persona.to_dict()
            self.base_persona_data[persona_id] = persona_dict.copy()
            
            # Store in database
            await self.database_service.store_persona(persona_id, persona_dict)
            
            logger.info(f"Created persona: {persona_id} ({config.persona_type})")
            return persona_id
            
        except PersonaTypeNotSupportedError:
            raise
        except Exception as e:
            logger.error(f"Failed to create persona: {e}")
            raise PersonaCreationError(str(e), str(config.persona_type))
    
    
    async def chat_with_persona(
        self,
        persona_id: str,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> PersonaResponse:
        """Handle chat interaction with persona including flow controls"""
        
        # Auto-load persona from database if not active
        if persona_id not in self.active_personas:
            await self._load_persona_from_db(persona_id)
            
        if persona_id not in self.active_personas:
            raise PersonaNotFoundError(persona_id)
        
        persona = self.active_personas[persona_id]
        session_id = session_id or str(uuid.uuid4())
        
        print(f"DEBUG: Chat with persona {persona_id}, session_id: {session_id}")
        
        # Initialize session data if needed
        if session_id not in self.session_data:
            self.session_data[session_id] = {
                "start_time": datetime.utcnow(),
                "message_count": 0,
                "user_message_count": 0,
                "persona_message_count": 0,
                "last_message_time": datetime.utcnow(),
                "rushing_warnings": 0,
                "flow_control_triggered": False,
                "persona_id": persona_id
            }
            # Only initialize session adaptations if they don't exist
            if session_id not in self.session_adaptations:
                self.session_adaptations[session_id] = {}
        
        session_data = self.session_data[session_id]
        
        # Store persona traits before processing for comparison
        traits_before = self._get_persona_traits(persona)
        
        try:
            # Check conversation flow controls
            flow_control_result = await self._check_conversation_flow(
                session_id, message, persona
            )
            
            if flow_control_result.get("intervention_needed"):
                return PersonaResponse(
                    content=flow_control_result["intervention_message"],
                    confidence=1.0,
                    traits_activated=["flow_control"],
                    analysis={"flow_control": flow_control_result}
                )
            
            # Basic safety check (simplified - main safety handled by optimized service)
            if any(word in message.lower() for word in ['suicide', 'kill myself', 'end it all']):
                return PersonaResponse(
                    content="I'm concerned about what you've shared. Please reach out to a mental health professional or crisis helpline for immediate support.",
                    confidence=1.0,
                    traits_activated=[],
                    safety_flags=['crisis_content']
                )
            
            # Detect MI techniques if persona supports deliberate practice
            technique_data = {}
            if hasattr(persona, 'detect_mi_technique'):
                technique_data = persona.detect_mi_technique(message)
            
            # Generate response
            response = await persona.generate_response(message, context)
            
            # Apply technique-based adjustments for deliberate practice
            if technique_data and hasattr(persona, 'adjust_resistance_based_on_technique'):
                resistance_adjustment = persona.adjust_resistance_based_on_technique(technique_data)
                response.analysis = response.analysis or {}
                response.analysis["technique_detection"] = technique_data
                response.analysis["resistance_adjustment"] = resistance_adjustment
            
            # Update session tracking
            session_data["message_count"] += 2  # User + persona
            session_data["user_message_count"] += 1
            session_data["persona_message_count"] += 1
            session_data["last_message_time"] = datetime.utcnow()
            
            # Log interaction for analysis
            await self._log_interaction(
                persona_id, session_id, message, response, technique_data
            )
            
            # Store conversation
            await self._store_conversation(persona_id, session_id, message, response.content)
            
            # Note: Conversation safety monitoring moved to optimized MI service
            # Basic safety validation handled elsewhere
            
            # Check for trait changes and add adaptation notifications
            traits_after = self._get_persona_traits(persona)
            adaptation_traits = self._detect_trait_changes(traits_before, traits_after)
            
            # Add adaptation traits to the response
            if adaptation_traits:
                # Ensure traits_activated is a list before extending
                if not hasattr(response, 'traits_activated') or response.traits_activated is None:
                    response.traits_activated = []
                elif not isinstance(response.traits_activated, list):
                    response.traits_activated = list(response.traits_activated)
                
                response.traits_activated.extend(adaptation_traits)
            
            # Check for session adaptations and add adaptation notifications
            print(f"DEBUG: Checking for session adaptations with session_id: {session_id}, persona_id: {persona_id}")
            session_adaptation_traits = self._get_session_adaptation_traits(session_id, persona_id)
            print(f"DEBUG: Session adaptation traits detected: {session_adaptation_traits}")
            
            # Debug: Check what session adaptations are available
            print(f"DEBUG: Current session adaptations: {self.session_adaptations}")
            
            # Add session adaptation traits to the response
            if session_adaptation_traits:
                # Ensure traits_activated is a list before extending
                if not hasattr(response, 'traits_activated') or response.traits_activated is None:
                    response.traits_activated = []
                elif not isinstance(response.traits_activated, list):
                    response.traits_activated = list(response.traits_activated)
                
                original_traits = response.traits_activated[:]
                response.traits_activated.extend(session_adaptation_traits)
                print(f"DEBUG: Extended traits_activated from {original_traits} to {response.traits_activated}")
            
            print(f"DEBUG: Final response traits_activated: {response.traits_activated}")
            return response
            
        except Exception as e:
            logger.error(f"Chat failed for persona {persona_id}: {e}", exc_info=True)
            raise
    
    def _get_persona_traits(self, persona):
        """Get current persona traits for comparison"""
        traits = {}
        if hasattr(persona, 'defensiveness_level'):
            traits['defensiveness_level'] = persona.defensiveness_level
        if hasattr(persona, 'tone_intensity'):
            traits['tone_intensity'] = persona.tone_intensity
        if hasattr(persona, 'resistance_sophistication'):
            traits['resistance_sophistication'] = persona.resistance_sophistication
        if hasattr(persona, 'passive_aggression'):
            traits['passive_aggression'] = persona.passive_aggression
        if hasattr(persona, 'emotional_manipulation'):
            traits['emotional_manipulation'] = persona.emotional_manipulation
        return traits
    
    def _detect_trait_changes(self, before, after):
        """Detect changes in persona traits and return appropriate trait activation flags"""
        changes = []
        
        # Check for defensiveness changes
        if 'defensiveness_level' in before and 'defensiveness_level' in after:
            if after['defensiveness_level'] < before['defensiveness_level'] - 0.1:
                changes.append('defensiveness_decreased')
            elif after['defensiveness_level'] > before['defensiveness_level'] + 0.1:
                changes.append('defensiveness_increased')
        
        # Check for tone intensity changes
        if 'tone_intensity' in before and 'tone_intensity' in after:
            if after['tone_intensity'] < before['tone_intensity'] - 0.1:
                changes.append('tone_softened')
            elif after['tone_intensity'] > before['tone_intensity'] + 0.1:
                changes.append('tone_intensified')
        
        # Check for resistance sophistication changes
        if 'resistance_sophistication' in before and 'resistance_sophistication' in after:
            if after['resistance_sophistication'] < before['resistance_sophistication'] - 0.1:
                changes.append('resistance_decreased')
            elif after['resistance_sophistication'] > before['resistance_sophistication'] + 0.1:
                changes.append('resistance_increased')
        
        # Check for passive aggression activation
        if 'passive_aggression' in after and after['passive_aggression'] > 0.5:
            changes.append('passive_aggression')
        
        # Check for emotional manipulation activation
        if 'emotional_manipulation' in after and after['emotional_manipulation'] > 0.5:
            changes.append('emotional_manipulation')
        
        return changes
    
    async def _store_conversation(
        self,
        persona_id: str,
        session_id: str,
        user_message: str,
        assistant_response: str
    ):
        """Store conversation in database"""
        try:
            # Note: Conversation storage temporarily disabled
            # TODO: Implement conversation storage in database service
            # For now, conversations are only kept in persona memory
            pass
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
    
    def get_persona(self, persona_id: str) -> Optional[BasePersona]:
        """Get persona instance"""
        return self.active_personas.get(persona_id)
    
    def list_personas(self) -> List[Dict[str, Any]]:
        """List all active personas"""
        return [
            {
                "id": persona_id,
                **persona.to_dict()
            }
            for persona_id, persona in self.active_personas.items()
        ]
    
    async def delete_persona(self, persona_id: str) -> bool:
        """Delete persona"""
        if persona_id in self.active_personas:
            del self.active_personas[persona_id]
            if persona_id in self.base_persona_data:
                del self.base_persona_data[persona_id]
            logger.info(f"Deleted persona: {persona_id}")
            return True
        return False
    
    async def update_persona(
        self,
        persona_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update persona configuration"""
        if persona_id not in self.active_personas:
            return False
        
        persona = self.active_personas[persona_id]
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(persona, key):
                setattr(persona, key, value)
        
        # Update base persona data
        if persona_id in self.base_persona_data:
            persona_dict = persona.to_dict()
            self.base_persona_data[persona_id].update(persona_dict)
        
        return True
    
    def apply_session_adaptations(self, session_id: str, persona_id: str) -> None:
        """Apply session-specific adaptations to a persona"""
        if session_id not in self.session_adaptations:
            return
            
        if persona_id not in self.active_personas:
            return
            
        persona = self.active_personas[persona_id]
        adaptations = self.session_adaptations[session_id]
        
        # Apply adaptations to persona traits (for non-compliant personas)
        if hasattr(persona, 'defensiveness_level') and 'defensiveness_level' in adaptations:
            persona.defensiveness_level = adaptations['defensiveness_level']
        
        if hasattr(persona, 'tone_intensity') and 'tone_intensity' in adaptations:
            persona.tone_intensity = adaptations['tone_intensity']
            
        if hasattr(persona, 'resistance_sophistication') and 'resistance_sophistication' in adaptations:
            persona.resistance_sophistication = adaptations['resistance_sophistication']
            
        if hasattr(persona, 'intellectual_superiority') and 'intellectual_superiority' in adaptations:
            persona.intellectual_superiority = adaptations['intellectual_superiority']
            
        if hasattr(persona, 'passive_aggression') and 'passive_aggression' in adaptations:
            persona.passive_aggression = adaptations['passive_aggression']
            
        if hasattr(persona, 'emotional_manipulation') and 'emotional_manipulation' in adaptations:
            persona.emotional_manipulation = adaptations['emotional_manipulation']
    
    def reset_persona_to_base_values(self, persona_id: str) -> bool:
        """Reset a persona to its base values"""
        if persona_id not in self.base_persona_data:
            return False
            
        if persona_id not in self.active_personas:
            return False
            
        # Reconstruct persona from base data
        base_data = self.base_persona_data[persona_id]
        persona = self._reconstruct_persona_from_data(persona_id, base_data)
        
        if persona:
            self.active_personas[persona_id] = persona
            return True
            
        return False
    
    def reset_session_adaptations(self, session_id: str) -> None:
        """Reset session adaptations for a specific session"""
        if session_id in self.session_adaptations:
            del self.session_adaptations[session_id]
        self.session_adaptations[session_id] = {}
    
    async def process_session_metrics(
        self,
        session_id: str,
        persona_id: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process conversation metrics and apply session-specific adaptations"""
        # Initialize session adaptations if needed
        if session_id not in self.session_adaptations:
            self.session_adaptations[session_id] = {}
            
        # Get base persona values
        if persona_id not in self.base_persona_data:
            return {"error": "Base persona data not found"}
            
        base_data = self.base_persona_data[persona_id]
        
        # Apply adaptation rules (in memory only)
        adaptations = self._apply_adaptation_rules(base_data, metrics)
        
        # Store adaptations for this session
        self.session_adaptations[session_id].update(adaptations)
        
        # Apply adaptations to the active persona
        self.apply_session_adaptations(session_id, persona_id)
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Processed session metrics for session {session_id}")
        logger.debug(f"Applied adaptations: {adaptations}")
        logger.debug(f"Current session adaptations: {self.session_adaptations[session_id]}")
        
        return {"adaptations_applied": adaptations}
    
    def _apply_adaptation_rules(
        self,
        base_data: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply adaptation rules in memory (not to database)"""
        adaptations = {}
        
        # Get current values from base data
        defensiveness_level = base_data.get('defensiveness_level', 0.5)
        resistance_sophistication = base_data.get('resistance_sophistication', 0.5)
        tone_intensity = base_data.get('tone_intensity', 0.5)
        intellectual_superiority = base_data.get('intellectual_superiority', 0.5)
        passive_aggression = base_data.get('passive_aggression', 0.5)
        emotional_manipulation = base_data.get('emotional_manipulation', 0.5)
        
        # Apply rules based on metrics
        empathy_score = metrics.get('empathy_score', 0.0)
        reflection_quality = metrics.get('reflection_quality', 0.0)
        change_talk_frequency = metrics.get('change_talk_frequency', 0.0)
        overall_quality_score = metrics.get('overall_quality_score', 0.0)
        
        # Reduce defensiveness when high empathy is detected
        if empathy_score > 0.8:
            adaptations['defensiveness_level'] = max(0.1, defensiveness_level - 0.3)
        
        # Reduce resistance sophistication when high reflection quality is detected
        if reflection_quality > 0.75:
            adaptations['resistance_sophistication'] = max(0.1, resistance_sophistication - 0.2)
        
        # Reduce tone intensity when change talk is detected
        if change_talk_frequency > 0.7:
            adaptations['tone_intensity'] = max(0.1, tone_intensity - 0.2)
        
        # Reduce defensiveness when overall quality is high
        if overall_quality_score > 0.85:
            adaptations['defensiveness_level'] = max(0.1, defensiveness_level - 0.2)
        
        return adaptations
    
    async def _check_conversation_flow(
        self,
        session_id: str,
        message: str,
        persona: BasePersona
    ) -> Dict[str, Any]:
        """Check conversation flow and apply controls"""
        
        session_data = self.session_data[session_id]
        current_time = datetime.utcnow()
        
        # Check session duration
        session_duration = (current_time - session_data["start_time"]).total_seconds() / 60
        if session_duration > self.conversation_limits["max_session_duration_minutes"]:
            return {
                "intervention_needed": True,
                "intervention_message": "This session has been quite long. Consider taking a break and reflecting on what you've learned.",
                "reason": "session_duration_exceeded"
            }
        
        # Check message count
        if session_data["message_count"] >= self.conversation_limits["max_messages_per_session"]:
            return {
                "intervention_needed": True,
                "intervention_message": "You've had an extensive conversation. Let's wrap up and move to reflection.",
                "reason": "message_limit_exceeded"
            }
        
        # Check for rushing (too many messages too quickly)
        time_since_last = (current_time - session_data["last_message_time"]).total_seconds()
        if time_since_last < 20 and session_data["message_count"] > 5:  # Less than 20 seconds between messages
            session_data["rushing_warnings"] += 1
            if session_data["rushing_warnings"] >= self.conversation_limits["rushing_detection_threshold"]:
                return {
                    "intervention_needed": True,
                    "intervention_message": "I notice you're moving quickly through this conversation. In MI practice, it's important to slow down and really listen. Take a moment to reflect on what I've shared.",
                    "reason": "rushing_detected"
                }
        
        # Check for conversation domination
        if session_data["message_count"] > 10:
            user_ratio = session_data["user_message_count"] / session_data["message_count"]
            if user_ratio > self.conversation_limits["domination_detection_threshold"]:
                return {
                    "intervention_needed": True,
                    "intervention_message": "I notice you're doing most of the talking. In MI, it's important to listen more than we speak. What would you like to hear from me?",
                    "reason": "user_domination_detected"
                }
        
        return {"intervention_needed": False}
    
    async def _log_interaction(
        self,
        persona_id: str,
        session_id: str,
        user_message: str,
        response: PersonaResponse,
        technique_data: Dict[str, Any]
    ) -> None:
        """Log interaction for analysis and improvement"""
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "persona_id": persona_id,
            "session_id": session_id,
            "user_message_length": len(user_message),
            "persona_response_length": len(response.content),
            "confidence": response.confidence,
            "traits_activated": response.traits_activated,
            "technique_data": technique_data,
            "safety_flags": response.safety_flags or []
        }
        
        # Add deliberate practice metrics if available
        persona = self.active_personas.get(persona_id)
        if persona and hasattr(persona, 'get_deliberate_practice_summary'):
            try:
                practice_summary = persona.get_deliberate_practice_summary()
                if "error" not in practice_summary:
                    log_entry["deliberate_practice_metrics"] = practice_summary
            except Exception as e:
                logger.warning(f"Failed to get deliberate practice summary: {e}")
        
        # Store in interaction logs
        if persona_id not in self.interaction_logs:
            self.interaction_logs[persona_id] = []
        
        self.interaction_logs[persona_id].append(log_entry)
        
        # Keep only recent logs (last 100 interactions per persona)
        if len(self.interaction_logs[persona_id]) > 100:
            self.interaction_logs[persona_id] = self.interaction_logs[persona_id][-100:]
    
    def get_interaction_analytics(self, persona_id: str) -> Dict[str, Any]:
        """Get analytics for persona interactions"""
        
        if persona_id not in self.interaction_logs:
            return {"error": "No interaction data available"}
        
        logs = self.interaction_logs[persona_id]
        
        if not logs:
            return {"error": "No interaction data available"}
        
        # Calculate analytics
        total_interactions = len(logs)
        avg_confidence = sum(log.get("confidence", 0) for log in logs) / total_interactions
        
        # Technique usage analytics
        technique_counts = {}
        for log in logs:
            techniques = log.get("technique_data", {}).get("techniques", [])
            for technique in techniques:
                technique_counts[technique] = technique_counts.get(technique, 0) + 1
        
        # Session analytics
        unique_sessions = len(set(log.get("session_id") for log in logs))
        
        return {
            "persona_id": persona_id,
            "total_interactions": total_interactions,
            "unique_sessions": unique_sessions,
            "average_confidence": round(avg_confidence, 2),
            "technique_usage": technique_counts,
            "safety_incidents": sum(1 for log in logs if log.get("safety_flags")),
            "recent_activity": logs[-5:] if len(logs) >= 5 else logs
        }
    
    def _get_session_adaptation_traits(self, session_id: str, persona_id: str) -> List[str]:
        """Get adaptation traits based on current session adaptations"""
        traits = []
        
        # Debug logging
        print(f"DEBUG: Checking adaptations for session {session_id}, persona {persona_id}")
        print(f"DEBUG: Available session adaptations: {list(self.session_adaptations.keys())}")
        print(f"DEBUG: Session adaptations for this session: {self.session_adaptations.get(session_id, {})}")
        print(f"DEBUG: Base persona data available: {list(self.base_persona_data.keys())}")
        if persona_id in self.base_persona_data:
            print(f"DEBUG: Base persona data for this persona: {self.base_persona_data[persona_id]}")
        
        # Check if session has adaptations
        if session_id in self.session_adaptations:
            adaptations = self.session_adaptations[session_id]
            print(f"DEBUG: Found adaptations for session: {adaptations}")
            
            # Get base persona data for comparison - this is loaded from the database
            if persona_id in self.base_persona_data:
                base_data = self.base_persona_data[persona_id]
                print(f"DEBUG: Base data for persona: {base_data}")
                
                # Check for defensiveness changes
                if 'defensiveness_level' in adaptations:
                    # Use base value from database or default to 0.5 if not available
                    base_defensiveness = base_data.get('defensiveness_level', 0.5) if base_data.get('defensiveness_level') is not None else 0.5
                    current_defensiveness = adaptations['defensiveness_level']
                    diff = base_defensiveness - current_defensiveness
                    print(f"DEBUG: Defensiveness - base: {base_defensiveness}, current: {current_defensiveness}, diff: {diff}")
                    if diff > 0.1:
                        traits.append('defensiveness_decreased')
                        print("DEBUG: Added defensiveness_decreased trait")
                    elif diff < -0.1:
                        traits.append('defensiveness_increased')
                        print("DEBUG: Added defensiveness_increased trait")
                
                # Check for tone intensity changes
                if 'tone_intensity' in adaptations:
                    # Use base value from database or default to 0.5 if not available
                    base_tone = base_data.get('tone_intensity', 0.5) if base_data.get('tone_intensity') is not None else 0.5
                    current_tone = adaptations['tone_intensity']
                    diff = base_tone - current_tone
                    print(f"DEBUG: Tone intensity - base: {base_tone}, current: {current_tone}, diff: {diff}")
                    if diff > 0.1:
                        traits.append('tone_softened')
                        print("DEBUG: Added tone_softened trait")
                    elif diff < -0.1:
                        traits.append('tone_intensified')
                        print("DEBUG: Added tone_intensified trait")
                
                # Check for resistance sophistication changes
                if 'resistance_sophistication' in adaptations:
                    # Use base value from database or default to 0.5 if not available
                    base_resistance = base_data.get('resistance_sophistication', 0.5) if base_data.get('resistance_sophistication') is not None else 0.5
                    current_resistance = adaptations['resistance_sophistication']
                    diff = base_resistance - current_resistance
                    print(f"DEBUG: Resistance sophistication - base: {base_resistance}, current: {current_resistance}, diff: {diff}")
                    if diff > 0.1:
                        traits.append('resistance_decreased')
                        print("DEBUG: Added resistance_decreased trait")
                    elif diff < -0.1:
                        traits.append('resistance_increased')
                        print("DEBUG: Added resistance_increased trait")
                
                # Check for passive aggression activation
                if 'passive_aggression' in adaptations:
                    # Use base value from database or default to 0.5 if not available
                    base_passive_aggression = base_data.get('passive_aggression', 0.5) if base_data.get('passive_aggression') is not None else 0.5
                    current_passive_aggression = adaptations['passive_aggression']
                    print(f"DEBUG: Passive aggression - base: {base_passive_aggression}, current: {current_passive_aggression}")
                    if current_passive_aggression > 0.5:
                        traits.append('passive_aggression')
                        print("DEBUG: Added passive_aggression trait")
                
                # Check for emotional manipulation activation
                if 'emotional_manipulation' in adaptations:
                    # Use base value from database or default to 0.5 if not available
                    base_emotional_manipulation = base_data.get('emotional_manipulation', 0.5) if base_data.get('emotional_manipulation') is not None else 0.5
                    current_emotional_manipulation = adaptations['emotional_manipulation']
                    print(f"DEBUG: Emotional manipulation - base: {base_emotional_manipulation}, current: {current_emotional_manipulation}")
                    if current_emotional_manipulation > 0.5:
                        traits.append('emotional_manipulation')
                        print("DEBUG: Added emotional_manipulation trait")
            else:
                print(f"DEBUG: No base persona data found for persona_id: {persona_id}")
        else:
            print(f"DEBUG: No adaptations found for session {session_id}")
            print(f"DEBUG: Available sessions: {list(self.session_adaptations.keys())}")
        
        print(f"DEBUG: Returning adaptation traits: {traits}")
        return traits
    
    def _create_persona_from_config(self, persona_id: str, config: PersonaConfig) -> BasePersona:
        """Create persona instance from configuration"""
        # Note: This is a placeholder for the deprecated factory method
        # In the current system, personas are created via services
        from src.personas.base_persona import BasePersona
        
        class SimplePersona(BasePersona):
            def __init__(self, persona_id: str, config: PersonaConfig):
                super().__init__(
                    persona_id=persona_id,
                    name=config.name,
                    description=config.description,
                    max_tokens=getattr(config, 'max_tokens', 500)
                )
                self.config = config
                self.temperature = getattr(config, 'temperature', 0.7)
                
            def get_system_prompt(self) -> str:
                return f"You are {self.name}. {self.description}"
                
            def get_traits(self) -> List[str]:
                return getattr(self.config, 'traits', [])
        
        return SimplePersona(persona_id, config)
    
    def _reconstruct_persona_from_data(self, persona_id: str, persona_data: Dict[str, Any]) -> Optional[BasePersona]:
        """Reconstruct persona from stored data"""
        try:
            from src.personas.base_persona import BasePersona
            
            class DatabasePersona(BasePersona):
                def __init__(self, persona_id: str, data: Dict[str, Any]):
                    super().__init__(
                        persona_id=persona_id,
                        name=data.get('name', 'Unknown'),
                        description=data.get('description', ''),
                        max_tokens=data.get('max_tokens', 500)
                    )
                    self.persona_data = data
                    self.temperature = data.get('temperature', 0.7)
                    
                def get_system_prompt(self) -> str:
                    system_prompt = self.persona_data.get('system_prompt', '')
                    if system_prompt:
                        return system_prompt
                    return f"You are {self.name}. {self.description}"
                    
                def get_traits(self) -> List[str]:
                    return self.persona_data.get('traits', [])
            
            return DatabasePersona(persona_id, persona_data)
            
        except Exception as e:
            logger.error(f"Failed to reconstruct persona {persona_id}: {e}")
            return None
