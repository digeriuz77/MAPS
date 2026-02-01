# MAPS Training Module Implementation Plan

## Executive Summary

This document provides a comprehensive implementation plan for integrating structured practice dialogues into the MAPS application, aligned with the Money and Pensions Service (MaPS) "Guidance Competency Framework."

**Important Framework Context:**
MaPS does not ascribe to a single, named proprietary coaching model (like Motivational Interviewing or GROW). Instead, their approach is described as **"facilitative"** and **"empowering,"** rooted heavily in "Foundation Skills and Behaviours" as defined in the Money Guidance Competency Framework.

The core philosophy focuses on:
- **Empowerment over instruction**: "Facilitate customers to act on their own behalf"
- **Non-directive guidance**: "Help you identify your options... the decision is yours"
- **Holistic, client-centered approach**: Understanding money issues are linked to life events
- **Foundation competencies**: Rapport building, probing questions, empathy, emotional intelligence

**Key Changes from Previous Plan:**
1. Modules classified as **Customer-Facing**, **Colleague-Facing**, or **Shared**
2. Content split between **Learner-Facing** and **System-Only** models
3. Healthcare terminology (patient, doctor) replaced with MaPS-appropriate language
4. Framework references MaPS competencies, not MI-specific terminology

---

## Key Principles

- Do NOT explicitly label coaching techniques to learners
- Focus on nuance exploration, not right/wrong answers
- Provide progress tracking and analytics aligned with MAPS competency framework
- Use MaPS-appropriate terminology (customer/client, colleague - not patient)
- Maintain separation between learner-facing content and system scoring data
- Integrate seamlessly with existing Supabase/FastAPI/vanilla JS infrastructure

---

## Phase Overview

| Phase | Name | Key Deliverables | Status |
|-------|------|------------------|--------|
| 0 | Foundation Assessment | Framework alignment review, content classification | 🔄 CURRENT |
| 1A | Database Schema | Split schemas for learner/system content | ⏳ FUTURE |
| 1B | Pydantic Models | MIPracticeModuleLearner, MIPracticeModuleSystem | ⏳ FUTURE |
| 2A | Module Refactoring | Rewrite 13 modules with MaPS terminology | ⏳ FUTURE |
| 2B | Content Classification | Tag modules as Customer/Colleague/Shared | ⏳ FUTURE |
| 3 | Core Services | Updated services for content separation | ⏳ FUTURE |
| 4 | Frontend UI | Updated UI with proper content filtering | ⏳ FUTURE |
| 5 | Integration & Testing | Full integration, analytics | ⏳ FUTURE |

---

## Phase 0: Foundation Assessment

### 0.1 Framework Alignment Review

**Objective:** Align all content with MaPS "Guidance Competency Framework"

**MaPS Foundation Competencies to Reference:**

| Competency | Description | Application |
|------------|-------------|-------------|
| A1 | Build rapport and trust | Establish connection with customer/colleague |
| A2 | Empathy and emotional intelligence | Understand and respond to feelings |
| A4 | Diplomacy and sensitivity | Handle difficult topics professionally |
| A6 | Rapport building | Demonstrate understanding and validation |
| B1 | Questioning techniques | Use probing questions appropriately |
| B2 | Active listening | Demonstrate attentive listening |
| B6 | Client-centered approach | Tailor approach to individual needs |
| 1.1.1 | Holistic understanding | Consider complete situation |
| 1.2.1 | Probing questions | Ask detailed questions to understand needs |
| 1.2.3 | Goal identification | Help identify customer's own goals |

### 0.2 Module Content Classification

**Classification System:**

| Classification | Description | Language |
|---------------|-------------|----------|
| **Customer-Facing** | Direct work with external customers/clients | Use "customer", "client", "you" |
| **Colleague-Facing** | Internal coaching with colleagues | Use "colleague", "team member", "you" |
| **Shared** | Applicable to both contexts | Neutral language, adaptable |

**Initial Module Classification:**

