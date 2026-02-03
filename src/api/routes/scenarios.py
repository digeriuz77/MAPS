"""
Scenario Routes - API endpoints for scenario-based MI training

Provides endpoints for:
- Listing and browsing scenarios
- Starting scenario attempts
- Processing turns
- Getting analysis results

NOTE: Auth removed - using anonymous user for all requests
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from src.dependencies import get_supabase_client
from src.services.scenario_pipeline import get_scenario_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])

# Anonymous user ID for all requests
ANONYMOUS_USER_ID = "anonymous-user"


# ========== Request/Response Models ==========

class ScenarioListItem(BaseModel):
    """Lightweight scenario info for listing"""
    id: str
    code: str
    title: str
    mi_skill_category: str
    difficulty: str
    estimated_minutes: int
    learning_objective: str


class ScenarioDetail(BaseModel):
    """Full scenario details"""
    id: str
    code: str
    title: str
    mi_skill_category: str
    difficulty: str
    estimated_minutes: int
    situation: str
    learning_objective: str
    persona_config: Dict[str, Any]
    success_criteria: Dict[str, Any]


class StartScenarioRequest(BaseModel):
    """Request to start a scenario"""
    feedback_frequency: str = "key_moments"  # "always", "key_moments", "never"


class StartScenarioResponse(BaseModel):
    """Response when starting a scenario"""
    attempt_id: str
    scenario_id: str
    scenario_code: str
    scenario_title: str
    persona_name: str
    initial_message: str
    turn_count: int
    learning_objective: str


class ProcessTurnRequest(BaseModel):
    """Request to process a turn"""
    message: str = Field(..., min_length=1, max_length=1000)


class ProcessTurnResponse(BaseModel):
    """Response after processing a turn"""
    attempt_id: str
    persona_message: str
    persona_name: str
    persona_state: Dict[str, Any]
    realtime_feedback: Optional[str]
    analysis_summary: Dict[str, Any]
    turn_count: int
    is_complete: bool
    completion_reason: Optional[str]


class GetAnalysisResponse(BaseModel):
    """Full analysis after scenario completion"""
    attempt_id: str
    scenario_code: str
    scenario_title: str
    completed_at: Optional[str]
    total_turns: int
    success: bool
    completion_reason: str
    average_scores: Dict[str, float]
    strengths: List[str]
    opportunities: List[str]
    summary: str
    transcript: List[Dict[str, Any]]


# ========== Route Implementations ==========

@router.get("/", response_model=List[ScenarioListItem])
async def list_scenarios(
    skill_category: Optional[str] = Query(None, description="Filter by MI skill category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    show_inactive: bool = Query(False, description="Include inactive scenarios")
):
    """
    List available scenarios with optional filters.
    """
    try:
        supabase = get_supabase_client()

        # Build query
        query = supabase.table('scenarios').select(
            'id, code, title, mi_skill_category, difficulty, estimated_minutes, learning_objective, is_active'
        )

        if skill_category:
            query = query.eq('mi_skill_category', skill_category)

        if difficulty:
            query = query.eq('difficulty', difficulty)

        if not show_inactive:
            query = query.eq('is_active', True)

        result = query.order('mi_skill_category').order('difficulty').execute()

        if not result.data:
            return []

        scenarios = []
        for row in result.data:
            scenarios.append(ScenarioListItem(
                id=row['id'],
                code=row['code'],
                title=row['title'],
                mi_skill_category=row['mi_skill_category'],
                difficulty=row['difficulty'],
                estimated_minutes=row['estimated_minutes'],
                learning_objective=row['learning_objective']
            ))

        return scenarios

    except Exception as e:
        logger.error(f"Error listing scenarios: {e}")
        raise HTTPException(status_code=500, detail="Failed to list scenarios")


@router.get("/{scenario_id}", response_model=ScenarioDetail)
async def get_scenario(scenario_id: str):
    """
    Get full scenario details including persona configuration.
    """
    try:
        supabase = get_supabase_client()

        result = supabase.table('scenarios').select('*').eq('id', scenario_id).maybe_single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Scenario not found")

        scenario = result.data

        return ScenarioDetail(
            id=scenario['id'],
            code=scenario['code'],
            title=scenario['title'],
            mi_skill_category=scenario['mi_skill_category'],
            difficulty=scenario['difficulty'],
            estimated_minutes=scenario['estimated_minutes'],
            situation=scenario['situation'],
            learning_objective=scenario['learning_objective'],
            persona_config=scenario['persona_config'],
            success_criteria=scenario['success_criteria']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scenario: {e}")
        raise HTTPException(status_code=500, detail="Failed to get scenario")


@router.post("/{scenario_id}/start", response_model=StartScenarioResponse)
async def start_scenario(
    scenario_id: str,
    request: StartScenarioRequest = None
):
    """
    Start a new attempt at a scenario.
    """
    # Handle case where no body is provided
    if request is None:
        request = StartScenarioRequest()

    try:
        supabase = get_supabase_client()
        user_id = ANONYMOUS_USER_ID

        # Get scenario
        scenario_result = supabase.table('scenarios').select('*').eq('id', scenario_id).maybe_single().execute()

        if not scenario_result.data:
            raise HTTPException(status_code=404, detail="Scenario not found")

        scenario = scenario_result.data
        persona_config = scenario['persona_config']

        # Create attempt record
        attempt_data = {
            'user_id': user_id,
            'scenario_id': scenario_id,
            'turn_count': 0,
            'transcript': [],
            'initial_persona_state': persona_config.get('starting_state', {
                'trust_level': 4,
                'openness_level': 3,
                'resistance_active': True
            }),
            'current_persona_state': persona_config.get('starting_state', {
                'trust_level': 4,
                'openness_level': 3,
                'resistance_active': True
            }),
            'skills_demonstrated': [],
            'negative_behaviors': []
        }

        attempt_result = supabase.table('scenario_attempts').insert(attempt_data).execute()

        if not attempt_result.data:
            raise HTTPException(status_code=500, detail="Failed to create attempt")

        attempt = attempt_result.data[0]

        logger.info(f"Started scenario attempt: user={user_id}, scenario={scenario_id}, attempt={attempt['id']}")

        # Generate initial greeting from persona
        pipeline = get_scenario_pipeline()
        summary = pipeline.get_scenario_summary(scenario, attempt)

        return StartScenarioResponse(
            attempt_id=attempt['id'],
            scenario_id=scenario_id,
            scenario_code=scenario['code'],
            scenario_title=scenario['title'],
            persona_name=persona_config.get('name', 'Persona'),
            initial_message=f"Hi, thanks for meeting with me today. {persona_config.get('situation', '')}",
            turn_count=0,
            learning_objective=scenario['learning_objective']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting scenario: {e}")
        raise HTTPException(status_code=500, detail="Failed to start scenario")


@router.post("/attempts/{attempt_id}/turn", response_model=ProcessTurnResponse)
async def process_turn(
    attempt_id: str,
    request: ProcessTurnRequest
):
    """
    Process one turn in a scenario attempt.
    """
    try:
        supabase = get_supabase_client()

        # Get attempt
        attempt_result = supabase.table('scenario_attempts').select('*').eq('id', attempt_id).maybe_single().execute()

        if not attempt_result.data:
            raise HTTPException(status_code=404, detail="Attempt not found")

        attempt = attempt_result.data

        # Check if already complete
        if attempt.get('completed_at'):
            raise HTTPException(status_code=400, detail="Scenario already completed")

        # Get scenario
        scenario_result = supabase.table('scenarios').select('*').eq('id', attempt['scenario_id']).maybe_single().execute()

        if not scenario_result.data:
            raise HTTPException(status_code=404, detail="Scenario not found")

        scenario = scenario_result.data

        # Process turn through pipeline
        pipeline = get_scenario_pipeline()
        result = await pipeline.process_turn(scenario, attempt, request.message)

        # Update attempt in database
        updated_transcript = attempt.get('transcript', [])
        updated_transcript.append({
            'turn': result.turn_number,
            'manager_message': request.message,
            'persona_response': result.persona_message,
            'persona_state': result.persona_state,
            'analysis': result.analysis,
            'feedback': result.realtime_feedback,
            'timestamp': datetime.utcnow().isoformat()
        })

        update_data = {
            'turn_count': result.turn_number,
            'transcript': updated_transcript,
            'current_persona_state': result.persona_state,
            'skills_demonstrated': list(set(
                attempt.get('skills_demonstrated', []) +
                [t for t in result.analysis.get('mi_techniques_used', [])
                 if t in ['reflection', 'open_question', 'affirmation', 'summarization']]
            )),
            'negative_behaviors': list(set(
                attempt.get('negative_behaviors', []) +
                ([ 'unsolicited_advice'] if result.analysis.get('behaviors_detected', {}).get('unsolicited_advice') else []) +
                ([ 'fixing'] if result.analysis.get('behaviors_detected', {}).get('fix_mode') else [])
            ))
        }

        # If complete, mark completion
        if result.is_complete:
            update_data['completed_at'] = datetime.utcnow().isoformat()
            update_data['completion_reason'] = result.completion_reason
            update_data['final_persona_state'] = result.persona_state
            update_data['final_scores'] = result.analysis.get('maps_scores', {})

        supabase.table('scenario_attempts').update(update_data).eq('id', attempt_id).execute()

        logger.info(f"Processed turn {result.turn_number} for attempt {attempt_id}: complete={result.is_complete}")

        return ProcessTurnResponse(
            attempt_id=attempt_id,
            persona_message=result.persona_message,
            persona_name=scenario['persona_config'].get('name', 'Persona'),
            persona_state=result.persona_state,
            realtime_feedback=result.realtime_feedback,
            analysis_summary={
                'mi_techniques': result.analysis.get('mi_techniques_used', []),
                'maps_scores': result.analysis.get('maps_scores', {}),
                'state_trajectory': result.analysis.get('state_trajectory', 'stable')
            },
            turn_count=result.turn_number,
            is_complete=result.is_complete,
            completion_reason=result.completion_reason
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing turn: {e}")
        raise HTTPException(status_code=500, detail="Failed to process turn")


@router.get("/attempts/{attempt_id}/analysis", response_model=GetAnalysisResponse)
async def get_full_analysis(attempt_id: str):
    """
    Get complete analysis after scenario ends.
    """
    try:
        supabase = get_supabase_client()

        # Get attempt
        attempt_result = supabase.table('scenario_attempts').select('*').eq('id', attempt_id).maybe_single().execute()

        if not attempt_result.data:
            raise HTTPException(status_code=404, detail="Attempt not found")

        attempt = attempt_result.data

        # Get scenario
        scenario_result = supabase.table('scenarios').select('*').eq('id', attempt['scenario_id']).maybe_single().execute()

        if not scenario_result.data:
            raise HTTPException(status_code=404, detail="Scenario not found")

        scenario = scenario_result.data

        # Generate feedback summary
        pipeline = get_scenario_pipeline()
        feedback_gen = pipeline.feedback_gen

        analyses = [turn.get('analysis', {}) for turn in attempt.get('transcript', [])]

        if attempt.get('completed_at'):
            feedback = feedback_gen.generate_end_of_scenario_feedback(
                analyses,
                success=attempt.get('completion_reason') == 'Success criteria met',
                completion_reason=attempt.get('completion_reason', 'unknown')
            )
        else:
            feedback = {
                'success': False,
                'completion_reason': attempt.get('completion_reason', 'incomplete'),
                'average_scores': attempt.get('final_scores', {}),
                'strengths': [],
                'opportunities': [],
                'summary': 'Scenario not yet completed'
            }

        return GetAnalysisResponse(
            attempt_id=attempt_id,
            scenario_code=scenario['code'],
            scenario_title=scenario['title'],
            completed_at=attempt.get('completed_at'),
            total_turns=attempt['turn_count'],
            success=feedback['success'],
            completion_reason=feedback['completion_reason'],
            average_scores=feedback['average_scores'],
            strengths=feedback.get('strengths', []),
            opportunities=feedback.get('opportunities', []),
            summary=feedback['summary'],
            transcript=attempt.get('transcript', [])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis")


@router.post("/attempts/{attempt_id}/abandon")
async def abandon_scenario(attempt_id: str):
    """
    Mark a scenario attempt as abandoned.
    """
    try:
        supabase = get_supabase_client()

        # Get attempt
        attempt_result = supabase.table('scenario_attempts').select('*').eq('id', attempt_id).maybe_single().execute()

        if not attempt_result.data:
            raise HTTPException(status_code=404, detail="Attempt not found")

        attempt = attempt_result.data

        # Check if already complete
        if attempt.get('completed_at'):
            raise HTTPException(status_code=400, detail="Cannot abandon completed scenario")

        # Update attempt
        supabase.table('scenario_attempts').update({
            'completed_at': datetime.utcnow().isoformat(),
            'completion_reason': 'abandoned'
        }).eq('id', attempt_id).execute()

        logger.info(f"Abandoned scenario attempt: {attempt_id}")

        return {"message": "Scenario abandoned", "attempt_id": attempt_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error abandoning scenario: {e}")
        raise HTTPException(status_code=500, detail="Failed to abandon scenario")


@router.get("/skill-categories")
async def get_skill_categories():
    """
    Get list of available skill categories.
    """
    try:
        supabase = get_supabase_client()

        result = supabase.table('scenarios').select('mi_skill_category').execute()

        if not result.data:
            return []

        categories = list(set(row['mi_skill_category'] for row in result.data if row.get('mi_skill_category')))
        categories.sort()

        return categories

    except Exception as e:
        logger.error(f"Error getting skill categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get categories")
