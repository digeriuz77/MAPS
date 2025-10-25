-- Migration 041: Update Enhanced Personas with Minimal Core Identities
-- Purpose: Replace heavy core_identity with minimal versions for proper micro-context
-- Created: 2025-10-20
-- Enables progressive knowledge revelation through tiers instead of upfront spoilers

-- =============================================================================
-- UPDATE: Jan - Minimal confused employee identity
-- =============================================================================

UPDATE enhanced_personas 
SET core_identity = 'You are Jan, 28, a customer service representative at Money and Pensions Service. Your performance has dropped recently, and you''re confused about why.'
WHERE persona_id = 'jan';

-- =============================================================================
-- UPDATE: Mary - Minimal struggling employee identity  
-- =============================================================================

UPDATE enhanced_personas 
SET core_identity = 'You are Mary, 34, a Customer Service Representative at Money and Pensions Service. You were Rep of the Year in 2022, but your performance has slipped recently due to personal pressures.'
WHERE persona_id = 'mary';

-- =============================================================================
-- UPDATE: Terry - Minimal direct communicator identity
-- =============================================================================

UPDATE enhanced_personas 
SET core_identity = 'You are Terry, 42, a Senior Customer Service Representative with 15 years of experience at Money and Pensions Service. You''re the pension regulations expert, but colleagues find your communication style too direct.'
WHERE persona_id = 'terry';

-- =============================================================================
-- UPDATE: Vic - Minimal confident performer identity
-- =============================================================================

UPDATE enhanced_personas 
SET core_identity = 'You are Vic, 35, a customer service representative with 5 years of experience at Money and Pensions Service. You consistently meet targets and believe you''re one of the strongest performers, but received feedback about collaboration skills.'
WHERE persona_id = 'vic';

-- =============================================================================
-- Verification: Check updated core identities
-- =============================================================================

SELECT 
    persona_id,
    name,
    LENGTH(core_identity) as identity_length,
    LEFT(core_identity, 100) as identity_preview
FROM enhanced_personas
ORDER BY persona_id;

-- Expected results:
-- jan: ~95 chars (was ~500+)
-- mary: ~155 chars (was ~300+) 
-- terry: ~175 chars (was ~400+)
-- vic: ~190 chars (was ~600+)