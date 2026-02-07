import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Supabase Auth Callback Route
 * Handles OAuth redirects and email confirmations
 */
export async function GET(req: NextRequest) {
  const reqUrl = new URL(req.url);
  const code = reqUrl.searchParams.get("code");
  const redirect = reqUrl.searchParams.get("redirect") || "/dashboard";

  if (code) {
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: () => cookies(),
      }
    );
    await supabase.auth.exchangeCodeForSession(code);
  }

  return NextResponse.redirect(new URL(redirect, req.url));
}
