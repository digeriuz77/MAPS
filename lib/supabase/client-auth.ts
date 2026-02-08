import { createClient } from "./client";
import type { UserProfile } from "@/types/supabase";

/**
 * Client-side authentication utility functions
 * IMPORTANT: These functions use the BROWSER client and should only be called
 * from Client Components ("use client").
 * For server-side auth, use the functions from ./auth.ts
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
 * Get the current authenticated user (CLIENT-SIDE)
 * Returns null if not authenticated
 */
export async function getCurrentUserClient(): Promise<AuthUser | null> {
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
 * Sign in with email and password (CLIENT-SIDE)
 */
export async function signInClient(email: string, password: string) {
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
 * Sign up with email and password (CLIENT-SIDE)
 * Creates user profile in user_profiles table
 */
export async function signUpClient(
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
 * Sign out the current user (CLIENT-SIDE)
 */
export async function signOutClient() {
    const supabase = createClient();
    const { error } = await supabase.auth.signOut();

    if (error) {
        throw new Error(error.message);
    }
}

/**
 * Check if user has a specific role (CLIENT-SIDE)
 */
export async function hasRoleClient(role: "FULL" | "CONTROL"): Promise<boolean> {
    const user = await getCurrentUserClient();
    return user?.role === role;
}

/**
 * Request password reset email (CLIENT-SIDE)
 * Sends an email with a reset link to the user
 */
export async function requestPasswordReset(email: string) {
    const supabase = createClient();
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
    });

    if (error) {
        throw new Error(error.message);
    }
}

/**
 * Update user password (CLIENT-SIDE)
 * Used after user clicks the reset link from email
 */
export async function updatePassword(newPassword: string) {
    const supabase = createClient();
    const { error } = await supabase.auth.updateUser({
        password: newPassword,
    });

    if (error) {
        throw new Error(error.message);
    }
}
