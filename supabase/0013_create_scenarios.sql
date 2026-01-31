-- 0013_create_scenarios.sql
-- Scenarios table for scenario-based MI training platform

CREATE TABLE IF NOT EXISTS scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    mi_skill_category VARCHAR(100),
    difficulty VARCHAR(20) DEFAULT 'beginner',
    estimated_minutes INT DEFAULT 5,
    
    -- The setup
    situation TEXT NOT NULL,
    learning_objective TEXT NOT NULL,
    
    -- Persona configuration (JSONB for flexibility)
    persona_config JSONB NOT NULL,
    
    -- Success criteria
    success_criteria JSONB NOT NULL,
    
    -- MAPS scoring rubric
    maps_rubric JSONB NOT NULL,
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_scenarios_skill ON scenarios(mi_skill_category);
CREATE INDEX IF NOT EXISTS idx_scenarios_difficulty ON scenarios(difficulty);
CREATE INDEX IF NOT EXISTS idx_scenarios_code ON scenarios(code);
CREATE INDEX IF NOT EXISTS idx_scenarios_active ON scenarios(is_active) WHERE is_active = TRUE;

-- Comment
COMMENT ON TABLE scenarios IS 'Atomic training units for MI practice';
COMMENT ON COLUMN scenarios.code IS 'Unique code like "close-ambivalent-001"';
COMMENT ON COLUMN scenarios.persona_config IS 'Full persona configuration including personality, triggers, response patterns';
COMMENT ON COLUMN scenarios.success_criteria IS 'Turn range, required skills, avoid behaviors, state goals';
COMMENT ON COLUMN scenarios.maps_rubric IS 'MAPS rubric dimensions with weights and indicators';
