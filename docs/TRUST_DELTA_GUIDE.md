# Trust Delta Configuration Guide

## Overview

The trust system uses a **rich multiplier formula** to calculate trust changes based on four interaction dimensions:

```
delta = (base_quality_delta + trajectory_adjustment) × empathy_multiplier × approach_modifier
```

All configuration is stored in the `trust_configuration` table and can be adjusted without code deployment.

---

## Configuration Parameters

### 1. Quality Deltas (Base Trust Change)

**Database column**: `quality_deltas` (JSONB)

Maps interaction quality to base trust change:

```json
{
  "poor": -0.02,      // Hostile, dismissive, unhelpful
  "adequate": 0.01,   // Neutral, basic interaction
  "good": 0.04,       // Helpful, respectful, engaged
  "excellent": 0.06   // Highly empathetic, collaborative, insightful
}
```

**What to adjust:**
- **Increase excellent/good**: Faster trust building with positive interactions
- **Decrease poor penalty**: Reduce vicious cycle risk (personas forgive minor missteps)
- **Increase poor penalty**: Make personas more sensitive to disrespect

**Expected impact:**
- Changing `excellent` from 0.06 to 0.08: ~33% faster trust progression
- Changing `poor` from -0.02 to -0.04: Doubles trust loss from bad interactions

---

### 2. Empathy Multipliers

**Database column**: `empathy_multipliers` (JSONB)

Multiplies the delta based on emotional tone detected:

```json
{
  "hostile": 0.3,              // User is aggressive, dismissive, or rude
  "neutral": 1.0,              // No strong emotional tone
  "supportive": 1.6,           // User shows empathy, validation, understanding
  "deeply_empathetic": 2.0     // User demonstrates exceptional emotional intelligence
}
```

**What to adjust:**
- **Increase supportive multiplier**: Reward empathetic users more
- **Decrease hostile multiplier**: Soften negative impact (but keep above 0 to avoid reversing direction)
- **Add "deeply_empathetic"**: Recognize exceptional empathy (2.0-2.5x)

**Expected impact:**
- Changing `supportive` from 1.6 to 2.0: +25% trust gain when user is empathetic
- Changing `hostile` from 0.3 to 0.5: Reduces trust loss from hostile interactions by 40%

**Current behavior with hostile tone:**
- **YES, system applies negative deltas**: If `quality = "poor"` and `empathy_tone = "hostile"`:
  - Base: -0.02 (poor)
  - × 0.3 (hostile) = -0.006
  - Result: Trust decreases, but less dramatically than old system

---

### 3. Trajectory Adjustments (Consistency Bonus)

**Database column**: `trajectory_adjustments` (JSONB)

Adds bonus/penalty based on recent trust direction:

```json
{
  "declining": -0.01,     // Trust has been falling (user losing rapport)
  "stable": 0.00,         // Trust unchanged for several turns
  "building": 0.02,       // Trust consistently increasing (positive momentum)
  "breakthrough": 0.04    // Major trust leap just occurred
}
```

**What to adjust:**
- **Increase building bonus**: Reward consistent positive interactions more
- **Reduce declining penalty**: Prevent vicious cycles
- **Add breakthrough tier**: Recognize major trust milestones

**Expected impact:**
- Changing `building` from 0.02 to 0.03: Adds +50% bonus for consistent good interactions
- This rewards users who maintain empathy over time vs. one-off good turns

---

### 4. Approach Modifiers (Communication Style)

**Database column**: `approach_modifiers` (JSONB)

Multiplies delta based on how the user communicates:

```json
{
  "directive": 1.2,       // Telling, instructing (some personas like Terry appreciate this)
  "questioning": 1.0,     // Asking questions, exploring
  "curious": 1.3,         // Genuine interest, non-judgmental inquiry
  "collaborative": 1.9,   // "Let's work on this together"
  "supportive": 1.7       // "I'm here to help, what do you need?"
}
```

**What to adjust:**
- **Increase collaborative**: Encourage partnership-based interactions
- **Persona-specific tuning**: Terry might prefer `directive: 1.5`, Mary prefers `supportive: 2.0`
- **Add "reflective"**: Recognize motivational interviewing techniques

**Expected impact:**
- Changing `collaborative` from 1.9 to 2.2: +16% trust gain when user partners with persona
- This is where you prevent dismissive behavior: If user is collaborative, persona responds positively

---

## Persona-Specific Configurations

