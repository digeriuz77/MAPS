/**
 * Audio Utility Functions - Shared audio processing utilities
 * 
 * Provides common audio processing functions used by both:
 * - VoiceClient (main thread)
 * - AudioProcessor (Web Audio API worklet)
 */

/**
 * Audio processing constants
 */
export const AUDIO_CONSTANTS = {
    // Flux STT recommended settings
    FLUX_OPTIMAL_CHUNK_MS: 80,
    FLUX_SAMPLE_RATE: 16000,
    
    // Voice Agent (Deepgram) recommended settings
    VOICE_AGENT_SAMPLE_RATE: 24000,
    
    // Maximum retries for audio operations
    MAX_AUDIO_RETRIES: 3,
    
    // Audio buffer limits
    MAX_AUDIO_CHUNK_SIZE: 8192,
    MIN_AUDIO_CHUNK_SIZE: 128,
    
    // Supported audio formats
    SUPPORTED_FORMATS: ['linear16', 'wav', 'mp3', 'ogg'],
    
    // Channel configuration
    MONO_CHANNELS: 1,
    STEREO_CHANNELS: 2
};

/**
 * Convert float32 audio samples to int16 format
 * @param {Float32Array} float32Array - Input audio data in float32 format
 * @returns {Int16Array} Converted audio data in int16 format
 */
export function float32ToInt16(float32Array) {
    const int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
        const sample = Math.max(-1, Math.min(1, float32Array[i]));
        int16Array[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
    }
    return int16Array;
}

/**
 * Convert int16 audio samples to float32 format
 * @param {Int16Array} int16Array - Input audio data in int16 format
 * @returns {Float32Array} Converted audio data in float32 format
 */
export function int16ToFloat32(int16Array) {
    const float32Array = new Float32Array(int16Array.length);
    for (let i = 0; i < int16Array.length; i++) {
        float32Array[i] = int16Array[i] / 0x8000;
    }
    return float32Array;
}

/**
 * Validate audio chunk size
 * @param {ArrayBuffer|Uint8Array|Int16Array|Float32Array} audioData - Audio data chunk
 * @param {number} minSize - Minimum valid size
 * @param {number} maxSize - Maximum valid size
 * @returns {boolean} True if chunk size is valid
 */
export function isValidAudioChunkSize(audioData, minSize = AUDIO_CONSTANTS.MIN_AUDIO_CHUNK_SIZE, maxSize = AUDIO_CONSTANTS.MAX_AUDIO_CHUNK_SIZE) {
    const length = ArrayBuffer.isView(audioData) ? audioData.length : audioData.byteLength || audioData.length;
    return length >= minSize && length <= maxSize;
}

/**
 * Calculate RMS (Root Mean Square) for audio amplitude
 * @param {Float32Array} audioData - Audio samples in float32 format
 * @returns {number} RMS value (0.0 - 1.0)
 */
export function calculateRMS(audioData) {
    let sum = 0;
    for (let i = 0; i < audioData.length; i++) {
        sum += audioData[i] * audioData[i];
    }
    const mean = sum / audioData.length;
    return Math.sqrt(mean);
}

/**
 * Check if audio contains significant sound (voice activity detection helper)
 * @param {Float32Array} audioData - Audio samples in float32 format
 * @param {number} threshold - Activity threshold (0.0 - 1.0)
 * @returns {boolean} True if significant sound detected
 */
export function hasSignificantSound(audioData, threshold = 0.01) {
    const rms = calculateRMS(audioData);
    return rms > threshold;
}

/**
 * Trim silence from beginning and end of audio
 * @param {Float32Array} audioData - Audio samples in float32 format
 * @param {number} silenceThreshold - Silence threshold (0.0 - 1.0)
 * @returns {Float32Array} Trimmed audio
 */
export function trimSilence(audioData, silenceThreshold = 0.001) {
    let start = 0;
    while (start < audioData.length && Math.abs(audioData[start]) < silenceThreshold) {
        start++;
    }

    let end = audioData.length - 1;
    while (end > start && Math.abs(audioData[end]) < silenceThreshold) {
        end--;
    }

    return audioData.slice(start, end + 1);
}
