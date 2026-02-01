/**
 * @typedef {Object} VoiceClientOptions
 * @property {number} [sampleRate=16000] - Audio sample rate (Flux recommended: 16000)
 * @property {number} [channelCount=1] - Number of audio channels (mono recommended)
 * @property {number} [chunkSize=80] - Audio chunk size in milliseconds
 * @property {string} [apiBaseUrl='/api/voice'] - Base URL for voice API endpoints
 * @property {string|null} [transcriptContainer=null] - CSS selector for transcript display
 * @property {string|null} [statusIndicator=null] - CSS selector for status display
 * @property {string|null} [metricsContainer=null] - CSS selector for metrics display
 * @property {(data: any) => void} [onTranscript] - Callback for transcript updates
 * @property {(text: string, turn: number) => void} [onSpeechFinal] - Callback for speech finalization
 * @property {(from: string, to: string) => void} [onStateChange] - Callback for state changes
 * @property {(metrics: any) => void} [onMetrics] - Callback for metrics updates
 * @property {(audioData: ArrayBuffer) => void} [onAudio] - Callback for TTS audio data
 * @property {(error: Error) => void} [onError] - Callback for error handling
 */

/**
 * Voice Client - WebSocket-based voice interaction for scenarios
 * 
 * Supports:
 * - Real-time audio streaming via WebSocket
 * - Voice activity detection
 * - Transcript display
 * - Speech analysis metrics
 * 
 * Modes:
 * - 'stt_only': Flux speech-to-text for transcription
 * - 'full': Complete Voice Agent with TTS responses
 */

class VoiceClient {
    /**
     * Create a new VoiceClient instance
     * @param {VoiceClientOptions} [options={}] - Configuration options
     */
    constructor(options = {}) {
        // Audio processing constants
        this.CONSTANTS = {
            FLUX_OPTIMAL_CHUNK_MS: 80,
            FLUX_SAMPLE_RATE: 16000,
            VOICE_AGENT_SAMPLE_RATE: 24000,
            MAX_RETRIES: 3,
            MAX_AUDIO_CHUNK_SIZE: 8192
        };

        this.options = {
            // Audio settings
            sampleRate: this.CONSTANTS.FLUX_SAMPLE_RATE,
            channelCount: 1,
            chunkSize: this.CONSTANTS.FLUX_OPTIMAL_CHUNK_MS,

            // API settings
            apiBaseUrl: '/api/voice',

            // UI elements
            transcriptContainer: null,
            statusIndicator: null,
            metricsContainer: null,

            // Callbacks
            onTranscript: null,
            onSpeechFinal: null,
            onStateChange: null,
            onMetrics: null,
            onAudio: null,
            onError: null,

            ...options
        };

        // State
        this.sessionId = null;
        this.websocket = null;
        this.audioContext = null;
        this.mediaStream = null;
        this.mediaRecorder = null;
        this.audioWorklet = null;
        this.isRecording = false;
        this.status = 'idle';  // idle, connecting, listening, processing, speaking, error

        // Transcript
        this.transcripts = [];
        this.currentTranscript = '';

        // Audio playback for TTS
        this.audioQueue = [];
        this.isPlaying = false;
    }

