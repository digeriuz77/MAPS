-- 0012_add_default_persona_state.sql
-- Add default values for persona state fields to allow inserts without explicit state

-- Alter scenario_attempts to have default persona state
ALTER TABLE scenario_attempts
    ALTER COLUMN initial_persona_state
    SET DEFAULT '{"trust_level": 3, "openness_level": 2, "resistance_active": true}'::jsonb;

-- Ensure the column is nullable for flexibility
ALTER TABLE scenario_attempts
    ALTER COLUMN initial_persona_state DROP NOT NULL;

-- Also update mi_practice_attempts if it has similar constraints
DO $$
BEGIN
    -- Check if column exists and is NOT NULL, then make it nullable
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'mi_practice_attempts'
        AND column_name = 'initial_persona_state'
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE mi_practice_attempts
            ALTER COLUMN initial_persona_state DROP NOT NULL;
    END IF;

    -- Add default if it doesn't have one
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'mi_practice_attempts'
        AND column_name = 'initial_persona_state'
        AND column_default IS NULL
    ) THEN
        ALTER TABLE mi_practice_attempts
            ALTER COLUMN initial_persona_state
            SET DEFAULT '{"rapport": 50, "resistance": 5}'::jsonb;
    END IF;
END $$;
