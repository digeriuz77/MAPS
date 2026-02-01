# Supabase Migration and Seeding Strategy

## Overview

This document outlines the database migration strategy for the MAPS Training Platform, organizing migrations into logical categories and establishing clear seeding procedures aligned with the MaPS Money Guidance Competency Framework.

## MaPS Framework Alignment

### The MaPS Coaching Approach

The Money Guidance Competency Framework (September 2022) describes a **facilitative coaching approach** rather than adopting named proprietary models like Motivational Interviewing. Key principles:

1. **Facilitation over Instruction** (Domain 1.2.9)
   - "Facilitate customers to act on their own behalf, where appropriate with the aim of empowering them to manage their own affairs and change behaviours"

2. **Empowerment and Behavior Change**
   - Tier 2 explicitly mentions: "the practitioner may offer some coaching to customers to improve their financial capability and money management skills"

3. **Impartiality and Non-Directive** (Section A3)
   - "Providers of money guidance must do so impartially"
   - "The decision is yours" - guidance helps identify options but does not direct

4. **Foundation Skills and Behaviours** (Section 6.1)
   - Personal qualities and attributes (A)
   - Transferable skills (B)
   - Self-management (C)

### Competency Mapping

| MaPS Code | Competency | Application in Training |
|-----------|------------|------------------------|
| A1 | Personal Integrity | Acting as role model, commitment to equal opportunities |
| A2 | Self-awareness | Knowing strengths/limitations, controlling emotions |
| A3 | Impartiality | Objective, not influenced by personal feelings |
| A4 | Diplomacy | Sensitive and skilful in managing relations |
| A5 | Flexibility | Adapting approach to customer needs |
| A6 | Rapport building | Empathising, gauging confidence, building trust |
| B6 | Communication | Verbal/written communication, appropriate language |
| C1 | Self-management | Recognizing limits, resilience |
| C2 | Improve practice | Accepting feedback, evaluating performance |

## Directory Structure

```
supabase/
├── migrations/
│   ├── shared/              # Shared migrations (extensions, RLS)
│   │   ├── 0000_shared_extensions.sql
│   │   └── 0001_shared_rls_policies.sql
│   ├── current/             # Current MAPS platform migrations
│   │   ├── 0000_current_profiles.sql
│   │   ├── 0001_current_scenarios.sql
│   │   ├── 0002_current_scenario_attempts.sql
│   │   ├── 0003_current_voice_sessions.sql
│   │   └── 0004_current_mi_practice_tables.sql
│   └── legacy/              # Legacy Character AI migrations (deprecated)
├── seed/
│   ├── seed_all.sql         # Master seed orchestration
│   ├── seed_profiles.sql    # User profiles
│   ├── seed_scenarios.sql   # Training scenarios
│   ├── seed_mi_modules.sql  # Coaching practice modules
│   └── seed_learning_paths.sql # Learning paths and curricula
└── data/                    # Reference data
```

## Migration Phases

### Phase 1: Foundation (Shared)
These migrations must run first as they set up the database foundation.

**Order:**
1. `migrations/shared/0000_shared_extensions.sql` - Enable pgcrypto
2. `migrations/shared/0001_shared_rls_policies.sql` - RLS policies

**What they do:**
- Enable UUID generation via pgcrypto extension
- Set up Row Level Security for data protection
- Establish shared configuration tables

### Phase 2: Core Tables (Current)
These migrations set up the MAPS Training Platform tables.

**Order:**
1. `migrations/current/0000_current_profiles.sql` - User profiles
2. `migrations/current/0001_current_scenarios.sql` - Training scenarios
3. `migrations/current/0002_current_scenario_attempts.sql` - Attempt tracking
4. `migrations/current/0003_current_voice_sessions.sql` - Voice sessions
5. `migrations/current/0004_current_mi_practice_tables.sql` - Coaching modules, attempts, learning paths

**What they do:**
- Create user profile tables with roles and permissions
- Create scenario tables for training content
- Track user attempts and progress
- Support voice-based practice sessions
- Create coaching practice module structures

### Phase 3: Legacy Tables (Legacy)
These are migrations from the original Character AI application.

**Note:** These tables may not be used in the current MAPS platform but are kept for reference.

## Seed Data Strategy

### Seed Execution Order

1. **seed_profiles.sql** - Creates default user profiles
   - Admin users
   - Trainer roles
   - Demo/practice users

2. **seed_scenarios.sql** - Creates training scenarios
   - MAPS-specific scenarios (pension, debt, budgeting)
   - Competency-based scoring rubrics
   - Persona configurations

3. **seed_mi_modules.sql** - Creates coaching practice modules
   - 4 core modules (rapport, probing questions, reflections, working with reluctance)
   - Branching dialogue structures
   - MaPS-appropriate contexts
   - Competency mappings to MaPS framework

4. **seed_learning_paths.sql** - Creates learning paths
   - Facilitative Coaching Foundations path
   - Debt Advice Coaching specialization
   - Pensions Coaching specialization
   - Advanced Practitioner path
   - Colleague Support path

5. **seed_all.sql** - Master orchestration script
   - Runs all seeds in correct order
   - Provides verification queries

### Seed Data Principles

