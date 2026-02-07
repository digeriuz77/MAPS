import { NextRequest, NextResponse } from "next/server";
import { getMistralClient } from "@/lib/voice/mistral-client";

/**
 * Transcribe audio using Mistral Audio API
 * POST /api/voice/transcribe
 *
 * Body: {
 *   audio: string (Base64 encoded audio)
 *   language?: string
 *   prompt?: string
 * }
 */
export async function POST(req: NextRequest) {
  try {
    const { audio, language, prompt } = await req.json();

    if (!audio) {
      return NextResponse.json(
        { error: "Audio data is required" },
        { status: 400 }
      );
    }

    const client = getMistralClient();

    // Convert Base64 to ArrayBuffer
    const binaryString = atob(audio);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    const audioBuffer = bytes.buffer;

    // Transcribe
    const result = await client.transcribe(audioBuffer, {
      language,
      prompt,
    });

    return NextResponse.json({
      text: result.text,
      duration: result.duration,
      language: result.language,
    });
  } catch (error) {
    console.error("Transcription error:", error);
    return NextResponse.json(
      {
        error: "Transcription failed",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
