"""
Reflection API routes for simplified static question reflection
Uses GPT-4.1-nano for cost-effective summary generation
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.dependencies import get_supabase_client
from src.services.llm_service import LLMService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reflection", tags=["reflection"])

@router.get("/health")
async def reflection_health():
    """Health check for reflection service"""
    return {"status": "healthy", "service": "reflection"}

@router.get("/sessions/recent")
async def get_recent_reflections(limit: int = 10, supabase = Depends(get_supabase_client)):
    """Return the most recent reflection_sessions rows for verification"""
    try:
        result = supabase.table('reflection_sessions') \
            .select('*') \
            .order('session_date', desc=True) \
            .limit(max(1, min(limit, 50))) \
            .execute()
        rows = result.data or []
        return {"count": len(rows), "rows": rows}
    except Exception as e:
        logger.error(f"Failed to fetch recent reflections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to query reflection sessions")

class ReflectionSummaryRequest(BaseModel):
    """Request model for reflection summary generation"""
    question1_response: str
    question2_response: str
    question3_response: str
    session_id: Optional[str] = None
    persona_practiced: Optional[str] = None

class ReflectionSummaryResponse(BaseModel):
    """Response model for reflection summary"""
    summary: str
    generated_at: str

@router.post("/generate-summary", response_model=ReflectionSummaryResponse)
async def generate_reflection_summary(
    request: ReflectionSummaryRequest,
    supabase = Depends(get_supabase_client)
):
    """
    Generate a cohesive summary from three reflection question responses.
    Uses GPT-4.1-nano for cost-effective, high-quality summaries.
    
    The prompt is stored in Supabase system_prompts table as per project specification.
    """
    try:
        logger.info(f"Reflection summary request received for session {request.session_id}")
        logger.info(f"Request data: persona={request.persona_practiced}")
        logger.info(f"Response lengths: q1={len(request.question1_response)}, q2={len(request.question2_response)}, q3={len(request.question3_response)}")
        
        # Get the reflection summary prompt from Supabase with error handling
        prompt_result = None
        try:
            prompt_result = supabase.table('system_prompts')\
                .select('*')\
                .eq('prompt_key', 'reflection_summary')\
                .maybe_single()\
                .execute()
            
            if prompt_result.data and prompt_result.data.get('prompt_text'):
                base_prompt = prompt_result.data['prompt_text']
                logger.info("Using reflection prompt from Supabase")
            else:
                # Fallback prompt if not in database (should add to Supabase)
                logger.warning("Reflection summary prompt not found in database, using fallback")
                base_prompt = """Based on the following reflection responses, create a concise, cohesive summary (2-3 paragraphs) that synthesizes the practitioner's insights:

What went well: {question1}

Struggles: {question2}

Future improvements: {question3}

Provide an encouraging, professional summary that highlights key insights and growth opportunities. Focus on patterns, strengths to build on, and specific actionable improvements."""
        except Exception as db_error:
            logger.error(f"Failed to get prompt from Supabase: {db_error}")
            # Use fallback prompt
            base_prompt = """Based on the following reflection responses, create a concise, cohesive summary (2-3 paragraphs) that synthesizes the practitioner's insights:

What went well: {question1}

Struggles: {question2}

Future improvements: {question3}

