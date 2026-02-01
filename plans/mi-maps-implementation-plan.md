# MAPS Training Module Implementation Plan

> **Related Documents:**
> - [`supabase/MIGRATION_STRATEGY.md`](../supabase/MIGRATION_STRATEGY.md) - Database migration organization
> - [`supabase/SEED_STRATEGY.md`](../supabase/SEED_STRATEGY.md) - Seed data strategy

## Executive Summary

This document provides an implementation plan for integrating structured practice dialogues into the MAPS application, aligned with the Money and Pensions Service (MaPS) "Guidance Competency Framework."

**Framework Context:**
MaPS describes their coaching approach as **"facilitative"** and **"empowering,"** rooted in "Foundation Skills and Behaviours" rather than adopting named proprietary models (like MI or GROW).

Key principles from MaPS:
- **Facilitation over Instruction**: "Facilitate customers to act on their own behalf"
- **Empowerment and Behavior Change**: Coaching to improve financial capability
- **Impartiality and Non-Directive**: "The decision is yours" - guidance helps identify options
- **Foundation Competencies**: Personal qualities, transferable skills, self-management

## Key Principles

- Do NOT explicitly label coaching techniques to learners
- Focus on nuance exploration, not right/wrong answers
- Provide progress tracking and analytics aligned with MAPS competency framework
- Use MaPS-appropriate terminology (customer/client, colleague - not patient)
- Maintain separation between learner-facing content and system scoring data
- Reference existing migration and seed strategies for implementation details

---

## Phase Overview

| Phase | Name | Key Deliverables | Status |
|-------|------|------------------|--------|
| 0 | Foundation Assessment | Framework alignment review, content classification | 🔄 CURRENT |
| 1 | Content Separation | Split tables/models into learner/system content | ⏳ FUTURE |
| 2 | Module Refactoring | Rewrite 13 modules with MaPS terminology | ⏳ FUTURE |
| 3 | Service Updates | Updated services for content separation | ⏳ FUTURE |
| 4 | Frontend UI | Updated UI with proper content filtering | ⏳ FUTURE |
| 5 | Integration & Testing | Full integration, analytics | ⏳ FUTURE |

---

## Phase 0: Foundation Assessment

### 0.1 Framework Alignment Review

**MaPS Competency Framework Reference:** [`supabase/MIGRATION_STRATEGY.md`](../supabase/MIGRATION_STRATEGY.md)

**MaPS Foundation Competencies:**

| Competency | Description | Application |
|------------|-------------|-------------|
| A1 | Personal Integrity | Acting as role model, commitment to equal opportunities |
| A2 | Self-awareness | Knowing strengths/limitations, controlling emotions |
| A3 | Impartiality | Objective, not influenced by personal feelings |
| A4 | Diplomacy | Sensitive and skilful in managing relations |
| A5 | Flexibility | Adapting approach to customer needs |
| A6 | Rapport building | Empathising, gauging confidence, building trust |
| B1 | Literacy | Written communication skills |
| B2 | Numeracy | Scenario scoring |
| B6 | Communication | Verbal/written communication, appropriate language |
| C1 | Self-management | Recognizing limits, resilience |
| C2 | Improve practice | Accepting feedback, evaluating performance |

### 0.2 Module Content Classification

**Classification System:**

| Classification | Description | Language |
|---------------|-------------|----------|
| **Customer-Facing** | Direct work with external customers/clients | Use "customer", "client", "you" |
| **Colleague-Facing** | Internal coaching with colleagues | Use "colleague", "team member", "you" |
| **Shared** | Applicable to both contexts | Neutral language, adaptable |

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
    "technique_tags": ["open_question"],                    // INTERNAL - system scoring
    "competency_links": ["A6", "B1"],                       // INTERNAL - system scoring
    "feedback": {
      "immediate": "Good open question...",                 // EXTERNAL - shown to learner
      "learning_note": "Open questions invite..."           // EXTERNAL - shown to learner
    }
  }]
}
```

**Solution:** Split into separate content sections (see Phase 1).

---

## Phase 1: Content Separation

### 1.1 Database Schema Updates

**Reference:** [`supabase/MIGRATION_STRATEGY.md` - Directory Structure](../supabase/MIGRATION_STRATEGY.md#directory-structure)

The migration strategy already defines the structure:
- `migrations/shared/` - Shared extensions and RLS
- `migrations/current/` - Current MAPS platform migrations
- `migrations/legacy/` - Deprecated migrations

**Current Table:** `mi_practice_modules` (needs splitting)

**Proposed Tables:**

| Table | Purpose | Content Type |
|-------|---------|--------------|
| `practice_content` | Learner-facing content | External |
| `practice_system_config` | System scoring config | Internal |

**Migration Files to Create:**

1. `supabase/migrations/current/0004a_practice_content.sql` - Learner content table
2. `supabase/migrations/current/0004b_practice_system_config.sql` - System config table

### 1.2 Pydantic Models

**Reference:** [`supabase/SEED_STRATEGY.md`](../supabase/SEED_STRATEGY.md) for seed structure

**File:** `src/models/practice_models.py` (NEW)

**Models to Create:**

```python
# Learner-Facing Models (frontend-safe)
class PracticeContentLearner(BaseModel)
class PracticeContentSummary(BaseModel)
class DialogueStructureLearner(BaseModel)
class DialogueNodeLearner(BaseModel)
class ChoicePointLearner(BaseModel)
class PersonaConfigLearner(BaseModel)
class FeedbackLearner(BaseModel)

