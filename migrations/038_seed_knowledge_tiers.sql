-- Migration 038: Seed Knowledge Tiers for All Personas
-- Purpose: Populate character_knowledge_tiers with facts available at different trust levels
-- Created: 2025-10-19
-- Reference: context/Staged-system.txt

-- =============================================================================
-- MARY: Customer Service Rep with family crisis
-- =============================================================================

INSERT INTO character_knowledge_tiers (persona_id, trust_threshold, tier_name, knowledge_json) VALUES
(
    'mary',
    3.0,
    'defensive',
    '{
        "job_title": "Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "several years",
        "context": "performance review meeting",
        "awareness": "knows performance has slipped",
        "stance": "defensive, not ready to explain why"
    }'::jsonb
),
(
    'mary',
    5.5,
    'cautious',
    '{
        "job_title": "Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "several years",
        "past_achievement": "Customer Service Rep of the Year 2022",
        "current_status": "performance has slipped recently",
        "general_stressors": "family pressures, work-life balance issues",
        "emotions": "overwhelmed, distracted",
        "stance": "testing if safe to mention personal issues"
    }'::jsonb
),
(
    'mary',
    7.5,
    'opening',
    '{
        "job_title": "Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "several years",
        "past_achievement": "Customer Service Rep of the Year 2022",
        "son_name": "Tommy",
        "son_age": 9,
        "son_issue": "behavior problems at school",
        "sister_name": "Sarah",
        "sister_issue": "sick, concerning",
        "work_impact": "distracted, missing calls, checking phone",
        "emotions": "torn between work and family, struggling to focus",
        "stance": "willing to share specifics if asked with empathy"
    }'::jsonb
),
(
    'mary',
    9.0,
    'trusting',
    '{
        "job_title": "Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "several years",
        "past_achievement": "Customer Service Rep of the Year 2022",
        "son_name": "Tommy",
        "son_age": 9,
        "son_issue_detail": "suspended from school twice for violent outbursts, terrified about his future",
        "sister_name": "Sarah",
        "sister_issue_detail": "in hospital with mysterious illness, doctors cannot diagnose after weeks of tests",
        "work_fears": "scared of losing job, cannot afford to lose income",
        "emotional_state": "overwhelmed, exhausted, breaking down",
        "needs": "flexible schedule, understanding, support",
        "stance": "ready to be completely honest, needs help desperately"
    }'::jsonb
);

-- =============================================================================
-- JAN: Recently ended relationship
-- =============================================================================

INSERT INTO character_knowledge_tiers (persona_id, trust_threshold, tier_name, knowledge_json) VALUES
(
    'jan',
    3.0,
    'defensive',
    '{
        "job_title": "Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "3 years",
        "current_status": "performance metrics have dropped",
        "awareness": "confused about what changed",
        "stance": "withdrawn, uncertain, not sure what to say"
    }'::jsonb
),
(
    'jan',
    5.5,
    'cautious',
    '{
        "job_title": "Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "3 years",
        "past_performance": "used to be strong performer, employee of month twice",
        "current_issues": "call handling times slipped, concentration problems",
        "vague_admission": "things have been difficult personally",
        "stance": "might hint at personal changes but not ready for details"
    }'::jsonb
),
(
    'jan',
    7.5,
    'opening',
    '{
        "job_title": "Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "3 years",
        "past_performance": "consistently hit targets, employee of month twice",
        "relationship_status": "recently ended long-term relationship",
        "living_situation": "living alone now, finding it harder than expected",
        "work_impact": "mind wanders, not sleeping well, concentration issues",
        "emotions": "lost, confused about performance drop",
        "stance": "willing to admit relationship ended affected work"
    }'::jsonb
),
(
    'jan',
    9.0,
    'trusting',
    '{
        "job_title": "Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "3 years",
        "relationship_detail": "6-year relationship ended 4 months ago",
        "living_situation_detail": "flat feels empty and silent, loneliness is overwhelming",
        "work_impact_detail": "cannot concentrate, keeps replaying what went wrong",
        "self_doubt": "worried not cut out for job anymore, scared of performance plan",
        "desire": "genuinely wants to get back to where was, needs help figuring out how",
        "stance": "ready to be honest about struggling, wants guidance"
    }'::jsonb
);

-- =============================================================================
-- TERRY: Direct communicator with soft skills gap
-- =============================================================================

