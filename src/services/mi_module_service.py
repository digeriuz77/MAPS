"""
MI Module Service

Service for managing MI practice modules including listing, retrieval,
and module-related operations.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from supabase import Client

from src.models.mi_models import (
    MIPracticeModule,
    MIPracticeModuleSummary,
    MILearningPath,
    MILearningPathSummary,
    ContentType,
)

logger = logging.getLogger(__name__)


class MIModuleService:
    """
    Service for MI Practice Module operations.
    
    Handles:
    - Module listing with filtering
    - Module retrieval
    - Learning path management
    - Module discovery and recommendations
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        logger.info("MIModuleService initialized")
    
    # ============================================
    # MODULE LISTING & RETRIEVAL
    # ============================================
    
    async def list_modules(
        self,
        content_type: Optional[ContentType] = None,
        focus_area: Optional[str] = None,
        difficulty: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[MIPracticeModuleSummary]:
        """
        List available MI practice modules with optional filtering.

        Args:
            content_type: Filter by content type (shared, customer_facing, colleague_facing)
            focus_area: Filter by MI focus area (e.g., "Building Rapport")
            difficulty: Filter by difficulty level ("beginner", "intermediate", "advanced")
            user_id: If provided, includes user-specific progress information
            limit: Maximum number of modules to return
            offset: Pagination offset

        Returns:
            List of module summaries
        """
        try:
            # Build base query
            query = self.supabase.table('mi_practice_modules').select(
                'id', 'code', 'title', 'content_type', 'mi_focus_area', 'difficulty_level',
                'estimated_minutes', 'learning_objective', 'target_competencies'
            ).eq('is_active', True)

            # Apply filters
            if content_type:
                query = query.eq('content_type', content_type.value)
            if focus_area:
                query = query.eq('mi_focus_area', focus_area)
            if difficulty:
                query = query.eq('difficulty_level', difficulty)
            
            # Execute query
            result = query.limit(limit).offset(offset).execute()
            
            if not result.data:
                return []
            
            modules = []
            for module_data in result.data:
                summary = MIPracticeModuleSummary(
                    id=str(module_data['id']),
                    code=module_data['code'],
                    title=module_data['title'],
                    content_type=ContentType(module_data.get('content_type', 'shared')),
                    mi_focus_area=module_data.get('mi_focus_area'),
                    difficulty_level=module_data['difficulty_level'],
                    estimated_minutes=module_data['estimated_minutes'],
                    learning_objective=module_data['learning_objective'],
                    target_competencies=module_data.get('target_competencies', []),
                )
                
                # Add user progress if user_id provided
                if user_id:
                    progress = await self._get_user_module_progress(user_id, module_data['id'])
                    summary.user_attempts = progress.get('attempts', 0)
                    summary.best_score = progress.get('best_score')
                    summary.is_completed = progress.get('is_completed', False)
                    summary.last_attempted_at = progress.get('last_attempted_at')
                
                modules.append(summary)
            
            logger.info(f"Listed {len(modules)} modules for user {user_id or 'anonymous'}")
            return modules
            
        except Exception as e:
            logger.error(f"Error listing modules: {e}")
            raise
    
    async def get_module(self, module_id: str, user_id: Optional[str] = None) -> Optional[MIPracticeModule]:
        """
        Get detailed information about a specific module.
        
        Args:
            module_id: The module UUID
            user_id: Optional user ID for attempt history
            
        Returns:
            Full module configuration or None if not found
        """
        try:
            result = self.supabase.table('mi_practice_modules').select('*').eq('id', module_id).execute()
            
            if not result.data:
                logger.warning(f"Module not found: {module_id}")
                return None
            
            module_data = result.data[0]
            
            # Build MIPracticeModule from database data
            module = MIPracticeModule(
                id=str(module_data['id']),
                code=module_data['code'],
                title=module_data['title'],
                content_type=ContentType(module_data.get('content_type', 'shared')),
                mi_focus_area=module_data.get('mi_focus_area'),
                difficulty_level=module_data['difficulty_level'],
                estimated_minutes=module_data['estimated_minutes'],
                learning_objective=module_data['learning_objective'],
                scenario_context=module_data['scenario_context'],
                persona_config=module_data['persona_config'],
                dialogue_structure=module_data['dialogue_structure'],
                target_competencies=module_data.get('target_competencies', []),
                maps_rubric=module_data['maps_rubric'],
                maps_framework_alignment=module_data.get('maps_framework_alignment'),
                is_active=module_data['is_active'],
                created_at=module_data.get('created_at'),
                updated_at=module_data.get('updated_at'),
            )
            
            logger.info(f"Retrieved module: {module.code} for user {user_id or 'anonymous'}")
            return module
            
        except Exception as e:
            logger.error(f"Error retrieving module {module_id}: {e}")
            raise
    
    async def get_module_by_code(self, code: str) -> Optional[MIPracticeModule]:
        """
        Get module by its unique code.
        
        Args:
            code: Module code (e.g., "mi-simple-reflections-001")
            
        Returns:
            Full module configuration or None if not found
        """
        try:
            result = self.supabase.table('mi_practice_modules').select('*').eq('code', code).execute()
            
            if not result.data:
                return None
            
            module_data = result.data[0]
            return MIPracticeModule(
                id=str(module_data['id']),
                code=module_data['code'],
                title=module_data['title'],
                content_type=ContentType(module_data.get('content_type', 'shared')),
                mi_focus_area=module_data.get('mi_focus_area'),
                difficulty_level=module_data['difficulty_level'],
                estimated_minutes=module_data['estimated_minutes'],
                learning_objective=module_data['learning_objective'],
                scenario_context=module_data['scenario_context'],
                persona_config=module_data['persona_config'],
                dialogue_structure=module_data['dialogue_structure'],
                target_competencies=module_data.get('target_competencies', []),
                maps_rubric=module_data['maps_rubric'],
                maps_framework_alignment=module_data.get('maps_framework_alignment'),
                is_active=module_data['is_active'],
                created_at=module_data.get('created_at'),
                updated_at=module_data.get('updated_at'),
            )
            
        except Exception as e:
            logger.error(f"Error retrieving module by code {code}: {e}")
            raise
    
    # ============================================
    # USER PROGRESS HELPERS
    # ============================================
    
    async def _get_user_module_progress(self, user_id: str, module_id: str) -> Dict[str, Any]:
        """
        Get user's progress for a specific module.
        
        Returns dict with:
        - attempts: Number of attempts
        - best_score: Best overall score
        - is_completed: Whether module has been completed
        - last_attempted_at: Timestamp of last attempt
        """
        try:
            result = self.supabase.table('mi_practice_attempts').select(
                'completed_at', 'final_scores', 'completion_status'
            ).eq('user_id', user_id).eq('module_id', module_id).execute()
            
            if not result.data:
                return {'attempts': 0, 'best_score': None, 'is_completed': False}
            
            attempts = result.data
            completed_attempts = [a for a in attempts if a.get('completed_at')]
            
            # Calculate best score
            best_score = None
            for attempt in completed_attempts:
                scores = attempt.get('final_scores', {})
                if scores and 'overall_score' in scores:
                    score = scores['overall_score']
                    if best_score is None or score > best_score:
                        best_score = score
            
            # Get last attempt timestamp
            last_attempted_at = None
            for attempt in attempts:
                if attempt.get('completed_at'):
                    ts = attempt['completed_at']
                    if last_attempted_at is None or ts > last_attempted_at:
                        last_attempted_at = ts
            
            return {
                'attempts': len(attempts),
                'best_score': best_score,
                'is_completed': len(completed_attempts) > 0,
                'last_attempted_at': last_attempted_at,
            }
            
        except Exception as e:
            logger.error(f"Error getting user module progress: {e}")
            return {'attempts': 0, 'best_score': None, 'is_completed': False}
    
    # ============================================
    # LEARNING PATHS
    # ============================================
    
    async def list_learning_paths(
        self,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[MILearningPathSummary]:
        """
        List available learning paths.
        
        Args:
            user_id: If provided, includes enrollment status
            limit: Maximum number of paths to return
            
        Returns:
            List of learning path summaries
        """
        try:
            result = self.supabase.table('mi_learning_paths').select(
                '*'
            ).eq('is_active', True).limit(limit).execute()
            
            if not result.data:
                return []
            
            paths = []
            for path_data in result.data:
                summary = MILearningPathSummary(
                    id=str(path_data['id']),
                    code=path_data['code'],
                    title=path_data['title'],
                    description=path_data.get('description'),
                    module_count=len(path_data.get('module_sequence', [])),
                    estimated_total_minutes=path_data.get('estimated_total_minutes'),
                    target_audience=path_data.get('target_audience'),
                )
                
                # Add enrollment status if user_id provided
                if user_id:
                    progress = await self._get_user_path_progress(user_id, path_data['id'])
                    summary.is_enrolled = progress.get('is_enrolled', False)
                    summary.progress_percent = progress.get('progress_percent', 0.0)
                    summary.current_module_index = progress.get('current_module_index', 0)
                
                paths.append(summary)
            
            return paths
            
        except Exception as e:
            logger.error(f"Error listing learning paths: {e}")
            raise
    
    async def get_learning_path(self, path_id: str) -> Optional[MILearningPath]:
        """
        Get detailed information about a learning path.
        
        Args:
            path_id: The learning path UUID
            
        Returns:
            Full learning path configuration
        """
        try:
            result = self.supabase.table('mi_learning_paths').select('*').eq('id', path_id).execute()
            
            if not result.data:
                return None
            
            path_data = result.data[0]
            return MILearningPath(
                id=str(path_data['id']),
                code=path_data['code'],
                title=path_data['title'],
                description=path_data.get('description'),
                module_sequence=[str(m) for m in path_data.get('module_sequence', [])],
                target_audience=path_data.get('target_audience'),
                estimated_total_minutes=path_data.get('estimated_total_minutes'),
                maps_competencies_targeted=path_data.get('maps_competencies_targeted', []),
                is_active=path_data['is_active'],
                created_at=path_data.get('created_at'),
                updated_at=path_data.get('updated_at'),
            )
            
        except Exception as e:
            logger.error(f"Error retrieving learning path {path_id}: {e}")
            raise
    
    async def _get_user_path_progress(self, user_id: str, path_id: str) -> Dict[str, Any]:
        """Get user's progress in a learning path"""
        try:
            result = self.supabase.table('mi_user_progress').select(
                'active_learning_path_id', 'current_module_index'
            ).eq('user_id', user_id).execute()
            
            if not result.data:
                return {'is_enrolled': False, 'progress_percent': 0.0, 'current_module_index': 0}
            
            progress_data = result.data[0]
            is_enrolled = str(progress_data.get('active_learning_path_id')) == str(path_id)
            
            if not is_enrolled:
                return {'is_enrolled': False, 'progress_percent': 0.0, 'current_module_index': 0}
            
            # Get total modules in path
            path_result = self.supabase.table('mi_learning_paths').select(
                'module_sequence'
            ).eq('id', path_id).execute()
            
            total_modules = len(path_result.data[0].get('module_sequence', [])) if path_result.data else 1
            current_index = progress_data.get('current_module_index', 0)
            
            progress_percent = (current_index / total_modules * 100) if total_modules > 0 else 0.0
            
            return {
                'is_enrolled': True,
                'progress_percent': progress_percent,
                'current_module_index': current_index,
            }
            
        except Exception as e:
            logger.error(f"Error getting user path progress: {e}")
            return {'is_enrolled': False, 'progress_percent': 0.0, 'current_module_index': 0}
    
    # ============================================
    # MODULE DISCOVERY
    # ============================================
    
    async def get_focus_areas(self) -> List[Dict[str, Any]]:
        """
        Get list of available focus areas with module counts.
        
        Returns:
            List of focus area info with counts
        """
        try:
            result = self.supabase.table('mi_practice_modules').select(
                'mi_focus_area'
            ).eq('is_active', True).execute()
            
            if not result.data:
                return []
            
            # Count modules per focus area
            focus_areas = {}
            for module in result.data:
                area = module.get('mi_focus_area') or 'General'
                if area not in focus_areas:
                    focus_areas[area] = 0
                focus_areas[area] += 1
            
            return [
                {'name': area, 'module_count': count}
                for area, count in sorted(focus_areas.items())
            ]
            
        except Exception as e:
            logger.error(f"Error getting focus areas: {e}")
            raise
    
    async def get_content_types(self) -> List[Dict[str, Any]]:
        """
        Get list of content types with module counts.

        Returns:
            List of content type info with counts
        """
        try:
            result = self.supabase.table('mi_practice_modules').select(
                'content_type'
            ).eq('is_active', True).execute()

            if not result.data:
                return []

            # Count modules per content type
            content_types = {}
            for module in result.data:
                ct = module.get('content_type') or 'shared'
                if ct not in content_types:
                    content_types[ct] = 0
                content_types[ct] += 1

            return [
                {
                    'name': ct,
                    'label': {
                        'shared': 'Core Skills',
                        'customer_facing': 'Customer-Facing',
                        'colleague_facing': 'Colleague-Facing'
                    }.get(ct, ct),
                    'module_count': count
                }
                for ct, count in sorted(content_types.items())
            ]

        except Exception as e:
            logger.error(f"Error getting content types: {e}")
            raise

    async def get_difficulty_levels(self) -> List[Dict[str, Any]]:
        """
        Get list of difficulty levels with module counts.
        
        Returns:
            List of difficulty level info with counts
        """
        try:
            result = self.supabase.table('mi_practice_modules').select(
                'difficulty_level'
            ).eq('is_active', True).execute()
            
            if not result.data:
                return []
            
            # Count modules per difficulty
            difficulties = {}
            for module in result.data:
                level = module.get('difficulty_level', 'beginner')
                if level not in difficulties:
                    difficulties[level] = 0
                difficulties[level] += 1
            
            # Order by difficulty
            order = ['beginner', 'intermediate', 'advanced']
            return [
                {'name': level, 'module_count': difficulties.get(level, 0)}
                for level in order if level in difficulties
            ]
            
        except Exception as e:
            logger.error(f"Error getting difficulty levels: {e}")
            raise
    
    async def get_recommended_modules(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[MIPracticeModuleSummary]:
        """
        Get module recommendations for a user based on their progress.
        
        Args:
            user_id: The user to get recommendations for
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended module summaries
        """
        try:
            # Get user's progress
            progress_result = self.supabase.table('mi_user_progress').select('*').eq('user_id', user_id).execute()
            
            if not progress_result.data:
                # New user - recommend beginner modules
                return await self.list_modules(difficulty='beginner', limit=limit)
            
            progress = progress_result.data[0]
            
            # Check if user has an active learning path
            active_path_id = progress.get('active_learning_path_id')
            if active_path_id:
                # Get next module in path
                path = await self.get_learning_path(str(active_path_id))
                if path:
                    current_index = progress.get('current_module_index', 0)
                    if current_index < len(path.module_sequence):
                        next_module_id = path.module_sequence[current_index]
                        next_module = await self.get_module(next_module_id)
                        if next_module:
                            return [MIPracticeModuleSummary(
                                id=next_module.id,
                                code=next_module.code,
                                title=next_module.title,
                                content_type=next_module.content_type,
                                mi_focus_area=next_module.mi_focus_area,
                                difficulty_level=next_module.difficulty_level,
                                estimated_minutes=next_module.estimated_minutes,
                                learning_objective=next_module.learning_objective,
                                target_competencies=next_module.target_competencies,
                            )]
            
            # Recommend based on competency gaps
            competency_scores = progress.get('competency_scores', {})
            weak_competencies = [
                comp for comp, data in competency_scores.items()
                if data.get('current', 0) < 7.0
            ]
            
            if weak_competencies:
                # Find modules targeting weak competencies
                all_modules = await self.list_modules(user_id=user_id, limit=50)
                recommended = []
                
                for module in all_modules:
                    if any(comp in module.target_competencies for comp in weak_competencies):
                        if not module.is_completed:
                            recommended.append(module)
                    
                    if len(recommended) >= limit:
                        break
                
                if recommended:
                    return recommended
            
            # Fallback: return incomplete modules at user's level
            return await self.list_modules(user_id=user_id, limit=limit)
            
        except Exception as e:
            logger.error(f"Error getting recommended modules: {e}")
            # Fallback to beginner modules
            return await self.list_modules(difficulty='beginner', limit=limit)
