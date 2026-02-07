import { NextRequest, NextResponse } from "next/server";
import { getDeepgramClient } from "@/lib/voice/deepgram-client";

/**
 * Convert text to speech using Deepgram API
 * POST /api/voice/tts
 *
 * Body: {
 *   text: string
 *   voice?: string
 *   speed?: number
 * }
 */
export async function POST(req: NextRequest) {
  try {
    const { text, voice, speed } = await req.json();

    if (!text) {
      return NextResponse.json(
        { error: "Text is required" },
        { status: 400 }
      );
    }

    const client = getDeepgramClient();

    if (!client.isConfigured()) {
      return NextResponse.json(
        { error: "Deepgram not configured", message: "DEEPGRAM_API_KEY not set" },
        { status: 503 }
      );
    }

    // Generate speech
    const result = await client.textToSpeech(text, {
      voice: voice || "aura-asteria-en",
      speed: speed || 1.0,
    });

    // Return audio buffer
    return new NextResponse(result.audio, {
      headers: {
        "Content-Type": result.contentType,
        "Content-Disposition": 'attachment; filename="speech.mp3"',
      },
    });
  } catch (error) {
    console.error("TTS error:", error);
    return NextResponse.json(
      {
        error: "Text-to-speech failed",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