| Module | Current Title | Classification | Required Changes |
|--------|---------------|----------------|------------------|
| 1 | Simple Reflections - Building Engagement | Customer-Facing | Replace "patient" with "customer" |
| 2 | Open-Ended Questions - Inviting Exploration | Customer-Facing | Replace "patient" with "customer" |
| 3 | Complex Reflections - Adding Meaning | Customer-Facing | Replace "patient" with "customer" |
| 4 | Affirmations - Recognizing Strengths | Customer-Facing | Replace "patient" with "customer" |
| 5 | Summarizing - Linking and Transitioning | Customer-Facing | Replace "patient" with "customer" |
| 6 | Eliciting Change Talk | Customer-Facing | Replace "patient" with "customer" |
| 7 | Rolling with Resistance | Customer-Facing | Replace "patient" with "customer" |
| 8 | Developing Discrepancy | Customer-Facing | Replace "patient" with "customer" |
| 9 | Colleague Coaching - Performance Discussion | Colleague-Facing | Rewrite with colleague context |
| 10 | Handling Objections | Customer-Facing | Replace "patient" with "customer" |
| 11 | Action Planning | Customer-Facing | Replace "patient" with "customer" |
| 12 | Difficult Conversations | Colleague-Facing | Rewrite with colleague context |

### 0.3 Internal/External Content Analysis

**Current Issue:** The `dialogue_structure` field contains mixed content:

```json
{
  "choice_points": [{
    "id": "cp_1",
    "option_text": "How can I help you today?",           // EXTERNAL - shown to learner
    "preview_hint": "Open question approach",              // EXTERNAL - shown to learner
    "rapport_impact": 1,                                    // INTERNAL - system scoring
    "resistance_impact": -1,                                // INTERNAL - system scoring
    "tone_shift": 0.15,                                     // INTERNAL - system scoring
    "technique_tags": ["open_question"],                    // INTERNAL - system scoring
    "competency_links": ["A6", "B1"],                       // INTERNAL - system scoring
    "feedback": {
      "immediate": "Good open question...",                 // EXTERNAL - shown to learner
      "learning_note": "Open questions invite..."           // EXTERNAL - shown to learner
    }
  }]
}
```

**Solution:** Split into separate content sections

---

## Phase 1A: Database Schema Updates

### 1.1.1 Create Learner Content Table

**File:** `supabase/migrations/current/0004a_practice_content.sql`

```sql
-- Learner-facing content table (safe to expose to frontend)
CREATE TABLE IF NOT EXISTS practice_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    
    -- Classification
    content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('customer_facing', 'colleague_facing', 'shared')),
    difficulty_level VARCHAR(20) DEFAULT 'beginner',
    estimated_minutes INT DEFAULT 5,
    
    -- Learning design (learner-facing)
    learning_objective TEXT NOT NULL,
    scenario_context TEXT NOT NULL,
    persona_config JSONB NOT NULL,  -- Only external fields
    dialogue_structure JSONB NOT NULL,  -- Only external fields
    
    -- MAPS alignment
    target_competencies TEXT[] DEFAULT '{}',
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_practice_content_type ON practice_content(content_type);
CREATE INDEX idx_practice_content_difficulty ON practice_content(difficulty_level);
CREATE INDEX idx_practice_content_active ON practice_content(is_active) WHERE is_active = TRUE;
```

### 1.1.2 Create System Configuration Table

**File:** `supabase/migrations/current/0004b_practice_system_config.sql`

```sql
-- System-only configuration (NEVER exposed to frontend)
CREATE TABLE IF NOT EXISTS practice_system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL REFERENCES practice_content(id) ON DELETE CASCADE,
    
    -- Scoring configuration (internal only)
    maps_rubric JSONB NOT NULL,
    
    -- Dialogue impact values (internal only)
    choice_impacts JSONB NOT NULL,  -- Maps choice_id to impact values
    
    -- Technique classification (internal only)
    technique_tags JSONB NOT NULL,  -- Maps choice_id to technique tags
    
    -- Competency mappings (internal only)
    competency_links JSONB NOT NULL,  -- Maps choice_id to competency codes
    
    -- Extended feedback with system notes (internal only)
    extended_feedback JSONB NOT NULL,  -- Detailed feedback for system analysis
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_practice_system_content ON practice_system_config(content_id);
```

### 1.1.3 Update Attempts Table

**File:** `supabase/migrations/current/0004c_practice_attempts_update.sql`

```sql
ALTER TABLE mi_practice_attempts 
    ADD COLUMN IF NOT EXISTS content_type VARCHAR(20) DEFAULT 'customer_facing';
```

---

## Phase 1B: Pydantic Models Update

### 1.2.1 Create Learner-Facing Model

**File:** `src/models/practice_models.py` (NEW)

