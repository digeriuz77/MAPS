-- 0008_trust_configuration.sql
-- Trust delta configuration per persona
-- Enables trust tuning without code deployment

-- Create trust_configuration table
CREATE TABLE IF NOT EXISTS trust_configuration (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  persona_id TEXT NOT NULL UNIQUE REFERENCES enhanced_personas(persona_id) ON DELETE CASCADE,

  -- Trust deltas based on interaction quality
  quality_deltas JSONB NOT NULL DEFAULT '{
    "poor": -0.02,
    "adequate": 0.00,
    "good": 0.01,
    "excellent": 0.02
  }'::jsonb,

  -- Multipliers based on empathy tone
  empathy_multipliers JSONB NOT NULL DEFAULT '{
    "hostile": 0.5,
    "neutral": 1.0,
    "supportive": 1.5,
    "deeply_empathetic": 2.0
  }'::jsonb,

  -- Adjustments based on trust trajectory
  trajectory_adjustments JSONB NOT NULL DEFAULT '{
    "declining": -0.01,
    "stable": 0.00,
    "building": 0.005,
    "breakthrough": 0.02
  }'::jsonb,

  -- User approach modifiers
  approach_modifiers JSONB NOT NULL DEFAULT '{
    "directive": 0.8,
    "questioning": 1.0,
    "curious": 1.2,
    "collaborative": 1.3,
    "supportive": 1.5
  }'::jsonb,

  -- Trust decay settings
  trust_decay_rate FLOAT DEFAULT 0.01, -- Daily decay if no interaction
  min_trust FLOAT DEFAULT 0.10,        -- Floor (can't go below)
  max_trust FLOAT DEFAULT 0.95,        -- Ceiling (can't exceed)

  -- Tier transition settings
  tier_transition_momentum FLOAT DEFAULT 0.02,  -- Bonus when crossing tier boundary
  regression_penalty FLOAT DEFAULT -0.03,       -- Penalty for dropping tier

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for fast persona lookups
CREATE INDEX idx_trust_config_persona ON trust_configuration(persona_id);

-- Seed configurations for all 3 personas
-- MARY: Slower to trust (more defensive), needs consistent empathy
INSERT INTO trust_configuration (
  persona_id,
  quality_deltas,
  empathy_multipliers,
  trajectory_adjustments,
  approach_modifiers,
  trust_decay_rate,
  tier_transition_momentum,
  regression_penalty
) VALUES (
  'mary',
  '{
    "poor": -0.03,
    "adequate": 0.00,
    "good": 0.015,
    "excellent": 0.025
  }'::jsonb,
  '{
    "hostile": 0.3,
    "neutral": 1.0,
    "supportive": 1.6,
    "deeply_empathetic": 2.2
  }'::jsonb,
  '{
    "declining": -0.015,
    "stable": 0.00,
    "building": 0.008,
    "breakthrough": 0.025
  }'::jsonb,
  '{
    "directive": 0.7,
    "questioning": 1.0,
    "curious": 1.3,
    "collaborative": 1.4,
    "supportive": 1.6
  }'::jsonb,
  0.012,  -- Slightly faster decay (stress makes her withdraw)
  0.025,  -- Good momentum bonus
  -0.04   -- Strong regression penalty (setbacks hit hard)
) ON CONFLICT (persona_id) DO UPDATE SET
  quality_deltas = EXCLUDED.quality_deltas,
  empathy_multipliers = EXCLUDED.empathy_multipliers,
  trajectory_adjustments = EXCLUDED.trajectory_adjustments,
  approach_modifiers = EXCLUDED.approach_modifiers,
  trust_decay_rate = EXCLUDED.trust_decay_rate,
  tier_transition_momentum = EXCLUDED.tier_transition_momentum,
  regression_penalty = EXCLUDED.regression_penalty,
  updated_at = NOW();

