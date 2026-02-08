import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";

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

    const updateData: Record<string, unknown> = {
      updated_at: new Date().toISOString(),
    };

    if (currentNodeId !== undefined) {
      updateData.current_node_id = currentNodeId;
    }

    if (pathTaken !== undefined) {
      updateData.path_taken = pathTaken;
    }

    if (choicesMade !== undefined) {
      updateData.choices_made = choicesMade;
    }

    if (rapportScore !== undefined) {
      updateData.current_rapport_score = rapportScore;
    }

    if (resistanceLevel !== undefined) {
      updateData.current_resistance_level = resistanceLevel;
    }

    const { data, error } = await supabase
      .from("mi_practice_attempts")
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

    // Update attempt as completed
    const { data, error } = await supabase
      .from("mi_practice_attempts")
      .update({
        completion_status: completionStatus || "completed",
        completed_at: new Date().toISOString(),
        final_scores: finalScores || {},
        updated_at: new Date().toISOString(),
      })
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
