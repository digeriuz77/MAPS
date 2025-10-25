"""
Analysis API routes for person-centred transcript analysis
"""
import logging
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel

from src.dependencies import get_supabase_client
from src.services.analysis import get_analysis_service, AnalysisRequest
from src.services.analysis.types import CompleteAnalysisResult
from src.services.analysis.maps_analysis_service import get_maps_analysis_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])

# In-memory job storage (in production, use Redis or database)
analysis_jobs: Dict[str, Dict[str, Any]] = {}

class AnalysisSubmission(BaseModel):
    transcript: str
    context: Optional[Dict[str, Any]] = None
    speaker_hints: Optional[Dict[str, Any]] = None

@router.post("/submit")
async def submit_analysis(request: AnalysisSubmission):
    """Submit transcript for person-centred analysis"""
    try:
        job_id = str(uuid.uuid4())
        
        # Store job with initial status
        analysis_jobs[job_id] = {
            "status": "pending",
            "progress": 0,
            "stage": "parsing",
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None
        }
        
        # Start analysis in background (simplified for now)
        try:
            analysis_service = get_analysis_service()
            
            # Convert request to analysis format
            analysis_request = AnalysisRequest(
                transcript=request.transcript,
                context=request.context,
                speaker_hints=request.speaker_hints
            )
            
            # Run analysis (in production, this should be async/background task)
            result = await analysis_service.analyze_transcript(
                raw_transcript=request.transcript,
                context=analysis_request.context,
                speaker_hints=analysis_request.speaker_hints
            )
            
            # Update job with results
            analysis_jobs[job_id].update({
                "status": "complete",
                "progress": 100,
                "stage": "complete",
                "result": result.dict() if hasattr(result, 'dict') else result
            })
            
        except Exception as e:
            logger.error(f"Analysis failed for job {job_id}: {e}")
            analysis_jobs[job_id].update({
                "status": "error",
                "error": str(e),
                "stage": "error"
            })
        
        return {"job_id": job_id, "status": "submitted"}
        
    except Exception as e:
        logger.error(f"Failed to submit analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit analysis")

