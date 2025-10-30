-- 0008a_update_trust_deltas_faster.sql
-- Update trust deltas to reward consistent empathy and avoid vicious cycles
-- Goal: 5-7 good interactions should reach cautious (0.40 → 0.60)
--       10-12 excellent interactions should reach opening (0.60 → 0.80)

-- ================================================================
-- STRATEGY:
-- - Increase base deltas for good/excellent interactions
-- - Boost multipliers for supportive/collaborative approaches
-- - Add larger bonuses for building trajectory (consistency reward)
-- - Reduce penalties to avoid vicious cycles
-- ================================================================

-- MARY: Needs to feel consistent safety to open up
UPDATE trust_configuration
SET
  quality_deltas = '{
    "poor": -0.02,
    "adequate": 0.01,
    "good": 0.03,
    "excellent": 0.05
  }'::jsonb,
  empathy_multipliers = '{
    "hostile": 0.2,
    "neutral": 1.0,
    "supportive": 1.8,
    "deeply_empathetic": 2.5
  }'::jsonb,
  trajectory_adjustments = '{
    "declining": -0.01,
    "stable": 0.00,
    "building": 0.015,
    "breakthrough": 0.035
  }'::jsonb,
  approach_modifiers = '{
    "directive": 0.6,
    "questioning": 1.0,
    "curious": 1.4,
    "collaborative": 1.8,
    "supportive": 2.0
  }'::jsonb,
  regression_penalty = -0.02  -- Reduced from -0.04 to avoid vicious cycle
WHERE persona_id = 'mary';

-- TERRY: Values directness but responds to respect
UPDATE trust_configuration
SET
  quality_deltas = '{
    "poor": -0.02,
    "adequate": 0.01,
    "good": 0.04,
    "excellent": 0.06
  }'::jsonb,
  empathy_multipliers = '{
    "hostile": 0.3,
    "neutral": 1.0,
    "supportive": 1.6,
    "deeply_empathetic": 2.0
  }'::jsonb,
  trajectory_adjustments = '{
    "declining": -0.01,
    "stable": 0.00,
    "building": 0.02,
    "breakthrough": 0.04
  }'::jsonb,
  approach_modifiers = '{
    "directive": 1.2,
    "questioning": 1.0,
    "curious": 1.3,
    "collaborative": 1.9,
    "supportive": 1.7
  }'::jsonb,
  regression_penalty = -0.02  -- Reduced from -0.025
WHERE persona_id = 'terry';

-- JAN: Fastest to open but most fragile (unchanged fragility, faster opening)
UPDATE trust_configuration
SET
  quality_deltas = '{
    "poor": -0.03,
    "adequate": 0.01,
    "good": 0.04,
    "excellent": 0.07
  }'::jsonb,
  empathy_multipliers = '{
    "hostile": 0.2,
    "neutral": 1.0,
    "supportive": 2.0,
    "deeply_empathetic": 2.8
  }'::jsonb,
  trajectory_adjustments = '{
    "declining": -0.02,
    "stable": 0.00,
    "building": 0.02,
    "breakthrough": 0.05
  }'::jsonb,
  approach_modifiers = '{
    "directive": 0.5,
    "questioning": 1.0,
    "curious": 1.5,
    "collaborative": 2.0,
    "supportive": 2.2
  }'::jsonb,
  regression_penalty = -0.03  -- Reduced from -0.05 (still fragile but not trap)
WHERE persona_id = 'jan';

-- ================================================================
-- NEW TRUST PROGRESSION EXAMPLES
-- ================================================================

-- TERRY: Excellent + Supportive + Collaborative + Building
-- Base: 0.06 (excellent)
-- Trajectory: +0.02 (building) = 0.08
-- Empathy: ×1.6 (supportive) = 0.128
-- Approach: ×1.9 (collaborative) = 0.243 (~0.24 per turn!)
-- Result: 5 turns = 1.2 trust gain (defensive 0.30 → trusting 1.50) - TOO FAST, will cap at tier boundaries

-- More realistic: Good + Supportive + Collaborative + Building
-- Base: 0.04 (good)
-- Trajectory: +0.02 (building) = 0.06
-- Empathy: ×1.6 (supportive) = 0.096
-- Approach: ×1.9 (collaborative) = 0.182 (~0.18 per turn)
-- Result: 5 turns ≈ 0.90 gain (should be capped at tier transitions)

-- MARY: Excellent + Supportive + Collaborative + Building
-- Base: 0.05 (excellent)
-- Trajectory: +0.015 (building) = 0.065
-- Empathy: ×1.8 (supportive) = 0.117
-- Approach: ×1.8 (collaborative) = 0.211 (~0.21 per turn)
-- Result: 5 turns ≈ 1.05 gain (excellent progression)

-- ================================================================
-- RECOMMENDED TIER CAPS (to implement in code)
-- ================================================================
-- Defensive → Cautious: Cap at +0.10 per turn (reach in 3-4 excellent turns)
-- Cautious → Opening: Cap at +0.08 per turn (reach in 3-4 excellent turns)
-- Opening → Trusting: Cap at +0.06 per turn (final barrier, needs consistency)
--
-- This prevents unrealistic jumps while still rewarding excellent MI practice
-- Total: 10-12 excellent turns to reach trusting (realistic for training)

-- Verify updates
SELECT
  persona_id,
  quality_deltas->>'excellent' as excellent_delta,
  empathy_multipliers->>'supportive' as supportive_mult,
  approach_modifiers->>'collaborative' as collab_mult,
  trajectory_adjustments->>'building' as building_adj
FROM trust_configuration
ORDER BY persona_id;
