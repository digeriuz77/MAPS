# MI-MAPS Integration Architecture

## Executive Summary

This document outlines the comprehensive integration architecture for combining structured motivational interviewing (MI) dialogues from the mi-learning-platform with the MAPS application's competency framework. The solution creates a new "MI Practice" module within MAPS that adapts the "choose the best response" pattern while maintaining MAPS' native feel and 4-tier behavioral progression system.

---

## 1. Content Mapping Strategy

### 1.1 MI Techniques to MAPS Competencies Mapping

| MI Technique | MAPS Foundation Skill | MAPS Domain | Behavioral Tier Impact |
|--------------|----------------------|-------------|------------------------|
| **Open Questions** | A6: Rapport Building | 1: Knowing Your Customer | Increases openness, invites disclosure |
| **Complex Reflection** | A2: Self-Awareness | 1: Knowing Your Customer | Deepens trust, shows understanding |
| **Simple Reflection** | A6: Rapport Building | 1: Knowing Your Customer | Maintains connection |
| **Affirmation** | A6: Rapport Building | A: Personal Qualities | Builds trust, increases engagement |
| **Summarization** | B6: Communication | 1: Knowing Your Customer | Consolidates progress |
| **Elicit Change Talk** | C1: Self-Management | 1: Knowing Your Customer | Critical for tier progression |
| **Ask-Share-Ask** | B6: Communication | D: Service Boundaries | Collaborative, respects autonomy |
| **Confrontation** | (Anti-pattern) | - | Triggers resistance, decreases trust |
| **Premature Advice** | (Anti-pattern) | D: Service Boundaries | Violates guidance boundaries |

### 1.2 Dialogue Node to Scenario Mapping

```
MI Learning Platform Structure          MAPS Scenario Structure
------------------------------          -----------------------
dialogueTreeId                          scenario.code
characterName                           persona_config.name
nodes[].text                            persona_config.initial_message
nodes[].npcMood                         persona_config.starting_state
nodes[].choices[]                       scenario.choice_points (NEW)
choices[].technique                     maps_rubric.technique_tags
choices[].rapportScore                  maps_rubric.rapport_impact
choices[].feedback                      feedback_templates
choices[].nextNodeId                    choice_points[].branching
```

### 1.3 Nuance-Focused Design Principles

Instead of "right/wrong" answers, the system evaluates:

1. **Approach Quality Spectrum**
   - Optimal: Demonstrates multiple MAPS competencies simultaneously
   - Good: Shows solid foundational skills
   - Adequate: Meets minimum standards
   - Suboptimal: Misses opportunities or triggers mild resistance
   - Counterproductive: Triggers significant resistance or violates boundaries

2. **Contextual Appropriateness**
   - Same technique rated differently based on persona's current tier state
   - What works for "trusting" may not work for "defensive"
   - Timing and sequencing matters

3. **Exploratory vs. Directive Continuum**
   - MI Practice module emphasizes exploratory approaches
   - Learners discover through consequences, not labels
   - Feedback describes effects, not technique names

---

## 2. Data Model Extensions

### 2.1 New Tables

#### `mi_practice_modules` - Structured Dialogue Scenarios

```sql
CREATE TABLE mi_practice_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL, -- e.g., "mi-explore-resistance-001"
    title VARCHAR(200) NOT NULL,
    
    -- Categorization
    mi_focus_area VARCHAR(100), -- "Building Rapport", "Exploring Resistance", "Action Planning"
    difficulty_level VARCHAR(20), -- "beginner", "intermediate", "advanced"
    estimated_minutes INT DEFAULT 5,
    
    -- Learning design
    learning_objective TEXT NOT NULL,
    scenario_context TEXT NOT NULL, -- Background situation
    
    -- Persona configuration (JSONB)
    persona_config JSONB NOT NULL,
    
    -- Dialogue structure (JSONB) - ADAPTED from mi-learning-platform
    dialogue_structure JSONB NOT NULL,
    
    -- MAPS alignment
    target_competencies TEXT[] NOT NULL, -- ["A6", "B6", "1.2.1"]
    maps_rubric JSONB NOT NULL,
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_mi_modules_focus ON mi_practice_modules(mi_focus_area);
CREATE INDEX idx_mi_modules_difficulty ON mi_practice_modules(difficulty_level);
CREATE INDEX idx_mi_modules_active ON mi_practice_modules(is_active) WHERE is_active = TRUE;
```

