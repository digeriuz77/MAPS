-- 0010_memory_importance_config.sql
-- Add memory importance configuration to trust_configuration table
-- Enables per-persona memory importance tuning

-- Add memory_importance_config column
ALTER TABLE trust_configuration 
ADD COLUMN IF NOT EXISTS memory_importance_config JSONB NOT NULL DEFAULT '{
  "base_importance": 6.0,
  "quality_boosts": {
    "excellent": 2.0,
    "good": 1.0,
    "adequate": 0.0,
    "poor": 1.5
  },
  "trajectory_boosts": {
    "breakthrough": 1.5,
    "building": 0.5,
    "stable": 0.0,
    "declining": 1.0
  },
  "safety_boost": 1.0,
  "max_importance": 10.0
}'::jsonb;

-- Update Mary's config (stressed parent - high importance on breakthroughs)
UPDATE trust_configuration
SET memory_importance_config = '{
  "base_importance": 6.0,
  "quality_boosts": {
    "excellent": 2.5,
    "good": 1.2,
    "adequate": 0.0,
    "poor": 2.0
  },
  "trajectory_boosts": {
    "breakthrough": 2.0,
    "building": 0.8,
    "stable": 0.0,
    "declining": 1.5
  },
  "safety_boost": 1.5,
  "max_importance": 10.0
}'::jsonb
WHERE persona_id = 'mary';

-- Update Terry's config (direct communicator - values efficiency breakthroughs)
UPDATE trust_configuration
SET memory_importance_config = '{
  "base_importance": 6.0,
  "quality_boosts": {
    "excellent": 2.0,
    "good": 1.5,
    "adequate": 0.5,
    "poor": 1.0
  },
  "trajectory_boosts": {
    "breakthrough": 1.8,
    "building": 1.0,
    "stable": 0.0,
    "declining": 0.8
  },
  "safety_boost": 0.5,
  "max_importance": 10.0
}'::jsonb
WHERE persona_id = 'terry';

-- Update Jan's config (internalized stress - high importance on all emotional moments)
UPDATE trust_configuration
SET memory_importance_config = '{
  "base_importance": 6.5,
  "quality_boosts": {
    "excellent": 2.5,
    "good": 1.5,
    "adequate": 0.5,
    "poor": 2.5
  },
  "trajectory_boosts": {
    "breakthrough": 2.5,
    "building": 1.2,
    "stable": 0.0,
    "declining": 2.0
  },
  "safety_boost": 2.0,
  "max_importance": 10.0
}'::jsonb
WHERE persona_id = 'jan';

-- Add comment
COMMENT ON COLUMN trust_configuration.memory_importance_config IS 'Memory importance calculation config per persona. Controls how significant different interaction types are for memory formation.';
