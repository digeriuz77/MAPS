import { getCurrentUser } from "@/lib/supabase/auth";
import { getUserProgress } from "@/lib/supabase/queries";
import { calculateLevel, getPointsToNextLevel, getLevelProgress } from "@/lib/gamification/scoring";
import Link from "next/link";

export default async function ProgressPage() {
  const user = await getCurrentUser();

  if (!user) {
    return null;
  }

  const progress = await getUserProgress(user.id);
  const completedModules = progress.filter((p) => p.status === "completed");
  const inProgressModules = progress.filter((p) => p.status === "in_progress");

  const levelProgress = getLevelProgress(user.total_points);
  const pointsToNext = getPointsToNextLevel(user.total_points);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-maps-navy">Your Progress</h1>
        <p className="text-gray-600 mt-1">
          Track your MI training journey
        </p>
      </div>

      {/* Overview Cards */}
      <div className="grid md:grid-cols-4 gap-4">
        <StatCard
          label="Current Level"
          value={user.level.toString()}
          color="teal"
        />
        <StatCard
          label="Total Points"
          value={user.total_points.toString()}
          color="blue"
        />
        <StatCard
          label="Completed"
          value={completedModules.length.toString()}
          color="green"
        />
        <StatCard
          label="In Progress"
          value={inProgressModules.length.toString()}
          color="purple"
        />
      </div>

      {/* Level Progress */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-maps-navy">Level Progress</h2>
          <span className="text-sm text-gray-500">
            {pointsToNext} points to Level {user.level + 1}
          </span>
        </div>
        <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-maps-teal to-maps-blue transition-all"
            style={{ width: `${levelProgress}%` }}
          />
        </div>
        <div className="mt-2 text-right text-sm text-gray-600">
          {Math.round(levelProgress)}% complete
        </div>
      </div>

      {/* Completed Modules */}
      {completedModules.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-maps-navy mb-4">
            Completed Modules
          </h2>
          <div className="space-y-3">
            {completedModules.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <div className="font-medium text-maps-navy">
                    {item.learning_modules?.title || "Module"}
                  </div>
                  <div className="text-sm text-gray-500">
                    Completed:{" "}
                    {item.completed_at
                      ? new Date(item.completed_at).toLocaleDateString()
                      : "N/A"}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-maps-teal font-semibold">
                    {item.completion_score || 0}%
                  </div>
                  <div className="text-sm text-gray-500">
                    {item.points_earned || 0} pts
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* In Progress Modules */}
      {inProgressModules.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-maps-navy mb-4">
            Continue Learning
          </h2>
          <div className="space-y-3">
            {inProgressModules.map((item) => (
              <Link
                key={item.id}
                href={`/mi-practice/${item.module_id}`}
                className="flex items-center justify-between p-3 bg-maps-teal/10 rounded-lg hover:bg-maps-teal/20 transition-colors"
              >
                <div>
                  <div className="font-medium text-maps-navy">
                    {item.learning_modules?.title || "Module"}
                  </div>
                  <div className="text-sm text-gray-500">
                    Started:{" "}
                    {new Date(item.started_at).toLocaleDateString()}
                  </div>
                </div>
                <div className="text-maps-teal font-medium">
                  Continue →
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Stats Breakdown */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-semibold text-maps-navy mb-3">MI Skills</h3>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Change Talk Evoked</span>
              <span className="font-medium text-maps-navy">
                {user.change_talk_evoked}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Reflections Offered</span>
              <span className="font-medium text-maps-navy">
                {user.reflections_offered}
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="font-semibold text-maps-navy mb-3">Technique Mastery</h3>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Open Questions</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-maps-teal" style={{ width: "70%" }} />
                </div>
              </div>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Reflections</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-maps-blue" style={{ width: "60%" }} />
                </div>
              </div>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Affirmations</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-maps-purple" style={{ width: "80%" }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-center gap-4">
        <Link href="/mi-practice" className="btn-primary">
          Continue Learning
        </Link>
        <Link href="/leaderboard" className="btn-outline">
          View Leaderboard
        </Link>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: "teal" | "blue" | "green" | "purple";
}) {
  const colorClasses = {
    teal: "bg-maps-teal text-white",
    blue: "bg-maps-blue text-white",
    green: "bg-green-500 text-white",
    purple: "bg-maps-purple text-white",
  };

  return (
    <div className="card text-center">
      <div className={`w-12 h-12 rounded-full ${colorClasses[color]} flex items-center justify-center text-xl font-bold mx-auto mb-2`}>
        {value}
      </div>
      <div className="text-sm text-gray-600">{label}</div>
    </div>
  );
}
