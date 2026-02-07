-- =====================================================
-- MAPS Unified Schema Migration
-- Merges MAPS and mi-learning-platform schemas
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- User Profiles Table (merged from both platforms)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    user_id UUID UNIQUE NOT NULL,

    -- MAPS role-based access
    role TEXT NOT NULL CHECK (role IN ('FULL', 'CONTROL')) DEFAULT 'FULL',

    -- Display name
    display_name VARCHAR(100),

    -- mi-learning-platform gamification
    total_points INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    modules_completed INTEGER DEFAULT 0,

    -- MI-specific tracking
    change_talk_evoked INTEGER DEFAULT 0,
    reflections_offered INTEGER DEFAULT 0,
    technique_mastery JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on user_id for lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON public.user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_points ON public.user_profiles(total_points DESC, level DESC);

-- =====================================================
-- Learning Modules Table (unified)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.learning_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Common fields
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    learning_objective TEXT NOT NULL,
    difficulty_level VARCHAR(20) DEFAULT 'beginner',
    estimated_minutes INT DEFAULT 5,
    is_active BOOLEAN DEFAULT TRUE,

    -- MAPS-specific
    mi_skill_category VARCHAR(100),
    scenario_context TEXT,
    persona_config JSONB,
    maps_rubric JSONB,
    target_competencies TEXT[] DEFAULT '{}',

    -- mi-learning-platform specific
    module_number INTEGER UNIQUE,
    slug VARCHAR(255) UNIQUE,
    technique_focus VARCHAR(100),
    stage_of_change VARCHAR(50),
    mi_process VARCHAR(50),
    description TEXT,
    dialogue_content JSONB,
    points INTEGER DEFAULT 500,
    display_order INTEGER DEFAULT 0,
    is_published BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_learning_modules_code ON public.learning_modules(code);
CREATE INDEX IF NOT EXISTS idx_learning_modules_published ON public.learning_modules(is_published, display_order);
CREATE INDEX IF NOT EXISTS idx_learning_modules_active ON public.learning_modules(is_active, display_order);

-- =====================================================
-- Scenarios Table (MAPS free-form persona chat)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_name VARCHAR(100) NOT NULL,
    persona_description TEXT NOT NULL,
    persona_config JSONB NOT NULL,
    scenario_context TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scenarios_active ON public.scenarios(is_active);