```python
"""MAPS Practice Module Models
Split into learner-facing and system-only models for proper content separation
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    CUSTOMER_FACING = "customer_facing"
    COLLEAGUE_FACING = "colleague_facing"
    SHARED = "shared"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# ============================================
# LEARNER-FACING MODELS (Safe for frontend)
# ============================================

class ChoicePointLearner(BaseModel):
    """Learner-facing choice option - no scoring data"""
    id: str = Field(..., description="Unique identifier for this choice point")
    option_text: str = Field(..., description="The text shown for this choice")
    preview_hint: Optional[str] = Field(None, description="Hint about the approach style")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "cp_start_1",
                "option_text": "Thanks for coming in. I wanted to check in about how things are going.",
                "preview_hint": "Open, appreciative invitation"
            }
        }


class DialogueNodeLearner(BaseModel):
    """Learner-facing dialogue node - no scoring data"""
    id: str = Field(..., description="Unique node identifier")
    persona_text: str = Field(..., description="The persona's response text")
    persona_mood: str = Field(..., description="Current mood/state descriptor")
    themes: List[str] = Field(default_factory=list, description="Themes present in this node")
    choice_points: List[ChoicePointLearner] = Field(default_factory=list, description="Available choices")
    is_endpoint: bool = Field(False, description="Whether this is an ending node")
    endpoint_type: Optional[str] = Field(None, description="Type of ending if applicable")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "node_1",
                "persona_text": "I'm not sure why we're meeting. Is this about my performance?",
                "persona_mood": "defensive_guarded",
                "themes": ["Work Performance", "Trust"],
                "choice_points": [],
                "is_endpoint": False
            }
        }


class DialogueStructureLearner(BaseModel):
    """Learner-facing dialogue tree structure"""
    start_node_id: str = Field(..., description="ID of the starting node")
    nodes: Dict[str, DialogueNodeLearner] = Field(default_factory=dict, description="All nodes by ID")


class PersonaConfigLearner(BaseModel):
    """Learner-facing persona configuration"""
    name: str = Field(..., description="Persona name")
    role: str = Field(..., description="Persona's role (e.g., 'customer', 'colleague')")
    background: str = Field(..., description="Background context for the persona")
    personality_traits: List[str] = Field(default_factory=list, description="Key personality traits")
    
    # Starting position for dialogue
    starting_mood: str = Field("defensive_guarded", description="Starting mood descriptor")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jordan",
                "role": "team member",
                "background": "Recently disengaged colleague with performance concerns",
                "personality_traits": ["defensive", "guarded", "values autonomy"],
                "starting_mood": "defensive_guarded"
            }
        }


class FeedbackLearner(BaseModel):
    """Learner-facing feedback content"""
    immediate: str = Field(..., description="Immediate feedback after choice")
    learning_note: str = Field(..., description="Educational insight")


class PracticeContentLearner(BaseModel):
    """Learner-facing practice module content"""
    id: Optional[str] = None
    code: str = Field(..., pattern=r'^[a-z0-9-]+$')
    title: str = Field(..., min_length=5, max_length=200)
    
    # Classification
    content_type: ContentType
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    estimated_minutes: int = Field(5, ge=1, le=60)
    
    # Learning design
    learning_objective: str = Field(..., min_length=10)
    scenario_context: str = Field(..., min_length=10)
    
    # Persona and dialogue (learner-facing only)
    persona_config: PersonaConfigLearner
    dialogue_structure: DialogueStructureLearner
    
    # MAPS alignment
    target_competencies: List[str] = Field(default_factory=list)
    
    # Metadata
    is_active: bool = True


class PracticeContentSummary(BaseModel):
    """Lightweight summary for listing"""
    id: str
    code: str
    title: str
    content_type: ContentType
    difficulty_level: str
    estimated_minutes: int
    learning_objective: str
    target_competencies: List[str]
    
    # User-specific fields (populated at runtime)
    user_attempts: int = 0
    best_score: Optional[float] = None
    is_completed: bool = False
    last_attempted_at: Optional[datetime] = None
```

### 1.2.2 Create System-Only Model

