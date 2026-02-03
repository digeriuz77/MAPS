"""
Voice Gateway Service - Deepgram Voice Agent Integration

This service provides real-time bidirectional voice communication using
Deepgram's Voice Agent API. It supports:
- Full voice agent mode (STT + TTS + LLM)
- Optional TTS/STT to augment text-based interaction
- Voice-driven scenarios with speech analysis

Updated for Deepgram SDK v3 API
"""

import asyncio
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# Deepgram SDK v3 imports
try:
    from deepgram import DeepgramClient
    from deepgram.clients.agent.v1.websocket import (
        AgentWebSocketClient,
        SettingsConfigurationOptions,
    )
    from deepgram.clients.agent.v1.websocket.response import (
        WelcomeResponse,
        SettingsAppliedResponse,
        ConversationTextResponse,
        UserStartedSpeakingResponse,
        AgentStartedSpeakingResponse,
        AgentThinkingResponse,
        AgentAudioDoneResponse,
    )
    DEEPGRAM_AVAILABLE = True
except ImportError as e:
    DEEPGRAM_AVAILABLE = False
    DeepgramClient = None
    AgentWebSocketClient = None
    logging.warning(f"Deepgram SDK not available: {e}")

logger = logging.getLogger(__name__)


@dataclass
class VoiceMetrics:
    """Speech analysis metrics from a voice session"""
    total_speaking_time_ms: int = 0
    total_pauses_ms: int = 0
    pause_count: int = 0
    average_pause_duration_ms: float = 0.0
    longest_pause_ms: int = 0
    words_per_minute: float = 0.0
    hesitation_count: int = 0  # "um", "uh", etc.
    interruption_count: int = 0
    turn_count: int = 0
    confidence_scores: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_speaking_time_ms": self.total_speaking_time_ms,
            "total_pauses_ms": self.total_pauses_ms,
            "pause_count": self.pause_count,
            "average_pause_duration_ms": self.average_pause_duration_ms,
            "longest_pause_ms": self.longest_pause_ms,
            "words_per_minute": self.words_per_minute,
            "hesitation_count": self.hesitation_count,
            "interruption_count": self.interruption_count,
            "turn_count": self.turn_count,
            "average_confidence": sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 0.0
        }


@dataclass
class VoiceTranscriptEntry:
    """Single entry in a voice transcript"""
    role: str  # "user" or "agent"
    text: str
    timestamp: str
    start_time_ms: int = 0
    duration_ms: int = 0
    confidence: float = 0.0
    words: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "text": self.text,
            "timestamp": self.timestamp,
            "start_time_ms": self.start_time_ms,
            "duration_ms": self.duration_ms,
            "confidence": self.confidence,
            "words": self.words
        }


@dataclass
class VoiceSessionState:
    """Current state of a voice session"""
    session_id: str
    attempt_id: str
    user_id: str
    status: str = "initializing"  # initializing, connected, listening, processing, speaking, closed, error
    mode: str = "full"  # "full" (Voice Agent), "stt_only", "tts_only"
    transcript: List[VoiceTranscriptEntry] = field(default_factory=list)
    metrics: VoiceMetrics = field(default_factory=VoiceMetrics)
    audio_buffer: bytearray = field(default_factory=bytearray)
    started_at: Optional[str] = None
    last_activity_at: Optional[str] = None
    error: Optional[str] = None

    # Timing for pause analysis
    last_speech_end_ms: int = 0
    current_speech_start_ms: int = 0
    session_start_ms: int = 0


