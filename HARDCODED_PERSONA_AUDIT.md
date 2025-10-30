# Hardcoded Persona Data Audit
**Date**: October 29, 2025
**Status**: ⚠️ CRITICAL - Hardcoded persona data found in active services

---

## Executive Summary

**Finding**: Two active services contain extensive hardcoded persona information that duplicates and potentially conflicts with Supabase data.

**Impact**:
- ⚠️ High risk of data inconsistency between code and database
- ⚠️ Persona data exists in 3 locations (code, database, migrations)
- ⚠️ Contains data for 4 personas (Mary, Terry, Alex, Jordan) but only 3 exist in database
- ✅ Both services ARE actively being called in the pipeline

---

## Affected Services

### 1. Character Consistency Service ⚠️

**File**: `src/services/character_consistency_service.py`

**Status**: ✅ **ACTIVELY USED** in pipeline (line 246 of enhanced_persona_service.py)

**Hardcoded Data**: Lines 45-258

**Personas Defined**:
- Mary (lines 53-100)
- Terry (lines 105-152)
- Alex (lines 157-204) ❌ **NOT IN DATABASE**
- Jordan (lines 209-256) ❌ **NOT IN DATABASE**

**Data Types Hardcoded**:
```python
rules["mary"] = ConsistencyRules(
    persona_id="mary",
    trust_level_rules={
        "low_trust": [...],
        "building_trust": [...],
        "high_trust": [...]
    },
    personality_constraints=[...],
    knowledge_boundaries={
        "work": ["Customer Service Rep of the Year 2022", "Money and Pensions Service", "performance decline"],
        "family": ["son Tommy age 9", "sister Sarah health problems", "single mother"],
        "values": ["Buddhist philosophy", "compassion", "understanding", "work excellence"]
    },
    forbidden_phrases=[
        "I don't have children",
        "My husband",
        "I don't care about work",
        "I've never had performance issues"
    ],
    required_traits=[...]
)
```

**Terry's Hardcoded Data**:
```python
knowledge_boundaries={
    "work": ["15 years experience", "pension regulations expert", "customer service", "efficiency focused"],
    "feedback": ["too direct", "abrupt", "intimidating to colleagues", "communication issues"],
    "values": ["competence", "efficiency", "helping customers", "getting results"]
},
forbidden_phrases=[
    "I love small talk",
    "I'm new to this job",
    "I don't care about helping customers",
    "Communication has never been an issue"
]
```

**Integration Point**:
```python
# enhanced_persona_service.py:246
validated_response, was_corrected, violations = await character_consistency_service.validate_and_correct(
    persona_id=persona_id,
    response=response,
    trust_level=trust_level,
    user_input=user_message,
    interaction_quality=interaction_context.interaction_quality
)
```

---

### 2. Character Vector Service ⚠️

**File**: `src/services/character_vector_service.py`

**Status**: ✅ **ACTIVELY USED** in pipeline (line 436 of enhanced_persona_service.py)

**Hardcoded Data**: Starts at line 58 (`_initialize_character_data()`)

**Personas Defined**:
- Mary (extensive memories)
- Terry (extensive memories)
- Alex ❌ **NOT IN DATABASE**
- Jordan ❌ **NOT IN DATABASE**

**Data Types Hardcoded**:
```python
mary_memories = [
    CharacterMemory(
        memory_id="mary_001",
        persona_id="mary",
        memory_type="experience",
        content="Won Customer Service Rep of the Year in 2022 - felt proud and accomplished",
        context_tags=["achievement", "work_pride", "past_success"],
        emotional_weight=0.9,
        trust_level_required=0.3,
    ),
    CharacterMemory(
        memory_id="mary_002",
        persona_id="mary",
        memory_type="experience",
        content="Tommy's teacher called last week about behavioral issues at school",
        context_tags=["parenting_stress", "guilt", "school_problems"],
        emotional_weight=0.8,
        trust_level_required=0.7,
    ),
    # ... many more memories
]
```

