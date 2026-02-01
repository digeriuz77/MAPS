-- 0002_current_scenario_attempts.sql
-- CURRENT APPLICATION - MAPS MI Training Platform
-- Track user attempts at scenarios

CREATE TABLE IF NOT EXISTS scenario_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    scenario_id UUID NOT NULL,
    
    -- Timestamps
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP NULL,
    
    -- Conversation data
    turn_count INT DEFAULT 0,
    transcript JSONB NOT NULL DEFAULT '[]',
    
    -- Final outcomes
    final_scores JSONB NULL,
    completion_reason VARCHAR(50),
    
    -- State tracking
    initial_persona_state JSONB NOT NULL,
    final_persona_state JSONB NULL,
    
    -- Skills and behaviors
    skills_demonstrated TEXT[] DEFAULT '{}',
    negative_behaviors TEXT[] DEFAULT '{}',
    
    -- Foreign keys
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_scenario FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_scenario_attempts_user ON scenario_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_scenario_attempts_scenario ON scenario_attempts(scenario_id);
CREATE INDEX IF NOT EXISTS idx_scenario_attempts_completed ON scenario_attempts(completed_at) WHERE completed_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_scenario_attempts_user_scenario ON scenario_attempts(user_id, scenario_id);

COMMENT ON TABLE scenario_attempts IS 'User attempts at training scenarios';
COMMENT ON COLUMN scenario_attempts.transcript IS 'Array of turns with manager message, persona response, analysis';
COMMENT ON COLUMN scenario_attempts.completion_reason IS 'success, abandoned, time_limit';
