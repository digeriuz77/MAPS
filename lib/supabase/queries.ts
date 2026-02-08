// @ts-nocheck - Supabase type inference issues with complex queries and JSON columns
import type {
  Scenario,
  ScenarioAttempt,
  UserProfile,
} from "@/types/supabase";
import {
  calculateLevel,
  getPointsToNextLevel,
  getLevelProgress,
} from "@/lib/gamification/scoring";

// Re-export gamification functions for convenience
export { calculateLevel, getPointsToNextLevel, getLevelProgress };

/**
 * Database query utilities for MAPS
 * Updated to match the actual Supabase schema
 * 
 * ACTUAL SCHEMA IN SUPABASE:
 * - scenarios: id, code, title, situation, persona_config (JSON), is_active, etc.
 * - scenario_attempts: exists but may be empty
 * - profiles: exists but empty (not user_profiles)
 * 
 * MISSING TABLES (need to be created or code adapted):
 * - learning_modules (for MI practice)
 * - user_progress
 */

// =====================================================
// Scenarios Queries (UPDATED TO ACTUAL SCHEMA)
// =====================================================

export async function getScenarios(activeOnly: boolean = true): Promise<Scenario[]> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

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
    return [];
  }

  // Transform to expected format for compatibility
  return (data || []).map(item => ({
    ...item,
    // Map 'title' to expected fields for display
    persona_name: item.persona_config?.name || item.title?.split('(')[0]?.trim() || 'Unknown',
    persona_description: item.situation || item.learning_objective || '',
  }));
}

export async function getScenarioById(id: string): Promise<Scenario | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("scenarios")
    .select("*")
    .eq("id", id)
    .single();

  if (error) {
    console.error("Error fetching scenario:", error);
    return null;
  }

  if (!data) return null;

  // Transform to expected format
  return {
    ...data,
    persona_name: data.persona_config?.name || data.title?.split('(')[0]?.trim() || 'Unknown',
    persona_description: data.situation || data.learning_objective || '',
  };
}

export async function getScenarioByCode(code: string): Promise<Scenario | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("scenarios")
    .select("*")
    .eq("code", code)
    .single();

  if (error) {
    console.error("Error fetching scenario by code:", error);
    return null;
  }

  if (!data) return null;

  return {
    ...data,
    persona_name: data.persona_config?.name || data.title?.split('(')[0]?.trim() || 'Unknown',
    persona_description: data.situation || data.learning_objective || '',
  };
}

// =====================================================
// Scenario Attempts Queries
// =====================================================

export async function createScenarioAttempt(
  scenarioId: string,
  userId: string
): Promise<ScenarioAttempt | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await (supabase as any)
    .from("scenario_attempts")
    .insert({
      scenario_id: scenarioId,
      user_id: userId,
      turn_count: 0,
      conversation_history: [],
    })
    .select()
    .single();

  if (error) {
    console.error("Error creating scenario attempt:", error);
    return null;
  }

  return data as ScenarioAttempt | null;
}

export async function getScenarioAttempt(attemptId: string): Promise<ScenarioAttempt | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("scenario_attempts")
    .select("*")
    .eq("id", attemptId)
    .single();

  if (error) {
    console.error("Error fetching scenario attempt:", error);
    return null;
  }

  return data as ScenarioAttempt | null;
}

export async function updateScenarioAttempt(
  attemptId: string,
  updates: Partial<ScenarioAttempt>
): Promise<ScenarioAttempt | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await (supabase as any)
    .from("scenario_attempts")
    .update(updates)
    .eq("id", attemptId)
    .select()
    .single();

  if (error) {
    console.error("Error updating scenario attempt:", error);
    return null;
  }

  return data as ScenarioAttempt | null;
}

export async function getUserScenarioAttempts(
  userId: string,
  limit?: number
): Promise<ScenarioAttempt[]> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  let query = supabase
    .from("scenario_attempts")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false });

  if (limit) {
    query = query.limit(limit);
  }

  const { data, error } = await query;

  if (error) {
    console.error("Error fetching user scenario attempts:", error);
    return [];
  }

  return (data as ScenarioAttempt[]) || [];
}