-- =====================================================
-- Scenario Attempts Table (free-form chat)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.scenario_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    scenario_id UUID NOT NULL REFERENCES public.scenarios(id) ON DELETE CASCADE,

    turn_count INT DEFAULT 0,
    transcript JSONB DEFAULT '[]',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    final_scores JSONB,
    completion_reason VARCHAR(50),

    -- Persona state tracking
    initial_persona_state JSONB,
    final_persona_state JSONB,

    -- Skills tracking
    skills_demonstrated TEXT[] DEFAULT '{}',
    negative_behaviors TEXT[] DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_scenario_attempts_user ON public.scenario_attempts(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scenario_attempts_scenario ON public.scenario_attempts(scenario_id);

-- =====================================================
-- User Progress Table (module-based)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.user_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    module_id UUID NOT NULL REFERENCES public.learning_modules(id) ON DELETE CASCADE,

    -- Status
    status VARCHAR(20) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed')),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- MAPS-specific
    current_rapport_score INT DEFAULT 0,
    current_resistance_level INT DEFAULT 5,
    tone_spectrum_position FLOAT DEFAULT 0.0,
    path_taken TEXT[] DEFAULT '{}',

    -- mi-learning-platform specific
    current_node_id VARCHAR(50) DEFAULT 'node_1',
    nodes_completed TEXT[] DEFAULT '{}',
    points_earned INTEGER DEFAULT 0,
    completion_score INTEGER DEFAULT 0,
    techniques_demonstrated JSONB DEFAULT '{}',

    UNIQUE(user_id, module_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_user_progress_user ON public.user_progress(user_id, status);
CREATE INDEX IF NOT EXISTS idx_user_progress_module ON public.user_progress(module_id, status);

-- =====================================================
-- Dialogue Attempts Table (granular choice tracking)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.dialogue_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attempt_id UUID NOT NULL REFERENCES public.user_progress(id) ON DELETE CASCADE,

    node_id VARCHAR(50) NOT NULL,
    choice_id VARCHAR(50) NOT NULL,
    choice_text TEXT NOT NULL,
    technique VARCHAR(100) NOT NULL,
    is_correct_technique BOOLEAN NOT NULL,
    feedback_text TEXT NOT NULL,
    evoked_change_talk BOOLEAN DEFAULT FALSE,
    points_earned INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index
CREATE INDEX IF NOT EXISTS idx_dialogue_attempts_attempt ON public.dialogue_attempts(attempt_id);

-- =====================================================
-- Learning Paths Table (MAPS feature)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.learning_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    module_sequence UUID[] NOT NULL,
    target_audience VARCHAR(100),
    estimated_total_minutes INT,
    maps_competencies_targeted TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_learning_paths_active ON public.learning_paths(is_active);

-- =====================================================
-- Voice Sessions Table (optional)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.voice_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attempt_id UUID NOT NULL REFERENCES public.scenario_attempts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    mode VARCHAR(20) NOT NULL DEFAULT 'stt_only',
    mistral_config JSONB,
    persona_config JSONB,

    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    duration_seconds INT DEFAULT 0,
    transcript JSONB DEFAULT '[]',
    metrics JSONB,
    status VARCHAR(20) DEFAULT 'created',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index
CREATE INDEX IF NOT EXISTS idx_voice_sessions_attempt ON public.voice_sessions(attempt_id);

-- =====================================================
-- Row Level Security (RLS) Policies
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.learning_modules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scenarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scenario_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dialogue_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.learning_paths ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.voice_sessions ENABLE ROW LEVEL SECURITY;

-- User Profiles
CREATE POLICY "Users can view own profile"
    ON public.user_profiles
    FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON public.user_profiles
    FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.user_profiles
    FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Service role can manage all profiles"
    ON public.user_profiles
    FOR ALL
    USING (auth.role() = 'service_role');

-- Learning Modules (publicly readable if active/published)
CREATE POLICY "Public can view active modules"
    ON public.learning_modules
    FOR SELECT
    USING (is_active = TRUE);

CREATE POLICY "Service role can manage modules"
    ON public.learning_modules
    FOR ALL
    USING (auth.role() = 'service_role');

-- Scenarios (publicly readable if active)
CREATE POLICY "Public can view active scenarios"
    ON public.scenarios
    FOR SELECT
    USING (is_active = TRUE);

CREATE POLICY "Service role can manage scenarios"
    ON public.scenarios
    FOR ALL
    USING (auth.role() = 'service_role');

-- Scenario Attempts
CREATE POLICY "Users can view own attempts"
    ON public.scenario_attempts
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own attempts"
    ON public.scenario_attempts
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own attempts"
    ON public.scenario_attempts
    FOR UPDATE
    USING (auth.uid() = user_id);

-- User Progress
CREATE POLICY "Users can view own progress"
    ON public.user_progress
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own progress"
    ON public.user_progress
    FOR ALL
    USING (auth.uid() = user_id);

-- Dialogue Attempts
CREATE POLICY "Users can view own dialogue attempts"
    ON public.dialogue_attempts
    FOR SELECT
    USING (auth.uid() = (SELECT user_id FROM public.user_progress WHERE id = dialogue_attempts.attempt_id));

CREATE POLICY "Users can create own dialogue attempts"
    ON public.dialogue_attempts
    FOR INSERT
    WITH CHECK (auth.uid() = (SELECT user_id FROM public.user_progress WHERE id = dialogue_attempts.attempt_id));

-- Learning Paths
CREATE POLICY "Public can view active learning paths"
    ON public.learning_paths
    FOR SELECT
    USING (is_active = TRUE);

CREATE POLICY "Service role can manage learning paths"
    ON public.learning_paths
    FOR ALL
    USING (auth.role() = 'service_role');

-- Voice Sessions
CREATE POLICY "Users can view own voice sessions"
    ON public.voice_sessions
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own voice sessions"
    ON public.voice_sessions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- =====================================================
-- Functions and Triggers
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to tables with updated_at
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_user_progress_updated_at
    BEFORE UPDATE ON public.user_progress
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_learning_modules_updated_at
    BEFORE UPDATE ON public.learning_modules
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_learning_paths_updated_at
    BEFORE UPDATE ON public.learning_paths
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_scenario_attempts_updated_at
    BEFORE UPDATE ON public.scenario_attempts
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_voice_sessions_updated_at
    BEFORE UPDATE ON public.voice_sessions
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- Function to create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, user_id, display_name, role)
    VALUES (
        NEW.id,
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'display_name', NEW.email->>'0', split_part(NEW.email, '@', 1)),
        'FULL'
    )
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop existing trigger if exists
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Trigger to create profile on user signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- =====================================================
-- Grant Permissions
-- =====================================================
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON public.user_profiles TO authenticated, service_role;
GRANT SELECT ON public.learning_modules TO anon, authenticated, service_role;
GRANT SELECT ON public.scenarios TO anon, authenticated, service_role;
GRANT ALL ON public.scenario_attempts TO authenticated, service_role;
GRANT ALL ON public.user_progress TO authenticated, service_role;
GRANT ALL ON public.dialogue_attempts TO authenticated, service_role;
GRANT SELECT ON public.learning_paths TO anon, authenticated, service_role;
GRANT ALL ON public.voice_sessions TO authenticated, service_role;
