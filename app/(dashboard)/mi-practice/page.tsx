import { getLearningModules, getLearningPaths } from "@/lib/supabase/queries";
import Link from "next/link";

export default async function MIPracticePage() {
  const [modules, paths] = await Promise.all([
    getLearningModules({ active: true }),
    getLearningPaths({ activeOnly: true }),
  ]);

  // Group modules by difficulty
  const beginnerModules = modules.filter((m) => m.difficulty_level === "beginner");
  const intermediateModules = modules.filter((m) => m.difficulty_level === "intermediate");
  const advancedModules = modules.filter((m) => m.difficulty_level === "advanced");

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-maps-navy">MI Practice Modules</h1>
        <p className="text-gray-600 mt-1">
          Structured learning modules to develop your Motivational Interviewing skills
        </p>
      </div>

      {/* Learning Paths */}
      {paths.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold text-maps-navy mb-4">Learning Paths</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {paths.map((path) => (
              <Link
                key={path.id}
                href={`/mi-practice/path/${path.id}`}
                className="card hover:shadow-medium transition-all cursor-pointer group"
              >
                <div className="flex items-start gap-3">
                  <div className="text-2xl">📚</div>
                  <div>
                    <h3 className="font-semibold text-maps-navy group-hover:text-maps-teal transition-colors">
                      {path.title}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                      {path.description}
                    </p>
                    <div className="text-xs text-gray-500 mt-2">
                      {path.module_sequence.length} modules •{" "}
                      {path.estimated_total_minutes || 30} min
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Module Library */}
      <section>
        <h2 className="text-xl font-semibold text-maps-navy mb-4">Module Library</h2>

        {/* Beginner */}
        {beginnerModules.length > 0 && (
          <ModuleSection
            title="Beginner"
            modules={beginnerModules}
            color="green"
          />
        )}

        {/* Intermediate */}
        {intermediateModules.length > 0 && (
          <ModuleSection
            title="Intermediate"
            modules={intermediateModules}
            color="blue"
          />
        )}

        {/* Advanced */}
        {advancedModules.length > 0 && (
          <ModuleSection
            title="Advanced"
            modules={advancedModules}
            color="purple"
          />
        )}
      </section>
    </div>
  );
}

function ModuleSection({
  title,
  modules,
  color,
}: {
  title: string;
  modules: typeof getLearningModules;
  color: "green" | "blue" | "purple";
}) {
  const colorClasses = {
    green: "bg-green-100 text-green-800",
    blue: "bg-blue-100 text-blue-800",
    purple: "bg-purple-100 text-purple-800",
  };

  return (
    <div className="mb-8">
      <h3 className="text-lg font-semibold text-maps-navy mb-3 flex items-center gap-2">
        <span className={`px-2 py-1 rounded text-xs font-medium ${colorClasses[color]}`}>
          {title}
        </span>
        <span className="text-sm font-normal text-gray-500">
          {modules.length} modules
        </span>
      </h3>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {modules.map((module) => (
          <ModuleCard key={module.id} module={module} />
        ))}
      </div>
    </div>
  );
}

function ModuleCard({ module }: { module: Awaited<ReturnType<typeof getLearningModules>>[number] }) {
  return (
    <Link
      href={`/mi-practice/${module.id}`}
      className="card hover:shadow-medium transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h4 className="font-semibold text-maps-navy group-hover:text-maps-teal transition-colors">
            {module.title}
          </h4>
          <p className="text-xs text-gray-500 mt-1">
            {module.technique_focus || module.mi_skill_category || "General MI"}
          </p>
        </div>
        <span className="text-maps-teal font-bold text-sm">
          {module.points} pts
        </span>
      </div>
      <p className="text-sm text-gray-600 line-clamp-2 mb-3">
        {module.description || module.learning_objective}
      </p>
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{module.estimated_minutes} min</span>
        <span>{module.stage_of_change || ""}</span>
      </div>
    </Link>
  );
}
