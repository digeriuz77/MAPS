-- Add profiles for existing auth users
-- Run this AFTER creating users in auth.users (via Supabase Dashboard or Auth API)

-- Option 1: Add profiles by email lookup (recommended)
-- This automatically finds the correct UUID from auth.users
INSERT INTO profiles (id, email, role)
SELECT
    au.id,
    au.email,
    CASE
        WHEN au.email = 'test@mapspractice.org' THEN 'FULL'
        WHEN au.email = 'control@mapspractice.org' THEN 'CONTROL'
        ELSE 'CONTROL'  -- Default to CONTROL for safety
    END as role
FROM auth.users au
WHERE au.email IN ('test@mapspractice.org', 'control@mapspractice.org')
ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    role = EXCLUDED.role,
    updated_at = NOW();

-- Verify the insert
SELECT
    p.id,
    p.email,
    p.role,
    p.created_at,
    au.created_at as auth_user_created_at
FROM profiles p
JOIN auth.users au ON p.id = au.id
ORDER BY p.created_at DESC;