### Terry (Efficient, Direct, Values Respect)

```sql
UPDATE trust_configuration SET
  quality_deltas = '{"poor": -0.02, "adequate": 0.01, "good": 0.04, "excellent": 0.06}'::jsonb,
  empathy_multipliers = '{"hostile": 0.3, "neutral": 1.0, "supportive": 1.6}'::jsonb,
  approach_modifiers = '{"directive": 1.2, "collaborative": 1.9, "supportive": 1.7}'::jsonb
WHERE persona_id = 'terry';
```

**Character traits:**
- Appreciates directness (directive: 1.2 vs. Mary's 0.6)
- Values collaboration over hand-holding
- Moderate empathy response (supportive: 1.6 vs. Jan's 2.0)

### Mary (Stressed Parent, Needs Empathy)

```sql
UPDATE trust_configuration SET
  quality_deltas = '{"poor": -0.02, "adequate": 0.01, "good": 0.03, "excellent": 0.05}'::jsonb,
  empathy_multipliers = '{"hostile": 0.2, "neutral": 1.0, "supportive": 1.8}'::jsonb,
  approach_modifiers = '{"directive": 0.6, "collaborative": 1.8, "supportive": 2.0}'::jsonb
WHERE persona_id = 'mary';
```

**Character traits:**
- Very sensitive to hostility (hostile: 0.2 - lowest of all personas)
- Needs empathy and support (supportive approach: 2.0)
- Dislikes being told what to do (directive: 0.6)

### Jan (Uncertain, Needs Validation)

```sql
UPDATE trust_configuration SET
  quality_deltas = '{"poor": -0.03, "adequate": 0.01, "good": 0.04, "excellent": 0.07}'::jsonb,
  empathy_multipliers = '{"hostile": 0.2, "neutral": 1.0, "supportive": 2.0}'::jsonb,
  approach_modifiers = '{"directive": 0.5, "collaborative": 2.0, "supportive": 2.2}'::jsonb
WHERE persona_id = 'jan';
```

**Character traits:**
- Highest trust gain potential (excellent: 0.07)
- Very responsive to empathy (supportive: 2.0)
- Most collaborative (collaborative: 2.0, supportive: 2.2)
- Most fragile (poor: -0.03, directive: 0.5)

---

## Trust Progression Examples

### Scenario 1: Excellent Empathetic Interaction (Terry)

**User message**: "I appreciate your directness. Can you tell me more about what's been challenging?"

**Analysis**:
- Quality: `excellent` (base: +0.06)
- Empathy: `supportive` (mult: 1.6x)
- Approach: `collaborative` (mult: 1.9x)
- Trajectory: `building` (bonus: +0.02)

**Calculation**:
```
delta = (0.06 + 0.02) × 1.6 × 1.9
      = 0.08 × 1.6 × 1.9
      = 0.243
```

**Result**: Trust increases by **+0.15** (capped at max_delta_per_turn)

**Tier progression**: 1 turn can cross from defensive (0.35) to cautious (0.50)!

---

### Scenario 2: Hostile Directive Interaction (Mary)

**User message**: "Mary, you need to get your performance back on track. What's your plan?"

**Analysis**:
- Quality: `poor` (base: -0.02)
- Empathy: `hostile` (mult: 0.2x)
- Approach: `directive` (mult: 0.6x)
- Trajectory: `stable` (bonus: 0.00)

**Calculation**:
```
delta = (-0.02 + 0.00) × 0.2 × 0.6
      = -0.02 × 0.2 × 0.6
      = -0.0024
```

**Result**: Trust decreases by **-0.002** (minimal damage)

**Why it's small**: The multipliers prevent vicious cycles. Even hostile interactions don't destroy trust catastrophically.

---

### Scenario 3: Adequate Neutral Interaction

**User message**: "Hi, how are you today?"

**Analysis**:
- Quality: `adequate` (base: +0.01)
- Empathy: `neutral` (mult: 1.0x)
- Approach: `questioning` (mult: 1.0x)
- Trajectory: `stable` (bonus: 0.00)

**Calculation**:
```
delta = (0.01 + 0.00) × 1.0 × 1.0
      = 0.01
```

**Result**: Trust increases by **+0.01** (slow but safe progress)

---

## Trust Tiers and Behavioral Changes

### Defensive Tier (0.00 - 0.40)

**Current trust range**: Personas start here (0.30)

**Behavior**:
- Guarded, surface-level responses
- Task-focused, avoids personal topics
- Brief answers, minimal elaboration
- **Planning willingness**: LOW - will deflect or give vague commitments

**Knowledge access**: Only basic facts (importance ≤ 0.4)

**Sample response** (Terry):
> "Everything's fine. Just busy with the usual tasks. What's your concrete ask?"

---

### Cautious Tier (0.40 - 0.60)

**Reached after**: 2-4 good interactions with supportive approach

**Behavior**:
- Testing safety, sharing surface-level concerns
- Mentions challenges but stays guarded about emotions
- More willing to engage in conversation
- **Planning willingness**: MODERATE - will discuss options but hesitant to commit

**Knowledge access**: Work challenges, general stressors (importance ≤ 0.6)

**Sample response** (Mary):
> "Things have been tough lately with work and childcare. I was doing well last year, but now it feels overwhelming."

**Planning behavior**: "I guess we could look at some options, but I'm not sure what would help."

---

### Opening Tier (0.60 - 0.80)

**Reached after**: 6-8 excellent/good interactions

**Behavior**:
- Sharing deeper concerns and emotions
- Willing to admit vulnerabilities
- Asking for input and guidance
- **Planning willingness**: HIGH - actively explores solutions

**Knowledge access**: Personal struggles, self-doubt, vulnerabilities (importance ≤ 0.8)

**Sample response** (Terry):
> "I appreciate you asking. I think it would be helpful to focus on improving communication within the team. I've received feedback about being too direct."

**Planning behavior**:
- **YES**: "Any ideas on how we can approach this would be valuable."
- Willing to collaborate on action plans
- Open to trying new approaches

---

### Trusting Tier (0.80 - 1.00)

**Reached after**: 10-12 excellent interactions with consistent empathy

**Behavior**:
- Full vulnerability and openness
- Actively partners in problem-solving
- Shares root causes and deeper emotions
- **Planning willingness**: VERY HIGH - co-creates action plans

**Knowledge access**: All memories including sensitive topics (importance ≤ 1.0)

**Sample response** (Jan):
> "I've been struggling with imposter syndrome. I don't feel like I belong here, and every mistake confirms that feeling. Can we work on building my confidence?"

**Planning behavior**:
- **FULL COLLABORATION**: "Let's create a plan together"
- Suggests specific actions
- Takes ownership of next steps
- Follows through on commitments

---

## Does the System Handle Offensive/Hostile Interactions?

### YES - Multi-Layer Response System

#### 1. **Negative Trust Deltas Applied**

When user is hostile or offensive:

```
quality = "poor" (base: -0.02)
empathy_tone = "hostile" (mult: 0.3x)
approach = "directive" (mult: 0.6-1.2x depending on persona)

delta = -0.02 × 0.3 × 0.6 = -0.0036
```

**Result**: Trust decreases, but gradually (prevents ragequit)

#### 2. **Behavioral State Changes**

The system doesn't have an explicit "offended mode", but personas react behaviorally:

**At defensive tier with hostile interaction**:
- `emotional_availability`: `closed`
- `defensiveness_level`: `high`
- `information_sharing`: `resistant`
- `tone_adjustment`: `cold`

**Sample response to hostile user** (Terry at 0.25 trust):
> "I need to get back to work. If there's a specific task you need, send it via email."

**At cautious tier with hostile interaction**:
- Persona may **drop back to defensive behaviors**
- Trust trajectory changes to `declining`
- Future responses become more guarded

#### 3. **Character Consistency Validation**

The `character_consistency_service` can flag responses that are too accommodating:

**Forbidden response** (if user is hostile):
> "I'm sorry you feel that way. Let me help you immediately!" ❌

**Correct response**:
> "I'm focused on my work right now. If you have specific feedback, please share it constructively." ✅

---

## Planning Willingness by Trust Level

### Question: "Does the system allow personas to move towards collaborative planning?"

**YES - This is the core progression:**

| Trust Level | Planning Behavior | Example Response |
|-------------|------------------|------------------|
| **0.00-0.40 (Defensive)** | Deflects planning | "I'm just focused on my tasks right now." |
| **0.40-0.60 (Cautious)** | Acknowledges need but hesitant | "Maybe we could look at some options, but I'm not sure..." |
| **0.60-0.80 (Opening)** | Actively explores solutions | "That's a good idea. How would we approach this?" |
| **0.80-1.00 (Trusting)** | Co-creates action plans | "Let's create a plan together. I think if we start with X, then Y..." |

### Implementation in Knowledge Tiers

The `character_knowledge_tiers` table controls this:

```sql
-- Defensive tier (0.00-0.40)
{
  "planning_willingness": "deflects or gives vague commitments",
  "action_orientation": "passive, waits for instructions",
  "collaboration_style": "resistant, prefers to work alone"
}

-- Opening tier (0.60-0.80)
{
  "planning_willingness": "actively explores solutions and suggests ideas",
  "action_orientation": "proactive, initiates problem-solving",
  "collaboration_style": "partners in planning, offers suggestions"
}

-- Trusting tier (0.80-1.00)
{
  "planning_willingness": "co-creates detailed action plans with enthusiasm",
  "action_orientation": "takes ownership, follows through on commitments",
  "collaboration_style": "full partnership, shares leadership"
}
```

### Behavioral Adjustments

The `enhanced_persona_service` applies these based on trust:

**Defensive (0.30 trust)**:
```python
{
    'response_length': 'brief',
    'emotional_availability': 'closed',
    'information_sharing': 'resistant',
    'planning_engagement': 'minimal'  # Won't commit to plans
}
```

**Opening (0.70 trust)**:
```python
{
    'response_length': 'detailed',
    'emotional_availability': 'open',
    'information_sharing': 'generous',
    'planning_engagement': 'active'  # Engages in planning
}
```

**Trusting (0.85 trust)**:
```python
{
    'response_length': 'comprehensive',
    'emotional_availability': 'vulnerable',
    'information_sharing': 'unrestricted',
    'planning_engagement': 'collaborative_leadership'  # Co-leads planning
}
```

---

## Adjustment Recommendations

### To Speed Up Trust Building (More Forgiving)

```sql
UPDATE trust_configuration SET
  quality_deltas = '{"poor": -0.01, "adequate": 0.02, "good": 0.05, "excellent": 0.08}'::jsonb,
  empathy_multipliers = '{"hostile": 0.5, "neutral": 1.0, "supportive": 2.0}'::jsonb,
  approach_modifiers = '{"collaborative": 2.5, "supportive": 2.3}'::jsonb
WHERE persona_id = 'terry';
```

**Result**: Reach trusting tier in 6-8 turns instead of 10-12

---

### To Slow Down Trust Building (More Realistic)

```sql
UPDATE trust_configuration SET
  quality_deltas = '{"poor": -0.03, "adequate": 0.005, "good": 0.02, "excellent": 0.04}'::jsonb,
  empathy_multipliers = '{"hostile": 0.2, "neutral": 1.0, "supportive": 1.4}'::jsonb,
  regression_penalty = -0.05
WHERE persona_id = 'mary';
```

**Result**: Requires 15-20 turns to reach trusting tier

---

### To Increase Sensitivity to Hostility

```sql
UPDATE trust_configuration SET
  quality_deltas = '{"poor": -0.05}'::jsonb,  -- 2.5x more damage
  empathy_multipliers = '{"hostile": 0.1}'::jsonb,  -- Even less impact from hostile
  regression_penalty = -0.08  -- Big penalty for trust drops
WHERE persona_id = 'jan';
```

**Result**: One hostile interaction can undo 2-3 good interactions

---

## Testing Your Changes

After adjusting trust configuration:

```bash
# Run 5-turn test
python test_5_turns_all_personas.py

# Check specific persona
python -c "
import requests
resp = requests.post('http://localhost:8000/api/chat/start', json={'persona_id': 'terry'})
data = resp.json()
print(f'Session: {data[\"session_id\"][:8]}')

# Send test messages and observe trust progression
"
```

**Monitor**:
- Trust level changes per turn
- Tier transitions (defensive → cautious → opening → trusting)
- Response quality (are personas too accommodating or too resistant?)
- Planning engagement (do personas start collaborating at appropriate trust levels?)

---

## Summary

✅ **System applies negative deltas for hostile interactions**
✅ **No explicit "offended mode" but behavioral shifts occur**
✅ **Planning willingness increases dramatically with trust**
✅ **Collaborative planning emerges naturally at opening tier (0.60+)**
✅ **Full partnership and action plans at trusting tier (0.80+)**
✅ **All adjustable via database without code deployment**

**Key insight**: The vicious cycle is solved by keeping hostile multipliers above 0 (0.2-0.3) so negative interactions don't compound catastrophically. Users can recover trust with consistent empathy.
