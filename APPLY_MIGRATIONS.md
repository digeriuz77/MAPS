# How to Apply Database Migrations

## Quick Start

You have **4 new migrations** ready to apply:
1. `0008_trust_configuration.sql` - Trust calculation parameters
2. `0009_character_consistency_rules.sql` - Validation rules
3. `0010_character_vector_memories.sql` - Detailed memories (FIXED - no pgvector error)
4. `0011_enrich_long_term_memories.sql` - More universal memories

---

## Option 1: Supabase Dashboard (Recommended)

### Steps:
1. Go to https://supabase.com/dashboard
2. Select your project
3. Click **SQL Editor** in left sidebar
4. Click **New Query**
5. Copy/paste each migration file **in order**
6. Click **Run** for each one

### Order:
```
1. 0008_trust_configuration.sql       (creates trust_configuration table)
2. 0009_character_consistency_rules.sql (creates character_consistency_rules table)
3. 0010_character_vector_memories.sql  (creates character_vector_memories table)
4. 0011_enrich_long_term_memories.sql  (adds memories to existing long_term_memories)
```

---

## Option 2: Supabase CLI

### Prerequisites:
```bash
# Install Supabase CLI if not already installed
npm install -g supabase

# Login to Supabase
supabase login
```

### Link Project:
```bash
cd /c/builds/character/character-ai-chat
supabase link --project-ref YOUR_PROJECT_REF
```

### Apply Migrations:
```bash
# Supabase CLI will auto-detect migrations in supabase/ folder
supabase db push

# Or apply individually:
supabase db execute -f supabase/0008_trust_configuration.sql
supabase db execute -f supabase/0009_character_consistency_rules.sql
supabase db execute -f supabase/0010_character_vector_memories.sql
supabase db execute -f supabase/0011_enrich_long_term_memories.sql
```

---

## Option 3: Direct psql (If you have database credentials)

```bash
# Apply each migration
psql postgresql://postgres:[YOUR-PASSWORD]@[HOST]:5432/postgres -f supabase/0008_trust_configuration.sql
psql postgresql://postgres:[YOUR-PASSWORD]@[HOST]:5432/postgres -f supabase/0009_character_consistency_rules.sql
psql postgresql://postgres:[YOUR-PASSWORD]@[HOST]:5432/postgres -f supabase/0010_character_vector_memories.sql
psql postgresql://postgres:[YOUR-PASSWORD]@[HOST]:5432/postgres -f supabase/0011_enrich_long_term_memories.sql
```

---

## Verification After Application

### Check Tables Created:
```sql
-- Should return 1 for each
SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'trust_configuration';
SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'character_consistency_rules';
SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'character_vector_memories';
```

### Check Data Inserted:
```sql
-- Should return 3 (Mary, Terry, Jan)
SELECT COUNT(*) FROM trust_configuration;
SELECT COUNT(*) FROM character_consistency_rules;

-- Should return 56 (20 + 18 + 18)
SELECT COUNT(*) FROM character_vector_memories;

-- Should return 78 (28 + 25 + 25)
SELECT COUNT(*) FROM long_term_memories WHERE session_id IS NULL;
```

### Check Per-Persona Counts:
```sql
-- Trust configurations
SELECT persona_id FROM trust_configuration ORDER BY persona_id;
-- Expected: jan, mary, terry

-- Consistency rules
SELECT persona_id FROM character_consistency_rules ORDER BY persona_id;
-- Expected: jan, mary, terry

-- Vector memories
SELECT persona_id, COUNT(*)
FROM character_vector_memories
GROUP BY persona_id
ORDER BY persona_id;
-- Expected: jan (18), mary (20), terry (18)

-- Long-term memories (universal)
SELECT persona_id, COUNT(*)
FROM long_term_memories
WHERE session_id IS NULL
GROUP BY persona_id
ORDER BY persona_id;
-- Expected: jan (25), mary (28), terry (25)
```

---

## Troubleshooting

### Error: "relation enhanced_personas does not exist"
**Cause**: Need to run earlier migrations first (0001-0007)
**Fix**: Apply migrations 0001-0007 first

### Error: "type vector does not exist"
**Cause**: pgvector extension not available (FIXED in migration 0010)
**Status**: ✅ Migration 0010 updated to use JSONB instead - no longer an issue

