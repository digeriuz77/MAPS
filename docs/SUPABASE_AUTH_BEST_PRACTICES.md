# Supabase Authentication Best Practices

## The "Dual Authentication Mismatch" Problem

### What Went Wrong in mi-learning-platform

The app had **two separate authentication mechanisms** that were not synchronized:

1. **Backend API** (`/api/v1/auth/login`):
   - User submits email/password to backend
   - Backend calls Supabase server-side
   - Backend returns JWT to browser
   - Browser stores JWT in localStorage
   - **Result**: Authenticated backend requests

2. **Browser Supabase Client** (CDN script):
   - Created with anon key: `supabase.createClient(url, anonKey)`
   - **Never authenticated** - no `supabase.auth.signInWithPassword()` call
   - All queries were **anonymous**
   - RLS policies blocked requests (406 errors)
   - **Result**: Admin features never appeared

### Why This Happened

The browser Supabase client maintains its **own session** separate from the backend JWT. Even though the user was "logged in" via the backend API, the browser client had no session context.

When code tried:
```javascript
supabaseClient.from('users').select('role').eq('id', userId)
```

Supabase saw an **anonymous request** because `auth.uid()` was null. The RLS policy:
```sql
USING (auth.uid() = id)
```

Blocked the request with `406 Not Acceptable`.

### The Fix

1. **Removed browser Supabase client** from app.js and admin.js
2. **Created backend API endpoints** using service-role client (bypasses RLS)
3. **Routed all database queries through backend API** with JWT authentication
4. **JWT sent with requests**: `fetch(url, { headers: { Authorization: \`Bearer ${token}\` } })`

---

## MAPS Next.js Architecture (Correct Approach)

### Why MAPS Doesn't Have This Problem

MAPS uses **`@supabase/ssr`** which is fundamentally different:

| Aspect | mi-learning-platform (BROKEN) | MAPS Next.js (CORRECT) |
|--------|-------------------------------|-------------------------|
| Auth Library | CDN script (`@supabase/supabase-js`) | `@supabase/ssr` |
| Session Storage | Separate backend JWT + browser client | **Shared via cookies** |
| Server Client | Not used | `createServerClient()` reads cookies |
| Browser Client | Anon key, never authenticated | `createBrowserClient()` reads cookies |
| RLS | Blocked (anonymous) | **Works** (auth.uid() from cookies) |

### Key Points

1. **Single Source of Truth**: Authentication state is in **cookies only**
2. **Server and browser share cookies**: Both clients read the same session
3. **No manual browser auth needed**: Server establishes session, browser inherits it
4. **RLS works out of the box**: `auth.uid()` is available from cookies

### Code Patterns

#### ✅ Correct: Server Component (uses cookies)
```typescript
// app/dashboard/page.tsx
import { createClient } from "@/lib/supabase/server";

export default async function DashboardPage() {
  const supabase = await createClient();  // Reads cookies
  const { data: { user } } = await supabase.auth.getUser();
  // User is authenticated if session exists in cookies
}
```

#### ✅ Correct: Server Action (uses cookies)
```typescript
// app/api/scenarios/route.ts
import { createClient } from "@/lib/supabase/server";

export async function POST(req: NextRequest) {
  const supabase = await createClient();  // Reads cookies
  // Can access user data via auth.uid() in RLS policies
}
```

#### ✅ Correct: Client Component with Server Data
```typescript
// Use server components to fetch data, pass to client
// Or use server actions for mutations
```

#### ⚠️ Use with Caution: Direct Browser Client
```typescript
// components/chat.tsx (client component)
import { createClient } from "@/lib/supabase/client";

const supabase = createClient();  // Reads cookies, will have session if logged in
// This works because @supabase/ssr shares cookies between server and browser
// But prefer server actions for mutations
```

### Anti-Patterns to Avoid

#### ❌ Don't: Mix backend JWT with browser Supabase client
```typescript
// WRONG: Two separate auth mechanisms
const backendJWT = localStorage.getItem('token');  // From API login
const supabase = createBrowserClient(url, key);     // Separate session!
// supabase has NO session even though backendJWT exists
```

#### ❌ Don't: Use anon key for admin operations
```typescript
// WRONG: Anon key can't bypass RLS
const supabase = createClient();  // Uses anon key
const { data } = await supabase.from('users').select('*');  // Blocked by RLS!
```

#### ✅ Instead: Use admin client for privileged operations
```typescript
// CORRECT: Service role bypasses RLS
import { createAdminClient } from "@/lib/supabase/server";

const supabase = createAdminClient();  // Uses service role key
const { data } = await supabase.from('users').select('*');  // Works!
```

---

## Quick Reference

### When to use each client

| Client | When to Use | Session Source |
|--------|-------------|-----------------|
| `createClient()` (server) | Server Components, Route Handlers, Middleware | Cookies |
| `createAdminClient()` | Admin operations (bypass RLS) | Service role key |
| `createClient()` (browser) | Client Components, Subscriptions | Cookies (shared) |
| Server Actions | Mutations from client components | Cookies |

### Environment Variables Needed

```env
# Required for all clients
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Required for admin operations (NEVER expose to client!)
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

---

## Troubleshooting

### Symptom: "406 Not Acceptable" or "RLS policy blocked"
**Cause**: Query made with anonymous/unauthenticated client
**Fix**: Ensure client has session (use server client or verify cookies)

### Symptom: "auth.uid() is null"
**Cause**: No session in cookies
**Fix**: User needs to log in via `/login` page which sets cookie session

### Symptom: Admin features not showing
**Cause**: User doesn't have admin role in database
**Fix**: Check `user_profiles.role` field, ensure admin client used for role check

---

## Migration Checklist

If migrating from CDN-based to SSR-based:

- [ ] Replace `@supabase/supabase-js` with `@supabase/ssr`
- [ ] Update server components to use `createServerClient()`
- [ ] Update middleware to refresh session from cookies
- [ ] Remove manual `signInWithPassword()` calls from browser
- [ ] Ensure auth callback sets cookies properly
- [ ] Test RLS policies work with cookie-based auth
- [ ] Remove any localStorage JWT handling (not needed)
