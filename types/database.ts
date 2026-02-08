/**
 * Supabase Database Types
 *
 * These types match the actual database schema and should be used
 * instead of (supabase as any) workarounds.
 */

// =============================================================================
// SCENARIAS & ATTEMPTS
// =============================================================================

export interface Scenario {
  id: string;
  code: string;
  title: string;
  mi_skill_category: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  estimated_minutes: number;
  situation: string;
  learning_objective: string;
  persona_config: PersonaConfig;
  success_criteria: SuccessCriteria;
  maps_rubric: MapsRubric;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  mi_practice_module_id: string | null;
  has_structured_dialogue: boolean;
}

export interface PersonaConfig {
  name: string;
  role: string;
  triggers?: {
    trust_decrease?: string[];
    trust_increase?: string[];
    resistance_increase?: string[];
  };
  personality?: string;
  core_identity?: string;
  starting_state: {
    trust_level: number;
    openness_level: number;
    resistance_active: boolean;
  };
  current_mindset?: string;
  speech_patterns?: {
    when_trusting?: string;
    when_defensive?: string;
    signature_phrases?: string[];
  };
  current_situation?: string;
  response_patterns?: {
    to_empathy: string;
    to_reflection: string;
    to_confrontation: string;
    to_direct_advice: string;
    to_autonomy_support: string;
  };
  tone?: string;
}

export interface SuccessCriteria {
  min_trust?: number;
  required_techniques?: string[];
  turn_range?: [number, number];
  state_goals?: {
    trust_maintained?: boolean;
    trust_increased?: boolean;
    resistance_decreased?: boolean;
    resistance_not_increased?: boolean;
    engagement_maintained?: boolean;
    openness_increased?: boolean;
  };
  avoid_behaviors?: string[];
  required_skills?: string[];
}

export interface MapsRubric {
  dimensions?: Array<{
    name: string;
    weight: number;
    description: string;
  }>;
}

export interface ScenarioAttempt {
  id: string;
  user_id: string;
  scenario_id: string;
  transcript: TranscriptMessage[];
  turn_count: number;
  started_at: string;
  ended_at: string | null;
  updated_at: string;
  current_persona_state?: {
    trust_level: number;
    openness_level: number;
    resistance_active: boolean;
  };
  final_scores?: Record<string, number>;
}

export interface TranscriptMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  metadata?: {
    technique_used?: string;
    trust_change?: number;
    resistance_change?: number;
  };
}

// =============================================================================
// MI PRACTICE MODULES
// =============================================================================

export interface MiPracticeModule {
  id: string;
  code: string;
  title: string;
  mi_focus_area: string;
  difficulty_level: "beginner" | "intermediate" | "advanced";
  estimated_minutes: number;
  learning_objective: string;
  scenario_context: string;
  persona_config: PersonaConfig;
  dialogue_structure: DialogueStructure;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DialogueStructure {
  nodes: Record<string, DialogueNode>;
}

export interface DialogueNode {
  id: string;
  themes: string[];
  is_endpoint: boolean;
  persona_mood: string;
  persona_text: string;
  choice_points: ChoicePoint[];
}

export interface ChoicePoint {
  id: string;
  feedback: {
    immediate: string;
    learning_note: string;
  };
  tone_shift: number;
  option_text: string;
  next_node_id: string;
  preview_hint: string;
  rapport_impact: number;
  technique_tags: string[];
  competency_links: string[];
  exploration_depth: string;
  resistance_impact: number;
}

export interface MiPracticeAttempt {
  id: string;
  user_id: string;
  module_id: string;
  started_at: string;
  completed_at: string | null;
  current_node_id: string;
  path_taken: string[];
  choices_made: Record<string, unknown>[];
  completion_status: "in_progress" | "completed" | "abandoned";
  final_scores?: Record<string, unknown>;
  current_rapport_score?: number;
  current_resistance_level?: number;
  updated_at: string;
}

// =============================================================================
// MI LEARNING PATHS
// =============================================================================

export interface MiLearningPath {
  id: string;
  code: string;
  title: string;
  description: string;
  module_ids: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// =============================================================================
// PROFILES
// =============================================================================

export interface Profile {
  id: string;
  email: string;
  display_name: string | null;
  role: "FULL" | "CONTROL";
  level: number;
  total_points: number;
  modules_completed: number;
  change_talk_evoked: number;
  reflections_offered: number;
  created_at: string;
  updated_at: string;
}

// =============================================================================
// FEEDBACK & REFLECTIONS
// =============================================================================

export interface FeedbackEntry {
  id: string;
  attempt_id: string;
  feedback_type: "realtime_tip" | "end_of_session" | "reflection_prompt";
  content: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface ReflectionPrompt {
  id: string;
  user_id: string;
  attempt_id: string;
  prompt: string;
  response: string | null;
  created_at: string;
  answered_at: string | null;
}

// =============================================================================
// ANALYTICS
// =============================================================================

export interface SystemMetrics {
  id: string;
  metric_name: string;
  metric_value: number;
  timestamp: string;
  metadata: Record<string, unknown> | null;
}

// =============================================================================
// INSERT TYPES (for creating new records)
// =============================================================================

export interface ScenarioAttemptInsert {
  user_id: string;
  scenario_id: string;
  transcript?: TranscriptMessage[];
  turn_count?: number;
  initial_persona_state?: {
    trust_level: number;
    openness_level: number;
    resistance_active: boolean;
  };
}

export interface MiPracticeAttemptInsert {
  user_id: string;
  module_id: string;
  started_at?: string;
  current_node_id?: string;
  path_taken?: string[];
  choices_made?: Record<string, unknown>[];
}

export interface ScenarioAttemptUpdate {
  transcript?: TranscriptMessage[];
  turn_count?: number;
  ended_at?: string;
  current_persona_state?: {
    trust_level: number;
    openness_level: number;
    resistance_active: boolean;
  };
  final_scores?: Record<string, number>;
}

export interface MiPracticeAttemptUpdate {
  current_node_id?: string;
  path_taken?: string[];
  choices_made?: Record<string, unknown>[];
  current_rapport_score?: number;
  current_resistance_level?: number;
  completion_status?: string;
  completed_at?: string;
  final_scores?: Record<string, unknown>;
}

// =============================================================================
// TABLE NAMES
// =============================================================================

export const Tables = {
  SCENARIOS: "scenarios",
  SCENARIO_ATTEMPTS: "scenario_attempts",
  MI_PRACTICE_MODULES: "mi_practice_modules",
  MI_PRACTICE_ATTEMPTS: "mi_practice_attempts",
  MI_LEARNING_PATHS: "mi_learning_paths",
  PROFILES: "profiles",
  FEEDBACK: "feedback",
  REFLECTION_PROMPTS: "reflection_prompts",
  SYSTEM_METRICS: "system_metrics",
} as const;
