import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

type CookieToSet = {
  name: string;
  value: string;
  options?: Record<string, unknown>;
};

/**
 * Supabase Auth Callback Route
 * Handles OAuth redirects, email confirmations, and password resets
 */
export async function GET(req: NextRequest) {
  const reqUrl = new URL(req.url);
  const code = reqUrl.searchParams.get("code");
  const type = reqUrl.searchParams.get("type");
  const redirect = reqUrl.searchParams.get("redirect") || "/dashboard";

  if (code) {
    const cookieStore = await cookies();
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll() {
            return cookieStore.getAll();
          },
          setAll(cookiesToSet: CookieToSet[]) {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            );
          },
        },
      }
    );
    await supabase.auth.exchangeCodeForSession(code);
  }

  // Handle password reset redirect
  if (type === "recovery") {
    return NextResponse.redirect(new URL("/reset-password", req.url));
  }

  return NextResponse.redirect(new URL(redirect, req.url));
}