**dialogue_structure JSON Schema:**
```json
{
  "startNodeId": "node_1",
  "nodes": {
    "node_1": {
      "id": "node_1",
      "personaText": "I'm not sure why we're meeting...",
      "personaMood": "defensive_guarded",
      "themes": ["Work Performance", "Trust"],
      "choicePoints": [
        {
          "id": "cp_1a",
          "optionText": "Thanks for coming. I wanted to check in about how things are going.",
          "techniqueTags": ["open_question", "rapport_building"],
          "competencyLinks": ["A6", "B6"],
          "rapportImpact": 1,
          "resistanceImpact": -1,
          "feedback": {
            "immediate": "Starting with appreciation and an open invitation helps establish safety.",
            "learningNote": "Open questions at the start invite the person to share their perspective."
          },
          "nextNodeId": "node_2_open",
          "explorationDepth": "surface"
        },
        {
          "id": "cp_1b",
          "optionText": "I've noticed some changes in your engagement recently.",
          "techniqueTags": ["observation", "confronting"],
          "competencyLinks": ["A2"],
          "rapportImpact": -1,
          "resistanceImpact": 2,
          "feedback": {
            "immediate": "Starting with observations can feel evaluative before rapport is established.",
            "learningNote": "Consider building connection before raising concerns."
          },
          "nextNodeId": "node_2_defensive",
          "explorationDepth": "surface"
        }
      ]
    }
  }
}
```

#### `mi_practice_attempts` - User Progress Tracking

```sql
CREATE TABLE mi_practice_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    module_id UUID NOT NULL REFERENCES mi_practice_modules(id) ON DELETE CASCADE,
    
    -- Timing
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP NULL,
    
    -- Progress tracking
    current_node_id VARCHAR(50),
    path_taken TEXT[] DEFAULT '{}', -- Array of choice point IDs
    
    -- State tracking
    current_rapport_score INT DEFAULT 0,
    current_resistance_level INT DEFAULT 5, -- 1-10 scale
    persona_tier_state VARCHAR(20) DEFAULT 'defensive', -- defensive, cautious, opening, trusting
    
    -- Attempt data
    choices_made JSONB DEFAULT '[]',
    /* Structure:
    [
      {
        "nodeId": "node_1",
        "choicePointId": "cp_1a",
        "chosenAt": "2026-01-31T10:00:00Z",
        "rapportImpact": 1,
        "resistanceImpact": -1,
        "techniquesUsed": ["open_question"],
        "competenciesDemonstrated": ["A6", "B6"]
      }
    ]
    */
    
    -- Final assessment
    completion_status VARCHAR(50), -- "completed", "abandoned", "max_turns"
    final_scores JSONB,
    /* Structure:
    {
      "overallScore": 7.5,
      "competencyScores": {
        "A6": 8.0,
        "B6": 7.0,
        "1.2.1": 7.5
      },
      "techniqueCounts": {
        "open_question": 3,
        "reflection": 2,
        "affirmation": 1
      },
      "resistanceTriggered": 1,
      "rapportBuilt": true
    }
    */
    
    -- Learning analytics
    insights_generated JSONB DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_mi_attempts_user ON mi_practice_attempts(user_id);
CREATE INDEX idx_mi_attempts_module ON mi_practice_attempts(module_id);
CREATE INDEX idx_mi_attempts_completed ON mi_practice_attempts(completed_at) WHERE completed_at IS NOT NULL;
CREATE INDEX idx_mi_attempts_user_module ON mi_practice_attempts(user_id, module_id);
```

#### `mi_learning_paths` - Curated Module Sequences

