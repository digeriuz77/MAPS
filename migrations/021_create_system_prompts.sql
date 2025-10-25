-- Migration: Create system_prompts table and add reflection summary prompt
-- Purpose: Store all system prompts in database per project specification
-- Date: 2025-10-18

-- Create system_prompts table
CREATE TABLE IF NOT EXISTS system_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_key VARCHAR(100) UNIQUE NOT NULL,
    prompt_name VARCHAR(255) NOT NULL,
    prompt_text TEXT NOT NULL,
    model_recommended VARCHAR(50),
    temperature FLOAT DEFAULT 0.7,
    max_tokens INT DEFAULT 500,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create index on prompt_key for fast lookups
CREATE INDEX IF NOT EXISTS idx_system_prompts_key ON system_prompts(prompt_key);

-- Enable Row Level Security
ALTER TABLE system_prompts ENABLE ROW LEVEL SECURITY;

-- Policy for service role access
CREATE POLICY "Service role can manage system_prompts" ON system_prompts
FOR ALL USING (auth.role() = 'service_role');

-- Insert reflection summary prompt
INSERT INTO system_prompts (
    prompt_key,
    prompt_name,
    prompt_text,
    model_recommended,
    temperature,
    max_tokens
) VALUES (
    'reflection_summary',
    'Reflection Summary Generation',
    'Based on the following reflection responses, create a concise, cohesive summary (2-3 paragraphs) that synthesizes the practitioner''s insights:

What went well: {question1}

Struggles: {question2}

Future improvements: {question3}

Provide an encouraging, professional summary that highlights key insights and growth opportunities. Focus on patterns, strengths to build on, and specific actionable improvements. Use a supportive, coaching tone that acknowledges both successes and areas for development.',
    'gpt-4.1-nano',
    0.7,
    500
) ON CONFLICT (prompt_key) DO UPDATE SET
    prompt_text = EXCLUDED.prompt_text,
    model_recommended = EXCLUDED.model_recommended,
    updated_at = NOW();

-- Grant permissions
GRANT ALL ON system_prompts TO service_role;