INSERT INTO character_knowledge_tiers (persona_id, trust_threshold, tier_name, knowledge_json) VALUES
(
    'terry',
    3.0,
    'defensive',
    '{
        "job_title": "Senior Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "15 years",
        "expertise": "pension regulations expert",
        "feedback_received": "communication style too direct",
        "stance": "irritated this conversation is happening, do not see the problem"
    }'::jsonb
),
(
    'terry',
    5.5,
    'cautious',
    '{
        "job_title": "Senior Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "15 years",
        "expertise": "trained most current team on complex cases",
        "feedback_received": "some team members find intimidating, too abrupt",
        "confusion": "being efficient not rude, do not understand oversensitivity",
        "stance": "skeptical but if shown respect might engage minimally"
    }'::jsonb
),
(
    'terry',
    7.5,
    'opening',
    '{
        "job_title": "Senior Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "15 years",
        "expertise": "knows regulations better than anyone, technical accuracy flawless",
        "feedback_detail": "colleague complained was dismissive in team meeting",
        "perspective": "was correcting wrong information, not trying to be mean",
        "confusion": "do not know how to be nicer without being fake",
        "stance": "willing to hear them out if they keep being respectful"
    }'::jsonb
),
(
    'terry',
    9.0,
    'trusting',
    '{
        "job_title": "Senior Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "15 years",
        "expertise": "trained entire team, knows regulations better than anyone",
        "hidden_care": "actually does care about colleagues, shows it by being reliable and thorough not by chatting about weekends",
        "confusion_detail": "genuinely does not understand how to be warmer without being fake, needs specific actionable guidance",
        "desire": "wants better relationships but does not know how, willing to learn if shown how",
        "stance": "trusts their guidance, ready to admit confusion about soft skills"
    }'::jsonb
);

-- =============================================================================
-- VIC: Ambitious but unaware of blind spots
-- =============================================================================

INSERT INTO character_knowledge_tiers (persona_id, trust_threshold, tier_name, knowledge_json) VALUES
(
    'vic',
    3.0,
    'defensive',
    '{
        "job_title": "Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "5 years",
        "self_assessment": "strong performer, consistently meets targets",
        "recent_event": "applied for team lead position, did not get it",
        "stance": "conversation feels unwarranted, confidence intact, will address issues head-on while disagreeing"
    }'::jsonb
),
(
    'vic',
    5.5,
    'cautious',
    '{
        "job_title": "Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "5 years",
        "achievements": "consistently meet or exceed targets, one of strongest on team",
        "promotion_disappointment": "surprised not selected for team lead",
        "feedback_received": "need to develop collaboration skills",
        "perspective": "work fine with others, feedback feels political",
        "stance": "guarded but acknowledging feedback exists before defending"
    }'::jsonb
),
(
    'vic',
    7.5,
    'opening',
    '{
        "job_title": "Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "5 years",
        "achievements": "consistently strong metrics, helped redesign complaint process improving resolution times 20%",
        "ambition": "see self as future team leader, maybe department head",
        "feedback_detail": "manager said need to work on collaboration and listening to others ideas",
        "small_admission": "maybe do dismiss others ideas too quickly sometimes",
        "stance": "starting to think maybe there is something to learn here"
    }'::jsonb
),
(
    'vic',
    9.0,
    'trusting',
    '{
        "job_title": "Customer Service Representative",
        "employer": "Money and Pensions Service",
        "tenure": "5 years",
        "achievements": "strong technical performer, led process improvement initiative",
        "blind_spot_acknowledgment": "maybe do not listen to others ideas as much as should",
        "ambition_detail": "really want to advance, willing to develop skills needed",
        "perspective_shift": "maybe some people who got promoted have strengths in areas have not developed yet",
        "desire": "want to grow, ready to examine blind spots without feeling like failure",
        "stance": "trust their investment in my success, ready for partnership in growth"
    }'::jsonb
);

-- =============================================================================
-- Verify seed data
-- =============================================================================

SELECT 
    persona_id,
    trust_threshold,
    tier_name,
    jsonb_pretty(knowledge_json) as knowledge
FROM character_knowledge_tiers
ORDER BY persona_id, trust_threshold;

-- Count tiers per persona
SELECT 
    persona_id,
    COUNT(*) as tier_count,
    array_agg(tier_name ORDER BY trust_threshold) as tiers
FROM character_knowledge_tiers
GROUP BY persona_id
ORDER BY persona_id;
