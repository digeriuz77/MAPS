import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import { asTypedClient, insertMiPracticeAttempt } from "@/lib/supabase/typed-helpers";
import { Tables } from "@/types/database";

/**
 * Get all MI practice modules
 * GET /api/mi-practice/modules
 * Query params:
 * - active: boolean filter for active modules only (default: true)
 * - difficulty: filter by difficulty level (beginner, intermediate, advanced)
 * - focusArea: filter by MI focus area
 * - limit: limit number of results
 */
export async function GET(req: NextRequest) {
  try {
    const supabase = await createClient();
    const { searchParams } = new URL(req.url);
    const activeOnly = searchParams.get("active") !== "false";
    const difficulty = searchParams.get("difficulty");
    const focusArea = searchParams.get("focusArea");
    const limit = searchParams.get("limit");

    let query = supabase
      .from("mi_practice_modules")
      .select("*")
      .order("created_at", { ascending: true });

    if (activeOnly) {
      query = query.eq("is_active", true);
    }

    if (difficulty) {
      query = query.eq("difficulty_level", difficulty);
    }

    if (focusArea) {
      query = query.eq("mi_focus_area", focusArea);
    }

    if (limit) {
      query = query.limit(parseInt(limit));
    }

    const { data, error } = await query;

    if (error) {
      console.error("Error fetching MI practice modules:", error);
      return NextResponse.json(
        { error: "Failed to fetch modules", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json({
      modules: data || [],
      count: data?.length || 0,
    });
  } catch (error) {
    console.error("Error in modules route:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

/**
 * Start a new MI practice module session
 * POST /api/mi-practice/modules/start
 * Body: { moduleId, userId }
 */
export async function POST(req: NextRequest) {
  try {
    const { moduleId, userId } = await req.json();

    if (!moduleId || !userId) {
      return NextResponse.json(
        { error: "Module ID and User ID are required" },
        { status: 400 }
      );
    }

    const supabase = await createClient();

    // First verify the module exists
    const { data: module, error: moduleError } = await supabase
      .from("mi_practice_modules")
      .select("*")
      .eq("id", moduleId)
      .single();

    if (moduleError || !module) {
      return NextResponse.json(
        { error: "Module not found", details: moduleError?.message },
        { status: 404 }
      );
    }

    // Create an attempt in mi_practice_attempts with typed helper
    const typedClient = asTypedClient(supabase);
    const attemptData = insertMiPracticeAttempt({
      user_id: userId,
      module_id: moduleId,
      started_at: new Date().toISOString(),
      current_node_id: "node_1",
      path_taken: [],
      choices_made: [],
    });

    const { data: attempt, error: attemptError } = await typedClient
      .from(Tables.MI_PRACTICE_ATTEMPTS)
      .insert(attemptData)
      .select()
      .single();

    if (attemptError) {
      console.error("Error creating attempt:", attemptError);
      return NextResponse.json(
        { error: "Failed to start module", details: attemptError.message },
        { status: 500 }
      );
    }

    return NextResponse.json({
      attempt,
      module,
      isNew: true,
    });
  } catch (error) {
    console.error("Error in start module route:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
