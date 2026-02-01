"""
MI Progress Service

Service for tracking and aggregating user progress across MI practice modules.
Handles competency scoring, technique tracking, and learning insights.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from supabase import Client

from src.models.mi_models import (
    MIUserProgress,
    MIPracticeAttempt,
    CompetencyScoreDetail,
    TechniquePracticeDetail,
    UserProgressResponse,
)
from src.services.mi_scoring_service import MIScoringService

logger = logging.getLogger(__name__)


class MIProgressService:
    """
    Service for MI user progress tracking.
    
    Handles:
    - Aggregating progress across attempts
    - Competency score tracking with trends
    - Technique practice statistics
    - Learning insight generation
    - Learning path enrollment
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.scoring_service = MIScoringService()
        logger.info("MIProgressService initialized")
    
    # ============================================
    # PROGRESS RETRIEVAL
    # ============================================
    
    async def get_user_progress(self, user_id: str) -> Optional[MIUserProgress]:
        """
        Get or create user progress record.
        
        Args:
            user_id: The user UUID
            
        Returns:
            MIUserProgress or None if error
        """
        try:
            result = self.supabase.table('mi_user_progress').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                progress_data = result.data[0]
                return self._build_progress_from_data(progress_data)
            
            # Create new progress record
            return await self._create_user_progress(user_id)
            
        except Exception as e:
            logger.error(f"Error getting user progress for {user_id}: {e}")
            return None
    
    async def get_progress_response(self, user_id: str) -> Optional[UserProgressResponse]:
        """
        Get formatted progress response for API.
        
        Args:
            user_id: The user UUID
            
        Returns:
            UserProgressResponse with aggregated data
        """
        progress = await self.get_user_progress(user_id)
        if not progress:
            return None
        
        # Get recent attempts
        recent_attempts = await self._get_recent_attempts(user_id, limit=5)
        
        # Calculate overall progress percentage
        total_modules_result = self.supabase.table('mi_practice_modules').select('id', count='exact').eq('is_active', True).execute()
        total_modules = getattr(total_modules_result, 'count', 0) or 0

        overall_percent = 0.0
        if total_modules > 0:
            # Count unique completed modules
            completed_result = self.supabase.table('mi_practice_attempts').select('module_id').eq('user_id', user_id).eq('completion_status', 'completed').execute()
            completed_data = getattr(completed_result, 'data', None) or []
            unique_completed = len(set(a['module_id'] for a in completed_data))
            overall_percent = (unique_completed / total_modules) * 100
        
        return UserProgressResponse(
            modules_completed=progress.modules_completed,
            modules_attempted=progress.modules_attempted,
            total_practice_minutes=progress.total_practice_minutes,
            overall_progress_percent=round(overall_percent, 1),
            competency_scores=progress.competency_scores,
            techniques_practiced=progress.techniques_practiced,
            recent_attempts=recent_attempts,
            learning_insights=progress.learning_insights,
        )
    
    async def get_competency_breakdown(self, user_id: str) -> Dict[str, Any]:
        """
        Get detailed competency breakdown for a user.
        
        Returns:
            Dict with competency scores, trends, and analysis
        """
        progress = await self.get_user_progress(user_id)
        if not progress:
            return {'competencies': [], 'overall_average': 0.0}
        
        # Get all attempts for trend analysis
        attempts_result = self.supabase.table('mi_practice_attempts').select(
            'final_scores', 'completed_at'
        ).eq('user_id', user_id).eq('completion_status', 'completed').order('completed_at').execute()
        
        competency_history = {}
        
        if attempts_result.data:
            for attempt in attempts_result.data:
                final_scores = attempt.get('final_scores', {})
                comp_scores = final_scores.get('competency_scores', {})
                completed_at = attempt.get('completed_at')
                
                for comp_id, score in comp_scores.items():
                    if comp_id not in competency_history:
                        competency_history[comp_id] = []
                    competency_history[comp_id].append({
                        'score': score,
                        'date': completed_at,
                    })
        
        # Build competency breakdown
        competencies = []
        for comp_id, detail in progress.competency_scores.items():
            history = competency_history.get(comp_id, [])
            
            # Calculate trend
            trend = detail.trend
            if len(history) >= 3:
                recent = [h['score'] for h in history[-3:]]
                older = [h['score'] for h in history[:-3]] if len(history) > 3 else [history[0]['score']]
                
                recent_avg = sum(recent) / len(recent)
                older_avg = sum(older) / len(older)
                
                if recent_avg > older_avg + 0.5:
                    trend = 'improving'
                elif recent_avg < older_avg - 0.5:
                    trend = 'declining'
                else:
                    trend = 'stable'
            
            competencies.append({
                'id': comp_id,
                'current_score': detail.current,
                'trend': trend,
                'attempts': detail.attempts,
                'history': history[-5:],  # Last 5 scores
            })
        
        # Calculate overall average
        overall_avg = 0.0
        if competencies:
            overall_avg = sum(c['current_score'] for c in competencies) / len(competencies)
        
        return {
            'competencies': competencies,
            'overall_average': round(overall_avg, 1),
            'total_attempts': progress.modules_attempted,
        }
    
    # ============================================
    # PROGRESS UPDATES
    # ============================================
    
    async def update_progress_after_attempt(self, attempt: MIPracticeAttempt) -> bool:
        """
        Update user progress after an attempt is completed.
        
        Args:
            attempt: The completed attempt
            
        Returns:
            True if successful
        """
        try:
            progress = await self.get_user_progress(attempt.user_id)
            if not progress:
                return False
            
            # Update basic stats
            progress.modules_attempted += 1
            if attempt.completion_status == 'completed':
                progress.modules_completed += 1
            
            # Add practice time (estimate from module)
            module_result = self.supabase.table('mi_practice_modules').select('estimated_minutes').eq('id', attempt.module_id).execute()
            if module_result.data:
                minutes = module_result.data[0].get('estimated_minutes', 5)
                progress.total_practice_minutes += minutes
            
            # Update competency scores
            if attempt.final_scores and attempt.final_scores.competency_scores:
                for comp_id, score in attempt.final_scores.competency_scores.items():
                    await self._update_competency_score(progress, comp_id, score)
            
            # Update technique practice
            if attempt.final_scores and attempt.final_scores.technique_counts:
                for technique, count in attempt.final_scores.technique_counts.items():
                    await self._update_technique_practice(progress, technique, count)
            
            # Save updated progress
            await self._save_progress(progress)
            
            logger.info(f"Updated progress for user {attempt.user_id} after attempt {attempt.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating progress after attempt: {e}")
            return False
    
    async def _update_competency_score(
        self,
        progress: MIUserProgress,
        competency_id: str,
        new_score: float
    ):
        """Update a competency score with rolling average"""
        if competency_id not in progress.competency_scores:
            progress.competency_scores[competency_id] = CompetencyScoreDetail(
                current=new_score,
                trend='stable',
                attempts=1,
            )
        else:
            existing = progress.competency_scores[competency_id]
            
            # Rolling average (weighted toward recent scores)
            total_attempts = existing.attempts + 1
            weighted_avg = (existing.current * existing.attempts + new_score) / total_attempts
            
            # Determine trend
            trend = existing.trend
            if new_score > existing.current + 0.5:
                trend = 'improving'
            elif new_score < existing.current - 0.5:
                trend = 'declining'
            
            progress.competency_scores[competency_id] = CompetencyScoreDetail(
                current=round(weighted_avg, 1),
                trend=trend,
                attempts=total_attempts,
            )
    
    async def _update_technique_practice(
        self,
        progress: MIProgress,
        technique: str,
        count: int
    ):
        """Update technique practice statistics"""
        if technique not in progress.techniques_practiced:
            progress.techniques_practiced[technique] = TechniquePracticeDetail(
                count=count,
                avg_quality=7.0,  # Default starting quality
            )
        else:
            existing = progress.techniques_practiced[technique]
            
            # Update count
            new_count = existing.count + count
            
            # Slowly adjust quality (simplified)
            # In reality, this would be based on scoring
            quality_adjustment = 0.1 if count > 0 else 0
            new_quality = min(10.0, existing.avg_quality + quality_adjustment)
            
            progress.techniques_practiced[technique] = TechniquePracticeDetail(
                count=new_count,
                avg_quality=round(new_quality, 1),
            )
    
    # ============================================
    # LEARNING PATHS
    # ============================================
    
    async def enroll_in_path(self, user_id: str, path_id: str) -> bool:
        """
        Enroll a user in a learning path.
        
        Args:
            user_id: The user UUID
            path_id: The learning path UUID
            
        Returns:
            True if successful
        """
        try:
            # Verify path exists
            path_result = self.supabase.table('mi_learning_paths').select('id').eq('id', path_id).execute()
            if not path_result.data:
                logger.warning(f"Learning path not found: {path_id}")
                return False
            
            # Update user progress
            progress = await self.get_user_progress(user_id)
            if not progress:
                return False
            
            update_data = {
                'active_learning_path_id': path_id,
                'current_module_index': 0,
                'updated_at': datetime.utcnow().isoformat(),
            }
            
            result = self.supabase.table('mi_user_progress').update(update_data).eq('user_id', user_id).execute()
            
            if result.data:
                logger.info(f"User {user_id} enrolled in path {path_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error enrolling in path: {e}")
            return False
    
    async def advance_in_path(self, user_id: str) -> bool:
        """
        Advance user to next module in their active learning path.
        
        Returns:
            True if advanced, False if at end or not enrolled
        """
        try:
            progress = await self.get_user_progress(user_id)
            if not progress or not progress.active_learning_path_id:
                return False
            
            # Get path details
            path_result = self.supabase.table('mi_learning_paths').select('module_sequence').eq('id', progress.active_learning_path_id).execute()
            if not path_result.data:
                return False
            
            module_sequence = path_result.data[0].get('module_sequence', [])
            current_index = progress.current_module_index
            
            if current_index >= len(module_sequence) - 1:
                # At end of path
                return False
            
            # Advance index
            new_index = current_index + 1
            
            result = self.supabase.table('mi_user_progress').update({
                'current_module_index': new_index,
                'updated_at': datetime.utcnow().isoformat(),
            }).eq('user_id', user_id).execute()
            
            if result.data:
                logger.info(f"User {user_id} advanced to module {new_index} in path")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error advancing in path: {e}")
            return False
    
    async def get_active_path_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get progress in the currently active learning path.
        
        Returns:
            Dict with path details and current position
        """
        try:
            progress = await self.get_user_progress(user_id)
            if not progress or not progress.active_learning_path_id:
                return None
            
            # Get path details
            path_result = self.supabase.table('mi_learning_paths').select('*').eq('id', progress.active_learning_path_id).execute()
            if not path_result.data:
                return None
            
            path_data = path_result.data[0]
            module_sequence = path_data.get('module_sequence', [])
            current_index = progress.current_module_index
            
            # Get current module details
            current_module = None
            if current_index < len(module_sequence):
                module_result = self.supabase.table('mi_practice_modules').select('id', 'code', 'title').eq('id', module_sequence[current_index]).execute()
                if module_result.data:
                    current_module = module_result.data[0]
            
            # Get next module
            next_module = None
            if current_index + 1 < len(module_sequence):
                next_result = self.supabase.table('mi_practice_modules').select('id', 'code', 'title').eq('id', module_sequence[current_index + 1]).execute()
                if next_result.data:
                    next_module = next_result.data[0]
            
            # Calculate progress percentage
            progress_percent = (current_index / len(module_sequence) * 100) if module_sequence else 0
            
            return {
                'path_id': str(path_data['id']),
                'path_code': path_data['code'],
                'path_title': path_data['title'],
                'description': path_data.get('description'),
                'total_modules': len(module_sequence),
                'completed_modules': current_index,
                'progress_percent': round(progress_percent, 1),
                'current_module': current_module,
                'next_module': next_module,
                'is_complete': current_index >= len(module_sequence),
            }
            
        except Exception as e:
            logger.error(f"Error getting active path progress: {e}")
            return None
    
    # ============================================
    # INSIGHTS & ANALYTICS
    # ============================================
    
    async def generate_learning_insights(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Generate personalized learning insights for a user.
        
        Args:
            user_id: The user UUID
            limit: Maximum number of insights
            
        Returns:
            List of insight dicts
        """
        insights = []
        
        try:
            progress = await self.get_user_progress(user_id)
            if not progress:
                return insights
            
            # Insight 1: Strength identification
            if progress.competency_scores:
                strongest = max(progress.competency_scores.items(), key=lambda x: x[1].current)
                if strongest[1].current >= 7.0:
                    insights.append({
                        'type': 'strength',
                        'title': f'Strong {strongest[0]} Skills',
                        'description': f'Your {strongest[0]} score of {strongest[1].current} shows solid competency.',
                        'competency': strongest[0],
                    })
            
            # Insight 2: Improvement area
            if progress.competency_scores:
                weakest = min(progress.competency_scores.items(), key=lambda x: x[1].current)
                if weakest[1].current < 7.0:
                    insights.append({
                        'type': 'improvement',
                        'title': f'Develop Your {weakest[0]} Skills',
                        'description': f'Focus on {weakest[0]} to strengthen your practice.',
                        'competency': weakest[0],
                    })
            
            # Insight 3: Technique balance
            if progress.techniques_practiced:
                reflection_count = progress.techniques_practiced.get('simple_reflection', TechniquePracticeDetail()).count
                question_count = (
                    progress.techniques_practiced.get('open_question', TechniquePracticeDetail()).count +
                    progress.techniques_practiced.get('closed_question', TechniquePracticeDetail()).count
                )
                
                if question_count > reflection_count * 2:
                    insights.append({
                        'type': 'tip',
                        'title': 'Balance Questions with Reflections',
                        'description': 'Try using 2 reflections for every question to deepen understanding.',
                        'competency': '2.1.1',
                    })
            
            # Insight 4: Practice consistency
            recent_attempts = await self._get_recent_attempts(user_id, limit=7)
            if len(recent_attempts) >= 3:
                insights.append({
                    'type': 'achievement',
                    'title': 'Consistent Practice',
                    'description': f'You\'ve completed {len(recent_attempts)} practice sessions recently. Keep it up!',
                })
            elif len(recent_attempts) == 0 and progress.modules_attempted > 0:
                insights.append({
                    'type': 'reminder',
                    'title': 'Return to Practice',
                    'description': 'It\'s been a while since your last practice. Regular practice builds skills.',
                })
            
            # Insight 5: Module completion
            if progress.modules_completed > 0:
                insights.append({
                    'type': 'achievement',
                    'title': 'Module Explorer',
                    'description': f'You\'ve completed {progress.modules_completed} modules. Great progress!',
                })
            
            return insights[:limit]
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return insights
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    async def _create_user_progress(self, user_id: str) -> Optional[MIUserProgress]:
        """Create a new user progress record"""
        try:
            insert_data = {
                'user_id': user_id,
                'modules_completed': 0,
                'modules_attempted': 0,
                'total_practice_minutes': 0,
                'competency_scores': {},
                'techniques_practiced': {},
                'current_module_index': 0,
                'learning_insights': [],
            }
            
            result = self.supabase.table('mi_user_progress').insert(insert_data).execute()
            
            if result.data:
                logger.info(f"Created progress record for user {user_id}")
                return self._build_progress_from_data(result.data[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating user progress: {e}")
            return None
    
    async def _save_progress(self, progress: MIUserProgress) -> bool:
        """Save progress to database"""
        try:
            update_data = {
                'modules_completed': progress.modules_completed,
                'modules_attempted': progress.modules_attempted,
                'total_practice_minutes': progress.total_practice_minutes,
                'competency_scores': {
                    k: {
                        'current': v.current,
                        'trend': v.trend,
                        'attempts': v.attempts,
                    }
                    for k, v in progress.competency_scores.items()
                },
                'techniques_practiced': {
                    k: {
                        'count': v.count,
                        'avg_quality': v.avg_quality,
                    }
                    for k, v in progress.techniques_practiced.items()
                },
                'active_learning_path_id': progress.active_learning_path_id,
                'current_module_index': progress.current_module_index,
                'learning_insights': progress.learning_insights,
                'updated_at': datetime.utcnow().isoformat(),
            }
            
            result = self.supabase.table('mi_user_progress').update(update_data).eq('user_id', progress.user_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
            return False
    
    def _build_progress_from_data(self, data: Dict[str, Any]) -> MIUserProgress:
        """Build MIUserProgress from database data"""
        # Parse competency scores
        competency_scores = {}
        for comp_id, comp_data in data.get('competency_scores', {}).items():
            competency_scores[comp_id] = CompetencyScoreDetail(
                current=comp_data.get('current', 0.0),
                trend=comp_data.get('trend', 'stable'),
                attempts=comp_data.get('attempts', 0),
            )
        
        # Parse technique practice
        techniques_practiced = {}
        for tech, tech_data in data.get('techniques_practiced', {}).items():
            techniques_practiced[tech] = TechniquePracticeDetail(
                count=tech_data.get('count', 0),
                avg_quality=tech_data.get('avg_quality', 0.0),
            )
        
        return MIUserProgress(
            id=str(data['id']),
            user_id=str(data['user_id']),
            modules_completed=data.get('modules_completed', 0),
            modules_attempted=data.get('modules_attempted', 0),
            total_practice_minutes=data.get('total_practice_minutes', 0),
            competency_scores=competency_scores,
            techniques_practiced=techniques_practiced,
            active_learning_path_id=str(data['active_learning_path_id']) if data.get('active_learning_path_id') else None,
            current_module_index=data.get('current_module_index', 0),
            learning_insights=data.get('learning_insights', []),
            updated_at=data.get('updated_at'),
        )
    
    async def _get_recent_attempts(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent attempts for a user"""
        try:
            result = self.supabase.table('mi_practice_attempts').select(
                'id', 'module_id', 'completed_at', 'completion_status', 'final_scores'
            ).eq('user_id', user_id).order('started_at', desc=True).limit(limit).execute()
            
            attempts = []
            for attempt_data in result.data:
                final_scores = attempt_data.get('final_scores', {})
                attempts.append({
                    'attempt_id': str(attempt_data['id']),
                    'module_id': str(attempt_data['module_id']),
                    'completed_at': attempt_data.get('completed_at'),
                    'status': attempt_data.get('completion_status'),
                    'score': final_scores.get('overall_score') if final_scores else None,
                })
            
            return attempts
            
        except Exception as e:
            logger.error(f"Error getting recent attempts: {e}")
            return []