```sql
CREATE TABLE mi_learning_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Path structure
    module_sequence UUID[] NOT NULL, -- Ordered array of mi_practice_modules.id
    
    -- Learning design
    target_audience VARCHAR(100), -- "beginners", "intermediate", "advanced"
    estimated_total_minutes INT,
    
    -- MAPS alignment
    maps_competencies_targeted TEXT[],
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `mi_user_progress` - Aggregated Learning Progress

```sql
CREATE TABLE mi_user_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Overall progress
    modules_completed INT DEFAULT 0,
    modules_attempted INT DEFAULT 0,
    total_practice_minutes INT DEFAULT 0,
    
    -- Competency tracking (aggregated from attempts)
    competency_scores JSONB DEFAULT '{}',
    /* Structure:
    {
      "A6": {"current": 7.5, "trend": "improving", "attempts": 5},
      "B6": {"current": 6.8, "trend": "stable", "attempts": 5},
      "1.2.1": {"current": 7.0, "trend": "improving", "attempts": 3}
    }
    */
    
    -- Technique exposure
    techniques_practiced JSONB DEFAULT '{}',
    /* Structure:
    {
      "open_question": {"count": 15, "avgQuality": 7.2},
      "reflection": {"count": 12, "avgQuality": 6.8},
      "affirmation": {"count": 8, "avgQuality": 7.5}
    }
    */
    
    -- Current learning path
    active_learning_path_id UUID REFERENCES mi_learning_paths(id),
    current_module_index INT DEFAULT 0,
    
    -- Insights (generated periodically)
    learning_insights JSONB DEFAULT '[]',
    
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id)
);
```

### 2.2 Extended Tables (Existing MAPS Tables)

#### Extend `scenarios` table

Add column to link to MI practice modules:

```sql
-- Add to existing scenarios table
ALTER TABLE scenarios ADD COLUMN mi_practice_module_id UUID REFERENCES mi_practice_modules(id);
ALTER TABLE scenarios ADD COLUMN has_structured_dialogue BOOLEAN DEFAULT FALSE;
```

#### Extend `scenario_attempts` table

Add MI-specific tracking:

```sql
-- Add to existing scenario_attempts table
ALTER TABLE scenario_attempts ADD COLUMN mi_module_attempt_id UUID REFERENCES mi_practice_attempts(id);
ALTER TABLE scenario_attempts ADD COLUMN dialogue_path JSONB DEFAULT NULL;
```

---

## 3. API Design

### 3.1 New Endpoints

#### Module Management

```
GET    /api/mi-practice/modules                    # List available modules
GET    /api/mi-practice/modules/{module_id}        # Get module details
GET    /api/mi-practice/modules/{module_id}/start  # Start a new attempt
```

#### Practice Session

```
POST   /api/mi-practice/attempts/{attempt_id}/choose    # Make a choice
GET    /api/mi-practice/attempts/{attempt_id}/state     # Get current state
POST   /api/mi-practice/attempts/{attempt_id}/complete  # Complete attempt
```

#### Progress & Analytics

```
GET    /api/mi-practice/progress                     # Get user's overall progress
GET    /api/mi-practice/progress/competencies        # Get competency breakdown
GET    /api/mi-practice/attempts/{attempt_id}/review # Review completed attempt
GET    /api/mi-practice/insights                     # Get learning insights
```

#### Learning Paths

```
GET    /api/mi-practice/learning-paths               # List available paths
POST   /api/mi-practice/learning-paths/{path_id}/enroll  # Enroll in path
GET    /api/mi-practice/learning-paths/active        # Get active path progress
```

### 3.2 API Specifications

#### GET /api/mi-practice/modules

**Response:**
```json
{
  "modules": [
    {
      "id": "uuid",
      "code": "mi-explore-resistance-001",
      "title": "Exploring Resistance with Jordan",
      "mi_focus_area": "Exploring Resistance",
      "difficulty_level": "intermediate",
      "estimated_minutes": 8,
      "learning_objective": "Practice responding to defensive statements without triggering additional resistance",
      "target_competencies": ["A6", "B6", "1.2.1"],
      "user_attempts": 2,
      "best_score": 7.5,
      "is_completed": false
    }
  ]
}
```

#### POST /api/mi-practice/modules/{module_id}/start

**Response:**
```json
{
  "attempt_id": "uuid",
  "module_id": "uuid",
  "module_code": "mi-explore-resistance-001",
  "module_title": "Exploring Resistance with Jordan",
  "current_state": {
    "node_id": "jordan_start",
    "persona_text": "I'm not sure why we're meeting. Is this about my performance?",
    "persona_mood": "defensive_guarded",
    "rapport_score": 3,
    "resistance_level": 7,
    "tier_state": "defensive"
  },
  "choice_points": [
    {
      "id": "cp_start_1",
      "option_text": "Thanks for coming in. I wanted to check in about how things are going for you.",
      "preview_hint": "Open, appreciative invitation"
    },
    {
      "id": "cp_start_2",
      "option_text": "I've noticed some changes in your engagement recently and wanted to discuss them.",
      "preview_hint": "Direct observation"
    },
    {
      "id": "cp_start_3",
      "option_text": "Yes, I have some concerns about your recent performance we'd need to address.",
      "preview_hint": "Confrontational approach"
    }
  ],
  "learning_objective": "Practice responding to defensive statements without triggering additional resistance"
}
```

#### POST /api/mi-practice/attempts/{attempt_id}/choose

**Request:**
```json
{
  "choice_point_id": "cp_start_1"
}
```

**Response:**
```json
{
  "attempt_id": "uuid",
  "turn_number": 1,
  "choice_made": {
    "choice_point_id": "cp_start_1",
    "techniques_used": ["open_question", "rapport_building"],
    "competencies_demonstrated": ["A6", "B6"],
    "rapport_impact": 1,
    "resistance_impact": -1
  },
  "feedback": {
    "immediate": "Starting with appreciation and an open invitation helps establish safety.",
    "learning_note": "Open questions at the start invite the person to share their perspective.",
    "show_technique": false
  },
  "new_state": {
    "node_id": "jordan_response_open",
    "persona_text": "Well... things have been a bit overwhelming lately, if I'm honest. There's a lot going on.",
    "persona_mood": "cautious_opening",
    "rapport_score": 4,
    "resistance_level": 6,
    "tier_state": "cautious"
  },
  "next_choice_points": [
    {
      "id": "cp_response_1a",
      "option_text": "It sounds like you're juggling a lot right now.",
      "preview_hint": "Reflective response"
    },
    {
      "id": "cp_response_1b",
      "option_text": "What specifically has been feeling overwhelming?",
      "preview_hint": "Exploratory question"
    },
    {
      "id": "cp_response_1c",
      "option_text": "Have you tried prioritizing your tasks better?",
      "preview_hint": "Problem-solving approach"
    }
  ],
  "is_complete": false
}
```

#### GET /api/mi-practice/attempts/{attempt_id}/review

**Response:**
```json
{
  "attempt_id": "uuid",
  "module": {
    "id": "uuid",
    "code": "mi-explore-resistance-001",
    "title": "Exploring Resistance with Jordan"
  },
  "completed_at": "2026-01-31T10:15:00Z",
  "completion_status": "completed",
  "turns_taken": 6,
  "final_scores": {
    "overall": 7.5,
    "competency_scores": {
      "A6": 8.0,
      "B6": 7.0,
      "1.2.1": 7.5
    },
    "technique_counts": {
      "open_question": 3,
      "reflection": 2,
      "affirmation": 1
    }
  },
  "path_review": [
    {
      "turn": 1,
      "node_id": "jordan_start",
      "persona_text": "I'm not sure why we're meeting...",
      "choice_made": {
        "id": "cp_start_1",
        "text": "Thanks for coming in...",
        "techniques": ["open_question"],
        "rapport_impact": 1
      },
      "feedback": "Starting with appreciation and an open invitation helps establish safety.",
      "alternative_choices": [
        {
          "id": "cp_start_2",
          "text": "I've noticed some changes...",
          "why_different": "This observation, while accurate, can feel evaluative before rapport is established."
        }
      ]
    }
  ],
  "insights": [
    "You demonstrated strong rapport-building skills, particularly in the opening turns.",
    "Consider using more complex reflections to deepen understanding.",
    "You successfully navigated Jordan's initial resistance without escalating."
  ],
  "next_recommendations": [
    {
      "module_id": "uuid",
      "code": "mi-deepen-reflection-001",
      "title": "Deepening with Complex Reflections",
      "reason": "Build on your rapport skills with deeper reflection techniques"
    }
  ]
}
```

---

## 4. Frontend Architecture

### 4.1 Page Structure

```
/mi-practice                    # Main landing page
/mi-practice/modules            # Browse all modules
/mi-practice/modules/{id}       # Module detail/start page
/mi-practice/session/{attempt_id}  # Active practice session
/mi-practice/review/{attempt_id}   # Review completed attempt
/mi-practice/progress           # User progress dashboard
/mi-practice/learning-paths     # Available learning paths
```

### 4.2 Component Structure

```
static/
├── mi-practice/
│   ├── mi-practice.html           # Main landing
│   ├── mi-modules.html            # Module browser
│   ├── mi-session.html            # Active session
│   ├── mi-review.html             # Attempt review
│   ├── mi-progress.html           # Progress dashboard
│   ├── mi-learning-paths.html     # Learning paths
│   └── components/
│       ├── mi-choice-card.js      # Choice selection component
│       ├── mi-persona-display.js  # Persona message display
│       ├── mi-feedback-modal.js   # Feedback display
│       ├── mi-progress-bar.js     # Session progress
│       ├── mi-competency-badge.js # Competency indicator
│       └── mi-path-timeline.js    # Learning path visualization
```

### 4.3 Key Components

#### MIChoiceCard Component

```javascript
// Choice card with nuance indicators (not right/wrong labels)
class MIChoiceCard extends HTMLElement {
  // Properties:
  // - choiceId: string
  // - optionText: string
  // - previewHint: string (subtle cue about approach style)
  // - isSelected: boolean
  // - isRevealed: boolean (after selection)
  
