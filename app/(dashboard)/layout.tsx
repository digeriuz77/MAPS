import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { getCurrentUser } from "@/lib/supabase/auth";
import { redirect } from "next/navigation";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <div className="min-h-screen bg-maps-background">
      {/* Top Navigation Bar */}
      <nav className="bg-maps-surface border-b border-maps-gray-light sticky top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link href="/dashboard" className="flex items-center gap-2">
              <span className="text-2xl font-bold text-maps-teal">MAPS</span>
              <span className="hidden sm:inline text-sm text-gray-500">
                AI Persona System
              </span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-6">
              <NavLink href="/dashboard">Dashboard</NavLink>
              <NavLink href="/scenarios">Personas</NavLink>
              <NavLink href="/mi-practice">MI Practice</NavLink>
              <NavLink href="/analysis">Analysis</NavLink>
              <NavLink href="/progress">Progress</NavLink>
              <NavLink href="/leaderboard">Leaderboard</NavLink>
            </div>

            {/* User Menu */}
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-sm font-medium text-maps-navy">
                  {user.displayName}
                </div>
                <div className="text-xs text-gray-500">
                  Level {user.level ?? 1} • {user.total_points ?? 0} pts
                </div>
              </div>
              <form action="/auth/signout" method="post">
                <button
                  type="submit"
                  className="text-sm text-gray-600 hover:text-maps-teal transition-colors"
                >
                  Sign Out
                </button>
              </form>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation */}
      <div className="md:hidden bg-maps-surface border-b border-maps-gray-light py-2">
        <div className="container mx-auto px-4 flex gap-4 overflow-x-auto">
          <MobileNavLink href="/dashboard">Dashboard</MobileNavLink>
          <MobileNavLink href="/scenarios">Personas</MobileNavLink>
          <MobileNavLink href="/mi-practice">MI Practice</MobileNavLink>
          <MobileNavLink href="/analysis">Analysis</MobileNavLink>
          <MobileNavLink href="/progress">Progress</MobileNavLink>
          <MobileNavLink href="/leaderboard">Leaderboard</MobileNavLink>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">{children}</main>
    </div>
  );
}

function NavLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="text-sm font-medium text-gray-600 hover:text-maps-teal transition-colors"
    >
      {children}
    </Link>
  );
}

function MobileNavLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="text-sm font-medium text-gray-600 hover:text-maps-teal transition-colors whitespace-nowrap"
    >
      {children}
    </Link>
  );
}
