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
from src.services.analysis import AnalysisRequest
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
    """Submit transcript for person-centred MAPS analysis (legacy endpoint - use /text instead)"""
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
        
        # Start MAPS analysis in background
        try:
            maps_service = get_maps_analysis_service()
            
            # Extract speaker names
            speaker_hints = request.speaker_hints or {}
            context = request.context or {}
            
            coach_name = speaker_hints.get("practitioner_identifier_hint") or context.get("practitioner_role", "Coach")
            person_name = speaker_hints.get("client_identifier_hint") or context.get("client_role", "Person")
            
            # Run MAPS analysis
            result = await maps_service.analyze_transcript(
                transcript=request.transcript,
                context=context,
                manager_name=coach_name,
                persona_name=person_name
            )
            
            # Convert to frontend format
            frontend_result = _convert_to_frontend_format(result)
            
            # Update job with results
            analysis_jobs[job_id].update({
                "status": "complete",
                "progress": 100,
                "stage": "complete",
                "result": frontend_result
            })
            
        except Exception as e:
            logger.error(f"MAPS analysis failed for job {job_id}: {e}")
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
        
        # Note: MITI cache_service removed in V3 (MAPS doesn't use caching)
        # In-memory job storage cleared above is sufficient
        
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
        logger.info(f"Converting result to frontend format. Type: {type(result)}")
        logger.info(f"Has overall_quality_score: {hasattr(result, 'overall_quality_score')}")
        
        # Check if this is a MAPSAnalysisResult
        if hasattr(result, 'overall_quality_score'):
            # MAPS format - convert to frontend format (no overall score)
            logger.info("Processing MAPS result (no overall score)")

            # Use new core_coaching_effectiveness structure (3 themes)
            core_effectiveness = result.core_coaching_effectiveness
            
            # Build report structure with new theme names
            # Access as dicts since MAPS service returns dicts, not Pydantic models
            fts = core_effectiveness.get('foundational_trust_safety', {}) if isinstance(core_effectiveness, dict) else core_effectiveness.foundational_trust_safety
            epa = core_effectiveness.get('empathic_partnership_autonomy', {}) if isinstance(core_effectiveness, dict) else core_effectiveness.empathic_partnership_autonomy
            ec = core_effectiveness.get('empowerment_clarity', {}) if isinstance(core_effectiveness, dict) else core_effectiveness.empowerment_clarity
            
            # Handle both dict and Pydantic model access
            report_data = {
                "core_coaching_effectiveness": {
                    "foundational_trust_safety": {
                        "score": fts.get('score') if isinstance(fts, dict) else fts.score,
                        "evidence": fts.get('evidence') if isinstance(fts, dict) else fts.evidence,
                        "notes": fts.get('notes') if isinstance(fts, dict) else fts.notes
                    },
                    "empathic_partnership_autonomy": {
                        "score": epa.get('score') if isinstance(epa, dict) else epa.score,
                        "evidence": epa.get('evidence') if isinstance(epa, dict) else epa.evidence,
                        "notes": epa.get('notes') if isinstance(epa, dict) else epa.notes
                    },
                    "empowerment_clarity": {
                        "score": ec.get('score') if isinstance(ec, dict) else ec.score,
                        "evidence": ec.get('evidence') if isinstance(ec, dict) else ec.evidence,
                        "notes": ec.get('notes') if isinstance(ec, dict) else ec.notes
                    }
                }
            }

            # Extract strengths_and_suggestions structure and convert to dicts
            suggestions = result.strengths_and_suggestions if hasattr(result, 'strengths_and_suggestions') else result.get('strengths_and_suggestions', {})
            
            # Handle both dict and Pydantic access
            if isinstance(suggestions, dict):
                raw_strengths = suggestions.get('strengths', [])
                raw_opportunities = suggestions.get('opportunities', [])
                next_focus = suggestions.get('next_session_focus', [])
                maps_alignment = suggestions.get('maps_alignment', '')
            else:
                raw_strengths = suggestions.strengths if hasattr(suggestions, 'strengths') else []
                raw_opportunities = suggestions.opportunities if hasattr(suggestions, 'opportunities') else []
                next_focus = suggestions.next_session_focus if hasattr(suggestions, 'next_session_focus') else []
                maps_alignment = suggestions.maps_alignment if hasattr(suggestions, 'maps_alignment') else ''
            
            # Convert strengths list (may be Pydantic models or dicts)
            strengths_list = [
                s.dict() if hasattr(s, 'dict') else s 
                for s in raw_strengths
            ] if raw_strengths else []
            
            # Convert opportunities list (may be Pydantic models or dicts)
            opportunities_list = [
                o.dict() if hasattr(o, 'dict') else o
                for o in raw_opportunities
            ] if raw_opportunities else []

            # Extract conversation statistics from patterns_observed
            patterns = result.patterns_observed if hasattr(result, 'patterns_observed') else result.get('patterns_observed', {})
            
            if isinstance(patterns, dict):
                conversation_balance = patterns.get('conversation_balance', {})
                coach_patterns = patterns.get('coach_patterns', [])
                person_patterns = patterns.get('person_patterns', [])
                manager_patterns = patterns.get('manager_patterns', [])
                employee_patterns = patterns.get('employee_patterns', [])
                interaction_dynamics = patterns.get('interaction_dynamics', '')
            else:
                conversation_balance = patterns.conversation_balance if hasattr(patterns, 'conversation_balance') else {}
                coach_patterns = patterns.coach_patterns if hasattr(patterns, 'coach_patterns') else []
                person_patterns = patterns.person_patterns if hasattr(patterns, 'person_patterns') else []
                manager_patterns = patterns.manager_patterns if hasattr(patterns, 'manager_patterns') else []
                employee_patterns = patterns.employee_patterns if hasattr(patterns, 'employee_patterns') else []
                interaction_dynamics = patterns.interaction_dynamics if hasattr(patterns, 'interaction_dynamics') else ''
            
            # Calculate turn estimates from coach/person patterns
            coach_patterns_count = len(coach_patterns)
            person_patterns_count = len(person_patterns)
            estimated_turns = max(coach_patterns_count + person_patterns_count, 10)  # Minimum 10 to show activity
            
            # Extract speaking percentages from conversation_balance
            coach_percentage = conversation_balance.get('coach_speaking_percentage', 50)
            person_percentage = conversation_balance.get('person_speaking_percentage', 50)
            
            # Estimate turn distribution based on speaking percentage
            practitioner_turns = int(estimated_turns * (coach_percentage / 100))
            client_turns = int(estimated_turns * (person_percentage / 100))
            
            # Build frontend-compatible result with NEW structure
            maps_summary = result.maps_values_summary if hasattr(result, 'maps_values_summary') else result.get('maps_values_summary', '')
            
            frontend_result = {
                # no overall score
                "maps_values_summary": maps_summary,
                "report": {
                    "core_coaching_effectiveness": report_data["core_coaching_effectiveness"],
                    "strengths_and_suggestions": {
                        "strengths": strengths_list,
                        "opportunities": opportunities_list,
                        "next_session_focus": next_focus,
                        "maps_alignment": maps_alignment
                    },
                    "patterns_observed": {
                        "manager_patterns": manager_patterns,
                        "employee_patterns": employee_patterns,
                        "interaction_dynamics": interaction_dynamics,
                        "conversation_balance": conversation_balance
                    }
                }
            }
            
            logger.info(f"Frontend result created successfully. Keys: {frontend_result.keys()}")
            logger.info(f"Report keys: {frontend_result['report'].keys()}")
            logger.info(f"Core coaching effectiveness keys: {frontend_result['report']['core_coaching_effectiveness'].keys()}")

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