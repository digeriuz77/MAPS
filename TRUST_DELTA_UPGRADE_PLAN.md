# Trust Delta Upgrade Plan

## Problem Identified

**Current Situation**: Trust progression is too slow, creating vicious cycles
- 5 excellent+supportive turns = only 0.060 increase (0.30 → 0.36)
- Need 15 excellent turns to reach cautious threshold (0.40 → 0.60)
- Users get frustrated → LLM sees frustration as hostile → Trust decreases → Vicious cycle

**Root Cause**: The rich `trust_configuration` table exists (migration 0008) but isn't being used yet.

---

## Current Architecture

### What's Happening Now
```python
# conversation_state.py line 181
trust_delta = self.trust_config_service.calculate_trust_delta(empathy_score, trust_config)
#                                                              ^^^^^^^^^^^^^ Only 1 parameter!
```

The old `trust_configuration_service.py`:
- Tries to query `enhanced_personas.trust_variable` (doesn't exist)
- Tries to query `trust_tiers` table (doesn't exist)
- **Falls back to hardcoded deltas**: `+0.015` for excellent, `+0.010` for good

### What We Have in Database (Not Being Used)
```sql
-- trust_configuration table (migration 0008)
SELECT quality_deltas, empathy_multipliers, approach_modifiers
FROM trust_configuration
WHERE persona_id = 'terry';

-- Result:
quality_deltas: {"excellent": 0.025, "good": 0.015, ...}
empathy_multipliers: {"supportive": 1.6, "neutral": 1.0, ...}
approach_modifiers: {"collaborative": 1.4, "supportive": 1.6, ...}
```

**Rich calculation formula**:
```
delta = (base_quality + trajectory_adjustment) × empathy_mult × approach_mod
```

But this isn't being calculated because the service signature is wrong!

---

## Available Data

The system already captures all needed data in `InteractionContext`:

```python
@dataclass
class InteractionContext:
    interaction_quality: str     # "poor", "adequate", "good", "excellent" ✅
    empathy_tone: str            # "hostile", "neutral", "supportive" ✅
    user_approach: str           # "directive", "questioning", "collaborative" ✅
    trust_trajectory: str        # "declining", "stable", "building" ✅
```

We just need to pass these to the trust calculation!

---

## Solution: 3-Step Upgrade

### Step 1: Apply Updated Trust Deltas (READY)
**File**: `supabase/0008a_update_trust_deltas_faster.sql`

**Changes**:
| Persona | Old Excellent | New Excellent | Supportive Mult | Collaborative Mod |
|---------|---------------|---------------|-----------------|-------------------|
| Mary    | 0.025         | 0.05          | 1.6 → 1.8       | 1.4 → 1.8         |
| Terry   | 0.03          | 0.06          | 1.3 → 1.6       | 1.4 → 1.9         |
| Jan     | 0.035         | 0.07          | 1.8 → 2.0       | 1.6 → 2.0         |

**New Trust Progression** (Terry example):
```
Good + Supportive + Collaborative + Building:
Base: 0.04 (good)
+ Trajectory: 0.02 (building)
= 0.06
× Empathy: 1.6 (supportive)
= 0.096
× Approach: 1.9 (collaborative)
= 0.182 per turn

Result: 5 turns = 0.91 increase (capped at tier boundaries)
Goal achieved: 5-7 turns to reach cautious ✅
```

### Step 2: Replace trust_configuration_service (READY)
**File**: `src/services/trust_configuration_service_v2.py`

**Key Changes**:
- Queries NEW `trust_configuration` table (not enhanced_personas.trust_variable)
- `calculate_trust_delta(quality, empathy_tone, approach, trajectory, trust_config)`
- Returns rich calculated delta using multipliers

### Step 3: Update conversation_state.py to Pass Rich Parameters
**File**: `src/models/conversation_state.py`

**Current**:
```python
async def update_with_llm_insights(
    self,
    empathy_score: float,  # OLD: 0-10 scale
    ...
) -> ConversationState:
    trust_delta = await self._calculate_trust_delta_from_db(empathy_score, state, persona_id)
```

**Needs**:
```python
async def update_with_llm_insights(
    self,
    interaction_context: InteractionContext,  # NEW: rich context with quality, empathy, approach, trajectory
    ...
) -> ConversationState:
    trust_delta = await self._calculate_trust_delta_from_db(interaction_context, state, persona_id)
```

**Then**:
```python
async def _calculate_trust_delta_from_db(
    self,
    interaction_context: InteractionContext,
    state: ConversationState,
    persona_id: str
) -> float:
    trust_config = self.trust_config_service.get_persona_trust_config(persona_id)

    trust_delta = self.trust_config_service.calculate_trust_delta(
        quality=interaction_context.interaction_quality,      # "excellent"
        empathy_tone=interaction_context.empathy_tone,        # "supportive"
        approach=interaction_context.user_approach,           # "collaborative"
        trajectory=interaction_context.trust_trajectory,      # "building"
        trust_config=trust_config
    )

    return trust_delta
```

---

## Impact Analysis

### Before Upgrade
- **5 excellent turns**: 0.060 increase (too slow)
- **Vicious cycle risk**: High (frustrated users → trust drops)
- **Training time**: 15-20 turns to reach cautious

### After Upgrade
- **5-7 good turns**: 0.60-0.90 increase (reaches cautious!)
- **Vicious cycle risk**: Low (system rewards consistency)
- **Training time**: 10-12 turns to reach trusting (realistic)

### New Progression Example (Terry)
```
Turn 1: Adequate + Neutral    = +0.010 (0.30 → 0.31)
Turn 2: Good + Supportive      = +0.096 (0.31 → 0.41) ← Crosses to Cautious!
Turn 3: Excellent + Supportive = +0.182 (0.41 → 0.59)
Turn 4: Excellent + Supportive = +0.182 (0.59 → 0.77) ← Crosses to Opening!
Turn 5: Good + Supportive      = +0.096 (0.77 → 0.87) ← Near Trusting!
```

With caps at tier transitions: ~7-8 turns to reach trusting tier (much more realistic!)

---

## Tier Transition Caps (Recommended)

To prevent unrealistic jumps, implement per-tier caps:

```python
def _apply_tier_transition_cap(self, current_trust: float, raw_delta: float) -> float:
    """Cap trust gains at tier boundaries to prevent unrealistic jumps"""

    # Defensive → Cautious (0.00-0.40 → 0.40-0.60)
    if current_trust < 0.40 and current_trust + raw_delta > 0.40:
        return min(raw_delta, 0.10)  # Max +0.10 per turn when crossing

    # Cautious → Opening (0.40-0.60 → 0.60-0.80)
    elif 0.40 <= current_trust < 0.60 and current_trust + raw_delta > 0.60:
        return min(raw_delta, 0.08)  # Max +0.08 per turn

    # Opening → Trusting (0.60-0.80 → 0.80-1.00)
    elif 0.60 <= current_trust < 0.80 and current_trust + raw_delta > 0.80:
        return min(raw_delta, 0.06)  # Max +0.06 per turn (hardest barrier)

    return raw_delta  # No cap within tier
```

---

## Implementation Steps

### ✅ Step 1: Apply SQL Migration (User Action Required)
```sql
-- Run this in Supabase SQL Editor
\i supabase/0008a_update_trust_deltas_faster.sql
```

### Step 2: Replace trust_configuration_service
```bash
mv src/services/trust_configuration_service.py src/services/trust_configuration_service_OLD.py
mv src/services/trust_configuration_service_v2.py src/services/trust_configuration_service.py
```

### Step 3: Initialize in main.py
```python
# main.py (add after other service initializations)
from src.services.trust_configuration_service import initialize_trust_configuration_service
initialize_trust_configuration_service(_supabase)
```

### Step 4: Update conversation_state.py
- Change `update_with_llm_insights` signature to accept `InteractionContext`
- Update `_calculate_trust_delta_from_db` to call new service with rich parameters
- Add tier transition caps

### Step 5: Update enhanced_persona_service.py Call Site
- Pass `interaction_context` instead of just `empathy_score`

---

## Testing After Upgrade

Run the 5-turn test again:
```bash
python test_5_turns_all_personas.py
```

**Expected Results**:
- Turn 1-2: Defensive tier (0.30-0.40)
- Turn 3-4: Cautious tier (0.40-0.60) ← Should reach by turn 4-5
- Turn 5: Opening tier (0.60+) ← Should reach or be very close

**Success Criteria**:
- Trust increase per excellent+supportive turn: 0.08-0.12 (vs current 0.012-0.015)
- Reach cautious by turn 5-7 (vs current turn 15+)
- No vicious cycles when user is consistently supportive

---

## Files Modified

1. ✅ `supabase/0008a_update_trust_deltas_faster.sql` - CREATED
2. ✅ `src/services/trust_configuration_service_v2.py` - CREATED
3. ⚠️ `src/services/trust_configuration_service.py` - TO BE REPLACED
4. ⚠️ `src/main.py` - ADD INITIALIZATION
5. ⚠️ `src/models/conversation_state.py` - UPDATE SIGNATURE & CALCULATION
6. ⚠️ `src/services/enhanced_persona_service.py` - UPDATE CALL SITE

---

## Risk Assessment

**Low Risk**:
- Database schema unchanged (only UPDATE values)
- Fallback to defaults if new service fails
- Can rollback SQL changes easily

**Medium Risk**:
- Need to update function signatures (breaks compatibility temporarily)
- Need to test thoroughly after upgrade

**Mitigation**:
- Keep OLD services as backups
- Test with all 3 personas before considering complete
- Monitor logs for any trust calculation errors

---

## Next Step

**USER ACTION REQUIRED**: Apply the SQL migration:
```sql
-- Copy/paste contents of supabase/0008a_update_trust_deltas_faster.sql
-- into Supabase SQL Editor and run
```

After that, I can complete steps 2-6 (code changes).
