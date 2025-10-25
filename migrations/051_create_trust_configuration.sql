-- Migration: Create trust_configuration table for configurable trust deltas
-- Purpose: Allow remote configuration of trust progression speeds
-- Date: 2025-10-22

-- Create trust_configuration table
CREATE TABLE IF NOT EXISTS trust_configuration (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_name VARCHAR(255) NOT NULL,
    config_description TEXT NOT NULL,
    numeric_value FLOAT NOT NULL,
    min_value FLOAT DEFAULT 0.0,
    max_value FLOAT DEFAULT 1.0,
    category VARCHAR(50) DEFAULT 'trust_progression',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_trust_config_key ON trust_configuration(config_key);
CREATE INDEX IF NOT EXISTS idx_trust_config_category ON trust_configuration(category, is_active);

-- Enable Row Level Security
ALTER TABLE trust_configuration ENABLE ROW LEVEL SECURITY;

-- Policy for service role access
CREATE POLICY "Service role can manage trust_configuration" ON trust_configuration
FOR ALL USING (auth.role() = 'service_role');

-- Insert default trust delta configurations
INSERT INTO trust_configuration (
    config_key,
    config_name,
    config_description,
    numeric_value,
    min_value,
    max_value,
    category
) VALUES 
    -- Current values (can be increased for faster progression)
    ('trust_delta_excellent', 'Excellent Empathy Trust Gain', 'Trust increase per turn for empathy scores 8.5+', 0.15, 0.05, 0.50, 'trust_progression'),
    ('trust_delta_good', 'Good Empathy Trust Gain', 'Trust increase per turn for empathy scores 7.0-8.4', 0.10, 0.05, 0.40, 'trust_progression'),
    ('trust_delta_adequate', 'Adequate Empathy Trust Gain', 'Trust increase per turn for empathy scores 5.0-6.9', 0.05, 0.01, 0.30, 'trust_progression'),
    ('trust_delta_poor', 'Poor Empathy Trust Loss', 'Trust decrease per turn for empathy scores below 4.0', -0.15, -0.50, -0.05, 'trust_progression'),
    
    -- Trust thresholds (tier boundaries)
    ('trust_threshold_cautious', 'Cautious Trust Threshold', 'Trust level needed to reach Cautious tier', 4.5, 3.0, 6.0, 'trust_thresholds'),
    ('trust_threshold_opening', 'Opening Trust Threshold', 'Trust level needed to reach Opening tier', 6.5, 5.0, 8.0, 'trust_thresholds'),
    ('trust_threshold_trusting', 'Trusting Trust Threshold', 'Trust level needed to reach Trusting tier', 8.0, 6.5, 9.5, 'trust_thresholds'),
    
    -- Starting configuration
    ('trust_starting_level', 'Starting Trust Level', 'Initial trust level for new conversations', 3.0, 1.0, 5.0, 'trust_initialization'),
    
    -- Empathy score thresholds
    ('empathy_threshold_excellent', 'Excellent Empathy Threshold', 'Empathy score threshold for excellent rating', 8.5, 7.0, 10.0, 'empathy_thresholds'),
    ('empathy_threshold_good', 'Good Empathy Threshold', 'Empathy score threshold for good rating', 7.0, 5.0, 8.5, 'empathy_thresholds'),
    ('empathy_threshold_adequate', 'Adequate Empathy Threshold', 'Empathy score threshold for adequate rating', 5.0, 3.0, 7.0, 'empathy_thresholds'),
    ('empathy_threshold_poor', 'Poor Empathy Threshold', 'Empathy score threshold for poor rating (below this)', 4.0, 1.0, 6.0, 'empathy_thresholds')

ON CONFLICT (config_key) DO UPDATE SET
    config_name = EXCLUDED.config_name,
    config_description = EXCLUDED.config_description,
    numeric_value = EXCLUDED.numeric_value,
    updated_at = NOW();

-- Add table comment
COMMENT ON TABLE trust_configuration IS 'Configurable parameters for trust progression system';

-- Grant permissions
GRANT ALL ON trust_configuration TO service_role;