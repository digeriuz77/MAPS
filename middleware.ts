import { createServerClient } from "@supabase/ssr";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js middleware for Supabase authentication
 *
 * This middleware runs on every request (matched routes only) and:
 * 1. Refreshes the Supabase session from cookies
 * 2. Protects routes based on authentication status
 * 3. Redirects authenticated users away from auth pages
 *
 * The session is maintained via cookies set by Supabase auth helpers,
 * ensuring browser and server clients share the same auth state.
 *
 * IMPORTANT: Unlike the old CDN approach, we don't need to manually
 * manage browser auth - @supabase/ssr handles this via cookies.
 */
export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Get environment variables with fallbacks
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY;

  // If env vars are missing, skip auth checks and continue
  // This allows the app to run in environments where env vars aren't available at middleware runtime
  if (!supabaseUrl || !supabaseAnonKey) {
    console.warn('[Middleware] Supabase env vars not available, skipping auth checks');
    return NextResponse.next();
  }

  // Create Supabase client with getAll/setAll cookie methods
  const supabase = createServerClient(
    supabaseUrl,
    supabaseAnonKey,
    {
      cookies: {
        getAll() {
          return req.cookies.getAll();
        },
        setAll(cookiesToSet: Array<{ name: string; value: string; options?: Record<string, unknown> }>) {
          cookiesToSet.forEach(({ name, value }) => req.cookies.set(name, value));
        },
      },
    }
  );

  // Refresh session if expired - wrap in try/catch to handle errors gracefully
  let session = null;
  try {
    const { data } = await supabase.auth.getSession();
    session = data.session;
  } catch (error) {
    console.warn('[Middleware] Error getting session:', error);
    // Continue without session - user will be treated as unauthenticated
  }

  // Protected routes - require authentication
  const protectedRoutes = ["/dashboard", "/scenarios", "/mi-practice", "/analysis", "/progress", "/leaderboard"];
  const isProtectedRoute = protectedRoutes.some((route) => pathname.startsWith(route));

  // Auth routes - redirect to dashboard if already authenticated
  const authRoutes = ["/login", "/signup", "/forgot-password"];
  const isAuthRoute = authRoutes.some((route) => pathname.startsWith(route));

  // Redirect unauthenticated users from protected routes to login
  if (isProtectedRoute && !session) {
    const redirectUrl = new URL("/login", req.url);
    redirectUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(redirectUrl);
  }

  // Redirect authenticated users from auth routes to dashboard
  if (isAuthRoute && session) {
    return NextResponse.redirect(new URL("/dashboard", req.url));
  }

  return NextResponse.next();
}

/**
 * Matcher for middleware
 * Run on all routes except static files, api routes, and _next
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
