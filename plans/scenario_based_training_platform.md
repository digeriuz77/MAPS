# Implementation Plan: Scenario-Based MI Training Platform

## Overview

This plan outlines the migration from a **conversation-based system** to a **scenario-based micro-training platform**. The key change is making persona responses **emergent** - personas respond naturally to whatever the manager actually says, rather than following predefined paths.

---

## Current Architecture Analysis

### Existing System Flow
```
User → /api/chat/start → conversations table
     → /api/chat/send → enhanced_persona_service → multiple LLM calls
     → analysis → conversation_transcripts table
```

### Key Existing Components
| Component | Location | Purpose |
|-----------|----------|---------|
| `PersonaEngine` | `src/core/persona_engine.py` | Central persona management |
| `EnhancedPersonaService` | `src/services/enhanced_persona_service.py` | Natural empathy assessment |
| `LLMInteractionAnalyzer` | `src/services/llm_interaction_analyzer.py` | Interaction quality analysis |
| `ConversationStateManager` | `src/models/conversation_state.py` | Trust/openness tracking |
| `MAPSAnalysisService` | `src/services/analysis/maps_analysis_service.py` | MAPS rubric scoring |
| `EnhancedChatRoutes` | `src/api/routes/enhanced_chat.py` | Conversation API |

### Current Database Tables
- `enhanced_personas` - Persona configurations
- `conversations` - Conversation metadata
- `conversation_transcripts` - Message history
- `conversation_memories` - Memory storage
- `trust_configuration` - Persona-specific trust deltas

---

## Phase 1: Database Schema Changes

### New Tables to Create

#### 1. `scenarios` - Atomic Training Units

```sql
CREATE TABLE scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL, -- e.g., "close-ambivalent-001"
    title VARCHAR(200) NOT NULL,
    mi_skill_category VARCHAR(100), -- "Closing", "Action Planning", "Change Talk"
    difficulty VARCHAR(20), -- "beginner", "intermediate", "advanced"
    estimated_minutes INT DEFAULT 5,
    
    -- The setup (what situation the persona is in)
    situation TEXT NOT NULL,
    learning_objective TEXT NOT NULL,
    
    -- Persona configuration (JSONB for flexibility)
    persona_config JSONB NOT NULL,
    
    -- Success criteria
    success_criteria JSONB NOT NULL,
    
    -- MAPS scoring rubric
    maps_rubric JSONB NOT NULL,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_scenarios_skill ON scenarios(mi_skill_category);
CREATE INDEX idx_scenarios_difficulty ON scenarios(difficulty);
CREATE INDEX idx_scenarios_code ON scenarios(code);
```

**Persona Config JSON Structure:**
```json
{
    "name": "Jordan",
    "role": "Team member, 2 years in role",
    "current_mindset": "Polite but evasive",
    "personality": "Ambivalent about change...",
    "response_patterns": {
        "to_reflection": "Cautiously agree but add caveats",
        "to_direct_advice": "Polite dismissal",
        "to_confrontation": "Defensive deflection",
        "to_empathy": "Slightly more open",
        "to_autonomy_support": "Most responsive"
    },
    "triggers": {
        "trust_increase": ["Empathy", "Asking permission", "Validating feelings"],
        "trust_decrease": ["Direct advice", "Blame", "Dismissing concerns"],
        "resistance_increase": ["Confrontation", "Should statements", "Fixing"]
    },
    "starting_state": {
        "trust_level": 4,
        "openness_level": 3,
        "resistance_active": true
    }
}
```

#### 2. `scenario_attempts` - User Attempts Tracking

```sql
CREATE TABLE scenario_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    scenario_id UUID NOT NULL REFERENCES scenarios(id),
    
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP NULL,
    
    turn_count INT DEFAULT 0,
    transcript JSONB NOT NULL DEFAULT '[]',
    
    -- Final outcomes
    final_scores JSONB NULL,
    completion_reason VARCHAR(50), -- "success", "abandoned", "time_limit"
    
    -- State tracking
    initial_persona_state JSONB NOT NULL,
    final_persona_state JSONB NULL
);

CREATE INDEX idx_scenario_attempts_user ON scenario_attempts(user_id);
CREATE INDEX idx_scenario_attempts_scenario ON scenario_attempts(scenario_id);
CREATE INDEX idx_scenario_attempts_completed ON scenario_attempts(completed_at) WHERE completed_at IS NOT NULL;
```