```python
# ============================================
# SYSTEM-ONLY MODELS (Never exposed to frontend)
# ============================================

class ImpactValues(BaseModel):
    """System scoring impact values"""
    rapport_impact: int = Field(0, ge=-3, le=3)
    resistance_impact: int = Field(0, ge=-3, le=3)
    tone_shift: float = Field(0.0, ge=-0.5, le=0.5)
    exploration_depth: str = Field("surface", description="surface, middle, or deep")


class ChoicePointSystem(BaseModel):
    """System-only choice configuration"""
    choice_id: str = Field(..., description="Matches learner-facing choice ID")
    impacts: ImpactValues
    technique_tags: List[str] = Field(default_factory=list)
    competency_links: List[str] = Field(default_factory=list)
    feedback_extended: Optional[str] = Field(None, description="Detailed feedback for analysis")


class DialogueNodeSystem(BaseModel):
    """System-only dialogue node configuration"""
    node_id: str = Field(..., description="Matches learner-facing node ID")
    choice_points: List[ChoicePointSystem] = Field(default_factory=list)


class PracticeSystemConfig(BaseModel):
    """System-only practice configuration"""
    content_id: str
    maps_rubric: Dict[str, Any]  # Scoring rubric
    dialogue_nodes: Dict[str, DialogueNodeSystem]  # System-only node configs
    extended_feedback: Dict[str, str]  # Detailed feedback by choice ID
```

---

## Phase 2A: Module Refactoring

### 2.1 Content Rewriting Guidelines

**Terminology Mapping:**

| Old Term (MI) | New Term (MaPS) | Example |
|---------------|-----------------|---------|
| Patient | Customer / Client | "How can I help you today?" instead of "How can I help you, patient?" |
| Client | Customer | Standardize on "customer" for external work |
| Doctor/Medical | Financial/Support | Use financial context, not health |
| Treatment/Prescription | Guidance/Support | Use guidance terminology |
| Change talk | Goal acknowledgment | "I hear that you want to improve..." |
| Resistance | Hesitation | Frame as natural hesitation |
| Precontemplation | Not yet ready | Neutral language |

### 2.2 Module Rewrite Template

**Before (MI terminology):**
```json
{
  "code": "mi-simple-reflections-001",
  "title": "Module 1: Simple Reflections - Building Engagement",
  "mi_focus_area": "Reflective Listening",
  "persona_config": {
    "name": "Yeah,",
    "role": "patient/client",
    "background": "Does not recognize the problem or feels it's not significant enough to address."
  }
}
```

**After (MaPS terminology):**
```json
{
  "code": "maps-simple-reflections-001",
  "title": "Module 1: Simple Reflections - Building Engagement",
  "content_type": "customer_facing",
  "learning_objective": "Learn to use simple reflections to demonstrate understanding and build rapport with a customer who may not yet recognize their financial concerns.",
  "persona_config": {
    "name": "Jordan",
    "role": "customer",
    "background": "Customer who has been referred for a financial review but may not yet see the need for change."
  }
}
```

### 2.3 Rewrite Tasks by Module

**Task 2.3.1: Customer-Facing Modules (Modules 1-8, 10, 11)**
- [ ] Replace "patient" with "customer" or "client"
- [ ] Rewrite scenario context to use financial/guidance framing
- [ ] Remove healthcare-specific references (smoking cessation, doctor visits)
- [ ] Update persona backgrounds to reflect typical MaPS customer scenarios
- [ ] Ensure dialogue reflects MaPS non-directive approach

**Task 2.3.2: Colleague-Facing Modules (Modules 9, 12)**
- [ ] Rewrite from colleague coaching perspective
- [ ] Use "colleague" and "team member" terminology
- [ ] Frame scenarios as performance discussions, not clinical interactions
- [ ] Align with MAPS colleague-facing competency areas

---

## Phase 2B: Content Classification

### 2.4 Competency Mapping Update

**New MAPS Competency Mapping:**

| Technique | MAPS Competency | Rationale |
|-----------|-----------------|-----------|
| Open questioning | B1, 1.2.1 | Probing questions to understand needs |
| Reflective listening | A6, B2 | Rapport building and active listening |
| Affirmation | A6, A4 | Recognizing strengths diplomatically |
| Summarizing | B2, 1.1.1 | Active listening and holistic understanding |
| Handling hesitation | A2, A4 | Emotional intelligence and diplomacy |
| Goal identification | 1.2.3 | Helping identify customer's own goals |
| Exploring concerns | B1, 1.2.1 | Probing questions and understanding needs |

---

## Phase 3: Core Services Update

### 3.1 Service Layer Changes

