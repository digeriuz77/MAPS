# MI Practice Module - Setup and Deployment Guide

This guide covers the setup, deployment, and configuration of the MI Practice module for the MAPS platform.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Database Setup](#database-setup)
4. [Environment Configuration](#environment-configuration)
5. [Module Seeding](#module-seeding)
6. [Running the Application](#running-the-application)
7. [Adding New Modules](#adding-new-modules)
8. [Troubleshooting](#troubleshooting)

## Overview

The MI Practice module provides interactive training scenarios for Motivational Interviewing techniques. It includes:

- **13 Pre-built Modules**: Covering various MI focus areas and difficulty levels
- **Dynamic Scoring**: Continuous 1-10 spectrum across 5 competency dimensions
- **Progress Tracking**: Comprehensive analytics and learning insights
- **Branching Dialogues**: Responsive conversations based on user choices

## Prerequisites

### Required Software
- Python 3.11 or higher
- PostgreSQL 14+ (via Supabase)
- Git

### Required Accounts
- Supabase account (https://supabase.com)
- (Optional) Deepgram account for voice features

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
- `supabase/0018_create_mi_practice_tables.sql` - Creates core MI Practice tables

### 3. Database Schema

The MI Practice module uses the following tables:

#### `mi_practice_modules`
Stores module definitions and configurations.

```sql
CREATE TABLE mi_practice_modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    mi_focus_area VARCHAR(100),
    difficulty_level VARCHAR(20) DEFAULT 'beginner',
    estimated_minutes INTEGER DEFAULT 5,
    learning_objective TEXT NOT NULL,
    scenario_context TEXT,
    persona_config JSONB NOT NULL,
    dialogue_structure JSONB NOT NULL,
    target_competencies TEXT[],
    maps_rubric JSONB NOT NULL,
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
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    module_sequence UUID[],
    target_audience VARCHAR(200),
    estimated_total_minutes INTEGER,
    maps_competencies_targeted TEXT[],
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

# (Optional) Deepgram for voice features
DEEPGRAM_API_KEY=your-deepgram-key
```

### 3. Verify Configuration

```bash
python -c "from src.config.settings import settings; print('Config loaded successfully')"
```

## Module Seeding

### 1. Convert Legacy Modules (if applicable)

If you have legacy module files:

```bash
python scripts/convert_mi_modules.py
```

This converts old module formats to the new schema.

### 2. Seed Modules to Database

```bash
python scripts/seed_mi_modules.py
```

This script:
- Reads module JSON files from `src/data/mi_modules/`
- Validates module structure
- Inserts/updates records in the database
- Reports any validation errors

### 3. Verify Seeding

Check the Supabase SQL Editor:

```sql
SELECT code, title, mi_focus_area, difficulty_level 
FROM mi_practice_modules 
WHERE is_active = true;
```

Expected: 13 modules listed

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

Test the health check:

```bash
curl http://localhost:8000/api/mi-practice/health
```

Expected response:
```json
{
  "status": "healthy",
  "module_count": 13,
  "service": "mi-practice",
  "timestamp": "2026-02-01T00:00:00"
}
```

## Adding New Modules

### 1. Module Structure

Create a new JSON file in `src/data/mi_modules/`:

```json
{
  "code": "mi-focus-area-XXX",
  "title": "Module Title",
  "mi_focus_area": "Building Rapport",
  "difficulty_level": "beginner",
  "estimated_minutes": 5,
  "learning_objective": "What the learner will practice",
  "scenario_context": "Background context for the scenario",
  "persona_config": {
    "name": "Character Name",
    "role": "team member",
    "background": "Character background",
    "personality_traits": ["trait1", "trait2"],
    "tone_spectrum": {
      "word_complexity": 0.5,
      "sentence_length": 0.5,
      "emotional_expressiveness": 0.3,
      "disclosure_level": 0.2,
      "response_latency": 0.5,
      "confidence_level": 0.4
    },
    "starting_tone_position": 0.2,
    "triggers": ["trigger1"],
    "comfort_topics": ["topic1"]
  },
  "dialogue_structure": {
    "start_node_id": "node_1",
    "nodes": {
      "node_1": {
        "id": "node_1",
        "persona_text": "Character's opening line",
        "persona_mood": "defensive_guarded",
        "themes": ["Trust"],
        "choice_points": [
          {
            "id": "cp_1_1",
            "option_text": "User's response option",
            "preview_hint": "Hint about the approach",
            "rapport_impact": 1,
            "resistance_impact": -1,
            "tone_shift": 0.1,
            "technique_tags": ["open_question"],
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
        "positive_signals": ["open_questions"],
        "negative_signals": ["confrontation"]
      }
    },
    "overall_scoring_logic": "weighted_average"
  }
}
```

### 2. Code Naming Convention

Format: `mi-{focus-area}-{number}`

Examples:
- `mi-building-rapport-001`
- `mi-explore-resistance-002`
- `mi-action-planning-001`

### 3. Focus Areas

Valid focus areas:
- Building Rapport
- Exploring Resistance
- Action Planning
- Eliciting Change Talk
- Affirming
- Reflective Listening

### 4. Difficulty Levels

- `beginner`: 5-7 minutes, straightforward scenarios
- `intermediate`: 8-12 minutes, moderate complexity
- `advanced`: 13-20 minutes, complex multi-layered scenarios

### 5. Validate and Seed

After creating the module file:

```bash
# Validate JSON syntax
python -m json.tool src/data/mi_modules/module_new.json

# Seed to database
python scripts/seed_mi_modules.py
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

## Support

For issues or questions:

1. Check this guide's troubleshooting section
2. Review logs in Supabase Dashboard
3. Check browser console for frontend errors
4. Refer to architecture documentation in `plans/`

---

**Last Updated**: 2026-02-01  
**Version**: 1.0.0  
**Status**: Production Ready