1. **Idempotent seeds**: All seeds use `ON CONFLICT DO NOTHING` to allow re-runs
2. **MaPS-aligned**: All scenarios use money, pension, and debt advice contexts
3. **Progressive difficulty**: Modules and paths progress from beginner to advanced
4. **Competency alignment**: All content maps to MaPS competency framework
5. **Facilitative approach**: Skills framed as "facilitative coaching" not proprietary models

## MaPS Competency Framework Alignment

### Foundation Competencies Covered

| Code | Competency | Modules/Paths |
|------|------------|---------------|
| A1 | Personal Integrity | All |
| A2 | Self-awareness | All |
| A3 | Impartiality | All, especially Working with Reluctance |
| A5 | Flexibility | Advanced paths |
| A6 | Rapport building | All, especially Foundations |
| B1 | Literacy | All (written exercises) |
| B2 | Numeracy | Scenario scoring |
| B6 | Communication | All, especially Foundations |
| C1 | Self-management | Advanced paths |
| C2 | Improve practice | All |

### Technical Domains Covered

| Domain | Description | Paths |
|--------|-------------|-------|
| Domain 1 | Knowing your customer | All modules |
| Domain 2 | Debt | Debt Advice specialization |
| Domain 5 | Budgeting | Foundation scenarios |
| Domain 11 | Pensions | Pensions guidance path |

### Tier Alignment

- **Tier 1**: Foundation path focuses on factual information, signposting, and basic rapport
- **Tier 1-2**: Debt and Pensions paths include coaching for capability improvement
- **Tier 2-3**: Advanced path covers complex cases and mentoring others

## Running Migrations and Seeds

### Via Supabase CLI

```bash
# Apply all migrations
supabase db push

# Apply seeds (if using supabase seed)
supabase db push --include-seed
```

### Via SQL Editor (Supabase Dashboard)

1. Run migrations in order (Phase 1, then Phase 2)
2. Run `supabase/seed/seed_all.sql`
3. Verify with provided queries

### Via psql

```bash
psql -h [host] -d [database] -f supabase/migrations/shared/0000_shared_extensions.sql
psql -h [host] -d [database] -f supabase/migrations/shared/0001_shared_rls_policies.sql
psql -h [host] -d [database] -f supabase/migrations/current/0000_current_profiles.sql
# ... continue with remaining migrations
psql -h [host] -d [database] -f supabase/seed/seed_all.sql
```

## Verification Queries

### Check Migration Status

```sql
SELECT * FROM pg_stat_user_tables 
WHERE schemaname = 'public' 
ORDER BY relname;
```

### Check Seed Data

```sql
-- Profiles
SELECT * FROM profiles LIMIT 5;

-- Coaching Modules
SELECT code, title, mi_focus_area, difficulty, 
       maps_rubric->'target_competencies' as competencies
FROM mi_practice_modules;

-- Learning Paths
SELECT code, title, difficulty_level, estimated_duration_hours,
       path_structure->'completion_bonus'->>'badge' as badge
FROM mi_learning_paths
ORDER BY estimated_duration_hours;
```

### Check MaPS Competency Mapping

```sql
-- See which competencies each module addresses
SELECT code, title,
       maps_rubric->'target_competencies' as target_competencies,
       maps_rubric->'maps_framework'->>'section' as framework_section
FROM mi_practice_modules;
```

## Rollback Strategy

### Migration Rollbacks

To rollback a migration, create a new migration with `DROP TABLE` or `DROP FUNCTION` statements:

```sql
-- Example rollback migration
CREATE OR REPLACE FUNCTION rollback_migration_0004()
RETURNS void AS $$
BEGIN
  DROP TABLE IF EXISTS mi_learning_paths CASCADE;
  DROP TABLE IF EXISTS mi_path_prerequisites CASCADE;
  DROP TABLE IF EXISTS mi_practice_attempts CASCADE;
  DROP TABLE IF EXISTS mi_practice_modules CASCADE;
END;
$$ LANGUAGE plpgsql;

SELECT rollback_migration_0004();
DROP FUNCTION rollback_migration_0004;
```

### Seed Rollbacks

Seed data is idempotent - re-running seeds will not duplicate data. To clear and reseed:

```sql
TRUNCATE TABLE mi_learning_paths CASCADE;
TRUNCATE TABLE mi_practice_attempts CASCADE;
TRUNCATE TABLE mi_practice_modules CASCADE;
TRUNCATE TABLE scenarios CASCADE;
TRUNCATE TABLE profiles CASCADE;

-- Then re-run seeds
\i seed_all.sql
```

## Best Practices

1. **Always test migrations** in a development environment first
2. **Use `ON CONFLICT DO NOTHING`** in seeds to make them idempotent
3. **Document changes** in this strategy document
4. **Version migrations sequentially** with clear descriptions
5. **Keep legacy migrations** for reference but mark them as deprecated
6. **Align with MaPS framework** - all content should map to competency areas
7. **Use MaPS terminology** - "facilitative coaching" not proprietary model names

## References

- Money Guidance Competency Framework (September 2022), Money & Pensions Service
- MaPS Domain 1: Knowing your Customer
- MaPS Section A: Personal qualities and attributes
- MaPS Section B: Transferable skills
- MaPS Section C: Self-management
- Tier 1-3 competency descriptions
