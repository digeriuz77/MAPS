"""
Voice API Routes - Endpoints for voice-enabled scenarios

Provides endpoints for:
- Creating voice sessions (full agent or STT-only)
- WebSocket streaming for real-time audio
- Session management and analysis
- TTS synthesis for persona responses
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from src.dependencies import get_current_user, get_supabase_client
from src.services.voice_gateway import VoiceGateway, get_voice_gateway
from src.services.flux_stt_service import FluxSTTService, get_flux_stt_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])


# ========== Request/Response Models ==========

class CreateVoiceSessionRequest(BaseModel):
    """Request to create a new voice session"""
    attempt_id: str = Field(..., description="Scenario attempt ID")
    mode: str = Field(
        default="stt_only",
        description="Voice mode: 'full' (Voice Agent), 'stt_only' (Flux), 'tts_only'"
    )
    persona_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Persona configuration for full voice agent mode"
    )
    # Flux-specific configuration
    eot_threshold: float = Field(
        default=0.7,
        ge=0.5,
        le=0.9,
        description="End-of-turn confidence threshold"
    )
    eager_eot_threshold: Optional[float] = Field(
        default=None,
        ge=0.3,
        le=0.9,
        description="Early end-of-turn threshold for faster responses"
    )
    eot_timeout_ms: int = Field(
        default=5000,
        ge=500,
        le=10000,
        description="Max silence before forced end-of-turn"
    )


class VoiceSessionResponse(BaseModel):
    """Response for voice session creation"""
    session_id: str
    attempt_id: str
    mode: str
    status: str
    websocket_url: str
    created_at: str


class VoiceSessionStatusResponse(BaseModel):
    """Response for session status"""
    session_id: str
    attempt_id: str
    mode: str
    status: str
    transcript_count: int
    current_transcript: Optional[str]
    started_at: Optional[str]
    last_activity_at: Optional[str]


class VoiceTranscriptResponse(BaseModel):
    """Response for session transcript"""
    session_id: str
    transcript: List[Dict[str, Any]]
    full_text: str
    word_count: int


class VoiceAnalysisResponse(BaseModel):
    """Response for voice session analysis"""
    session_id: str
    attempt_id: str
    mode: str
    duration_ms: int
    transcript: List[Dict[str, Any]]
    full_text: str
    metrics: Dict[str, Any]
    speech_analysis: Optional[Dict[str, Any]]


class TTSRequest(BaseModel):
    """Request for text-to-speech synthesis"""
    text: str = Field(..., min_length=1, max_length=5000)
    voice: str = Field(default="aura-2-thalia-en")
    output_format: str = Field(default="wav")


# ========== Route Implementations ==========

@router.post("/sessions", response_model=VoiceSessionResponse)
async def create_voice_session(
    request: CreateVoiceSessionRequest,
    current_user_id: str = Depends(get_current_user)
):
    """
    Create a new voice session for a scenario attempt.
    
    Modes:
    - 'full': Complete Voice Agent with STT + LLM + TTS
    - 'stt_only': Flux STT for transcription only
    - 'tts_only': Text-to-speech for persona responses
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Verify attempt exists and belongs to user
        supabase = get_supabase_client()
        attempt_result = supabase.table('scenario_attempts').select('*').eq(
            'id', request.attempt_id
        ).maybe_single().execute()
        
        if not attempt_result.data:
            raise HTTPException(status_code=404, detail="Attempt not found")
        
        if attempt_result.data['user_id'] != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized for this attempt")
        
        # Create session based on mode
        if request.mode == "full":
            # Full Voice Agent mode
            gateway = get_voice_gateway()
            await gateway.create_session(
                session_id=session_id,
                attempt_id=request.attempt_id,
                user_id=current_user_id,
                mode="full",
            )
            
        elif request.mode == "stt_only":
            # Flux STT mode
            flux_service = get_flux_stt_service()
            await flux_service.create_session(
                session_id=session_id,
                attempt_id=request.attempt_id,
                user_id=current_user_id,
                eot_threshold=request.eot_threshold,
                eager_eot_threshold=request.eager_eot_threshold,
                eot_timeout_ms=request.eot_timeout_ms,
            )
            
        elif request.mode == "tts_only":
            # TTS-only mode (handled via separate endpoint)
            pass
        else:
            raise HTTPException(status_code=400, detail=f"Invalid mode: {request.mode}")
        
        # Store session in database
        session_data = {
            'id': session_id,
            'attempt_id': request.attempt_id,
            'user_id': current_user_id,
            'mode': request.mode,
            'flux_config': {
                'eot_threshold': request.eot_threshold,
                'eager_eot_threshold': request.eager_eot_threshold,
                'eot_timeout_ms': request.eot_timeout_ms,
            } if request.mode == "stt_only" else None,
            'started_at': datetime.utcnow().isoformat(),
        }
        
        supabase.table('voice_sessions').insert(session_data).execute()
        
        logger.info(f"Created voice session {session_id} in {request.mode} mode")
        
        return VoiceSessionResponse(
            session_id=session_id,
            attempt_id=request.attempt_id,
            mode=request.mode,
            status="created",
            websocket_url=f"/api/voice/ws/{session_id}",
            created_at=datetime.utcnow().isoformat(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating voice session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create voice session")


@router.get("/sessions/{session_id}", response_model=VoiceSessionStatusResponse)
async def get_session_status(
    session_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """Get status of a voice session"""
    try:
        # Check database for session info
        supabase = get_supabase_client()
        session_result = supabase.table('voice_sessions').select('*').eq(
            'id', session_id
        ).maybe_single().execute()
        
        if not session_result.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = session_result.data
        
        if session_data['user_id'] != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Get live state if session is active
        mode = session_data.get('mode', 'stt_only')
        status = "unknown"
        transcript_count = 0
        current_transcript = None
        
        if mode == "full":
            gateway = get_voice_gateway()
            state = gateway.get_session_state(session_id)
            if state:
                status = state.status
                transcript_count = len(state.transcript)
                current_transcript = state.transcript[-1].text if state.transcript else None
        elif mode == "stt_only":
            flux_service = get_flux_stt_service()
            state = flux_service.get_session_state(session_id)
            if state:
                status = state.status
                transcript_count = len(state.transcript_entries)
                current_transcript = state.current_transcript
        
        # Fall back to database status if session is closed
        if status == "unknown":
            status = session_data.get('status', 'closed')
            transcript_count = len(session_data.get('transcript', []))
        
        return VoiceSessionStatusResponse(
            session_id=session_id,
            attempt_id=session_data['attempt_id'],
            mode=mode,
            status=status,
            transcript_count=transcript_count,
            current_transcript=current_transcript,
            started_at=session_data.get('started_at'),
            last_activity_at=session_data.get('ended_at'),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session status")


@router.get("/sessions/{session_id}/transcript", response_model=VoiceTranscriptResponse)
async def get_session_transcript(
    session_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """Get transcript for a voice session"""
    try:
        supabase = get_supabase_client()
        session_result = supabase.table('voice_sessions').select('*').eq(
            'id', session_id
        ).maybe_single().execute()
        
        if not session_result.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = session_result.data
        
        if session_data['user_id'] != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        mode = session_data.get('mode', 'stt_only')
        transcript = []
        full_text = ""
        word_count = 0
        
        # Get live transcript if session is active
        if mode == "full":
            gateway = get_voice_gateway()
            transcript = gateway.get_session_transcript(session_id)
            full_text = " ".join(t.get("text", "") for t in transcript)
        elif mode == "stt_only":
            flux_service = get_flux_stt_service()
            full_text = flux_service.get_full_transcript(session_id)
            state = flux_service.get_session_state(session_id)
            if state:
                transcript = [e.to_dict() for e in state.transcript_entries]
                word_count = state.word_count
        
        # Fall back to database transcript
        if not transcript:
            transcript = session_data.get('transcript', [])
            full_text = " ".join(t.get("text", "") for t in transcript)
            word_count = sum(len(t.get("text", "").split()) for t in transcript)
        
        return VoiceTranscriptResponse(
            session_id=session_id,
            transcript=transcript,
            full_text=full_text,
            word_count=word_count,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcript: {e}")
        raise HTTPException(status_code=500, detail="Failed to get transcript")


@router.post("/sessions/{session_id}/end", response_model=VoiceAnalysisResponse)
async def end_voice_session(
    session_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    End a voice session and get full analysis.
    
    Returns speech analysis including:
    - Full transcript
    - Timing metrics (pauses, speaking rate)
    - Fluency and engagement scores
    - Areas for improvement
    """
    try:
        supabase = get_supabase_client()
        session_result = supabase.table('voice_sessions').select('*').eq(
            'id', session_id
        ).maybe_single().execute()
        
        if not session_result.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = session_result.data
        
        if session_data['user_id'] != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        mode = session_data.get('mode', 'stt_only')
        analysis = None
        
        # Close session and get analysis
        if mode == "full":
            gateway = get_voice_gateway()
            analysis = await gateway.close_session(session_id)
        elif mode == "stt_only":
            flux_service = get_flux_stt_service()
            analysis = await flux_service.close_session(session_id)
        
        if not analysis:
            # Session already closed, return stored data
            analysis = {
                "session_id": session_id,
                "attempt_id": session_data['attempt_id'],
                "mode": mode,
                "duration_ms": session_data.get('duration_seconds', 0) * 1000,
                "transcript": session_data.get('transcript', []),
                "metrics": session_data.get('metrics', {}),
                "speech_analysis": session_data.get('speech_analysis'),
            }
        
        # Update database with final analysis
        update_data = {
            'ended_at': datetime.utcnow().isoformat(),
            'transcript': analysis.get('transcript', []),
            'metrics': analysis.get('metrics', {}),
            'speech_analysis': analysis.get('speech_analysis'),
            'duration_seconds': analysis.get('duration_ms', 0) // 1000,
        }
        
        supabase.table('voice_sessions').update(update_data).eq('id', session_id).execute()
        
        logger.info(f"Ended voice session {session_id}")
        
        return VoiceAnalysisResponse(
            session_id=session_id,
            attempt_id=session_data['attempt_id'],
            mode=mode,
            duration_ms=analysis.get('duration_ms', 0),
            transcript=analysis.get('transcript', []),
            full_text=" ".join(t.get("text", "") for t in analysis.get('transcript', [])),
            metrics=analysis.get('metrics', {}),
            speech_analysis=analysis.get('speech_analysis'),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending voice session: {e}")
        raise HTTPException(status_code=500, detail="Failed to end voice session")


@router.websocket("/ws/{session_id}")
async def voice_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for real-time voice streaming.
    
    Protocol:
    - Client sends binary audio data (linear16, 16kHz or 24kHz)
    - Server sends JSON messages for transcripts and state changes
    - Server sends binary audio for TTS responses (full mode only)
    
    Client messages:
    - Binary: Audio data chunks (~80ms recommended)
    - JSON: {"type": "config", ...} for configuration
    - JSON: {"type": "keepalive"} for keep-alive
    
    Server messages:
    - {"type": "connected", "session_id": ...}
    - {"type": "transcript", "text": ..., "is_final": ..., ...}
    - {"type": "speech_final", "text": ..., "turn": ...}
    - {"type": "state_change", "from": ..., "to": ...}
    - {"type": "metrics", "data": {...}}
    - {"type": "error", "message": ...}
    - Binary: TTS audio response
    """
    await websocket.accept()
    
    try:
        # Get session info from database
        supabase = get_supabase_client()
        session_result = supabase.table('voice_sessions').select('*').eq(
            'id', session_id
        ).maybe_single().execute()
        
        if not session_result.data:
            await websocket.send_json({"type": "error", "message": "Session not found"})
            await websocket.close()
            return
        
        session_data = session_result.data
        mode = session_data.get('mode', 'stt_only')
        
        # Set up callbacks for real-time updates
        async def on_transcript(data):
            await websocket.send_json({"type": "transcript", **data})
        
        async def on_speech_final(text, turn):
            await websocket.send_json({
                "type": "speech_final",
                "text": text,
                "turn": turn,
            })
        
        async def on_state_change(old_state, new_state):
            await websocket.send_json({
                "type": "state_change",
                "from": old_state,
                "to": new_state,
            })
        
        async def on_audio(data):
            await websocket.send_bytes(data)
        
        async def on_metrics(data):
            await websocket.send_json({"type": "metrics", "data": data})
        
        # Connect to appropriate service
        if mode == "full":
            gateway = get_voice_gateway()
            # Update callbacks
            gateway.callbacks[session_id] = {
                "on_transcript": lambda d: asyncio.create_task(on_transcript(d)),
                "on_audio": lambda d: asyncio.create_task(on_audio(d)),
                "on_metrics": lambda d: asyncio.create_task(on_metrics(d)),
                "on_state_change": lambda o, n: asyncio.create_task(on_state_change(o, n)),
            }
            
            # Connect to Deepgram
            persona_config = session_data.get('persona_config')
            connected = await gateway.connect_session(session_id, persona_config)
            
            if not connected:
                await websocket.send_json({"type": "error", "message": "Failed to connect to voice agent"})
                await websocket.close()
                return
                
        elif mode == "stt_only":
            flux_service = get_flux_stt_service()
            # Update callbacks
            flux_service.callbacks[session_id] = {
                "on_transcript": lambda d: asyncio.create_task(on_transcript(d)),
                "on_speech_final": lambda t, n: asyncio.create_task(on_speech_final(t, n)),
                "on_state_change": lambda o, n: asyncio.create_task(on_state_change(o, n)),
            }
            
            # Connect to Flux
            connected = await flux_service.connect_session(session_id)
            
            if not connected:
                await websocket.send_json({"type": "error", "message": "Failed to connect to Flux STT"})
                await websocket.close()
                return
        
        # Send connected confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "mode": mode,
        })
        
        # Main message loop
        while True:
            message = await websocket.receive()
            
            if "bytes" in message:
                # Audio data
                audio_data = message["bytes"]
                
                if mode == "full":
                    await gateway.send_audio(session_id, audio_data)
                elif mode == "stt_only":
                    await flux_service.send_audio(session_id, audio_data)
                    
            elif "text" in message:
                # JSON message
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")
                    
                    if msg_type == "keepalive":
                        if mode == "full":
                            await gateway.send_keep_alive(session_id)
                        # Flux handles keep-alive automatically
                        
                    elif msg_type == "config":
                        # Handle configuration updates
                        logger.info(f"Received config update for session {session_id}")
                        
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON message for session {session_id}")
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        # Don't close the session - let the client explicitly end it
        pass


@router.get("/sessions")
async def list_voice_sessions(
    attempt_id: Optional[str] = Query(None, description="Filter by attempt ID"),
    current_user_id: str = Depends(get_current_user)
):
    """List voice sessions for the current user"""
    try:
        supabase = get_supabase_client()
        
        query = supabase.table('voice_sessions').select('*').eq('user_id', current_user_id)
        
        if attempt_id:
            query = query.eq('attempt_id', attempt_id)
        
        result = query.order('started_at', desc=True).limit(50).execute()
        
        return {
            "sessions": result.data or [],
            "count": len(result.data or []),
        }
        
    except Exception as e:
        logger.error(f"Error listing voice sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to list sessions")
