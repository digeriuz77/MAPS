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
    constructor(options = {}) {
        this.options = {
            // Audio settings
            sampleRate: 16000,  // Flux recommended
            channelCount: 1,
            chunkSize: 80,  // ms, optimal for Flux

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
    async connect() {
        if (!this.sessionId) {
            throw new Error('No session created. Call createSession first.');
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
    async startRecording() {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket not connected');
        }

        if (this.isRecording) {
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
    stopRecording() {
        if (!this.isRecording) {
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
    getTranscript() {
        return this.transcripts.map(t => t.text).join(' ');
    }

    /**
     * Get current status
     */
    getStatus() {
        return this.status;
    }

    // ========== Private Methods ==========

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

    _float32ToInt16(float32Array) {
        const int16Array = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            const s = Math.max(-1, Math.min(1, float32Array[i]));
            int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return int16Array.buffer;
    }

    _sendAudioChunk(audioData) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(audioData);
        }
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
