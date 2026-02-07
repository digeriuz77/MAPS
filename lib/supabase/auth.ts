import { createClient } from "./server";
import type { UserProfile } from "@/types/supabase";

/**
 * Authentication utility functions
 * IMPORTANT: These functions use the SERVER client and should only be called
 * from Server Components, Route Handlers, or Server Actions.
 * For client-side auth, use the Supabase client directly.
 */

export interface AuthUser {
  id: string;
  email: string;
  displayName?: string;
  role?: "FULL" | "CONTROL";
  level?: number;
  total_points?: number;
  modules_completed?: number;
  change_talk_evoked?: number;
  reflections_offered?: number;
}

/**
 * Get the current authenticated user (SERVER-SIDE ONLY)
 * Returns null if not authenticated
 */
export async function getCurrentUser(): Promise<AuthUser | null> {
  try {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return null;
    }

    // Fetch user profile data
    const { data: profile } = await supabase
      .from("user_profiles")
      .select("*")
      .eq("id", user.id)
      .single();

    const typedProfile = profile as UserProfile | null;

    return {
      id: user.id,
      email: user.email || "",
      displayName: typedProfile?.display_name || user.email?.split("@")[0],
      role: typedProfile?.role || "FULL",
      level: typedProfile?.level || 1,
      total_points: typedProfile?.total_points || 0,
      modules_completed: typedProfile?.modules_completed || 0,
      change_talk_evoked: typedProfile?.change_talk_evoked || 0,
      reflections_offered: typedProfile?.reflections_offered || 0,
    };
  } catch (error) {
    console.error("Error fetching current user:", error);
    return null;
  }
}

/**
 * Sign in with email and password (SERVER-SIDE ONLY)
 */
export async function signIn(email: string, password: string) {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    throw new Error(error.message);
  }

  return data;
}

/**
 * Sign up with email and password (SERVER-SIDE ONLY)
 * Creates user profile in user_profiles table
 */
export async function signUp(
  email: string,
  password: string,
  displayName?: string
) {
  const supabase = await createClient();

  // First, create the auth user
  const { data: authData, error: authError } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        display_name: displayName || email.split("@")[0],
      },
    },
  });

  if (authError) {
    throw new Error(authError.message);
  }

  // Note: User profile will be created automatically by the database trigger
  // See the handle_new_user() function in the migration

  return authData;
}

/**
 * Sign out the current user (SERVER-SIDE ONLY)
 */
export async function signOut() {
  const supabase = await createClient();
  const { error } = await supabase.auth.signOut();

  if (error) {
    throw new Error(error.message);
  }
}

/**
 * Check if user has a specific role
 */
export async function hasRole(role: "FULL" | "CONTROL"): Promise<boolean> {
  const user = await getCurrentUser();
  return user?.role === role;
}
