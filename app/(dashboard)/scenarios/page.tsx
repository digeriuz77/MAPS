import { getScenarios } from "@/lib/supabase/queries";
import Link from "next/link";

export const dynamic = 'force-dynamic';

export default async function ScenariosPage() {
  const scenarios = await getScenarios();

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-maps-navy">AI Persona Practice</h1>
        <p className="text-gray-600 mt-1">
          Practice Motivational Interviewing with sophisticated AI personas
        </p>
      </div>

      {/* Personas Grid */}
      {scenarios.length > 0 ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {scenarios.map((scenario) => (
            <Link
              key={scenario.id}
              href={`/scenarios/${scenario.id}/chat`}
              className="card hover:shadow-medium transition-all cursor-pointer group"
            >
              <div className="text-center">
                {/* Avatar */}
                <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-maps-teal to-maps-blue flex items-center justify-center text-white text-3xl font-bold group-hover:scale-110 transition-transform">
                  {scenario.persona_name.charAt(0)}
                </div>

                {/* Name */}
                <h3 className="text-lg font-semibold text-maps-navy mb-2">
                  {scenario.persona_name}
                </h3>

                {/* Description */}
                <p className="text-sm text-gray-600 line-clamp-3 mb-4">
                  {scenario.persona_description}
                </p>

                {/* CTA */}
                <div className="text-maps-teal font-medium text-sm group-hover:text-maps-teal-dark">
                  Start Practice →
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-gray-500">No personas available yet.</p>
        </div>
      )}

      {/* Info Section */}
      <div className="card bg-maps-navy text-white">
        <h3 className="text-lg font-semibold mb-2">About AI Persona Practice</h3>
        <p className="text-gray-300 text-sm">
          Our AI personas are designed to be nuanced, sophisticated, and challenging.
          They simulate real client conversations with context awareness, emotional states,
          and realistic responses. Each persona has unique characteristics and will respond
          authentically based on your MI approach.
        </p>
      </div>
    </div>
  );
}
