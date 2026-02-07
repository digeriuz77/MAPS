/**
 * Supabase Database Types
 * Generated based on the unified schema for MAPS + mi-learning-platform
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      user_profiles: {
        Row: {
          id: string;
          user_id: string;
          role: "FULL" | "CONTROL";
          display_name: string | null;
          total_points: number;
          level: number;
          modules_completed: number;
          change_talk_evoked: number;
          reflections_offered: number;
          technique_mastery: Json;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          role?: "FULL" | "CONTROL";
          display_name?: string | null;
          total_points?: number;
          level?: number;
          modules_completed?: number;
          change_talk_evoked?: number;
          reflections_offered?: number;
          technique_mastery?: Json;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          role?: "FULL" | "CONTROL";
          display_name?: string | null;
          total_points?: number;
          level?: number;
          modules_completed?: number;
          change_talk_evoked?: number;
          reflections_offered?: number;
          technique_mastery?: Json;
          created_at?: string;
          updated_at?: string;
        };
      };
      learning_modules: {
        Row: {
          id: string;
          code: string;
          title: string;
          learning_objective: string;
          difficulty_level: string;
          estimated_minutes: number;
          is_active: boolean;
          mi_skill_category: string | null;
          scenario_context: string | null;
          persona_config: Json | null;
          maps_rubric: Json | null;
          target_competencies: string[];
          module_number: number | null;
          slug: string | null;
          technique_focus: string | null;
          stage_of_change: string | null;
          mi_process: string | null;
          description: string | null;
          dialogue_content: Json | null;
          points: number;
          display_order: number;
          is_published: boolean;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          code: string;
          title: string;
          learning_objective: string;
          difficulty_level?: string;
          estimated_minutes?: number;
          is_active?: boolean;
          mi_skill_category?: string | null;
          scenario_context?: string | null;
          persona_config?: Json | null;
          maps_rubric?: Json | null;
          target_competencies?: string[];
          module_number?: number | null;
          slug?: string | null;
          technique_focus?: string | null;
          stage_of_change?: string | null;
          mi_process?: string | null;
          description?: string | null;
          dialogue_content?: Json | null;
          points?: number;
          display_order?: number;
          is_published?: boolean;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          code?: string;
          title?: string;
          learning_objective?: string;
          difficulty_level?: string;
          estimated_minutes?: number;
          is_active?: boolean;
          mi_skill_category?: string | null;
          scenario_context?: string | null;
          persona_config?: Json | null;
          maps_rubric?: Json | null;
          target_competencies?: string[];
          module_number?: number | null;
          slug?: string | null;
          technique_focus?: string | null;
          stage_of_change?: string | null;
          mi_process?: string | null;
          description?: string | null;
          dialogue_content?: Json | null;
          points?: number;
          display_order?: number;
          is_published?: boolean;
          created_at?: string;
          updated_at?: string;
        };
      };
      scenarios: {
        Row: {
          id: string;
          persona_name: string;
          persona_description: string;
          persona_config: Json;
          scenario_context: string | null;
          is_active: boolean;
          created_at: string;
        };
        Insert: {
          id?: string;
          persona_name: string;
          persona_description: string;
          persona_config: Json;
          scenario_context?: string | null;
          is_active?: boolean;
          created_at?: string;
        };
        Update: {
          id?: string;
          persona_name?: string;
          persona_description?: string;
          persona_config?: Json;
          scenario_context?: string | null;
          is_active?: boolean;
          created_at?: string;
        };
      };
      scenario_attempts: {
        Row: {
          id: string;
          user_id: string;
          scenario_id: string;
          turn_count: number;
          transcript: Json;
          started_at: string;
          completed_at: string | null;
          final_scores: Json | null;
          completion_reason: string | null;
          initial_persona_state: Json | null;
          final_persona_state: Json | null;
          skills_demonstrated: string[];
          negative_behaviors: string[];
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          scenario_id: string;
          turn_count?: number;
          transcript?: Json;
          started_at?: string;
          completed_at?: string | null;
          final_scores?: Json | null;
          completion_reason?: string | null;
          initial_persona_state?: Json | null;
          final_persona_state?: Json | null;
          skills_demonstrated?: string[];
          negative_behaviors?: string[];
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          scenario_id?: string;
          turn_count?: number;
          transcript?: Json;
          started_at?: string;
          completed_at?: string | null;
          final_scores?: Json | null;
          completion_reason?: string | null;
          initial_persona_state?: Json | null;
          final_persona_state?: Json | null;
          skills_demonstrated?: string[];
          negative_behaviors?: string[];
          created_at?: string;
          updated_at?: string;
        };
      };
      user_progress: {
        Row: {
          id: string;
          user_id: string;
          module_id: string;
          status: "not_started" | "in_progress" | "completed";
          started_at: string;
          completed_at: string | null;
          updated_at: string;
          current_rapport_score: number;
          current_resistance_level: number;
          tone_spectrum_position: number;
          path_taken: string[];
          current_node_id: string;
          nodes_completed: string[];
          points_earned: number;
          completion_score: number;
          techniques_demonstrated: Json;
        };
        Insert: {
          id?: string;
          user_id: string;
          module_id: string;
          status?: "not_started" | "in_progress" | "completed";
          started_at?: string;
          completed_at?: string | null;
          updated_at?: string;
          current_rapport_score?: number;
          current_resistance_level?: number;
          tone_spectrum_position?: number;
          path_taken?: string[];
          current_node_id?: string;
          nodes_completed?: string[];
          points_earned?: number;
          completion_score?: number;
          techniques_demonstrated?: Json;
        };
        Update: {
          id?: string;
          user_id?: string;
          module_id?: string;
          status?: "not_started" | "in_progress" | "completed";
          started_at?: string;
          completed_at?: string | null;
          updated_at?: string;
          current_rapport_score?: number;
          current_resistance_level?: number;
          tone_spectrum_position?: number;
          path_taken?: string[];
          current_node_id?: string;
          nodes_completed?: string[];
          points_earned?: number;
          completion_score?: number;
          techniques_demonstrated?: Json;
        };
      };
      dialogue_attempts: {
        Row: {
          id: string;
          attempt_id: string;
          node_id: string;
          choice_id: string;
          choice_text: string;
          technique: string;
          is_correct_technique: boolean;
          feedback_text: string;
          evoked_change_talk: boolean;
          points_earned: number;
          created_at: string;
        };
        Insert: {
          id?: string;
          attempt_id: string;
          node_id: string;
          choice_id: string;
          choice_text: string;
          technique: string;
          is_correct_technique: boolean;
          feedback_text: string;
          evoked_change_talk?: boolean;
          points_earned?: number;
          created_at?: string;
        };
        Update: {
          id?: string;
          attempt_id?: string;
          node_id?: string;
          choice_id?: string;
          choice_text?: string;
          technique?: string;
          is_correct_technique?: boolean;
          feedback_text?: string;
          evoked_change_talk?: boolean;
          points_earned?: number;
          created_at?: string;
        };
      };
      learning_paths: {
        Row: {
          id: string;
          code: string;
          title: string;
          description: string | null;
          module_sequence: string[];
          target_audience: string | null;
          estimated_total_minutes: number | null;
          maps_competencies_targeted: string[];
          is_active: boolean;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          code: string;
          title: string;
          description?: string | null;
          module_sequence: string[];
          target_audience?: string | null;
          estimated_total_minutes?: number | null;
          maps_competencies_targeted?: string[];
          is_active?: boolean;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          code?: string;
          title?: string;
          description?: string | null;
          module_sequence?: string[];
          target_audience?: string | null;
          estimated_total_minutes?: number | null;
          maps_competencies_targeted?: string[];
          is_active?: boolean;
          created_at?: string;
          updated_at?: string;
        };
      };
      voice_sessions: {
        Row: {
          id: string;
          attempt_id: string;
          user_id: string;
          mode: string;
          mistral_config: Json | null;
          persona_config: Json | null;
          started_at: string;
          ended_at: string | null;
          duration_seconds: number;
          transcript: Json;
          metrics: Json | null;
          status: string;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          attempt_id: string;
          user_id: string;
          mode?: string;
          mistral_config?: Json | null;
          persona_config?: Json | null;
          started_at?: string;
          ended_at?: string | null;
          duration_seconds?: number;
          transcript?: Json;
          metrics?: Json | null;
          status?: string;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          attempt_id?: string;
          user_id?: string;
          mode?: string;
          mistral_config?: Json | null;
          persona_config?: Json | null;
          started_at?: string;
          ended_at?: string | null;
          duration_seconds?: number;
          transcript?: Json;
          metrics?: Json | null;
          status?: string;
          created_at?: string;
          updated_at?: string;
        };
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      [_ in never]: never;
    };
  };
}

// Type aliases for convenience
export type UserProfile = Database["public"]["Tables"]["user_profiles"]["Row"];
export type LearningModule = Database["public"]["Tables"]["learning_modules"]["Row"];
export type Scenario = Database["public"]["Tables"]["scenarios"]["Row"];
export type ScenarioAttempt = Database["public"]["Tables"]["scenario_attempts"]["Row"];
export type UserProgress = Database["public"]["Tables"]["user_progress"]["Row"];
export type DialogueAttempt = Database["public"]["Tables"]["dialogue_attempts"]["Row"];
export type LearningPath = Database["public"]["Tables"]["learning_paths"]["Row"];
export type VoiceSession = Database["public"]["Tables"]["voice_sessions"]["Row"];
