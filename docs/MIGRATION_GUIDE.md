# API Migration Guide

This document describes the API changes and migration path from the old system to the new scenario-based training platform.

## Overview

The codebase has been reorganized to:
1. Consolidate overlapping routes
2. Deprecate legacy endpoints with clear migration paths
3. Introduce a clean scenario-based training API

## Route Changes Summary

### Analysis Routes (Consolidated)

**Old Routes (Deprecated):**
- `POST /api/v1/analysis/submit` → Use `POST /api/analysis/transcript`
- `POST /api/v1/analysis/text` → Use `POST /api/analysis/transcript`
- `POST /api/v1/analysis/maps` → Use `POST /api/analysis/transcript`
- `POST /api/v1/analysis/enhanced/{conversation_id}` → Use `POST /api/analysis/conversation`
- `GET /api/v1/analysis/status/{job_id}` → Use `GET /api/analysis/status/{job_id}`
- `GET /api/v1/analysis/result/{job_id}` → Use `GET /api/analysis/result/{job_id}`

**Old Routes (maps_analysis.py - Deprecated):**
- `POST /api/v1/maps/analyze/transcript` → Use `POST /api/analysis/transcript`
- `POST /api/v1/maps/analyze/conversation` → Use `POST /api/analysis/conversation`
- `GET /api/v1/maps/status/{job_id}` → Use `GET /api/analysis/status/{job_id}`
- `GET /api/v1/maps/result/{job_id}` → Use `GET /api/analysis/result/{job_id}`
- `DELETE /api/v1/maps/cache` → Use `DELETE /api/analysis/cache`

**New Consolidated Routes:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analysis/transcript` | Analyze raw transcript text |
| POST | `/api/analysis/conversation` | Analyze conversation from database |
| GET | `/api/analysis/status/{job_id}` | Get analysis job status |
| GET | `/api/analysis/result/{job_id}` | Get completed analysis results |
| GET | `/api/analysis/result/{job_id}/export` | Export results (json/html/txt) |
| DELETE | `/api/analysis/cache` | Clear analysis cache |

### Chat Routes (Deprecated)

**Old Routes (enhanced_chat.py - Deprecated):**
- `POST /api/chat/start` → Use `POST /api/scenarios/{id}/start`
- `POST /api/chat/send` → Use `POST /api/scenarios/attempts/{id}/turn`
- `GET /api/chat/personas` → Use `GET /api/scenarios`
- `GET /api/chat/conversations/{id}` → Use `GET /api/scenarios/attempts/{id}/analysis`

**New Scenario Routes:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scenarios` | List available scenarios |
| GET | `/api/scenarios/{id}` | Get scenario details |
| GET | `/api/scenarios/skill-categories` | Get skill categories |
| POST | `/api/scenarios/{id}/start` | Start scenario attempt |
| POST | `/api/scenarios/attempts/{id}/turn` | Process one turn |
| GET | `/api/scenarios/attempts/{id}/analysis` | Get full analysis |
| POST | `/api/scenarios/attempts/{id}/abandon` | Abandon attempt |

## Migration Examples

### Example 1: Analyzing a Transcript

**Old Way:**
```bash
curl -X POST http://localhost:8000/api/v1/maps/analyze/transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Coach: How are you feeling? Person: I am stressed..."}'
```

**New Way:**
```bash
curl -X POST http://localhost:8000/api/analysis/transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Coach: How are you feeling? Person: I am stressed..."}'
```

### Example 2: Starting a Scenario

**Old Way:**
```bash
curl -X POST http://localhost:8000/api/chat/start \
  -H "Content-Type: application/json" \
  -d '{"persona_id": "jordan-001"}'
```

**New Way:**
```bash
curl -X POST http://localhost:8000/api/scenarios/{scenario_id}/start
```

### Example 3: Processing a Turn

**Old Way:**
```bash
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Thanks for meeting with me", "persona_id": "jordan-001", "session_id": "xxx"}'
```

**New Way:**
```bash
curl -X POST http://localhost:8000/api/scenarios/attempts/{attempt_id}/turn \
  -H "Content-Type: application/json" \
  -d '{"message": "Thanks for meeting with me"}'
```

## Deprecation Timeline

| Phase | Timeline Actions | |
|-------|----------|---------|
| Phase 1 | Now | New routes available, old routes show deprecation warnings |
| Phase 2 | 2 weeks | Old routes return 410 Gone with migration instructions |
| Phase 3 | 4 weeks | Remove old route files (maps_analysis.py, enhanced_chat.py) |

## Files Changed

### New Files Created:
- `src/services/persona_response_engine.py` - Persona response generation
- `src/services/interaction_analyzer.py` - Single-turn MAPS analysis
- `src/services/feedback_generator.py` - Real-time coaching tips
- `src/services/completion_checker.py` - Scenario completion checking
- `src/services/scenario_pipeline.py` - Core orchestrator
- `src/api/routes/scenarios.py` - Scenario API endpoints
- `supabase/0013-0016_create_scenarios.sql` - Database migrations
- `scripts/seed_scenarios.py` - Seed data script

### Files Modified:
- `src/main.py` - Updated route registration
- `src/api/routes/analysis.py` - Consolidated from maps_analysis.py
- `src/api/routes/maps_analysis.py` - Marked as deprecated wrapper
- `src/api/routes/enhanced_chat.py` - Marked as deprecated wrapper

### Files to Remove (Phase 3):
- `src/api/routes/maps_analysis.py`
- `src/api/routes/enhanced_chat.py`

## Backward Compatibility

The deprecated routes (maps_analysis.py, enhanced_chat.py) still work but log warnings. They forward to the new routes internally, providing a smooth migration path.

## Database Changes

New tables added:
- `scenarios` - Training scenarios
- `scenario_attempts` - User attempts
- `learning_paths` - Curated sequences
- `user_learning_progress` - Progress tracking

Run migrations:
```bash
psql -f supabase/0013_create_scenarios.sql
psql -f supabase/0014_create_scenario_attempts.sql
psql -f supabase/0015_create_learning_paths.sql
psql -f supabase/0016_create_user_learning_progress.sql
```

Seed example scenarios:
```bash
python scripts/seed_scenarios.py
```
