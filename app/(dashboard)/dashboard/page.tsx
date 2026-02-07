import { getCurrentUser } from "@/lib/supabase/auth";
import {
  getUserProgress,
  getUserScenarioAttempts,
  getLearningModules,
} from "@/lib/supabase/queries";
import Link from "next/link";

export default async function DashboardPage() {
  const user = await getCurrentUser();

  if (!user) {
    return null;
  }

  const [progress, attempts, modules] = await Promise.all([
    getUserProgress(user.id),
    getUserScenarioAttempts(user.id, 5),
    getLearningModules({ active: true, limit: 3 }),
  ]);

  const completedModules = progress.filter((p) => p.status === "completed").length;
  const inProgressModules = progress.filter((p) => p.status === "in_progress").length;
  const totalAttempts = attempts.length;

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div>
        <h1 className="text-3xl font-bold text-maps-navy">
          Welcome back, {user.displayName}!
        </h1>
        <p className="text-gray-600 mt-1">
          Continue your MI training journey
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard
          title="Current Level"
          value={user.level.toString()}
          subtitle={`${user.total_points} total points`}
          color="teal"
        />
        <StatCard
          title="Modules Completed"
          value={completedModules.toString()}
          subtitle={`${inProgressModules} in progress`}
          color="blue"
        />
        <StatCard
          title="Practice Sessions"
          value={totalAttempts.toString()}
          subtitle="Scenario attempts"
          color="purple"
        />
        <StatCard
          title="Change Talk Evoked"
          value={user.change_talk_evoked.toString()}
          subtitle="MI technique mastery"
          color="green"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6">
        <ActionCard
          title="Practice with AI Personas"
          description="Engage in realistic MI conversations with nuanced AI personas"
          href="/scenarios"
          icon="💬"
          buttonText="Start Practice"
        />
        <ActionCard
          title="Continue Learning"
          description="Work through structured MI practice modules"
          href="/mi-practice"
          icon="📚"
          buttonText="Browse Modules"
        />
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-xl font-semibold text-maps-navy mb-4">Recent Activity</h2>
        {attempts.length > 0 ? (
          <div className="space-y-3">
            {attempts.map((attempt) => (
              <div
                key={attempt.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <div className="font-medium text-maps-navy">
                    Scenario Attempt
                  </div>
                  <div className="text-sm text-gray-500">
                    {new Date(attempt.created_at).toLocaleDateString()} •{" "}
                    {attempt.turn_count} turns
                  </div>
                </div>
                <div className="text-sm text-maps-teal font-medium">
                  {attempt.completed_at ? "Completed" : "In Progress"}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">
            No activity yet. Start a practice session to see your progress!
          </p>
        )}
      </div>

      {/* Recommended Modules */}
      {modules.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold text-maps-navy mb-4">
            Recommended Modules
          </h2>
          <div className="grid md:grid-cols-3 gap-4">
            {modules.map((module) => (
              <Link
                key={module.id}
                href={`/mi-practice/${module.id}`}
                className="block p-4 bg-gray-50 rounded-lg hover:bg-maps-teal/10 transition-colors"
              >
                <div className="text-sm text-maps-teal font-medium mb-1">
                  {module.difficulty_level}
                </div>
                <div className="font-semibold text-maps-navy mb-2">
                  {module.title}
                </div>
                <div className="text-sm text-gray-500 line-clamp-2">
                  {module.description || module.learning_objective}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  title,
  value,
  subtitle,
  color,
}: {
  title: string;
  value: string;
  subtitle: string;
  color: "teal" | "blue" | "purple" | "green";
}) {
  const colorClasses = {
    teal: "bg-maps-teal text-white",
    blue: "bg-maps-blue text-white",
    purple: "bg-maps-purple text-white",
    green: "bg-green-500 text-white",
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm text-gray-500 mb-1">{title}</div>
          <div className="text-3xl font-bold text-maps-navy">{value}</div>
          <div className="text-sm text-gray-500 mt-1">{subtitle}</div>
        </div>
        <div className={`w-12 h-12 rounded-full ${colorClasses[color]} flex items-center justify-center text-xl font-bold`}>
          {value[0]}
        </div>
      </div>
    </div>
  );
}

function ActionCard({
  title,
  description,
  href,
  icon,
  buttonText,
}: {
  title: string;
  description: string;
  href: string;
  icon: string;
  buttonText: string;
}) {
  return (
    <div className="card">
      <div className="flex items-start gap-4">
        <div className="text-4xl">{icon}</div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-maps-navy mb-1">{title}</h3>
          <p className="text-gray-600 mb-4">{description}</p>
          <Link href={href} className="btn-primary inline-block">
            {buttonText}
          </Link>
        </div>
      </div>
    </div>
  );
}
