"""
Feedback API routes for user feedback collection
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from src.dependencies import get_supabase_client
from src.auth.auth_dependencies import AuthenticatedUser, get_current_user
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

class FeedbackSubmission(BaseModel):
    """User feedback submission model"""
    session_id: str
    conversation_id: Optional[str] = None
    persona_practiced: Optional[str] = None
    helpfulness_score: int = Field(..., ge=0, le=10, description="Rating from 0-10")
    what_was_helpful: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    user_email: Optional[str] = None

@router.post("/submit")
async def submit_feedback(
    feedback: FeedbackSubmission,
    current_user: AuthenticatedUser = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """
    Submit user feedback after practice session.
    
    Accessible by: Both FULL and CONTROL users
    Stores feedback in Supabase user_feedback table.
    """
    try:
        # Validate score
        if not 0 <= feedback.helpfulness_score <= 10:
            raise HTTPException(
                status_code=400,
                detail="Helpfulness score must be between 0 and 10"
            )
        
        # Prepare data for insertion
        feedback_data = {
            "id": str(uuid.uuid4()),
            "session_id": feedback.session_id,
            "conversation_id": feedback.conversation_id,
            "persona_practiced": feedback.persona_practiced,
            "helpfulness_score": feedback.helpfulness_score,
            "what_was_helpful": feedback.what_was_helpful,
            "improvement_suggestions": feedback.improvement_suggestions,
            "user_email": feedback.user_email,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {}
        }
        
        # Store in Supabase
        result = supabase.table('user_feedback').insert(feedback_data).execute()
        
        logger.info(f"Feedback submitted successfully: {feedback_data['id']}")
        
        return {
            "success": True,
            "feedback_id": feedback_data["id"],
            "message": "Thank you for your feedback!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit feedback: {str(e)}"
        )

@router.get("/stats")
async def get_feedback_stats(
    supabase = Depends(get_supabase_client)
):
    """
    Get aggregate feedback statistics.
    
    Returns average helpfulness score and total feedback count.
    """
    try:
        # Get all feedback
        result = supabase.table('user_feedback').select('*').execute()
        
        if not result.data:
            return {
                "total_feedback": 0,
                "average_score": 0,
                "score_distribution": {}
            }
        
        # Calculate stats
        scores = [f['helpfulness_score'] for f in result.data]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Score distribution
        distribution = {}
        for score in scores:
            distribution[score] = distribution.get(score, 0) + 1
        
        return {
            "total_feedback": len(result.data),
            "average_score": round(avg_score, 2),
            "score_distribution": distribution
        }
        
    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve feedback statistics: {str(e)}"
        )
