-- Add trust_variable column to enhanced_personas table
-- This single editable value determines the persona's trust characteristics

ALTER TABLE enhanced_personas 
ADD COLUMN trust_variable DECIMAL(3,2) DEFAULT 0.50 
CHECK (trust_variable >= 0.00 AND trust_variable <= 1.00);

-- Set initial trust_variable values based on persona characteristics
-- Based on character traits and descriptions from existing personas
UPDATE enhanced_personas 
SET trust_variable = CASE 
    -- Vic: confident, overestimates impact, dismisses feedback - moderately cautious
    WHEN persona_id = 'vic' THEN 0.35
    -- Mary: caring, empathetic when safe, family-oriented - moderately trusting 
    WHEN persona_id = 'mary' THEN 0.65
    -- Jan: self-critical, internalizes stress, confused - cautious
    WHEN persona_id = 'jan' THEN 0.40
    -- Terry: direct, dismissive of inefficiency, values competence - defensive
    WHEN persona_id = 'terry' THEN 0.25
    -- Default for any other personas
    ELSE 0.50
END;

-- Add comment for documentation
COMMENT ON COLUMN enhanced_personas.trust_variable IS 'Trust personality variable (0.00-1.00): 0.00=very defensive, 1.00=very trusting. Used to determine trust progression mechanics from trust_tiers table.';

-- Create index for efficient trust tier lookups
CREATE INDEX idx_enhanced_personas_trust_variable ON enhanced_personas(trust_variable);