#### 3. `learning_paths` - Curated Scenario Sequences

```sql
CREATE TABLE learning_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    target_audience VARCHAR(100), -- "beginners", "intermediate", "managers"
    scenario_sequence UUID[] NOT NULL,
    estimated_total_minutes INT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 4. `user_learning_progress` - User Progress Tracking

```sql
CREATE TABLE user_learning_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    learning_path_id UUID NOT NULL REFERENCES learning_paths(id),
    
    current_scenario_index INT DEFAULT 0,
    completed_scenario_ids UUID[] DEFAULT '{}',
    
    started_at TIMESTAMP DEFAULT NOW(),
    last_activity_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP NULL,
    
    avg_scores JSONB NULL,
    
    UNIQUE(user_id, learning_path_id)
);
```

### Tables to Deprecate (Phase 4)
- `personas` - Replaced by `scenarios.persona_config`
- `conversations` - Replaced by `scenario_attempts`
- `conversation_transcripts` - Now in `scenario_attempts.transcript`

---

## Phase 2: New Service Layer

### Service Architecture

```
                    ┌─────────────────────┐
                    │   ScenarioPipeline  │ ← Core orchestrator
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌─────────────────┐    ┌───────────────────┐
│PersonaResponse│    │Interaction      │    │CompletionChecker  │
│Engine         │    │Analyzer         │    │                   │
└───────┬───────┘    └────────┬────────┘    └─────────┬─────────┘
        │                     │                        │
        │              ┌──────┴──────┐                 │
        │              │FeedbackGen  │                 │
        │              └─────────────┘                 │
        └──────────────────────────────────────────────┘
```

### 2.1 PersonaResponseEngine

**Location:** `src/services/persona_response_engine.py`

```python
from dataclasses import dataclass
from typing import List, Dict, Any
import asyncio

@dataclass
class PersonaState:
    trust_level: int      # 1-10
    openness_level: int   # 1-10
    resistance_active: bool

@dataclass
class PersonaResponse:
    message: str
    updated_state: PersonaState
    reasoning: str = None  # For debugging

class PersonaResponseEngine:
    """Generates contextual, in-character responses"""
    
    def __init__(self, llm_service):
        self.llm = llm_service
    
    async def generate_response(
        self,
        persona_config: Dict[str, Any],
        manager_message: str,
        conversation_history: List[Dict],
        current_state: PersonaState
    ) -> PersonaResponse:
        """
        Core method: Generate authentic persona response
        
        1. Build dynamic prompt with persona config, history, current state
        2. Single LLM call for persona response
        3. Update state based on manager's approach
        """
        prompt = self._build_persona_prompt(
            persona_config, manager_message, conversation_history, current_state
        )
        
        response_text = await self.llm.complete(prompt)
        
        new_state = self._update_state(
            manager_message, response_text, current_state, 
            persona_config["triggers"]
        )
        
        return PersonaResponse(
            message=response_text,
            updated_state=new_state
        )
    
    def _build_persona_prompt(self, config, message, history, state) -> str:
        """Construct rich, contextual prompt for persona"""
        return f"""You are {config['name']}, {config['role']}.

CURRENT SITUATION:
{config['situation']}

YOUR PERSONALITY & MINDSET:
{config['personality']}
{config['current_mindset']}

HOW YOU RESPOND TO DIFFERENT APPROACHES:
{self._format_response_patterns(config['response_patterns'])}

YOUR CURRENT STATE:
- Trust in this manager: {state.trust_level}/10
- Openness to discussion: {state.openness_level}/10
- Currently resistant: {state.resistance_active}

CONVERSATION SO FAR:
{self._format_history(history)}

MANAGER JUST SAID:
"{message}"

Respond naturally as {config['name']}:"""
    
    def _update_state(self, manager_msg, persona_response, current_state, triggers) -> PersonaState:
        """Update trust/openness based on manager's approach patterns"""
        # Analyze manager's approach for state changes
        trust_delta = 0
        openness_delta = 0
        resistance_change = current_state.resistance_active
        
        # Check trust increase triggers
        for trigger in triggers.get("trust_increase", []):
            if trigger.lower() in manager_msg.lower():
                trust_delta += 1
                openness_delta += 1
        
        # Check trust decrease triggers
        for trigger in triggers.get("trust_decrease", []):
            if trigger.lower() in manager_msg.lower():
                trust_delta -= 2
                openness_delta -= 2
        
        # Check resistance triggers
        for trigger in triggers.get("resistance_increase", []):
            if trigger.lower() in manager_msg.lower():
                resistance_change = True
        
        return PersonaState(
            trust_level=max(1, min(10, current_state.trust_level + trust_delta)),
            openness_level=max(1, min(10, current_state.openness_level + openness_delta)),
            resistance_active=resistance_change
        )
