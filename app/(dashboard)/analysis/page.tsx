"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function AnalysisPage() {
  const router = useRouter();
  const [transcript, setTranscript] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!transcript.trim()) return;

    setIsAnalyzing(true);
    try {
      const response = await fetch("/api/analysis/transcript", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript }),
      });

      if (!response.ok) {
        throw new Error("Analysis failed");
      }

      const data = await response.json();
      setResults(data.analysis);
    } catch (error) {
      console.error("Error:", error);
      alert("Analysis failed. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const downloadPDF = async () => {
    if (!results) return;

    try {
      const response = await fetch("/api/pdf/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: "analysis-report",
          data: {
            userName: "User", // TODO: Get from auth
            transcript,
            analysis: results,
            date: new Date().toISOString(),
          },
        }),
      });

      if (!response.ok) {
        throw new Error("PDF generation failed");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `maps-analysis-${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error:", error);
      alert("Failed to generate PDF");
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-maps-navy">MAPS Analysis</h1>
        <p className="text-gray-600 mt-1">
          Analyze your MI conversations for person-centered coaching insights
        </p>
      </div>

      {!results ? (
        /* Input Form */
        <div className="card mt-8">
          <h2 className="text-xl font-semibold text-maps-navy mb-4">
            Submit Your Transcript
          </h2>
          <p className="text-gray-600 mb-6">
            Paste a transcript of your MI conversation to receive detailed feedback
            on your use of MI techniques, person-centered language, and overall
            effectiveness.
          </p>

          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Paste your conversation transcript here...

Example format:
Practitioner: Hello, tell me about your situation.
Client: Well, I've been struggling with...
Practitioner: I see. It sounds like..."
            className="w-full h-64 p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-maps-teal resize-none font-mono text-sm"
          />

          <div className="flex justify-between items-center mt-4">
            <div className="text-sm text-gray-500">
              {transcript.length} characters
            </div>
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing || !transcript.trim()}
              className="btn-primary disabled:opacity-50"
            >
              {isAnalyzing ? "Analyzing..." : "Analyze Transcript"}
            </button>
          </div>
        </div>
      ) : (
        /* Results Display */
        <div className="mt-8 space-y-6">
          {/* Score Card */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-maps-navy">
                MI Spirit Score
              </h2>
              <button
                onClick={() => setResults(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                New Analysis
              </button>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-5xl font-bold text-maps-teal">
                {results.miSpiritScore || 75}%
              </div>
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-maps-teal transition-all"
                    style={{ width: `${results.miSpiritScore || 75}%` }}
                  />
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  {results.miSpiritScore >= 80
                    ? "Excellent demonstration of MI spirit!"
                    : results.miSpiritScore >= 60
                    ? "Good foundation with room for growth."
                    : "Keep practicing - focus on MI core skills."}
                </p>
              </div>
            </div>
          </div>

          {/* Techniques */}
          <div className="card">
            <h3 className="text-lg font-semibold text-maps-navy mb-3">
              Techniques Demonstrated
            </h3>
            <div className="flex flex-wrap gap-2">
              {(results.techniquesUsed || [
                "Open-ended questions",
                "Reflections",
                "Affirmations",
              ]).map((technique: string, index: number) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-maps-teal/10 text-maps-teal rounded-full text-sm"
                >
                  {technique}
                </span>
              ))}
            </div>
          </div>

          {/* Strengths */}
          <div className="card">
            <h3 className="text-lg font-semibold text-maps-navy mb-3">
              Strengths
            </h3>
            <ul className="space-y-2">
              {(results.strengths || [
                "Good use of open-ended questions",
                "Demonstrated active listening",
                "Showed empathy throughout",
              ]).map((strength: string, index: number) => (
                <li key={index} className="flex items-start gap-2 text-gray-700">
                  <span className="text-green-500 mt-0.5">✓</span>
                  {strength}
                </li>
              ))}
            </ul>
          </div>

          {/* Improvements */}
          <div className="card">
            <h3 className="text-lg font-semibold text-maps-navy mb-3">
              Areas for Improvement
            </h3>
            <ul className="space-y-2">
              {(results.improvements || [
                "Try using more reflections to show understanding",
                "Consider eliciting more change talk",
                "Practice rolling with resistance",
              ]).map((improvement: string, index: number) => (
                <li key={index} className="flex items-start gap-2 text-gray-700">
                  <span className="text-amber-500 mt-0.5">→</span>
                  {improvement}
                </li>
              ))}
            </ul>
          </div>

          {/* Overall Feedback */}
          <div className="card">
            <h3 className="text-lg font-semibold text-maps-navy mb-3">
              Overall Feedback
            </h3>
            <p className="text-gray-700">
              {results.overallFeedback ||
                "Your conversation demonstrates a solid foundation in Motivational Interviewing. Continue practicing your reflections and working to elicit change talk naturally. Consider reviewing OARS techniques and focusing on the MI spirit of collaboration, evocation, and autonomy."}
            </p>
          </div>

          {/* Actions */}
          <div className="flex justify-center gap-4">
            <button onClick={downloadPDF} className="btn-primary">
              Download PDF Report
            </button>
            <button
              onClick={() => setResults(null)}
              className="btn-outline"
            >
              Analyze Another Transcript
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
