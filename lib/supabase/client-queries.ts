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
 *
 * UPDATED FOR ACTUAL SUPABASE SCHEMA:
 * - scenarios table uses 'title' (not persona_name)
 * - mi_practice_modules (not learning_modules)
 * - profiles table (not user_profiles)
 * - scenario_attempts uses 'transcript' (not conversation_history)
 * - mi_learning_paths (not learning_paths)
 */

// =====================================================
// User Profile Queries (CLIENT-SIDE)
// Uses 'profiles' table (actual table name in Supabase)
// =====================================================

export async function getUserProfileClient(userId: string): Promise<UserProfile | null> {
    const { createClient } = await import("./client");
    const supabase = createClient();

    const { data, error } = await supabase
        .from("profiles")
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
// MI Practice Modules Queries (CLIENT-SIDE)
// Uses 'mi_practice_modules' table (actual table name in Supabase)
// =====================================================

export async function getLearningModulesClient(options: {
    active?: boolean;
    difficulty?: string;
    limit?: number;
    focusArea?: string;
}): Promise<LearningModule[]> {
    const { createClient } = await import("./client");
    const supabase = createClient();

    let query = supabase
        .from("mi_practice_modules")
        .select("*")
        .order("created_at", { ascending: true });

    if (options.active !== undefined) {
        query = query.eq("is_active", options.active);
    }
    if (options.difficulty) {
        query = query.eq("difficulty_level", options.difficulty);
    }
    if (options.focusArea) {
        query = query.eq("mi_focus_area", options.focusArea);
    }
    if (options.limit) {
        query = query.limit(options.limit);
    }

    const { data, error } = await query;

    if (error) {
        console.error("Error fetching MI practice modules:", error);
        return [];
    }

    return data || [];
}

export async function getLearningModuleByIdClient(id: string): Promise<LearningModule | null> {
    const { createClient } = await import("./client");
    const supabase = createClient();

    const { data, error } = await supabase
        .from("mi_practice_modules")
        .select("*")
        .eq("id", id)
        .single();

    if (error) {
        console.error("Error fetching MI practice module:", error);
        return null;
    }

    return data;
}

// =====================================================
// Scenarios Queries (CLIENT-SIDE)
// Uses 'title' column (not persona_name)
// =====================================================

export async function getScenariosClient(activeOnly: boolean = true): Promise<Scenario[]> {
    const { createClient } = await import("./client");
    const supabase = createClient();

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
// Uses correct column names: transcript (not conversation_history)
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
            transcript: [],
            initial_persona_state: {},
            current_persona_state: {},
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
// STUB FUNCTIONS - Schema doesn't match expected types
// Use mi_practice_attempts table for module-specific progress
// =====================================================

export async function getUserProgressClient(userId: string): Promise<UserProgress[]> {
    console.warn("getUserProgressClient: mi_user_progress table has different schema");
    return [];
}

export async function getUserProgressForModuleClient(
    userId: string,
    moduleId: string
): Promise<UserProgress | null> {
    // The mi_user_progress table doesn't have module_id - it tracks overall progress
    // For module-specific progress, use mi_practice_attempts table
    console.warn("getUserProgressForModuleClient: Use mi_practice_attempts table for module progress");
    return null;
}

export async function createUserProgressClient(
    userId: string,
    moduleId: string,
    data: Partial<UserProgress> = {}
): Promise<UserProgress | null> {
    console.warn("createUserProgressClient: Schema mismatch - use mi_practice_attempts table");
    return null;
}

export async function updateUserProgressClient(
    userId: string,
    moduleId: string,
    updates: Partial<UserProgress>
): Promise<UserProgress | null> {
    console.warn("updateUserProgressClient: Schema mismatch - use mi_practice_attempts table");
    return null;
}

export async function completeUserProgressClient(
    userId: string,
    moduleId: string,
    score: number
): Promise<UserProgress | null> {
    console.warn("completeUserProgressClient: Schema mismatch - use mi_practice_attempts table");
    return null;
}

// =====================================================
// Learning Paths Queries (CLIENT-SIDE)
// Uses 'mi_learning_paths' table (actual table name in Supabase)
// =====================================================

export async function getLearningPathsClient(activeOnly: boolean = true): Promise<LearningPath[]> {
    const { createClient } = await import("./client");
    const supabase = createClient();

    let query = supabase
        .from("mi_learning_paths")
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

    return (data as LearningPath[]) || [];
}
