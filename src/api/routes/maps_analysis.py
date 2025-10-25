"""
Direct MAPS analysis routes - bypassing the general analysis.py
Uses the updated MAPS service with OpenAI fallback
"""
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.dependencies import get_supabase_client
from src.services.analysis.maps_analysis_service import get_maps_analysis_service, create_standalone_maps_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/maps", tags=["maps_analysis"])

# In-memory job storage for this service (production: use Redis)
maps_jobs: Dict[str, Dict[str, Any]] = {}


class TranscriptAnalysisRequest(BaseModel):
    transcript: str
    context: Optional[Dict[str, Any]] = None
    manager_name: str = "Manager"
    persona_name: str = "Employee"


class ConversationAnalysisRequest(BaseModel):
    conversation_id: str
    context: Optional[Dict[str, Any]] = None


@router.post("/analyze/transcript")
async def analyze_transcript(request: TranscriptAnalysisRequest):
    """
    Analyze a raw transcript using MAPS framework
    Uses standalone service (no Supabase dependency)
    """
    try:
        job_id = str(uuid.uuid4())
        
        logger.info(f"Starting MAPS transcript analysis: job_id={job_id}, length={len(request.transcript)}")
        
        # Store job with initial status
        maps_jobs[job_id] = {
            "status": "processing",
            "progress": 10,
            "stage": "analyzing",
            "current_item": "Running MAPS analysis...",
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None,
            "analysis_type": "transcript"
        }
        
        try:
            # Create standalone service (no Supabase needed)
            service = create_standalone_maps_service()
            
            # Update progress
            maps_jobs[job_id].update({
                "progress": 30,
                "current_item": "Analyzing behavioral patterns..."
            })
            
            # Run analysis
            result = await service.analyze_transcript(
                transcript=request.transcript,
                context=request.context,
                manager_name=request.manager_name,
                persona_name=request.persona_name
            )
            
            # Update progress
            maps_jobs[job_id].update({
                "progress": 80,
                "current_item": "Generating report..."
            })
            
            # Convert result to dict for frontend
            result_dict = {
                "session_id": result.session_id,
                "conversation_id": result.conversation_id,
                "analyzed_at": result.analyzed_at.isoformat(),
                "overall_quality_score": result.overall_quality_score,
                "maps_values_summary": result.maps_values_summary,
                "conditions_for_change": {
                    "safety_trust": result.conditions_for_change.safety_trust,
                    "empowerment": result.conditions_for_change.empowerment,
                    "autonomy": result.conditions_for_change.autonomy,
                    "clarity": result.conditions_for_change.clarity,
                    "confidence_building": result.conditions_for_change.confidence_building,
                    "overall_score": result.conditions_for_change.overall_score,
                    "summary": result.conditions_for_change.summary
                },
                "person_centred_conditions": {
                    "genuineness": result.person_centred_conditions.genuineness,
                    "positive_regard": result.person_centred_conditions.positive_regard,
                    "empathic_understanding": result.person_centred_conditions.empathic_understanding,
                    "active_listening": result.person_centred_conditions.active_listening,
                    "collaboration": result.person_centred_conditions.collaboration,
                    "overall_score": result.person_centred_conditions.overall_score,
                    "summary": result.person_centred_conditions.summary
                },
                "patterns_observed": {
                    "manager_patterns": result.patterns_observed.manager_patterns,
                    "employee_patterns": result.patterns_observed.employee_patterns,
                    "interaction_dynamics": result.patterns_observed.interaction_dynamics,
                    "conversation_balance": result.patterns_observed.conversation_balance
                },
                "strengths_and_suggestions": {
                    "strengths": result.strengths_and_suggestions.strengths,
                    "opportunities": result.strengths_and_suggestions.opportunities,
                    "next_session_focus": result.strengths_and_suggestions.next_session_focus,
                    "maps_alignment": result.strengths_and_suggestions.maps_alignment
                }
            }
            
            # Complete job
            maps_jobs[job_id].update({
                "status": "complete",
                "progress": 100,
                "stage": "complete",
                "current_item": "Analysis complete!",
                "result": result_dict,
                "completed_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"MAPS transcript analysis completed: job_id={job_id}, score={result.overall_quality_score}/10")
            
        except Exception as e:
            logger.error(f"MAPS analysis failed for job {job_id}: {e}", exc_info=True)
            maps_jobs[job_id].update({
                "status": "error",
                "error": str(e),
                "stage": "error",
                "current_item": f"Error: {str(e)}"
            })
        
        return {"job_id": job_id, "status": "submitted", "analysis_type": "maps_transcript"}
        
    except Exception as e:
        logger.error(f"Failed to submit MAPS transcript analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit analysis: {str(e)}")


@router.post("/analyze/conversation")
async def analyze_conversation(
    request: ConversationAnalysisRequest,
    supabase=Depends(get_supabase_client)
):
    """
    Analyze a conversation from Supabase by conversation_id using MAPS framework
    """
    try:
        job_id = str(uuid.uuid4())
        
        logger.info(f"Starting MAPS conversation analysis: job_id={job_id}, conversation_id={request.conversation_id}")
        
        # Store job with initial status
        maps_jobs[job_id] = {
            "status": "processing",
            "progress": 10,
            "stage": "fetching",
            "current_item": "Fetching conversation from database...",
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None,
            "analysis_type": "conversation",
            "conversation_id": request.conversation_id
        }
        
        try:
            # Get MAPS service with Supabase
            service = get_maps_analysis_service(supabase_client=supabase)
            
            # Update progress
            maps_jobs[job_id].update({
                "progress": 30,
                "current_item": "Analyzing conversation with MAPS framework..."
            })
            
            # Run analysis
            result = await service.analyze_conversation_by_id(
                conversation_id=request.conversation_id,
                context=request.context
            )
            
            # Update progress
            maps_jobs[job_id].update({
                "progress": 80,
                "current_item": "Generating detailed report..."
            })
            
            # Convert result to dict (same as transcript analysis)
            result_dict = {
                "session_id": result.session_id,
                "conversation_id": result.conversation_id,
                "analyzed_at": result.analyzed_at.isoformat(),
                "overall_quality_score": result.overall_quality_score,
                "maps_values_summary": result.maps_values_summary,
                "conditions_for_change": {
                    "safety_trust": result.conditions_for_change.safety_trust,
                    "empowerment": result.conditions_for_change.empowerment,
                    "autonomy": result.conditions_for_change.autonomy,
                    "clarity": result.conditions_for_change.clarity,
                    "confidence_building": result.conditions_for_change.confidence_building,
                    "overall_score": result.conditions_for_change.overall_score,
                    "summary": result.conditions_for_change.summary
                },
                "person_centred_conditions": {
                    "genuineness": result.person_centred_conditions.genuineness,
                    "positive_regard": result.person_centred_conditions.positive_regard,
                    "empathic_understanding": result.person_centred_conditions.empathic_understanding,
                    "active_listening": result.person_centred_conditions.active_listening,
                    "collaboration": result.person_centred_conditions.collaboration,
                    "overall_score": result.person_centred_conditions.overall_score,
                    "summary": result.person_centred_conditions.summary
                },
                "patterns_observed": {
                    "manager_patterns": result.patterns_observed.manager_patterns,
                    "employee_patterns": result.patterns_observed.employee_patterns,
                    "interaction_dynamics": result.patterns_observed.interaction_dynamics,
                    "conversation_balance": result.patterns_observed.conversation_balance
                },
                "strengths_and_suggestions": {
                    "strengths": result.strengths_and_suggestions.strengths,
                    "opportunities": result.strengths_and_suggestions.opportunities,
                    "next_session_focus": result.strengths_and_suggestions.next_session_focus,
                    "maps_alignment": result.strengths_and_suggestions.maps_alignment
                }
            }
            
            # Complete job
            maps_jobs[job_id].update({
                "status": "complete",
                "progress": 100,
                "stage": "complete",
                "current_item": "Analysis complete!",
                "result": result_dict,
                "completed_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"MAPS conversation analysis completed: job_id={job_id}, score={result.overall_quality_score}/10")
            
        except Exception as e:
            logger.error(f"MAPS conversation analysis failed for job {job_id}: {e}", exc_info=True)
            maps_jobs[job_id].update({
                "status": "error",
                "error": str(e),
                "stage": "error",
                "current_item": f"Error: {str(e)}"
            })
        
        return {"job_id": job_id, "status": "submitted", "analysis_type": "maps_conversation"}
        
    except Exception as e:
        logger.error(f"Failed to submit MAPS conversation analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit analysis: {str(e)}")


@router.get("/status/{job_id}")
async def get_maps_job_status(job_id: str):
    """Get MAPS analysis job status"""
    if job_id not in maps_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = maps_jobs[job_id]
    
    response = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "stage": job["stage"],
        "current_item": job.get("current_item", ""),
        "created_at": job["created_at"],
        "analysis_type": job.get("analysis_type", "maps"),
        "error": job.get("error")
    }
    
    # Include result when complete
    if job["status"] == "complete" and job.get("result"):
        response["result"] = job["result"]
    
    return response


@router.get("/result/{job_id}")
async def get_maps_result(job_id: str):
    """Get completed MAPS analysis results"""
    if job_id not in maps_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = maps_jobs[job_id]
    
    if job["status"] != "complete":
        raise HTTPException(status_code=400, detail=f"Job not complete. Status: {job['status']}")
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "analysis_type": job.get("analysis_type", "maps"),
        "result": job["result"],
        "completed_at": job.get("completed_at", job["created_at"])
    }


@router.delete("/cache")
async def clear_maps_cache():
    """Clear MAPS analysis cache"""
    try:
        global maps_jobs
        cleared_count = len(maps_jobs)
        maps_jobs.clear()
        
        return {
            "status": "success",
            "message": f"MAPS cache cleared successfully. Removed {cleared_count} cached analyses.",
            "cleared_jobs": cleared_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear MAPS cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")