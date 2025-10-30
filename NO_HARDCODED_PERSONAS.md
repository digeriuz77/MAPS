# NO HARDCODED PERSONAS RULE
**Status**: 🔴 **MANDATORY ARCHITECTURAL RULE**
**Date Established**: October 29, 2025

---

## Core Rule

**ALL persona data MUST be stored in Supabase database tables.**

**NO persona-specific information may be hardcoded in application code.**

---

## Rationale

### Problem with Hardcoded Personas
1. **Deployment Overhead**: Every persona iteration requires full application redeployment
2. **Data Inconsistency**: Multiple sources of truth (code + database) inevitably drift
3. **Scalability**: Cannot add new personas without code changes
4. **Maintenance**: Changes require developer intervention instead of database updates
5. **Testing**: Cannot test persona variations without code modifications

### Benefits of Database-Only Approach
1. ✅ **Zero-Deployment Updates**: Modify personas via database migrations
2. ✅ **Single Source of Truth**: Database is canonical, no drift possible
3. ✅ **Rapid Iteration**: Test persona variations immediately
4. ✅ **Non-Technical Updates**: Content team can adjust personas
5. ✅ **Version Control**: Database migrations track all changes
6. ✅ **Environment Parity**: Dev/staging/prod use same persona logic

---

## What Is Prohibited

### ❌ NEVER Do This

**Hardcoded Persona Details**:
```python
# ❌ FORBIDDEN
if persona_id == "mary":
    return "Single mother with son Tommy"

# ❌ FORBIDDEN
mary_traits = {
    "family": ["son Tommy age 9", "sister Sarah"],
    "work": ["Rep of the Year 2022"]
}

# ❌ FORBIDDEN
PERSONA_CONFIGS = {
    "terry": {
        "experience_years": 15,
        "forbidden_phrases": ["I love small talk"]
    }
}
```

**Hardcoded Behavioral Rules**:
```python
# ❌ FORBIDDEN
if persona_id == "terry" and trust_level < 0.4:
    return "Be blunt and professional"
```

**Hardcoded Memories**:
```python
# ❌ FORBIDDEN
terry_memories = [
    "I have 15 years of experience",
    "I trained the current team"
]
```

**Hardcoded Validation Rules**:
```python
# ❌ FORBIDDEN
forbidden_phrases = {
    "mary": ["I don't have children", "My husband"],
    "terry": ["I love small talk", "I'm new here"]
}
```

---

## What Is Allowed

### ✅ ALWAYS Do This

**Generic Persona Logic**:
```python
# ✅ ALLOWED - No persona-specific details
persona_data = await get_persona_from_database(persona_id)
traits = persona_data.get('traits', {})
speech_patterns = traits.get('speech_patterns', {})
```

**Database-Driven Rules**:
```python
# ✅ ALLOWED - Loads from database
consistency_rules = await load_consistency_rules(persona_id)
forbidden_phrases = consistency_rules.get('forbidden_phrases', [])
```

**Configuration References**:
```python
# ✅ ALLOWED - References database-stored config
trust_config = await get_trust_configuration(persona_id)
trust_delta = trust_config.calculate_delta(interaction_quality)
```

---

## Database Schema Requirements

All persona data MUST be stored in these tables:

### 1. Core Persona Data
**Table**: `enhanced_personas`
**Contains**:
- `persona_id` (identifier)
- `name` (display name)
- `description` (overview)
- `system_context` (voice/boundaries)
- `core_identity` (foundational traits)
- `current_situation` (context)
- `traits` (JSONB: speech_patterns, defensiveness, etc.)
- `trust_behaviors` (JSONB: share budgets per tier)

### 2. Long-Term Memories
**Table**: `long_term_memories`
**Contains**:
- `persona_id` (reference)
- `content` (memory text)
- `importance` (0.0-1.0, maps to trust tiers)
- `memory_type` (semantic, episodic, preference)
- `session_id` (NULL for universal, UUID for session-specific)

### 3. Knowledge Tiers
**Table**: `character_knowledge_tiers`
**Contains**:
- `persona_id` (reference)
- `tier_name` (defensive, cautious, opening, trusting)
- `trust_threshold` (minimum trust to unlock)
- `available_knowledge` (JSONB: topics, details, resistance phrases)

### 4. Trust Configuration (NEW)
**Table**: `trust_configuration`
**Contains**:
- `persona_id` (reference)
- `quality_deltas` (JSONB: poor→-0.02, excellent→+0.03)
- `empathy_multipliers` (JSONB: hostile→0.5, supportive→1.5)
- `trajectory_adjustments` (JSONB: declining→-0.01, breakthrough→+0.05)
- `trust_decay_rate` (daily decay if no interaction)

