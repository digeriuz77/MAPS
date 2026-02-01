# MI Practice Module - Setup and Deployment Guide

This guide covers the setup, deployment, and configuration of the MI Practice module for the MAPS platform.

## Table of Contents

1. [Overview](#overview)
2. [Module Classification](#module-classification)
3. [Prerequisites](#prerequisites)
4. [Database Setup](#database-setup)
5. [Environment Configuration](#environment-configuration)
6. [Module Seeding](#module-seeding)
7. [Running the Application](#running-the-application)
8. [Adding New Modules](#adding-new-modules)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)

## Overview

The MI Practice module provides interactive training scenarios for Motivational Interviewing techniques aligned with the MAPS Money Guidance Competency Framework. It includes:

- **20 Practice Modules**: Across three classifications (Shared, Customer-Facing, Colleague-Facing)
- **8 Learning Pathways**: Structured progression from foundational to advanced skills
- **Dynamic Scoring**: MAPS competency-based assessment with continuous feedback
- **Progress Tracking**: Comprehensive analytics and learning insights
- **Branching Dialogues**: Responsive conversations based on user choices

## Module Classification

MI Practice modules are organized into three categories:

### 1. Shared Modules (Core Skills)
**Purpose**: Core MI techniques with neutral language applicable universally

| Code | Title | Focus Area | Difficulty |
|------|-------|------------|------------|
| `shared-simple-reflections-001` | Simple Reflections | Reflective Listening | Beginner |
| `shared-open-questions-002` | Open-Ended Questions | Building Rapport | Beginner |
| `shared-affirmations-004` | Affirmations | Building Confidence | Beginner |
| `shared-complex-reflections-003` | Complex & Double-Sided Reflections | Exploring Ambivalence | Beginner |
| `shared-summarizing-005` | Summarizing | Linking & Transitioning | Intermediate |
| `shared-change-talk-006` | Recognizing & Evoking Change Talk | Evoking | Intermediate |
| `shared-collaborative-climate-007` | Collaborative Climate | Partnership | Beginner |
| `shared-confidence-scaling-008` | Confidence Scaling | Assessment | Beginner |
| `shared-decisional-balance-009` | Decisional Balance | Decision Making | Intermediate |
| `shared-elicit-provide-elicit-010` | Elicit-Provide-Elicit | Information Exchange | Intermediate |
| `shared-planning-011` | Planning | Goal Setting | Advanced |
| `shared-anticipatory-coping-012` | Anticipatory Coping | Sustaining Change | Advanced |

### 2. Customer-Facing Modules (MAPS Financial Scenarios)
**Purpose**: Apply MI skills to specific money guidance contexts

| Code | Title | MAPS Domain | Difficulty |
|------|-------|-------------|------------|
| `customer-debt-initial-001` | Debt Advice: Initial Engagement | Domain 2 (Debt) | Intermediate |
| `customer-budgeting-002` | Budget Planning with Impartial Guidance | Domain 5 (Budgeting) | Intermediate |
| `customer-financial-anxiety-003` | Supporting Financial Anxiety | Domain 1 (Knowing Customer) | Intermediate |
| `customer-savings-goals-004` | Savings Goal Setting | Domain 5 (Budgeting) | Beginner |
| `customer-pensions-exploration-005` | Pensions Exploration | Domain 11 (Pensions) | Intermediate |

### 3. Colleague-Facing Modules (Workplace Scenarios)
**Purpose**: Apply MI skills to internal colleague contexts

| Code | Title | Context | Difficulty |
|------|-------|---------|------------|
| `colleague-performance-review-001` | Performance Review: Reflective Practice | Annual Review | Intermediate |
| `colleague-career-development-002` | Career Development: Coaching Conversation | Development | Intermediate |
| `colleague-skill-gap-003` | Skill Gap Coaching: Development Support | Training | Intermediate |
| `colleague-team-dynamics-004` | Team Dynamics: Mediation and Facilitation | Team Working | Advanced |

## Prerequisites

### Required Software
- Python 3.11 or higher
- PostgreSQL 14+ (via Supabase)
- Git

### Required Accounts
- Supabase account (https://supabase.com)

### Python Dependencies
```bash
pip install fastapi uvicorn pydantic supabase-py pytest httpx
```

## Database Setup

### 1. Create Supabase Project

1. Log in to Supabase Dashboard
2. Create a new project
3. Save your Project URL and Anon Key

### 2. Run Database Migrations

Execute the migration files in order:

```bash
# Using Supabase CLI
supabase db push

# Or execute via SQL Editor in Supabase Dashboard
```

**Required Migration Files:**
- `supabase/migrations/current/0004_current_mi_practice_tables.sql` - Creates core MI Practice tables
- `supabase/migrations/current/0005_mi_learning_pathways.sql` - Creates learning pathways table

### 3. Database Schema

The MI Practice module uses the following tables:

#### `mi_practice_modules`
Stores module definitions and configurations.

```sql
CREATE TABLE mi_practice_modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    content_type VARCHAR(50) NOT NULL,  -- 'shared', 'customer_facing', 'colleague_facing'
    mi_focus_area VARCHAR(100),
    difficulty_level VARCHAR(20) DEFAULT 'beginner',
    estimated_minutes INTEGER DEFAULT 5,
    learning_objective TEXT NOT NULL,
    scenario_context TEXT,
    persona_config JSONB NOT NULL,
    dialogue_structure JSONB NOT NULL,
    target_competencies TEXT[],
    maps_rubric JSONB NOT NULL,
    maps_framework_alignment JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `mi_practice_attempts`
Tracks user practice attempts.

```sql
CREATE TABLE mi_practice_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    module_id UUID NOT NULL REFERENCES mi_practice_modules(id),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    current_node_id VARCHAR(100),
    path_taken TEXT[],
    current_rapport_score INTEGER DEFAULT 0,
    current_resistance_level INTEGER DEFAULT 5,
    tone_spectrum_position FLOAT DEFAULT 0.2,
    choices_made JSONB DEFAULT '[]',
    completion_status VARCHAR(50),
    final_scores JSONB,
    insights_generated JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `mi_user_progress`
Aggregates user progress across all modules.

```sql
CREATE TABLE mi_user_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id),
    modules_completed INTEGER DEFAULT 0,
    modules_attempted INTEGER DEFAULT 0,
    total_practice_minutes INTEGER DEFAULT 0,
    competency_scores JSONB DEFAULT '{}',
    techniques_practiced JSONB DEFAULT '{}',
    active_learning_path_id UUID,
    current_module_index INTEGER DEFAULT 0,
    learning_insights JSONB DEFAULT '[]',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `mi_learning_paths`
Defines structured learning sequences.

```sql
CREATE TABLE mi_learning_paths (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pathway_data JSONB NOT NULL,  -- Stores full pathway configuration
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Environment Configuration

### 1. Create .env File

```bash
cp .env.example .env
```

### 2. Required Environment Variables

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
```

### 3. Verify Configuration

```bash
python -c "from src.config.settings import settings; print('Config loaded successfully')"
```

## Module Seeding

### 1. Generate Seed Scripts

From module JSON files:

```bash
python scripts/generate_seed_scripts.py
```

This generates Supabase-compatible seed SQL scripts for:
- All 20 MI practice modules
- Learning pathways configuration

### 2. Run Seed Scripts

**Option A: Individual scripts via Supabase SQL Editor**
```bash
# Navigate to the seed directory
cd supabase/seed

# Copy and paste each script into Supabase SQL Editor
# Scripts are named: seed_{module-code}.sql
```

**Option B: Batch import via Supabase CLI**
```bash
# Run all seed scripts
for script in supabase/seed/seed_*.sql; do
    supabase db execute --file "$script"
done
```

### 3. Verify Seeding

Check the Supabase SQL Editor:

```sql
-- Verify modules
SELECT code, title, content_type, mi_focus_area, difficulty_level
FROM mi_practice_modules
WHERE is_active = true
ORDER BY content_type, code;

-- Expected: 20 modules
-- 12 shared, 5 customer_facing, 4 colleague_facing

-- Verify learning pathways
SELECT id, pathway_data->>'name' as name,
       pathway_data->>'target_audience' as audience
FROM mi_learning_paths
WHERE is_active = true;

-- Expected: 8 pathways
```

## Running the Application

### 1. Start Development Server

```bash
# From project root
python src/main.py
```

Or with uvicorn directly:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Access the Application

- Main application: http://localhost:8000
- MI Practice: http://localhost:8000/mi-practice.html
- API docs: http://localhost:8000/docs

### 3. Verify API Endpoints

```bash
# Health check
curl http://localhost:8000/api/mi-practice/health

# List modules
curl http://localhost:8000/api/mi-practice/modules

# Get content types
curl http://localhost:8000/api/mi-practice/content-types

# Filter by content type
curl http://localhost:8000/api/mi-practice/modules?content_type=shared
```

## Adding New Modules

### 1. Module Structure

Create a new JSON file in `src/data/mi_modules/`:

```json
{
  "id": "00000000-0000-0000-0001-000000000XXX",
  "code": "{type}-{slug}-{XXX}",
  "title": "Module Title",
  "content_type": "shared",
  "mi_focus_area": "Reflective Listening",
  "difficulty_level": "beginner",
  "estimated_minutes": 10,
  "learning_objective": "What the learner will practice",
  "scenario_context": "Background context for the scenario",
  "persona_config": {
    "name": "Character Name",
    "role": "person",
    "background": "Character background",
    "personality_traits": ["trait1", "trait2"],
    "tone_spectrum": {
      "word_complexity": 0.5,
      "sentence_length": 0.5,
      "emotional_expressiveness": 0.5,
      "disclosure_level": 0.5,
      "response_latency": 0.5,
      "confidence_level": 0.5
    },
    "starting_tone_position": 0.5,
    "triggers": ["trigger1"],
    "comfort_topics": ["topic1"]
  },
  "dialogue_structure": {
    "start_node_id": "node_1",
    "nodes": {
      "node_1": {
        "id": "node_1",
        "persona_text": "Character's opening line",
        "persona_mood": "neutral_curious",
        "themes": ["Theme1"],
        "choice_points": [
          {
            "id": "cp_1_1",
            "option_text": "User's response option",
            "preview_hint": "Hint about the approach",
            "rapport_impact": 1,
            "tone_shift": 0.1,
            "technique_tags": ["reflection"],
            "competency_links": ["A6"],
            "feedback": {
              "immediate": "Immediate feedback",
              "learning_note": "Educational insight"
            },
            "next_node_id": "node_2",
            "exploration_depth": "surface"
          }
        ],
        "is_endpoint": false
      }
    }
  },
  "target_competencies": ["A6", "B6"],
  "maps_rubric": {
    "dimensions": {
      "A6": {
        "description": "Rapport Building",
        "weight": 1.5,
        "positive_signals": ["reflection"],
        "negative_signals": ["confrontation"]
      }
    },
    "overall_scoring_logic": "weighted_average"
  },
  "maps_framework_alignment": {
    "framework_name": "MaPS Money Guidance Competency Framework",
    "framework_version": "September 2022",
    "sections": ["A6", "B6"],
    "tier_relevance": "All Tiers",
    "domains": ["Universal Skill"]
  },
  "is_active": true,
  "created_at": "2026-02-01T00:00:00Z",
  "updated_at": "2026-02-01T00:00:00Z"
}
```

### 2. Code Naming Convention

**Format:** `{type}-{slug}-{number}`

**Types:**
- `shared-*`: Core technique modules with neutral language
- `customer-*`: MAPS financial scenarios
- `colleague-*`: MAPS workplace scenarios

**Examples:**
- `shared-active-listening-001`
- `customer-debt-initial-001`
- `colleague-performance-review-001`

### 3. Language Guidelines

**Shared Modules:**
- Use: "person", "individual", "participant"
- Avoid: "customer", "colleague", "patient", "client"
- Focus: The skill itself, not the context

**Customer-Facing Modules:**
- Use: "customer", "client"
- MAPS Domains: 1 (Knowing Customer), 2 (Debt), 5 (Budgeting), 11 (Pensions)
- Themes: Financial anxiety, debt stress, budgeting, savings, pensions

**Colleague-Facing Modules:**
- Use: "colleague", "team member"
- Themes: Performance, development, coaching, team dynamics, career growth
- Tone: Collaborative, developmental, supportive

### 4. Generate Seed Script

```bash
# Generate seed script for new module
python scripts/generate_seed_scripts.py
```

### 5. Seed to Database

```bash
# Run generated seed script in Supabase SQL Editor
supabase/seed/seed_{module-code}.sql
```

## API Reference

### Module Endpoints

#### List Modules
```
GET /api/mi-practice/modules
```

Query Parameters:
- `content_type`: Filter by type (`shared`, `customer_facing`, `colleague_facing`)
- `focus_area`: Filter by MI focus area
- `difficulty`: Filter by difficulty level
- `user_id`: Include user progress information

#### Get Module
```
GET /api/mi-practice/modules/{module_id}
```

#### Discovery Endpoints

**Content Types**
```
GET /api/mi-practice/content-types
```
Returns content types with module counts.

**Focus Areas**
```
GET /api/mi-practice/focus-areas
```
Returns focus areas with module counts.

**Difficulty Levels**
```
GET /api/mi-practice/difficulty-levels
```
Returns difficulty levels with module counts.

### Practice Endpoints

#### Start Attempt
```
POST /api/mi-practice/modules/{module_id}/start
```

#### Make Choice
```
POST /api/mi-practice/attempts/{attempt_id}/choose
```

#### Get Attempt Review
```
GET /api/mi-practice/attempts/{attempt_id}/review
```

### Learning Path Endpoints

#### List Learning Paths
```
GET /api/mi-practice/learning-paths
```

#### Get Learning Path
```
GET /api/mi-practice/learning-paths/{path_id}
```

#### Enroll in Path
```
POST /api/mi-practice/learning-paths/enroll
```

## Troubleshooting

### Database Connection Issues

**Problem**: `Connection refused` or timeout errors

**Solution**:
1. Verify Supabase URL and keys in `.env`
2. Check network connectivity
3. Ensure IP is allowlisted in Supabase dashboard

### Module Seeding Errors

**Problem**: `ValidationError` when seeding

**Solution**:
1. Check module JSON syntax
2. Verify required fields are present
3. Ensure `code` follows naming convention
4. Check that `start_node_id` matches a node in `dialogue_structure.nodes`
5. Validate `content_type` is one of: `shared`, `customer_facing`, `colleague_facing`

### API 404 Errors

**Problem**: Endpoints return 404

**Solution**:
1. Verify router is included in `src/main.py`
2. Check that the router prefix matches your request URL
3. Restart the server after code changes

### Frontend Not Loading

**Problem**: MI Practice pages show blank or error

**Solution**:
1. Check browser console for JavaScript errors
2. Verify static files are in `static/` directory
3. Clear browser cache and hard reload (Ctrl+F5)
4. Check that Supabase client is properly initialized

### Scoring Not Working

**Problem**: Attempts complete but no scores shown

**Solution**:
1. Verify `maps_rubric` is properly defined in module
2. Check that `competency_links` are set in choice points
3. Review server logs for scoring service errors

### Progress Not Saving

**Problem**: Progress doesn't persist between sessions

**Solution**:
1. Verify user is authenticated
2. Check `mi_user_progress` table has correct RLS policies
3. Ensure `user_id` is being passed correctly in API calls

## Testing

### Run Tests

```bash
# All tests
pytest tests/ -v

# Integration tests only
pytest tests/test_mi_practice.py -v

# Unit tests only
pytest tests/test_mi_services.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Manual Testing Checklist

- [ ] Navigate to MI Practice from welcome page
- [ ] View module list with filters
- [ ] Filter by content type (shared/customer/colleague)
- [ ] Start a practice attempt
- [ ] Make choices and see feedback
- [ ] Complete an attempt
- [ ] Review attempt results
- [ ] Check progress dashboard
- [ ] Verify data persists after refresh

## Production Deployment

### 1. Environment Setup

```env
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
```

### 2. Database

- Enable RLS policies on all tables
- Set up proper indexes for performance
- Configure automated backups

### 3. Security

- Use service role key only for server-side operations
- Enable Row Level Security (RLS) in Supabase
- Set up proper CORS origins

### 4. Monitoring

- Set up error tracking (Sentry recommended)
- Configure application logs
- Monitor database performance

## MAPS Framework Alignment

All modules align with the **MaPS Money Guidance Competency Framework (September 2022)**.

### Competency Sections
- **A**: Working with People
- **B**: Communication Skills
- **C**: Knowledge and Understanding

### Tier Relevance
- **Tier 1**: Universal and Foundation Services
- **Tier 2**: Specialized and Targeted Services
- **Tier 3**: Specialist and Intensive Services

### Domains
- **Domain 1**: Knowing Your Customer
- **Domain 2**: Debt
- **Domain 5**: Budgeting
- **Domain 11**: Pensions

---

**Last Updated**: 2026-02-01
**Version**: 2.0.0
**Status**: Phase 3 Complete - 20 modules ready for deployment
