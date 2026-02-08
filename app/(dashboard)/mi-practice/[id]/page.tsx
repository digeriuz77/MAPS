"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { getLearningModuleByIdClient, createUserProgressClient, getUserProgressForModuleClient } from "@/lib/supabase/client-queries";
import type { LearningModule } from "@/types/supabase";

interface DialogueNode {
  id: string;
  text: string;
  speaker: "persona" | "coach";
  choices?: Choice[];
}

interface Choice {
  id: string;
  text: string;
  technique: string;
  isCorrect: boolean;
  feedback: string;
  nextNode: string;
  points: number;
}

interface ProgressData {
  status: "not_started" | "in_progress" | "completed";
  currentNodeId: string;
  nodesCompleted: string[];
  pointsEarned: number;
  completionScore: number;
}

export default function MIPracticeSessionPage() {
  const params = useParams();
  const router = useRouter();
  const moduleId = params.id as string;

  const [module, setModule] = useState<LearningModule | null>(null);
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [currentNode, setCurrentNode] = useState<DialogueNode | null>(null);
  const [selectedChoice, setSelectedChoice] = useState<Choice | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(true);
  const [history, setHistory] = useState<Array<{ nodeId: string; choice: Choice }>>([]);

  useEffect(() => {
    loadModule();
  }, [moduleId]);

  const loadModule = async () => {
    try {
      const moduleData = await getLearningModuleByIdClient(moduleId);
      if (!moduleData) {
        router.push("/mi-practice");
        return;
      }

      setModule(moduleData);

      // Get or create progress
      // For demo purposes, we're using anonymous user
      const userId = "anonymous"; // TODO: Replace with actual user ID
      let userProgress = await getUserProgressForModuleClient(userId, moduleId);

      if (!userProgress) {
        userProgress = await createUserProgressClient(userId, moduleId);
      }

      if (userProgress) {
        // Map database fields to ProgressData interface
        setProgress({
          status: userProgress.status,
          currentNodeId: userProgress.current_node_id,
          nodesCompleted: userProgress.nodes_completed,
          pointsEarned: userProgress.points_earned,
          completionScore: userProgress.completion_score,
        });

        // Load current node or start from beginning
        const dialogueContent = moduleData.dialogue_content as Record<string, unknown>;
        const nodes = dialogueContent.nodes as Record<string, DialogueNode> || {};

        const startingNodeId = userProgress.current_node_id || "node_1";
        setCurrentNode(nodes[startingNodeId] || null);
      }

      setIsLoading(false);
      setIsStarting(false);
    } catch (error) {
      console.error("Error loading module:", error);
      setIsLoading(false);
      setIsStarting(false);
    }
  };

  const handleChoiceSelect = (choice: Choice) => {
    setSelectedChoice(choice);
    setShowFeedback(true);
  };

  const handleContinue = async () => {
    if (!selectedChoice || !module || !progress) return;

    // Record the choice
    const newHistory = [...history, { nodeId: currentNode?.id || "", choice: selectedChoice }];
    setHistory(newHistory);

    // Calculate new progress
    const newNodesCompleted = [...new Set([...progress.nodesCompleted, currentNode?.id || ""])];
    const newPoints = progress.pointsEarned + selectedChoice.points;

    // Move to next node or complete
    const dialogueContent = module.dialogue_content as Record<string, unknown>;
    const nodes = dialogueContent.nodes as Record<string, DialogueNode> || {};

    if (selectedChoice.nextNode === "end" || !nodes[selectedChoice.nextNode]) {
      // Module completed
      await completeModule(newPoints, newNodesCompleted);
      return;
    }

    const nextNode = nodes[selectedChoice.nextNode];
    setCurrentNode(nextNode);
    setSelectedChoice(null);
    setShowFeedback(false);

    // Update progress
    // TODO: Call API to update progress
    setProgress({
      ...progress,
      currentNodeId: selectedChoice.nextNode,
      nodesCompleted: newNodesCompleted,
      pointsEarned: newPoints,
    });
  };

  const completeModule = async (points: number, nodesCompleted: string[]) => {
    if (!module || !progress) return;

    // Calculate completion score
    const totalNodes = Object.keys((module.dialogue_content as Record<string, unknown>).nodes || {}).length;
    const completionScore = Math.round((nodesCompleted.length / totalNodes) * 100);

    // TODO: Call API to mark module as complete
    router.push(`/mi-practice/${module.id}/complete?score=${completionScore}&points=${points}`);
  };

  if (isLoading || isStarting) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading module...</div>
      </div>
    );
  }

  if (!module || !currentNode) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Module not found</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-maps-navy">{module.title}</h1>
          <p className="text-gray-500 text-sm">
            {progress?.pointsEarned || 0} points earned
          </p>
        </div>
        <div className="text-right text-sm text-gray-500">
          <div>Step {history.length + 1}</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-maps-teal transition-all"
            style={{
              width: `${Math.min(((history.length + 1) / 10) * 100, 100)}%`,
            }}
          />
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Dialogue Area */}
        <div className="lg:col-span-2 space-y-4">
          {/* Dialogue Node */}
          <div className="card">
            <div className="flex items-start gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${currentNode.speaker === "persona"
                ? "bg-gradient-to-br from-maps-teal to-maps-blue"
                : "bg-gray-400"
                }`}>
                {currentNode.speaker === "persona" ? module.title.charAt(0) : "C"}
              </div>
              <div className="flex-1">
                <div className="text-sm text-gray-500 mb-1">
                  {currentNode.speaker === "persona" ? module.title : "Coach"}
                </div>
                <p className="text-gray-800">{currentNode.text}</p>
              </div>
            </div>
          </div>

          {/* Choices */}
          {!showFeedback && currentNode.choices && currentNode.choices.length > 0 && (
            <div className="space-y-3">
              <p className="text-sm font-medium text-maps-navy">How would you respond?</p>
              {currentNode.choices.map((choice) => (
                <button
                  key={choice.id}
                  onClick={() => handleChoiceSelect(choice)}
                  className="w-full card text-left hover:shadow-medium transition-all group"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full border-2 border-gray-300 group-hover:border-maps-teal flex items-center justify-center">
                      <div className="w-3 h-3 rounded-full bg-maps-teal opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    <div className="flex-1">
                      <p className="text-gray-800">{choice.text}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {choice.technique}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Feedback */}
          {showFeedback && selectedChoice && (
            <div className={`card ${selectedChoice.isCorrect ? "border-l-4 border-l-green-500" : "border-l-4 border-l-amber-500"
              }`}>
              <div className="flex items-start gap-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${selectedChoice.isCorrect ? "bg-green-100 text-green-600" : "bg-amber-100 text-amber-600"
                  }`}>
                  {selectedChoice.isCorrect ? "✓" : "!"}
                </div>
                <div className="flex-1">
                  <h3 className={`font-semibold mb-2 ${selectedChoice.isCorrect ? "text-green-800" : "text-amber-800"
                    }`}>
                    {selectedChoice.isCorrect ? "Great choice!" : "Let's reflect on this"}
                  </h3>
                  <p className="text-gray-700 mb-3">{selectedChoice.feedback}</p>
                  <div className="flex items-center justify-between">
                    <span className={`text-sm font-medium ${selectedChoice.isCorrect ? "text-green-600" : "text-amber-600"
                      }`}>
                      {selectedChoice.isCorrect ? `+${selectedChoice.points} points` : "No points earned"}
                    </span>
                    <button
                      onClick={handleContinue}
                      className="btn-primary text-sm"
                    >
                      Continue
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Module Info */}
          <div className="card">
            <h3 className="font-semibold text-maps-navy mb-2">About This Module</h3>
            <p className="text-sm text-gray-600">{module.learning_objective}</p>
            <div className="mt-3 pt-3 border-t border-gray-200 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Technique</span>
                <span className="font-medium">{module.technique_focus || "General"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Stage of Change</span>
                <span className="font-medium">{module.stage_of_change || "N/A"}</span>
              </div>
            </div>
          </div>

          {/* History */}
          {history.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-maps-navy mb-3">Your Responses</h3>
              <div className="space-y-2 text-sm">
                {history.slice(-5).map((item, index) => (
                  <div key={index} className="p-2 bg-gray-50 rounded">
                    <p className="text-gray-700 line-clamp-1">{item.choice.text}</p>
                    <p className={`text-xs mt-1 ${item.choice.isCorrect ? "text-green-600" : "text-amber-600"
                      }`}>
                      {item.choice.technique} {item.choice.isCorrect ? "✓" : "!"}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