```

### 2.2 InteractionAnalyzer

**Location:** `src/services/interaction_analyzer.py`

Simplified from current `LLMInteractionAnalyzer` to focus on single-turn MAPS scoring:

```python
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class InteractionAnalysis:
    mi_techniques_used: List[str]
    maps_scores: Dict[str, float]
    behaviors_detected: Dict[str, bool]
    state_trajectory: str  # "trust_increased", "trust_stable", "resistance_triggered"

class InteractionAnalyzer:
    """Analyzes single turn against MAPS rubric"""
    
    def __init__(self, llm_service):
        self.llm = llm_service
    
    async def analyze_turn(
        self,
        manager_message: str,
        persona_response: str,
        persona_state_change: Dict,
        rubric: Dict[str, Any]
    ) -> InteractionAnalysis:
        """Analyze single interaction turn - one LLM call with structured output"""
        prompt = self._build_analysis_prompt(
            manager_message, persona_response, persona_state_change, rubric
        )
        
        analysis_json = await self.llm.structured_completion(prompt, format="json")
        
        return InteractionAnalysis(**analysis_json)
```

### 2.3 FeedbackGenerator

**Location:** `src/services/feedback_generator.py`

Template-based real-time coaching tips:

```python
class FeedbackGenerator:
    """Generates real-time coaching feedback"""
    
    def generate_realtime_tip(
        self,
        analysis: InteractionAnalysis,
        learning_objective: str,
        show_frequency: str = "key_moments"
    ) -> str:
        """Generate coaching tip for current turn - fast, deterministic"""
        
        if show_frequency == "key_moments":
            if analysis.behaviors_detected.get("unsolicited_advice"):
                return "💡 Consider using ask-share-ask before giving advice"
            elif analysis.state_trajectory == "resistance_triggered":
                return "⚠️ Resistance increased - try empathetic reflection"
            elif analysis.state_trajectory == "trust_increased":
                return "✓ Good - you're building rapport"
        
        return None
```

### 2.4 CompletionChecker

**Location:** `src/services/completion_checker.py`

```python
class CompletionChecker:
    """Determines if scenario is complete"""
    
    def check_completion(
        self,
        scenario: Dict,
        attempt: Dict,
        latest_analysis: InteractionAnalysis
    ) -> Dict:
        """Check if scenario success criteria met - deterministic rules"""
        
        criteria = scenario["success_criteria"]
        turn_count = attempt["turn_count"]
        
        # Check turn count range
        in_turn_range = (
            criteria["turn_range"][0] <= turn_count <= criteria["turn_range"][1]
        )
        
        # Check required skills demonstrated
        required_skills = criteria["required_skills"]
        skills_met = all(
            skill in attempt.get("skills_demonstrated", [])
            for skill in required_skills
        )
        
        # Check avoided behaviors
        avoid_behaviors = criteria["avoid_behaviors"]
        behaviors_avoided = not any(
            behavior in attempt.get("negative_behaviors", [])
            for behavior in avoid_behaviors
        )
        
        return {
            "is_complete": in_turn_range and skills_met and behaviors_avoided,
            "reason": self._generate_reason(criteria, attempt),
            "success": in_turn_range and skills_met and behaviors_avoided
        }