  // Visual states:
  // - Default: Neutral card with preview hint
  // - Hover: Slight elevation, hint becomes more visible
  // - Selected: Highlighted, waiting for feedback
  // - Revealed: Shows outcome with contextual feedback (no "correct/incorrect" label)
}
```

#### MIPersonaDisplay Component

```javascript
// Displays persona message with mood/context
class MIPersonaDisplay extends HTMLElement {
  // Properties:
  // - personaName: string
  // - message: string
  // - mood: string (affects visual styling)
  // - tierState: string (defensive, cautious, opening, trusting)
  // - themes: string[]
  
  // Visual indicators:
  // - Mood-based color accents (subtle)
  // - Tier state progression visualization
  // - Theme tags
}
```

#### MIFeedbackModal Component

```javascript
// Shows feedback without explicit technique labels
class MIFeedbackModal extends HTMLElement {
  // Properties:
  // - immediateFeedback: string (what happened)
  // - learningNote: string (why it matters)
  // - showTechnique: boolean (false by default)
  // - techniqueName: string (only if showTechnique is true)
  // - nextOptions: ChoiceOption[]
  
  // Design principles:
  // - Focus on effects and consequences
  // - Describe what the persona experienced
  // - Connect to MAPS competencies implicitly
}
```

### 4.4 State Management

```javascript
// Session state structure
const miSessionState = {
  attemptId: string,
  moduleId: string,
  currentNode: {
    id: string,
    personaText: string,
    mood: string,
    tierState: string
  },
  choicePoints: ChoicePoint[],
  sessionMetrics: {
    turnsTaken: number,
    rapportScore: number,
    resistanceLevel: number,
    competenciesDemonstrated: string[],
    techniquesUsed: object
  },
  history: TurnHistory[],
  isComplete: boolean
};
```

---

## 5. Integration Points

### 5.1 Integration with Existing MAPS Services

```
┌─────────────────────────────────────────────────────────────────┐
│                    MI Practice Module                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │ MI Practice  │──────│   Existing   │──────│   Existing   │  │
│  │   Services   │      │   Services   │      │   Database   │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                     │                     │          │
│         │                     │                     │          │
│         ▼                     ▼                     ▼          │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                    Integration Layer                      │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ • mi_response_mapper (behavioral cues)                   │ │
│  │ • behavioral_tier_service (tier progression)             │ │
│  │ • maps_analysis_service (competency scoring)             │ │
│  │ • feedback_generator (contextual feedback)               │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Service Integration Details