-- TERRY: Medium trust building, values directness and efficiency
INSERT INTO trust_configuration (
  persona_id,
  quality_deltas,
  empathy_multipliers,
  trajectory_adjustments,
  approach_modifiers,
  trust_decay_rate,
  tier_transition_momentum,
  regression_penalty
) VALUES (
  'terry',
  '{
    "poor": -0.02,
    "adequate": 0.005,
    "good": 0.02,
    "excellent": 0.03
  }'::jsonb,
  '{
    "hostile": 0.6,
    "neutral": 1.0,
    "supportive": 1.3,
    "deeply_empathetic": 1.5
  }'::jsonb,
  '{
    "declining": -0.01,
    "stable": 0.00,
    "building": 0.01,
    "breakthrough": 0.03
  }'::jsonb,
  '{
    "directive": 1.1,
    "questioning": 1.0,
    "curious": 1.2,
    "collaborative": 1.4,
    "supportive": 1.2
  }'::jsonb,
  0.008,  -- Moderate decay
  0.02,   -- Standard momentum
  -0.025  -- Moderate regression penalty
) ON CONFLICT (persona_id) DO UPDATE SET
  quality_deltas = EXCLUDED.quality_deltas,
  empathy_multipliers = EXCLUDED.empathy_multipliers,
  trajectory_adjustments = EXCLUDED.trajectory_adjustments,
  approach_modifiers = EXCLUDED.approach_modifiers,
  trust_decay_rate = EXCLUDED.trust_decay_rate,
  tier_transition_momentum = EXCLUDED.tier_transition_momentum,
  regression_penalty = EXCLUDED.regression_penalty,
  updated_at = NOW();

-- JAN: Fastest to trust (but fragile), needs gentle approach
INSERT INTO trust_configuration (
  persona_id,
  quality_deltas,
  empathy_multipliers,
  trajectory_adjustments,
  approach_modifiers,
  trust_decay_rate,
  tier_transition_momentum,
  regression_penalty
) VALUES (
  'jan',
  '{
    "poor": -0.04,
    "adequate": 0.005,
    "good": 0.025,
    "excellent": 0.035
  }'::jsonb,
  '{
    "hostile": 0.2,
    "neutral": 1.0,
    "supportive": 1.8,
    "deeply_empathetic": 2.5
  }'::jsonb,
  '{
    "declining": -0.02,
    "stable": 0.00,
    "building": 0.012,
    "breakthrough": 0.03
  }'::jsonb,
  '{
    "directive": 0.6,
    "questioning": 1.0,
    "curious": 1.4,
    "collaborative": 1.6,
    "supportive": 1.8
  }'::jsonb,
  0.015,  -- Fastest decay (internalized stress)
  0.03,   -- High momentum (opens up quickly)
  -0.05   -- Highest regression penalty (fragile trust)
) ON CONFLICT (persona_id) DO UPDATE SET
  quality_deltas = EXCLUDED.quality_deltas,
  empathy_multipliers = EXCLUDED.empathy_multipliers,
  trajectory_adjustments = EXCLUDED.trajectory_adjustments,
  approach_modifiers = EXCLUDED.approach_modifiers,
  trust_decay_rate = EXCLUDED.trust_decay_rate,
  tier_transition_momentum = EXCLUDED.tier_transition_momentum,
  regression_penalty = EXCLUDED.regression_penalty,
  updated_at = NOW();

-- Comments explaining the trust formula
COMMENT ON TABLE trust_configuration IS 'Per-persona trust calculation parameters. Enables trust tuning without code deployment.';
COMMENT ON COLUMN trust_configuration.quality_deltas IS 'Base trust change per interaction quality level';
COMMENT ON COLUMN trust_configuration.empathy_multipliers IS 'Multiplier based on user empathy tone';
COMMENT ON COLUMN trust_configuration.trajectory_adjustments IS 'Additional delta based on trust direction';
COMMENT ON COLUMN trust_configuration.approach_modifiers IS 'Multiplier based on user approach style';
COMMENT ON COLUMN trust_configuration.trust_decay_rate IS 'Daily trust decay when no interaction occurs';
COMMENT ON COLUMN trust_configuration.tier_transition_momentum IS 'Bonus when crossing tier threshold upward';
COMMENT ON COLUMN trust_configuration.regression_penalty IS 'Penalty when dropping below tier threshold';

-- Usage example in comments
COMMENT ON TABLE trust_configuration IS E'Trust Formula:\n\nfinal_delta = (\n  quality_deltas[interaction_quality] +\n  trajectory_adjustments[trust_trajectory]\n) * empathy_multipliers[empathy_tone] * approach_modifiers[user_approach]\n\nwith tier_transition_momentum added when crossing tier boundary upward\nand regression_penalty added when dropping tier';
