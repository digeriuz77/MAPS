# MAPS Application - Current Status

## Overview

The MAPS (AI Persona System) application is a Motivational Interviewing training platform with scenario-based chat and MI practice modules.

**Repository:** C:\builds\MAPS
**Main Branch:** main
**Last Commit:** 6c289dc (Fix authentication removal and add missing LLM service methods)

---

## ✅ Working Core Features

| Feature | Endpoint | Status | Details |
|---------|----------|--------|---------|
| **Health Check** | `GET /health` | ✅ Working | Returns server/DB status |
| **List Scenarios** | `GET /api/scenarios/` | ✅ Working | Returns 8 scenarios |
| **Start Scenario** | `POST /api/scenarios/{id}/start` | ✅ Working | Creates attempt, returns initial message |
| **Process Turn** | `POST /api/scenarios/attempts/{attempt_id}/turn` | ✅ Working | Chat with persona fully functional |
| **List MI Modules** | `GET /api/mi-practice/modules` | ✅ Working | Returns 45 modules |
| **Start MI Module** | `POST /api/mi-practice/modules/{id}/start` | ✅ Working | Creates attempt with choice points |
| **Static Pages** | `/chat`, `/mi-practice`, etc. | ✅ Working | HTML pages served |

---

## ✅ Recent Fixes (Committed)

### 1. Turn Processing Feedback Generator Integration (Commit 2cee43d)
- **Issue:** `generate_realtime_tip()` expected dict but received `InteractionAnalysis` object
- **Fix:** Convert analysis to dict before passing to feedback generator
- **Impact:** Chat with persona now fully functional

### 2. Deepgram SDK v3 Compatibility (Commit 3b4a1b1)
- **Issue:** Deepgram imports failing on v3 SDK
- **Fix:** Added graceful handling with stub types when SDK unavailable
- **Impact:** Voice features now optional (non-blocking for core functionality)

### 3. Authentication Removal & LLM Service (Commits 6c289dc, 2b70f82)
- **Issue:** Auth guards blocking requests, missing LLM methods
- **Fix:** Removed AuthConfig, added wrapper methods, fixed type hints
- **Impact:** All routes now public, app fully functional without auth

---

## ⚠️ Known Minor Issues

### 1. Voice Routes (LOW PRIORITY)
- **Status:** Gracefully disabled when Deepgram SDK unavailable
- **Impact:** Voice features unavailable (non-blocking)
- **Note:** Text-based chat works perfectly

### 2. Redis Cache (LOW PRIORITY)
- **Warning:** "redis-py not installed, caching disabled"
- **Impact:** No caching, slightly slower response times
- **Status:** Non-blocking warning

---

## Database Status

**Foreign Key Constraints:** Using existing valid user ID `a126e8ec-00ff-4914-8fd2-eb6e2864d3f0` for all anonymous requests.

**Tables Affected:**
- `scenario_attempts` - ✅ Working
- `mi_practice_attempts` - ✅ Working

---

## Testing Commands

```bash
# Health check
curl http://localhost:8001/health

# List scenarios
curl http://localhost:8001/api/scenarios/

# Start scenario
curl -X POST http://localhost:8001/api/scenarios/92f286e1-fd09-4eda-ab08-cf7f9c183f17/start \
  -H "Content-Type: application/json" -d '{"module_id": "92f286e1-fd09-4eda-ab08-cf7f9c183f17"}'

# Process turn (WORKING!)
curl -X POST http://localhost:8001/api/scenarios/attempts/{attempt_id}/turn \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi Terry, how are things going?"}'

# List MI modules
curl http://localhost:8001/api/mi-practice/modules?limit=3

# Start MI module
curl -X POST "http://localhost:8001/api/mi-practice/modules/395f2eb9-3e13-4cf5-8b33-9072b769e511/start" \
  -H "Content-Type: application/json" \
  -d '{"module_id": "395f2eb9-3e13-4cf5-8b33-9072b769e511"}'
```

---

## Deployment Status

**Local Server:** Running on http://localhost:8001

**API Documentation:** http://localhost:8001/docs

### 🚨 Production Deployment Error (2026-02-07)

**Status:** Deployment failing with Supabase configuration error

