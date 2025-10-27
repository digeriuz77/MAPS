-- 0002_rls_policies_dev.sql
-- Enable RLS and permissive dev policies (adjust for production later)

-- Enable RLS
alter table personas enable row level security;
alter table enhanced_personas enable row level security;
alter table character_knowledge_tiers enable row level security;
alter table conversations enable row level security;
alter table conversation_transcripts enable row level security;
alter table conversation_memories enable row level security;
alter table conversation_summaries enable row level security;
alter table persona_greetings enable row level security;
alter table coach_knowledge enable row level security;
alter table long_term_memories enable row level security;
alter table memory_audit_log enable row level security;

-- DEV-ONLY: allow all operations for anon
-- Replace with auth-based policies before production
create policy dev_all_personas on personas for all using (true) with check (true);
create policy dev_all_enhanced_personas on enhanced_personas for all using (true) with check (true);
create policy dev_all_ck_tiers on character_knowledge_tiers for all using (true) with check (true);
create policy dev_all_conversations on conversations for all using (true) with check (true);
create policy dev_all_transcripts on conversation_transcripts for all using (true) with check (true);
create policy dev_all_memories on conversation_memories for all using (true) with check (true);
create policy dev_all_summaries on conversation_summaries for all using (true) with check (true);
create policy dev_all_greetings on persona_greetings for all using (true) with check (true);
create policy dev_all_coach_knowledge on coach_knowledge for all using (true) with check (true);
create policy dev_all_ltm on long_term_memories for all using (true) with check (true);
create policy dev_all_audit on memory_audit_log for all using (true) with check (true);
