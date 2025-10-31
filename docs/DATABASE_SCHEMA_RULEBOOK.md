# Database Schema Rulebook
**Last Updated**: October 29, 2025

## Purpose
This document defines the CANONICAL database schema for the Character AI Chat system. It prevents duplicate tables and maintains lean architecture.

---

## Existing Tables (from migrations 0000-0005)

### Core Persona System

#### `enhanced_personas` (PRIMARY persona table)
**Purpose**: Main persona definitions with traits and voice fingerprints
**Columns**:
- `persona_id` TEXT PRIMARY KEY
- `name` TEXT NOT NULL
- `description` TEXT
- `system_context` TEXT (voice patterns, boundaries)
- `core_identity` TEXT
- `current_situation` TEXT
- `traits` JSONB (defensiveness_level, tone_intensity, speech_patterns)
- `trust_behaviors` JSONB (share_budget, rotation, directive_user_effects)
- `created_at` TIMESTAMPTZ

**DO NOT CREATE**: Alternative persona tables, character_profiles, persona_configs

---

#### `personas` (LEGACY - health check only)
**Purpose**: Legacy table for backward compatibility
**Status**: Keep for `/health` endpoint, do not use for new features
**Columns**: id, persona_id, name, description, system_prompt, metadata

---

### Memory System (3-tier architecture)

#### `long_term_memories` (CANONICAL long-term storage)
**Purpose**: Consolidated, high-value memories across all sessions
**Columns**:
- `id` BIGSERIAL PRIMARY KEY
- `persona_id` TEXT NOT NULL
- `session_id` UUID (nullable - universal memories use NULL)
- `memory_type` TEXT ('episodic', 'preference', 'semantic')
- `content` TEXT NOT NULL
- `importance` NUMERIC (0.0-1.0 scale)
- `last_accessed` TIMESTAMPTZ
- `created_at` TIMESTAMPTZ
- `updated_at` TIMESTAMPTZ
- `hash` TEXT UNIQUE (for deduplication)

**Indexes**: persona_id, session_id, last_accessed
**USE FOR**: Persona background stories, consolidated memories, character knowledge
**DO NOT CREATE**: persona_memories, background_memories, character_memories

---

#### `conversation_memories` (CANONICAL short-term storage)
**Purpose**: Dynamic, in-conversation insights
**Columns**:
- `id` BIGSERIAL PRIMARY KEY
- `session_id` UUID NOT NULL
- `key_insights` TEXT NOT NULL
- `importance_score` NUMERIC (0.0-1.0)
- `created_at` TIMESTAMPTZ

**Indexes**: session_id, created_at
**USE FOR**: Turn-by-turn conversation dynamics, relationship state
**DO NOT CREATE**: session_memories, dynamic_memories, interaction_memories

---

#### `conversation_summaries` (CANONICAL mid-term storage)
**Purpose**: Summarized conversation segments
**Columns**:
- `id` BIGSERIAL PRIMARY KEY
- `session_id` UUID NOT NULL
- `persona_id` TEXT NOT NULL
- `summary_id` TEXT UNIQUE
- `start_turn` INT
- `end_turn` INT
- `message_count` INT
- `summary_text` TEXT
- `key_topics` JSONB
- `user_preferences` JSONB
- `emotional_moments` JSONB
- `trust_progression` TEXT
- `importance_score` NUMERIC
- `created_at` TIMESTAMPTZ

**Indexes**: session_id
**USE FOR**: Memory consolidation, context window optimization
**DO NOT CREATE**: memory_summaries, session_summaries

---

### Knowledge Tier System

#### `character_knowledge_tiers` (CANONICAL trust-gated knowledge)
**Purpose**: Progressive revelation based on trust level
**Columns**:
- `id` UUID PRIMARY KEY
- `persona_id` TEXT REFERENCES enhanced_personas(persona_id)
- `tier_name` TEXT ('defensive', 'cautious', 'opening', 'trusting')
- `trust_threshold` NUMERIC (0.0, 0.4, 0.6, 0.8)
- `available_knowledge` JSONB (opening_topics, safe_details, deeper_details, etc.)
- `created_at` TIMESTAMPTZ

**Indexes**: persona_id, trust_threshold
**USE FOR**: Trust-based progressive revelation, topic rotation
**DO NOT CREATE**: knowledge_gates, trust_tiers, persona_knowledge

---

### Conversation System

#### `conversations` (CANONICAL conversation tracking)
**Purpose**: Track active conversations
**Columns**:
- `id` UUID PRIMARY KEY
- `persona_id` TEXT NOT NULL
- `persona_seed` TEXT
- `status` TEXT ('active', 'archived')
- `created_at` TIMESTAMPTZ

