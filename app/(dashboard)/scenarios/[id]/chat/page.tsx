"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { getScenarioById, createScenarioAttempt } from "@/lib/supabase/queries";
import type { Scenario } from "@/types/supabase";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
}

interface FeedbackTip {
  type: "strength" | "improvement";
  message: string;
}

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const scenarioId = params.id as string;

  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isStarting, setIsStarting] = useState(true);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [feedbackTips, setFeedbackTips] = useState<FeedbackTip[]>([]);
  const [turnCount, setTurnCount] = useState(0);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load scenario and start session
  useEffect(() => {
    loadScenario();
  }, [scenarioId]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadScenario = async () => {
    try {
      const data = await getScenarioById(scenarioId);
      if (data) {
        setScenario(data);
        await startSession(data);
      } else {
        router.push("/scenarios");
      }
    } catch (error) {
      console.error("Error loading scenario:", error);
      router.push("/scenarios");
    }
  };

  const startSession = async (scenarioData: Scenario) => {
    try {
      // For anonymous/demo users, we'll create a temporary attempt
      // In production, this would use the authenticated user's ID
      const userId = "anonymous"; // TODO: Replace with actual user ID

      const personaConfig = scenarioData.persona_config as Record<string, unknown> | null;

      const attempt = await createScenarioAttempt(
        userId,
        scenarioData.id,
        personaConfig || undefined
      );

      if (attempt) {
        setAttemptId(attempt.id);

        // Add initial greeting from persona
        const greeting = personaConfig?.greeting as string ||
          `Hello, I'm ${scenarioData.persona_name}. ${scenarioData.persona_description}`;

        setMessages([
          {
            role: "assistant",
            content: greeting,
            timestamp: new Date(),
          },
        ]);
      }

      setIsStarting(false);
    } catch (error) {
      console.error("Error starting session:", error);
      setIsStarting(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMessage, timestamp: new Date() },
    ]);
    setIsLoading(true);
    setFeedbackTips([]);

    try {
      const response = await fetch("/api/scenarios/turn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          attemptId,
          message: userMessage,
          scenarioId,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response,
          timestamp: new Date(),
        },
      ]);

      setTurnCount((prev) => prev + 1);

      if (data.feedback) {
        setFeedbackTips(data.feedback);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "system",
          content: "Sorry, I couldn't get a response. Please try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const endSession = async () => {
    try {
      if (attemptId) {
        await fetch(`/api/scenarios/attempts/${attemptId}/end`, {
          method: "POST",
        });
      }
      router.push("/analysis");
    } catch (error) {
      console.error("Error ending session:", error);
    }
  };

  if (isStarting) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Starting conversation...</div>
      </div>
    );
  }

  if (!scenario) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Persona not found</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-maps-navy">{scenario.persona_name}</h1>
          <p className="text-gray-500 text-sm">Turn {turnCount}</p>
        </div>
        <button
          onClick={endSession}
          className="px-4 py-2 text-sm text-gray-600 hover:text-maps-teal border border-gray-300 rounded-lg hover:border-maps-teal transition-colors"
        >
          End Session
        </button>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Chat Area */}
        <div className="lg:col-span-2 card">
          <div className="h-[500px] overflow-y-auto p-4 space-y-4">
            {messages.map((message, index) => (
              <MessageBubble key={index} message={message} />
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg px-4 py-2 max-w-[80%]">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-75"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-150"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="input flex-1"
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={isLoading || !input.trim()}
                className="btn-primary disabled:opacity-50"
              >
                Send
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Feedback Tips */}
          {feedbackTips.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-maps-navy mb-3">Real-time Feedback</h3>
              <div className="space-y-2">
                {feedbackTips.map((tip, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg text-sm ${
                      tip.type === "strength"
                        ? "bg-green-50 text-green-800"
                        : "bg-amber-50 text-amber-800"
                    }`}
                  >
                    {tip.message}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Persona Info */}
          <div className="card">
            <h3 className="font-semibold text-maps-navy mb-2">About {scenario.persona_name}</h3>
            <p className="text-sm text-gray-600">{scenario.persona_description}</p>
            {scenario.scenario_context && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <p className="text-xs text-gray-500">
                  <strong>Context:</strong> {scenario.scenario_context}
                </p>
              </div>
            )}
          </div>

          {/* Tips */}
          <div className="card bg-maps-teal/10">
            <h3 className="font-semibold text-maps-teal-dark mb-2">MI Tips</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Use open-ended questions</li>
              <li>• Practice reflective listening</li>
              <li>• Elicit change talk</li>
              <li>• Show empathy and understanding</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <div className="bg-amber-50 text-amber-800 rounded-lg px-4 py-2 text-sm">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`rounded-lg px-4 py-2 max-w-[80%] ${
          isUser
            ? "bg-maps-teal text-white"
            : "bg-gray-100 text-gray-800"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        <p
          className={`text-xs mt-1 ${
            isUser ? "text-maps-teal-light" : "text-gray-500"
          }`}
        >
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
    </div>
  );
}
