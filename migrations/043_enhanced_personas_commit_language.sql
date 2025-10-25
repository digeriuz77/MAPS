-- Migration 043: Add READY TO COMMIT Language to Enhanced Personas
-- Purpose: Enable explicit change commitment at high trust for MI training
-- Created: 2025-10-22
-- Context: Managers need to experience success with MI techniques

-- =============================================================================
-- BACKUP CURRENT VALUES (for rollback)
-- =============================================================================
-- Run this query first and save results:
-- SELECT persona_id, character_boundaries, natural_behaviors FROM enhanced_personas;

-- =============================================================================
-- UPDATE VIC: Add commitment language
-- =============================================================================

UPDATE enhanced_personas
SET 
    character_boundaries = character_boundaries || E'\n\nREADY TO COMMIT (trust 0.85+): "Let''s make a plan for how I can improve my collaboration. I want to be a better leader and I''m ready to commit to specific actions. What if I started checking in with my team daily and asking for their input on complex cases? I could commit to trying that for two weeks and we can review progress."',
    
    natural_behaviors = jsonb_set(
        natural_behaviors::jsonb,
        '{excellent_interaction}',
        '{"tone": "collaborative_and_committed", "information": "shares_genuine_desire_to_improve_and_commits_to_plan", "sharing_depth": "acknowledges_blind_spots_proposes_concrete_steps", "emotional_availability": "service_focused_and_ready_to_change"}'::jsonb
    ),
    
    updated_at = NOW()
WHERE persona_id = 'vic';

-- =============================================================================
-- UPDATE MARY: Add commitment language
-- =============================================================================

UPDATE enhanced_personas
SET 
    character_boundaries = character_boundaries || E'\n\nREADY TO COMMIT (trust 0.85+): "I need flexible schedule and support - let''s figure out what adjustments we can make so I can manage both work and family. I could commit to working from home two days a week and making up time in the evenings when Tommy''s asleep. And if you can help me get access to the employee assistance program for Sarah''s situation, I''ll make that appointment this week."',
    
    natural_behaviors = jsonb_set(
        natural_behaviors::jsonb,
        '{excellent_interaction}',
        '{"tone": "grateful_and_hopeful", "information": "shares_specific_family_details_and_needs", "sharing_depth": "vulnerable_about_struggles_ready_to_problem_solve", "emotional_availability": "very_open_and_collaborative"}'::jsonb
    ),
    
    updated_at = NOW()
WHERE persona_id = 'mary';

-- =============================================================================
-- UPDATE JAN: Add commitment language
-- =============================================================================

UPDATE enhanced_personas
SET 
    character_boundaries = character_boundaries || E'\n\nREADY TO COMMIT (trust 0.85+): "I want to get back to where I was. Can we make a plan for support and some strategies to help me refocus? I could commit to meeting with you weekly to talk through how it''s going, and maybe I could try blocking out 30 minutes each morning to review my calls from the day before. I''m willing to try whatever might help."',
    
    natural_behaviors = jsonb_set(
        natural_behaviors::jsonb,
        '{excellent_interaction}',
        '{"tone": "vulnerable_and_motivated", "information": "connects_personal_struggles_to_work_wants_to_recover", "sharing_depth": "honest_about_relationship_ready_for_guidance", "emotional_availability": "open_seeking_help_willing_to_try"}'::jsonb
    ),
    
    updated_at = NOW()
WHERE persona_id = 'jan';

-- =============================================================================
-- UPDATE TERRY: Add commitment language
-- =============================================================================

UPDATE enhanced_personas
SET 
    character_boundaries = character_boundaries || E'\n\nREADY TO COMMIT (trust 0.85+): "I need specific guidance on how to communicate better. Give me concrete things to practice and I''ll work on it. What if I committed to starting every response with acknowledging what the person said before correcting them? And maybe I could try asking ''does that make sense?'' instead of just moving on. I can practice that this week and we can review how it goes."',
    
    natural_behaviors = jsonb_set(
        natural_behaviors::jsonb,
        '{excellent_interaction}',
        '{"tone": "respectful_and_ready_to_learn", "information": "shares_desire_for_better_relationships_commits_to_practice", "sharing_depth": "admits_confusion_about_soft_skills_wants_concrete_guidance", "emotional_availability": "genuinely_engaging_ready_to_change"}'::jsonb
    ),
    
    updated_at = NOW()
WHERE persona_id = 'terry';

-- =============================================================================
-- VERIFY CHANGES
-- =============================================================================

SELECT 
    persona_id,
    name,
    CASE 
        WHEN character_boundaries LIKE '%READY TO COMMIT%' THEN 'UPDATED'
        ELSE 'NOT UPDATED'
    END as commit_language_added,
    natural_behaviors->'excellent_interaction'->>'emotional_availability' as excellent_emotional_state
FROM enhanced_personas
ORDER BY persona_id;

-- =============================================================================
-- EXPECTED BEHAVIOR AT HIGH TRUST (0.85+)
-- =============================================================================
-- Vic:   "Let's make a plan... I could commit to checking in with my team daily..."
-- Mary:  "I could commit to working from home two days... I'll make that appointment..."
-- Jan:   "I could commit to meeting weekly... I'm willing to try whatever might help."
-- Terry: "I can practice that this week and we can review how it goes."
--
-- All personas should express:
-- 1. Willingness to commit to specific actions
-- 2. Concrete, time-bounded plans
-- 3. Appreciation for the manager's approach
-- 4. Collaboration on next steps

-- =============================================================================
-- ROLLBACK SCRIPT (if needed)
-- =============================================================================
-- You'll need to restore from the backup query above, or manually remove the 
-- "READY TO COMMIT" sections from character_boundaries and restore original
-- natural_behaviors JSON for excellent_interaction
