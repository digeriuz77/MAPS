# Supabase Seed Strategy

## Overview

This document describes the seed data strategy for populating the MAPS MI Training Platform database after migrations are applied.

## Seed Data Locations

```
supabase/
├── migrations/              # Schema migrations
├── seed/                    # Seed SQL scripts
│   ├── seed_profiles.sql    # User profiles
│   ├── seed_scenarios.sql   # MI training scenarios
│   ├── seed_mi_modules.sql  # Structured MI practice modules
│   └── seed_learning_paths.sql # Learning path definitions
└── data/                    # JSON seed data files (for scripts)
    ├── mi_modules/          # MI module JSON definitions
    └── scenarios/           # Scenario JSON definitions
```

## Seed Execution Order

### Phase 1: User Profiles (Required for Auth)

```sql
-- Run: supabase/seed/seed_profiles.sql
```

**Contents:**
- Admin profile (FULL access)
- Demo profile (CONTROL access)

**Prerequisite:** Users must exist in `auth.users` first.

```sql
-- Example: Insert profiles for existing auth users
INSERT INTO profiles (id, email, role)
SELECT au.id, au.email,
  CASE WHEN au.email = 'admin@mapspractice.org' THEN 'FULL' ELSE 'CONTROL' END
FROM auth.users au
WHERE au.email IN ('admin@mapspractice.org', 'demo@mapspractice.org')
ON CONFLICT (id) DO NOTHING;
```

### Phase 2: MI Scenarios (Required for Training)

```sql
-- Run: supabase/seed/seed_scenarios.sql
```

**Contents:**
- 8 pre-built training scenarios covering:
  - Rolling with resistance (3 scenarios)
  - Listening/Reflections (2 scenarios)
  - Evoking (2 scenarios)
  - Complex skills (1 scenario)

**Each scenario includes:**
- Situation/context
- Learning objectives
- Persona configuration
- Success criteria
- MAPS rubric alignment

### Phase 3: MI Practice Modules (Required for Structured Practice)

```sql
-- Run: supabase/seed/seed_mi_modules.sql
```

**Contents:**
- 4 structured dialogue modules:
  1. Building Rapport (beginner)
  2. Open Questions Practice (beginner)
  3. Reflections Practice (beginner)
  4. Rolling with Resistance (intermediate)

**Each module includes:**
- Branching dialogue tree with choice points
- Feedback on each choice (technique, impact)
- MAPS competency alignment

### Phase 4: Learning Paths (Optional)

```sql
-- Run: supabase/seed/seed_learning_paths.sql
```

**Contents:**
- 3 curated learning paths:
  1. MI Fundamentals (3 modules, 15 min)
  2. Core Interviewing Skills (3 modules, 17 min)
  3. Complete Beginner Path (4 modules, 22 min)

## Seed Scripts

### seed_profiles.sql

Creates user profiles with role-based access control:

```sql
INSERT INTO profiles (id, email, role)
SELECT au.id, au.email,
  CASE
    WHEN au.email = 'admin@mapspractice.org' THEN 'FULL'
    WHEN au.email = 'demo@mapspractice.org' THEN 'CONTROL'
    ELSE 'CONTROL'
  END
FROM auth.users au
WHERE au.email IN ('admin@mapspractice.org', 'demo@mapspractice.org')
ON CONFLICT (id) DO UPDATE SET role = EXCLUDED.role;
```

### seed_scenarios.sql

Seeds training scenarios:

| Code | Title | Category | Difficulty |
|------|-------|----------|------------|
| close-ambivalent-001 | Closing with Ambivalent Client | rolling_with_resistance | beginner |
| handle-confrontational-001 | Handling Confrontational Client | rolling_with_resistance | intermediate |
| explore-change-talk-001 | Exploring Change Talk | evoking | beginner |
| simple-reflections-001 | Simple Reflections Practice | listening | beginner |
| complex-reflections-001 | Complex Reflections Practice | listening | intermediate |
| affirmation-practice-001 | Affirmation Practice | evoking | beginner |
| sustain-talk-001 | Responding to Sustain Talk | rolling_with_resistance | intermediate |
| developing-discrepancy-001 | Developing Discrepancy | evoking | advanced |

### seed_mi_modules.sql

Seeds structured dialogue modules with branching choices:

**Module: Building Rapport**
- Focus: Establishing connection
- 10 choice points with feedback
- Skills: Open questions, reflections, affirmations

**Module: Open Questions Practice**
- Focus: Asking evocative questions
- 9 choice points with feedback
- Skills: Open vs closed questions, evocative style

**Module: Reflections Practice**
- Focus: Reflecting content and feeling
- 8 choice points with feedback
- Skills: Simple, complex, double-sided reflections

**Module: Rolling with Resistance**
- Focus: Handling discord
- 10 choice points with feedback
- Skills: Not taking sides, emphasizing autonomy

### seed_learning_paths.sql

Creates curated sequences:

| Path | Modules | Duration | Target |
|------|---------|----------|--------|
| MI Fundamentals | 3 | 15 min | beginners |
| Core Interviewing Skills | 3 | 17 min | intermediate |
| Complete Beginner Path | 4 | 22 min | beginners |

## Verification

After seeding, verify:

```sql
-- Check profiles
SELECT * FROM profiles;

-- Check scenarios
SELECT code, title, mi_skill_category, difficulty FROM scenarios;

-- Check MI modules
SELECT code, title, mi_focus_area, difficulty FROM mi_practice_modules;

-- Check learning paths
SELECT code, title, array_length(module_sequence, 1) as module_count 
FROM mi_learning_paths;
```

## Using Seed Scripts

### With Supabase CLI

```bash
# Apply seeds
cat supabase/seed/seed_profiles.sql | supabase db execute
cat supabase/seed/seed_scenarios.sql | supabase db execute
cat supabase/seed/seed_mi_modules.sql | supabase db execute
cat supabase/seed/seed_learning_paths.sql | supabase db execute
```

### With SQL Editor

1. Open Supabase SQL Editor
2. Copy seed script content
3. Execute

### Resetting Seed Data

```sql
-- Clear all seed data (⚠️ loses user progress)
TRUNCATE TABLE mi_user_progress CASCADE;
TRUNCATE TABLE mi_learning_paths CASCADE;
TRUNCATE TABLE mi_practice_attempts CASCADE;
TRUNCATE TABLE mi_practice_modules CASCADE;
TRUNCATE TABLE scenario_attempts CASCADE;
TRUNCATE TABLE scenarios CASCADE;
-- profiles should not be truncated (links to auth.users)
```

## Production Considerations

1. **Auth First**: Ensure `auth.users` exists before seeding profiles
2. **Idempotent Seeds**: Use `ON CONFLICT DO NOTHING` for re-runnability
3. **Large Datasets**: Use COPY command for bulk inserts
4. **Environment Variables**: Use env vars for admin credentials
5. **Backup**: Backup before seeding large datasets
