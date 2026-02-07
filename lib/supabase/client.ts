import { createBrowserClient } from "@supabase/ssr";
import type { Database } from "@/types/supabase";

/**
 * Supabase client for client-side components
 *
 * IMPORTANT: This uses @supabase/ssr which shares authentication state via cookies.
 * Unlike the old CDN approach, this client WILL have an authenticated session if
 * the user is logged in (session is established via server-side auth and shared via cookies).
 *
 * The browser client and server client both read from the same cookie jar, so:
 * - Server creates session → stored in cookies → browser client can read it
 * - No need for separate browser auth.signInWithPassword() call
 * - RLS policies work correctly because auth.uid() is available via cookies
 *
 * This avoids the "dual authentication mismatch" problem where browser clients
 * were anonymous while backend was authenticated.
 */
export function createClient() {
  return createBrowserClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}

/**
 * Singleton instance for client-side usage
 * Note: In most cases, prefer using createClient() function
 * This is provided for convenience in non-React contexts
 */
let clientInstance: ReturnType<typeof createClient> | null = null;

export function getClient() {
  if (!clientInstance) {
    clientInstance = createClient();
  }
  return clientInstance;
}

/**
 * Helper to check if there's an active session on the client
 * Returns true if user is authenticated (session exists in cookies)
 */
export async function isAuthenticated(): Promise<boolean> {
  const client = createClient();
  const { data: { session } } = await client.auth.getSession();
  return !!session;
}
