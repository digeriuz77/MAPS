-- Migration: Create profiles table for user roles
-- Purpose: Store user roles (FULL, CONTROL) for authentication and access control
-- Dependencies: Requires Supabase auth.users table to exist

-- Create profiles table
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('FULL', 'CONTROL')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);

-- Create index on role for filtering
CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role);

-- Enable Row Level Security (RLS)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can read their own profile
CREATE POLICY "Users can view their own profile"
    ON profiles
    FOR SELECT
    USING (auth.uid() = id);

-- RLS Policy: Service role can manage all profiles (for admin operations)
CREATE POLICY "Service role can manage all profiles"
    ON profiles
    FOR ALL
    USING (auth.role() = 'service_role');

-- Function: Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_profiles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Update updated_at on row modification
CREATE TRIGGER trigger_update_profiles_timestamp
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_profiles_updated_at();

-- Note: Only insert profiles for users that already exist in auth.users
-- If you need to create new auth users, do it through Supabase Dashboard or Auth API first
--
-- Example: Insert profiles for existing auth users
-- Uncomment and modify the IDs to match your actual auth.users entries:
--
-- INSERT INTO profiles (id, email, role, created_at, updated_at)
-- SELECT
--     id,
--     email,
--     'FULL' as role,  -- Change to 'CONTROL' for limited access
--     NOW() as created_at,
--     NOW() as updated_at
-- FROM auth.users
-- WHERE email IN ('test@mapspractice.org', 'control@mapspractice.org')
-- ON CONFLICT (id) DO UPDATE SET
--     email = EXCLUDED.email,
--     role = EXCLUDED.role,
--     updated_at = NOW();

-- Manual insert (only if you know the exact UUIDs from auth.users):
-- INSERT INTO profiles (id, email, role)
-- VALUES
--     ('73f08f90-6b02-42b9-a1dd-5b4a7c854f07', 'test@mapspractice.org', 'FULL'),
--     ('01c5046d-3854-46af-8fe6-012c893171c0', 'control@mapspractice.org', 'CONTROL')
-- ON CONFLICT (id) DO NOTHING;

-- Comment the table and columns
COMMENT ON TABLE profiles IS 'User profiles with role-based access control (FULL or CONTROL)';
COMMENT ON COLUMN profiles.id IS 'User ID (references auth.users)';
COMMENT ON COLUMN profiles.email IS 'User email address';
COMMENT ON COLUMN profiles.role IS 'User role: FULL (full access) or CONTROL (limited access)';
COMMENT ON COLUMN profiles.created_at IS 'Profile creation timestamp';
COMMENT ON COLUMN profiles.updated_at IS 'Profile last update timestamp';
