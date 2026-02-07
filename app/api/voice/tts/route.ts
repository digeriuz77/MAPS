import { NextRequest, NextResponse } from "next/server";
import { getMistralClient } from "@/lib/voice/mistral-client";

/**
 * Convert text to speech using Mistral Audio API
 * POST /api/voice/tts
 *
 * Body: {
 *   text: string
 *   voice?: "alloy" | "echo" | "fable" | "onyx" | "nova" | "shimmer"
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

    const client = getMistralClient();

    // Generate speech
    const result = await client.textToSpeech(text, {
      voice: voice || "alloy",
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
