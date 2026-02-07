import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import type { Database } from "@/types/supabase";

/**
 * Supabase client for server-side components (Server Components, Route Handlers, Middleware)
 *
 * This client reads authentication state from cookies and is the PRIMARY way to
 * access Supabase in Next.js App Router.
 *
 * Key advantages over browser client:
 * - Always has access to the latest session from cookies
 * - Works in Server Components, Route Handlers, and Middleware
 * - Can use service role key for admin operations (see createAdminClient)
 *
 * The cookie-based session is shared between server and browser, ensuring
 * consistent authentication state across the application.
 */
export async function createClient() {
  const cookieStore = cookies();

  return createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: () => cookieStore,
    }
  );
}

/**
 * Admin client with service role key
 * Use this for operations that bypass RLS (e.g., admin operations)
 * NEVER expose this to client-side code
 */
import { createClient as createSupabaseClient } from "@supabase/supabase-js";

export function createAdminClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

  if (!supabaseUrl || !supabaseServiceKey) {
    throw new Error("Missing Supabase environment variables");
  }

  return createSupabaseClient<Database>(supabaseUrl, supabaseServiceKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });
}