**Indexes**: persona_id

---

#### `conversation_transcripts` (CANONICAL message log)
**Purpose**: Full message history
**Columns**:
- `id` BIGSERIAL PRIMARY KEY
- `conversation_id` UUID REFERENCES conversations(id)
- `role` TEXT ('user', 'persona')
- `message` TEXT
- `turn_number` INT
- `timestamp` TIMESTAMPTZ

**Indexes**: conversation_id + turn_number

---

### Supporting Tables

#### `memory_audit_log`
**Purpose**: Track memory consolidation operations
**Columns**: id, action, persona_id, session_id, source, content_hash, details, created_at

#### `coach_knowledge`
**Purpose**: System prompts, company values, canned responses
**Columns**: id, persona_id, knowledge_type, content, metadata, created_at

#### `persona_greetings`
**Purpose**: Greeting message pool
**Columns**: id, greeting_text, is_active, created_at

---

## Memory Architecture Rules

### RULE 1: Three-Tier Memory Only
- **SHORT-TERM**: Use `conversation_memories` (dynamic, session-specific)
- **MID-TERM**: Use `conversation_summaries` (consolidated segments)
- **LONG-TERM**: Use `long_term_memories` (persistent, high-value)

**DO NOT CREATE**: Additional memory tables

### RULE 2: Universal vs Session-Specific Memories
- **Universal memories**: `long_term_memories.session_id = NULL` (persona background, available to all conversations)
- **Session memories**: `long_term_memories.session_id = <uuid>` (specific relationship history)

### RULE 3: Trust-Gated Knowledge
- Use `character_knowledge_tiers` table with `available_knowledge` JSONB
- Trust thresholds: 0.0 (defensive), 0.4 (cautious), 0.6 (opening), 0.8 (trusting)

### RULE 4: Memory Consolidation Pipeline
```
conversation_memories (high importance)
    ↓ (consolidation service)
long_term_memories (persistent)
    ↓ (decay service)
archived (or deleted)
```

---

## Migration Naming Convention
- `0000_extensions.sql` - Database extensions
- `0001_init_core.sql` - Core tables
- `0002_rls_policies_dev.sql` - Security policies
- `0003_seed_minimum.sql` - Minimal seed data
- `0004_personas_upsert.sql` - Persona definitions
- `0005_tiers_mary_terry.sql` - Knowledge tier enrichment
- **NEXT**: `0006_seed_universal_memories.sql` - Populate long_term_memories

---

## Critical Don'ts

### ❌ DO NOT CREATE
- `persona_memories` table (use `long_term_memories` instead)
- `background_memories` table (use `long_term_memories` with session_id=NULL)
- `static_memories` table (use `long_term_memories`)
- `character_memories` table (use `long_term_memories`)
- `session_specific_memories` table (use `conversation_memories`)
- `archived_persona_memories` table (handle archival in `long_term_memories` with status flag if needed)

### ✅ DO USE
- `long_term_memories` for all persistent persona knowledge
- `conversation_memories` for all dynamic session insights
- `character_knowledge_tiers` for trust-gated progressive revelation
- `conversation_summaries` for consolidated context

---

## Vector Database Strategy

**Current State**: No external vector DB (ChromaDB, Pinecone) deployed

**When to Add Vector DB**:
1. When semantic similarity search is required (not just keyword matching)
2. When memory corpus exceeds 10,000+ entries per persona
3. When embedding-based retrieval provides measurable improvement over importance scoring

**Current Approach**:
- Use `importance_score` + keyword matching in `long_term_memories`
- Filter by `trust_threshold` in `character_knowledge_tiers`
- This is sufficient for 4 personas with ~20-50 memories each

**DO NOT**: Add ChromaDB/Pinecone/Weaviate until proven necessary by testing

---

## Schema Validation Checklist

Before creating any new table, ask:
1. ✅ Can this use `long_term_memories`? (persistent knowledge)
2. ✅ Can this use `conversation_memories`? (dynamic insights)
3. ✅ Can this use `character_knowledge_tiers`? (trust-gated content)
4. ✅ Can this be a JSONB column on an existing table?
5. ❌ Only create new table if all above are NO

---

## Current Schema Status
- ✅ All core tables exist (0001)
- ✅ Personas defined (0004: mary, terry, jan)
- ✅ Knowledge tiers populated (0005: mary, terry)
- ❌ `long_term_memories` table is EMPTY (needs seeding)
- ❌ SmartMemoryManager queries non-existent `persona_memories` table

**Next Migration**: Populate `long_term_memories` with universal persona backgrounds
