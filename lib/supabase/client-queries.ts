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
 * CLIENT-SIDE Database query utilities for MAPS
 * Use these from Client Components ("use client")
 * For server-side queries, use functions from ./queries.ts
 */

// =====================================================
// User Profile Queries (CLIENT-SIDE)
// =====================================================

export async function getUserProfileClient(userId: string): Promise<UserProfile | null> {
    const { createClient } = await import("./client");
    const supabase = createClient();

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

// =====================================================
// Learning Modules Queries (CLIENT-SIDE)
// =====================================================

export async function getLearningModulesClient(options: {
    active?: boolean;
    published?: boolean;
    difficulty?: string;
    limit?: number;
}): Promise<LearningModule[]> {
    const { createClient } = await import("./client");
    const supabase = createClient();

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

export async function getLearningModuleByIdClient(id: string): Promise<LearningModule | null> {
    const { createClient } = await import("./client");
    const supabase = createClient();

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

// =====================================================
// Scenarios Queries (CLIENT-SIDE)
// =====================================================

export async function getScenariosClient(activeOnly: boolean = true): Promise<Scenario[]> {
    const { createClient } = await import("./client");
    const supabase = createClient();

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

export async function getScenarioByIdClient(id: string): Promise<Scenario | null> {
    const { createClient } = await import("./client");
    const supabase = createClient();

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
// Scenario Attempts Queries (CLIENT-SIDE)
// =====================================================

export async function createScenarioAttemptClient(
    scenarioId: string,
    userId: string
): Promise<ScenarioAttempt | null> {
    const { createClient } = await import("./client");
    const supabase = createClient();

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

export async function getScenarioAttemptClient(attemptId: string): Promise<ScenarioAttempt | null> {
    const { createClient } = await import("./client");
    const supabase = createClient();

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

export async function updateScenarioAttemptClient(
    attemptId: string,
    updates: Partial<ScenarioAttempt>
): Promise<ScenarioAttempt | null> {
    const { createClient } = await import("./client");
    const supabase = createClient();

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

export async function getUserScenarioAttemptsClient(
    userId: string,
    limit?: number
): Promise<ScenarioAttempt[]> {
    const { createClient } = await import("./client");
    const supabase = createClient();

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
// User Progress Queries (CLIENT-SIDE)
// =====================================================

export async function getUserProgressClient(userId: string): Promise<UserProgress[]> {
    const { createClient } = await import("./client");
    const supabase = createClient();

    const { data, error } = await supabase
        .from("user_progress")
        .select("*")
        .eq("user_id", userId);

    if (error) {
        console.error("Error fetching user progress:", error);
        return [];
    }

    return (data as UserProgress[]) || [];
}

export async function getUserProgressForModuleClient(
    userId: string,
    moduleId: string
): Promise<UserProgress | null> {
    const { createClient } = await import("./client");
    const supabase = createClient();

    const { data, error } = await supabase
        .from("user_progress")
        .select("*")
        .eq("user_id", userId)
        .eq("module_id", moduleId)
        .single();

    if (error) {
        // PGRST116 means no rows returned, which is fine for non-existent progress
        if (error.code !== "PGRST116") {
            console.error("Error fetching user progress for module:", error);
        }
        return null;
    }

    return data as UserProgress | null;
}

export async function createUserProgressClient(
    userId: string,
    moduleId: string,
    data: Partial<UserProgress> = {}
): Promise<UserProgress | null> {
    const { createClient } = await import("./client");
    const supabase = createClient();

    const { data: progress, error } = await (supabase as any)
        .from("user_progress")
        .insert({
            user_id: userId,
            module_id: moduleId,
            status: "in_progress",
            ...data,
        })
        .select()
        .single();

    if (error) {
        console.error("Error creating user progress:", error);
        return null;
    }

    return progress as UserProgress | null;
}

export async function updateUserProgressClient(
    userId: string,
    moduleId: string,
    updates: Partial<UserProgress>
): Promise<UserProgress | null> {
    const { createClient } = await import("./client");
    const supabase = createClient();

    const { data, error } = await (supabase as any)
        .from("user_progress")
        .update(updates)
        .eq("user_id", userId)
        .eq("module_id", moduleId)
        .select()
        .single();

    if (error) {
        console.error("Error updating user progress:", error);
        return null;
    }

    return data as UserProgress | null;
}

export async function completeUserProgressClient(
    userId: string,
    moduleId: string,
    score: number
): Promise<UserProgress | null> {
    const { createClient } = await import("./client");
    const supabase = createClient();

    const { data, error } = await (supabase as any)
        .from("user_progress")
        .update({
            status: "completed",
            completed_at: new Date().toISOString(),
            completion_score: score,
        })
        .eq("user_id", userId)
        .eq("module_id", moduleId)
        .select()
        .single();

    if (error) {
        console.error("Error completing user progress:", error);
        return null;
    }

    return data as UserProgress | null;
}

// =====================================================
// Learning Paths Queries (CLIENT-SIDE)
// =====================================================

export async function getLearningPathsClient(activeOnly: boolean = true): Promise<LearningPath[]> {
    const { createClient } = await import("./client");
    const supabase = createClient();

    let query = supabase
        .from("learning_paths")
        .select("*")
        .order("display_order", { ascending: true });

    if (activeOnly) {
        query = query.eq("is_active", true);
    }

    const { data, error } = await query;

    if (error) {
        console.error("Error fetching learning paths:", error);
        return [];
    }

    return (data as LearningPath[]) || [];
}
