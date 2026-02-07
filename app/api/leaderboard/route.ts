import { createAdminClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import type { UserProfile } from "@/types/supabase";

/**
 * Get leaderboard data
 * GET /api/leaderboard?limit=10&offset=0
 *
 * Returns top users by points, including current user's rank
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const limit = parseInt(searchParams.get("limit") || "10");
    const offset = parseInt(searchParams.get("offset") || "0");
    const includeCurrentUser = searchParams.get("includeCurrentUser") === "true";

    const supabase = createAdminClient();

    // Get top users
    const { data: topUsers, error: usersError } = await supabase
      .from("user_profiles")
      .select("*")
      .order("total_points", { ascending: false })
      .range(offset, offset + limit - 1);

    if (usersError) {
      throw usersError;
    }

    let currentUserRank = null;

    // Optionally include current user's rank
    if (includeCurrentUser) {
      // For demo purposes, we'll skip this as we need the actual user ID
      // In production, this would be:
      // const { data: { user } } = await supabase.auth.getUser();
      // if (user) {
      //   const rank = await getUserRank(user.id);
      //   currentUserRank = rank;
      // }
    }

    return NextResponse.json({
      leaderboard: (topUsers as UserProfile[] | null)?.map((user, index) => ({
        rank: offset + index + 1,
        displayName: user.display_name || "Anonymous",
        totalPoints: user.total_points,
        level: user.level,
        modulesCompleted: user.modules_completed,
      })) || [],
      currentUserRank,
      hasMore: (topUsers?.length || 0) === limit,
    });
  } catch (error) {
    console.error("Leaderboard error:", error);
    return NextResponse.json(
      {
        error: "Failed to fetch leaderboard",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