class VoiceGateway:
    """
    Gateway service for Deepgram Voice Agent integration.

    Updated for Deepgram SDK v3 API
    """

    # Session timeout configuration
    SESSION_TIMEOUT_SECONDS = 300  # 5 minutes of inactivity
    SESSION_MAX_AGE_SECONDS = 3600  # 1 hour absolute maximum
    CLEANUP_INTERVAL_SECONDS = 60  # Check for expired sessions every minute

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not DEEPGRAM_AVAILABLE:
            logger.warning("Deepgram SDK not available - voice features will be disabled")
            self.client = None
        elif not self.api_key:
            logger.warning("DEEPGRAM_API_KEY not set - voice features will be disabled")
            self.client = None
        else:
            try:
                self.client = DeepgramClient(api_key=self.api_key)
                logger.info("Deepgram client initialized successfully")
            except Exception as e:
                logger.warning(f"Deepgram client initialization failed: {e}")
                self.client = None

        self.sessions: Dict[str, VoiceSessionState] = {}
        self.connections: Dict[str, Any] = {}
        self.callbacks: Dict[str, Dict[str, Callable]] = {}
        self._cleanup_task = None
        self._shutdown = False

        # Hesitation words to detect
        self.hesitation_words = {"um", "uh", "er", "ah", "like", "you know", "actually", "basically"}

        logger.info("VoiceGateway initialized")

    async def start_cleanup_task(self):
        """Start the background session cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Session cleanup task started")

    async def _cleanup_loop(self):
        """Background loop to periodically clean up expired sessions"""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.CLEANUP_INTERVAL_SECONDS)
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_expired_sessions(self):
        """Remove expired sessions based on timeout and max age"""
        now = time.time()
        expired_sessions = []

        for session_id, state in self.sessions.items():
            # Check absolute max age
            session_age = now - (state.session_start_ms / 1000)
            if session_age > self.SESSION_MAX_AGE_SECONDS:
                expired_sessions.append(session_id)
                logger.info(f"Session {session_id} expired (max age: {session_age:.0f}s)")
                continue

            # Check inactivity timeout
            if state.last_activity_at:
                last_activity = datetime.fromisoformat(state.last_activity_at).timestamp()
                inactive_time = now - last_activity
                if inactive_time > self.SESSION_TIMEOUT_SECONDS:
                    expired_sessions.append(session_id)
                    logger.info(f"Session {session_id} expired (inactive: {inactive_time:.0f}s)")

        # Close expired sessions
        for session_id in expired_sessions:
            await self.close_session(session_id)

    async def close_session(self, session_id: str) -> bool:
        """Close a voice session and clean up resources"""
        logger.info(f"Closing voice session: {session_id}")

        # Close connection if exists
        connection = self.connections.pop(session_id, None)
        if connection:
            try:
                await connection.finish()
            except Exception as e:
                logger.warning(f"Error closing connection for {session_id}: {e}")

        # Remove session and callbacks
        self.sessions.pop(session_id, None)
        self.callbacks.pop(session_id, None)

        logger.info(f"Voice session {session_id} closed")
        return True

    async def shutdown(self):
        """Graceful shutdown - close all sessions"""
        logger.info("VoiceGateway shutdown initiated")
        self._shutdown = True

        # Stop cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Close all sessions
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self.close_session(session_id)

        logger.info("VoiceGateway shutdown complete")

    def _create_agent_settings(
        self,
        mode: str = "full",
        persona_prompt: str = "You are a friendly AI assistant.",
        persona_greeting: str = "Hello! How can I help you today?",
        listen_model: str = "nova-3",
        think_model: str = "gpt-4o-mini",
        speak_model: str = "aura-2-thalia-en",
        input_sample_rate: int = 24000,
        output_sample_rate: int = 24000,
    ) -> SettingsConfigurationOptions:
        """Create Voice Agent settings configuration (v3 API)"""
        # Build settings for Deepgram v3
        return SettingsConfigurationOptions(
            # Agent configuration
            agent={
                "listen": {
                    "model": listen_model,
                },
                "think": {
                    "provider": "openai",
                    "model": think_model,
                    "instructions": persona_prompt,
                },
                "speak": {
                    "provider": "deepgram",
                    "model": speak_model,
                },
                "greeting": persona_greeting,
            },
            # Audio configuration
            audio={
                "input": {
                    "encoding": "linear16",
                    "sample_rate": input_sample_rate,
                },
                "output": {
                    "encoding": "linear16",
                    "sample_rate": output_sample_rate,
                },
            },
        )

    async def create_session(
        self,
        session_id: str,
        attempt_id: str,
        user_id: str,
        mode: str = "full",
        persona_config: Optional[Dict[str, Any]] = None,
        on_transcript: Optional[Callable] = None,
        on_audio: Optional[Callable] = None,
        on_metrics: Optional[Callable] = None,
        on_state_change: Optional[Callable] = None,
    ) -> VoiceSessionState:
        """Create a new voice session"""
        # Create session state
        state = VoiceSessionState(
            session_id=session_id,
            attempt_id=attempt_id,
            user_id=user_id,
            mode=mode,
            started_at=datetime.utcnow().isoformat(),
            session_start_ms=int(time.time() * 1000),
        )
        self.sessions[session_id] = state

        # Store callbacks
        self.callbacks[session_id] = {
            "on_transcript": on_transcript,
            "on_audio": on_audio,
            "on_metrics": on_metrics,
            "on_state_change": on_state_change,
        }

        logger.info(f"Created voice session {session_id} in {mode} mode")
        return state

    async def connect_session(
        self,
        session_id: str,
        persona_config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Connect a session to Deepgram Voice Agent using v3 API"""
        # Check if Deepgram client is available
        if not self.client:
            logger.error("Deepgram client not initialized - check DEEPGRAM_API_KEY")
            return False

        state = self.sessions.get(session_id)
        if not state:
            logger.error(f"Session {session_id} not found")
            return False

        try:
            self._update_state(session_id, "connecting")

            # Create settings based on persona config
            persona_prompt = "You are a friendly AI assistant."
            persona_greeting = "Hello! How can I help you today?"

            if persona_config:
                persona_prompt = persona_config.get("personality", persona_prompt)
                name = persona_config.get("name", "Assistant")
                situation = persona_config.get("situation", "")
                persona_greeting = f"Hi, I'm {name}. {situation}"

            settings = self._create_agent_settings(
                mode=state.mode,
                persona_prompt=persona_prompt,
                persona_greeting=persona_greeting,
            )

            # Create async websocket client (v3 API)
            agent_ws = self.client.agent.websocket.v("1")
            connection = agent_ws("async_client")

            # Register event handlers for v3 API
            connection.on(WelcomeResponse, self._create_welcome_handler(session_id))
            connection.on(SettingsAppliedResponse, self._create_settings_handler(session_id))
            connection.on(ConversationTextResponse, self._create_conversation_handler(session_id))
            connection.on(UserStartedSpeakingResponse, self._create_user_speaking_handler(session_id))
            connection.on(AgentStartedSpeakingResponse, self._create_agent_speaking_handler(session_id))
            connection.on(AgentThinkingResponse, self._create_thinking_handler(session_id))
            connection.on(AgentAudioDoneResponse, self._create_audio_done_handler(session_id))

            # Start the connection with settings
            await connection.start(settings)

            self.connections[session_id] = {
                "connection": connection,
            }

            self._update_state(session_id, "connected")
            logger.info(f"Voice session {session_id} connected to Deepgram v3")
            return True

        except Exception as e:
            logger.error(f"Failed to connect voice session {session_id}: {e}")
            state.error = str(e)
            self._update_state(session_id, "error")
            return False

    def _create_welcome_handler(self, session_id: str):
        """Create handler for welcome messages"""
        async def handle_welcome(result: WelcomeResponse, **kwargs):
            logger.info(f"Voice session {session_id} received welcome")
        return handle_welcome

    def _create_settings_handler(self, session_id: str):
        """Create handler for settings applied"""
        async def handle_settings(result: SettingsAppliedResponse, **kwargs):
            logger.info(f"Voice session {session_id} settings applied")
            self._update_state(session_id, "listening")
        return handle_settings

    def _create_conversation_handler(self, session_id: str):
        """Create handler for conversation text"""
        async def handle_conversation(result: ConversationTextResponse, **kwargs):
            self._handle_conversation_text(session_id, result)
        return handle_conversation

    def _create_user_speaking_handler(self, session_id: str):
        """Create handler for user started speaking"""
        async def handle_user_speaking(result: UserStartedSpeakingResponse, **kwargs):
            self._handle_user_started_speaking(session_id)
        return handle_user_speaking

    def _create_agent_speaking_handler(self, session_id: str):
        """Create handler for agent started speaking"""
        async def handle_agent_speaking(result: AgentStartedSpeakingResponse, **kwargs):
            state = self.sessions.get(session_id)
            if state:
                state.audio_buffer = bytearray()  # Reset buffer
            self._update_state(session_id, "speaking")
        return handle_agent_speaking

    def _create_thinking_handler(self, session_id: str):
        """Create handler for agent thinking"""
        async def handle_thinking(result: AgentThinkingResponse, **kwargs):
            self._update_state(session_id, "processing")
        return handle_thinking

    def _create_audio_done_handler(self, session_id: str):
        """Create handler for agent audio done"""
        async def handle_audio_done(result: AgentAudioDoneResponse, **kwargs):
            self._handle_agent_audio_done(session_id)
            self._update_state(session_id, "listening")
        return handle_audio_done

    def _handle_conversation_text(self, session_id: str, result: ConversationTextResponse):
        """Handle transcription text from Voice Agent"""
        state = self.sessions.get(session_id)
        if not state:
            return

        current_time_ms = int(time.time() * 1000)

        # Extract transcript info from v3 API response
        role = getattr(result, 'role', 'user')
        content = getattr(result, 'content', '')
        text = content if isinstance(content, str) else str(content)

        # Check for hesitations
        hesitation_count = 0
        for word in self.hesitation_words:
            hesitation_count += text.lower().count(word)
        state.metrics.hesitation_count += hesitation_count

        # Calculate pause if this is user speech
        if role == "user" and state.last_speech_end_ms > 0:
            pause_ms = state.current_speech_start_ms - state.last_speech_end_ms
            if pause_ms > 100:  # Only count pauses > 100ms
                state.metrics.pause_count += 1
                state.metrics.total_pauses_ms += pause_ms
                state.metrics.longest_pause_ms = max(state.metrics.longest_pause_ms, pause_ms)
                state.metrics.average_pause_duration_ms = (
                    state.metrics.total_pauses_ms / state.metrics.pause_count
                )

        # Create transcript entry
        entry = VoiceTranscriptEntry(
            role=role,
            text=text,
            timestamp=datetime.utcnow().isoformat(),
            start_time_ms=state.current_speech_start_ms,
        )
        state.transcript.append(entry)
        state.metrics.turn_count += 1

        # Notify transcript callback
        callbacks = self.callbacks.get(session_id, {})
        if callbacks.get("on_transcript"):
            asyncio.create_task(callbacks["on_transcript"](entry.to_dict()))

        logger.info(f"Voice session {session_id} transcript: {role}: {text[:50]}...")

    def _handle_user_started_speaking(self, session_id: str):
        """Handle user started speaking event"""
        state = self.sessions.get(session_id)
        if not state:
            return

        state.current_speech_start_ms = int(time.time() * 1000)

        # Check for interruption
        if state.status == "speaking":
            state.metrics.interruption_count += 1
            state.audio_buffer = bytearray()  # Clear agent audio
            logger.info(f"Voice session {session_id}: User interrupted agent")

        self._update_state(session_id, "listening")

    def _handle_agent_audio_done(self, session_id: str):
        """Handle agent finished speaking"""
        state = self.sessions.get(session_id)
        if not state:
            return

        state.last_speech_end_ms = int(time.time() * 1000)

        # Notify metrics callback
        callbacks = self.callbacks.get(session_id, {})
        if callbacks.get("on_metrics"):
            asyncio.create_task(callbacks["on_metrics"](state.metrics.to_dict()))

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

        logger.debug(f"Voice session {session_id} state: {old_status} -> {new_status}")

    async def send_audio(self, session_id: str, audio_data: bytes) -> bool:
        """Send audio data to the Voice Agent"""
        conn_info = self.connections.get(session_id)
        if not conn_info:
            logger.error(f"No connection for session {session_id}")
            return False

        try:
            connection = conn_info["connection"]
            await connection.send(audio_data)
            return True
        except Exception as e:
            logger.error(f"Failed to send audio for session {session_id}: {e}")
            return False

    async def send_keep_alive(self, session_id: str) -> bool:
        """Send keep-alive to maintain connection"""
        conn_info = self.connections.get(session_id)
        if not conn_info:
            return False

        try:
            connection = conn_info["connection"]
            await connection.keep_alive()
            return True
        except Exception as e:
            logger.error(f"Failed to send keep-alive for session {session_id}: {e}")
            return False

    async def close_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Close a voice session and return final analysis"""
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
                logger.error(f"Error closing connection {session_id}: {e}")

        # Calculate final metrics
        session_duration_ms = int(time.time() * 1000) - state.session_start_ms

        # Calculate words per minute
        total_words = sum(len(entry.text.split()) for entry in state.transcript if entry.role == "user")
        if session_duration_ms > 0:
            state.metrics.words_per_minute = (total_words / session_duration_ms) * 60000

        # Build analysis result
        analysis = {
            "session_id": session_id,
            "attempt_id": state.attempt_id,
            "user_id": state.user_id,
            "mode": state.mode,
            "started_at": state.started_at,
            "ended_at": datetime.utcnow().isoformat(),
            "duration_ms": session_duration_ms,
            "transcript": [entry.to_dict() for entry in state.transcript],
            "metrics": state.metrics.to_dict(),
            "speech_analysis": self._generate_speech_analysis(state),
        }

        # Cleanup
        self._update_state(session_id, "closed")
        del self.sessions[session_id]
        if session_id in self.connections:
            del self.connections[session_id]
        if session_id in self.callbacks:
            del self.callbacks[session_id]

        logger.info(f"Closed voice session {session_id}")
        return analysis

    def _generate_speech_analysis(self, state: VoiceSessionState) -> Dict[str, Any]:
        """Generate speech analysis insights from session metrics"""
        metrics = state.metrics

        analysis = {
            "fluency_score": 0.0,
            "engagement_score": 0.0,
            "confidence_score": 0.0,
            "insights": [],
            "areas_for_improvement": [],
        }

        # Calculate fluency score (based on hesitations and pauses)
        hesitation_rate = metrics.hesitation_count / max(metrics.turn_count, 1)
        if hesitation_rate < 0.1:
            analysis["fluency_score"] = 5.0
        elif hesitation_rate < 0.2:
            analysis["fluency_score"] = 4.0
        elif hesitation_rate < 0.3:
            analysis["fluency_score"] = 3.0
        else:
            analysis["fluency_score"] = 2.0

        # Calculate engagement score (based on turn-taking and response time)
        if metrics.average_pause_duration_ms < 1000:
            analysis["engagement_score"] = 5.0
        elif metrics.average_pause_duration_ms < 2000:
            analysis["engagement_score"] = 4.0
        elif metrics.average_pause_duration_ms < 3000:
            analysis["engagement_score"] = 3.0
        else:
            analysis["engagement_score"] = 2.0

        # Calculate confidence score
        avg_confidence = sum(metrics.confidence_scores) / len(metrics.confidence_scores) if metrics.confidence_scores else 0.8
        analysis["confidence_score"] = avg_confidence * 5.0

        # Generate insights
        if metrics.hesitation_count > 5:
            analysis["insights"].append("Frequent use of filler words detected")
            analysis["areas_for_improvement"].append("Practice speaking with fewer filler words")

        if metrics.average_pause_duration_ms > 2000:
            analysis["insights"].append("Longer pauses between responses")
            analysis["areas_for_improvement"].append("Try to maintain conversation flow")

        if metrics.interruption_count > 0:
            analysis["insights"].append(f"Interrupted the speaker {metrics.interruption_count} time(s)")

        if metrics.words_per_minute < 100:
            analysis["insights"].append("Speaking pace is on the slower side")
        elif metrics.words_per_minute > 180:
            analysis["insights"].append("Speaking pace is quite fast")

        return analysis

    def get_session_state(self, session_id: str) -> Optional[VoiceSessionState]:
        """Get current state of a voice session"""
        return self.sessions.get(session_id)

    def get_session_transcript(self, session_id: str) -> List[Dict[str, Any]]:
        """Get transcript for a voice session"""
        state = self.sessions.get(session_id)
        if not state:
            return []
        return [entry.to_dict() for entry in state.transcript]

    def get_session_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current metrics for a voice session"""
        state = self.sessions.get(session_id)
        if not state:
            return None
        return state.metrics.to_dict()


# Singleton instance
_voice_gateway: Optional[VoiceGateway] = None


def get_voice_gateway() -> VoiceGateway:
    """Get or create the singleton VoiceGateway"""
    global _voice_gateway
    if _voice_gateway is None:
        _voice_gateway = VoiceGateway()
    return _voice_gateway