Provide an encouraging, professional summary that highlights key insights and growth opportunities. Focus on patterns, strengths to build on, and specific actionable improvements."""
        
        # Format the prompt with user responses
        formatted_prompt = base_prompt.format(
            question1=request.question1_response,
            question2=request.question2_response,
            question3=request.question3_response
        )
        
        logger.info("Attempting to generate reflection summary with LLM")
        
        # Get LLM service - REQUIRED for reflection summaries
        llm_service = LLMService()
        
        logger.info("Generating reflection summary with OpenAI GPT-4o-mini")
        
        # Use model and settings from database prompt
        model_to_use = "gpt-4o-mini"  # Default fallback (valid OpenAI model)
        temperature_to_use = 0.7
        max_tokens_to_use = 600

        # If we got the prompt from database, use its recommended settings
        if prompt_result and prompt_result.data:
            model_to_use = prompt_result.data.get('model_recommended', model_to_use)
            temperature_to_use = prompt_result.data.get('temperature', temperature_to_use)
            max_tokens_to_use = prompt_result.data.get('max_tokens', max_tokens_to_use)
            logger.info(f"Using database settings: model={model_to_use}, temp={temperature_to_use}, tokens={max_tokens_to_use}")
        
        # Generate summary using database-specified model and settings
        summary = await llm_service.generate_response(
            prompt=formatted_prompt,
            system_prompt="You are an expert person-centred coach providing thoughtful, encouraging reflection summaries for motivational interviewing practice sessions.",
            model=model_to_use,
            temperature=temperature_to_use,
            max_tokens=max_tokens_to_use
        )
        
        if not summary or not summary.strip():
            raise HTTPException(status_code=500, detail="Generated summary was empty")
        
        logger.info(f"Successfully generated reflection summary for session {request.session_id}")
        
        # Store the reflection in the database
        try:
            # Only set conversation_id if session_id looks like a valid UUID
            conversation_id = None
            if request.session_id:
                # Check if session_id is a valid UUID format
                import re
                uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                if re.match(uuid_pattern, request.session_id, re.IGNORECASE):
                    conversation_id = request.session_id
                else:
                    logger.info(f"Session ID '{request.session_id}' is not a valid UUID, storing as None")
            
            # Generate a UUID for the reflection record (table requires non-null id)
            import uuid
            reflection_id = str(uuid.uuid4())
            
            reflection_data = {
                'id': reflection_id,
                'user_id': '00000000-0000-0000-0000-000000000001',  # Default user ID
                'session_date': datetime.utcnow().date().isoformat(),
                'question1': request.question1_response,
                'question2': request.question2_response,
                'question3': request.question3_response,
                'summary': summary.strip(),
                'conversation_id': conversation_id,  # top-level for easy querying
                'metadata': {
                    'conversation_id': conversation_id,
                    'persona_practiced': request.persona_practiced,
                    'completed': True,
                    'session_type': 'coaching_reflection'
                }
            }
            
            # Insert into reflection_sessions table
            reflection_result = supabase.table('reflection_sessions').insert(reflection_data).execute()
            
            if reflection_result.data:
                logger.info(f"Stored reflection in database with ID: {reflection_result.data[0]['id']}")
            else:
                logger.warning("Failed to store reflection in database - no data returned")
                
        except Exception as db_error:
            logger.error(f"Failed to store reflection in database: {db_error}", exc_info=True)
            # Don't fail the whole request if database storage fails
        
        return ReflectionSummaryResponse(
            summary=summary.strip(),
            generated_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to generate reflection summary: {e}", exc_info=True)
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception args: {e.args}")
        
        # Provide specific error messages for common issues
        error_msg = str(e).lower()
        if "api key" in error_msg or "authentication" in error_msg:
            detail = "OpenAI API key is missing or invalid. Please check OPENAI_API_KEY environment variable."
        elif "rate limit" in error_msg:
            detail = "OpenAI API rate limit exceeded. Please try again in a few minutes."
        elif "timeout" in error_msg:
            detail = "OpenAI API request timed out. Please try again."
        elif "network" in error_msg or "connection" in error_msg:
            detail = "Network error connecting to OpenAI. Please check your internet connection."
        else:
            detail = f"Failed to generate reflection summary: {str(e)}"
            
        raise HTTPException(
            status_code=500,
            detail=detail
        )

class EmailReflectionRequest(BaseModel):
    """Request model for emailing reflection"""
    email: str
    question1: str
    question2: str
    question3: str
    summary: str
    session_id: Optional[str] = None
    persona_practiced: Optional[str] = None

@router.post("/send-email")
async def send_reflection_email(
    request: EmailReflectionRequest,
    supabase = Depends(get_supabase_client)
):
    """
    Send reflection results via email.

    Note: Email service requires SMTP configuration.
    If not configured, returns success but doesn't send email.
    """
    try:
        from src.services.email_service import EmailService
        
        email_service = EmailService()
        
        if not email_service.enabled:
            logger.warning(f"Email service not configured. Skipping email to {request.email}")
            return {
                "success": True,
                "message": "Email service not configured. Please download your reflection instead.",
                "email_configured": False
            }
        
        # Format email content
        email_subject = "Your MI Practice Reflection Summary"
        email_body = f"""
Thank you for practicing on the 1-1 platform!

Here is your reflection summary from your practice session{f' with {request.persona_practiced}' if request.persona_practiced else ''}:

═══════════════════════════════════════════════════════

WHAT WENT WELL:
{request.question1}

WHAT YOU STRUGGLED WITH:
{request.question2}

WHAT YOU MIGHT DO DIFFERENTLY:
{request.question3}

═══════════════════════════════════════════════════════

YOUR PERSONALIZED SUMMARY:

{request.summary}

═══════════════════════════════════════════════════════

Keep practicing! Come back anytime to continue improving your MI skills.

- The 1-1 Practice Platform Team
Virtual Health Labs

Session ID: {request.session_id or 'N/A'}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""
        
        # Attach a .txt file of the reflection as well
        attachment_filename = f"reflection_{datetime.utcnow().strftime('%Y%m%d_%H%M%SZ')}.txt"
        attachments = [{
            'filename': attachment_filename,
            'content': email_body.encode('utf-8')
        }]

        # Send email using simple method with attachment
        success = await email_service._send_email(
            recipient_email=request.email,
            subject=email_subject,
            text_content=email_body,
            attachments=attachments
        )
        
        if success:
            logger.info(f"Sent reflection email to {request.email}")
            
            # Update database to record email was sent
            try:
                if request.session_id:
                    # Find the reflection session by conversation_id and update email field
                    supabase.table('reflection_sessions').update({
                        'email_sent_to': request.email
                    }).eq('conversation_id', request.session_id).execute()
                    logger.info(f"Updated reflection record with email sent to {request.email}")
            except Exception as db_error:
                logger.warning(f"Failed to update email tracking in database: {db_error}")
            
            return {
                "success": True,
                "message": "Reflection summary sent to your email",
                "email_configured": True
            }
        else:
            raise Exception("Email service failed to send")
        
    except Exception as e:
        logger.error(f"Failed to send reflection email: {e}", exc_info=True)
        # Don't fail the request - just notify that email didn't work
        return {
            "success": False,
            "message": "Failed to send email. Please download your reflection instead.",
            "email_configured": False,
            "error": str(e)
        }
