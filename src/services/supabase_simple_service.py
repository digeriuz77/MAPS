"""
Simple Supabase Service for Persona Storage (No Vector/Embeddings)
"""
import logging
from typing import List, Dict, Any, Optional
import json

from supabase import create_client, Client

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

class SupabaseSimpleService:
    """Simple Supabase service for persona storage without vector operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Client = None
        
    async def initialize(self):
        """Initialize Supabase client"""
        try:
            self.client = create_client(
                self.settings.SUPABASE_URL,
                self.settings.SUPABASE_SERVICE_ROLE_KEY
            )
            logger.info("Supabase simple service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase service: {e}")
            raise
    
    async def store_persona(self, persona_id: str, persona_data: Dict[str, Any]) -> str:
        """Store persona in Supabase (no embeddings)"""
        try:
            # Check if persona already exists
            existing = self.client.table('personas').select('id').eq('persona_id', persona_id).execute()
            
            if existing.data:
                # Update existing persona
                result = self.client.table('personas').update(persona_data).eq('persona_id', persona_id).execute()
                logger.info(f"Updated existing persona: {persona_id}")
            else:
                # Insert new persona
                persona_data['persona_id'] = persona_id
                result = self.client.table('personas').insert(persona_data).execute()
                logger.info(f"Created new persona: {persona_id}")
            
            if result.data:
                return result.data[0]['id']
            else:
                raise Exception(f"Failed to store persona: {result}")
                
        except Exception as e:
            logger.error(f"Failed to store persona {persona_id}: {e}")
            raise
    
    async def get_persona(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve specific persona by ID"""
        try:
            result = self.client.table('personas').select('*').eq('persona_id', persona_id).execute()

            if result.data and len(result.data) > 0:
                row = result.data[0]

                # Parse metadata - it might be a JSON string, a dict, or the prompt text itself
                metadata = row.get('metadata', {})
                parsed_metadata = {}

                if isinstance(metadata, str):
                    # Try to parse as JSON first
                    import json
                    try:
                        parsed_metadata = json.loads(metadata)
                    except json.JSONDecodeError:
                        # If it's not JSON, treat the entire string as the system prompt
                        parsed_metadata = {'system_prompt': metadata}

                elif isinstance(metadata, dict):
                    parsed_metadata = metadata
                else:
                    parsed_metadata = {}

                # Extract system prompt - check multiple sources
                system_prompt = None

                # First, check if system_prompt exists in the row directly (not in metadata)
                if 'system_prompt' in row and row['system_prompt']:
                    system_prompt = row['system_prompt']
                    # If it's a JSON string (starts and ends with quotes), parse it
                    if isinstance(system_prompt, str) and system_prompt.startswith('"') and system_prompt.endswith('"'):
                        try:
                            import json
                            system_prompt = json.loads(system_prompt)
                        except json.JSONDecodeError:
                            # Remove surrounding quotes if present
                            if system_prompt.startswith('"') and system_prompt.endswith('"'):
                                system_prompt = system_prompt[1:-1]
                            # Unescape JSON
                            system_prompt = system_prompt.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')

                # If not found, check parsed metadata
                if not system_prompt:
                    system_prompt = (parsed_metadata.get('system_prompt') or
                                   parsed_metadata.get('prompt'))

                # If still not found, try coach_knowledge table
                if not system_prompt:
                    try:
                        knowledge_result = self.client.table('coach_knowledge').select('*').eq('persona_id', persona_id).eq('knowledge_type', 'system_prompt').execute()
                        if knowledge_result.data and len(knowledge_result.data) > 0:
                            system_prompt = knowledge_result.data[0].get('content')
                    except Exception as e:
                        logger.warning(f"Could not fetch system prompt from coach_knowledge for {persona_id}: {e}")

                return {
                    'persona_id': row['persona_id'],
                    'metadata': parsed_metadata,
                    'persona_type': row.get('persona_type'),
                    'name': row.get('name'),
                    'description': row.get('description'),
                    'max_tokens': row.get('max_tokens', 400),
                    # Extract trait values from parsed metadata
                    'defensiveness_level': parsed_metadata.get('defensiveness_level'),
                    'resistance_sophistication': parsed_metadata.get('resistance_sophistication'),
                    'intellectual_superiority': parsed_metadata.get('intellectual_superiority'),
                    'passive_aggression': parsed_metadata.get('passive_aggression'),
                    'emotional_manipulation': parsed_metadata.get('emotional_manipulation'),
                    'tone_intensity': parsed_metadata.get('tone_intensity'),
                    'language_markers': parsed_metadata.get('language_markers'),
                    'communication_style': parsed_metadata.get('communication_style'),
                    'workplace_context': parsed_metadata.get('company_id') or parsed_metadata.get('workplace_context'),
                    'specific_traits': parsed_metadata.get('traits') or parsed_metadata.get('specific_traits'),
                    # System prompt from metadata or coach_knowledge
                    'system_prompt': system_prompt
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get persona {persona_id}: {e}")
            return None
    
    async def list_all_personas(self) -> List[Dict[str, Any]]:
        """List all personas in the database"""
        try:
            result = self.client.table('personas').select('*').execute()

            if result.data:
                personas = []
                for row in result.data:
                    # Parse metadata - it might be a JSON string, a dict, or the prompt text itself
                    metadata = row.get('metadata', {})
                    parsed_metadata = {}

                    if isinstance(metadata, str):
                        # Try to parse as JSON first
                        import json
                        try:
                            parsed_metadata = json.loads(metadata)
                        except json.JSONDecodeError:
                            # If it's not JSON, treat the entire string as the system prompt
                            parsed_metadata = {'system_prompt': metadata}

                    elif isinstance(metadata, dict):
                        parsed_metadata = metadata
                    else:
                        parsed_metadata = {}

                    # Extract system prompt - check multiple sources
                    system_prompt = None

                    # First, check if system_prompt exists in the row directly (not in metadata)
                    if 'system_prompt' in row and row['system_prompt']:
                        system_prompt = row['system_prompt']
                        # If it's a JSON string (starts and ends with quotes), parse it
                        if isinstance(system_prompt, str) and system_prompt.startswith('"') and system_prompt.endswith('"'):
                            try:
                                import json
                                system_prompt = json.loads(system_prompt)
                            except json.JSONDecodeError:
                                # Remove surrounding quotes if present
                                if system_prompt.startswith('"') and system_prompt.endswith('"'):
                                    system_prompt = system_prompt[1:-1]
                                # Unescape JSON
                                system_prompt = system_prompt.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')

                    # If not found, check parsed metadata
                    if not system_prompt:
                        system_prompt = (parsed_metadata.get('system_prompt') or
                                       parsed_metadata.get('prompt'))

                    # If still not found, try coach_knowledge table
                    if not system_prompt:
                        try:
                            persona_id = row['persona_id']
                            knowledge_result = self.client.table('coach_knowledge').select('*').eq('persona_id', persona_id).eq('knowledge_type', 'system_prompt').execute()
                            if knowledge_result.data and len(knowledge_result.data) > 0:
                                system_prompt = knowledge_result.data[0].get('content')
                        except Exception as e:
                            logger.warning(f"Could not fetch system prompt from coach_knowledge for {row['persona_id']}: {e}")

                    # Extract trait values from parsed metadata
                    persona_data = {
                        'persona_id': row['persona_id'],
                        'metadata': parsed_metadata,
                        'persona_type': row.get('persona_type'),
                        'name': row.get('name'),
                        'description': row.get('description'),
                        'max_tokens': row.get('max_tokens', 400),
                        # Extract trait values from parsed metadata
                        'defensiveness_level': parsed_metadata.get('defensiveness_level'),
                        'resistance_sophistication': parsed_metadata.get('resistance_sophistication'),
                        'intellectual_superiority': parsed_metadata.get('intellectual_superiority'),
                        'passive_aggression': parsed_metadata.get('passive_aggression'),
                        'emotional_manipulation': parsed_metadata.get('emotional_manipulation'),
                        'tone_intensity': parsed_metadata.get('tone_intensity'),
                        'language_markers': parsed_metadata.get('language_markers'),
                        'communication_style': parsed_metadata.get('communication_style'),
                        'workplace_context': parsed_metadata.get('company_id') or parsed_metadata.get('workplace_context'),
                        'specific_traits': parsed_metadata.get('traits') or parsed_metadata.get('specific_traits'),
                        # System prompt from metadata or coach_knowledge
                        'system_prompt': system_prompt
                    }
                    personas.append(persona_data)
                return personas
            return []

        except Exception as e:
            logger.error(f"Failed to list personas: {e}")
            return []
    
    async def search_similar_personas(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Simple text search (not vector-based)"""
        try:
            # Simple search by name or type
            result = self.client.table('personas').select('*').or_(
                f"name.ilike.%{query}%,persona_type.ilike.%{query}%,description.ilike.%{query}%"
            ).limit(limit).execute()
            
            if result.data:
                return [
                    {
                        'persona_id': row['persona_id'],  # Consistent with list_all_personas
                        'metadata': row.get('metadata', {}),  # Extract only the metadata column, not the entire row
                        'similarity': 1.0  # Dummy similarity score
                    } for row in result.data
                ]
            return []
            
        except Exception as e:
            logger.error(f"Failed to search personas: {e}")
            return []
    
    async def get_company_values(self, company_id: str) -> List[Dict[str, Any]]:
        """Get company values (deprecated - now stored in coach_knowledge)"""
        try:
            # Search coach_knowledge for company values
            result = self.client.table('coach_knowledge').select('*').eq('knowledge_type', 'company_values').execute()
            if result.data:
                # Filter by company_id if specified in metadata
                filtered_data = []
                for item in result.data:
                    metadata = item.get('metadata', {})
                    if metadata.get('company_id') == company_id:
                        filtered_data.append(item)
                return filtered_data
            return []
        except Exception as e:
            logger.error(f"Failed to get company values: {e}")
            return []
    
    async def get_coaching_responses(self) -> List[Dict[str, Any]]:
        """Get all coaching responses from coach_knowledge table"""
        try:
            result = self.client.table('coach_knowledge').select('*').eq('knowledge_type', 'coaching_response').execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get coaching responses: {e}")
            return []
    
    async def store_conversation(self, conversation_data: dict) -> str:
        """Store conversation data in conversations and messages tables"""
        try:
            # Store basic conversation record
            conversation_record = {
                'session_id': conversation_data.get('session_id', 'unknown'),
                'persona_id': conversation_data.get('persona_id'),
                'user_id': conversation_data.get('user_id'),
                'metadata': {}
            }
            
            conv_result = self.client.table('conversations').insert(conversation_record).execute()
            
            if conv_result.data and conversation_data.get('messages'):
                conversation_id = conv_result.data[0]['id']
                
                # Store individual messages
                for message in conversation_data.get('messages', []):
                    message_record = {
                        'conversation_id': conversation_id,
                        'role': message.get('role', 'user'),
                        'content': message.get('content', ''),
                        'metadata': message.get('metadata', {}),
                        'tokens_used': message.get('tokens_used', 0)
                    }
                    self.client.table('messages').insert(message_record).execute()
                
                logger.info(f"Stored conversation {conversation_id} with {len(conversation_data.get('messages', []))} messages")
                return str(conversation_id)
            
            return conversation_data.get('conversation_id', 'stored')
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            # Return a fallback ID instead of raising error
            return f"conversation_{conversation_data.get('session_id', 'unknown')}"
    
    async def update_persona(self, persona_id: str, persona_data: Dict[str, Any]) -> bool:
        """Update existing persona"""
        try:
            result = self.client.table('personas').update(persona_data).eq('persona_id', persona_id).execute()
            success = len(result.data) > 0
            if success:
                logger.info(f"Updated persona: {persona_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to update persona {persona_id}: {e}")
            return False
    
    async def delete_persona(self, persona_id: str) -> bool:
        """Delete persona from database"""
        try:
            result = self.client.table('personas').delete().eq('persona_id', persona_id).execute()
            success = len(result.data) > 0
            if success:
                logger.info(f"Deleted persona: {persona_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete persona {persona_id}: {e}")
            return False
    
    async def close(self):
        """Close Supabase client connections (placeholder for cleanup)"""
        # Supabase client doesn't require explicit closing
        # This method exists for compatibility with the lifespan manager
        logger.info("Supabase simple service closed")
        pass
