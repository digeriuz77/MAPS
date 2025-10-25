-- Create trust_tiers configuration table
-- This defines the trust progression mechanics for different trust levels

CREATE TABLE trust_tiers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tier_name VARCHAR(20) NOT NULL UNIQUE,
    min_threshold DECIMAL(3,2) NOT NULL,
    max_threshold DECIMAL(3,2) NOT NULL,
    trust_delta_excellent DECIMAL(3,2) NOT NULL,
    trust_delta_good DECIMAL(3,2) NOT NULL,
    trust_delta_adequate DECIMAL(3,2) NOT NULL,
    trust_delta_poor DECIMAL(3,2) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert the four trust tiers with initial configurations
INSERT INTO trust_tiers (tier_name, min_threshold, max_threshold, trust_delta_excellent, trust_delta_good, trust_delta_adequate, trust_delta_poor, description) VALUES
('defensive', 0.00, 0.25, 0.08, 0.05, 0.02, -0.25, 'Very cautious personas - slow to trust, quick to lose trust'),
('cautious', 0.25, 0.50, 0.12, 0.08, 0.03, -0.20, 'Moderately cautious personas - careful but can build trust'),
('opening', 0.50, 0.75, 0.18, 0.12, 0.06, -0.15, 'Moderately trusting personas - open to building relationships'),
('trusting', 0.75, 1.00, 0.25, 0.18, 0.10, -0.10, 'Very trusting personas - quick to trust, slow to lose trust');

-- Add comments for documentation
COMMENT ON TABLE trust_tiers IS 'Configuration table defining trust progression mechanics for different trust personality types';
COMMENT ON COLUMN trust_tiers.tier_name IS 'Name of the trust tier (defensive, cautious, opening, trusting)';
COMMENT ON COLUMN trust_tiers.min_threshold IS 'Minimum trust_variable value for this tier (0.00-1.00)';
COMMENT ON COLUMN trust_tiers.max_threshold IS 'Maximum trust_variable value for this tier (0.00-1.00)';
COMMENT ON COLUMN trust_tiers.trust_delta_excellent IS 'Trust increase for excellent empathy (8.5+)';
COMMENT ON COLUMN trust_tiers.trust_delta_good IS 'Trust increase for good empathy (7.0+)';
COMMENT ON COLUMN trust_tiers.trust_delta_adequate IS 'Trust increase for adequate empathy (5.0+)';
COMMENT ON COLUMN trust_tiers.trust_delta_poor IS 'Trust change for poor empathy (<4.0)';

-- Create index for efficient tier lookups
CREATE INDEX idx_trust_tiers_thresholds ON trust_tiers(min_threshold, max_threshold);