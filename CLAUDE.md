# MAPS Application - Current Status

## Overview

The MAPS (AI Persona System) application is a Motivational Interviewing training platform with scenario-based chat and MI practice modules.

**Repository:** C:\builds\MAPS
**Main Branch:** main
**Last Commit:** 6c289dc (Fix authentication removal and add missing LLM service methods)

---

## 🔍 Supabase Schema Discovery (2026-02-08)

### Tables That Exist:
| Table | Count | Columns |
|-------|-------|---------|
| `scenarios` | 8 | `id`, `code`, `title`, `situation`, `persona_config` (JSON), `is_active`, etc. |
| `scenario_attempts` | 0 | (empty) |
| `mi_practice_modules` | 0 | (empty - needs seeding) |
| `profiles` | 0 | (empty) |

### Tables That DON'T Exist:
- `learning_modules` (code expected this, actual is `mi_practice_modules`)
- `user_profiles` (code expected this, actual is `profiles`)
- `user_progress`
- `learning_paths`

### Schema Mismatch Fixes Applied:
1. **Scenarios table** - Uses `title` and `persona_config.name`, not `persona_name`
2. **Learning modules** - Changed queries to use `mi_practice_modules` table
3. **User profiles** - Changed queries to use `profiles` table with fallback

### Debug Endpoint:
- `GET /api/debug/supabase` - Shows all table discovery results

---

## ✅ Working Core Features

| Feature | Endpoint | Status | Details |
|---------|----------|--------|---------|
| **List Scenarios** | `GET /api/scenarios` | ✅ Working | Returns 8 scenarios |
| **Debug Supabase** | `GET /api/debug/supabase` | ✅ Working | Shows table discovery |
| **Login Page** | `/login` | ✅ Working | Client-side auth |
| **Signup Page** | `/signup` | ✅ Working | Client-side auth |

---

## ✅ Recent Fixes (2026-02-07 to 2026-02-08)

### 1. Next.js 15 Deployment Environment Variables
- **Issue:** `NEXT_PUBLIC_*` env vars not accessible in middleware at runtime
- **Fix:** Updated [`middleware.ts`](middleware.ts), [`lib/supabase/server.ts`](lib/supabase/server.ts) to check both `NEXT_PUBLIC_*` and non-prefixed variants
- **Files Changed:**
  - [`middleware.ts`](middleware.ts:21-30) - Graceful fallback for missing env vars
  - [`lib/supabase/server.ts`](lib/supabase/server.ts:22-27) - Server client env var fallbacks with `getAll/setAll` cookie methods
  - [`.env.local.example`](.env.local.example) - Updated to match actual variable naming

### 2. Client/Server Component Separation
- **Issue:** Client components importing server-only code (cookies)
- **Fix:** Created separate client-side modules
- **Files Changed:**
  - [`lib/supabase/client-auth.ts`](lib/supabase/client-auth.ts) - Client-side auth functions
  - [`lib/supabase/client-queries.ts`](lib/supabase/client-queries.ts) - Client-side query functions
  - [`app/(auth)/login/page.tsx`](app/(auth)/login/page.tsx) - Uses client-auth
  - [`app/(auth)/signup/page.tsx`](app/(auth)/signup/page.tsx) - Uses client-auth

### 3. Supabase Schema Alignment (2026-02-08)
- **Issue:** Code expected different table/column names than actual Supabase schema
- **Fix:** Updated queries to match actual schema
- **Files Changed:**
  - [`lib/supabase/queries.ts`](lib/supabase/queries.ts) - Uses `mi_practice_modules` table, maps `scenarios.title` to display name
  - [`app/api/scenarios/route.ts`](app/api/scenarios/route.ts) - Orders by `title` not `persona_name`

### 4. Voice API (Deepgram)
- **Files Changed:**
  - [`lib/voice/deepgram-client.ts`](lib/voice/deepgram-client.ts) - New Deepgram client
  - [`app/api/voice/transcribe/route.ts`](app/api/voice/transcribe/route.ts) - Uses Deepgram
  - [`app/api/voice/tts/route.ts`](app/api/voice/tts/route.ts) - Uses Deepgram

---

## ⚠️ Known Issues

### 1. Empty MI Practice Modules Table
- **Status:** `mi_practice_modules` table exists but is empty
- **Impact:** MI Practice page shows no modules
- **Fix Required:** Seed the `mi_practice_modules` table with module data

### 2. Auth Protection Disabled
- **Status:** Middleware auth checks temporarily disabled
- **Reason:** Prevent redirect loops during development
- **Location:** [`middleware.ts`](middleware.ts:70-71)

---

## Environment Variables Required

```bash
# Supabase (with NEXT_PUBLIC_ prefix)
NEXT_PUBLIC_SUPABASE_URL=https://wrevbimglixdzlcwveug.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<key>
NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY=<key>

# AI/LLM
OPENAI_API_KEY=<key>
DEEPGRAM_API_KEY=<key>
GEMINI_API_KEY=<key>
DEFAULT_MODEL=gpt-4o-mini
LLM_PROVIDER=openai

# App Config
ENVIRONMENT=production
DEBUG=false
```

---

## Application Architecture

### Core Features

1. **Chat with Persona**
   - User selects a scenario from `scenarios` table
   - Persona config stored in `persona_config` JSON column
   - Engages in text-based conversation with AI persona

2. **MI Practice Modules**
   - Modules stored in `mi_practice_modules` table (currently empty)
   - Choice-based dialogue practice

### API Routes

- `/api/scenarios` - Scenario listing and management
- `/api/debug/supabase` - Database discovery endpoint
- `/api/voice/transcribe` - Deepgram transcription
- `/api/voice/tts` - Deepgram TTS

---

**Last Updated:** 2026-02-08
**Status:** ✅ Build successful. Scenarios API working. MI modules table needs seeding.
