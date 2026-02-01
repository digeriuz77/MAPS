# MAPS Training Module Implementation Plan

> **Reference Implementation:**
> - [`mi-learning-platform/scripts/import_modules.py`](C:/builds/mi-learning-platform/scripts/import_modules.py) - Module import script
> - [`mi-learning-platform/app/db/migrations/001_init_schema.sql`](C:/builds/mi-learning-platform/app/db/migrations/001_init_schema.sql) - Reference schema
> - [`supabase/MIGRATION_STRATEGY.md`](../supabase/MIGRATION_STRATEGY.md) - MAPS migration organization
> - [`supabase/SEED_STRATEGY.md`](../supabase/SEED_STRATEGY.md) - MAPS seed strategy

## Executive Summary

This document provides a comprehensive implementation plan for integrating structured practice dialogues into the MAPS application, following the approach established in `mi-learning-platform`.

**Reference Approach:**
- Modules stored as JSON files in `src/data/mi_modules/`
- Imported to database via `scripts/import_modules.py`
- Database schema stores dialogue content as JSONB

**Key Changes for MAPS:**
1. Content separation: Learner-facing vs System-only content
2. MaPS terminology: Replace MI/healthcare language with MaPS-appropriate terms
3. Module classification: Customer-Facing, Colleague-Facing, Shared

---

## Phase Overview

| Phase | Name | Status | Key Deliverables |
|-------|------|--------|------------------|
| 0 | Foundation Assessment | ✅ COMPLETE | Framework alignment, content classification |
| 1 | Initial Module Conversion | ⏳ SUPERSEDED | Initial conversion approach (replaced) |
| 2 | Module Restructuring | ✅ COMPLETE | 20 modules + Learning Pathways |
| 3 | Service/API Updates | ✅ COMPLETE | Content type filtering support |
| 4 | Frontend Integration | ⏳ PENDING | Content filtering UI |
| 5 | Testing & Verification | ⏳ PENDING | Test suite, verification queries |
| 6 | Documentation | ⏳ PENDING | Updated docs and guides |

---

## Phase 0: Foundation Assessment ✅ COMPLETE

### 0.1 Framework Alignment

