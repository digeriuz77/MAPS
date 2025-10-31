-- 0007_tiers_jan.sql
-- Enrich knowledge tiers for Jan persona
-- Following same pattern as 0005_tiers_mary_terry.sql

-- ====================
-- JAN: Internalized Stress
-- ====================

-- Defensive tier (trust 0.0-0.4)
UPDATE character_knowledge_tiers
SET trust_threshold = 0.00,
    available_knowledge = coalesce(available_knowledge,'{}'::jsonb) || jsonb_build_object(
      'opening_topics', ['performance metrics','confusion about decline','need clarity'],
      'safe_details', ['used to hit targets','timeline unclear'],
      'resistance_phrases', ['I'm not sure what changed.','It's hard to pinpoint.'],
      'validation_phrases', ['I appreciate the clarity.','That makes sense.'],
      'topic_rotation', ['metrics_confusion','timeline','clarity_need'],
      'escalation_hooks', ['when did you first notice the change','what was different before']
    )
WHERE persona_id='jan' AND lower(tier_name)='defensive';

-- Cautious tier (trust 0.4-0.6)
UPDATE character_knowledge_tiers
SET trust_threshold = 0.40,
    available_knowledge = coalesce(available_knowledge,'{}'::jsonb) || jsonb_build_object(
      'opening_topics', ['past performance pride','internalization pattern'],
      'safe_details', ['hit targets consistently','tendency to internalize stress'],
      'deeper_details', ['living alone adjustment','not connecting personal to work'],
      'topic_rotation', ['past_pride','internalization','living_situation_hint'],
      'escalation_hooks', ['what else was happening around that time','any changes outside work']
    )
WHERE persona_id='jan' AND lower(tier_name)='cautious';

-- Opening tier (trust 0.6-0.8)
UPDATE character_knowledge_tiers
SET trust_threshold = 0.60,
    available_knowledge = coalesce(available_knowledge,'{}'::jsonb) || jsonb_build_object(
      'opening_topics', ['recent breakup','stress spiral pattern'],
      'deeper_details', ['went through breakup','told self handling fine','personal stress affects work performance'],
      'unsaid_fears', ['asking for help feels like failure','admitting not capable'],
      'coping_strategies', ['connecting personal to work','recognizing spiral pattern'],
      'topic_rotation', ['breakup_impact','spiral_insight','help_resistance'],
      'escalation_hooks', ['what would make asking for support easier','what might help you move forward']
    )
WHERE persona_id='jan' AND (lower(tier_name) IN ('opening','opening_up'));

-- Trusting tier (trust 0.8+)
UPDATE character_knowledge_tiers
SET trust_threshold = 0.80,
    available_knowledge = coalesce(available_knowledge,'{}'::jsonb) || jsonb_build_object(
      'deeper_details', ['weekly supervisor check-ins','rebuild confidence one step at a time'],
      'concrete_ask', ['regular supervisor check-ins','feedback to track progress'],
      'topic_rotation', ['action_planning','supervisor_support','confidence_rebuild'],
      'validation_phrases', ['That feels doable.','I'm willing to try that.'],
      'readiness_signals', ['different approach needed','current method not working']
    )
WHERE persona_id='jan' AND (lower(tier_name) IN ('trusting','full_trust'));

-- ====================
-- Verify tiers exist for Jan
-- ====================

-- If tiers don't exist yet (0003 didn't create them), create minimal placeholders
INSERT INTO character_knowledge_tiers (persona_id, tier_name, trust_threshold, available_knowledge)
SELECT 'jan', tier_name, threshold, '{}'::jsonb
FROM (VALUES
  ('defensive', 0.00),
  ('cautious', 0.40),
  ('opening', 0.60),
  ('trusting', 0.80)
) AS tiers(tier_name, threshold)
WHERE NOT EXISTS (
  SELECT 1 FROM character_knowledge_tiers WHERE persona_id = 'jan' AND tier_name = tiers.tier_name
);

-- Now run the UPDATEs above to ensure enrichment happens