**Integration Point**:
```python
# enhanced_persona_service.py:436
character_context = character_vector_service.get_character_context(
    persona_id=persona_id,
    user_input=user_message,
    trust_level=trust_level,
    interaction_quality=interaction_context.interaction_quality
)
```

---

## Data Duplication Analysis

### Mary's Data Comparison

**Supabase (`long_term_memories` table)**:
- 15 memories about work, team, stress
- General professional context
- Importance-based (0.30-0.95)

**Character Vector Service (hardcoded)**:
- Specific family details: "Tommy age 9", "sister Sarah health problems"
- Detailed emotional triggers
- Experience-based memories
- "Customer Service Rep of the Year 2022"

**Character Consistency Service (hardcoded)**:
- Forbidden phrases: "I don't have children", "My husband"
- Knowledge boundaries: "son Tommy age 9", "sister Sarah", "Buddhist philosophy"
- Trust level rules for what to reveal when

**Overlap**: "Rep of the Year 2022" exists in both Supabase migration AND hardcoded services ✅

**Conflict Risk**: Family details (Tommy, Sarah) NOT in Supabase but heavily referenced in code ⚠️

---

### Terry's Data Comparison

**Supabase (`long_term_memories` table)**:
- 12 memories about experience, efficiency, accuracy
- "I have 15 years of experience"
- "I prioritize efficiency and accuracy"
- Professional focus

**Character Vector Service (hardcoded)**:
- "15 years customer service experience"
- Pension regulations expertise
- Specific response patterns based on trust level

**Character Consistency Service (hardcoded)**:
- Forbidden phrases: "I love small talk", "I'm new to this job"
- Knowledge boundaries: "15 years experience", "pension regulations expert"
- Trust-based behavior rules

**Overlap**: "15 years experience" consistent across all sources ✅

**Conflict Risk**: Low - hardcoded data generally aligns with Supabase ✅

---

### Jan's Data Comparison

**Supabase (`long_term_memories` table)**:
- 12 memories about performance confusion, metrics, personal stress
- General work context

**Character Vector Service (hardcoded)**:
- ❌ **DOES NOT EXIST** (only Mary, Terry, Alex, Jordan)

**Character Consistency Service (hardcoded)**:
- ❌ **DOES NOT EXIST** (only Mary, Terry, Alex, Jordan)

**Problem**: Jan exists in database but NOT in hardcoded services! ⚠️

---

## Critical Issues

### Issue #1: Phantom Personas (Alex & Jordan)

**Problem**: Code contains extensive data for Alex and Jordan who don't exist in Supabase

**Files**:
- `character_consistency_service.py` lines 157-204 (Alex)
- `character_consistency_service.py` lines 209-256 (Jordan)
- `character_vector_service.py` (extensive Alex & Jordan memories)

**Impact**:
- Code expects 4 personas, database has 3
- If user tries to access Alex/Jordan, will fail at database level
- Wasted memory and initialization time
- Log line says "initialized with 4 personas" (character_vector_service.py:56)

**Evidence**:
```python
# character_vector_service.py:56
logger.info("🎭 Character Vector Service initialized with 4 personas")
```

---

### Issue #2: Missing Persona (Jan)

**Problem**: Jan exists in database but NOT in hardcoded services

**Database Evidence**:
- Migration 0006: 12 memories for Jan
- Migration 0007: Tier enrichment for Jan
- Enhanced_personas table: Jan's profile exists

**Code Evidence**:
- character_consistency_service.py: Only Mary, Terry, Alex, Jordan
- character_vector_service.py: Only Mary, Terry, Alex, Jordan

**Impact**:
- Jan conversations will NOT benefit from consistency validation
- Jan conversations will NOT get character-specific context from vector service
- Asymmetric functionality across personas

**Potential Failure**:
```python
# character_consistency_service.py:275-277
if persona_id not in self.character_rules:
    logger.warning(f"No consistency rules found for persona {persona_id}")
    return True, []  # Silently passes without validation!
```

