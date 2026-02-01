# MAPS Training Module Implementation Plan

> **Reference Implementation:**
> - [`mi-learning-platform/scripts/import_modules.py`](C:/builds/mi-learning-platform/scripts/import_modules.py) - Module import script
> - [`mi-learning-platform/app/db/migrations/001_init_schema.sql`](C:/builds/mi-learning-platform/app/db/migrations/001_init_schema.sql) - Reference schema
> - [`supabase/MIGRATION_STRATEGY.md`](../supabase/MIGRATION_STRATEGY.md) - MAPS migration organization
> - [`supabase/SEED_STRATEGY.md`](../supabase/SEED_STRATEGY.md) - MAPS seed strategy

## Executive Summary

This document provides an implementation plan for integrating structured practice dialogues into the MAPS application, following the approach established in `mi-learning-platform`.

**Reference Approach:**
- Modules stored as JSON files in `src/data/mi_modules/`
- Imported to database via `scripts/import_modules.py`
- Database schema stores dialogue content as JSONB

**Key Changes for MAPS:**
1. Content separation: Learner-facing vs System-only content
2. MaPS terminology: Replace MI/healthcare language with MaPS-appropriate terms
3. Module classification: Customer-Facing, Colleague-Facing, Shared

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
    "nodes": [
      {
        "id": "node_1",
        "patient_statement": "...",
        "practitioner_choices": [
          {
            "text": "Response option",              // EXTERNAL
            "technique": "Simple reflection",       // INTERNAL
            "next_node_id": "node_2",              // EXTERNAL
            "feedback": "Feedback text",            // EXTERNAL
            "rapport_impact": 1,                    // INTERNAL
            "resistance_impact": -1                 // INTERNAL
          }
        ]
      }
    ]
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
    "nodes": [
      {
        "id": "node_1",
        "persona_statement": "...",
        "choices": [
          {
            "id": "cp_1",
            "option_text": "Response option",
            "preview_hint": "Open question approach"
          }
        ]
      }
    ]
  },
  "internal": {
    "technique_mapping": {
      "cp_1": {
        "technique": "simple_reflection",
        "competency_links": ["A6", "B2"],
        "impacts": {
          "rapport": 1,
          "resistance_change": -1
        }
      }
    },
    "feedback": {
      "cp_1": {
        "immediate": "Good reflection...",
        "learning_note": "Reflections build rapport..."
      }
    }
  }
}
```

---

## Phase 1: Import Script Development

### 1.1 Create Import Script

**Reference:** [`mi-learning-platform/scripts/import_modules.py`](C:/builds/mi-learning-platform/scripts/import_modules.py)

**File:** `scripts/import_modules.py` (NEW - adapted from mi-learning-platform)

**Key Functions:**
```python
#!/usr/bin/env python
"""
Module Data Import Script for MAPS Training Platform

Imports module content from src/data/mi_modules/*.json into Supabase database.
Supports content separation (external/internal) for secure delivery.

Usage:
    python scripts/import_modules.py [--clear-existing]

Requirements:
    - SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env file
    - Database schema already created
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from supabase import create_client


def import_module(supabase, module_file: Path) -> dict:
    """
    Import a single module from JSON file to Supabase.
    
    Args:
        supabase: Supabase admin client
        module_file: Path to module JSON file
    
    Returns:
        dict: Import result with status
    """
    try:
        with open(module_file, 'r') as f:
            data = json.load(f)
        
        # Extract external content (safe for frontend)
        external_content = data.get('external', {})
        
        # Extract internal content (system-only)
        internal_content = data.get('internal', {})
        
        # Validate required fields
        if not external_content.get('title'):
            return {'status': 'error', 'file': str(module_file), 'error': 'Missing title'}
        
        # Prepare database record
        module_data = {
            "code": external_content.get('code', module_file.stem),
            "title": external_content.get('title'),
            "content_type": external_content.get('content_type', 'shared'),
            "difficulty_level": external_content.get('difficulty_level', 'beginner'),
            "estimated_minutes": external_content.get('estimated_minutes', 10),
            "learning_objective": external_content.get('learning_objective', ''),
            "scenario_context": external_content.get('scenario_context', ''),
            "persona_config": json.dumps(external_content.get('persona_config', {})),
            "dialogue_structure": json.dumps(external_content.get('dialogue_structure', {})),
            "target_competencies": external_content.get('target_competencies', []),
            "maps_rubric": json.dumps(internal_content.get('maps_rubric', {})),
            "is_active": True
        }
        
        # Check if module already exists
        existing = supabase.table('mi_practice_modules').select('id').eq('code', module_data['code']).execute()
        
        if existing.data:
            # Update existing module
            result = supabase.table('mi_practice_modules').update(module_data).eq('code', module_data['code']).execute()
            return {
                'status': 'updated',
                'code': module_data['code'],
                'title': module_data['title']
            }
        else:
            # Insert new module
            result = supabase.table('mi_practice_modules').insert(module_data).execute()
            return {
                'status': 'created',
                'code': module_data['code'],
                'title': module_data['title']
            }
    
    except Exception as e:
        return {
            'status': 'error',
            'file': str(module_file),
            'error': str(e)
        }


def main():
    """Main import function"""
    # Validate environment
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        return 1
    
    # Create Supabase client
    print("🔌 Connecting to Supabase...")
    supabase = create_client(supabase_url, supabase_key)
    
    # Check connection
    try:
        result = supabase.table('mi_practice_modules').select('id').limit(1).execute()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return 1
    
    # Import modules
    modules_dir = Path(__file__).parent.parent / 'src' / 'data' / 'mi_modules'
    results = []
    
    print(f"\n📦 Importing modules from {modules_dir}...\n")
    
    # Import all module JSON files
    for module_file in sorted(modules_dir.glob('module_*.json')):
        print(f"  → {module_file.name}...", end=' ')
        result = import_module(supabase, module_file)
        results.append(result)
        
        if result['status'] == 'error':
            print(f"❌ Error: {result.get('error')}")
        else:
            status_icon = '✓' if result['status'] == 'created' else '↻'
            print(f"{status_icon} {result['status']}: {result.get('title', 'N/A')}")
    
    # Summary
    print("\n" + "="*50)
    created = sum(1 for r in results if r['status'] == 'created')
    updated = sum(1 for r in results if r['status'] == 'updated')
    errors = sum(1 for r in results if r['status'] == 'error')
    
    print(f"📊 Import Summary:")
    print(f"  Created: {created}")
    print(f"  Updated: {updated}")
    print(f"  Errors:  {errors}")
    
    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
```

### 1.2 Database Schema

**Reference:** [`mi-learning-platform/app/db/migrations/001_init_schema.sql`](C:/builds/mi-learning-platform/app/db/migrations/001_init_schema.sql)

**Current MAPS Schema:** [`supabase/migrations/current/0004_current_mi_practice_tables.sql`](../supabase/migrations/current/0004_current_mi_practice_tables.sql)

The existing schema stores all content in single JSONB fields. For content separation:

| Field | Content Type | Notes |
|-------|--------------|-------|
| `dialogue_structure` | External | Only learner-facing content |
| `maps_rubric` | Internal | System scoring config |

---

## Phase 2: Module JSON Refactoring

### 2.1 JSON Structure Update

**Reference Format:** [`mi-learning-platform/mi_modules/module_1.json`](C:/builds/mi-learning-platform/mi_modules/module_1.json)

**Target Format:** Split JSON with `external` and `internal` sections

### 2.2 Terminology Mapping

| Old Term | New Term |
|----------|----------|
| patient | customer / client |
| doctor/medical | financial / guidance |
| treatment | support / guidance |
| change talk | goal acknowledgment |
| resistance | hesitation |
| precontemplation | not yet ready |

### 2.3 Module Files to Update

Located in `src/data/mi_modules/`:

| File | Current Title | Target Classification |
|------|---------------|----------------------|
| `module_1.json` | Simple Reflections | Customer-Facing |
| `module_2.json` | Open-Ended Questions | Customer-Facing |
| `module_3.json` | Complex Reflections | Customer-Facing |
| `module_4.json` | Affirmations | Customer-Facing |
| `module_5.json` | Summarizing | Customer-Facing |
| `module_6.json` | Eliciting Change Talk | Customer-Facing |
| `module_7.json` | Rolling with Resistance | Customer-Facing |
| `module_8.json` | Developing Discrepancy | Customer-Facing |
| `module_9.json` | Colleague Coaching | Colleague-Facing |
| `module_10.json` | Handling Objections | Customer-Facing |
| `module_11.json` | Action Planning | Customer-Facing |
| `module_12.json` | Difficult Conversations | Colleague-Facing |

---

## Phase 3: Service Layer Updates

### 3.1 Content Service

**File:** `src/services/mi_module_service.py` (existing - needs updates)

**Key Methods:**
```python
class MIModuleService:
    async def list_modules(
        self,
        content_type: Optional[str] = None,  # 'customer_facing', 'colleague_facing'
        difficulty: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[MIPracticeModuleSummary]
    
    async def get_module_external(
        self,
        module_id: str
    ) -> Dict[str, Any]  # Returns only external content
    
    async def get_module_internal(
        self,
        module_id: str,
        admin_user_id: str
    ) -> Dict[str, Any]  # Returns full content for scoring
```

---

## Phase 4: Frontend Integration

### 4.1 API Endpoints

Reference existing endpoints in `src/api/routes/mi_practice.py`

**Update:** Add content type filtering to list endpoints

```python
@router.get("/modules")
async def list_modules(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    # ... existing parameters
):
    """List modules with optional content type filtering"""
```

---

## Phase 5: Verification

### 5.1 Import Verification

```bash
# Run import script
python scripts/import_modules.py

# Verify in Supabase
SELECT code, title, content_type, difficulty_level FROM mi_practice_modules;
```

### 5.2 Content Separation Test

```sql
-- Check that external content is accessible
SELECT code, title, dialogue_structure 
FROM mi_practice_modules
WHERE is_active = TRUE
LIMIT 1;

-- Internal content should only be accessible via admin endpoints
-- Not directly exposed in SELECT queries to regular users
```

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

**Document Version:** 2.1  
**Last Updated:** 2026-02-01  
**Status:** Phase 0 Complete - Ready for Phase 1
