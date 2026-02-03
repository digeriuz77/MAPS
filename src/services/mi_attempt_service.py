"""
MI Attempt Service

Service for managing MI practice attempts including starting attempts,
processing choices, and managing attempt state.

Optimized for high concurrency with:
- Dialogue structure caching (avoid refetching on every choice)
- Efficient database updates
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from supabase import Client

from src.models.mi_models import (
    MIPracticeAttempt,
    MIPracticeModule,
    ChoiceMade,
    FinalScores,
    CompletionStatus,
    StartAttemptResponse,
    MakeChoiceResponse,
)
from src.services.cache_service import get_cache_service, CacheService

logger = logging.getLogger(__name__)


class MIAttemptService:
    """
    Service for MI Practice Attempt operations.

    Handles:
    - Starting new attempts
    - Processing choices
    - Managing attempt state (rapport, resistance, tone spectrum)
    - Completing attempts

    Performance optimizations:
    - Dialogue structure cached on first access (1hr TTL)
    - Avoids redundant module fetches on each choice
    """

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.cache = get_cache_service()
        logger.info("MIAttemptService initialized with caching")
    
    # ============================================
    # ATTEMPT LIFECYCLE
    # ============================================
    
    async def start_attempt(
        self,
        module_id: str,
        user_id: str
    ) -> Optional[StartAttemptResponse]:
        """
        Start a new practice attempt for a module.
        
        Args:
            module_id: The module UUID
            user_id: The user starting the attempt
            
        Returns:
            StartAttemptResponse with initial state or None if module not found
        """
        try:
            # Get module details
            module_result = self.supabase.table('mi_practice_modules').select('*').eq('id', module_id).execute()
            
            if not module_result.data:
                logger.warning(f"Module not found: {module_id}")
                return None
            
            module_data = module_result.data[0]
            
            # Get starting node
            dialogue_structure = module_data.get('dialogue_structure', {})
            start_node_id = dialogue_structure.get('start_node_id')
            nodes = dialogue_structure.get('nodes', {})
            
            if not start_node_id or start_node_id not in nodes:
                logger.error(f"Invalid dialogue structure for module: {module_id}")
                return None
            
            # Get persona starting tone position
            persona_config = module_data.get('persona_config', {})
            starting_tone = persona_config.get('starting_tone_position', 0.2)
            
            # Create attempt record
            attempt_data = {
                'id': str(uuid4()),
                'user_id': user_id,
                'module_id': module_id,
                'current_node_id': start_node_id,
                'path_taken': [start_node_id],
                'current_rapport_score': 0,
                'current_resistance_level': 5,  # Start at middle resistance
                'tone_spectrum_position': starting_tone,
                'choices_made': [],
                'completion_status': None,
            }
            
            result = self.supabase.table('mi_practice_attempts').insert(attempt_data).execute()
            
            if not result.data:
                logger.error(f"Failed to create attempt for module: {module_id}")
                return None
            
            attempt_record = result.data[0]
            start_node = nodes[start_node_id]
            
            # Build choice points for response
            choice_points = []
            for cp in start_node.get('choice_points', []):
                choice_points.append({
                    'id': cp['id'],
                    'option_text': cp['option_text'],
                    'preview_hint': cp.get('preview_hint'),
                })
            
            logger.info(f"Started attempt {attempt_record['id']} for user {user_id} on module {module_data['code']}")
            
            return StartAttemptResponse(
                attempt_id=str(attempt_record['id']),
                module_id=module_id,
                module_code=module_data['code'],
                module_title=module_data['title'],
                current_state={
                    'node_id': start_node_id,
                    'persona_text': start_node.get('persona_text', ''),
                    'persona_mood': start_node.get('persona_mood', 'neutral'),
                    'themes': start_node.get('themes', []),
                    'rapport_score': 0,
                    'resistance_level': 5,
                    'tone_position': starting_tone,
                },
                choice_points=choice_points,
                learning_objective=module_data['learning_objective'],
            )
            
        except Exception as e:
            logger.error(f"Error starting attempt: {e}")
            raise
    
    async def get_attempt(self, attempt_id: str) -> Optional[MIPracticeAttempt]:
        """
        Get attempt by ID.
        
        Args:
            attempt_id: The attempt UUID
            
        Returns:
            MIPracticeAttempt or None if not found
        """
        try:
            result = self.supabase.table('mi_practice_attempts').select('*').eq('id', attempt_id).execute()
            
            if not result.data:
                return None
            
            attempt_data = result.data[0]
            
            return MIPracticeAttempt(
                id=str(attempt_data['id']),
                user_id=str(attempt_data['user_id']),
                module_id=str(attempt_data['module_id']),
                started_at=attempt_data['started_at'],
                completed_at=attempt_data.get('completed_at'),
                current_node_id=attempt_data.get('current_node_id'),
                path_taken=attempt_data.get('path_taken', []),
                current_rapport_score=attempt_data.get('current_rapport_score', 0),
                current_resistance_level=attempt_data.get('current_resistance_level', 5),
                tone_spectrum_position=attempt_data.get('tone_spectrum_position', 0.0),
                choices_made=attempt_data.get('choices_made', []),
                completion_status=attempt_data.get('completion_status'),
                final_scores=attempt_data.get('final_scores'),
                insights_generated=attempt_data.get('insights_generated', []),
                created_at=attempt_data.get('created_at'),
                updated_at=attempt_data.get('updated_at'),
            )
            
        except Exception as e:
            logger.error(f"Error getting attempt {attempt_id}: {e}")
            raise
    
    async def _get_cached_dialogue_structure(self, module_id: str) -> Optional[Dict[str, Any]]:
        """
        Get dialogue structure with caching.

        OPTIMIZED: Caches dialogue structure (50-100KB) to avoid
        redundant fetches on every choice (could be 30+ per conversation).

        Args:
            module_id: Module UUID

        Returns:
            Dialogue structure dict or None if not found
        """
        # Try cache first
        cached = await self.cache.get_dialogue_structure(module_id)
        if cached is not None:
            logger.debug(f"Cache HIT for dialogue structure module={module_id}")
            return cached

        # Fetch from database - only get dialogue_structure column
        result = self.supabase.table('mi_practice_modules').select(
            'dialogue_structure'
        ).eq('id', module_id).execute()

        if not result.data:
            return None

        dialogue_structure = result.data[0].get('dialogue_structure', {})

        # Cache for future calls
        await self.cache.set_dialogue_structure(module_id, dialogue_structure)
        logger.debug(f"Cached dialogue structure for module={module_id}")

        return dialogue_structure

    async def make_choice(
        self,
        attempt_id: str,
        choice_point_id: str
    ) -> Optional[MakeChoiceResponse]:
        """
        Process a choice in an active attempt.

        OPTIMIZED: Uses cached dialogue structure instead of
        fetching entire module on every choice.

        Args:
            attempt_id: The attempt UUID
            choice_point_id: The ID of the chosen option

        Returns:
            MakeChoiceResponse with updated state or None if invalid
        """
        try:
            # Get attempt
            attempt = await self.get_attempt(attempt_id)
            if not attempt:
                logger.warning(f"Attempt not found: {attempt_id}")
                return None

            if attempt.completion_status:
                logger.warning(f"Attempt already completed: {attempt_id}")
                return None

            # OPTIMIZED: Get cached dialogue structure instead of full module
            dialogue_structure = await self._get_cached_dialogue_structure(attempt.module_id)
            if not dialogue_structure:
                logger.error(f"Dialogue structure not found for module: {attempt.module_id}")
                return None

            nodes = dialogue_structure.get('nodes', {})
            
            # Get current node
            current_node_id = attempt.current_node_id
            if not current_node_id or current_node_id not in nodes:
                logger.error(f"Invalid current node for attempt: {attempt_id}")
                return None
            
            current_node = nodes[current_node_id]
            
            # Find the chosen choice point
            choice_point = None
            for cp in current_node.get('choice_points', []):
                if cp['id'] == choice_point_id:
                    choice_point = cp
                    break
            
            if not choice_point:
                logger.warning(f"Choice point not found: {choice_point_id}")
                return None
            
            # Calculate new state
            new_rapport = max(-10, min(10, 
                attempt.current_rapport_score + choice_point.get('rapport_impact', 0)
            ))
            new_resistance = max(1, min(10,
                attempt.current_resistance_level + choice_point.get('resistance_impact', 0)
            ))
            new_tone = max(0.0, min(1.0,
                attempt.tone_spectrum_position + choice_point.get('tone_shift', 0.0)
            ))
            
            # Record the choice
            choice_record = {
                'node_id': current_node_id,
                'choice_point_id': choice_point_id,
                'chosen_at': datetime.utcnow().isoformat(),
                'rapport_impact': choice_point.get('rapport_impact', 0),
                'resistance_impact': choice_point.get('resistance_impact', 0),
                'tone_shift': choice_point.get('tone_shift', 0.0),
                'techniques_used': choice_point.get('technique_tags', []),
                'competencies_demonstrated': choice_point.get('competency_links', []),
            }
            
            choices_made = attempt.choices_made + [choice_record]
            
            # Get next node
            next_node_id = choice_point.get('next_node_id')
            if not next_node_id or next_node_id not in nodes:
                logger.error(f"Invalid next node: {next_node_id}")
                return None
            
            next_node = nodes[next_node_id]
            
            # Check if this is an endpoint
            is_complete = next_node.get('is_endpoint', False)
            
            # Update attempt
            update_data = {
                'current_node_id': next_node_id,
                'path_taken': attempt.path_taken + [next_node_id],
                'current_rapport_score': new_rapport,
                'current_resistance_level': new_resistance,
                'tone_spectrum_position': new_tone,
                'choices_made': choices_made,
                'updated_at': datetime.utcnow().isoformat(),
            }
            
            if is_complete:
                update_data['completion_status'] = 'completed'
                update_data['completed_at'] = datetime.utcnow().isoformat()
            
            self.supabase.table('mi_practice_attempts').update(update_data).eq('id', attempt_id).execute()
            
            # Build response
            feedback = choice_point.get('feedback', {})
            next_choice_points = []
            
            if not is_complete:
                for cp in next_node.get('choice_points', []):
                    next_choice_points.append({
                        'id': cp['id'],
                        'option_text': cp['option_text'],
                        'preview_hint': cp.get('preview_hint'),
                    })
            
            logger.info(f"Processed choice {choice_point_id} for attempt {attempt_id}")
            
            return MakeChoiceResponse(
                attempt_id=attempt_id,
                turn_number=len(choices_made),
                choice_made={
                    'choice_point_id': choice_point_id,
                    'option_text': choice_point.get('option_text', ''),
                    'techniques_used': choice_point.get('technique_tags', []),
                },
                feedback={
                    'immediate': feedback.get('immediate', ''),
                    'learning_note': feedback.get('learning_note', ''),
                },
                new_state={
                    'node_id': next_node_id,
                    'persona_text': next_node.get('persona_text', ''),
                    'persona_mood': next_node.get('persona_mood', 'neutral'),
                    'themes': next_node.get('themes', []),
                    'rapport_score': new_rapport,
                    'resistance_level': new_resistance,
                    'tone_position': new_tone,
                },
                next_choice_points=next_choice_points,
                is_complete=is_complete,
            )
            
        except Exception as e:
            logger.error(f"Error making choice: {e}")
            raise
    
    async def complete_attempt(
        self,
        attempt_id: str,
        final_scores: Optional[FinalScores] = None
    ) -> Optional[MIPracticeAttempt]:
        """
        Complete a practice attempt.
        
        Args:
            attempt_id: The attempt UUID
            final_scores: Optional pre-calculated final scores
            
        Returns:
            Updated MIPracticeAttempt or None if not found
        """
        try:
            attempt = await self.get_attempt(attempt_id)
            if not attempt:
                return None
            
            if attempt.completion_status:
                logger.warning(f"Attempt already completed: {attempt_id}")
                return attempt
            
            # Calculate final scores if not provided
            if not final_scores:
                final_scores = await self._calculate_final_scores(attempt)
            
            # Generate insights
            insights = await self._generate_insights(attempt, final_scores)
            
            # Update attempt
            update_data = {
                'completion_status': 'completed',
                'completed_at': datetime.utcnow().isoformat(),
                'final_scores': final_scores.model_dump() if final_scores else None,
                'insights_generated': insights,
                'updated_at': datetime.utcnow().isoformat(),
            }
            
            result = self.supabase.table('mi_practice_attempts').update(update_data).eq('id', attempt_id).execute()
            
            if result.data:
                logger.info(f"Completed attempt {attempt_id}")
                return await self.get_attempt(attempt_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error completing attempt: {e}")
            raise
    
    async def abandon_attempt(self, attempt_id: str) -> bool:
        """
        Mark an attempt as abandoned.
        
        Args:
            attempt_id: The attempt UUID
            
        Returns:
            True if successful
        """
        try:
            update_data = {
                'completion_status': 'abandoned',
                'completed_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
            }
            
            result = self.supabase.table('mi_practice_attempts').update(update_data).eq('id', attempt_id).execute()
            
            if result.data:
                logger.info(f"Abandoned attempt {attempt_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error abandoning attempt: {e}")
            raise
    
    # ============================================
    # SCORING & INSIGHTS
    # ============================================
    
    async def _calculate_final_scores(self, attempt: MIPracticeAttempt) -> FinalScores:
        """
        Calculate final scores for a completed attempt.
        
        Uses the choices made to calculate:
        - Overall score (1-10)
        - Competency scores
        - Technique counts
        - Resistance triggered count
        - Rapport built status
        """
        choices = attempt.choices_made
        
        if not choices:
            return FinalScores(
                overall_score=5.0,
                competency_scores={},
                technique_counts={},
                resistance_triggered=0,
                rapport_built=False,
                final_tone_position=attempt.tone_spectrum_position,
            )
        
        # Count techniques
        technique_counts = {}
        for choice in choices:
            for technique in choice.get('techniques_used', []):
                technique_counts[technique] = technique_counts.get(technique, 0) + 1
        
        # Calculate competency scores
        competency_scores = {}
        competency_totals = {}
        
        for choice in choices:
            for competency in choice.get('competencies_demonstrated', []):
                if competency not in competency_totals:
                    competency_totals[competency] = {'count': 0, 'score': 0}
                competency_totals[competency]['count'] += 1
                # Score based on rapport impact
                competency_totals[competency]['score'] += max(0, choice.get('rapport_impact', 0))
        
        for comp, data in competency_totals.items():
            # Normalize to 1-10 scale
            competency_scores[comp] = min(10.0, 5.0 + (data['score'] * 0.5))
        
        # Calculate overall score
        # Based on: final rapport score, resistance level, tone position, technique variety
        rapport_factor = (attempt.current_rapport_score + 10) / 20  # Normalize to 0-1
        resistance_factor = 1 - ((attempt.current_resistance_level - 1) / 9)  # Lower is better
        tone_factor = attempt.tone_spectrum_position
        technique_factor = min(1.0, len(technique_counts) / 3)  # Variety bonus
        
        overall_score = (
            (rapport_factor * 2.5) +
            (resistance_factor * 2.5) +
            (tone_factor * 2.5) +
            (technique_factor * 2.5)
        )
        
        # Count resistance triggers (negative rapport impacts)
        resistance_triggered = sum(
            1 for c in choices if c.get('rapport_impact', 0) < 0
        )
        
        return FinalScores(
            overall_score=round(overall_score, 1),
            competency_scores=competency_scores,
            technique_counts=technique_counts,
            resistance_triggered=resistance_triggered,
            rapport_built=attempt.current_rapport_score > 0,
            final_tone_position=attempt.tone_spectrum_position,
        )
    
    async def _generate_insights(
        self,
        attempt: MIPracticeAttempt,
        scores: FinalScores
    ) -> List[Dict[str, Any]]:
        """
        Generate learning insights from an attempt.
        
        Analyzes choices and scores to generate personalized insights.
        """
        insights = []
        choices = attempt.choices_made
        
        if not choices:
            return insights
        
        # Analyze technique usage
        technique_counts = scores.technique_counts
        
        if 'simple_reflection' in technique_counts:
            count = technique_counts['simple_reflection']
            if count >= 3:
                insights.append({
                    'type': 'strength',
                    'title': 'Strong Reflection Skills',
                    'description': f'You used {count} reflections effectively to build rapport.',
                    'competency': '2.1.1',
                })
        
        if 'righting_reflex' in technique_counts:
            insights.append({
                'type': 'improvement',
                'title': 'Watch for the Righting Reflex',
                'description': 'You showed a tendency to educate or fix. Try reflecting more before offering solutions.',
                'competency': '4.1.1',
            })
        
        # Analyze rapport building
        if scores.rapport_built:
            insights.append({
                'type': 'strength',
                'title': 'Rapport Building',
                'description': 'You successfully built rapport with the patient.',
                'competency': 'A6',
            })
        
        # Analyze resistance management
        if scores.resistance_triggered > 2:
            insights.append({
                'type': 'improvement',
                'title': 'Managing Resistance',
                'description': f'Resistance was triggered {scores.resistance_triggered} times. Focus on rolling with resistance rather than confronting it.',
                'competency': '4.1.1',
            })
        
        # Tone progression
        if scores.final_tone_position > 0.6:
            insights.append({
                'type': 'strength',
                'title': 'Positive Engagement',
                'description': 'You successfully helped the patient become more open and engaged.',
                'competency': 'B6',
            })
        
        return insights
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    async def get_user_attempts(
        self,
        user_id: str,
        module_id: Optional[str] = None,
        limit: int = 20
    ) -> List[MIPracticeAttempt]:
        """
        Get attempts for a user.
        
        Args:
            user_id: The user UUID
            module_id: Optional module filter
            limit: Maximum attempts to return
            
        Returns:
            List of attempts
        """
        try:
            query = self.supabase.table('mi_practice_attempts').select('*').eq('user_id', user_id)
            
            if module_id:
                query = query.eq('module_id', module_id)
            
            result = query.order('started_at', desc=True).limit(limit).execute()
            
            attempts = []
            for attempt_data in result.data:
                attempts.append(MIPracticeAttempt(
                    id=str(attempt_data['id']),
                    user_id=str(attempt_data['user_id']),
                    module_id=str(attempt_data['module_id']),
                    started_at=attempt_data['started_at'],
                    completed_at=attempt_data.get('completed_at'),
                    current_node_id=attempt_data.get('current_node_id'),
                    path_taken=attempt_data.get('path_taken', []),
                    current_rapport_score=attempt_data.get('current_rapport_score', 0),
                    current_resistance_level=attempt_data.get('current_resistance_level', 5),
                    tone_spectrum_position=attempt_data.get('tone_spectrum_position', 0.0),
                    choices_made=attempt_data.get('choices_made', []),
                    completion_status=attempt_data.get('completion_status'),
                    final_scores=attempt_data.get('final_scores'),
                    insights_generated=attempt_data.get('insights_generated', []),
                    created_at=attempt_data.get('created_at'),
                    updated_at=attempt_data.get('updated_at'),
                ))
            
            return attempts
            
        except Exception as e:
            logger.error(f"Error getting user attempts: {e}")
            raise
    
    async def get_attempt_state(self, attempt_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of an attempt.
        
        Returns current node, available choices, and state metrics.
        """
        try:
            attempt = await self.get_attempt(attempt_id)
            if not attempt:
                return None
            
            # Get module for dialogue structure
            module_result = self.supabase.table('mi_practice_modules').select('*').eq('id', attempt.module_id).execute()
            if not module_result.data:
                return None
            
            module_data = module_result.data[0]
            dialogue_structure = module_data.get('dialogue_structure', {})
            nodes = dialogue_structure.get('nodes', {})
            
            current_node_id = attempt.current_node_id
            if not current_node_id or current_node_id not in nodes:
                return None
            
            current_node = nodes[current_node_id]
            
            # Build choice points
            choice_points = []
            for cp in current_node.get('choice_points', []):
                choice_points.append({
                    'id': cp['id'],
                    'option_text': cp['option_text'],
                    'preview_hint': cp.get('preview_hint'),
                })
            
            return {
                'attempt_id': attempt_id,
                'current_node': {
                    'id': current_node_id,
                    'persona_text': current_node.get('persona_text', ''),
                    'persona_mood': current_node.get('persona_mood', ''),
                    'themes': current_node.get('themes', []),
                    'is_endpoint': current_node.get('is_endpoint', False),
                },
                'choice_points': choice_points,
                'state': {
                    'rapport_score': attempt.current_rapport_score,
                    'resistance_level': attempt.current_resistance_level,
                    'tone_position': attempt.tone_spectrum_position,
                    'turns_taken': len(attempt.choices_made),
                },
            }
            
        except Exception as e:
            logger.error(f"Error getting attempt state: {e}")
            raise
