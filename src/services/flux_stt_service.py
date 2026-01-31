"""
Flux STT Service - Conversational Speech Recognition

Deepgram Flux is built specifically for voice agents with:
- Smart turn detection (~260ms end-of-turn detection)
- Early LLM responses via EagerEndOfTurn events
- Natural interruption handling (barge-in)
- Nova-3 level accuracy

This service provides STT-only functionality for scenarios
that need speech input but use custom response generation.
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from deepgram.extensions.types.sockets import ListenV2SocketClientResponse

logger = logging.getLogger(__name__)


@dataclass
class FluxTranscriptWord:
    """Individual word with confidence and timing"""
    word: str
    start_time: float
    end_time: float
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "word": self.word,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "confidence": self.confidence,
        }


@dataclass
class FluxTranscriptEntry:
    """A complete transcript segment"""
    text: str
    words: List[FluxTranscriptWord]
    confidence: float
    is_final: bool
    speech_final: bool  # True when end-of-turn detected
    timestamp: str
    start_time: float = 0.0
    end_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "words": [w.to_dict() for w in self.words],
            "confidence": self.confidence,
            "is_final": self.is_final,
            "speech_final": self.speech_final,
            "timestamp": self.timestamp,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }


@dataclass
class FluxSessionState:
    """State tracking for a Flux STT session"""
    session_id: str
    attempt_id: str
    user_id: str
    status: str = "initializing"  # initializing, connected, listening, processing, closed, error
    transcript_entries: List[FluxTranscriptEntry] = field(default_factory=list)
    current_transcript: str = ""
    full_transcript: str = ""
    started_at: Optional[str] = None
    last_activity_at: Optional[str] = None
    error: Optional[str] = None
    
    # Speech analysis metrics
    total_speech_time_ms: int = 0
    total_pause_time_ms: int = 0
    pause_count: int = 0
    word_count: int = 0
    average_confidence: float = 0.0
    turn_count: int = 0
    
    # Flux-specific metrics
    eager_eot_triggered: int = 0  # Early end-of-turn triggers
    turn_resumed_count: int = 0  # User continued after EagerEndOfTurn


class FluxSTTService:
    """
    Flux Speech-to-Text service for conversational recognition.
    
    Provides:
    - Real-time streaming transcription
    - Configurable end-of-turn detection
    - EagerEndOfTurn for early response preparation
    - Speech analysis metrics
    
    Use this for scenarios that need:
    - Custom LLM processing (not using Deepgram's Voice Agent think)
    - Text augmentation (adding voice input to text scenarios)
    - Detailed speech timing analysis
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY environment variable is not set")
        
        self.sessions: Dict[str, FluxSessionState] = {}
        self.connections: Dict[str, Any] = {}
        self.callbacks: Dict[str, Dict[str, Callable]] = {}
        
        logger.info("FluxSTTService initialized")
    
    async def create_session(
        self,
        session_id: str,
        attempt_id: str,
        user_id: str,
        eot_threshold: float = 0.7,
        eager_eot_threshold: Optional[float] = None,
        eot_timeout_ms: int = 5000,
        on_transcript: Optional[Callable] = None,
        on_speech_final: Optional[Callable] = None,
        on_eager_eot: Optional[Callable] = None,
        on_state_change: Optional[Callable] = None,
    ) -> FluxSessionState:
        """
        Create a new Flux STT session.
        
        Args:
            session_id: Unique session identifier
            attempt_id: Scenario attempt ID
            user_id: User ID
            eot_threshold: End-of-turn confidence threshold (0.5-0.9, default 0.7)
            eager_eot_threshold: Early end-of-turn threshold (0.3-0.9, optional)
            eot_timeout_ms: Max silence before forced end-of-turn (500-10000ms)
            on_transcript: Callback for interim transcripts
            on_speech_final: Callback when turn is complete
            on_eager_eot: Callback for early end-of-turn (prepare response)
            on_state_change: Callback for state changes
        
        Returns:
            FluxSessionState: The created session state
        """
        state = FluxSessionState(
            session_id=session_id,
            attempt_id=attempt_id,
            user_id=user_id,
            started_at=datetime.utcnow().isoformat(),
        )
        self.sessions[session_id] = state
        
        # Store callbacks
        self.callbacks[session_id] = {
            "on_transcript": on_transcript,
            "on_speech_final": on_speech_final,
            "on_eager_eot": on_eager_eot,
            "on_state_change": on_state_change,
        }
        
        # Store Flux configuration
        self.sessions[session_id].flux_config = {
            "eot_threshold": eot_threshold,
            "eager_eot_threshold": eager_eot_threshold,
            "eot_timeout_ms": eot_timeout_ms,
        }
        
        logger.info(f"Created Flux STT session {session_id}")
        return state
    
    async def connect_session(
        self,
        session_id: str,
        sample_rate: int = 16000,
    ) -> bool:
        """
        Connect a session to Deepgram Flux.
        
        Args:
            session_id: Session ID to connect
            sample_rate: Audio sample rate (16000 recommended)
        
        Returns:
            bool: True if connection successful
        """
        state = self.sessions.get(session_id)
        if not state:
            logger.error(f"Session {session_id} not found")
            return False
        
        try:
            self._update_state(session_id, "connecting")
            
            # Create async client
            client = AsyncDeepgramClient(api_key=self.api_key)
            
            # Get Flux configuration
            flux_config = getattr(state, 'flux_config', {})
            
            # Build connection parameters
            connect_params = {
                "model": "flux-general-en",
                "encoding": "linear16",
                "sample_rate": str(sample_rate),
            }
            
            # Add Flux-specific parameters
            if flux_config.get("eot_threshold"):
                connect_params["eot_threshold"] = str(flux_config["eot_threshold"])
            if flux_config.get("eager_eot_threshold"):
                connect_params["eager_eot_threshold"] = str(flux_config["eager_eot_threshold"])
            if flux_config.get("eot_timeout_ms"):
                connect_params["eot_timeout_ms"] = str(flux_config["eot_timeout_ms"])
            
            # Connect to Flux (v2 endpoint)
            connection = await client.listen.v2.connect(**connect_params)
            self.connections[session_id] = {
                "connection": connection,
                "client": client,
            }
            
            # Set up event handlers
            self._setup_event_handlers(session_id, connection)
            
            # Start listening task
            asyncio.create_task(connection.start_listening())
            
            self._update_state(session_id, "connected")
            logger.info(f"Flux STT session {session_id} connected")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect Flux session {session_id}: {e}")
            state.error = str(e)
            self._update_state(session_id, "error")
            return False
    
    def _setup_event_handlers(self, session_id: str, connection):
        """Set up event handlers for Flux connection"""
        
        def on_open(event):
            logger.info(f"Flux session {session_id} connection opened")
            self._update_state(session_id, "listening")
        
        def on_message(message: ListenV2SocketClientResponse):
            self._handle_message(session_id, message)
        
        def on_error(error):
            logger.error(f"Flux session {session_id} error: {error}")
            state = self.sessions.get(session_id)
            if state:
                state.error = str(error)
                self._update_state(session_id, "error")
        
        def on_close(event):
            logger.info(f"Flux session {session_id} connection closed")
            self._update_state(session_id, "closed")
        
        connection.on(EventType.OPEN, on_open)
        connection.on(EventType.MESSAGE, on_message)
        connection.on(EventType.ERROR, on_error)
        connection.on(EventType.CLOSE, on_close)
    
    def _handle_message(self, session_id: str, message: ListenV2SocketClientResponse):
        """Handle incoming messages from Flux"""
        state = self.sessions.get(session_id)
        if not state:
            return
        
        # Update last activity
        state.last_activity_at = datetime.utcnow().isoformat()
        
        msg_type = getattr(message, "type", "Unknown")
        
        if msg_type == "Connected":
            logger.info(f"Flux session {session_id} connected to Deepgram")
            return
        
        # Handle transcript results
        if hasattr(message, 'transcript') and message.transcript:
            self._handle_transcript(session_id, message)
        
        # Handle Flux-specific events
        elif msg_type == "EndOfTurn":
            self._handle_end_of_turn(session_id, message)
        
        elif msg_type == "EagerEndOfTurn":
            self._handle_eager_end_of_turn(session_id, message)
        
        elif msg_type == "TurnResumed":
            self._handle_turn_resumed(session_id, message)
    
    def _handle_transcript(self, session_id: str, message):
        """Handle transcript message"""
        state = self.sessions.get(session_id)
        if not state:
            return
        
        transcript_text = message.transcript
        is_final = getattr(message, 'is_final', False)
        speech_final = getattr(message, 'speech_final', False)
        
        # Extract word-level information
        words = []
        if hasattr(message, 'words') and message.words:
            for word_data in message.words:
                words.append(FluxTranscriptWord(
                    word=word_data.word,
                    start_time=word_data.start,
                    end_time=word_data.end,
                    confidence=word_data.confidence,
                ))
        
        # Calculate confidence
        confidence = 0.0
        if words:
            confidence = sum(w.confidence for w in words) / len(words)
        
        # Create entry
        entry = FluxTranscriptEntry(
            text=transcript_text,
            words=words,
            confidence=confidence,
            is_final=is_final,
            speech_final=speech_final,
            timestamp=datetime.utcnow().isoformat(),
        )
        
        # Update state
        state.current_transcript = transcript_text
        
        if is_final:
            state.transcript_entries.append(entry)
            state.full_transcript += " " + transcript_text
            state.full_transcript = state.full_transcript.strip()
            state.word_count += len(words)
            
            # Update confidence average
            if state.word_count > 0:
                total_conf = sum(w.confidence for e in state.transcript_entries for w in e.words)
                state.average_confidence = total_conf / state.word_count
        
        # Notify callbacks
        callbacks = self.callbacks.get(session_id, {})
        if callbacks.get("on_transcript"):
            callbacks["on_transcript"](entry.to_dict())
        
        if speech_final:
            state.turn_count += 1
            if callbacks.get("on_speech_final"):
                callbacks["on_speech_final"](state.full_transcript, state.turn_count)
            # Reset for next turn
            state.full_transcript = ""
    
    def _handle_end_of_turn(self, session_id: str, message):
        """Handle confirmed end-of-turn"""
        state = self.sessions.get(session_id)
        if not state:
            return
        
        state.turn_count += 1
        logger.info(f"Flux session {session_id}: End of turn {state.turn_count}")
        
        callbacks = self.callbacks.get(session_id, {})
        if callbacks.get("on_speech_final"):
            callbacks["on_speech_final"](state.full_transcript, state.turn_count)
    
    def _handle_eager_end_of_turn(self, session_id: str, message):
        """Handle early end-of-turn (start preparing response)"""
        state = self.sessions.get(session_id)
        if not state:
            return
        
        state.eager_eot_triggered += 1
        logger.info(f"Flux session {session_id}: Eager end-of-turn triggered")
        
        callbacks = self.callbacks.get(session_id, {})
        if callbacks.get("on_eager_eot"):
            callbacks["on_eager_eot"](state.current_transcript)
    
    def _handle_turn_resumed(self, session_id: str, message):
        """Handle user continued speaking after EagerEndOfTurn"""
        state = self.sessions.get(session_id)
        if not state:
            return
        
        state.turn_resumed_count += 1
        logger.info(f"Flux session {session_id}: Turn resumed (cancel draft response)")
    
    def _update_state(self, session_id: str, new_status: str):
        """Update session state and notify callback"""
        state = self.sessions.get(session_id)
        if not state:
            return
        
        old_status = state.status
        state.status = new_status
        
        callbacks = self.callbacks.get(session_id, {})
        if callbacks.get("on_state_change"):
            callbacks["on_state_change"](old_status, new_status)
        
        logger.debug(f"Flux session {session_id} state: {old_status} -> {new_status}")
    
    async def send_audio(self, session_id: str, audio_data: bytes) -> bool:
        """
        Send audio data to Flux.
        
        Args:
            session_id: Session ID
            audio_data: Raw audio bytes (linear16, ~80ms chunks recommended)
        
        Returns:
            bool: True if sent successfully
        """
        conn_info = self.connections.get(session_id)
        if not conn_info:
            logger.error(f"No connection for Flux session {session_id}")
            return False
        
        try:
            connection = conn_info["connection"]
            await connection._send(audio_data)
            return True
        except Exception as e:
            logger.error(f"Failed to send audio for Flux session {session_id}: {e}")
            return False
    
    async def close_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Close a Flux STT session and return analysis.
        
        Args:
            session_id: Session ID to close
        
        Returns:
            Dict containing transcript and analysis
        """
        state = self.sessions.get(session_id)
        if not state:
            return None
        
        # Close connection
        conn_info = self.connections.get(session_id)
        if conn_info:
            try:
                connection = conn_info["connection"]
                await connection.finish()
            except Exception as e:
                logger.error(f"Error closing Flux connection {session_id}: {e}")
        
        # Build analysis result
        analysis = {
            "session_id": session_id,
            "attempt_id": state.attempt_id,
            "user_id": state.user_id,
            "started_at": state.started_at,
            "ended_at": datetime.utcnow().isoformat(),
            "transcript_entries": [e.to_dict() for e in state.transcript_entries],
            "full_transcript": " ".join(e.text for e in state.transcript_entries),
            "metrics": {
                "word_count": state.word_count,
                "turn_count": state.turn_count,
                "average_confidence": state.average_confidence,
                "eager_eot_triggered": state.eager_eot_triggered,
                "turn_resumed_count": state.turn_resumed_count,
            },
        }
        
        # Cleanup
        self._update_state(session_id, "closed")
        del self.sessions[session_id]
        if session_id in self.connections:
            del self.connections[session_id]
        if session_id in self.callbacks:
            del self.callbacks[session_id]
        
        logger.info(f"Closed Flux STT session {session_id}")
        return analysis
    
    def get_session_state(self, session_id: str) -> Optional[FluxSessionState]:
        """Get current state of a Flux session"""
        return self.sessions.get(session_id)
    
    def get_current_transcript(self, session_id: str) -> str:
        """Get current (interim) transcript"""
        state = self.sessions.get(session_id)
        return state.current_transcript if state else ""
    
    def get_full_transcript(self, session_id: str) -> str:
        """Get full (final) transcript so far"""
        state = self.sessions.get(session_id)
        if not state:
            return ""
        return " ".join(e.text for e in state.transcript_entries)


# Singleton instance
_flux_stt_service: Optional[FluxSTTService] = None


def get_flux_stt_service() -> FluxSTTService:
    """Get or create the singleton FluxSTTService"""
    global _flux_stt_service
    if _flux_stt_service is None:
        _flux_stt_service = FluxSTTService()
    return _flux_stt_service
