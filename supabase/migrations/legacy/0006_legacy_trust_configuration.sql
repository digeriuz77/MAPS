-- 0006_legacy_trust_configuration.sql
-- Trust delta configuration per persona
-- LEGACY APPLICATION - Character AI Chat App
-- Enables trust tuning without code deployment

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
  trust_decay_rate FLOAT DEFAULT 0.01,
  min_trust FLOAT DEFAULT 0.10,
  max_trust FLOAT DEFAULT 0.95,

  -- Tier transition settings
  tier_transition_momentum FLOAT DEFAULT 0.02,
  regression_penalty FLOAT DEFAULT -0.03,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trust_config_persona ON trust_configuration(persona_id);

-- MARY: Slower to trust (more defensive), needs consistent empathy
INSERT INTO trust_configuration (
  persona_id, quality_deltas, empathy_multipliers, trajectory_adjustments,
  approach_modifiers, trust_decay_rate, tier_transition_momentum, regression_penalty
) VALUES (
  'mary',
  '{"poor": -0.02, "adequate": 0.01, "good": 0.03, "excellent": 0.05}'::jsonb,
  '{"hostile": 0.2, "neutral": 1.0, "supportive": 1.8, "deeply_empathetic": 2.5}'::jsonb,
  '{"declining": -0.01, "stable": 0.00, "building": 0.015, "breakthrough": 0.035}'::jsonb,
  '{"directive": 0.6, "questioning": 1.0, "curious": 1.4, "collaborative": 1.8, "supportive": 2.0}'::jsonb,
  0.012, 0.025, -0.02
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
  persona_id, quality_deltas, empathy_multipliers, trajectory_adjustments,
  approach_modifiers, trust_decay_rate, tier_transition_momentum, regression_penalty
) VALUES (
  'terry',
  '{"poor": -0.02, "adequate": 0.01, "good": 0.04, "excellent": 0.06}'::jsonb,
  '{"hostile": 0.3, "neutral": 1.0, "supportive": 1.6, "deeply_empathetic": 2.0}'::jsonb,
  '{"declining": -0.01, "stable": 0.00, "building": 0.02, "breakthrough": 0.04}'::jsonb,
  '{"directive": 1.2, "questioning": 1.0, "curious": 1.3, "collaborative": 1.9, "supportive": 1.7}'::jsonb,
  0.008, 0.02, -0.02
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
  persona_id, quality_deltas, empathy_multipliers, trajectory_adjustments,
  approach_modifiers, trust_decay_rate, tier_transition_momentum, regression_penalty
) VALUES (
  'jan',
  '{"poor": -0.03, "adequate": 0.01, "good": 0.04, "excellent": 0.07}'::jsonb,
  '{"hostile": 0.2, "neutral": 1.0, "supportive": 2.0, "deeply_empathetic": 2.8}'::jsonb,
  '{"declining": -0.02, "stable": 0.00, "building": 0.02, "breakthrough": 0.05}'::jsonb,
  '{"directive": 0.5, "questioning": 1.0, "curious": 1.5, "collaborative": 2.0, "supportive": 2.2}'::jsonb,
  0.015, 0.03, -0.03
) ON CONFLICT (persona_id) DO UPDATE SET
  quality_deltas = EXCLUDED.quality_deltas,
  empathy_multipliers = EXCLUDED.empathy_multipliers,
  trajectory_adjustments = EXCLUDED.trajectory_adjustments,
  approach_modifiers = EXCLUDED.approach_modifiers,
  trust_decay_rate = EXCLUDED.trust_decay_rate,
  tier_transition_momentum = EXCLUDED.tier_transition_momentum,
  regression_penalty = EXCLUDED.regression_penalty,
  updated_at = NOW();

COMMENT ON TABLE trust_configuration IS 'Per-persona trust calculation parameters';