**Error Logs:**
```
2026-02-07T12:31:36.000000000Z [inf]  Starting Container
2026-02-07T12:31:37.336536702Z [inf]  ✓ Ready in 377ms
2026-02-07T12:31:37.336556662Z [err]  npm warn config production Use `--omit=dev` instead.
2026-02-07T12:31:37.336567012Z [inf]  > maps-app@2.0.0 start
2026-02-07T12:31:37.336571682Z [inf]  > next start
2026-02-07T12:31:37.336578362Z [inf]
2026-02-07T12:31:37.336584622Z [inf]     ▲ Next.js 15.5.12
2026-02-07T12:31:37.336589982Z [inf]     - Local:        http://localhost:8080
2026-02-07T12:31:37.336595002Z [inf]     - Network:      http://10.173.218.70:8080
2026-02-07T12:31:37.336599872Z [inf]
2026-02-07T12:31:37.336604872Z [inf]  ✓ Starting...
2026-02-07T22:33:58.651507369Z [err]  Error: Your project's URL and Key are required to create a Supabase client!
2026-02-07T22:33:58.651516549Z [err]
2026-02-07T22:33:58.651527729Z [err]  Check your Supabase project's API settings to find these values
2026-02-07T22:33:58.651534020Z [err]
2026-02-07T22:33:58.651540360Z [err]  https://supabase.com/dashboard/project/_/settings/api
2026-02-07T22:33:58.651546940Z [err]     at <unknown> (.next/server/middleware.js:49:53624)
2026-02-07T22:33:58.651560589Z [err]     at eC (.next/server/middleware.js:53:5177)
2026-02-07T22:33:58.651567229Z [err]     at handler (.next/server/middleware.js:53:6609)
2026-02-07T22:33:58.651586160Z [err]     at async bs (.next/server/middleware.js:13:33569)
2026-02-07T22:33:58.651591949Z [err]  ⨯ Error: Cannot append headers after they are sent to the client
2026-02-07T22:33:58.651602969Z [err]     at p (.next/server/app/_not-found/page.js:2:4781)
2026-02-07T22:33:58.651608580Z [err]    code: 'ERR_HTTP_HEADERS_SENT'
```

**Root Cause:** Next.js 15 standalone server doesn't properly expose `NEXT_PUBLIC_*` environment variables to middleware at runtime. Variables are embedded at build time but middleware runs in a separate context.

**Variables Confirmed Set in Railway:**
- `NEXT_PUBLIC_SUPABASE_URL` ✅
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` ✅

**Fix Applied (2026-02-07):** Updated [`middleware.ts`](middleware.ts:19-40) to:
1. Check for both `NEXT_PUBLIC_*` and non-prefixed variants (e.g., `SUPABASE_URL`)
2. Gracefully skip auth checks if env vars aren't available at middleware runtime
3. Log warning instead of crashing

**Railway Configuration Note:**
Railway may require variables without the `NEXT_PUBLIC_` prefix for server-side/middleware access. Add these additional variables in Railway:
- `SUPABASE_URL` (same value as `NEXT_PUBLIC_SUPABASE_URL`)
- `SUPABASE_ANON_KEY` (same value as `NEXT_PUBLIC_SUPABASE_ANON_KEY`)

**Reference Files:**
- [`middleware.ts`](middleware.ts:19-40) - Middleware with fallback env var handling
- [`lib/supabase/server.ts`](lib/supabase/server.ts:19-28) - Server client
- [`.env.local.example`](.env.local.example:1-12) - All expected variable names

---

## Application Architecture

### Core Features

1. **Chat with Persona**
   - User selects a scenario (Terry, Mary, Jan, Vic)
   - Engages in text-based conversation with AI persona
   - Receives real-time MI feedback
   - Optional voice interface (STT/TTS) - requires Deepgram SDK

2. **MI Practice Modules**
   - 45 structured learning modules
   - Choice-based dialogue practice
   - Immediate feedback on MI technique
   - Progress tracking

### API Routes

- `/api/scenarios/` - Scenario-based training
- `/api/mi-practice/` - MI practice modules
- `/api/analysis` - MAPS analysis
- `/api/voice` - Voice interface (optional)
- `/api/feedback` - Feedback system
- `/api/reflection` - Reflection prompts
- `/api/metrics` - Usage metrics

---

## Git Status

**Current branch:** main
**Status:** Clean (all changes committed)

Recent commits:
- `2cee43d` Fix turn processing feedback generator integration
- `3b4a1b1` Add graceful Deepgram SDK v3 compatibility handling
- `6c289dc` Fix authentication removal and add missing LLM service methods
- `2b70f82` Remove duplicate model definitions in mi_models.py
- `30260c8` Merge pull request #4 - Remove all authentication

---

**Last Updated:** 2026-02-07
**Status:** 🚨 Production deployment failing - missing Supabase environment variables. Local development works.
