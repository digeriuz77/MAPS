import { createAdminClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import { asTypedClient, updateScenarioAttempt } from "@/lib/supabase/typed-helpers";
import { Tables } from "@/types/database";

/**
 * End a scenario attempt session
 * POST /api/scenarios/attempts/[attemptId]/end
 */
export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ attemptId: string }> }
) {
  try {
    const { attemptId } = await params;

    if (!attemptId) {
      return NextResponse.json(
        { error: "Attempt ID is required" },
        { status: 400 }
      );
    }

    const supabaseAdmin = createAdminClient();

    // Update the attempt to mark it as completed with typed helper
    const updateData = updateScenarioAttempt({
      ended_at: new Date().toISOString(),
    });

    const typedClient = asTypedClient(supabaseAdmin);
    const { data, error } = await typedClient
      .from(Tables.SCENARIO_ATTEMPTS)
      .update(updateData)
      .eq("id", attemptId)
      .select()
      .single();

    if (error) {
      console.error("Error ending scenario attempt:", error);
      return NextResponse.json(
        { error: "Failed to end session" },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      attempt: data,
    });
  } catch (error) {
    console.error("Error in end route:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
