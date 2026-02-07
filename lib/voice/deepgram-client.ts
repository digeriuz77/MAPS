/**
 * Deepgram API Client
 * Handles transcription and text-to-speech using Deepgram's API
 */

export interface TranscriptionOptions {
    language?: string;
    punctuate?: boolean;
    diarize?: boolean;
    model?: string;
}

export interface TTSOptions {
    voice?: string;
    speed?: number;
}

export interface TranscriptionResult {
    text: string;
    duration: number;
    language?: string;
    confidence?: number;
}

export interface TTSResult {
    audio: ArrayBuffer;
    contentType: string;
}

/**
 * Deepgram API Client Class
 */
export class DeepgramClient {
    private apiKey: string;
    private baseURL: string;

    constructor(apiKey?: string) {
        this.apiKey = apiKey || process.env.DEEPGRAM_API_KEY || "";
        this.baseURL = "https://api.deepgram.com/v1";
    }

    /**
     * Check if Deepgram is configured
     */
    isConfigured(): boolean {
        return !!this.apiKey;
    }

    /**
     * Transcribe audio to text using Deepgram's API
     * @param audioData - Audio data as ArrayBuffer or Base64 string
     * @param options - Transcription options
     */
    async transcribe(
        audioData: ArrayBuffer | string,
        options: TranscriptionOptions = {}
    ): Promise<TranscriptionResult> {
        if (!this.apiKey) {
            throw new Error("Deepgram API key is required");
        }

        let audioBuffer: ArrayBuffer;

        // Convert input to ArrayBuffer
        if (typeof audioData === "string") {
            // Base64 string
            const binaryString = atob(audioData);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            audioBuffer = bytes.buffer;
        } else {
            audioBuffer = audioData;
        }

        // Build query parameters
        const params = new URLSearchParams();
        params.append("model", options.model || "nova-2");
        if (options.language) {
            params.append("language", options.language);
        }
        if (options.punctuate !== false) {
            params.append("punctuate", "true");
        }
        if (options.diarize) {
            params.append("diarize", "true");
        }

        // Make the request
        const response = await fetch(
            `${this.baseURL}/listen?${params.toString()}`,
            {
                method: "POST",
                headers: {
                    Authorization: `Token ${this.apiKey}`,
                    "Content-Type": "audio/webm",
                },
                body: audioBuffer,
            }
        );

        if (!response.ok) {
            const error = await response.text();
            throw new Error(`Deepgram transcription failed: ${error}`);
        }

        const result = await response.json();
        const channel = result.results?.channels?.[0];
        const alternative = channel?.alternatives?.[0];

        return {
            text: alternative?.transcript || "",
            duration: result.metadata?.duration || 0,
            language: result.metadata?.language,
            confidence: alternative?.confidence,
        };
    }

    /**
     * Convert text to speech using Deepgram's TTS
     * @param text - Text to convert
     * @param options - TTS options
     */
    async textToSpeech(
        text: string,
        options: TTSOptions = {}
    ): Promise<TTSResult> {
        if (!this.apiKey) {
            throw new Error("Deepgram API key is required");
        }

        const params = new URLSearchParams();
        params.append("model", "aura-asteria-en");
        if (options.voice) {
            params.append("voice", options.voice);
        }

        const response = await fetch(
            `${this.baseURL}/speak?${params.toString()}`,
            {
                method: "POST",
                headers: {
                    Authorization: `Token ${this.apiKey}`,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    text,
                    speed: options.speed || 1.0,
                }),
            }
        );

        if (!response.ok) {
            const error = await response.text();
            throw new Error(`Deepgram TTS failed: ${error}`);
        }

        const audioBuffer = await response.arrayBuffer();

        return {
            audio: audioBuffer,
            contentType: "audio/mpeg",
        };
    }
}

/**
 * Default singleton instance
 */
let defaultClient: DeepgramClient | null = null;

export function getDeepgramClient(): DeepgramClient {
    if (!defaultClient) {
        defaultClient = new DeepgramClient();
    }
    return defaultClient;
}

/**
 * Convert audio file to Base64 for client-side upload
 */
export function audioFileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            if (typeof reader.result === "string") {
                // Remove data URL prefix
                const base64 = reader.result.split(",")[1];
                resolve(base64);
            } else {
                reject(new Error("Failed to convert file to Base64"));
            }
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

/**
 * Convert Blob to Base64
 */
export function blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            if (typeof reader.result === "string") {
                const base64 = reader.result.split(",")[1];
                resolve(base64);
            } else {
                reject(new Error("Failed to convert blob to Base64"));
            }
        };
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}
