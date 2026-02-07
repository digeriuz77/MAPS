import { createClientComponentClient } from "@supabase/auth-helpers-nextjs";
import type { Database } from "@/types/supabase";

/**
 * Supabase client for client-side components
 * Uses @supabase/auth-helpers-nextjs for Next.js App Router compatibility
 */
export const createClient = () => {
  return createClientComponentClient<Database>();
};

/**
 * Singleton instance for client-side usage
 * Note: In most cases, prefer using createClient() function
 * This is provided for convenience in non-React contexts
 */
let clientInstance: ReturnType<typeof createClient> | null = null;

export const getClient = () => {
  if (!clientInstance) {
    clientInstance = createClient();
  }
  return clientInstance;
};