### 5. Consistency Rules (NEW)
**Table**: `character_consistency_rules`
**Contains**:
- `persona_id` (reference)
- `forbidden_phrases` (JSONB array)
- `required_traits` (JSONB array)
- `knowledge_boundaries` (JSONB: topic → allowed knowledge)
- `personality_constraints` (JSONB array)
- `trust_level_rules` (JSONB: tier → sharing rules)

### 6. Vector Memories (NEW)
**Table**: `character_vector_memories`
**Contains**:
- `persona_id` (reference)
- `memory_type` (experience, knowledge, emotional_trigger, response_pattern)
- `content` (memory text)
- `context_tags` (JSONB array: ["work_stress", "family"])
- `emotional_weight` (0.0-1.0)
- `trust_level_required` (0.0-1.0)
- `embedding` (vector for future semantic search)

---

## Migration Strategy

### Adding New Personas
```sql
-- Step 1: Core profile
INSERT INTO enhanced_personas (persona_id, name, description, traits, ...)
VALUES ('new_persona', 'New Name', 'Description', ...);

-- Step 2: Universal memories
INSERT INTO long_term_memories (persona_id, content, importance, ...)
VALUES ('new_persona', 'Memory content', 0.35, ...);

-- Step 3: Knowledge tiers
INSERT INTO character_knowledge_tiers (persona_id, tier_name, available_knowledge, ...)
VALUES ('new_persona', 'defensive', '{"topics": [...]}', ...);

-- Step 4: Trust configuration
INSERT INTO trust_configuration (persona_id, quality_deltas, ...)
VALUES ('new_persona', '{"poor": -0.02, ...}', ...);

-- Step 5: Consistency rules
INSERT INTO character_consistency_rules (persona_id, forbidden_phrases, ...)
VALUES ('new_persona', '["phrase1", "phrase2"]', ...);

-- Step 6: Vector memories
INSERT INTO character_vector_memories (persona_id, content, context_tags, ...)
VALUES ('new_persona', 'Detailed memory', '["tag1", "tag2"]', ...);
```

**Result**: New persona available immediately without code deployment ✅

### Modifying Existing Personas
```sql
-- Update voice patterns
UPDATE enhanced_personas
SET traits = jsonb_set(
    traits,
    '{speech_patterns,signature_phrases}',
    '["New phrase", "Another phrase"]'
)
WHERE persona_id = 'terry';

-- Add new memories
INSERT INTO long_term_memories (persona_id, content, importance, ...)
VALUES ('mary', 'New memory about recent event', 0.65, ...);

-- Adjust trust deltas
UPDATE trust_configuration
SET quality_deltas = jsonb_set(
    quality_deltas,
    '{excellent}',
    '0.04'  -- Increased from 0.03
)
WHERE persona_id = 'jan';
```

**Result**: Persona updated without code deployment ✅

---

## Code Patterns

### Service Initialization

**❌ OLD (Hardcoded)**:
```python
class CharacterConsistencyService:
    def __init__(self):
        self.character_rules = self._initialize_character_rules()  # Hardcoded!

    def _initialize_character_rules(self):
        rules = {}
        rules["mary"] = ConsistencyRules(...)  # ❌ Hardcoded Mary
        rules["terry"] = ConsistencyRules(...)  # ❌ Hardcoded Terry
        return rules
```

**✅ NEW (Database-Driven)**:
```python
class CharacterConsistencyService:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        # No hardcoded initialization!

    async def get_consistency_rules(self, persona_id: str):
        # Load from database on-demand
        result = self.supabase.table('character_consistency_rules')\
            .select('*')\
            .eq('persona_id', persona_id)\
            .single()\
            .execute()
        return result.data  # ✅ Database-driven
```

### Validation Logic

**❌ OLD (Hardcoded)**:
```python
if persona_id == "terry":
    forbidden = ["I love small talk", "I'm new here"]  # ❌ Hardcoded
    for phrase in forbidden:
        if phrase in response:
            return False
```

**✅ NEW (Database-Driven)**:
```python
rules = await self.get_consistency_rules(persona_id)  # ✅ From DB
forbidden = rules.get('forbidden_phrases', [])
for phrase in forbidden:
    if phrase in response:
        return False
```

---

## Exception: Framework Code

### What IS Allowed to Be Hardcoded

**Generic Constants** (not persona-specific):
```python
# ✅ ALLOWED - Generic trust thresholds
TRUST_TIERS = {
    'defensive': (0.0, 0.4),
    'cautious': (0.4, 0.6),
    'opening': (0.6, 0.8),
    'trusting': (0.8, 1.0)
}

# ✅ ALLOWED - Generic quality levels
INTERACTION_QUALITIES = ['poor', 'adequate', 'good', 'excellent']

# ✅ ALLOWED - Generic empathy tones
EMPATHY_TONES = ['hostile', 'neutral', 'supportive', 'deeply_empathetic']
```

