# Authentication Reinstated - Implementation Summary

## Overview

Server-side authentication has been reinstated to protect API endpoints. The system now validates Supabase JWT tokens and checks the `profiles` table for user roles.

---

## Changes Made

### 1. Created Authentication Dependencies

**File**: `src/auth/auth_dependencies.py`

Provides FastAPI dependencies for route protection:

```python
# Get current authenticated user
current_user: AuthenticatedUser = Depends(get_current_user)

# Require FULL role access
current_user: AuthenticatedUser = Depends(require_full_access)

# Optional auth (returns None if not authenticated)
current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional)
```

**How it works**:
1. Extracts JWT token from `Authorization: Bearer <token>` header
2. Validates token with Supabase: `supabase.auth.get_user(token)`
3. Fetches user role from `profiles` table
4. Returns `AuthenticatedUser` object with `user_id`, `email`, and `role`

### 2. Updated API Routes

**File**: `src/api/routes/enhanced_chat.py`

Both chat endpoints now require authentication:

```python
@router.post("/start")
async def start_enhanced_conversation(
    request: StartConversationRequest,
    current_user: AuthenticatedUser = Depends(require_full_access)  # ← Added
):
    logger.info(f"User {current_user.email} starting conversation...")
    # ... rest of endpoint

@router.post("/send")
async def send_enhanced_message(
    request: EnhancedChatRequest,
    current_user: AuthenticatedUser = Depends(require_full_access)  # ← Added
):
    # ... endpoint implementation
```

---

## User Roles

Based on the `profiles` table you provided:

### FULL Role
- **Email**: `test@mapspractice.org`
- **Access**: Can use all chat features
- **Endpoints allowed**: `/api/chat/start`, `/api/chat/send`, all other features

### CONTROL Role
- **Email**: `control@mapspractice.org`
- **Access**: Limited (currently redirected to `/thank-you-locked` page)
- **Endpoints blocked**: All chat endpoints (returns 403 Forbidden)

---

## Authentication Flow

### 1. User Login (Client-Side)

**File**: `static/auth.html`

```javascript
// User logs in
const { data, error } = await supabase.auth.signInWithPassword({
    email: email,
    password: password
});

// Fetch user role from profiles table
const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', data.user.id)
    .single();

// Store role in localStorage
localStorage.setItem('userRole', profile.role);

// Redirect based on role
if (profile.role === 'FULL') {
    window.location.href = '/welcome';
} else if (profile.role === 'CONTROL') {
    window.location.href = '/thank-you-locked';
}
```

### 2. API Request with Token

Client must send JWT token in headers:

```javascript
const session = await supabase.auth.getSession();
const token = session.data.session.access_token;

fetch('/api/chat/start', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,  // ← Required
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ persona_id: 'terry' })
});
```

### 3. Server-Side Validation

**Flow**:
1. FastAPI receives request with `Authorization: Bearer <token>`
2. `get_current_user()` dependency extracts token
3. Calls `supabase.auth.get_user(token)` to validate
4. Queries `profiles` table for user role
5. If `require_full_access()` used, checks `role == "FULL"`
6. Returns `AuthenticatedUser` or raises `HTTPException`

**Success Response**:
- Returns `AuthenticatedUser` with `user_id`, `email`, `role`
- Endpoint proceeds normally

**Error Responses**:
- **401 Unauthorized**: Token missing, invalid, or expired
- **403 Forbidden**: User authenticated but doesn't have FULL role

---

## Testing Authentication

### Test with FULL Role User

```bash
# 1. Get token from Supabase (login as test@mapspractice.org)
# 2. Make authenticated request

curl -X POST http://localhost:8000/api/chat/start \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"persona_id": "terry"}'

# Expected: 200 OK with conversation data
```

### Test with CONTROL Role User

```bash
# 1. Get token from Supabase (login as control@mapspractice.org)
# 2. Make authenticated request

curl -X POST http://localhost:8000/api/chat/start \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"persona_id": "terry"}'

# Expected: 403 Forbidden
# {
#   "detail": "Access denied - FULL role required (you have CONTROL)"
# }
```

