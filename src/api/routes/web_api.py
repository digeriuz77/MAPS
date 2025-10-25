"""
Simplified web API routes for browser interface
"""
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from pydantic import BaseModel
import io

from src.core.persona_engine import PersonaEngine
from src.dependencies import get_persona_engine
from src.utils.security import InputValidator, hash_session_id
from src.exceptions import SafetyViolationError

logger = logging.getLogger(__name__)
router = APIRouter()

# Simplified models for web interface
class WebPersonaInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    difficulty: str = "intermediate"

class WebChatRequest(BaseModel):
    message: str
    session_id: str
    context: Optional[dict] = None

class WebChatResponse(BaseModel):
    response: str
    timestamp: str = None

@router.get("/personas", response_model=dict)
async def list_personas_web(
    engine: PersonaEngine = Depends(get_persona_engine)
):
    """List all personas in web-friendly format"""
    personas_list = engine.list_personas()
    
    web_personas = []
    for persona_data in personas_list:
        # Map difficulty levels
        difficulty = "intermediate"
        if hasattr(persona_data, 'difficulty_level'):
            if persona_data.difficulty_level <= 3:
                difficulty = "novice"
            elif persona_data.difficulty_level >= 7:
                difficulty = "expert"
        
        web_personas.append({
            "id": persona_data.get("id", "unknown"),
            "name": persona_data.get("name", "Unknown Persona"),
            "description": persona_data.get("description", ""),
            "difficulty": difficulty,
            "metadata": persona_data.get("metadata", {})
        })
    
    return {"personas": web_personas}

@router.post("/personas/{persona_id}/chat", response_model=WebChatResponse)
async def chat_with_persona_web(
    persona_id: str,
    request: WebChatRequest,
    engine: PersonaEngine = Depends(get_persona_engine)
):
    """Simplified chat endpoint for web interface"""
    try:
        # Validate input
        validated_message = InputValidator.validate_message(request.message)
        validated_context = request.context or {}
        
        # Hash session ID for privacy
        hashed_session = hash_session_id(request.session_id)
        
        # Get response from persona
        response = await engine.chat_with_persona(
            persona_id=persona_id,
            message=validated_message,
            session_id=hashed_session,
            context=validated_context
        )
        
        return WebChatResponse(
            response=response,
            timestamp=datetime.now().isoformat()
        )
        
    except SafetyViolationError as e:
        raise HTTPException(status_code=400, detail="Your message contains inappropriate content. Please try again.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_id}' not found")
    except Exception as e:
        logger.error(f"Error in web chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Sorry, I encountered an error. Please try again.")

@router.get("/v1/dialogue/scenarios")
async def get_dialogue_scenarios():
    """Get available dialogue scenarios"""
    return {
        "scenarios": [
            {
                "id": "petra_jones",
                "name": "Manager Check-in with Petra Jones",
                "description": "Practice motivational interviewing techniques with a team member who feels their performance is being questioned",
                "difficulty": "intermediate",
                "character": "Petra Jones",
                "duration": "15-20 minutes"
            }
        ]
    }

@router.get("/v1/dialogue/scenarios/{scenario_id}")
async def get_dialogue_scenario(scenario_id: str):
    """Get specific dialogue scenario data"""
    import json
    import os

    if scenario_id != "petra_jones":
        raise HTTPException(status_code=404, detail="Scenario not found")

    try:
        # Get petra dialogue file path
        petra_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "src", "data", "dialogues", "petra_jones.json"
        )

        if not os.path.exists(petra_file):
            raise HTTPException(status_code=404, detail="Dialogue scenario not found")

        with open(petra_file, 'r', encoding='utf-8') as f:
            petra_data = json.load(f)

        return {"scenario": petra_data}

    except Exception as e:
        logger.error(f"Error loading dialogue scenario: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load scenario data")

@router.post("/v1/dialogue/scenarios/{scenario_id}/next")
async def dialogue_next_step(scenario_id: str, request: dict):
    """Handle dialogue progression - simplified version"""
    if scenario_id != "petra_jones":
        raise HTTPException(status_code=404, detail="Scenario not found")

    # For now, just return success - the client handles the dialogue tree logic
    return {"success": True, "message": "Choice recorded"}

@router.post("/export/pdf")
async def export_conversation_pdf(
    request: dict
):
    """Export conversation as PDF (returns HTML for now, can be enhanced with reportlab)"""
    try:
        messages = request.get("messages", [])
        metadata = request.get("metadata", {})
        
        if not messages:
            raise HTTPException(status_code=400, detail="No messages to export")
        
        # Generate HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Conversation with {metadata.get('persona', 'Assistant')}</title>
    <style>
        @media print {{
            body {{ margin: 0; }}
            .no-print {{ display: none; }}
        }}
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            border-bottom: 2px solid #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
        }}
        .message {{
            margin: 15px 0;
            padding: 10px;
            border-left: 3px solid #ddd;
        }}
        .message.user {{
            border-left-color: #3498db;
            background-color: #f0f8ff;
        }}
        .message.assistant {{
            border-left-color: #2ecc71;
            background-color: #f0fff0;
        }}
        .sender {{
            font-weight: bold;
            color: #555;
        }}
        .time {{
            font-size: 0.8em;
            color: #888;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Conversation with {metadata.get('persona', 'Assistant')}</h1>
        <p><strong>Date:</strong> {metadata.get('exportDate', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</p>
        <p><strong>Session:</strong> {metadata.get('sessionId', 'Unknown')}</p>
        <p><strong>Total Messages:</strong> {len(messages)}</p>
    </div>
    
    <div class="messages">
"""
        
        for msg in messages:
            sender_class = 'user' if msg.get('sender') == 'user' else 'assistant'
            sender_name = 'You' if msg.get('sender') == 'user' else metadata.get('persona', 'Assistant')
            html_content += f"""
        <div class="message {sender_class}">
            <div class="sender">{sender_name}</div>
            <div class="content">{msg.get('text', '')}</div>
            <div class="time">{msg.get('time', '')}</div>
        </div>
"""
        
        html_content += """
    </div>
    
    <div class="footer">
        <p>Generated by Persona AI Training System</p>
    </div>
</body>
</html>
"""
        
        # Return HTML with appropriate headers for PDF printing
        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Content-Disposition": f"inline; filename={metadata.get('persona', 'conversation').replace(' ', '_')}_export.html"
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF export: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate export")