```

### 2.5 ScenarioPipeline (Core Orchestrator)

**Location:** `src/services/scenario_pipeline.py`

```python
class ScenarioPipeline:
    """
    Deterministic pipeline for processing scenario turns
    
    This is the heart of the new architecture
    """
    
    def __init__(
        self,
        persona_engine: PersonaResponseEngine,
        analyzer: InteractionAnalyzer,
        feedback_gen: FeedbackGenerator,
        completion_checker: CompletionChecker
    ):
        self.persona_engine = persona_engine
        self.analyzer = analyzer
        self.feedback_gen = feedback_gen
        self.completion_checker = completion_checker
    
    async def process_turn(
        self,
        scenario: Dict,
        attempt: Dict,
        manager_input: str
    ) -> Dict:
        """
        Process one turn of the scenario
        
        Pipeline:
        1. Persona responds (LLM - creative)
        2. Analyze interaction (LLM - structured)
        3. Generate feedback (template - deterministic)
        4. Check completion (rules - deterministic)
        """
        
        # STEP 1: Persona responds contextually
        persona_response = await self.persona_engine.generate_response(
            persona_config=scenario["persona_config"],
            manager_message=manager_input,
            conversation_history=attempt["transcript"],
            current_state=attempt["current_persona_state"]
        )
        
        # STEP 2: Analyze the interaction
        analysis = await self.analyzer.analyze_turn(
            manager_message=manager_input,
            persona_response=persona_response.message,
            persona_state_change=persona_response.updated_state.__dict__,
            rubric=scenario["maps_rubric"]
        )
        
        # STEP 3: Generate real-time feedback
        feedback = self.feedback_gen.generate_realtime_tip(
            analysis=analysis,
            learning_objective=scenario["learning_objective"]
        )
        
        # STEP 4: Update attempt record
        updated_attempt = self._update_attempt(
            attempt, manager_input, persona_response, analysis
        )
        
        # STEP 5: Check if scenario complete
        completion = self.completion_checker.check_completion(
            scenario, updated_attempt, analysis
        )
        
        return {
            "persona_message": persona_response.message,
            "persona_state": persona_response.updated_state.__dict__,
            "analysis": analysis.__dict__,
            "realtime_feedback": feedback,
            "is_complete": completion["is_complete"],
            "completion_reason": completion["reason"]
        }
```

### 2.6 ScenarioService

**Location:** `src/services/scenario_service.py`

```python
class ScenarioService:
    """Manages scenario loading and lifecycle"""
    
    def __init__(self, db):
        self.db = db
    
    async def load_scenario(self, scenario_id: str) -> Dict:
        """Load scenario with full configuration"""
        pass
    
    async def create_attempt(
        self,
        user_id: str,
        scenario_id: str
    ) -> Dict:
        """Initialize new scenario attempt"""
        pass
    
    async def get_user_progress(
        self,
        user_id: str,
        learning_path_id: str = None
    ) -> Dict:
        """Get user's progress across scenarios"""
        pass
```

---

## Phase 3: API Route Changes

### New Routes (`src/api/routes/scenarios.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])

@router.get("/")
async def list_scenarios(
    skill_category: str = None,
    difficulty: str = None
):
    """List available scenarios with filters"""
    pass

@router.get("/{scenario_id}")
async def get_scenario(scenario_id: UUID):
    """Get scenario details"""
    pass

@router.post("/{scenario_id}/start")
async def start_scenario(scenario_id: UUID, user_id: UUID = Depends(get_current_user)):
    """Start a new scenario attempt"""
    pass

@router.post("/attempts/{attempt_id}/turn")
async def process_turn(attempt_id: UUID, request: TurnRequest):
    """
    Process one turn in a scenario
    
    Main interaction endpoint
    """
    pass

@router.get("/attempts/{attempt_id}/analysis")
async def get_full_analysis(attempt_id: UUID):
    """Get complete analysis after scenario ends"""
    pass

@router.post("/attempts/{attempt_id}/abandon")
async def abandon_scenario(attempt_id: UUID):
    """User abandons scenario before completion"""
    pass
```

### Routes to Deprecate (Phase 4)
- `src/api/routes/enhanced_chat.py` - Replace with `scenarios.py`
- Keep read-only endpoints for existing data migration

---

## Phase 4: Migration Strategy

### Week 1-2: Build New System (Parallel)
- [ ] Create new database tables (keep old ones)
- [ ] Build ScenarioPipeline and core services
- [ ] Create 3 test scenarios (Jordan closing, action planning, change talk)
- [ ] Build new API routes
- [ ] Keep old system running

### Week 3: Test & Refine
- [ ] Internal testing with test scenarios
- [ ] Measure latency vs. old system
- [ ] Refine persona prompts
- [ ] Test with existing personas migrated to scenarios

### Week 4: Migrate
- [ ] Migrate existing personas → scenario configs
- [ ] Route traffic to new API
- [ ] Deprecate old routes (keep read-only)
- [ ] Monitor performance

### Week 5: Cleanup
- [ ] Remove old service files
- [ ] Drop deprecated tables
- [ ] Update documentation

---

## File Structure Changes

```
src/
├── api/
│   └── routes/
│       ├── scenarios.py          # NEW
│       ├── learning_paths.py     # NEW
│       ├── enhanced_chat.py      # DEPRECATE (Phase 4)
│       └── personas.py           # SIMPLIFY
│
├── services/
│   ├── scenario_service.py       # NEW
│   ├── scenario_pipeline.py      # NEW (core orchestrator)
│   ├── persona_response_engine.py # NEW (replaces enhanced_persona_service)
│   ├── interaction_analyzer.py   # SIMPLIFIED
│   ├── feedback_generator.py     # NEW
│   ├── completion_checker.py     # NEW
│   ├── llm_service.py            # KEEP
│   ├── enhanced_persona_service.py # DEPRECATE
│   ├── character_consistency_service.py # DEPRECATE
│   └── ...other services...
│
├── models/
│   ├── scenario.py               # NEW
│   ├── scenario_attempt.py       # NEW
│   ├── persona_state.py          # NEW
│   └── turn_result.py            # NEW
│
└── db/
    └── migrations/
        └── 001_create_scenarios.sql # NEW