---

### Issue #3: Family Details Not in Database

**Problem**: Mary's family details (Tommy, Sarah) are heavily used in hardcoded services but NOT in Supabase

**Hardcoded References**:
- "son Tommy age 9"
- "sister Sarah health problems"
- "Tommy's teacher called about behavioral issues"
- "Sarah's mysterious illness"

**Database**: No mentions of Tommy or Sarah in migration 0006

**Impact**:
- Inconsistency between memory retrieval (no family) and consistency checks (expects family)
- If long-term memories reference family, they might violate consistency rules
- New memories about family won't be validated against existing family context

---

### Issue #4: Data Synchronization Risk

**Problem**: Three sources of truth with no synchronization mechanism

**Sources**:
1. **Supabase migrations** (0006_seed_universal_memories.sql)
2. **Character Consistency Service** (character_consistency_service.py)
3. **Character Vector Service** (character_vector_service.py)

**Synchronization**: ❌ **NONE** - all manually maintained

**Risk Examples**:
- Change Mary's work history in Supabase → hardcoded services still have old data
- Add new persona to database → hardcoded services don't know about them
- Update Terry's experience from 15→17 years → must update 3 files manually

---

## Usage Analysis

### How Hardcoded Services Are Used

**Character Consistency Service**:
```python
# Called AFTER response generation (Step 6)
validated_response, was_corrected, violations = await character_consistency_service.validate_and_correct(
    persona_id=persona_id,
    response=response,
    trust_level=trust_level,
    user_input=user_message,
    interaction_quality=interaction_context.interaction_quality
)
```

**Purpose**: Post-processing validation
- Checks for forbidden phrases
- Validates trust-appropriate sharing
- Corrects out-of-character responses

**Character Vector Service**:
```python
# Called BEFORE response generation
character_context = character_vector_service.get_character_context(
    persona_id=persona_id,
    user_input=user_message,
    trust_level=trust_level,
    interaction_quality=interaction_context.interaction_quality
)
```

**Purpose**: Contextual enhancement
- Retrieves relevant character memories
- Provides situational response patterns
- Adds depth to persona responses

---

## Impact on 12-Turn Test

**Question**: Did hardcoded data affect the Terry test results?

**Answer**: ✅ **YES** - Both services were active

**Evidence from Logs**:
```
# Character Consistency Service initialized
🎭 Character Consistency Service initialized

# Character Vector Service initialized
🎭 Character Vector Service initialized with 4 personas

# Both called during pipeline (Steps 4 & 6)
```

**Terry's Hardcoded Data Used**:
- Forbidden phrases: "I love small talk", "I'm new to this job" (checked in validation)
- Knowledge boundaries: "15 years experience", "efficiency focused" (used for context)
- Trust-level rules: Defensive behavior patterns (influenced response style)

**Why It Still Worked**:
- Terry's hardcoded data ALIGNS with Supabase data ("15 years" consistent) ✅
- Consistency service validated responses matched Terry's character ✅
- Vector service provided additional depth beyond Supabase memories ✅

**Why It Could Have Failed**:
- If hardcoded data conflicted with Supabase, responses might be corrected incorrectly ⚠️
- Jan test would fail consistency checks (no rules defined) ⚠️
- Alex/Jordan references would silently fail database queries ⚠️

---

## Recommendations

### Option A: Remove All Hardcoded Data (Recommended)

**Action**: Migrate all hardcoded persona data to Supabase

**Steps**:
1. Create new migrations:
   - `0008_character_consistency_rules.sql` (forbidden phrases, knowledge boundaries)
   - `0009_character_vector_memories.sql` (detailed memories, emotional triggers)
2. Modify services to load from database:
   - `character_consistency_service.py`: Query rules from `character_consistency_rules` table
   - `character_vector_service.py`: Query memories from `character_vector_memories` table
3. Remove hardcoded `_initialize_character_rules()` and `_initialize_character_data()` methods
4. Add Jan's data to new tables
5. Remove Alex and Jordan data

