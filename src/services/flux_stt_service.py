"""
Flux STT Service - Conversational Speech Recognition

Deepgram Flux is built specifically for voice agents with:
- Smart turn detection (~260ms end-of-turn detection)
- Early LLM responses via EagerEndOfTurn events
- Natural interruption handling (barge-in)
- Nova-3 level accuracy

This service provides STT-only functionality for scenarios
that need speech input but use custom response generation.

Updated for Deepgram SDK v3 API
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# Deepgram SDK v3 imports
try:
    from deepgram import DeepgramClient
    from deepgram.clients.listen.v1.websocket import (
        AsyncListenWebSocketClient,
        ListenWebSocketOptions,
        LiveOptions,
        OpenResponse,
        WelcomeResponse,
    )
    from deepgram.clients.listen.v1.websocket.response import (
        LiveResultResponse,
        SpeechStartedResponse,
        UtteranceEndResponse,
    )
    DEEPGRAM_AVAILABLE = True
except ImportError as e:
    DEEPGRAM_AVAILABLE = False
    DeepgramClient = None
    AsyncListenWebSocketClient = None
    ListenWebSocketOptions = None
    LiveOptions = None
    logging.warning(f"Deepgram SDK not available: {e}")

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

    Updated for Deepgram SDK v3 API
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not DEEPGRAM_AVAILABLE:
            logger.warning("Deepgram SDK not available - Flux STT features will be disabled")
            self.client = None
        elif not self.api_key:
            logger.warning("DEEPGRAM_API_KEY not set - Flux STT features will be disabled")
            self.client = None
        else:
            try:
                self.client = DeepgramClient(api_key=self.api_key)
                logger.info("Deepgram client initialized successfully")
            except Exception as e:
                logger.warning(f"Deepgram client initialization failed: {e}")
                self.client = None

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
        """Create a new Flux STT session"""
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
        state.flux_config = {
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
        """Connect a session to Deepgram Flux using v3 API"""
        # Check if Deepgram client is available
        if not self.client:
            logger.error("Deepgram client not initialized - check DEEPGRAM_API_KEY")
            state = self.sessions.get(session_id)
            if state:
                state.error = "Deepgram SDK not available"
                self._update_state(session_id, "error")
            return False

        state = self.sessions.get(session_id)
        if not state:
            logger.error(f"Session {session_id} not found")
            return False

        try:
            self._update_state(session_id, "connecting")

            # Get Flux configuration
            flux_config = getattr(state, 'flux_config', {})

            # Build live options for Deepgram v3
            options = ListenWebSocketOptions(
                live_options=LiveOptions(
                    model="nova-3",
                    language="en-US",
                    # Add Flux-specific options
                    smart_format=True,
                    interim_results=True,
                    vad_events=True,
                )
            )

            # Create async websocket client (v3 API)
            deepgram_live = self.client.listen.websocket.v("1")
            connection = deepgram_live("async_client")

            # Register event handlers
            connection.on(LiveResultResponse, self._create_result_handler(session_id))
            connection.on(SpeechStartedResponse, self._create_speech_started_handler(session_id))
            connection.on(UtteranceEndResponse, self._create_utterance_end_handler(session_id))

            # Start the connection
            await connection.start(options)

            self.connections[session_id] = {
                "connection": connection,
            }

            self._update_state(session_id, "connected")
            logger.info(f"Flux STT session {session_id} connected to Deepgram v3")
            return True

        except Exception as e:
            logger.error(f"Failed to connect Flux session {session_id}: {e}")
            state.error = str(e)
            self._update_state(session_id, "error")
            return False

    def _create_result_handler(self, session_id: str):
        """Create handler for live transcription results"""
        async def handle_result(result: LiveResultResponse, **kwargs):
            self._handle_transcript_result(session_id, result)
        return handle_result

    def _create_speech_started_handler(self, session_id: str):
        """Create handler for speech started events"""
        async def handle_speech_started(result: SpeechStartedResponse, **kwargs):
            logger.debug(f"Speech started for session {session_id}")
        return handle_speech_started

    def _create_utterance_end_handler(self, session_id: str):
        """Create handler for utterance end events"""
        async def handle_utterance_end(result: UtteranceEndResponse, **kwargs):
            state = self.sessions.get(session_id)
            if state:
                state.turn_count += 1
                callbacks = self.callbacks.get(session_id, {})
                if callbacks.get("on_speech_final"):
                    await callbacks["on_speech_final"](state.full_transcript, state.turn_count)
                # Reset for next turn
                state.full_transcript = ""
        return handle_utterance_end

    def _handle_transcript_result(self, session_id: str, result: LiveResultResponse):
        """Handle live transcription result from Deepgram v3"""
        state = self.sessions.get(session_id)
        if not state:
            return

        # Update last activity
        state.last_activity_at = datetime.utcnow().isoformat()

        # Extract transcript
        if not hasattr(result, 'channel') or not result.channel:
            return

        channel = result.channel
        if hasattr(channel, 'alternatives') and channel.alternatives:
            alternative = channel.alternatives[0]
            transcript_text = alternative.transcript if hasattr(alternative, 'transcript') else ""
            is_final = result.is_final if hasattr(result, 'is_final') else False

            # Extract words if available
            words = []
            if hasattr(alternative, 'words') and alternative.words:
                for word_data in alternative.words:
                    words.append(FluxTranscriptWord(
                        word=word_data.word if hasattr(word_data, 'word') else "",
                        start_time=word_data.start if hasattr(word_data, 'start') else 0.0,
                        end_time=word_data.end if hasattr(word_data, 'end') else 0.0,
                        confidence=word_data.confidence if hasattr(word_data, 'confidence') else 0.0,
                    ))

            # Calculate confidence
            confidence = 0.0
            if words:
                confidence = sum(w.confidence for w in words) / len(words)
            elif hasattr(alternative, 'confidence'):
                confidence = alternative.confidence

            # Create entry
            entry = FluxTranscriptEntry(
                text=transcript_text,
                words=words,
                confidence=confidence,
                is_final=is_final,
                speech_final=False,  # Will be set by utterance end event
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
                asyncio.create_task(callbacks["on_transcript"](entry.to_dict()))

    async def send_audio(self, session_id: str, audio_data: bytes) -> bool:
        """Send audio data to Flux"""
        conn_info = self.connections.get(session_id)
        if not conn_info:
            logger.error(f"No connection for Flux session {session_id}")
            return False

        try:
            connection = conn_info["connection"]
            await connection.send(audio_data)
            return True
        except Exception as e:
            logger.error(f"Failed to send audio for Flux session {session_id}: {e}")
            return False

    async def close_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Close a Flux STT session and return analysis"""
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

    def _update_state(self, session_id: str, new_status: str):
        """Update session state and notify callback"""
        state = self.sessions.get(session_id)
        if not state:
            return

        old_status = state.status
        state.status = new_status

        callbacks = self.callbacks.get(session_id, {})
        if callbacks.get("on_state_change"):
            asyncio.create_task(callbacks["on_state_change"](old_status, new_status))

        logger.debug(f"Flux session {session_id} state: {old_status} -> {new_status}")

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


def get_flux_stt_service() -> Optional[FluxSTTService]:
    """Get or create the singleton FluxSTTService (returns None if Deepgram unavailable)"""
    global _flux_stt_service
    if _flux_stt_service is None:
        try:
            _flux_stt_service = FluxSTTService()
        except Exception as e:
            logger.warning(f"Failed to initialize FluxSTTService: {e}")
            return None
    return _flux_stt_service
