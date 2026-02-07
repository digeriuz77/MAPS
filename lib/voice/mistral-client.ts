/**
 * Mistral Audio API Client
 * Handles transcription and text-to-speech using Mistral's Voxtral models
 */

export interface TranscriptionOptions {
  language?: string;
  prompt?: string; // Optional prompt to guide transcription
}

export interface TTSOptions {
  voice?: "alloy" | "echo" | "fable" | "onyx" | "nova" | "shimmer";
  speed?: number; // 0.25 to 4.0
}

export interface TranscriptionResult {
  text: string;
  duration: number;
  language?: string;
}

export interface TTSResult {
  audio: ArrayBuffer;
  contentType: string;
}

/**
 * Mistral Audio API Client Class
 */
export class MistralAudioClient {
  private apiKey: string;
  private baseURL: string;
  private model: string;

  constructor(apiKey?: string, model?: string) {
    this.apiKey = apiKey || process.env.MISTRAL_API_KEY || "";
    this.baseURL = "https://api.mistral.ai/v1";
    this.model = model || process.env.NEXT_PUBLIC_MISTRAL_AUDIO_MODEL || "voxtral-mini-latest";
  }

  /**
   * Transcribe audio to text using Mistral's Voxtral models
   * @param audioData - Audio data as ArrayBuffer or Base64 string
   * @param options - Transcription options
   */
  async transcribe(
    audioData: ArrayBuffer | string,
    options: TranscriptionOptions = {}
  ): Promise<TranscriptionResult> {
    if (!this.apiKey) {
      throw new Error("Mistral API key is required");
    }

    let audioBlob: Blob;

    // Convert input to Blob
    if (typeof audioData === "string") {
      // Base64 string
      const binaryString = atob(this.base64ToArrayBuffer(audioData));
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      audioBlob = new Blob([bytes], { type: "audio/webm" });
    } else {
      // ArrayBuffer
      audioBlob = new Blob([audioData], { type: "audio/webm" });
    }

    // Create FormData for the request
    const formData = new FormData();
    formData.append("file", audioBlob, "audio.webm");
    formData.append("model", this.model);

    if (options.language) {
      formData.append("language", options.language);
    }

    if (options.prompt) {
      formData.append("prompt", options.prompt);
    }

    // Make the request
    const response = await fetch(`${this.baseURL}/audio/transcriptions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Mistral transcription failed: ${error}`);
    }

    const result = await response.json();

    return {
      text: result.text || "",
      duration: result.duration || 0,
      language: result.language,
    };
  }

  /**
   * Convert text to speech using Mistral's TTS
   * @param text - Text to convert
   * @param options - TTS options
   */
  async textToSpeech(
    text: string,
    options: TTSOptions = {}
  ): Promise<TTSResult> {
    if (!this.apiKey) {
      throw new Error("Mistral API key is required");
    }

    const response = await fetch(`${this.baseURL}/audio/speech`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "tts-1", // Mistral's TTS model
        input: text,
        voice: options.voice || "alloy",
        speed: options.speed || 1.0,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Mistral TTS failed: ${error}`);
    }

    const audioBuffer = await response.arrayBuffer();

    return {
      audio: audioBuffer,
      contentType: "audio/mpeg",
    };
  }

  /**
   * Convert ArrayBuffer to Base64
   */
  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = "";
    for (const byte of bytes) {
      binary += String.fromCharCode(byte);
    }
    return btoa(binary);
  }

  /**
   * Convert Base64 to ArrayBuffer (helper for the reverse)
   */
  private base64ToArrayBuffer(base64: string): string {
    // This is a placeholder - the actual implementation is handled in transcribe()
    return base64;
  }
}

/**
 * Default singleton instance
 */
let defaultClient: MistralAudioClient | null = null;

export function getMistralClient(): MistralAudioClient {
  if (!defaultClient) {
    defaultClient = new MistralAudioClient();
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
