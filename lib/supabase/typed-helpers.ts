/**
 * Typed Supabase Helpers
 *
 * Helper functions that use our database types instead of 'as any' workarounds.
 * These provide type safety while working with Supabase.
 */

import type {
  ScenarioAttemptInsert,
  ScenarioAttemptUpdate,
  MiPracticeAttemptInsert,
  MiPracticeAttemptUpdate,
} from "@/types/database";

/**
 * Type-safe insert for scenario_attempts
 */
export function insertScenarioAttempt(data: ScenarioAttemptInsert): Record<string, unknown> {
  return data as unknown as Record<string, unknown>;
}

/**
 * Type-safe update for scenario_attempts
 * Filters out undefined values to prevent overwriting with null
 */
export function updateScenarioAttempt(data: ScenarioAttemptUpdate): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(data)) {
    if (value !== undefined) {
      result[key] = value;
    }
  }
  return result;
}

/**
 * Type-safe insert for mi_practice_attempts
 */
export function insertMiPracticeAttempt(data: MiPracticeAttemptInsert): Record<string, unknown> {
  return data as unknown as Record<string, unknown>;
}

/**
 * Type-safe update for mi_practice_attempts
 * Filters out undefined values to prevent overwriting with null
 */
export function updateMiPracticeAttempt(data: MiPracticeAttemptUpdate): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(data)) {
    if (value !== undefined) {
      result[key] = value;
    }
  }
  return result;
}

/**
 * Helper to cast Supabase client to allow typed inserts/updates
 * This is a controlled type assertion that's safer than 'as any'
 */
export type TypedSupabaseClient = {
  from: (table: string) => {
    insert: (data: Record<string, unknown>) => {
      select: () => {
        single: () => Promise<{
          data: unknown;
          error: { message: string } | null;
        }>;
      };
    };
    update: (data: Record<string, unknown>) => {
      eq: (column: string, value: string) => {
        select: () => {
          single: () => Promise<{
            data: unknown;
            error: { message: string } | null;
          }>;
        };
      };
    };
  };
};

/**
 * Wrap a Supabase client to allow typed operations
 */
export function asTypedClient(client: unknown): TypedSupabaseClient {
  return client as TypedSupabaseClient;
}
