/**
 * Audio Processor Worklet - Processes audio chunks for streaming
 * 
 * This worklet runs in a separate thread and processes audio
 * with minimal latency. It converts float32 samples to int16
 * and chunks them for streaming to the server.
 */

class AudioProcessor extends AudioWorkletProcessor {
    constructor(options) {
        super();

        this.chunkSize = options.processorOptions?.chunkSize || 1280;  // ~80ms at 16kHz
        this.buffer = new Float32Array(0);
    }

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

    _float32ToInt16(float32Array) {
        const int16Array = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            const s = Math.max(-1, Math.min(1, float32Array[i]));
            int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return int16Array;
    }
}

registerProcessor('audio-processor', AudioProcessor);
