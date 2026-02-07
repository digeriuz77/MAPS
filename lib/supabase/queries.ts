// @ts-nocheck - Supabase type inference issues with complex queries and JSON columns
import type {
  UserProgress,
  LearningModule,
  Scenario,
  ScenarioAttempt,
  UserProfile,
  LearningPath,
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
 * Provides typed query functions for common operations
 */

// =====================================================
// User Profile Queries
// =====================================================

export async function getUserProfile(userId: string): Promise<UserProfile | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("user_profiles")
    .select("*")
    .eq("id", userId)
    .single();

  if (error) {
    console.error("Error fetching user profile:", error);
    return null;
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
    .from("user_profiles")
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
// Learning Modules Queries
// =====================================================

export async function getLearningModules(options: {
  active?: boolean;
  published?: boolean;
  difficulty?: string;
  limit?: number;
}): Promise<LearningModule[]> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  let query = supabase
    .from("learning_modules")
    .select("*")
    .order("display_order", { ascending: true });

  if (options.active !== undefined) {
    query = query.eq("is_active", options.active);
  }
  if (options.published !== undefined) {
    query = query.eq("is_published", options.published);
  }
  if (options.difficulty) {
    query = query.eq("difficulty_level", options.difficulty);
  }
  if (options.limit) {
    query = query.limit(options.limit);
  }

  const { data, error } = await query;

  if (error) {
    console.error("Error fetching learning modules:", error);
    return [];
  }

  return data || [];
}

export async function getLearningModuleById(id: string): Promise<LearningModule | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("learning_modules")
    .select("*")
    .eq("id", id)
    .single();

  if (error) {
    console.error("Error fetching learning module:", error);
    return null;
  }

  return data;
}

export async function getLearningModuleByCode(code: string): Promise<LearningModule | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("learning_modules")
    .select("*")
    .eq("code", code)
    .single();

  if (error) {
    console.error("Error fetching learning module by code:", error);
    return null;
  }

  return data;
}

// =====================================================
// Scenarios Queries
// =====================================================

export async function getScenarios(activeOnly: boolean = true): Promise<Scenario[]> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  let query = supabase
    .from("scenarios")
    .select("*")
    .order("persona_name", { ascending: true });

  if (activeOnly) {
    query = query.eq("is_active", true);
  }

  const { data, error } = await query;

  if (error) {
    console.error("Error fetching scenarios:", error);
    return [];
  }

  return data || [];
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

  return data;
}

// =====================================================
// Scenario Attempts Queries
// =====================================================

export async function createScenarioAttempt(
  userId: string,
  scenarioId: string,
  initialState?: Record<string, unknown>
): Promise<ScenarioAttempt | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("scenario_attempts")
    .insert({
      user_id: userId,
      scenario_id: scenarioId,
      initial_persona_state: initialState || null,
      transcript: [],
    })
    .select()
    .single();

  if (error) {
    console.error("Error creating scenario attempt:", error);
    return null;
  }

  return data;
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

  return data;
}

export async function updateScenarioAttempt(
  attemptId: string,
  updates: Partial<ScenarioAttempt>
): Promise<ScenarioAttempt | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("scenario_attempts")
    .update(updates)
    .eq("id", attemptId)
    .select()
    .single();

  if (error) {
    console.error("Error updating scenario attempt:", error);
    return null;
  }

  return data;
}

export async function getUserScenarioAttempts(
  userId: string,
  limit: number = 10
): Promise<ScenarioAttempt[]> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("scenario_attempts")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) {
    console.error("Error fetching user scenario attempts:", error);
    return [];
  }

  return data || [];
}

// =====================================================
// User Progress Queries
// =====================================================

export async function getUserProgress(userId: string): Promise<UserProgress[]> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("user_progress")
    .select("*, learning_modules(*)")
    .eq("user_id", userId)
    .order("updated_at", { ascending: false });

  if (error) {
    console.error("Error fetching user progress:", error);
    return [];
  }

  return data || [];
}

export async function getUserProgressForModule(
  userId: string,
  moduleId: string
): Promise<UserProgress | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("user_progress")
    .select("*")
    .eq("user_id", userId)
    .eq("module_id", moduleId)
    .single();

  if (error) {
    if (error.code !== "PGRST116") {
      // Not found is ok
      console.error("Error fetching user progress for module:", error);
    }
    return null;
  }

  return data;
}

export async function createUserProgress(
  userId: string,
  moduleId: string
): Promise<UserProgress | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("user_progress")
    .insert({
      user_id: userId,
      module_id: moduleId,
      status: "in_progress",
    })
    .select()
    .single();

  if (error) {
    console.error("Error creating user progress:", error);
    return null;
  }

  return data;
}

export async function updateUserProgress(
  progressId: string,
  updates: Partial<UserProgress>
): Promise<UserProgress | null> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("user_progress")
    .update(updates)
    .eq("id", progressId)
    .select()
    .single();

  if (error) {
    console.error("Error updating user progress:", error);
    return null;
  }

  return data;
}

// =====================================================
// Learning Paths Queries
// =====================================================

export async function getLearningPaths(activeOnly: boolean = true): Promise<LearningPath[]> {
  const { createClient } = await import("./server");
  const supabase = await createClient();

  let query = supabase
    .from("learning_paths")
    .select("*")
    .order("title", { ascending: true });

  if (activeOnly) {
    query = query.eq("is_active", true);
  }

  const { data, error } = await query;

  if (error) {
    console.error("Error fetching learning paths:", error);
    return [];
  }

  return data || [];
}

