import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import { asTypedClient, updateMiPracticeAttempt } from "@/lib/supabase/typed-helpers";
import { Tables } from "@/types/database";

/**
 * Update MI practice attempt progress
 * POST /api/mi-practice/progress
 * Body: { attemptId, currentNodeId, pathTaken, choicesMade }
 */
export async function POST(req: NextRequest) {
  try {
    const { attemptId, currentNodeId, pathTaken, choicesMade, rapportScore, resistanceLevel } = await req.json();

    if (!attemptId) {
      return NextResponse.json(
        { error: "Attempt ID is required" },
        { status: 400 }
      );
    }

    const supabase = await createClient();

    // Build update data with typed helper
    const updateData = updateMiPracticeAttempt({
      current_node_id: currentNodeId,
      path_taken: pathTaken,
      choices_made: choicesMade,
      current_rapport_score: rapportScore,
      current_resistance_level: resistanceLevel,
    });

    const typedClient = asTypedClient(supabase);
    const { data, error } = await typedClient
      .from(Tables.MI_PRACTICE_ATTEMPTS)
      .update(updateData)
      .eq("id", attemptId)
      .select()
      .single();

    if (error) {
      console.error("Error updating attempt progress:", error);
      return NextResponse.json(
        { error: "Failed to update progress", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in progress route:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

/**
 * Complete an MI practice attempt
 * PUT /api/mi-practice/progress/complete
 * Body: { attemptId, completionStatus, finalScores }
 */
export async function PUT(req: NextRequest) {
  try {
    const { attemptId, completionStatus, finalScores } = await req.json();

    if (!attemptId) {
      return NextResponse.json(
        { error: "Attempt ID is required" },
        { status: 400 }
      );
    }

    const supabase = await createClient();

    // Get current attempt
    const { data: currentAttempt } = await supabase
      .from("mi_practice_attempts")
      .select("*")
      .eq("id", attemptId)
      .single();

    if (!currentAttempt) {
      return NextResponse.json(
        { error: "Attempt not found" },
        { status: 404 }
      );
    }

    // Update attempt as completed with typed helper
    const completeData = updateMiPracticeAttempt({
      completion_status: completionStatus || "completed",
      completed_at: new Date().toISOString(),
      final_scores: finalScores || {},
    });

    const typedClient = asTypedClient(supabase);
    const { data, error } = await typedClient
      .from(Tables.MI_PRACTICE_ATTEMPTS)
      .update(completeData)
      .eq("id", attemptId)
      .select()
      .single();

    if (error) {
      console.error("Error completing attempt:", error);
      return NextResponse.json(
        { error: "Failed to complete module", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json({
      attempt: data,
    });
  } catch (error) {
    console.error("Error in complete route:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