**File:** `src/services/practice_content_service.py` (NEW - replaces mi_module_service.py)

```python
class PracticeContentService:
    """Service for practice content operations with content separation"""
    
    async def list_content(
        self,
        content_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[PracticeContentSummary]:
        """
        List available practice content with filtering.
        Returns only learner-facing content.
        """
        # Query practice_content table (learner-facing)
        query = self.supabase.table('practice_content').select(
            'id', 'code', 'title', 'content_type', 'difficulty_level',
            'estimated_minutes', 'learning_objective', 'target_competencies'
        ).eq('is_active', True)
        
        if content_type:
            query = query.eq('content_type', content_type)
        if difficulty:
            query = query.eq('difficulty_level', difficulty)
        
        result = query.execute()
        # ... process results
    
    async def get_content_learner(
        self,
        content_id: str,
        user_id: Optional[str] = None
    ) -> Optional[PracticeContentLearner]:
        """
        Get learner-facing content for a practice module.
        Returns ONLY learner-safe content - never exposes scoring data.
        """
        result = self.supabase.table('practice_content').select('*').eq('id', content_id).execute()
        # ... process results
    
    async def get_content_system(
        self,
        content_id: str,
        admin_user_id: str
    ) -> Optional[PracticeSystemConfig]:
        """
        Get system-only configuration for a practice module.
        Requires admin authentication - NEVER exposed to regular users.
        """
        # Verify admin access
        # Query practice_system_config table
        result = self.supabase.table('practice_system_config').select('*').eq('content_id', content_id).execute()
        # ... process results
```

---

## Phase 4: Frontend UI Update

### 4.1 Content Type Filtering

**File:** `static/js/practice-content-browser.js` (NEW)

```javascript
class PracticeContentBrowser {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.filters = {
            contentType: 'all',  // 'all', 'customer_facing', 'colleague_facing'
            difficulty: 'all'
        };
    }
    
    async loadContent() {
        const content = await this.apiClient.listPracticeContent({
            content_type: this.filters.contentType !== 'all' ? this.filters.contentType : null,
            difficulty: this.filters.difficulty !== 'all' ? this.filters.difficulty : null
        });
        this.render(content);
    }
    
    render(content) {
        // Filter out system-only content from display
        const learnerContent = content.filter(item => 
            this.isLearnerAccessible(item)
        );
        // ... render UI
    }
    
    isLearnerAccessible(content) {
        // Never expose internal scoring data
        return true; // All learner content is safe
    }
}
```

---

## Phase 5: Integration & Testing

### 5.1 Integration Checklist

- [ ] Database migrations applied successfully
- [ ] Pydantic models validate correctly
- [ ] API endpoints return only learner-facing content for regular users
- [ ] Admin endpoints return full content for authorized users
- [ ] Frontend displays content filtered by type (customer/colleague/shared)
- [ ] All healthcare terminology replaced with MaPS-appropriate language
- [ ] Scoring system continues to work with new internal models
- [ ] Progress tracking aligned with MAPS competency framework

### 5.2 Testing Strategy

**Unit Tests:**
- Test content separation (learner vs system)
- Test content type filtering
- Test terminology validation

**Integration Tests:**
- Test full practice workflow with new content
- Test scoring system with internal models
- Test admin access to system-only content

---

## Deliverables Summary

| Phase | File | Deliverable | Status |
|-------|------|-------------|--------|
| 0 | `plans/phase0-assessment.md` | Framework alignment review | ⏳ |
| 1A | `supabase/migrations/current/0004a_practice_content.sql` | Learner content table | ⏳ |
| 1A | `supabase/migrations/current/0004b_practice_system_config.sql` | System config table | ⏳ |
| 1B | `src/models/practice_models.py` | Split Pydantic models | ⏳ |
| 2A | `src/data/mi_modules/` | Rewritten modules (13 files) | ⏳ |
| 2B | Database records | Content type classification | ⏳ |
| 3 | `src/services/practice_content_service.py` | Updated service layer | ⏳ |
| 4 | `static/js/practice-content-browser.js` | Frontend content browser | ⏳ |
| 5 | Tests | Integration test suite | ⏳ |

---

**Document Version:** 2.0  
**Last Updated:** 2026-02-01  
**Status:** Awaiting Phase 0 Approval  
**Next Step:** Phase 0 Framework Assessment Review
