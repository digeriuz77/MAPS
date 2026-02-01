-- 0004_current_mi_practice_tables.sql
-- CURRENT APPLICATION - MAPS MI Training Platform
-- MI Practice Module Integration - Structured dialogue scenarios with tone interpolation

-- ============================================
-- 1. MI PRACTICE MODULES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS mi_practice_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    
    -- Categorization
    mi_focus_area VARCHAR(100),
    difficulty_level VARCHAR(20) DEFAULT 'beginner',
    estimated_minutes INT DEFAULT 5,
    
    -- Learning design
    learning_objective TEXT NOT NULL,
    scenario_context TEXT NOT NULL,
    
    -- Persona configuration (includes tone_spectrum for 0.0-1.0 interpolation)
    persona_config JSONB NOT NULL,
    
    -- Dialogue structure - branching dialogue tree
    dialogue_structure JSONB NOT NULL,
    
    -- MAPS alignment
    target_competencies TEXT[] DEFAULT '{}',
    maps_rubric JSONB NOT NULL,
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mi_modules_focus ON mi_practice_modules(mi_focus_area);
CREATE INDEX IF NOT EXISTS idx_mi_modules_difficulty ON mi_practice_modules(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_mi_modules_code ON mi_practice_modules(code);
CREATE INDEX IF NOT EXISTS idx_mi_modules_active ON mi_practice_modules(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE mi_practice_modules IS 'Structured MI practice dialogue modules';

-- ============================================
-- 2. MI PRACTICE ATTEMPTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS mi_practice_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    module_id UUID NOT NULL REFERENCES mi_practice_modules(id) ON DELETE CASCADE,
    
    -- Timing
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP NULL,
    
    -- Progress tracking
    current_node_id VARCHAR(50),
    path_taken TEXT[] DEFAULT '{}',
    
    -- State tracking (continuous spectrum 0.0-1.0)
    current_rapport_score INT DEFAULT 0,
    current_resistance_level INT DEFAULT 5,
    tone_spectrum_position FLOAT DEFAULT 0.0,
    
    -- Attempt data
    choices_made JSONB DEFAULT '[]',
    
    -- Final assessment
    completion_status VARCHAR(50),
    final_scores JSONB,
    
    -- Learning analytics
    insights_generated JSONB DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mi_attempts_user ON mi_practice_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_mi_attempts_module ON mi_practice_attempts(module_id);
CREATE INDEX IF NOT EXISTS idx_mi_attempts_completed ON mi_practice_attempts(completed_at) WHERE completed_at IS NOT NULL;

COMMENT ON TABLE mi_practice_attempts IS 'User attempts at MI practice modules';
COMMENT ON COLUMN mi_practice_attempts.tone_spectrum_position IS 'Continuous 0.0-1.0 scale for persona openness';

-- ============================================
-- 3. MI LEARNING PATHS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS mi_learning_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Path structure
    module_sequence UUID[] NOT NULL,
    
    -- Learning design
    target_audience VARCHAR(100),
    estimated_total_minutes INT,
    maps_competencies_targeted TEXT[] DEFAULT '{}',
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mi_paths_code ON mi_learning_paths(code);
CREATE INDEX IF NOT EXISTS idx_mi_paths_active ON mi_learning_paths(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE mi_learning_paths IS 'Curated learning paths through MI practice modules';

-- ============================================
-- 4. MI USER PROGRESS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS mi_user_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Overall progress
    modules_completed INT DEFAULT 0,
    modules_attempted INT DEFAULT 0,
    total_practice_minutes INT DEFAULT 0,
    
    -- Competency tracking
    competency_scores JSONB DEFAULT '{}',
    
    -- Technique exposure
    techniques_practiced JSONB DEFAULT '{}',
    
    -- Current learning path
    active_learning_path_id UUID REFERENCES mi_learning_paths(id),
    current_module_index INT DEFAULT 0,
    
    -- Insights
    learning_insights JSONB DEFAULT '[]',
    
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_mi_progress_user ON mi_user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_mi_progress_path ON mi_user_progress(active_learning_path_id);

COMMENT ON TABLE mi_user_progress IS 'Aggregated MI practice progress per user';

-- ============================================
-- 5. EXTEND SCENARIOS TABLE
-- ============================================
ALTER TABLE scenarios 
    ADD COLUMN IF NOT EXISTS mi_practice_module_id UUID REFERENCES mi_practice_modules(id),
    ADD COLUMN IF NOT EXISTS has_structured_dialogue BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_scenarios_mi_module ON scenarios(mi_practice_module_id);

-- ============================================
-- 6. EXTEND SCENARIO ATTEMPTS TABLE
-- ============================================
ALTER TABLE scenario_attempts 
    ADD COLUMN IF NOT EXISTS mi_module_attempt_id UUID REFERENCES mi_practice_attempts(id),
    ADD COLUMN IF NOT EXISTS dialogue_path JSONB DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_scenario_attempts_mi ON scenario_attempts(mi_module_attempt_id) WHERE mi_module_attempt_id IS NOT NULL;

-- ============================================
-- 7. RLS POLICIES
-- ============================================
ALTER TABLE mi_practice_modules ENABLE ROW LEVEL SECURITY;
ALTER TABLE mi_practice_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE mi_learning_paths ENABLE ROW LEVEL SECURITY;
ALTER TABLE mi_user_progress ENABLE ROW LEVEL SECURITY;

-- mi_practice_modules: readable by all authenticated users
CREATE POLICY "MI modules readable by authenticated users"
    ON mi_practice_modules FOR SELECT TO authenticated USING (is_active = TRUE);

-- mi_practice_attempts: users can only see their own attempts
CREATE POLICY "Users can view own attempts" ON mi_practice_attempts FOR SELECT
    USING (user_id = auth.uid());
CREATE POLICY "Users can create own attempts" ON mi_practice_attempts FOR INSERT
    WITH CHECK (user_id = auth.uid());
CREATE POLICY "Users can update own attempts" ON mi_practice_attempts FOR UPDATE
    USING (user_id = auth.uid());

-- mi_learning_paths: readable by all authenticated users
CREATE POLICY "Learning paths readable by authenticated users"
    ON mi_learning_paths FOR SELECT TO authenticated USING (is_active = TRUE);

-- mi_user_progress: users can only see/update their own progress
CREATE POLICY "Users can view own progress" ON mi_user_progress FOR SELECT
    USING (user_id = auth.uid());
CREATE POLICY "Users can create own progress" ON mi_user_progress FOR INSERT
    WITH CHECK (user_id = auth.uid());
CREATE POLICY "Users can update own progress" ON mi_user_progress FOR UPDATE
    USING (user_id = auth.uid());

-- ============================================
-- 8. TRIGGERS (auto-update timestamps)
-- ============================================
CREATE OR REPLACE FUNCTION update_mi_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_mi_practice_modules_updated_at
    BEFORE UPDATE ON mi_practice_modules FOR EACH ROW EXECUTE FUNCTION update_mi_updated_at();
CREATE TRIGGER update_mi_practice_attempts_updated_at
    BEFORE UPDATE ON mi_practice_attempts FOR EACH ROW EXECUTE FUNCTION update_mi_updated_at();
CREATE TRIGGER update_mi_learning_paths_updated_at
    BEFORE UPDATE ON mi_learning_paths FOR EACH ROW EXECUTE FUNCTION update_mi_updated_at();
CREATE TRIGGER update_mi_user_progress_updated_at
    BEFORE UPDATE ON mi_user_progress FOR EACH ROW EXECUTE FUNCTION update_mi_updated_at();