    /**
     * Create a voice session
     */
    /**
     * Create a new voice session
     * @param {string} attemptId - Scenario attempt ID
     * @param {string} [mode='stt_only'] - Voice mode: 'stt_only' or 'full'
     * @param {Object} [fluxConfig={}] - Flux STT configuration
     * @param {number} [fluxConfig.eotThreshold=0.7] - End-of-turn confidence threshold (0.5-0.9)
     * @param {number|null} [fluxConfig.eagerEotThreshold=null] - Early end-of-turn threshold (0.3-0.9)
     * @param {number} [fluxConfig.eotTimeoutMs=5000] - Max silence before forced EOT (500-10000ms)
     * @returns {Promise<Object>} Session creation response
     * @throws {Error} If session creation fails
     */
    async createSession(attemptId, mode = 'stt_only', fluxConfig = {}) {
        try {
            const response = await fetch(`${this.options.apiBaseUrl}/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    attempt_id: attemptId,
                    mode: mode,
                    eot_threshold: fluxConfig.eotThreshold || 0.7,
                    eager_eot_threshold: fluxConfig.eagerEotThreshold || null,
                    eot_timeout_ms: fluxConfig.eotTimeoutMs || 5000,
                }),
            });

            if (!response.ok) {
                throw new Error(`Failed to create session: ${response.statusText}`);
            }

            const data = await response.json();
            this.sessionId = data.session_id;

            console.log(`Voice session created: ${this.sessionId}`);
            return data;

        } catch (error) {
            console.error('Error creating voice session:', error);
            this._handleError(error);
            throw error;
        }
    }

    /**
     * Connect WebSocket and start audio streaming
     */
    /**
     * Connect WebSocket and initialize audio streaming
     * @returns {Promise<void>}
     * @throws {Error} If already connected or no session exists
     */
    async connect() {
        if (!this.sessionId) {
            throw new Error('No session created. Call createSession first.');
        }

        if (this.websocket?.readyState === WebSocket.OPEN) {
            console.warn('WebSocket already connected');
            return;
        }

        this._setStatus('connecting');

        try {
            // Initialize audio
            await this._initializeAudio();

            // Connect WebSocket
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}${this.options.apiBaseUrl}/ws/${this.sessionId}`;

            this.websocket = new WebSocket(wsUrl);
            this.websocket.binaryType = 'arraybuffer';

            this.websocket.onopen = () => {
                console.log('WebSocket connected');
            };

            this.websocket.onmessage = (event) => {
                this._handleWebSocketMessage(event);
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this._handleError(error);
            };

            this.websocket.onclose = () => {
                console.log('WebSocket closed');
                this._setStatus('idle');
            };

        } catch (error) {
            console.error('Error connecting:', error);
            this._handleError(error);
            throw error;
        }
    }

    /**
     * Start recording and streaming audio
     */
    /**
     * Start recording and streaming audio from microphone
     * @returns {Promise<void>}
     * @throws {Error} If WebSocket not connected or already recording
     */
    async startRecording() {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket not connected');
        }

        if (this.isRecording) {
            console.warn('Already recording');
            return;
        }

        try {
            // Request microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: this.options.sampleRate,
                    channelCount: this.options.channelCount,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                }
            });

            // Create audio context if needed
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                    sampleRate: this.options.sampleRate,
                });
            }

            // Set up audio processing
            await this._setupAudioProcessing();

            this.isRecording = true;
            this._setStatus('listening');

            console.log('Recording started');

        } catch (error) {
            console.error('Error starting recording:', error);
            this._handleError(error);
            throw error;
        }
    }

    /**
     * Stop recording
     */
    /**
     * Stop audio recording
     */
    stopRecording() {
        if (!this.isRecording) {
            console.warn('Not currently recording');
            return;
        }

        this.isRecording = false;

        // Stop audio processing
        if (this.audioWorklet) {
            this.audioWorklet.disconnect();
            this.audioWorklet = null;
        }

        // Stop media stream
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        console.log('Recording stopped');
    }

    /**
     * End the voice session and get analysis
     */
    /**
     * End the voice session and get final analysis
     * @returns {Promise<Object|null>} Final session analysis or null if failed
     */
    async endSession() {
        this.stopRecording();

        // Close WebSocket
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }

        // Get final analysis
        if (this.sessionId) {
            try {
                const response = await fetch(`${this.options.apiBaseUrl}/sessions/${this.sessionId}/end`, {
                    method: 'POST',
                });

                if (response.ok) {
                    const analysis = await response.json();
                    console.log('Session analysis:', analysis);
                    return analysis;
                }
            } catch (error) {
                console.error('Error ending session:', error);
            }
        }

        this.sessionId = null;
        this._setStatus('idle');
        return null;
    }

    /**
     * Get current transcript
     */
    /**
     * Get complete transcript as single text string
     * @returns {string} Full transcript
     */
    getTranscript() {
        return this.transcripts.map(t => t.text).join(' ');
    }

    /**
     * Get current session status
     * @returns {string} Current status: 'idle', 'connecting', 'listening', 'processing', 'speaking', or 'error'
     */
    getStatus() {
        return this.status;
    }

    // ========== Private Methods ==========

    /**
     * Initialize audio context and worklet
     * @returns {Promise<void>}
     */
    async _initializeAudio() {
        // Create audio context
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: this.options.sampleRate,
        });

        // Load audio worklet for processing
        try {
            await this.audioContext.audioWorklet.addModule('/static/js/audio-processor.js');
        } catch (error) {
            console.warn('AudioWorklet not available, using ScriptProcessor fallback');
        }
    }

    /**
     * Set up audio processing pipeline
     * @param {MediaStreamAudioSourceNode} source - Audio source node from microphone
     * @returns {Promise<void>}
     */
    async _setupAudioProcessing() {
        const source = this.audioContext.createMediaStreamSource(this.mediaStream);

        // Calculate chunk size in samples
        const chunkSamples = Math.floor(this.options.sampleRate * this.options.chunkSize / 1000);

        // Try AudioWorklet first
        try {
            this.audioWorklet = new AudioWorkletNode(this.audioContext, 'audio-processor', {
                processorOptions: {
                    chunkSize: chunkSamples,
                }
            });

            this.audioWorklet.port.onmessage = (event) => {
                if (event.data.audio && this.isRecording) {
                    this._sendAudioChunk(event.data.audio);
                }
            };

            source.connect(this.audioWorklet);
            this.audioWorklet.connect(this.audioContext.destination);

        } catch (error) {
            // Fallback to ScriptProcessor
            console.warn('Using ScriptProcessor fallback');
            this._setupScriptProcessor(source, chunkSamples);
        }
    }

    /**
     * Set up ScriptProcessor as fallback for older browsers
     * @param {MediaStreamAudioSourceNode} source - Audio source node
     * @param {number} bufferSize - Audio buffer size
     */
    _setupScriptProcessor(source, bufferSize) {
        // Round buffer size to power of 2
        bufferSize = Math.pow(2, Math.ceil(Math.log2(bufferSize)));
        bufferSize = Math.max(256, Math.min(16384, bufferSize));

        const processor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);

        processor.onaudioprocess = (event) => {
            if (!this.isRecording) return;

            const inputData = event.inputBuffer.getChannelData(0);
            const audioData = this._float32ToInt16(inputData);
            this._sendAudioChunk(audioData);
        };

        source.connect(processor);
        processor.connect(this.audioContext.destination);

        this.audioWorklet = processor;
    }

    /**
     * Convert float32 audio samples to int16 format
     * @param {Float32Array} float32Array - Input audio data in float32 format
     * @returns {ArrayBuffer} Converted audio data in int16 format as ArrayBuffer
     */
    _float32ToInt16(float32Array) {
        const int16Array = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            const sample = Math.max(-1, Math.min(1, float32Array[i]));
            int16Array[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
        }
        return int16Array.buffer;
    }

    /**
     * Send audio chunk to server via WebSocket
     * @param {ArrayBuffer|Uint8Array|Int16Array} audioData - Audio chunk to send
     * @returns {boolean} True if chunk was sent successfully
     */
    _sendAudioChunk(audioData) {
        const valid = this._validateAudioChunk(audioData);
        if (!valid) {
            return false;
        }

        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(audioData);
            return true;
        }
        
        return false;
    }

    /**
     * Validate audio chunk size
     * @param {ArrayBuffer|Uint8Array|Int16Array} audioData - Audio data to validate
     * @returns {boolean} True if chunk size is valid
     */
    _validateAudioChunk(audioData) {
        const length = ArrayBuffer.isView(audioData) 
            ? audioData.length 
            : audioData.byteLength || audioData.length;
        
        if (length > this.CONSTANTS.MAX_AUDIO_CHUNK_SIZE) {
            console.error('Audio chunk size exceeds maximum limit');
            this._handleError(new Error('Audio chunk size exceeds maximum limit'));
            return false;
        }

        if (length < 128) {
            console.warn('Audio chunk size below recommended minimum');
        }

        return true;
    }

    _handleWebSocketMessage(event) {
        // Binary data = TTS audio
        if (event.data instanceof ArrayBuffer) {
            this._handleAudioData(event.data);
            return;
        }

        // JSON message
        try {
            const message = JSON.parse(event.data);

            switch (message.type) {
                case 'connected':
                    console.log(`Connected to voice session: ${message.session_id}`);
                    this._setStatus('listening');
                    break;

                case 'transcript':
                    this._handleTranscript(message);
                    break;

                case 'speech_final':
                    this._handleSpeechFinal(message);
                    break;

                case 'state_change':
                    console.log(`State change: ${message.from} -> ${message.to}`);
                    this._setStatus(message.to);
                    if (this.options.onStateChange) {
                        this.options.onStateChange(message.from, message.to);
                    }
                    break;

                case 'metrics':
                    if (this.options.onMetrics) {
                        this.options.onMetrics(message.data);
                    }
                    this._updateMetricsDisplay(message.data);
                    break;

                case 'error':
                    console.error('Voice error:', message.message);
                    this._handleError(new Error(message.message));
                    break;

                default:
                    console.log('Unknown message type:', message.type);
            }

        } catch (error) {
            console.error('Error parsing message:', error);
        }
    }

    _handleTranscript(message) {
        this.currentTranscript = message.text;

        if (message.is_final) {
            this.transcripts.push({
                text: message.text,
                timestamp: message.timestamp,
                confidence: message.confidence,
            });
        }

        // Update UI
        this._updateTranscriptDisplay();

        // Callback
        if (this.options.onTranscript) {
            this.options.onTranscript(message);
        }
    }

    _handleSpeechFinal(message) {
        console.log(`Speech final (turn ${message.turn}): ${message.text}`);

        // Callback
        if (this.options.onSpeechFinal) {
            this.options.onSpeechFinal(message.text, message.turn);
        }
    }

    _handleAudioData(audioData) {
        // Queue audio for playback
        this.audioQueue.push(audioData);

        // Callback
        if (this.options.onAudio) {
            this.options.onAudio(audioData);
        }

        // Start playback if not already playing
        if (!this.isPlaying) {
            this._playAudioQueue();
        }
    }

    async _playAudioQueue() {
        if (this.audioQueue.length === 0) {
            this.isPlaying = false;
            return;
        }

        this.isPlaying = true;

        while (this.audioQueue.length > 0) {
            const audioData = this.audioQueue.shift();
            await this._playAudio(audioData);
        }

        this.isPlaying = false;
    }

    _playAudio(audioData) {
        return new Promise((resolve) => {
            // Decode and play audio
            const audioBlob = new Blob([audioData], { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);

            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                resolve();
            };

            audio.onerror = () => {
                URL.revokeObjectURL(audioUrl);
                resolve();
            };

            audio.play().catch(() => resolve());
        });
    }

    _setStatus(status) {
        this.status = status;

        // Update UI
        if (this.options.statusIndicator) {
            const indicator = document.querySelector(this.options.statusIndicator);
            if (indicator) {
                indicator.className = `voice-status voice-status-${status}`;
                indicator.textContent = this._getStatusText(status);
            }
        }
    }

    _getStatusText(status) {
        const statusTexts = {
            'idle': 'Ready',
            'connecting': 'Connecting...',
            'listening': '🎤 Listening',
            'processing': '🤔 Processing',
            'speaking': '🔊 Speaking',
            'error': '❌ Error',
        };
        return statusTexts[status] || status;
    }

    _updateTranscriptDisplay() {
        if (!this.options.transcriptContainer) return;

        const container = document.querySelector(this.options.transcriptContainer);
        if (!container) return;

        // Show finalized transcripts
        let html = this.transcripts.map(t =>
            `<div class="transcript-entry transcript-final">${t.text}</div>`
        ).join('');

        // Show current interim transcript
        if (this.currentTranscript) {
            html += `<div class="transcript-entry transcript-interim">${this.currentTranscript}</div>`;
        }

        container.innerHTML = html;
        container.scrollTop = container.scrollHeight;
    }

    _updateMetricsDisplay(metrics) {
        if (!this.options.metricsContainer) return;

        const container = document.querySelector(this.options.metricsContainer);
        if (!container) return;

        container.innerHTML = `
            <div class="voice-metric">
                <span class="metric-label">Words/min:</span>
                <span class="metric-value">${metrics.words_per_minute?.toFixed(0) || '-'}</span>
            </div>
            <div class="voice-metric">
                <span class="metric-label">Pauses:</span>
                <span class="metric-value">${metrics.pause_count || 0}</span>
            </div>
            <div class="voice-metric">
                <span class="metric-label">Hesitations:</span>
                <span class="metric-value">${metrics.hesitation_count || 0}</span>
            </div>
        `;
    }

    _handleError(error) {
        this._setStatus('error');

        if (this.options.onError) {
            this.options.onError(error);
        }
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceClient;
}
