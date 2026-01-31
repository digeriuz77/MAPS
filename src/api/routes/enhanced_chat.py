"""
DEPRECATED: Enhanced Chat Routes

This file is deprecated. All conversation functionality has been
replaced by the scenario-based training system in src/api/routes/scenarios.py.

Please use:
- GET /api/scenarios - List available scenarios
- POST /api/scenarios/{id}/start - Start a scenario
- POST /api/scenarios/attempts/{id}/turn - Process a turn
- GET /api/scenarios/attempts/{id}/analysis - Get analysis

This file will be removed in a future update.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import uuid
from datetime import datetime

from src.dependencies import get_supabase_client
from src.services.short_term_memory_service import short_term_memory
from src.services.analytics_service import analytics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["enhanced-chatdeprecated"])


class PersonaInfo(BaseModel):
    """Persona information for selection screen"""
    id: str
    name: str
    description: str


class EnhancedChatRequest(BaseModel):
    message: str
    persona_id: str
    session_id: str


class EnhancedChatResponse(BaseModel):
    conversation_id: str
    response: str
    trust_level: float


@router.get("/deprecated")
async def chat_deprecated():
    """Redirect notice for deprecated chat routes"""
    return {
        "message": "This endpoint is deprecated. Please use /api/scenarios/* instead.",
        "list_scenarios": "GET /api/scenarios",
        "start_scenario": "POST /api/scenarios/{id}/start",
        "process_turn": "POST /api/scenarios/attempts/{id}/turn",
        "get_analysis": "GET /api/scenarios/attempts/{id}/analysis"
    }


@router.get("/personas", response_model=List[PersonaInfo])
async def get_enhanced_personas():
    """
    DEPRECATED: Use GET /api/scenarios instead
    
    Get available personas for conversation.
    Now replaced by scenario-based training.
    """
    logger.warning("Using deprecated /api/chat/personas - use /api/scenarios instead")
    try:
        supabase = get_supabase_client()
        result = supabase.table('enhanced_personas').select('persona_id, name, description').execute()
        
        if not result.data:
            return []
        
        personas = []
        for persona_data in result.data:
            personas.append(PersonaInfo(
                id=persona_data['persona_id'],
                name=persona_data['name'],
                description=persona_data['description']
            ))
        
        return personas
        
    except Exception as e:
        logger.error(f"Error fetching personas: {e}")
        raise HTTPException(status_code=500, detail="Database error loading personas")


@router.post("/send", response_model=EnhancedChatResponse)
async def send_enhanced_message(request: EnhancedChatRequest):
    """
    DEPRECATED: Use POST /api/scenarios/attempts/{id}/turn instead
    
    Send message using enhanced persona system.
    This route is deprecated - please migrate to the scenario-based system.
    """
    logger.warning("Using deprecated /api/chat/send - use /api/scenarios/* instead")
    
    # Return deprecation notice with mock response
    return EnhancedChatResponse(
        conversation_id=request.session_id,
        response="This conversation endpoint is deprecated. Please use the scenario-based training system at /api/scenarios/*",
        trust_level=0.5
    )


@router.post("/start")
async def start_enhanced_conversation(request):
    """
    DEPRECATED: Use POST /api/scenarios/{id}/start instead
    
    Start a new conversation with a persona.
    This route is deprecated - please migrate to the scenario-based system.
    """
    logger.warning("Using deprecated /api/chat/start - use /api/scenarios/* instead")
    
    return {
        "message": "This endpoint is deprecated. Please use /api/scenarios/{scenario_id}/start instead.",
        "conversation_id": str(uuid.uuid4()),
        "initial_greeting": "Please use the scenario-based training system for MI practice."
    }


@router.get("/conversations/{conversation_id}")
async def get_enhanced_conversation(conversation_id: str):
    """
    DEPRECATED: Use GET /api/scenarios/attempts/{attempt_id}/analysis instead
    
    Get full conversation.
    This route is deprecated.
    """
    logger.warning("Using deprecated /api/chat/conversations - use /api/scenarios/* instead")
    
    return {
        "message": "This endpoint is deprecated. Please use /api/scenarios/attempts/{attempt_id}/analysis instead.",
        "conversation_id": conversation_id
    }