# System-Only Models (never exposed to frontend)
class PracticeSystemConfig(BaseModel)
class DialogueNodeSystem(BaseModel)
class ChoicePointSystem(BaseModel)
class ImpactValues(BaseModel)
```

---

## Phase 2: Module Refactoring

### 2.1 Content Rewriting Guidelines

**Terminology Mapping:**

| Old Term (MI) | New Term (MaPS) | Example |
|---------------|-----------------|---------|
| Patient | Customer / Client | "How can I help you today?" |
| Client | Customer | Standardize on "customer" |
| Doctor/Medical | Financial/Support | Use financial context |
| Treatment/Prescription | Guidance/Support | Use guidance terminology |
| Change talk | Goal acknowledgment | "I hear that you want to improve..." |
| Resistance | Hesitation | Frame as natural hesitation |
| Precontemplation | Not yet ready | Neutral language |

### 2.2 Module Rewrite Tasks

**Reference:** [`supabase/SEED_STRATEGY.md` - Seed Modules](../supabase/SEED_STRATEGY.md#phase-3-mi-practice-modules)

Current seed modules (4):
1. Building Rapport (beginner)
2. Open Questions Practice (beginner)
3. Reflections Practice (beginner)
4. Rolling with Resistance (intermediate)

Additional modules in `src/data/mi_modules/` (13 total) need similar updates.

**Rewrite Tasks:**
- [ ] Replace "patient" with "customer" or "client"
- [ ] Rewrite scenario context to use financial/guidance framing
- [ ] Remove healthcare-specific references
- [ ] Align dialogue with MaPS non-directive approach
- [ ] Classify each module as Customer-Facing, Colleague-Facing, or Shared

---

## Phase 3: Core Services Update

### 3.1 Service Layer Changes

**File:** `src/services/practice_content_service.py` (NEW - replaces mi_module_service.py)

**Key Methods:**

```python
class PracticeContentService:
    async def list_content(
        self,
        content_type: Optional[str] = None,  # 'customer_facing', 'colleague_facing', 'shared'
        difficulty: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[PracticeContentSummary]
    
    async def get_content_learner(
        self,
        content_id: str,
        user_id: Optional[str] = None
    ) -> Optional[PracticeContentLearner]
    
    async def get_content_system(
        self,
        content_id: str,
        admin_user_id: str
    ) -> Optional[PracticeSystemConfig]
```

---

## Phase 4: Frontend UI Update

### 4.1 Content Type Filtering

**File:** `static/js/practice-content-browser.js` (NEW)

**Features:**
- Filter by content type (Customer-Facing, Colleague-Facing, Shared)
- Display only learner-facing content
- Hide all system-only scoring data

---

## Phase 5: Integration & Testing

### 5.1 Verification Queries

**Reference:** [`supabase/MIGRATION_STRATEGY.md` - Verification Queries](../supabase/MIGRATION_STRATEGY.md#verification-queries)

```sql
-- Check content types
SELECT code, title, difficulty_level FROM practice_content;

-- Check competency mapping
SELECT code, title, target_competencies FROM practice_content;

-- Check learning paths
SELECT code, title, estimated_duration_hours FROM mi_learning_paths;
```

### 5.2 Testing Checklist

- [ ] Database migrations apply successfully
- [ ] Pydantic models validate correctly
- [ ] API endpoints return only learner-facing content for regular users
- [ ] Admin endpoints return full content for authorized users
- [ ] Frontend displays content filtered by type
- [ ] All healthcare terminology replaced with MaPS-appropriate language
- [ ] Scoring system continues to work with new internal models
- [ ] Progress tracking aligned with MAPS competency framework

---

## Learning Paths Reference

**Reference:** [`supabase/SEED_STRATEGY.md` - Learning Paths](../supabase/SEED_STRATEGY.md#phase-4-learning-paths-optional)

| Path | Modules | Duration | Target |
|------|---------|----------|--------|
| MI Fundamentals | 3 | 15 min | beginners |
| Core Interviewing Skills | 3 | 17 min | intermediate |
| Complete Beginner Path | 4 | 22 min | beginners |

**Additional MaPS-Aligned Paths:**
- Facilitative Coaching Foundations
- Debt Advice Coaching specialization
- Pensions Coaching specialization
- Advanced Practitioner path
- Colleague Support path

---

## Tier Alignment Reference

**Reference:** [`supabase/MIGRATION_STRATEGY.md` - Tier Alignment](../supabase/MIGRATION_STRATEGY.md#tier-alignment)

- **Tier 1**: Foundation path focuses on factual information, signposting, and basic rapport
- **Tier 1-2**: Debt and Pensions paths include coaching for capability improvement
- **Tier 2-3**: Advanced path covers complex cases and mentoring others

---

## Domain Alignment Reference

**Reference:** [`supabase/MIGRATION_STRATEGY.md` - Technical Domains](../supabase/MIGRATION_STRATEGY.md#technical-domains-covered)

| Domain | Description | Paths |
|--------|-------------|-------|
| Domain 1 | Knowing your customer | All modules |
| Domain 2 | Debt | Debt Advice specialization |
| Domain 5 | Budgeting | Foundation scenarios |
| Domain 11 | Pensions | Pensions guidance path |

---

## Best Practices

1. Reference existing strategy documents for implementation details
2. Use MaPS terminology - "facilitative coaching" not proprietary model names
3. Align all content with MaPS competency framework
4. Keep legacy migrations in `migrations/legacy/` for reference
5. Use `ON CONFLICT DO NOTHING` in seeds for idempotency

---

**Document Version:** 2.0  
**Last Updated:** 2026-02-01  
**Status:** Awaiting Phase 0 Approval  
**Related Documents:**
- [`supabase/MIGRATION_STRATEGY.md`](../supabase/MIGRATION_STRATEGY.md)
- [`supabase/SEED_STRATEGY.md`](../supabase/SEED_STRATEGY.md)