// =====================================================
// User Profile Queries (using 'profiles' table)
// =====================================================

export async function getUserProfile(userId: string): Promise<UserProfile | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  // Try 'profiles' table first (what exists in Supabase)
  const { data, error } = await supabase
    .from("profiles")
    .select("*")
    .eq("id", userId)
    .single();

  if (error) {
    // If profiles doesn't work, return a default profile
    console.warn("Could not fetch from profiles table:", error.message);
    return {
      id: userId,
      user_id: userId,
      display_name: "User",
      role: "FULL",
      total_points: 0,
      level: 1,
      modules_completed: 0,
      change_talk_evoked: 0,
      reflections_offered: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  }

  return data as UserProfile | null;
}

export async function updateUserProfile(
  userId: string,
  updates: Partial<UserProfile>
): Promise<UserProfile | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await (supabase as any)
    .from("profiles")
    .update(updates)
    .eq("id", userId)
    .select()
    .single();

  if (error) {
    console.error("Error updating user profile:", error);
    return null;
  }

  return data as UserProfile | null;
}

export async function addUserPoints(userId: string, points: number): Promise<UserProfile | null> {
  const profile = await getUserProfile(userId);
  if (!profile) return null;

  const newPoints = profile.total_points + points;
  const newLevel = calculateLevel(newPoints);

  return updateUserProfile(userId, {
    total_points: newPoints,
    level: newLevel,
  });
}

// =====================================================
// Learning Modules Queries (using mi_practice_modules table)
// The actual table in Supabase is 'mi_practice_modules'
// =====================================================

export async function getLearningModules(options: {
  active?: boolean;
  published?: boolean;
  difficulty?: string;
  limit?: number;
}): Promise<any[]> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  // Use the actual table name: mi_practice_modules
  let query = supabase
    .from("mi_practice_modules")
    .select("*")
    .order("module_number", { ascending: true });

  if (options.active !== undefined) {
    query = query.eq("is_active", options.active);
  }
  if (options.difficulty) {
    query = query.eq("difficulty_level", options.difficulty);
  }
  if (options.limit) {
    query = query.limit(options.limit);
  }

  const { data, error } = await query;

  if (error) {
    console.error("Error fetching learning modules:", error.message);
    return [];
  }

  return data || [];
}

export async function getLearningModuleById(id: string): Promise<any | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("mi_practice_modules")
    .select("*")
    .eq("id", id)
    .single();

  if (error) {
    console.error("Error fetching learning module:", error.message);
    return null;
  }

  return data;
}

export async function getLearningModuleByCode(code: string): Promise<any | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("mi_practice_modules")
    .select("*")
    .eq("code", code)
    .single();

  if (error) {
    console.error("Error fetching learning module by code:", error.message);
    return null;
  }

  return data;
}

// =====================================================
// User Progress Queries (STUB - table doesn't exist)
// =====================================================

export async function getUserProgress(userId: string): Promise<any[]> {
  console.warn("User progress table doesn't exist in Supabase. Returning empty array.");
  return [];
}

export async function getUserProgressForModule(
  userId: string,
  moduleId: string
): Promise<any | null> {
  console.warn("User progress table doesn't exist in Supabase.");
  return null;
}

export async function createUserProgress(
  userId: string,
  moduleId: string,
  data: any = {}
): Promise<any | null> {
  console.warn("User progress table doesn't exist in Supabase.");
  return null;
}

export async function updateUserProgress(
  userId: string,
  moduleId: string,
  updates: any
): Promise<any | null> {
  console.warn("User progress table doesn't exist in Supabase.");
  return null;
}

export async function completeUserProgress(
  userId: string,
  moduleId: string,
  score: number
): Promise<any | null> {
  console.warn("User progress table doesn't exist in Supabase.");
  return null;
}

// =====================================================
// Learning Paths Queries (STUB - table doesn't exist)
// =====================================================

export async function getLearningPaths(activeOnly: boolean = true): Promise<any[]> {
  console.warn("Learning paths table doesn't exist in Supabase. Returning empty array.");
  return [];
}