### Error: "duplicate key value violates unique constraint"
**Cause**: Data already exists from previous run
**Fix**: Safe to ignore - migrations use `ON CONFLICT DO UPDATE` or `ON CONFLICT DO NOTHING`

### Error: "column hash does not exist"
**Cause**: Migration 0011 expects `hash` column in long_term_memories
**Fix**: Check migration 0006 was applied (creates long_term_memories with hash column)

---

## What Each Migration Does

### 0008: trust_configuration
Creates per-persona trust calculation parameters.

**Enables**:
- Adjust trust deltas without code deployment
- Different personas respond differently to same interaction
- Mary: slow trust, fragile
- Terry: medium trust, values directness
- Jan: fast trust but very fragile

**Example Tuning**:
```sql
-- Make Terry build trust faster for excellent interactions
UPDATE trust_configuration
SET quality_deltas = jsonb_set(quality_deltas, '{excellent}', '0.04')
WHERE persona_id = 'terry';
```

### 0009: character_consistency_rules
Creates validation rules to prevent out-of-character responses.

**Enables**:
- Forbidden phrases per persona (e.g., Mary can't say "I don't have children")
- Knowledge boundaries (what they know/don't know)
- Trust-level appropriate sharing rules
- Response length constraints

**Example Update**:
```sql
-- Add new forbidden phrase for Mary
UPDATE character_consistency_rules
SET forbidden_phrases = forbidden_phrases || '["My husband"]'::jsonb
WHERE persona_id = 'mary';
```

### 0010: character_vector_memories
Creates detailed character memories for rich context.

**Enables**:
- 56 detailed memories (experiences, triggers, patterns)
- Trust-gated progressive revelation
- Emotional weight tracking
- Context tags for retrieval

**Example Query**:
```sql
-- Get Terry's memories accessible at trust 0.5
SELECT content, context_tags
FROM character_vector_memories
WHERE persona_id = 'terry'
  AND trust_level_required <= 0.5
ORDER BY emotional_weight DESC;
```

### 0011: enrich_long_term_memories
Adds 39 more memories to existing long_term_memories table.

**Enriches**:
- Mary: 15 → 28 memories (+13)
- Terry: 12 → 25 memories (+13)
- Jan: 12 → 25 memories (+13)

**Example Query**:
```sql
-- Get Mary's defensive tier memories
SELECT content, importance
FROM long_term_memories
WHERE persona_id = 'mary'
  AND session_id IS NULL
  AND importance <= 0.40
ORDER BY importance;
```

---

## After Migration: Update Code

Once migrations are applied:

### 1. Update character_consistency_service
```bash
# Backup old
mv src/services/character_consistency_service.py src/services/character_consistency_service_OLD.py

# Use new database-driven version
mv src/services/character_consistency_service_v2.py src/services/character_consistency_service.py
```

### 2. Initialize with Supabase Client
In `src/services/enhanced_persona_service.py`, ensure:
```python
from src.services.character_consistency_service import initialize_character_consistency_service
from src.dependencies import get_supabase_client

# At startup
supabase = get_supabase_client()
initialize_character_consistency_service(supabase)
```

### 3. Test
```bash
python test_12_turns.py  # Should work with Terry
```

---

## Rollback (If Needed)

### Database Rollback:
```sql
-- Remove in reverse order
DROP TABLE IF EXISTS character_vector_memories CASCADE;
DROP TABLE IF EXISTS character_consistency_rules CASCADE;
DROP TABLE IF EXISTS trust_configuration CASCADE;

-- Revert enrichment (optional - can leave the extra memories)
DELETE FROM long_term_memories
WHERE hash IN (
  'mary_email_delays', 'mary_context_preference', ...
  -- List all hashes from 0011 if needed
);
```

### Code Rollback:
```bash
mv src/services/character_consistency_service_OLD.py src/services/character_consistency_service.py
```

---

## Summary

**Migrations to Apply**: 4 files (0008, 0009, 0010, 0011)
**Method**: Supabase Dashboard SQL Editor (easiest)
**Time**: ~5 minutes
**Risk**: Low (migrations are additive, use IF NOT EXISTS)
**Verification**: Run SQL queries above to confirm counts
**Next Step**: Update code to use new database-driven services

**Status After Migration**:
- ✅ 3 personas with complete data (Mary, Terry, Jan)
- ✅ 78 long-term memories
- ✅ 56 vector memories
- ✅ Trust configuration per persona
- ✅ Consistency rules per persona
- ✅ Zero hardcoded persona data
