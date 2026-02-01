/**
 * Audio Processor Worklet - Processes audio chunks for streaming
 * 
 * This worklet runs in a separate thread and processes audio
 * with minimal latency. It converts float32 samples to int16
 * and chunks them for streaming to the server.
 */

class AudioProcessor extends AudioWorkletProcessor {
    /**
     * Create new AudioProcessor instance
     * @param {Object} options - Processor options
     * @param {Object} options.processorOptions - Custom processor options
     * @param {number} [options.processorOptions.chunkSize] - Audio chunk size in samples
     */
    constructor(options) {
        super();

        // Audio processing constants
        this.CONSTANTS = {
            FLUX_OPTIMAL_CHUNK_MS: 80,
            FLUX_SAMPLE_RATE: 16000,
            DEFAULT_CHUNK_SAMPLES: 1280  // ~80ms at 16kHz
        };

        this.chunkSize = options.processorOptions?.chunkSize || this.CONSTANTS.DEFAULT_CHUNK_SAMPLES;
        this.buffer = new Float32Array(0);
    }

    /**
     * Process audio input
     * @param {Float32Array[][]} inputs - Audio inputs
     * @param {Float32Array[][]} outputs - Audio outputs
     * @param {Object} parameters - Audio parameters
     * @returns {boolean} True to continue processing, false to stop
     */
    process(inputs, outputs, parameters) {
        const input = inputs[0];

        if (input.length === 0 || input[0].length === 0) {
            return true;
        }

        const inputData = input[0];

        // Append to buffer
        const newBuffer = new Float32Array(this.buffer.length + inputData.length);
        newBuffer.set(this.buffer);
        newBuffer.set(inputData, this.buffer.length);
        this.buffer = newBuffer;

        // Process complete chunks
        while (this.buffer.length >= this.chunkSize) {
            const chunk = this.buffer.slice(0, this.chunkSize);
            this.buffer = this.buffer.slice(this.chunkSize);

            // Convert to int16
            const int16Chunk = this._float32ToInt16(chunk);

            // Send to main thread
            this.port.postMessage({
                audio: int16Chunk.buffer
            }, [int16Chunk.buffer]);
        }

        return true;
    }

    /**
     * Convert float32 audio samples to int16 format
     * @param {Float32Array} float32Array - Input audio data in float32 format
     * @returns {Int16Array} Converted audio data in int16 format
     */
    _float32ToInt16(float32Array) {
        const int16Array = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            const sample = Math.max(-1, Math.min(1, float32Array[i]));
            int16Array[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
        }
        return int16Array;
    }
}

registerProcessor('audio-processor', AudioProcessor);