**Default Fallbacks** (when database missing):
```python
# ✅ ALLOWED - Sensible defaults if DB unavailable
DEFAULT_TRUST_DELTA = {
    'poor': -0.02,
    'adequate': 0.00,
    'good': +0.01,
    'excellent': +0.02
}
```

**Schema Definitions** (data structure, not content):
```python
# ✅ ALLOWED - Dataclass schemas
@dataclass
class ConsistencyRules:
    persona_id: str
    forbidden_phrases: List[str]  # Schema only
    required_traits: List[str]    # Schema only
    # No actual persona data!
```

---

## Enforcement

### Code Review Checklist
- [ ] No `if persona_id == "mary"` conditionals
- [ ] No dictionaries with persona names as keys
- [ ] No hardcoded lists of persona-specific values
- [ ] All persona data loaded from database
- [ ] Services accept `supabase_client` in constructor
- [ ] No `_initialize_character_data()` methods with hardcoded data

### Automated Checks
```bash
# Detect hardcoded persona references
grep -r "persona_id == ['\"]mary" src/
grep -r "persona_id == ['\"]terry" src/
grep -r "persona_id == ['\"]jan" src/

# Should return no results (except test files)
```

### Migration Verification
```bash
# Ensure all persona data in database
SELECT persona_id, COUNT(*) FROM enhanced_personas GROUP BY persona_id;
SELECT persona_id, COUNT(*) FROM long_term_memories WHERE session_id IS NULL GROUP BY persona_id;
SELECT persona_id, COUNT(*) FROM character_knowledge_tiers GROUP BY persona_id;
SELECT persona_id, COUNT(*) FROM trust_configuration GROUP BY persona_id;
SELECT persona_id, COUNT(*) FROM character_consistency_rules GROUP BY persona_id;
SELECT persona_id, COUNT(*) FROM character_vector_memories GROUP BY persona_id;
```

---

## Migration Timeline

### Phase 1: Create Tables (Week 1)
- [ ] Migration 0008: `trust_configuration` table
- [ ] Migration 0009: `character_consistency_rules` table
- [ ] Migration 0010: `character_vector_memories` table
- [ ] Migration 0011: Seed all 3 personas in new tables

### Phase 2: Update Services (Week 1)
- [ ] Modify `character_consistency_service.py` to use database
- [ ] Modify `character_vector_service.py` to use database
- [ ] Add database queries to replace hardcoded data
- [ ] Remove `_initialize_*` methods

### Phase 3: Testing (Week 1-2)
- [ ] Test Mary with database-driven data
- [ ] Test Terry with database-driven data
- [ ] Test Jan with database-driven data
- [ ] Verify no hardcoded references remain

### Phase 4: Cleanup (Week 2)
- [ ] Delete hardcoded data from services
- [ ] Update documentation
- [ ] Add automated checks to CI/CD

---

## Success Criteria

✅ **Zero hardcoded persona details in `src/` directory**
✅ **All 3 personas (Mary, Terry, Jan) have complete data in all 6 tables**
✅ **Services load persona data from database**
✅ **New persona can be added via SQL migration only**
✅ **Persona modifications require no code deployment**
✅ **Trust deltas configurable per persona in database**

---

## Violation Examples (From Current Code)

### Example 1: character_consistency_service.py
```python
# ❌ VIOLATION - Lines 45-258
def _initialize_character_rules(self):
    rules = {}
    rules["mary"] = ConsistencyRules(...)  # HARDCODED
    rules["terry"] = ConsistencyRules(...)  # HARDCODED
    return rules
```

**Fix Required**: Remove method, load from `character_consistency_rules` table

### Example 2: character_vector_service.py
```python
# ❌ VIOLATION - Lines 58+
def _initialize_character_data(self):
    mary_memories = [...]  # HARDCODED
    terry_memories = [...]  # HARDCODED
```

**Fix Required**: Remove method, load from `character_vector_memories` table

---

## Document Status

**Version**: 1.0
**Last Updated**: October 29, 2025
**Next Review**: Before any persona-related code changes
**Owner**: Architecture Team
**Enforcement**: Mandatory for all persona-related code

---

## Related Documents

- `HARDCODED_PERSONA_AUDIT.md` - Audit that identified violations
- `DATABASE_SCHEMA_RULEBOOK.md` - Schema design principles
- `ARCHITECTURE_REVIEW.md` - Overall system architecture
- `supabase/0008_trust_configuration.sql` - Trust delta configuration
- `supabase/0009_character_consistency_rules.sql` - Consistency rules
- `supabase/0010_character_vector_memories.sql` - Detailed memories
