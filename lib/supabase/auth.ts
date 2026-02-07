import { createClient } from "./client";

/**
 * Authentication utility functions
 */

export interface AuthUser {
  id: string;
  email: string;
  displayName?: string;
  role?: "FULL" | "CONTROL";
}

/**
 * Get the current authenticated user
 * Returns null if not authenticated
 */
export async function getCurrentUser(): Promise<AuthUser | null> {
  try {
    const supabase = createClient();
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

    return {
      id: user.id,
      email: user.email || "",
      displayName: profile?.display_name || user.email?.split("@")[0],
      role: profile?.role || "FULL",
    };
  } catch (error) {
    console.error("Error fetching current user:", error);
    return null;
  }
}

/**
 * Sign in with email and password
 */
export async function signIn(email: string, password: string) {
  const supabase = createClient();
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
 * Sign up with email and password
 * Creates user profile in user_profiles table
 */
export async function signUp(
  email: string,
  password: string,
  displayName?: string
) {
  const supabase = createClient();

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
 * Sign out the current user
 */
export async function signOut() {
  const supabase = createClient();
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
