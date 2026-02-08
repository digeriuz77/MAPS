# MAPS Application - Security & Functionality Audit

**Date:** 2026-02-08
**Status:** Ready for Review

---

## Summary

Comprehensive audit of the MAPS (Motivational Interviewing Training Platform) application covering API routes, security concerns, authentication flows, and codebase organization.

---

## ✅ Working Features

| Feature | Endpoint | Status |
|---------|----------|--------|
| Debug Endpoint | `GET /api/debug/supabase` | ✅ RPC method, efficient |
| List Scenarios | `GET /api/scenarios` | ✅ Returns 8 scenarios |
| List MI Modules | `GET /api/mi-practice/modules` | ✅ Returns 45 modules |
| Get Module by ID | `GET /api/mi-practice/modules/[id]` | ✅ Working |
| Turn Processing | `POST /api/scenarios/turn` | ✅ Functional |
| Static Pages | `/chat`, `/mi-practice`, etc. | ✅ Rendering |

---

## ⚠️ Critical Issues Requiring Immediate Action

### 1. Missing RLS Policies for Anonymous Inserts

**Severity:** HIGH - Blocks core functionality

**Issue:** Anonymous users cannot create attempts (`scenario_attempts`, `mi_practice_attempts`) due to missing INSERT RLS policies.

**Evidence:**
```json
{"error":"new row violates row-level security policy for table \"mi_practice_attempts\""}
```

**Fix:** Run migration `0010_add_anon_insert_to_attempts.sql` in Supabase SQL Editor

```sql
-- File: supabase/migrations/current/0010_add_anon_insert_to_attempts.sql
-- Adds INSERT and UPDATE permissions for anon users on attempts tables
```

---

### 2. Password Reset Functionality Missing

**Severity:** MEDIUM - Users cannot recover passwords

**Issue:** No password reset flow exists. Login page has no "forgot password" link or endpoint.

**Missing Components:**
- Password reset page (`/reset-password`, `/forgot-password`)
- Password reset API endpoint (`/api/auth/reset-password`)
- Password reset email sending functionality
- Reset token generation and validation

**Recommendation:** Implement Supabase's built-in password reset:
```typescript
// Add to lib/supabase/client-auth.ts
export async function resetPassword(email: string) {
  const supabase = createClient();
  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${window.location.origin}/reset-password`,
  });
  if (error) throw new Error(error.message);
}
```

---

### 3. Authentication Currently Disabled

**Severity:** MEDIUM - Security concern for production

**Issue:** Middleware bypasses all auth checks with `return NextResponse.next()` at line 69.

**Evidence from middleware.ts:**
```typescript
// Allow all routes for now to prevent redirect loops
// TODO: Re-enable auth protection once session handling is stable
return NextResponse.next();
```

**Risk:** Anyone can access dashboard, scenarios, and user data without authentication.

**Recommendation:** Re-enable auth checks after:
1. Testing session handling
2. Implementing proper protected route redirects
3. Ensuring anon RLS policies protect sensitive data

---

## 🔒 Security Analysis

### Passed Checks ✅

| Check | Result |
|-------|--------|
| No hardcoded API keys/secrets | ✅ Pass |
| No `eval()` or dangerous HTML patterns | ✅ Pass |
| Environment variables used correctly | ✅ Pass |
| Supabase service_role not exposed | ✅ Pass |
| SQL injection (parameterized queries) | ✅ Pass |

### Areas of Concern ⚠️

| Issue | Risk | Recommendation |
|-------|------|----------------|
| 10x `(supabase as any)` casts | Type safety bypass | Create proper Supabase types |
| Anon users can read all attempts | Data exposure | RLS policies should filter by user_id |
| Auth disabled in middleware | Unauthorized access | Re-enable when stable |
| No rate limiting on API routes | DoS risk | Add rate limiting middleware |
| No CSRF protection | CSRF risk | Ensure Next.js CSRF tokens active |

---

## 📁 Codebase Organization Issues

### 1. Duplicate/Inconsistent Patterns

**Type assertions workaround:** 10 occurrences of `(supabase as any)` spread across 6 files:
- `lib/supabase/queries.ts` (3)
- `lib/supabase/client-queries.ts` (2)
- `app/api/scenarios/route.ts` (1)
- `app/api/mi-practice/progress/route.ts` (2)
- `app/api/scenarios/attempts/[attemptId]/end/route.ts` (1)
- `app/api/mi-practice/modules/route.ts` (1)

**Fix:** Generate proper Supabase types or create a typed wrapper function.

### 2. Route Inconsistency

**Scenario start route pattern:**
- Documented as: `POST /api/scenarios/{id}/start`
- Actual implementation: `POST /api/scenarios` with `scenarioId` in body

**Impact:** Confusing for API consumers. Documentation should match implementation.

### 3. Table Name Mismatches (Already Fixed)

- ✅ `learning_modules` → `mi_practice_modules`
- ✅ `user_profiles` → `profiles`
- ✅ `persona_name` → `title`

---

## 🔄 API Routes Testing Status

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/debug/supabase` | GET | ✅ Working | RPC method efficient |
| `/api/scenarios` | GET | ✅ Working | Returns 8 scenarios |
| `/api/scenarios` | POST | ⚠️ Blocked | Needs migration 0010 |
| `/api/mi-practice/modules` | GET | ✅ Working | Returns 45 modules |
| `/api/mi-practice/modules` | POST | ⚠️ Blocked | Needs migration 0010 |
| `/api/mi-practice/modules/[id]` | GET | ✅ Working | Single module fetch |
| `/api/mi-practice/progress` | POST | ⚠️ Untested | Needs migration 0010 first |
| `/api/scenarios/turn` | POST | ✅ Working | Turn processing |
| `/api/scenarios/attempts/[id]/end` | POST | ⚠️ Untested | Needs migration 0010 |

---

## 📋 Action Items

### Immediate (Before Production)

1. **Run migration 0010** in Supabase SQL Editor
   ```bash
   # File location
   supabase/migrations/current/0010_add_anon_insert_to_attempts.sql
   ```

2. **Test all POST endpoints** after migration
3. **Re-enable authentication** in middleware
4. **Add password reset flow**

### Short-term

1. Create proper TypeScript types for Supabase
2. Implement rate limiting
3. Add API documentation
4. Fix route documentation vs implementation mismatch

### Long-term

1. Add comprehensive error logging
2. Implement analytics/tracking
3. Add user activity audit logs
4. Create automated testing suite

---

## 🏥 Health Check

**Server:** Running on `http://localhost:3000`
**Build:** ✅ Successful
**Database Connection:** ✅ Connected
**RPC Function:** ✅ Working

---

## 📊 Database Stats (from RPC)

| Table | Count | Status |
|-------|-------|--------|
| Scenarios | 8 | ✅ Active |
| MI Practice Modules | 45 | ✅ Active |
| Scenario Attempts | 18 | ✅ Tracking |
| Profiles | 3 | ✅ Created |

---

## 🚀 Deployment Checklist

- [x] Build succeeds without errors
- [x] TypeScript compilation passes
- [x] Environment variables configured
- [ ] Run migration 0010 in production
- [ ] Enable authentication in middleware
- [ ] Test all API routes in production
- [ ] Verify RLS policies protect user data
- [ ] Add password reset functionality
- [ ] Set up error monitoring
- [ ] Configure rate limiting

---

**Generated:** 2026-02-08
**Next Review:** After migration 0010 is applied