**Pros**:
- Single source of truth ✅
- Easier to maintain ✅
- Consistent across all 3 personas ✅
- No risk of data drift ✅

**Cons**:
- Requires schema changes (new tables)
- Migration effort (2-4 hours)
- Performance: database queries instead of in-memory

---

### Option B: Complete Hardcoded Data (Quick Fix)

**Action**: Add Jan to hardcoded services, remove Alex and Jordan

**Steps**:
1. Add Jan's consistency rules to `character_consistency_service.py`
2. Add Jan's memories to `character_vector_service.py`
3. Remove Alex's data from both files
4. Remove Jordan's data from both files
5. Update log message: "4 personas" → "3 personas"

**Pros**:
- Fast (30 minutes) ✅
- No schema changes ✅
- Immediate fix ✅

**Cons**:
- Maintains data duplication ⚠️
- Still 3 sources of truth ⚠️
- Manual synchronization required ⚠️
- Doesn't scale to new personas ⚠️

---

### Option C: Hybrid Approach

**Action**: Keep hardcoded for consistency rules, move detailed memories to database

**Reasoning**:
- Consistency rules change rarely (forbidden phrases, core traits)
- Memories should be in database (long-term, searchable, dynamic)

**Steps**:
1. Keep `character_consistency_service.py` hardcoded (update for Jan, remove Alex/Jordan)
2. Move `character_vector_service.py` memories to Supabase
3. Create new table: `character_detailed_memories` with trust-level filtering

**Pros**:
- Balances performance and flexibility ✅
- Reduces most critical duplication ✅
- Consistency rules fast (in-memory) ✅

**Cons**:
- Still some duplication ⚠️
- Complex architecture ⚠️

---

## Testing Impact

### Current Test Results

**12-Turn Terry Test**: ✅ PASSED despite hardcoded data

**Why**: Terry's hardcoded data aligned with database

**At Risk**:
- Jan 12-turn test ⚠️ (no consistency rules, no vector memories)
- Mary test with family mentions ⚠️ (family details not in DB)
- Future persona additions ⚠️ (must update 3 locations)

---

## Immediate Action Required

### Critical Fix (15 minutes)

**Add Jan to hardcoded services to ensure parity with Mary and Terry**:

```python
# character_consistency_service.py - Add after Terry (line 153)
rules["jan"] = ConsistencyRules(
    persona_id="jan",
    trust_level_rules={...},
    personality_constraints=[...],
    knowledge_boundaries={...},
    forbidden_phrases=[...],
    required_traits=[...]
)

# character_vector_service.py - Add after Terry
jan_memories = [...]
```

### Medium Priority (1-2 hours)

**Remove Alex and Jordan** from both services to match database reality

### Long-term (2-4 hours)

**Migrate to database-driven approach** (Option A) for maintainability

---

## Files to Modify

### Immediate
1. `src/services/character_consistency_service.py` - Add Jan, remove Alex/Jordan
2. `src/services/character_vector_service.py` - Add Jan, remove Alex/Jordan

### Future (Option A)
3. `supabase/0008_character_consistency_rules.sql` - New migration
4. `supabase/0009_character_vector_memories.sql` - New migration
5. Update both service files to query database instead of hardcoded data

---

## Conclusion

**Finding**: ⚠️ Extensive hardcoded persona data exists and IS actively used

**Risk Level**: 🟡 **MEDIUM**
- Currently working for Terry (data aligns)
- Would fail for Jan (missing data)
- Would fail for future personas
- Maintenance nightmare (3 sources of truth)

**Recommended Action**: **Option B (Quick Fix)** immediately, followed by **Option A (Database Migration)** for long-term sustainability

**Priority**:
- 🔴 **HIGH**: Add Jan to hardcoded services (prevent Jan test failures)
- 🟡 **MEDIUM**: Remove Alex/Jordan (clean up phantom personas)
- 🟢 **LOW**: Migrate to database (technical debt reduction)
