"""
Supabase database service for MITI analysis
"""
import logging
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from src.config.settings import get_settings
from .types import MitiCode

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for accessing MITI database in Supabase"""
    
    def __init__(self):
        settings = get_settings()
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not configured - database features disabled")
            self.client = None
        else:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Database service initialized successfully")
    
    def get_miti_code_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all MITI code definitions from database.
        
        Returns:
            Dictionary mapping code -> definition data
        """
        if not self.client:
            logger.warning("Database not available, returning empty definitions")
            return {}
        
        try:
            response = self.client.table('miti_code_definitions').select('*').execute()
            
            if response.data:
                definitions = {}
                for row in response.data:
                    definitions[row['code']] = {
                        'full_name': row['full_name'],
                        'category': row['category'],
                        'adherence_type': row['adherence_type'],
                        'definition': row['definition'],
                        'key_indicators': row['key_indicators'],
                        'examples': row['examples'],
                        'scoring_notes': row['scoring_notes']
                    }
                
                logger.info(f"Retrieved {len(definitions)} MITI code definitions")
                return definitions
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to retrieve MITI definitions: {e}")
            return {}
    
    def get_training_examples(
        self, 
        example_type: Optional[str] = None,
        focus_codes: Optional[List[str]] = None,
        difficulty_level: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve training examples from database with optional filtering.
        
        Args:
            example_type: Filter by type ('excellent', 'good', 'poor', 'mixed', 'edge_case')
            focus_codes: Filter by MITI codes these examples focus on
            difficulty_level: Filter by difficulty ('basic', 'intermediate', 'advanced')
            limit: Maximum number of examples to return
            
        Returns:
            List of training examples
        """
        if not self.client:
            logger.warning("Database not available, returning empty examples")
            return []
        
        try:
            query = self.client.table('miti_examples').select('*')
            
            # Apply filters
            if example_type:
                query = query.eq('example_type', example_type)
            
            if difficulty_level:
                query = query.eq('difficulty_level', difficulty_level)
            
            if focus_codes:
                # Use overlap operator to find examples that contain any of the focus codes
                query = query.overlaps('focus_codes', focus_codes)
            
            if limit:
                query = query.limit(limit)
            
            # Order by difficulty and type for consistent results
            query = query.order('difficulty_level').order('example_type')
            
            response = query.execute()
            
            if response.data:
                logger.info(f"Retrieved {len(response.data)} training examples")
                return response.data
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to retrieve training examples: {e}")
            return []
    
    def get_system_prompt(self, name: str = 'workplace_mi_analysis_v1.0') -> Optional[str]:
        """
        Retrieve system prompt from database.
        
        Args:
            name: Name of the prompt template to retrieve
            
        Returns:
            System prompt text or None if not found
        """
        if not self.client:
            logger.warning("Database not available, returning None for system prompt")
            return None
        
        try:
            response = (self.client
                       .table('prompt_templates')
                       .select('system_prompt')
                       .eq('name', name)
                       .eq('is_active', True)
                       .execute())
            
            if response.data and len(response.data) > 0:
                logger.info(f"Retrieved system prompt: {name}")
                return response.data[0]['system_prompt']
            
            logger.warning(f"System prompt not found: {name}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve system prompt: {e}")
            return None
    
    def get_examples_for_codes(self, codes: List[str]) -> List[Dict[str, Any]]:
        """
        Get training examples that demonstrate specific MITI codes.
        
        Args:
            codes: List of MITI code strings to find examples for
            
        Returns:
            List of relevant examples
        """
        return self.get_training_examples(focus_codes=codes)
    
    def get_examples_by_difficulty(self, difficulty: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get training examples of a specific difficulty level.
        
        Args:
            difficulty: 'basic', 'intermediate', or 'advanced'
            limit: Maximum number of examples
            
        Returns:
            List of examples
        """
        return self.get_training_examples(difficulty_level=difficulty, limit=limit)
    
    def get_excellent_examples(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get examples showing excellent MI technique."""
        return self.get_training_examples(example_type='excellent', limit=limit)
    
    def get_poor_examples(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get examples showing poor MI technique for learning."""
        return self.get_training_examples(example_type='poor', limit=limit)
    
    def search_examples(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for examples containing specific terms.
        
        Args:
            search_term: Term to search for in titles, descriptions, or content
            
        Returns:
            List of matching examples
        """
        if not self.client:
            return []
        
        try:
            # Search in multiple fields using ilike (case-insensitive)
            response = (self.client
                       .table('miti_examples')
                       .select('*')
                       .or_(f'title.ilike.%{search_term}%,description.ilike.%{search_term}%,transcript_snippet.ilike.%{search_term}%,learning_points.ilike.%{search_term}%')
                       .execute())
            
            if response.data:
                logger.info(f"Found {len(response.data)} examples matching '{search_term}'")
                return response.data
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to search examples: {e}")
            return []

# Singleton instance
_database_service = None

def get_database_service() -> DatabaseService:
    """Get or create the database service singleton"""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service