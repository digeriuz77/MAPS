-- 0003_seed_minimum.sql
-- Seed minimal data for development and smoke tests

-- Enhanced personas
insert into enhanced_personas (persona_id, name, description)
values
  ('mary', 'Mary', 'Stressed single parent juggling work and childcare'),
  ('alex', 'Alex', 'Junior developer with impostor syndrome'),
  ('jordan', 'Jordan', 'Healthcare worker experiencing burnout')
on conflict (persona_id) do nothing;

-- Character tiers (Mary)
insert into character_knowledge_tiers (persona_id, tier_name, trust_threshold, available_knowledge)
values
  ('mary','defensive',0.00,'{}'::jsonb),
  ('mary','cautious',0.40,'{}'::jsonb),
  ('mary','opening',0.60,'{}'::jsonb),
  ('mary','trusting',0.80,'{}'::jsonb)
on conflict do nothing;

-- Greetings
insert into persona_greetings (greeting_text, is_active) values
  ('Hi there! It''s good to connect today. How are things going?', true),
  ('Thanks for reaching out. What''s been on your mind?', true)
on conflict do nothing;

-- Legacy health persona for /health
insert into personas (persona_id, name)
values ('legacy_health_persona', 'Legacy Health Check')
on conflict (persona_id) do nothing;
