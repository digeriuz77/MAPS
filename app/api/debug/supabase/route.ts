import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

/**
 * Debug endpoint to test Supabase connection and get table info via RPC
 * GET /api/debug/supabase
 *
 * Uses the get_debug_info() RPC function for efficient single-call data retrieval
 */
export async function GET() {
    try {
        const supabase = await createClient();

        // Call the RPC function for efficient data retrieval
        const { data, error } = await supabase.rpc("get_debug_info");

        if (error) {
            // Fallback to manual discovery if RPC doesn't exist yet
            console.warn("RPC function error, falling back to manual discovery:", error.message);
            return await getDebugInfoManual(supabase, error.message);
        }

        // Type the RPC response
        type DebugRpcResponse = {
            scenarios: { count: number; sample: unknown[] };
            mi_practice_modules: { count: number; sample: unknown[] };
            scenario_attempts_count: number;
            profiles_count: number;
            timestamp: string;
        };

        const debugData = data as DebugRpcResponse | null;

        return NextResponse.json({
            connection: "ok",
            method: "rpc",
            ...(debugData ?? {}),
        });
    } catch (error) {
        return NextResponse.json(
            {
                connection: "failed",
                error: error instanceof Error ? error.message : String(error),
            },
            { status: 500 }
        );
    }
}

/**
 * Type definitions for database records
 */
type ScenarioRecord = {
    id: string;
    code: string;
    title: string;
    mi_skill_category: string | null;
    difficulty: string | null;
    [key: string]: unknown;
};

type ModuleRecord = {
    id: string;
    code: string;
    title: string;
    difficulty_level: string | null;
    mi_focus_area: string | null;
    [key: string]: unknown;
};

/**
 * Fallback manual discovery if RPC function doesn't exist
 */
async function getDebugInfoManual(
    supabase: Awaited<ReturnType<typeof createClient>>,
    rpcError?: string
) {
    // Get scenarios
    const { data: scenarios, error: scenariosError, count: scenariosCount } = await supabase
        .from("scenarios")
        .select("*", { count: "exact" })
        .eq("is_active", true)
        .limit(5);

    // Get MI practice modules
    const { data: modules, error: modulesError, count: modulesCount } = await supabase
        .from("mi_practice_modules")
        .select("*", { count: "exact" })
        .eq("is_active", true)
        .limit(5);

    // Get counts
    const { count: attemptsCount } = await supabase
        .from("scenario_attempts")
        .select("*", { count: "exact", head: true });

    const { count: profilesCount } = await supabase
        .from("profiles")
        .select("*", { count: "exact", head: true });

    return NextResponse.json({
        connection: "ok",
        method: "manual",
        rpc_error: rpcError || "RPC function not available",
        hint: "Run migration 0008_fix_debug_rpc_columns.sql in Supabase SQL Editor",
        scenarios: {
            count: scenariosCount || 0,
            error: scenariosError?.message,
            sample: (scenarios as ScenarioRecord[] | null)?.map(s => ({
                id: s.id,
                code: s.code,
                title: s.title,
                mi_skill_category: s.mi_skill_category,
                difficulty: s.difficulty,
            })) || [],
        },
        mi_practice_modules: {
            count: modulesCount || 0,
            error: modulesError?.message,
            sample: (modules as ModuleRecord[] | null)?.map(m => ({
                id: m.id,
                code: m.code,
                title: m.title,
                difficulty_level: m.difficulty_level,
                mi_focus_area: m.mi_focus_area,
            })) || [],
        },
        scenario_attempts_count: attemptsCount || 0,
        profiles_count: profilesCount || 0,
    });
}