#### MIResponseMapper Integration

The existing [`MIResponseMapper`](src/services/mi_response_mapper.py:1) is used to:
- Map chosen options to behavioral cues for persona responses
- Determine how the persona should react based on the technique used
- Maintain consistency with existing scenario pipeline

#### BehavioralTierService Integration

The existing [`BehavioralTierService`](src/services/behavioral_tier_service.py:1) provides:
- Tier state management (defensive → cautious → opening → trusting)
- Action pattern distributions for persona responses
- Resistance level tracking

#### MAPSAnalysisService Integration

The existing [`MAPSAnalysisService`](src/services/analysis/maps_analysis_service.py:1) is used for:
- Post-session comprehensive analysis
- Competency scoring against MAPS framework
- Pattern identification across multiple attempts

### 5.3 Data Flow

```
User selects choice
       │
       ▼
┌──────────────────┐
│  POST /choose    │
│  Create turn     │
│  record          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  MIResponseMapper│
│  → behavioral cue│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Update persona  │
│  state (tier,    │
│  resistance)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Get next node   │
│  based on choice │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Generate        │
│  contextual      │
│  feedback        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Return updated  │
│  state + choices │
└──────────────────┘
```

---

## 6. Scoring & Feedback System

### 6.1 Scoring Philosophy