### Test without Authentication

```bash
curl -X POST http://localhost:8000/api/chat/start \
  -H "Content-Type: application/json" \
  -d '{"persona_id": "terry"}'

# Expected: 401 Unauthorized
# {
#   "detail": "Not authenticated - missing token"
# }
```

---

## Client-Side Integration

The client-side JavaScript already includes auth guards in `static/js/authGuard.js`:

```javascript
async function requireAuth() {
    const { data: { session } } = await supabase.auth.getSession();

    if (!session) {
        window.location.href = '/auth';
        return false;
    }

    return true;
}
```

All protected pages (welcome, persona-select, chat, etc.) call `requireAuth()` on page load.

**No changes needed to client-side code** - it already sends tokens correctly via Supabase client library.

---

## Security Considerations

### ✅ What's Protected

1. **API Endpoints**: `/api/chat/start` and `/api/chat/send` require valid JWT + FULL role
2. **Token Validation**: Server validates tokens with Supabase auth service
3. **Role-Based Access**: Users with CONTROL role cannot access chat features
4. **Profile Verification**: Every request checks `profiles` table for role

### ⚠️ Current Limitations

1. **No Rate Limiting**: Auth endpoints not rate-limited (could add in future)
2. **No Session Refresh Logic**: Client handles token refresh, server doesn't force refresh
3. **CONTROL Role Functionality**: Currently blocked from chat, but no alternative features defined
4. **No Admin User Management**: Users must be added to `profiles` table manually

### 🔒 Best Practices Implemented

- JWT tokens validated on every request
- Role stored in database (not in JWT claims)
- Proper HTTP status codes (401 for auth, 403 for authorization)
- Logging of authentication events
- Clear error messages for debugging

---

## Profiles Table Structure

```sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    email TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('FULL', 'CONTROL')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Current Users**:
```json
[
  {
    "id": "73f08f90-6b02-42b9-a1dd-5b4a7c854f07",
    "email": "test@mapspractice.org",
    "role": "FULL"
  },
  {
    "id": "01c5046d-3854-46af-8fe6-012c893171c0",
    "email": "control@mapspractice.org",
    "role": "CONTROL"
  }
]
```

---

## Adding New Users

To add a new user with FULL access:

1. **Create Supabase Auth User** (via Supabase dashboard or API)
2. **Add Profile Entry**:

```sql
INSERT INTO profiles (id, email, role)
VALUES (
    'USER_UUID_FROM_AUTH_USERS',
    'newuser@mapspractice.org',
    'FULL'
);
```

**Note**: Sign-up is disabled in the UI (`static/auth.html` line 255). Admin must create users manually.

---

## Rollback Instructions

If you need to temporarily disable authentication:

**Option 1**: Comment out dependency in routes

```python
# @router.post("/start")
# async def start_enhanced_conversation(
#     request: StartConversationRequest,
#     current_user: AuthenticatedUser = Depends(require_full_access)  # ← Comment this line
# ):

@router.post("/start")
async def start_enhanced_conversation(request: StartConversationRequest):
    # ... endpoint works without auth
```

**Option 2**: Modify `require_full_access()` to always return dummy user

```python
# src/auth/auth_dependencies.py
async def require_full_access(...) -> AuthenticatedUser:
    # Bypass for testing
    return AuthenticatedUser(
        user_id="test-user",
        email="test@example.com",
        role="FULL"
    )
```

---

## Summary

✅ **Authentication reinstated** on `/api/chat/start` and `/api/chat/send`
✅ **Validates JWT tokens** with Supabase auth service
✅ **Checks profiles table** for user role
✅ **FULL role required** for chat access
✅ **CONTROL role blocked** from chat features
✅ **Client-side already compatible** - no frontend changes needed
✅ **Proper HTTP status codes** - 401 Unauthorized, 403 Forbidden
✅ **Logging enabled** for audit trail

The system is now secure and only authenticated users with FULL role can access chat features.
