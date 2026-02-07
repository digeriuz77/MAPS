import { createClient } from "@/lib/supabase/client";
import { createAdminClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";

/**
 * Process a chat turn with AI persona
 * Handles message submission and generates AI response
 */
export async function POST(req: NextRequest) {
  try {
    const { attemptId, message, scenarioId } = await req.json();

    if (!message || !scenarioId) {
      return NextResponse.json(
        { error: "Message and scenario ID are required" },
        { status: 400 }
      );
    }

    // Get scenario details
    const supabaseAdmin = createAdminClient();
    const { data: scenario } = await supabaseAdmin
      .from("scenarios")
      .select("*")
      .eq("id", scenarioId)
      .single();

    if (!scenario) {
      return NextResponse.json(
        { error: "Scenario not found" },
        { status: 404 }
      );
    }

    // Get attempt details
    let attempt = null;
    if (attemptId) {
      const { data: attemptData } = await supabaseAdmin
        .from("scenario_attempts")
        .select("*")
        .eq("id", attemptId)
        .single();

      attempt = attemptData;
    }

    // Initialize OpenAI
    const openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });

    // Build conversation context
    const transcript = attempt?.transcript || [];
    const personaConfig = scenario.persona_config as Record<string, unknown>;

    // Build messages for OpenAI
    const messages: OpenAI.Chat.ChatCompletionMessageParam[] = [
      {
        role: "system",
        content: buildSystemPrompt(scenario, personaConfig),
      },
    ];

    // Add conversation history (last 10 turns to stay within context)
    const recentTranscript = transcript.slice(-10);
    for (const turn of recentTranscript as Array<{ role: string; content: string }>) {
      messages.push({
        role: turn.role as "user" | "assistant",
        content: turn.content,
      });
    }

    // Add current user message
    messages.push({
      role: "user",
      content: message,
    });

    // Call OpenAI API
    const completion = await openai.chat.completions.create({
      model: process.env.DEFAULT_MODEL || "gpt-4o-mini",
      messages,
      temperature: 0.8, // Higher temperature for more varied responses
      max_tokens: 500,
    });

    const aiResponse = completion.choices[0]?.message?.content ||
      "I'm sorry, I didn't understand that. Could you please rephrase?";

    // Update transcript
    const newTranscript = [
      ...transcript,
      { role: "user", content: message },
      { role: "assistant", content: aiResponse },
    ];

    // Update attempt
    if (attemptId) {
      await supabaseAdmin
        .from("scenario_attempts")
        .update({
          transcript: newTranscript,
          turn_count: (attempt?.turn_count || 0) + 1,
          updated_at: new Date().toISOString(),
        })
        .eq("id", attemptId);
    }

    // Generate real-time feedback
    const feedback = await generateFeedback(message, aiResponse, personaConfig);

    return NextResponse.json({
      response: aiResponse,
      feedback,
      turnCount: (attempt?.turn_count || 0) + 1,
    });
  } catch (error) {
    console.error("Error processing turn:", error);
    return NextResponse.json(
      { error: "Failed to process message" },
      { status: 500 }
    );
  }
}

/**
 * Build the system prompt for the AI persona
 */
function buildSystemPrompt(
  scenario: Record<string, unknown>,
  personaConfig: Record<string, unknown>
): string {
  const personaName = scenario.persona_name as string;
  const personaDescription = scenario.persona_description as string;

  // Extract persona traits from config
  const traits = personaConfig.traits as Array<{ name: string; value: number }> || [];
  const knowledge = personaConfig.knowledge as Record<string, string> || {};

  let prompt = `You are ${personaName}, a realistic client persona for Motivational Interviewing training.

${personaDescription}

**Your Characteristics:**
`;

  // Add personality traits
  if (traits.length > 0) {
    prompt += "\nPersonality Traits (scale 1-5):\n";
    for (const trait of traits) {
      prompt += `- ${trait.name}: ${trait.value}/5\n`;
    }
  }

  // Add knowledge/beliefs
  if (Object.keys(knowledge).length > 0) {
    prompt += "\n**Your Beliefs & Knowledge:**\n";
    for (const [key, value] of Object.entries(knowledge)) {
      prompt += `- ${key}: ${value}\n`;
    }
  }

  prompt += `
**Interaction Guidelines:**
1. Stay in character at all times
2. Respond naturally as a client would, not as a facilitator
3. Vary your responses based on the practitioner's approach
4. Show realistic emotions and resistance when appropriate
5. Don't repeat the same responses - maintain conversation flow
6. Demonstrate the MI spirit based on how you're treated
7. If met with empathy, open up gradually
8. If confronted or judged, become defensive

**Important:** You are NOT a trainer or coach. You are a CLIENT. Do NOT give feedback on MI techniques.
Respond naturally as a client would in a real conversation.`;

  return prompt;
}

/**
 * Generate real-time feedback for the practitioner
 * Analyzes the user's message and the AI's response
 */
async function generateFeedback(
  userMessage: string,
  aiResponse: string,
  personaConfig: Record<string, unknown>
): Promise<Array<{ type: "strength" | "improvement"; message: string }>> {
  const feedback: Array<{ type: "strength" | "improvement"; message: string }> = [];

  // Simple rule-based feedback (can be enhanced with AI analysis)
  const lowerMessage = userMessage.toLowerCase();

  // Check for open-ended questions
  if (lowerMessage.startsWith("what") || lowerMessage.startsWith("how") || lowerMessage.startsWith("tell me about")) {
    feedback.push({
      type: "strength",
      message: "Good open-ended question! This invites elaboration.",
    });
  } else if (lowerMessage.startsWith("do you") || lowerMessage.startsWith("are you") || lowerMessage.startsWith("did you")) {
    feedback.push({
      type: "improvement",
      message: "Consider rephrasing as an open-ended question to invite more exploration.",
    });
  }

  // Check for reflections (simple heuristic)
  if (lowerMessage.includes("sounds like") || lowerMessage.includes("i hear") || lowerMessage.includes("it seems")) {
    feedback.push({
      type: "strength",
      message: "Nice reflection! This shows active listening.",
    });
  }

  // Check for affirmations
  if (lowerMessage.includes("you've shown") || lowerMessage.includes("it's clear that") || lowerMessage.includes("i appreciate")) {
    feedback.push({
      type: "strength",
      message: "Good affirmation! This validates the client's efforts.",
    });
  }

  // Check for confrontational language
  if (lowerMessage.includes("but you should") || lowerMessage.includes("you need to") || lowerMessage.includes("why don't you")) {
    feedback.push({
      type: "improvement",
      message: "This may sound confrontational. Try eliciting the client's own motivations.",
    });
  }

  return feedback;
}
