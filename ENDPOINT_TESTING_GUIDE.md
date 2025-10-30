# Endpoint Testing Guide

This guide explains how to test all API endpoints to ensure they're working correctly with proper authentication.

## Overview

The test script (`test_all_endpoints.py`) validates:
- ✅ All endpoints are accessible
- ✅ Authentication is working correctly
- ✅ FULL vs CONTROL user permissions are enforced
- ✅ Response status codes are correct
- ✅ No unexpected errors

## Prerequisites

1. **Python packages:**
   ```bash
   pip install httpx
   ```

2. **Authentication tokens:**
   You need JWT tokens for both FULL and CONTROL users.

### Getting Authentication Tokens

#### Option 1: From Frontend (Recommended)
1. Log in to your deployed app as a FULL user
2. Open browser DevTools (F12) → Application → Local Storage
3. Find the `supabase.auth.token` key
4. Copy the JWT token (long string starting with `eyJ...`)
5. Repeat for CONTROL user

#### Option 2: Using Supabase Dashboard
1. Go to Supabase Dashboard → Authentication → Users
2. Create test users with FULL and CONTROL roles
3. Use the API to sign in and get tokens:
   ```bash
   curl -X POST 'https://YOUR_PROJECT.supabase.co/auth/v1/token?grant_type=password' \
     -H "apikey: YOUR_ANON_KEY" \
     -H "Content-Type: application/json" \
     -d '{"email": "full-user@test.com", "password": "your-password"}'
   ```

## Running Tests

### Local Testing (Development)

```bash
# Set environment variables
$env:BASE_URL="http://localhost:8000"
$env:FULL_USER_TOKEN="eyJ...your-full-token"
$env:CONTROL_USER_TOKEN="eyJ...your-control-token"

# Run tests
python test_all_endpoints.py
```

### Production Testing (Railway)

```bash
# Set production URL
$env:BASE_URL="https://your-app.railway.app"
$env:FULL_USER_TOKEN="eyJ...your-full-token"
$env:CONTROL_USER_TOKEN="eyJ...your-control-token"

# Run tests
python test_all_endpoints.py
```

## What Gets Tested

### Chat Endpoints (`/api/chat/*`)
- ✅ Get personas list (public)
- ✅ Start conversation (FULL & CONTROL users)
- ✅ Send messages (FULL & CONTROL users)

### Analysis Endpoints (`/api/v1/analysis/*`)
- ✅ Submit transcript for analysis (FULL only)
- ✅ CONTROL users correctly blocked (403 expected)
- ✅ Check analysis status
- ✅ Get analysis results

### Reflection Endpoints (`/api/reflection/*`)
- ✅ Health check (public)
- ✅ Generate reflection summary (FULL only)
- ✅ Send reflection email (FULL only)
- ✅ CONTROL users correctly blocked (403 expected)

### Feedback Endpoints (`/api/feedback/*`)
- ✅ Submit user feedback (FULL only)
- ✅ Get feedback statistics (public)
- ✅ CONTROL users correctly blocked (403 expected)

### Metrics & Web Endpoints
- ✅ Get metrics (public)
- ✅ List web personas (public)
- ✅ Get dialogue scenarios (public)

## Understanding Test Results

### Expected Results

#### ✅ PASSED Tests
- **200/201**: Successful request
- **403**: CONTROL user correctly blocked from FULL-only endpoint
- **401**: Unauthenticated user correctly blocked from protected endpoint

#### ❌ FAILED Tests
- **500**: Server error (needs investigation)
- **404**: Endpoint not found (route configuration issue)
- **401** on authenticated request: Auth middleware broken
- **200** when 403 expected: Permission check not working

### Test Output

The script generates two outputs:

1. **Console Output**: Real-time test results
   ```
   Test 1: Get Enhanced Personas
     Method: GET /api/chat/personas
     Auth Required: False, FULL Only: False
     Result: ✓ PASSED (Status: 200)
   ```

2. **JSON Report**: Detailed results file
   - Filename: `endpoint_test_results_YYYYMMDD_HHMMSS.json`
   - Contains: All requests, responses, timings, errors

## Common Issues & Fixes

### Issue: All tests failing with "Connection refused"
**Cause**: Server not running
**Fix**: Start your FastAPI server
```bash
uvicorn src.main:app --reload
```

### Issue: All auth tests failing with 401
**Cause**: Invalid or expired tokens
**Fix**: Get fresh JWT tokens from login

### Issue: CONTROL user accessing FULL-only endpoints (200 instead of 403)
**Cause**: Permission checks not implemented
**Fix**: Review endpoint dependencies - should use `require_full_access`

### Issue: CONTROL user blocked from chat endpoints (403 instead of 200)
**Cause**: Incorrect auth dependency on chat routes
**Fix**: Chat endpoints should use `get_current_user` not `require_full_access`

## Interpreting Results

### Critical Issues (Fix Immediately)
- ❌ Chat endpoints returning 403 for CONTROL users
- ❌ Analysis/Reflection/Feedback accessible by CONTROL users
- ❌ 500 errors on any endpoint
- ❌ Authentication not working (all auth tests failing)

### Warnings (Review)
- ⚠️ Slow response times (>5 seconds)
- ⚠️ Unexpected error messages in responses
- ⚠️ Missing data in responses

### Success Criteria
- ✅ All public endpoints accessible (200)
- ✅ CONTROL users can access chat (200)
- ✅ CONTROL users blocked from analysis/reflection/feedback (403)
- ✅ FULL users can access everything (200)
- ✅ Unauthenticated requests blocked appropriately (401)

## Next Steps After Testing

1. **All tests pass**: ✅ Deploy with confidence
2. **Some failures**: 
   - Review failed tests in JSON report
   - Fix issues in code
   - Re-run tests
   - Commit and deploy
3. **Many failures**: 
   - Check server logs for errors
   - Verify database connectivity
   - Ensure environment variables set correctly

## Automated Testing (CI/CD)

To integrate into CI/CD pipeline:

```yaml
# .github/workflows/test.yml
- name: Test Endpoints
  env:
    BASE_URL: ${{ secrets.STAGING_URL }}
    FULL_USER_TOKEN: ${{ secrets.FULL_TOKEN }}
    CONTROL_USER_TOKEN: ${{ secrets.CONTROL_TOKEN }}
  run: python test_all_endpoints.py
```

## Need Help?

- Check logs: Server errors provide detailed traceback
- Review auth configuration: `src/auth/auth_dependencies.py`
- Verify routes: Check route files in `src/api/routes/`
- Test individual endpoints: Use curl or Postman for debugging