@router.post("/text")
async def submit_text_analysis(request: AnalysisSubmission):
    """Submit transcript text for person-centred MAPS analysis - Frontend compatibility endpoint"""
    try:
        logger.info(f"MAPS analysis request received: transcript length={len(request.transcript)}, context={request.context}, speaker_hints={request.speaker_hints}")
        
        job_id = str(uuid.uuid4())
        
        # Store job with initial status
        analysis_jobs[job_id] = {
            "status": "pending",
            "progress": 5,
            "stage": "preprocessing",
            "current_item": "Initializing MAPS analysis...",
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None
        }
        
        # Start MAPS analysis in background with enhanced error handling
        try:
            maps_service = get_maps_analysis_service()
            logger.info(f"MAPS analysis service obtained, starting analysis for job {job_id}")
            
            # Extract speaker names from hints or context
            speaker_hints = request.speaker_hints or {}
            context = request.context or {}
            
            coach_name = speaker_hints.get("practitioner_identifier_hint") or context.get("practitioner_role", "Coach")
            person_name = speaker_hints.get("client_identifier_hint") or context.get("client_role", "Person")
            
            logger.info(f"Using speaker names: coach={coach_name}, person={person_name}")
            
            # Update progress
            analysis_jobs[job_id].update({
                "progress": 15,
                "stage": "coding",
                "current_item": "Analyzing person-centred conditions..."
            })
            
            # Run MAPS analysis using standalone transcript method
            result = await maps_service.analyze_transcript(
                transcript=request.transcript,
                context=context,
                manager_name=coach_name,
                persona_name=person_name
            )
            
            # Update progress
            analysis_jobs[job_id].update({
                "progress": 90,
                "stage": "finalizing",
                "current_item": "Generating report..."
            })

            # Debug: Log result structure before conversion
            logger.info(f"MAPS result type: {type(result)}")
            logger.info(f"MAPS result attributes: {dir(result)}")
            if hasattr(result, 'statistics'):
                logger.info(f"Statistics exists: {result.statistics}")
            if hasattr(result, 'report'):
                logger.info(f"Report exists: {result.report}")

            # Convert result to frontend-compatible format
            frontend_result = _convert_to_frontend_format(result)

            # Update job with results
            analysis_jobs[job_id].update({
                "status": "complete",
                "progress": 100,
                "stage": "complete",
                "current_item": "Analysis complete!",
                "result": frontend_result,
                "completed_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"MAPS analysis completed successfully for job {job_id}. Score: {result.overall_quality_score}/10")
            
        except Exception as e:
            logger.error(f"MAPS analysis failed for job {job_id}: {e}", exc_info=True)
            analysis_jobs[job_id].update({
                "status": "error",
                "error": str(e),
                "stage": "error",
                "current_item": f"Error: {str(e)}"
            })
        
        return {"job_id": job_id, "status": "submitted"}
        
    except Exception as e:
        logger.error(f"Failed to submit MAPS analysis: {e}", exc_info=True)
        # Return more detailed error information for debugging
        error_detail = str(e)
        if "Gemini" in error_detail:
            error_detail = f"Gemini API error: {error_detail}"
        elif "database" in error_detail.lower():
            error_detail = f"Database error: {error_detail}"
        elif "import" in error_detail.lower():
            error_detail = f"Import error: {error_detail}"
        
        raise HTTPException(status_code=500, detail=f"Failed to submit analysis: {error_detail}")

@router.post("/enhanced/{conversation_id}")
async def analyze_enhanced_conversation(conversation_id: str):
    """Analyze enhanced chat conversation by conversation_id"""
    try:
        job_id = str(uuid.uuid4())
        supabase = get_supabase_client()
        
        logger.info(f"Enhanced conversation analysis requested for {conversation_id}")
        
        # Store job with initial status
        analysis_jobs[job_id] = {
            "status": "pending",
            "progress": 5,
            "stage": "fetching",
            "current_item": "Retrieving enhanced conversation...",
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None
        }
        
        try:
            # Fetch conversation from conversation_transcripts
            transcript_result = supabase.table('conversation_transcripts').select('*').eq(
                'conversation_id', conversation_id
            ).order('turn_number').order('timestamp').execute()
            
            if not transcript_result.data:
                raise HTTPException(status_code=404, detail=f"Enhanced conversation {conversation_id} not found")
            
            # Get conversation metadata
            conv_result = supabase.table('conversations').select('*').eq(
                'id', conversation_id
            ).maybe_single().execute()
            
            persona_info = {}
            if conv_result.data:
                persona_id = conv_result.data.get('persona_id')
                if persona_id:
                    # Get persona name from enhanced_personas
                    persona_result = supabase.table('enhanced_personas').select('name').eq(
                        'persona_id', persona_id
                    ).maybe_single().execute()
                    if persona_result.data:
                        persona_info['name'] = persona_result.data.get('name', 'Person')
            
            coach_name = "Coach"
            person_name = persona_info.get('name', 'Person')
            
            # Update progress
            analysis_jobs[job_id].update({
                "progress": 25,
                "stage": "formatting",
                "current_item": "Formatting conversation transcript..."
            })
            
            # Format messages into transcript
            transcript_lines = []
            for msg in transcript_result.data:
                role = msg.get('role')
                message = msg.get('message', '')
                
                # Map roles to speaker names
                if role == 'user':
                    speaker = coach_name
                elif role == 'persona':
                    speaker = person_name
                else:
                    speaker = role.title()
                
                transcript_lines.append(f"{speaker}: {message}")
            
            transcript = "\n\n".join(transcript_lines)
            
            logger.info(f"Enhanced conversation formatted: {len(transcript)} chars, {len(transcript_result.data)} messages")
            
            # Update progress
            analysis_jobs[job_id].update({
                "progress": 40,
                "stage": "analyzing",
                "current_item": "Running MAPS analysis..."
            })
            
            # Run MAPS analysis using updated service
            maps_service = get_maps_analysis_service(supabase_client=supabase)
            
            # Use the new analyze_conversation_by_id method directly
            result = await maps_service.analyze_conversation_by_id(
                conversation_id=conversation_id,
                context={"conversation_id": conversation_id, "source": "enhanced_chat"}
            )
            
            # Update progress
            analysis_jobs[job_id].update({
                "progress": 90,
                "stage": "finalizing",
                "current_item": "Generating report..."
            })
            
            # Convert result to frontend-compatible format
            frontend_result = _convert_to_frontend_format(result)
            
            # Update job with results
            analysis_jobs[job_id].update({
                "status": "complete",
                "progress": 100,
                "stage": "complete",
                "current_item": "Analysis complete!",
                "result": frontend_result,
                "completed_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Enhanced conversation analysis completed for {conversation_id}. Score: {result.overall_quality_score}/10")
            
            return {"job_id": job_id, "status": "submitted"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Enhanced conversation analysis failed for {conversation_id}: {e}", exc_info=True)
            analysis_jobs[job_id].update({
                "status": "error",
                "error": str(e),
                "stage": "error",
                "current_item": f"Error: {str(e)}"
            })
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start enhanced conversation analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

@router.delete("/cache")
async def clear_analysis_cache():
    """Clear analysis cache for fresh analysis"""
    try:
        # Clear in-memory job storage
        global analysis_jobs
        cleared_count = len(analysis_jobs)
        analysis_jobs.clear()
        
        # Also clear any service-level caches if available
        try:
            from src.services.analysis.cache_service import get_analysis_cache
            cache_service = get_analysis_cache()
            cache_service.clear_all()
        except ImportError:
            # Cache service not available, that's OK
            pass
        
        return {
            "status": "success",
            "message": f"Cache cleared successfully. Removed {cleared_count} cached analyses.",
            "cleared_jobs": cleared_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@router.post("/maps")
async def submit_maps_analysis(request: AnalysisSubmission):
    """
    Submit transcript for MAPS person-centred analysis
    
    Uses the 4-part MAPS framework:
    1. Conditions for Change
    2. Person-Centred Core Conditions
    3. Patterns Observed
    4. Strengths & Suggestions
    """
    try:
        logger.info(f"MAPS analysis request received: transcript length={len(request.transcript)}")
        
        job_id = str(uuid.uuid4())
        
        # Store job with initial status
        analysis_jobs[job_id] = {
            "status": "pending",
            "progress": 0,
            "stage": "initializing",
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None,
            "analysis_type": "maps"
        }
        
        # Start MAPS analysis
        try:
            maps_service = get_maps_analysis_service()
            logger.info(f"MAPS service obtained, starting analysis for job {job_id}")
            
            # Extract speaker names from context or use defaults
            context = request.context or {}
            coach_name = context.get("practitioner_role", "Coach")
            person_name = context.get("client_role", "Person")
            
            # Update progress
            analysis_jobs[job_id].update({
                "progress": 25,
                "stage": "analyzing"
            })
            
            # Run MAPS analysis using the standalone transcript method
            result = await maps_service.analyze_transcript(
                transcript=request.transcript,
                context=context,
                manager_name=coach_name,
                persona_name=person_name
            )

            # Convert result to frontend-compatible format
            frontend_result = _convert_to_frontend_format(result)

            # Update job with results
            analysis_jobs[job_id].update({
                "status": "complete",
                "progress": 100,
                "stage": "complete",
                "result": frontend_result,
                "completed_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"MAPS analysis completed successfully for job {job_id}. Score: {result.overall_quality_score}/10")
            
        except Exception as e:
            logger.error(f"MAPS analysis failed for job {job_id}: {e}", exc_info=True)
            analysis_jobs[job_id].update({
                "status": "error",
                "error": str(e),
                "stage": "error"
            })
        
        return {"job_id": job_id, "status": "submitted", "analysis_type": "maps"}
        
    except Exception as e:
        logger.error(f"Failed to submit MAPS analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit MAPS analysis: {str(e)}")

@router.get("/status/{job_id}")
async def get_analysis_status(job_id: str):
    """Get analysis job status"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    response = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "stage": job["stage"],
        "created_at": job["created_at"],
        "error": job.get("error")
    }
    
    # Include result when complete for frontend compatibility
    if job["status"] == "complete" and job.get("result"):
        response["result"] = job["result"]
    
    return response

@router.get("/result/{job_id}")
async def get_analysis_result(job_id: str):
    """Get completed analysis results"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    if job["status"] != "complete":
        raise HTTPException(status_code=400, detail=f"Job not complete. Status: {job['status']}")
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "result": job["result"],
        "completed_at": job.get("completed_at", job["created_at"])
    }

@router.get("/result/{job_id}/export")
async def export_analysis_result(
    job_id: str, 
    format: str = Query("json", description="Export format: json, html, txt")
):
    """Export analysis results in various formats"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    if job["status"] != "complete":
        raise HTTPException(status_code=400, detail=f"Job not complete. Status: {job['status']}")
    
    result = job["result"]
    if not result:
        raise HTTPException(status_code=404, detail="No results available")
    
    try:
        if format == "json":
            content = json.dumps(result, indent=2)
            media_type = "application/json"
            filename = f"miti_analysis_{job_id}.json"
            
        elif format == "html":
            content = _generate_html_report(result, job_id)
            media_type = "text/html"
            filename = f"miti_analysis_{job_id}.html"
            
        elif format == "txt":
            content = _generate_text_report(result, job_id)
            media_type = "text/plain"
            filename = f"miti_analysis_{job_id}.txt"
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use: json, html, txt")
        
        headers = {
            "Content-Disposition": f"attachment; filename={filename}"
        }
        
        return Response(
            content=content,
            media_type=media_type,
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Failed to export analysis {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to export analysis")

def _generate_html_report(result: Dict[str, Any], job_id: str) -> str:
    """Generate HTML report from analysis results"""
    
    # Extract key data with safe defaults
    statistics = result.get("statistics", {})
    report = result.get("report", {})
    global_ratings = report.get("global_ratings", {})
    
    # Build HTML content
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Person-Centred Analysis Report - {job_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .section {{ margin-bottom: 25px; padding: 15px; border-left: 4px solid #7C9BF5; background: #f8f9fa; }}
        .metric {{ display: inline-block; margin: 10px 15px; }}
        .metric-value {{ font-size: 1.5em; font-weight: bold; color: #7C9BF5; }}
        .metric-label {{ font-size: 0.9em; color: #666; }}
        .rating {{ margin: 10px 0; padding: 10px; background: white; border-radius: 5px; }}
        .score {{ font-weight: bold; color: #7C9BF5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Person-Centred Analysis Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Job ID: {job_id}</p>
    </div>
    
    <div class="section">
        <h2>Statistics Overview</h2>
        <div class="metric">
            <div class="metric-value">{statistics.get('total_turns', 'N/A')}</div>
            <div class="metric-label">Total Turns</div>
        </div>
        <div class="metric">
            <div class="metric-value">{statistics.get('reflection_to_question_ratio', 'N/A')}</div>
            <div class="metric-label">Reflection:Question Ratio</div>
        </div>
        <div class="metric">
            <div class="metric-value">{statistics.get('percentage_complex_reflections', 'N/A')}</div>
            <div class="metric-label">Complex Reflections</div>
        </div>
    </div>
    
    <div class="section">
        <h2>Global Ratings</h2>
        {_format_global_ratings_html(global_ratings)}
    </div>
    
    <div class="section">
        <h2>Practitioner Patterns</h2>
        <h3>Strengths</h3>
        <p>{report.get('practitioner_patterns', {}).get('strengths', 'No data available')}</p>
        <h3>Challenge Areas</h3>
        <p>{report.get('practitioner_patterns', {}).get('challenge_areas', 'No data available')}</p>
    </div>
    
    <div class="section">
        <h2>Recommendations</h2>
        <h3>Immediate Focus</h3>
        <p>{report.get('actionable_recommendations', {}).get('immediate_focus', 'No recommendations available')}</p>
        <h3>Skill Development</h3>
        <p>{report.get('actionable_recommendations', {}).get('skill_development', 'No recommendations available')}</p>
    </div>
</body>
</html>
"""
    
    return html_content

def _format_global_ratings_html(global_ratings: Dict[str, Any]) -> str:
    """Format global ratings for HTML display"""
    if not global_ratings:
        return "<p>No global ratings available</p>"
    
    html = ""
    for rating_name, rating_data in global_ratings.items():
        if isinstance(rating_data, dict):
            score = rating_data.get('score', 'N/A')
            rationale = rating_data.get('rationale', 'No rationale provided')
            name = rating_name.replace('_', ' ').title()
            
            html += f"""
            <div class="rating">
                <strong>{name}:</strong> <span class="score">{score}/5</span>
                <p>{rationale}</p>
            </div>
            """
    
    return html

def _generate_text_report(result: Dict[str, Any], job_id: str) -> str:
    """Generate plain text report from analysis results"""
    
    statistics = result.get("statistics", {})
    report = result.get("report", {})
    global_ratings = report.get("global_ratings", {})
    
    content = f"""PERSON-CENTRED ANALYSIS REPORT
{'='*50}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Job ID: {job_id}

STATISTICS OVERVIEW
{'-'*20}
Total Turns: {statistics.get('total_turns', 'N/A')}
Reflection to Question Ratio: {statistics.get('reflection_to_question_ratio', 'N/A')}
Complex Reflections: {statistics.get('percentage_complex_reflections', 'N/A')}
Person-Centred Adherent to Non-Adherent Ratio: {statistics.get('mia_to_mina_ratio', 'N/A')}

GLOBAL RATINGS
{'-'*15}
{_format_global_ratings_text(global_ratings)}

PRACTITIONER PATTERNS
{'-'*21}
Strengths:
{report.get('practitioner_patterns', {}).get('strengths', 'No data available')}

Challenge Areas:
{report.get('practitioner_patterns', {}).get('challenge_areas', 'No data available')}

RECOMMENDATIONS
{'-'*15}
Immediate Focus:
{report.get('actionable_recommendations', {}).get('immediate_focus', 'No recommendations available')}

Skill Development:
{report.get('actionable_recommendations', {}).get('skill_development', 'No recommendations available')}

{'='*50}
Generated by Persona AI Training System
"""
    
    return content

def _convert_to_frontend_format(result) -> Dict[str, Any]:
    """Convert MAPS analysis result to format expected by frontend"""
    try:
        # Check if this is a MAPSAnalysisResult
        if hasattr(result, 'overall_quality_score'):
            # MAPS format - convert to frontend format
            proficiency_score = int(result.overall_quality_score * 10)  # Convert 1-10 to 0-100

            # Extract scores from person_centred_conditions
            pc_conditions = result.person_centred_conditions
            global_ratings = {
                "partnership": {
                    "score": int(pc_conditions.collaboration.get('score', 3) if isinstance(pc_conditions.collaboration, dict) else 3),
                    "rationale": pc_conditions.collaboration.get('rationale', 'Collaboration assessed') if isinstance(pc_conditions.collaboration, dict) else 'Collaboration assessed'
                },
                "empathy": {
                    "score": int(pc_conditions.empathic_understanding.get('score', 3) if isinstance(pc_conditions.empathic_understanding, dict) else 3),
                    "rationale": pc_conditions.empathic_understanding.get('rationale', 'Empathic understanding assessed') if isinstance(pc_conditions.empathic_understanding, dict) else 'Empathic understanding assessed'
                },
                "cultivating_change_talk": {
                    "score": int(result.conditions_for_change.confidence_building.get('score', 3) if isinstance(result.conditions_for_change.confidence_building, dict) else 3),
                    "rationale": result.conditions_for_change.confidence_building.get('rationale', 'Confidence building assessed') if isinstance(result.conditions_for_change.confidence_building, dict) else 'Confidence building assessed'
                },
                "softening_sustain_talk": {
                    "score": int(result.conditions_for_change.safety_trust.get('score', 3) if isinstance(result.conditions_for_change.safety_trust, dict) else 3),
                    "rationale": result.conditions_for_change.safety_trust.get('rationale', 'Safety and trust assessed') if isinstance(result.conditions_for_change.safety_trust, dict) else 'Safety and trust assessed'
                }
            }

            # Extract strengths and opportunities
            strengths_list = result.strengths_and_suggestions.strengths
            opportunities_list = result.strengths_and_suggestions.opportunities
            next_focus = result.strengths_and_suggestions.next_session_focus

            # Format strengths as single string
            strengths_text = "; ".join([s.get('strength', '') for s in strengths_list]) if strengths_list else 'Analysis completed'

            # Format opportunities as single string
            opportunities_text = "; ".join([o.get('suggestion', '') for o in opportunities_list]) if opportunities_list else 'Continue practicing'

            # Format next steps
            immediate_focus = next_focus[0] if next_focus else 'Review the analysis above'
            skill_development = "; ".join(next_focus[1:]) if len(next_focus) > 1 else 'Continue developing person-centred skills'

            # Extract conversation statistics from patterns_observed
            patterns = result.patterns_observed
            conversation_balance = patterns.conversation_balance if hasattr(patterns, 'conversation_balance') else {}
            
            # Calculate turn estimates from coach/person patterns
            coach_patterns_count = len(patterns.coach_patterns) if hasattr(patterns, 'coach_patterns') else 0
            person_patterns_count = len(patterns.person_patterns) if hasattr(patterns, 'person_patterns') else 0
            estimated_turns = max(coach_patterns_count + person_patterns_count, 10)  # Minimum 10 to show activity
            
            # Extract speaking percentages from conversation_balance
            coach_percentage = conversation_balance.get('coach_speaking_percentage', 50)
            person_percentage = conversation_balance.get('person_speaking_percentage', 50)
            
            # Estimate turn distribution based on speaking percentage
            practitioner_turns = int(estimated_turns * (coach_percentage / 100))
            client_turns = int(estimated_turns * (person_percentage / 100))
            
            # Build frontend-compatible result
            frontend_result = {
                "proficiency_score": proficiency_score,
                "summary": {
                    "conversation_overview": {
                        "total_turns": estimated_turns,
                        "practitioner_turns": practitioner_turns,
                        "client_turns": client_turns
                    },
                    "mi_quality_indicators": {
                        "reflection_to_question_ratio": "N/A",  # MAPS uses different framework
                        "complex_reflection_percentage": "N/A",
                        "mi_adherent_ratio": f"{proficiency_score}%"  # Overall quality score
                    }
                },
                "report": {
                    "global_ratings": global_ratings,
                    "practitioner_patterns": {
                        "strengths": strengths_text,
                        "challenge_areas": opportunities_text
                    },
                    "actionable_recommendations": {
                        "immediate_focus": immediate_focus,
                        "skill_development": skill_development
                    }
                },
                "statistics": {
                    "total_turns": estimated_turns,
                    "reflection_to_question_ratio": "N/A",
                    "percentage_complex_reflections": "N/A",
                    "mia_to_mina_ratio": f"{coach_percentage:.0f}:{person_percentage:.0f}",
                    "code_counts": {
                        "coach_patterns": coach_patterns_count,
                        "person_patterns": person_patterns_count
                    }
                }
            }

            return frontend_result

        else:
            # Old CompleteAnalysisResult format - keep existing logic
            stats = result.statistics
            # ... (original conversion logic)

    except Exception as e:
        logger.error(f"Error converting analysis result to frontend format: {e}", exc_info=True)
        # Return minimal fallback structure
        return {
            "proficiency_score": 50,
            "summary": {
                "conversation_overview": {"total_turns": 0, "practitioner_turns": 0, "client_turns": 0},
                "mi_quality_indicators": {
                    "reflection_to_question_ratio": "N/A",
                    "complex_reflection_percentage": "N/A",
                    "mi_adherent_ratio": "N/A"
                }
            },
            "report": {
                "global_ratings": {},
                "practitioner_patterns": {
                    "strengths": "Analysis encountered an error",
                    "challenge_areas": "Please try again"
                },
                "actionable_recommendations": {
                    "immediate_focus": "Check transcript format",
                    "skill_development": "Ensure proper speaker identification"
                }
            },
            "statistics": {
                "total_turns": 0,
                "reflection_to_question_ratio": "N/A",
                "percentage_complex_reflections": "N/A",
                "mia_to_mina_ratio": "N/A",
                "code_counts": {}
            }
        }