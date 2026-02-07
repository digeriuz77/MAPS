"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface LeaderboardEntry {
  rank: number;
  displayName: string;
  totalPoints: number;
  level: number;
  modulesCompleted: number;
}

export default function LeaderboardPage() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    loadLeaderboard();
  }, []);

  const loadLeaderboard = async () => {
    try {
      const response = await fetch("/api/leaderboard?limit=20&includeCurrentUser=true");
      const data = await response.json();

      setLeaderboard(data.leaderboard || []);
      setHasMore(data.hasMore || false);
    } catch (error) {
      console.error("Error loading leaderboard:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const getRankBadge = (rank: number) => {
    if (rank === 1) return "🥇";
    if (rank === 2) return "🥈";
    if (rank === 3) return "🥉";
    return `#${rank}`;
  };

  const getRankColor = (rank: number) => {
    if (rank === 1) return "text-yellow-600";
    if (rank === 2) return "text-gray-500";
    if (rank === 3) return "text-amber-700";
    return "text-gray-600";
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-maps-navy">Leaderboard</h1>
        <p className="text-gray-600 mt-1">
          Top MI practitioners ranked by points
        </p>
      </div>

      {/* Leaderboard */}
      {isLoading ? (
        <div className="card text-center py-12">
          <div className="text-gray-500">Loading leaderboard...</div>
        </div>
      ) : leaderboard.length > 0 ? (
        <div className="card">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-maps-navy">Rank</th>
                  <th className="text-left py-3 px-4 font-semibold text-maps-navy">Practitioner</th>
                  <th className="text-right py-3 px-4 font-semibold text-maps-navy">Points</th>
                  <th className="text-center py-3 px-4 font-semibold text-maps-navy">Level</th>
                  <th className="text-center py-3 px-4 font-semibold text-maps-navy">Modules</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((entry) => (
                  <tr
                    key={entry.rank}
                    className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                  >
                    <td className={`py-3 px-4 font-bold ${getRankColor(entry.rank)}`}>
                      {getRankBadge(entry.rank)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-maps-navy">
                        {entry.displayName}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="font-semibold text-maps-teal">
                        {entry.totalPoints.toLocaleString()}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="inline-block px-2 py-1 bg-maps-teal/10 text-maps-teal rounded-full text-sm font-medium">
                        {entry.level}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center text-gray-600">
                      {entry.modulesCompleted}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {hasMore && (
            <div className="text-center py-4 border-t border-gray-200">
              <button
                onClick={loadLeaderboard}
                className="text-maps-teal hover:text-maps-teal-dark font-medium"
              >
                Load More
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-gray-500">No leaderboard data available yet.</p>
        </div>
      )}

      {/* Level Info */}
      <div className="card mt-6">
        <h3 className="font-semibold text-maps-navy mb-3">Level Thresholds</h3>
        <div className="grid grid-cols-5 gap-2 text-sm">
          {[
            { level: 1, points: 0 },
            { level: 2, points: 500 },
            { level: 3, points: 1500 },
            { level: 4, points: 3000 },
            { level: 5, points: 5000 },
            { level: 6, points: 8000 },
            { level: 7, points: 12000 },
            { level: 8, points: 18000 },
            { level: 9, points: 25000 },
            { level: 10, points: 30000 },
          ].map((tier) => (
            <div
              key={tier.level}
              className="text-center p-2 bg-gray-50 rounded"
            >
              <div className="font-bold text-maps-navy">L{tier.level}</div>
              <div className="text-gray-500 text-xs">{tier.points}pts</div>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-center gap-4 mt-8">
        <Link href="/mi-practice" className="btn-primary">
          Practice to Earn Points
        </Link>
        <Link href="/progress" className="btn-outline">
          View Your Progress
        </Link>
      </div>
    </div>
  );
}
