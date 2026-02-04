"""
MI Practice Module API Routes
Endpoints for Motivational Interviewing practice modules

NOTE: Auth removed - all endpoints are public
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.dependencies import (
    get_supabase_client,
    get_mi_module_service,
    get_mi_attempt_service,
    get_mi_progress_service,
)
from src.models.mi_models import (
    MIPracticeModule,
    MIPracticeModuleSummary,
    MIPracticeAttempt,
    MILearningPath,
    MILearningPathSummary,
    MIUserProgress,
    ContentType,
    StartAttemptRequest,
    StartAttemptResponse,
    MakeChoiceRequest,
    MakeChoiceResponse,
    AttemptReviewResponse,
    UserProgressResponse,
    EnrollPathRequest,
    EnrollPathResponse,
)
from src.services.mi_module_service import MIModuleService
from src.services.mi_attempt_service import MIAttemptService
from src.services.mi_progress_service import MIProgressService
from src.services.mi_scoring_service import MIScoringService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mi-practice", tags=["mi-practice"])

# Default user ID for all requests (using existing gstanyard@gmail.com user)
# TODO: Replace with proper authentication when ready
GSTANYARD_USER_ID = "a126e8ec-00ff-4914-8fd2-eb6e2864d3f0"


def _normalize_user_id(user_id: Optional[str]) -> str:
    """
    Normalize user_id by converting "anonymous" string to actual user UUID.

    The frontend may send "anonymous" but the database requires a valid UUID.
    Uses the gstanyard user as the default user for now.
    """
    if not user_id or user_id == "anonymous":
        return GSTANYARD_USER_ID
    return user_id


# ============================================
# MODULE MANAGEMENT ENDPOINTS
# ============================================

@router.get("/modules", response_model=List[MIPracticeModuleSummary])
async def list_modules(
    content_type: Optional[ContentType] = Query(None, description="Filter by content type: shared, customer_facing, or colleague_facing"),
    focus_area: Optional[str] = Query(None, description="Filter by MI focus area"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    user_id: Optional[str] = Query(None, description="User ID for progress tracking"),
    module_service: MIModuleService = Depends(get_mi_module_service),
):
    """
    List available MI practice modules.
    """
    logger.info(f"Listing MI practice modules - content_type: {content_type}, focus_area: {focus_area}, difficulty: {difficulty}")

    try:
        modules = await module_service.list_modules(
            content_type=content_type,
            focus_area=focus_area,
            difficulty=difficulty,
            user_id=user_id,
        )
        return modules
    except Exception as e:
        logger.error(f"Error listing modules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list modules: {str(e)}")


@router.get("/modules/{module_id}", response_model=MIPracticeModule)
async def get_module(
    module_id: str,
    user_id: Optional[str] = Query(None, description="User ID for attempt history"),
    module_service: MIModuleService = Depends(get_mi_module_service),
):
    """
    Get detailed information about a specific MI practice module.
    """
    logger.info(f"Getting module details for: {module_id}")

    try:
        module = await module_service.get_module(module_id, user_id)
        if not module:
            raise HTTPException(status_code=404, detail=f"Module not found: {module_id}")
        return module
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting module {module_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get module: {str(e)}")


@router.post("/modules/{module_id}/start", response_model=StartAttemptResponse)
async def start_attempt(
    module_id: str,
    request: StartAttemptRequest,
    attempt_service: MIAttemptService = Depends(get_mi_attempt_service),
):
    """
    Start a new practice attempt for a module.
    """
    logger.info(f"Starting attempt for module: {module_id}")

    try:
        # Normalize user_id - convert "anonymous" to actual user UUID
        user_id = _normalize_user_id(request.user_id)
        logger.debug(f"Normalized user_id: {user_id}")

        response = await attempt_service.start_attempt(module_id, user_id)
        if not response:
            raise HTTPException(status_code=404, detail=f"Module not found or could not start attempt: {module_id}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting attempt for module {module_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start attempt: {str(e)}")


# ============================================
# PRACTICE SESSION ENDPOINTS
# ============================================

@router.post("/attempts/{attempt_id}/choose", response_model=MakeChoiceResponse)
async def make_choice(
    attempt_id: str,
    request: MakeChoiceRequest,
    attempt_service: MIAttemptService = Depends(get_mi_attempt_service),
):
    """
    Make a choice in an active practice attempt.
    """
    logger.info(f"Processing choice for attempt: {attempt_id}, choice: {request.choice_point_id}")

    try:
        response = await attempt_service.make_choice(attempt_id, request.choice_point_id)
        if not response:
            raise HTTPException(status_code=404, detail=f"Attempt not found or invalid choice: {attempt_id}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making choice for attempt {attempt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process choice: {str(e)}")


@router.get("/attempts/{attempt_id}/state")
async def get_attempt_state(
    attempt_id: str,
    attempt_service: MIAttemptService = Depends(get_mi_attempt_service),
):
    """
    Get the current state of an active attempt.
    """
    logger.info(f"Getting state for attempt: {attempt_id}")

    try:
        state = await attempt_service.get_attempt_state(attempt_id)
        if not state:
            raise HTTPException(status_code=404, detail=f"Attempt not found: {attempt_id}")
        return state
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting attempt state for {attempt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get attempt state: {str(e)}")


@router.post("/attempts/{attempt_id}/complete")
async def complete_attempt(
    attempt_id: str,
    attempt_service: MIAttemptService = Depends(get_mi_attempt_service),
    progress_service: MIProgressService = Depends(get_mi_progress_service),
):
    """
    Complete a practice attempt.
    """
    logger.info(f"Completing attempt: {attempt_id}")

    try:
        # Complete the attempt
        attempt = await attempt_service.complete_attempt(attempt_id)
        if not attempt:
            raise HTTPException(status_code=404, detail=f"Attempt not found: {attempt_id}")

        # Update user progress
        await progress_service.update_progress_after_attempt(attempt)

        return {
            "success": True,
            "attempt_id": attempt_id,
            "completion_status": attempt.completion_status,
            "final_scores": attempt.final_scores.model_dump() if attempt.final_scores else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing attempt {attempt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete attempt: {str(e)}")


# ============================================
# PROGRESS & ANALYTICS ENDPOINTS
# ============================================

@router.get("/progress", response_model=UserProgressResponse)
async def get_user_progress(
    user_id: Optional[str] = Query(None, description="User ID to get progress for"),
    progress_service: MIProgressService = Depends(get_mi_progress_service),
):
    """
    Get overall MI practice progress for a user.
    """
    # Use default anonymous user_id since app is public
    user_id = user_id if user_id else GSTANYARD_USER_ID
    logger.info(f"Getting progress for user: {user_id}")

    try:
        progress = await progress_service.get_progress_response(user_id)
        if not progress:
            raise HTTPException(status_code=404, detail=f"Progress not found for user: {user_id}")
        return progress
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


@router.get("/progress/competencies")
async def get_competency_breakdown(
    user_id: Optional[str] = Query(None, description="User ID to get competencies for"),
    progress_service: MIProgressService = Depends(get_mi_progress_service),
):
    """
    Get detailed competency breakdown for a user.
    """
    # Use default anonymous user_id since app is public
    user_id = user_id if user_id else GSTANYARD_USER_ID
    logger.info(f"Getting competency breakdown for user: {user_id}")

    try:
        breakdown = await progress_service.get_competency_breakdown(user_id)
        return breakdown
    except Exception as e:
        logger.error(f"Error getting competency breakdown for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get competency breakdown: {str(e)}")


@router.get("/attempts/{attempt_id}/review")
async def review_attempt(
    attempt_id: str,
    attempt_service: MIAttemptService = Depends(get_mi_attempt_service),
):
    """
    Review a completed practice attempt.
    """
    logger.info(f"Reviewing attempt: {attempt_id}")

    try:
        attempt = await attempt_service.get_attempt(attempt_id)
        if not attempt:
            raise HTTPException(status_code=404, detail=f"Attempt not found: {attempt_id}")

        # Get module info
        from src.dependencies import get_mi_module_service
        module_service = get_mi_module_service()
        module = await module_service.get_module(attempt.module_id)

        # Build path review from choices
        path_review = []
        for choice in attempt.choices_made:
            # Handle both ChoiceMade objects and dicts
            if hasattr(choice, 'node_id'):
                # ChoiceMade object
                path_review.append({
                    'node_id': choice.node_id,
                    'choice_point_id': choice.choice_point_id,
                    'techniques_used': choice.techniques_used,
                    'rapport_impact': choice.rapport_impact,
                    'resistance_impact': choice.resistance_impact,
                })
            else:
                # Dict format
                path_review.append({
                    'node_id': choice.get('node_id'),
                    'choice_point_id': choice.get('choice_point_id'),
                    'techniques_used': choice.get('techniques_used', []),
                    'rapport_impact': choice.get('rapport_impact', 0),
                    'resistance_impact': choice.get('resistance_impact', 0),
                })

        return {
            "attempt_id": attempt_id,
            "module": {
                "id": attempt.module_id,
                "code": module.code if module else "unknown",
                "title": module.title if module else "Unknown Module",
            },
            "completed_at": attempt.completed_at,
            "completion_status": attempt.completion_status,
            "turns_taken": len(attempt.choices_made),
            "final_scores": attempt.final_scores.model_dump() if attempt.final_scores else None,
            "path_review": path_review,
            "key_moments": attempt.insights_generated,
            "learning_notes": [
                insight.get('description', '')
                for insight in attempt.insights_generated
            ] if attempt.insights_generated else [],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing attempt {attempt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to review attempt: {str(e)}")


@router.get("/insights")
async def get_learning_insights(
    user_id: Optional[str] = Query(None, description="User ID to get insights for"),
    limit: int = Query(5, ge=1, le=20, description="Number of insights to return"),
    progress_service: MIProgressService = Depends(get_mi_progress_service),
):
    """
    Get personalized learning insights for a user.
    """
    # Use default anonymous user_id since app is public
    user_id = user_id if user_id else GSTANYARD_USER_ID
    logger.info(f"Getting insights for user: {user_id}")

    try:
        insights = await progress_service.generate_learning_insights(user_id, limit)
        return {"insights": insights}
    except Exception as e:
        logger.error(f"Error getting insights for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")


# ============================================
# LEARNING PATH ENDPOINTS
# ============================================

@router.get("/learning-paths", response_model=List[MILearningPathSummary])
async def list_learning_paths(
    user_id: Optional[str] = Query(None, description="User ID for enrollment status"),
    module_service: MIModuleService = Depends(get_mi_module_service),
):
    """
    List available MI learning paths.
    """
    logger.info("Listing learning paths")

    try:
        paths = await module_service.list_learning_paths(user_id=user_id)
        return paths
    except Exception as e:
        logger.error(f"Error listing learning paths: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list learning paths: {str(e)}")


@router.post("/learning-paths/{path_id}/enroll", response_model=EnrollPathResponse)
async def enroll_in_path(
    path_id: str,
    request: EnrollPathRequest = None,  # Optional for backward compatibility
    progress_service: MIProgressService = Depends(get_mi_progress_service),
    module_service: MIModuleService = Depends(get_mi_module_service),
):
    """
    Enroll a user in a learning path.
    """
    logger.info(f"Enrolling in path: {path_id}")

    try:
        # Use gstanyard user_id since app is currently public
        user_id = GSTANYARD_USER_ID
        logger.info(f"DEBUG: Using gstanyard user_id: {user_id}")
        logger.info(f"DEBUG: request = {request}")

        # Enroll user
        success = await progress_service.enroll_in_path(user_id, path_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to enroll in path: {path_id}")

        # Get path details
        path = await module_service.get_learning_path(path_id)
        if not path:
            raise HTTPException(status_code=404, detail=f"Learning path not found: {path_id}")

        # Get first module
        current_module_id = path.module_sequence[0] if path.module_sequence else None

        return EnrollPathResponse(
            success=True,
            path_id=path_id,
            path_title=path.title,
            current_module_id=current_module_id or "",
            message=f"Successfully enrolled in {path.title}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enrolling in path {path_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enroll in path: {str(e)}")


@router.get("/learning-paths/active")
async def get_active_path_progress(
    user_id: Optional[str] = Query(None, description="User ID to get active path for"),
    progress_service: MIProgressService = Depends(get_mi_progress_service),
):
    """
    Get progress in the currently active learning path.
    """
    # Use default anonymous user_id since app is public
    user_id = user_id if user_id else GSTANYARD_USER_ID
    logger.info(f"Getting active path progress for user: {user_id}")

    try:
        progress = await progress_service.get_active_path_progress(user_id)
        if not progress:
            return {"is_enrolled": False, "message": "No active learning path"}
        return progress
    except Exception as e:
        logger.error(f"Error getting active path progress for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active path: {str(e)}")


# ============================================
# DISCOVERY & RECOMMENDATION ENDPOINTS
# ============================================

@router.get("/focus-areas")
async def get_focus_areas(
    module_service: MIModuleService = Depends(get_mi_module_service),
):
    """
    Get list of available focus areas with module counts.
    """
    try:
        focus_areas = await module_service.get_focus_areas()
        return {"focus_areas": focus_areas}
    except Exception as e:
        logger.error(f"Error getting focus areas: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get focus areas: {str(e)}")


@router.get("/difficulty-levels")
async def get_difficulty_levels(
    module_service: MIModuleService = Depends(get_mi_module_service),
):
    """
    Get list of difficulty levels with module counts.
    """
    try:
        levels = await module_service.get_difficulty_levels()
        return {"difficulty_levels": levels}
    except Exception as e:
        logger.error(f"Error getting difficulty levels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get difficulty levels: {str(e)}")


@router.get("/content-types")
async def get_content_types(
    module_service: MIModuleService = Depends(get_mi_module_service),
):
    """
    Get list of content types with module counts.
    """
    try:
        content_types = await module_service.get_content_types()
        return {"content_types": content_types}
    except Exception as e:
        logger.error(f"Error getting content types: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get content types: {str(e)}")


@router.get("/recommendations")
async def get_recommended_modules(
    user_id: Optional[str] = Query(None, description="User ID to get recommendations for"),
    limit: int = Query(5, ge=1, le=10, description="Number of recommendations"),
    module_service: MIModuleService = Depends(get_mi_module_service),
):
    """
    Get module recommendations for a user based on their progress.
    """
    # Use default anonymous user_id since app is public
    user_id = user_id if user_id else GSTANYARD_USER_ID
    try:
        recommendations = await module_service.get_recommended_modules(user_id, limit)
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Error getting recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


# ============================================
# ADMIN/UTILITY ENDPOINTS
# ============================================

@router.get("/health")
async def mi_practice_health_check(
    module_service: MIModuleService = Depends(get_mi_module_service),
):
    """
    Health check for MI practice module system.
    """
    logger.info("MI practice health check")

    try:
        # Try to get module count
        from src.dependencies import get_supabase_client
        supabase = get_supabase_client()
        result = supabase.table('mi_practice_modules').select('id', count='exact').eq('is_active', True).execute()
        module_count = result.count if hasattr(result, 'count') else 0

        return {
            "status": "healthy",
            "module_count": module_count,
            "service": "mi-practice",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "mi-practice",
            "timestamp": datetime.utcnow().isoformat(),
        }