**No Binary Right/Wrong** - Instead:
- **Spectrum scoring**: 1-10 scale for quality
- **Context-dependent**: Same choice rated differently based on state
- **Competency-based**: Scored against MAPS framework
- **Progressive**: Rewards exploration and learning from suboptimal choices

### 6.2 Scoring Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Rapport Building** | 25% | Impact on trust and connection |
| **Resistance Management** | 25% | Ability to navigate defensiveness |
| **Exploration Depth** | 20% | Moving from surface to deeper issues |
| **MAPS Competency** | 20% | Alignment with target competencies |
| **Timing/Sequencing** | 10% | Appropriateness given conversation state |

### 6.3 Feedback Design Principles

1. **Describe, Don't Label**
   - ❌ "You used an open question"
   - ✅ "Your invitation gave Jordan space to share what was on their mind"

2. **Show Consequences**
   - ❌ "Good technique"
   - ✅ "Jordan seemed to relax a bit and opened up about feeling overwhelmed"

3. **Connect to Experience**
   - ❌ "Reflection builds rapport"
   - ✅ "When you acknowledged Jordan's challenge, they seemed to feel understood"

4. **Offer Alternatives (in review)**
   - Show what other paths might have looked like
   - Explain differences without judgment

### 6.4 Feedback Timing Options

```javascript
// Configurable feedback frequency
const feedbackModes = {
  IMMEDIATE: 'immediate',     // After every choice
  KEY_MOMENTS: 'key_moments', // After significant state changes
  END_ONLY: 'end_only',       // Only at completion
  ON_DEMAND: 'on_demand'      // User requests feedback
};
```

### 6.5 Competency Tracking

```javascript
// Competency scoring structure
const competencyScore = {
  competencyId: 'A6',  // MAPS competency code
  score: 7.5,          // 0-10 scale
  confidence: 0.8,     // scoring confidence
  evidence: [
    {
      turn: 1,
      choiceId: 'cp_start_1',
      technique: 'open_question',
      impact: 'positive'
    }
  ],
  trend: 'improving'   // improving, stable, declining
};
```

---

## 7. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Landing    │  │   Module     │  │   Session    │  │   Review     │        │
│  │    Page      │  │   Browser    │  │    Page      │  │    Page      │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                 │                 │                 │                │
│         └─────────────────┴─────────────────┴─────────────────┘                │
│                                    │                                           │
│                         ┌──────────▼──────────┐                                │
│                         │   MI Practice SPA   │                                │
│                         │   (mi-session.js)   │                                │
│                         └──────────┬──────────┘                                │
└────────────────────────────────────┼────────────────────────────────────────────┘
                                     │
                                     │ HTTP/WebSocket
                                     │