supabase/
├── 0013_create_scenarios.sql     # NEW
├── 0014_create_scenario_attempts.sql
├── 0015_create_learning_paths.sql
└── 0016_create_user_learning_progress.sql
```

---

## Example Scenario Configuration

### Scenario: "Closing with Ambivalent Employee"

```yaml
code: "close-ambivalent-001"
title: "Closing the Conversation"
mi_skill_category: "Closing"
difficulty: "beginner"
estimated_minutes: 5

situation: |
  You're 8 minutes into a conversation with Jordan about time management.
  Jordan has acknowledged some issues but hasn't committed to any actions.
  The conversation needs to close soon.

persona_config:
  name: "Jordan"
  role: "Team member, 2 years in role"
  current_mindset: "Polite but evasive - acknowledges problems but deflects solutions"
  
  personality: |
    You're polite and professional, but you tend to deflect responsibility.
    You agree with criticisms in principle but always add "but" followed by
    external factors. You're ambivalent about change.
  
  response_patterns:
    to_reflection: "Cautiously agree but add caveats"
    to_direct_advice: "Polite dismissal - 'I've tried that'"
    to_confrontation: "Defensive - shift blame to external factors"
    to_empathy: "Slightly more open, but still guarded"
    to_autonomy_support: "Most responsive - hints at own ideas"
  
  triggers:
    trust_increase: ["Empathy", "Asking permission", "Validating feelings"]
    trust_decrease: ["Direct advice", "Blame", "Dismissing concerns"]
    resistance_increase: ["Confrontation", "Should statements", "Fixing"]
  
  starting_state:
    trust_level: 4
    openness_level: 3
    resistance_active: true

learning_objective: "Practice closing appropriately without forcing commitment"

success_criteria:
  turn_range: [3, 8]
  required_skills: ["summarization", "autonomy_support"]
  avoid_behaviors: ["unsolicited_advice", "fixing"]
  state_goals:
    trust_maintained: true
    resistance_not_increased: true

maps_rubric:
  dimensions:
    - name: "summarization_quality"
      weight: 0.3
    - name: "autonomy_support"
      weight: 0.3
    - name: "empathy"
      weight: 0.2
    - name: "evocation"
      weight: 0.2
```

---

## Success Metrics

### Performance
| Metric | Current | Target |
|--------|---------|--------|
| Turn latency | 3-4s | <1.5s |
| Scenario completion rate | N/A | >70% |
| System uptime | 99.5% | 99.5% |

### Learning Outcomes
- Users complete 5+ scenarios per week
- Average scenario score improvement over time
- Skill category coverage (closing, action planning, etc.)

### Technical
- Zero data loss
- <3 database queries per turn
- Caching hit rate >80% for persona configs

---

## Key Design Decisions

### 1. Why Single Persona Response Call?
- Current system: Multiple sequential LLM calls (2.5s+)
- New system: One persona call (~500-1000ms), analysis can be parallel or deferred

### 2. Why Template-Based Feedback?
- Deterministic and fast
- Consistent coaching messages
- Easier to measure tip effectiveness

### 3. Why JSONB for Transcript?
- Flexible schema for evolving turn data
- Single row per attempt (reduces joins)
- Easier to query for analytics

### 4. Why Scenario-Based vs. Open Conversation?
- Clear learning objectives
- Defined success criteria
- Focused skill practice
- Measurable outcomes