**MaPS Competency Framework Alignment:** [`supabase/MIGRATION_STRATEGY.md`](../supabase/MIGRATION_STRATEGY.md#maps-competency-framework-alignment)

### 0.2 Content Classification

| Classification | Description | Language |
|---------------|-------------|----------|
| **Customer-Facing** | External customers/clients | "customer", "client" |
| **Colleague-Facing** | Internal colleagues | "colleague", "team member" |
| **Shared** | Neutral, adaptable | Neutral language |

### 0.3 Internal/External Content Split

**Reference:** [`mi-learning-platform/mi_modules/module_1.json`](C:/builds/mi-learning-platform/mi_modules/module_1.json) for JSON structure

**Current JSON Structure (needs splitting):**
```json
{
  "dialogue_tree": {
    "title": "Module 1: Simple Reflections...",
    "learning_objective": "...",
    "nodes": [...]
  }
}
```

**Proposed JSON Structure (split):**
```json
{
  "external": {
    "title": "Module 1: Simple Reflections...",
    "learning_objective": "...",
    "content_type": "customer_facing",
    "dialogue_structure": {...}
  },
  "internal": {
    "maps_rubric": {...},
    "technique_impacts": {...}
  }
}
```

---

## Phase 1: Import Script Development & Module Refactoring ✅ COMPLETE

### 1.1 Create Import Script

**Reference:** [`mi-learning-platform/scripts/import_modules.py`](C:/builds/mi-learning-platform/scripts/import_modules.py)

**Status:** ✅ Complete - `scripts/import_modules.py` exists (uses existing code)

### 1.2 Module JSON Refactoring

**Status:** ✅ Complete - All 12 modules refactored to MAPS terminology

**Converted Modules:**
| Module | Code | Classification | Status |
|--------|------|----------------|--------|
| 1: Simple Reflections | `maps-simple-reflections-001` | Customer-Facing | ✅ |
| 2: Open-Ended Questions | `maps-openended-questions-vs-closed--002` | Customer-Facing | ✅ |
| 3: Complex Reflections | `maps-complex-reflections-and-double-003` | Customer-Facing | ✅ |
| 4: Affirmations | `maps-affirmations-004` | Customer-Facing | ✅ |
| 5: Summarizing | `maps-summarizing-005` | Customer-Facing | ✅ |
| 6: Change Talk | `maps-change-talk-recognition-and-ev-006` | Customer-Facing | ✅ |
| 7: Collaborative Climate | `maps-collaborative-climate--agenda--007` | Customer-Facing | ✅ |
| 8: Confidence Scaling | `maps-confidence-scaling-008` | Customer-Facing | ✅ |
| 9: Decisional Balance | `maps-decisional-balance-009` | Colleague-Facing | ✅ |
| 10: Planning | `maps-planning--implementation-inten-010` | Customer-Facing | ✅ |
| 11: Giving Information | `maps-elicitprovideelicit-011` | Customer-Facing | ✅ |
| 12: Anticipatory Coping | `maps-anticipatory-coping--relapse-p-012` | Colleague-Facing | ✅ |

### 1.3 Create Supabase Seed Scripts

**Status:** ✅ Complete - All 12 seed scripts created

**Location:** `supabase/seed/seed_mi_module_*.sql`

**Features:**
- ✅ Proper Supabase SQL syntax with JSONB casting
- ✅ `ON CONFLICT (code) DO UPDATE` for idempotency
- ✅ MAPS terminology (customer/colleague, not patient)
- ✅ Generated automatically via `scripts/generate_seed_scripts.py`

### 1.4 Helper Scripts Created

| Script | Purpose |
|--------|---------|
| `scripts/convert_mi_modules.py` | Converts healthcare modules to MAPS terminology |
| `scripts/generate_seed_scripts.py` | Generates Supabase seed SQL from converted modules |

### 1.5 Deliverables

- [x] `scripts/import_modules.py` exists (uses existing code)
- [x] Supabase seed script template created
- [x] All 12 module JSON files refactored to MAPS terminology
- [x] All 12 Supabase seed scripts created
- [x] Helper scripts for conversion and generation
- [x] Database schema validated for import

### 1.6 Progress Log

**2026-02-01:**
- ✅ Created `module_1_simple_reflections_maps.json` with Customer-Facing financial context
- ✅ Converted all 12 modules using `scripts/convert_mi_modules.py`
- ✅ Generated all 12 seed scripts using `scripts/generate_seed_scripts.py`
- ✅ Terminology mapping applied throughout: patient→customer/colleague, smoking→spending/performance, health→financial/performance, therapeutic→professional
- ✅ Content classifications applied: 10 Customer-Facing, 2 Colleague-Facing

---

## Phase 2: Module Restructuring ✅ COMPLETE

### 2.1 JSON Structure Update

**Reference Format:** [`mi-learning-platform/mi_modules/module_1.json`](C:/builds/mi-learning-platform/mi_modules/module_1.json)

**Target Format:** Split JSON with `external` and `internal` sections

**Structure:**
```json
{
  "external": {
    "code": "maps-simple-reflections-001",
    "title": "Module 1: Simple Reflections - Building Engagement",
    "content_type": "customer_facing",
    "difficulty_level": "beginner",
    "estimated_minutes": 10,
    "learning_objective": "...",
    "scenario_context": "...",
    "persona_config": {...},
    "dialogue_structure": {...}
  },
  "internal": {
    "maps_rubric": {...},
    "technique_impacts": {...}
  }
}
```

### 2.2 Terminology Mapping

| Old Term (MI) | New Term (MaPS) |
|---------------|-----------------|
| patient | customer / client |
| doctor/medical | financial / guidance |
| treatment | support / guidance |
| change talk | goal acknowledgment |
| resistance | hesitation |
| precontemplation | not yet ready |

### 2.3 Module Structure Redesign

**IMPORTANT CORRECTION:** Most MI techniques are SHARED/NEUTRAL strategies. The classification should be:

**Shared Modules (Core Technique Practice - Neutral Language):**
These modules teach the core MI skills that apply to both customer and colleague contexts.

| Code | Title | Focus Area | Difficulty | Status |
|------|-------|------------|------------|--------|
| `shared-simple-reflections-001` | Simple Reflections - Core Skill Practice | Reflective Listening | beginner | ✅ Complete |
| `shared-open-questions-002` | Open-Ended Questions | Building Rapport | beginner | ✅ Complete |
| `shared-complex-reflections-003` | Complex & Double-Sided Reflections | Reflective Listening | beginner | ✅ Complete |
| `shared-affirmations-004` | Affirmations | Building Rapport | beginner | ✅ Complete |
| `shared-summarizing-005` | Summarizing | Linking & Transitioning | intermediate | ✅ Complete |
| `shared-change-talk-006` | Recognizing & Evoking Change Talk | Eliciting | intermediate | ✅ Complete |
| `shared-collaborative-climate-007` | Collaborative Climate | Partnership | beginner | ✅ Complete |
| `shared-confidence-scaling-008` | Confidence Scaling | Assessment | beginner | ✅ Complete |
| `shared-decisional-balance-009` | Decisional Balance | Exploring Ambivalence | intermediate | ✅ Complete |
| `shared-elicit-provide-elicit-010` | Elicit-Provide-Elicit | Information Exchange | intermediate | ✅ Complete |
| `shared-planning-011` | Planning & Implementation | Goal Setting | advanced | ✅ Complete |
| `shared-anticipatory-coping-012` | Anticipatory Coping | Sustaining Change | advanced | ✅ Complete |

**Customer-Facing Modules (Specific MAPS Financial Scenarios):**
These modules apply core skills to specific money guidance contexts.

| Code | Title | MAPS Domain | Difficulty | Status |
|------|-------|-------------|------------|--------|
| `customer-debt-initial-001` | Debt Advice: Initial Engagement | Domain 2 (Debt) | intermediate | ✅ Complete |
| `customer-budgeting-002` | Budget Planning with Impartial Guidance | Domain 5 (Budgeting) | intermediate | ✅ Complete |
| `customer-financial-anxiety-003` | Supporting Financial Anxiety | Domain 1 (Knowing Customer) | intermediate | ✅ Complete |
| `customer-savings-goals-004` | Savings Goal Setting | Domain 5 (Budgeting) | beginner | ✅ Complete |
| `customer-pensions-exploration-005` | Pensions Exploration | Domain 11 (Pensions) | intermediate | ✅ Complete |

**Colleague-Facing Modules (Specific MAPS Performance Scenarios):**
These modules apply core skills to internal colleague contexts.

| Code | Title | Context | Difficulty | Status |
|------|-------|---------|------------|--------|
| `colleague-performance-review-001` | Performance Review: Reflective Practice | Annual Review | intermediate | ✅ Complete |
| `colleague-career-development-002` | Career Development: Coaching Conversation | Development | intermediate | ✅ Complete |
| `colleague-skill-gap-003` | Skill Gap Coaching: Development Support | Training | intermediate | ✅ Complete |
| `colleague-team-dynamics-004` | Team Dynamics: Mediation and Facilitation | Team Working | advanced | ✅ Complete |

### 2.4 Migration Notes

**Previous modules (incorrectly classified):** The original `module_*_maps.json` files were healthcare-focused MI modules that were converted with simple word substitutions. These are being replaced/deprecated in favor of the new structure above.

**Key Differences:**
- **SHARED modules** use neutral language (person, situation, change, reflection) that applies universally
- **CUSTOMER-FACING modules** are specific MAPS scenarios (debt advice, budgeting, pensions) with financial context
- **COLLEAGUE-FACING modules** are specific MAPS scenarios (performance reviews, coaching) with workplace context

### 2.4 Module Examples Created

**Shared Module Example: `shared_simple_reflections.json`**
- Uses neutral language: "person", "situation", "change"
- Teaches core reflection skill without specific context
- Applies universally to customers AND colleagues
- MAPS competencies: A6 (Rapport), B6 (Communication), 2.1.1 (Reflective Listening)

**Customer-Facing Example: `customer_debt_initial.json`**
- Domain 2 (Debt) specific scenario
- Customer seeking debt advice, feeling ashamed/overwhelmed
- Specific MAPS competencies: A6 (Rapport), A3 (Impartiality), A5 (Flexibility), B6 (Communication)
- Real financial guidance context with shame, hesitation, empowerment themes

**Colleague-Facing Example: `colleague_performance_review.json`**
- Performance review coaching scenario
- Colleague defensive, wants effort recognized, development-focused
- MAPS competencies: A6 (Rapport), A4 (Diplomacy), B6 (Communication), C1 (Self-Management)
- Real workplace context with defensiveness, effort recognition, growth themes

### 2.5 Language Guidelines

**SHARED Modules (Neutral):**
- Use: "person", "individual", "participant"
- Avoid: "customer", "colleague", "patient", "client"
- Focus: The skill itself, not the context

**Customer-Facing Modules:**
- Use: "customer", "client" (money guidance context)
- MAPS Domains: 1 (Knowing Customer), 2 (Debt), 5 (Budgeting), 11 (Pensions)
- Themes: Financial anxiety, debt stress, budgeting, savings, pensions

**Colleague-Facing Modules:**
- Use: "colleague", "team member" (workplace context)
- Themes: Performance, development, coaching, team dynamics, career growth
- Tone: Collaborative, developmental, supportive

### 2.6 Deliverables

- [x] Module structure redesign documented
- [x] All 12 SHARED modules created
- [x] All 5 CUSTOMER-FACING modules created
- [x] All 4 COLLEAGUE-FACING modules created
- [x] Learning Pathways configuration created
- [ ] Seed scripts generated for all new modules
- [ ] Old deprecated modules removed/archived

### 2.7 Progress Log

**2026-02-01 - Phase 2 COMPLETE:**
- ✅ Identified classification error: MI techniques are neutral strategies, not context-specific
- ✅ Created all 12 SHARED modules with neutral language:
  - shared_simple_reflections.json
  - shared_open_questions.json
  - shared_affirmations.json
  - shared_complex_reflections.json
  - shared_summarizing.json
  - shared_confidence_scaling.json
  - shared_change_talk.json
  - shared_collaborative_climate.json
  - shared_decisional_balance.json
  - shared_elicit_provide_elicit.json
  - shared_planning.json
  - shared_anticipatory_coping.json
- ✅ Created all 5 CUSTOMER-FACING modules with MAPS scenarios:
  - customer_debt_initial.json
  - customer_budgeting.json
  - customer_financial_anxiety.json
  - customer_savings_goals.json
  - customer_pensions.json
- ✅ Created all 4 COLLEAGUE-FACING modules with workplace scenarios:
  - colleague_performance_review.json
  - colleague_career_development.json
  - colleague_skill_gap.json
  - colleague_team_dynamics.json
- ✅ Created Learning Pathways configuration with 8 pathways
- ✅ Updated implementation plan with correct structure
- ✅ Documented language guidelines for each module type

---

## Phase 3: Service/API Updates ✅ COMPLETE

### 3.1 Models Updated

**File:** `src/models/mi_models.py`

**Changes:**
- Added `ContentType` enum: `SHARED`, `CUSTOMER_FACING`, `COLLEAGUE_FACING`
- Added `content_type` field to `MIPracticeModule`
- Added `content_type` field to `MIPracticeModuleSummary`
- Fixed broken `MIPracticeModule` class definition
- Added `maps_framework_alignment` field support

### 3.2 Service Layer Updated

**File:** `src/services/mi_module_service.py`

**Changes:**
- Added `content_type` parameter to `list_modules()` method
- Added `get_content_types()` method for discovery
- Updated module building to include `content_type`
- Updated all module retrieval methods to include `content_type`
- Added `maps_framework_alignment` support

### 3.3 API Layer Updated

**File:** `src/api/routes/mi_practice.py`

**Changes:**
- Added `content_type` query parameter to `GET /modules` endpoint
- Added `GET /content-types` endpoint for discovery
- Updated documentation for content types
- Imported `ContentType` enum

### 3.4 New API Endpoints

```
GET /api/mi-practice/modules?content_type=shared
GET /api/mi-practice/content-types
```

### 3.5 Deliverables

- [x] `ContentType` enum added
- [x] `MIPracticeModule.content_type` added
- [x] `MIPracticeModuleSummary.content_type` added
- [x] `MIModuleService.list_modules(content_type=...)` updated
- [x] `MIModuleService.get_content_types()` added
- [x] `GET /modules?content_type=...` endpoint updated
- [x] `GET /content-types` endpoint added

### 3.6 Progress Log

**2026-02-01 - Phase 3 COMPLETE:**
- ✅ Added ContentType enum to models
- ✅ Updated MIPracticeModule with content_type field
- ✅ Updated MIPracticeModuleSummary with content_type field
- ✅ Added content_type filtering to list_modules()
- ✅ Added get_content_types() discovery method
- ✅ Added GET /content-types API endpoint
- ✅ Updated API documentation

---

## Phase 4: Frontend Integration ⏳ PENDING

### 3.1 MIModuleService Updates

**File:** `src/services/mi_module_service.py` (existing)

**New/Updated Methods:**

```python
class MIModuleService:
    async def list_modules(
        self,
        content_type: Optional[str] = None,  # 'customer_facing', 'colleague_facing'
        difficulty: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[MIPracticeModuleSummary]
    """List modules with optional content type filtering."""
    
    async def get_module_external(
        self,
        module_id: str
    ) -> Optional[Dict[str, Any]]
    """Get module with external content only (safe for frontend)."""
    
    async def get_module_internal(
        self,
        module_id: str,
        admin_user_id: str
    ) -> Optional[Dict[str, Any]]
    """Get module with internal content for scoring (admin only)."""
```

### 3.2 MIAttemptService Updates

**File:** `src/services/mi_attempt_service.py` (existing)

**Updates Required:**
- Add content type tracking to attempts
- Support internal content lookup for scoring

### 3.3 Deliverables

- [ ] `MIModuleService.list_modules()` updated with content_type filter
- [ ] `MIModuleService.get_module_external()` added
- [ ] `MIModuleService.get_module_internal()` added (admin only)
- [ ] `MIAttemptService` updated for content type tracking

---

## Phase 4: API Layer Updates ⏳ PENDING

### 4.1 MI Practice Routes

**File:** `src/api/routes/mi_practice.py` (existing)

**New Endpoints/Parameters:**

```python
@router.get("/modules")
async def list_modules(
    content_type: Optional[str] = Query(
        None, 
        description="Filter by content type: customer_facing, colleague_facing, shared"
    ),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    # ... existing parameters
):
    """List modules with optional content type and difficulty filtering."""
```

### 4.2 Response Models

**File:** `src/models/mi_models.py` (existing)

**Updates Required:**
- Add `content_type` field to `MIPracticeModuleSummary`
- Add `content_type` enum

### 4.3 Deliverables

- [ ] API endpoint updated with content_type filter
- [ ] Response models updated
- [ ] API documentation updated

---

## Phase 5: Frontend Integration ⏳ PENDING

### 5.1 Module Browser Updates

**File:** `static/mi-practice.html` (existing)

**New Features:**
- Content type filter (Customer-Facing / Colleague-Facing / All)
- Difficulty filter
- Classification badges on module cards

### 5.2 Practice Session Updates

**File:** `static/mi-practice-module.html` (existing)

**Updates Required:**
- Display content classification
- Update persona context based on classification

### 5.3 Deliverables

- [ ] Content type filter added to module browser
- [ ] Classification badges displayed
- [ ] Persona context updated for classification

---

## Phase 6: Testing & Verification ⏳ PENDING

### 6.1 Unit Tests

**File:** `tests/test_mi_services.py` (existing)

**New Tests:**
- Test content type filtering
- Test external/internal content separation
- Test import script

### 6.2 Integration Tests

**Test Scenarios:**
1. Import all modules successfully
2. List modules with content type filter
3. Retrieve module external content
4. Practice session with content type tracking

### 6.3 Verification Queries

```sql
-- Check content types
SELECT code, title, content_type, difficulty_level FROM mi_practice_modules;

-- Check external content is accessible
SELECT code, title, dialogue_structure FROM mi_practice_modules WHERE is_active = TRUE;

-- Check learning paths
SELECT code, title, content_type FROM mi_learning_paths;
```

### 6.4 Deliverables

- [ ] Unit tests for content separation
- [ ] Integration tests for import workflow
- [ ] Verification queries documented
- [ ] Test coverage report

---

## Phase 7: Documentation ⏳ PENDING

### 7.1 Documentation Updates

- [ ] Update `MI_PRACTICE_SETUP.md` with new import process
- [ ] Update `README.md` with content classification info
- [ ] Update API documentation
- [ ] Add content authoring guide

### 7.2 User Guides

- [ ] Module creation guide (with external/internal split)
- [ ] Content classification guide
- [ ] Import process documentation

---

## File Reference Summary

| Source | Purpose |
|--------|---------|
| [`mi-learning-platform/scripts/import_modules.py`](C:/builds/mi-learning-platform/scripts/import_modules.py) | Import script reference |
| [`mi-learning-platform/app/db/migrations/001_init_schema.sql`](C:/builds/mi-learning-platform/app/db/migrations/001_init_schema.sql) | Schema reference |
| [`mi-learning-platform/mi_modules/module_1.json`](C:/builds/mi-learning-platform/mi_modules/module_1.json) | Module JSON reference |
| [`supabase/migrations/current/0004_current_mi_practice_tables.sql`](../supabase/migrations/current/0004_current_mi_practice_tables.sql) | Current MAPS schema |
| [`supabase/SEED_STRATEGY.md`](../supabase/SEED_STRATEGY.md) | Seed data approach |

---

## Implementation Checklist

### Phase 1: Import Script
- [ ] Create `scripts/import_modules.py`
- [ ] Test import with single module
- [ ] Validate database schema

### Phase 2: Module Refactoring
- [ ] Refactor `module_1.json` (Customer-Facing)
- [ ] Refactor `module_2.json` (Customer-Facing)
- [ ] Refactor `module_3.json` (Customer-Facing)
- [ ] Refactor `module_4.json` (Customer-Facing)
- [ ] Refactor `module_5.json` (Customer-Facing)
- [ ] Refactor `module_6.json` (Customer-Facing)
- [ ] Refactor `module_7.json` (Customer-Facing)
- [ ] Refactor `module_8.json` (Customer-Facing)
- [ ] Refactor `module_9.json` (Colleague-Facing)
- [ ] Refactor `module_10.json` (Customer-Facing)
- [ ] Refactor `module_11.json` (Customer-Facing)
- [ ] Refactor `module_12.json` (Colleague-Facing)
- [ ] Test import with all modules

### Phase 3: Service Updates
- [ ] Update `MIModuleService.list_modules()`
- [ ] Add `get_module_external()`
- [ ] Add `get_module_internal()`
- [ ] Update `MIAttemptService`

### Phase 4: API Updates
- [ ] Update list modules endpoint
- [ ] Update response models
- [ ] Update API documentation

### Phase 5: Frontend Updates
- [ ] Add content type filter
- [ ] Add classification badges
- [ ] Update persona context

### Phase 6: Testing
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Run verification queries

### Phase 7: Documentation
- [ ] Update setup guide
- [ ] Update README
- [ ] Add authoring guide

---

**Document Version:** 6.0
**Last Updated:** 2026-02-01
**Status:** Phase 2 COMPLETE - 20 modules created, Learning Pathways ready

**Recent Changes:**
- v6.0: Phase 2 COMPLETE - All 20 modules created (12 shared, 5 customer-facing, 4 colleague-facing), Learning Pathways configured
- v5.0: Corrected module classification - SHARED modules for core skills, Customer-Facing for MAPS financial scenarios, Colleague-Facing for workplace scenarios
- v4.0: Phase 1 Complete - 12 MAPS modules converted (now superseded by corrected structure)