┌────────────────────────────────────┼────────────────────────────────────────────┐
│                              API LAYER                                           │
│                         ┌──────────▼──────────┐                                │
│                         │  /api/mi-practice/* │                                │
│                         │    (New Routes)     │                                │
│                         └──────────┬──────────┘                                │
│                                    │                                           │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐ │
│  │                         SERVICE LAYER                                     │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │ │
│  │  │   MI Module  │  │   MI Attempt │  │   MI Choice  │  │   MI Review  │  │ │
│  │  │   Service    │  │   Service    │  │   Service    │  │   Service    │  │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │ │
│  │         │                 │                 │                 │         │ │
│  │         └─────────────────┴─────────────────┴─────────────────┘         │ │
│  │                                    │                                      │ │
│  │                    ┌───────────────▼───────────────┐                      │ │
│  │                    │   Existing Service Integration │                      │ │
│  │                    │  ┌─────────────────────────┐  │                      │ │
│  │                    │  │  MIResponseMapper       │  │                      │ │
│  │                    │  │  BehavioralTierService  │  │                      │ │
│  │                    │  │  FeedbackGenerator      │  │                      │ │
│  │                    │  │  MAPSAnalysisService    │  │                      │ │
│  │                    │  └─────────────────────────┘  │                      │ │
│  │                    └───────────────────────────────┘                      │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ SQL/JSONB
                                     │
┌────────────────────────────────────┼────────────────────────────────────────────┐
│                         DATABASE LAYER                                           │
│                         ┌──────────▼──────────┐                                │
│                         │     Supabase        │                                │
│                         │   (PostgreSQL)      │                                │
│                         └──────────┬──────────┘                                │
│                                    │                                           │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐ │
│  │                         TABLES                                            │ │
│  │  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐          │ │
│  │  │ mi_practice_     │ │ mi_practice_     │ │ mi_learning_     │          │ │
│  │  │ modules          │ │ attempts         │ │ paths            │          │ │
│  │  └──────────────────┘ └──────────────────┘ └──────────────────┘          │ │
│  │  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐          │ │
│  │  │ mi_user_         │ │ scenarios        │ │ scenario_        │          │ │
│  │  │ progress         │ │ (extended)       │ │ attempts         │          │ │
│  │  └──────────────────┘ └──────────────────┘ └──────────────────┘          │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Content Structure for Dialogues

### 8.1 Module Definition Structure

```json
{
  "moduleDefinition": {
    "code": "mi-explore-resistance-001",
    "title": "Exploring Resistance with Jordan",
    "version": "1.0",
    
    "metadata": {
      "author": "MAPS Content Team",
      "reviewedBy": "MI Expert",
      "createdAt": "2026-01-15",
      "difficulty": "intermediate",
      "estimatedMinutes": 8
    },
    
    "learningDesign": {
      "objective": "Practice responding to defensive statements without triggering additional resistance",
      "prerequisites": ["mi-rapport-basics-001"],
      "successCriteria": {
        "minTurns": 4,
        "maxTurns": 10,
        "requiredCompetencies": ["A6", "B6"],
        "minRapportScore": 5,
        "maxResistanceTriggers": 2
      }
    },
    
    "mapsAlignment": {
      "targetCompetencies": ["A6", "B6", "1.2.1", "1.2.3"],
      "foundationSkills": ["rapport_building", "communication"],
      "technicalDomains": ["knowing_your_customer"]
    },
    
    "persona": {
      "name": "Jordan",
      "role": "Team member, 2 years in role",
      "background": "Recently been quieter in meetings, missing some deadlines",
      "initialMindset": "Defensive and guarded - worried this is a performance review",
      "personalityTraits": ["conscientious", "prideful", "overwhelmed"],
      "startingState": {
        "tier": "defensive",
        "rapport": 3,
        "resistance": 7
      }
    },
    
    "dialogueTree": {
      "startNodeId": "jordan_start",
      "nodes": {
        "jordan_start": {
          "id": "jordan_start",
          "personaText": "I'm not sure why we're meeting. Is this about my performance?",
          "mood": "defensive_guarded",
          "context": "Jordan enters with arms crossed, sits at edge of seat",
          "themes": ["performance_anxiety", "trust_issues"],
          "choicePoints": [
            {
              "id": "cp_start_open",
              "optionText": "Thanks for coming in. I wanted to check in about how things are going for you.",
              "techniqueProfile": {
                "primary": "open_question",
                "secondary": ["rapport_building"],
                "competencies": ["A6", "B6"]
              },
              "impact": {
                "rapportDelta": 1,
                "resistanceDelta": -1,
                "tierProgression": 0.2
              },
              "feedback": {
                "immediate": "Starting with appreciation and an open invitation helps establish safety.",
                "learningNote": "Open questions at the start invite the person to share their perspective.",
                "alternativeConsideration": "Starting with observations might have put Jordan more on guard."
              },
              "nextNodeId": "jordan_cautious_open",
              "explorationDepth": "surface"
            },
            {
              "id": "cp_start_direct",
              "optionText": "I've noticed some changes in your engagement recently and wanted to discuss them.",
              "techniqueProfile": {
                "primary": "observation",
                "secondary": ["direct"],
                "competencies": ["A2"]
              },
              "impact": {
                "rapportDelta": -1,
                "resistanceDelta": 2,
                "tierProgression": -0.1
              },
              "feedback": {
                "immediate": "Jordan seems to tense up. Starting with observations can feel evaluative.",
                "learningNote": "Consider building connection before raising concerns.",
                "alternativeConsideration": "An open invitation might have helped Jordan feel safer first."
              },
              "nextNodeId": "jordan_defensive_escalate",
              "explorationDepth": "surface"
            }
          ]
        },
        
        "jordan_cautious_open": {
          "id": "jordan_cautious_open",
          "personaText": "Well... things have been a bit overwhelming lately, if I'm honest. There's a lot going on.",
          "mood": "cautious_opening",
          "context": "Jordan relaxes slightly, makes brief eye contact",
          "themes": ["workload", "stress"],
          "choicePoints": [
            // ... more choices
          ]
        }
      }
    },
    
    "reviewContent": {
      "keyLearningPoints": [
        "Starting with open invitations builds safety",
        "Defensive responses often mask underlying concerns",
        "Timing matters - rapport before challenge"
      ],
      "commonPitfalls": [
        "Starting with observations or concerns",
        "Moving to problem-solving too quickly",
        "Not acknowledging the person's experience"
      ],
      "practiceRecommendations": [
        "mi-deepen-reflection-001",
        "mi-action-planning-001"
      ]
    }
  }
}
```

### 8.2 Content Creation Guidelines

1. **Persona Authenticity**
   - Base personas on real case studies
   - Include specific behavioral cues
   - Maintain consistency across tier states

2. **Choice Design**
   - 3-4 choices per node (optimal cognitive load)
   - Avoid obviously "wrong" choices
   - Show spectrum of approaches, not binary right/wrong

3. **Feedback Crafting**
   - Describe effects, not techniques
   - Use persona's name and reactions
   - Connect to MAPS competencies implicitly

4. **Learning Progression**
   - Start with rapport-building scenarios
   - Progress to resistance navigation
   - Culminate in action planning

---

## 9. Implementation Phases

### Phase 1: Core Infrastructure
- Create database tables
- Build basic API endpoints
- Implement choice processing

### Phase 2: Content & UI
- Create initial module library
- Build session interface
- Implement feedback display

### Phase 3: Integration
- Connect to existing MAPS services
- Implement competency tracking
- Build progress dashboard

### Phase 4: Enhancement
- Learning paths
- Advanced analytics
- Peer comparison features

---

## 10. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Module Completion Rate | >70% | attempts completed / attempts started |
| Competency Score Improvement | +20% | compare first vs latest attempts |
| User Engagement | 3+ modules/week | active users metric |
| Learning Satisfaction | >4.0/5.0 | post-session survey |
| MAPS Alignment Accuracy | >85% | expert review of competency mapping |

---

## Appendix A: MI Technique to MAPS Competency Reference

| MI Technique | MAPS Competency | Evidence Indicator |
|--------------|-----------------|-------------------|
| Open Question | A6, B6, 1.2.1 | Invites elaboration |
| Complex Reflection | A2, A6, 1.2.3 | Shows understanding of underlying meaning |
| Affirmation | A6, C1 | Acknowledges strengths |
| Summarization | B6, 1.2.6 | Consolidates understanding |
| Eliciting Change Talk | 1.2.3, C1 | Explores motivation |
| Ask-Share-Ask | B6, D1 | Collaborative information sharing |

---

## Appendix B: JSON Schema Definitions

See inline JSON schemas in Section 2.1 for complete structure definitions.
