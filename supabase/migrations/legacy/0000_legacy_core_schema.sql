-- 0000_legacy_core_schema.sql
-- Core schema for Character AI Chat app (LEGACY APPLICATION)
-- This migration creates the foundational tables for the legacy character-based chat system

-- Personas (legacy/health check)
create table if not exists personas (
  id bigserial primary key,
  persona_id text unique not null,
  name text,
  description text,
  system_prompt text,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

-- Enhanced personas (primary persona definitions)
create table if not exists enhanced_personas (
  persona_id text primary key,
  name text not null,
  description text default '',
  system_context text default '',
  core_identity text default '',
  current_situation text default '',
  traits jsonb default '{}'::jsonb,
  trust_behaviors jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

-- Character knowledge tiers
create table if not exists character_knowledge_tiers (
  id uuid primary key default gen_random_uuid(),
  persona_id text references enhanced_personas(persona_id) on delete cascade,
  tier_name text not null,
  trust_threshold numeric not null default 0.0,
  available_knowledge jsonb not null default '{}'::jsonb,
  created_at timestamptz default now()
);
create index if not exists idx_ck_tiers_persona on character_knowledge_tiers(persona_id);
create index if not exists idx_ck_tiers_trust on character_knowledge_tiers(trust_threshold);

-- Conversations (enhanced chat)
create table if not exists conversations (
  id uuid primary key,
  persona_id text not null,
  persona_seed text,
  status text default 'active',
  created_at timestamptz default now()
);
create index if not exists idx_conversations_persona on conversations(persona_id);

-- Conversation transcripts (message log)
create table if not exists conversation_transcripts (
  id bigserial primary key,
  conversation_id uuid not null references conversations(id) on delete cascade,
  role text not null, -- 'user' | 'persona'
  message text not null,
  turn_number int not null,
  timestamp timestamptz default now()
);
create index if not exists idx_transcripts_conv on conversation_transcripts(conversation_id, turn_number);

-- Conversation memories (dynamic mid-run insights)
create table if not exists conversation_memories (
  id bigserial primary key,
  session_id uuid not null,
  key_insights text not null,
  importance_score numeric not null default 0.5,
  created_at timestamptz default now()
);
create index if not exists idx_memories_session on conversation_memories(session_id);
create index if not exists idx_memories_created on conversation_memories(created_at);

-- Conversation summaries (mid-term memory)
create table if not exists conversation_summaries (
  id bigserial primary key,
  session_id uuid not null,
  persona_id text not null,
  summary_id text unique not null,
  start_turn int not null,
  end_turn int not null,
  message_count int not null,
  summary_text text not null,
  key_topics jsonb not null default '[]'::jsonb,
  user_preferences jsonb not null default '[]'::jsonb,
  emotional_moments jsonb not null default '[]'::jsonb,
  trust_progression text not null default 'stable',
  importance_score numeric not null default 0.5,
  created_at timestamptz not null default now()
);
create index if not exists idx_summaries_session on conversation_summaries(session_id);

-- Persona greetings pool
create table if not exists persona_greetings (
  id bigserial primary key,
  greeting_text text not null,
  is_active boolean not null default true,
  created_at timestamptz default now()
);

-- Coach knowledge (system prompts, company values, canned responses)
create table if not exists coach_knowledge (
  id bigserial primary key,
  persona_id text,
  knowledge_type text not null, -- 'system_prompt' | 'company_values' | 'coaching_response'
  content text not null,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);
create index if not exists idx_coach_knowledge_persona on coach_knowledge(persona_id);
create index if not exists idx_coach_knowledge_type on coach_knowledge(knowledge_type);

-- Long-term memories (consolidation target)
create table if not exists long_term_memories (
  id bigserial primary key,
  persona_id text not null,
  session_id uuid,
  memory_type text not null, -- 'episodic' | 'preference' | 'semantic'
  content text not null,
  importance numeric not null default 0.5,
  last_accessed timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  hash text not null unique
);
create index if not exists idx_ltm_persona on long_term_memories(persona_id);
create index if not exists idx_ltm_session on long_term_memories(session_id);
create index if not exists idx_ltm_last_accessed on long_term_memories(last_accessed);

-- Memory audit log
create table if not exists memory_audit_log (
  id bigserial primary key,
  action text not null, -- 'ADD' | 'UPDATE' | 'DELETE'
  persona_id text,
  session_id uuid,
  source text, -- e.g., 'conversation_memories'
  content_hash text,
  details jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_audit_persona on memory_audit_log(persona_id);
create index if not exists idx_audit_session on memory_audit_log(session_id);
create index if not exists idx_audit_created on memory_audit_log(created_at);
