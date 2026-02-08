import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import { asTypedClient, insertScenarioAttempt } from "@/lib/supabase/typed-helpers";
import { Tables, type Scenario } from "@/types/database";

/**
 * Get all scenarios (personas)
 * GET /api/scenarios
 * Query params:
 * - active: boolean filter for active scenarios only
 */
export async function GET(req: NextRequest) {
  try {
    const supabase = await createClient();
    const { searchParams } = new URL(req.url);
    const activeOnly = searchParams.get("active") !== "false";

    let query = supabase
      .from("scenarios")
      .select("*")
      .order("title", { ascending: true });

    if (activeOnly) {
      query = query.eq("is_active", true);
    }

    const { data, error } = await query;

    if (error) {
      console.error("Error fetching scenarios:", error);
      return NextResponse.json(
        { error: "Failed to fetch scenarios" },
        { status: 500 }
      );
    }

    return NextResponse.json({
      scenarios: data || [],
      count: data?.length || 0,
    });
  } catch (error) {
    console.error("Error in scenarios route:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

/**
 * Start a new scenario attempt
 * POST /api/scenarios/start
 * Body: { scenarioId, userId }
 */
export async function POST(req: NextRequest) {
  try {
    const { scenarioId, userId } = await req.json();

    if (!scenarioId || !userId) {
      return NextResponse.json(
        { error: "Scenario ID and User ID are required" },
        { status: 400 }
      );
    }

    const supabase = await createClient();

    // First verify the scenario exists
    const { data: scenario, error: scenarioError } = await supabase
      .from("scenarios")
      .select("*")
      .eq("id", scenarioId)
      .single();

    const scenarioData = scenario as Scenario | null;

    if (scenarioError || !scenarioData) {
      return NextResponse.json(
        { error: "Scenario not found" },
        { status: 404 }
      );
    }

    // Create the attempt with typed helper
    const typedClient = asTypedClient(supabase);

    // Extract initial persona state from scenario config
    const initialState = scenarioData.persona_config?.starting_state || {
      trust_level: 3,
      openness_level: 2,
      resistance_active: true,
    };

    const attemptData = insertScenarioAttempt({
      user_id: userId,
      scenario_id: scenarioId,
      transcript: [],
      turn_count: 0,
      initial_persona_state: initialState,
    });

    const { data: attempt, error: attemptError } = await typedClient
      .from(Tables.SCENARIO_ATTEMPTS)
      .insert(attemptData)
      .select()
      .single();

    if (attemptError) {
      console.error("Error creating scenario attempt:", attemptError);
      return NextResponse.json(
        { error: "Failed to start scenario", details: attemptError.message },
        { status: 500 }
      );
    }

    return NextResponse.json({
      attempt,
      scenario: scenarioData,
      isNew: true,
    });
  } catch (error) {
    console.error("Error in start scenario route:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
