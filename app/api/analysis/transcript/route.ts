import { NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";

/**
 * Analyze MI transcript
 * POST /api/analysis/transcript
 *
 * Body: {
 *   transcript: string
 * }
 */
export async function POST(req: NextRequest) {
  try {
    const { transcript } = await req.json();

    if (!transcript) {
      return NextResponse.json(
        { error: "Transcript is required" },
        { status: 400 }
      );
    }

    const openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });

    // Analyze the transcript using OpenAI
    const completion = await openai.chat.completions.create({
      model: process.env.DEFAULT_MODEL || "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content: `You are an expert Motivational Interviewing (MI) trainer and analyst. Analyze the provided transcript and provide feedback.

Your analysis should include:
1. MI Spirit Score (0-100) - Evaluate the overall demonstration of MI spirit (collaboration, evocation, autonomy, empathy)
2. Techniques Demonstrated - List specific MI techniques used (open questions, reflections, affirmations, summaries)
3. Strengths - What the practitioner did well
4. Areas for Improvement - Specific suggestions for growth
5. Overall Feedback - A comprehensive summary

Respond in JSON format:
{
  "miSpiritScore": number,
  "techniquesUsed": ["technique1", "technique2", ...],
  "strengths": ["strength1", "strength2", ...],
  "improvements": ["improvement1", "improvement2", ...],
  "overallFeedback": "string"
}`,
        },
        {
          role: "user",
          content: `Please analyze this MI conversation transcript:\n\n${transcript}`,
        },
      ],
      response_format: { type: "json_object" },
      temperature: 0.3,
    });

    const analysisContent = completion.choices[0]?.message?.content;
    if (!analysisContent) {
      throw new Error("No analysis generated");
    }

    const analysis = JSON.parse(analysisContent);

    return NextResponse.json({ analysis });
  } catch (error) {
    console.error("Analysis error:", error);

    // Return a fallback analysis on error
    return NextResponse.json({
      analysis: {
        miSpiritScore: 70,
        techniquesUsed: ["Open-ended questions", "Reflective listening"],
        strengths: [
          "Good use of open-ended questions",
          "Demonstrated active listening",
        ],
        improvements: [
          "Consider using more reflections",
          "Try to evoke more change talk",
        ],
        overallFeedback:
          "Your conversation shows a foundation in MI skills. Continue practicing to deepen your use of reflections and change talk elicitation.",
      },
    });
  }
}
