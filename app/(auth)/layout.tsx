import Link from "next/link";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-maps-navy via-maps-navy-light to-maps-blue flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-block">
            <h1 className="text-4xl font-bold text-white">MAPS</h1>
            <p className="text-maps-teal-light text-sm mt-1">
              AI Persona System for MI Training
            </p>
          </Link>
        </div>

        {/* Auth Form Container */}
        <div className="card bg-white shadow-xl">
          {children}
        </div>

        {/* Footer Links */}
        <div className="text-center mt-6 text-gray-400 text-sm">
          <Link href="/" className="hover:text-maps-teal-light transition-colors">
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
