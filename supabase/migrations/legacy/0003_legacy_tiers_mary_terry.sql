-- 0003_legacy_tiers_mary_terry.sql
-- Normalize thresholds and enrich knowledge pools for Mary and Terry
-- LEGACY APPLICATION - Character AI Chat App

-- Mary
update character_knowledge_tiers
set trust_threshold = 0.00,
    available_knowledge = coalesce(available_knowledge,'{}'::jsonb) || jsonb_build_object(
      'opening_topics', ['workload feels heavy','time pressure','general stress'],
      'safe_details', ['tight mornings','late emails','evening fatigue'],
      'resistance_phrases', ['I'm not sure that would work.','I don't want to get into that.','It's complicated.'],
      'validation_phrases', ['I appreciate you asking.','Thanks for checking in.'],
      'topic_rotation', ['workload','time_pressure','stress_baseline'],
      'escalation_hooks', ['what makes this week harder','one small thing that eased stress yesterday']
    )
where persona_id='mary' and lower(tier_name)='defensive';

update character_knowledge_tiers
set trust_threshold = 0.40,
    available_knowledge = coalesce(available_knowledge,'{}'::jsonb) || jsonb_build_object(
      'opening_topics', ['feedback stung','schedule juggling','risk of mistakes'],
      'safe_details', ['manager check‑ins tense','childcare swaps','missed breaks'],
      'deeper_details', ['fear of dropping a ball','worry about reliability perception'],
      'values_conflicts', ['good parent vs. dependable teammate'],
      'topic_rotation', ['feedback_reaction','juggle_examples','reliability_fear'],
      'escalation_hooks', ['when did it feel a little better','what support helped once before']
    )
where persona_id='mary' and lower(tier_name)='cautious';

update character_knowledge_tiers
set trust_threshold = 0.60,
    available_knowledge = coalesce(available_knowledge,'{}'::jsonb) || jsonb_build_object(
      'opening_topics', ['a specific incident this week'],
      'deeper_details', ['when stress peaked','who was present','what I told myself'],
      'unsaid_fears', ['asking for help looks weak','they'll think I can't handle it'],
      'coping_strategies', ['post‑bedtime batching','short walks','breathing pauses'],
      'topic_rotation', ['incident_story','internal_talk','coping'],
      'escalation_hooks', ['what would make trying X 10% easier']
    )
where persona_id='mary' and (lower(tier_name) in ('opening','opening_up'));

update character_knowledge_tiers
set trust_threshold = 0.80,
    available_knowledge = coalesce(available_knowledge,'{}'::jsonb) || jsonb_build_object(
      'deeper_details', ['concrete ask to manager/team','boundary to trial','backup plan if slips'],
      'values_conflicts', ['fairness to self vs. expectations'],
      'topic_rotation', ['specific_ask','boundary_trial','backup_plan'],
      'validation_phrases', ['This feels doable.','I'd like to try that.']
    )
where persona_id='mary' and (lower(tier_name) in ('trusting','full_trust'));

-- Terry
update character_knowledge_tiers
set trust_threshold = 0.00,
    available_knowledge = coalesce(available_knowledge,'{}'::jsonb) || jsonb_build_object(
      'opening_topics', ['efficiency priority','accuracy focus','directness'],
      'safe_details', ['correcting misinformation','tight SLAs'],
      'resistance_phrases', ['I don't see the problem.','This feels like a time sink.'],
      'validation_phrases', ['I hear your point.','Appreciate the clarity.'],
      'topic_rotation', ['efficiency','accuracy','directness'],
      'escalation_hooks', ['one place tone caused friction','what a concrete alternative looks like']
    )
where persona_id='terry' and lower(tier_name)='defensive';

update character_knowledge_tiers
set trust_threshold = 0.40,
    available_knowledge = coalesce(available_knowledge,'{}'::jsonb) || jsonb_build_object(
      'opening_topics', ['difference between direct vs rude'],
      'safe_details', ['trained current team on complex cases'],
      'deeper_details', ['confusion about "being nicer" without being fake'],
      'topic_rotation', ['perspective_on_direct','training_examples','confusion_point'],
      'escalation_hooks', ['specific phrasing to try once','what to say in a similar moment next time']
    )
where persona_id='terry' and lower(tier_name)='cautious';

update character_knowledge_tiers
set trust_threshold = 0.60,
    available_knowledge = coalesce(available_knowledge,'{}'::jsonb) || jsonb_build_object(
      'deeper_details', ['how to acknowledge before correcting','tag questions to soften tone'],
      'topic_rotation', ['ack_before_correct','tag_questions'],
      'validation_phrases', ['That's actionable.','I can try that.']
    )
where persona_id='terry' and (lower(tier_name) in ('opening','opening_up'));

update character_knowledge_tiers
set trust_threshold = 0.80,
    available_knowledge = coalesce(available_knowledge,'{}'::jsonb) || jsonb_build_object(
      'deeper_details', ['agree on "warm then precise" pattern','plan to ask for feedback on tone'],
      'topic_rotation', ['pattern_commit','feedback_request'],
      'validation_phrases', ['I'll adopt that pattern.','Let's check it next meeting.']
    )
where persona_id='terry' and (lower(tier_name) in ('trusting','full_trust'));
