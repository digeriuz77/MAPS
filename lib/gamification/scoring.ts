/**
 * Gamification Scoring System
 * Points, levels, and achievement calculations
 */

export interface ScoringResult {
  pointsEarned: number;
  totalPoints: number;
  newLevel: number;
  levelProgress: number;
  pointsToNextLevel: number;
  achievements?: Achievement[];
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  unlockedAt?: Date;
}

/**
 * Level thresholds from mi-learning-platform
 */
export const LEVEL_THRESHOLDS = [
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
];

/**
 * Achievement definitions
 */
export const ACHIEVEMENTS: Achievement[] = [
  {
    id: "first_module",
    name: "First Steps",
    description: "Complete your first MI practice module",
    icon: "🎯",
  },
  {
    id: "five_modules",
    name: "MI Learner",
    description: "Complete 5 MI practice modules",
    icon: "📚",
  },
  {
    id: "ten_modules",
    name: "MI Practitioner",
    description: "Complete 10 MI practice modules",
    icon: "🏆",
  },
  {
    id: "level_5",
    name: "Rising Star",
    description: "Reach level 5",
    icon: "⭐",
  },
  {
    id: "level_10",
    name: "MI Master",
    description: "Reach the maximum level",
    icon: "👑",
  },
  {
    id: "change_talk_10",
    name: "Change Talk Catalyst",
    description: "Evoke change talk 10 times",
    icon: "💬",
  },
  {
    id: "perfect_score",
    name: "Perfect Practice",
    description: "Complete a module with 100% score",
    icon: "💯",
  },
  {
    id: "first_persona",
    name: "First Conversation",
    description: "Have your first persona conversation",
    icon: "🗣️",
  },
];

/**
 * Calculate level based on total points
 */
export function calculateLevel(totalPoints: number): number {
  let currentLevel = 1;
  for (const threshold of LEVEL_THRESHOLDS) {
    if (totalPoints >= threshold.points) {
      currentLevel = threshold.level;
    }
  }
  return currentLevel;
}

/**
 * Calculate points needed to reach next level
 */
export function getPointsToNextLevel(currentPoints: number): number {
  const currentLevel = calculateLevel(currentPoints);

  if (currentLevel >= 10) {
    return 0; // Max level
  }

  const nextLevel = LEVEL_THRESHOLDS.find((t) => t.level === currentLevel + 1);
  return nextLevel ? nextLevel.points - currentPoints : 0;
}

/**
 * Calculate progress percentage to next level
 */
export function getLevelProgress(currentPoints: number): number {
  const currentLevel = calculateLevel(currentPoints);

  if (currentLevel >= 10) {
    return 100; // Max level
  }

  const currentThreshold = LEVEL_THRESHOLDS.find((t) => t.level === currentLevel);
  const nextThreshold = LEVEL_THRESHOLDS.find((t) => t.level === currentLevel + 1);

  if (!currentThreshold || !nextThreshold) {
    return 0;
  }

  const pointsInCurrentLevel = currentPoints - currentThreshold.points;
  const pointsNeededForNextLevel = nextThreshold.points - currentThreshold.points;

  return Math.min(100, (pointsInCurrentLevel / pointsNeededForNextLevel) * 100);
}

/**
 * Calculate points for completing a dialogue choice
 */
export function calculateChoicePoints(isCorrect: boolean, isFirstAttempt: boolean): number {
  let points = 0;

  if (isCorrect) {
    points += 100; // Base points for correct technique

    if (isFirstAttempt) {
      points += 50; // First attempt bonus
    }
  }

  return points;
}

/**
 * Calculate points for completing a module
 */
export function calculateModuleCompletionPoints(
  completionScore: number,
  isFirstCompletion: boolean
): number {
  let points = 200; // Base completion points

  if (isFirstCompletion) {
    points += 100; // First time bonus
  }

  if (completionScore >= 90) {
    points += 100; // Excellence bonus
  } else if (completionScore >= 70) {
    points += 50; // Good score bonus
  }

  return points;
}

/**
 * Calculate points for evoking change talk
 */
export function calculateChangeTalkPoints(): number {
  return 50;
}

/**
 * Calculate points for a persona conversation
 */
export function calculatePersonaConversationPoints(
  turnCount: number,
  skillsDemonstrated: string[]
): number {
  let points = 50; // Base points for starting

  // Points for engagement (more turns = more practice)
  points += Math.min(turnCount * 5, 100);

  // Points for using MI skills
  points += skillsDemonstrated.length * 20;

  return points;
}

/**
 * Update user score and check for level ups
 */
export function updateUserScore(
  currentPoints: number,
  pointsEarned: number
): ScoringResult {
  const newPoints = currentPoints + pointsEarned;
  const newLevel = calculateLevel(newPoints);
  const progress = getLevelProgress(newPoints);
  const toNextLevel = getPointsToNextLevel(newPoints);

  return {
    pointsEarned,
    totalPoints: newPoints,
    newLevel,
    levelProgress: progress,
    pointsToNextLevel: toNextLevel,
  };
}

/**
 * Check for unlocked achievements
 */
export function checkAchievements(
  stats: {
    modulesCompleted: number;
    level: number;
    changeTalkEvoked: number;
    personaConversations: number;
  }
): Achievement[] {
  const unlocked: Achievement[] = [];

  for (const achievement of ACHIEVEMENTS) {
    let isUnlocked = false;

    switch (achievement.id) {
      case "first_module":
        isUnlocked = stats.modulesCompleted >= 1;
        break;
      case "five_modules":
        isUnlocked = stats.modulesCompleted >= 5;
        break;
      case "ten_modules":
        isUnlocked = stats.modulesCompleted >= 10;
        break;
      case "level_5":
        isUnlocked = stats.level >= 5;
        break;
      case "level_10":
        isUnlocked = stats.level >= 10;
        break;
      case "change_talk_10":
        isUnlocked = stats.changeTalkEvoked >= 10;
        break;
      case "first_persona":
        isUnlocked = stats.personaConversations >= 1;
        break;
      case "perfect_score":
        // This would be checked during module completion
        break;
    }

    if (isUnlocked) {
      unlocked.push({
        ...achievement,
        unlockedAt: new Date(),
      });
    }
  }

  return unlocked;
}
