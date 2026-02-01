-- 0000_current_profiles.sql
-- CURRENT APPLICATION - MAPS MI Training Platform
-- Create profiles table for user roles (FULL, CONTROL)

CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('FULL', 'CONTROL')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role);

-- Enable RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own profile"
    ON profiles FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Service role can manage all profiles"
    ON profiles FOR ALL USING (auth.role() = 'service_role');

-- Auto-update timestamp
CREATE OR REPLACE FUNCTION update_profiles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_profiles_timestamp
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_profiles_updated_at();

COMMENT ON TABLE profiles IS 'User profiles with role-based access control (FULL or CONTROL)';
COMMENT ON COLUMN profiles.id IS 'User ID (references auth.users)';
COMMENT ON COLUMN profiles.email IS 'User email address';
COMMENT ON COLUMN profiles.role IS 'User role: FULL (full access) or CONTROL (limited access)';
