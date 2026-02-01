-- System Metrics Table Migration
-- Stores persistent metrics for LLM usage and system operations
-- This table complements the in-memory metrics service for reliability across restarts

CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    llm_calls_total INTEGER DEFAULT 0,
    errors_total INTEGER DEFAULT 0,
    summaries_created INTEGER DEFAULT 0,
    consolidations_added INTEGER DEFAULT 0,
    consolidations_updated INTEGER DEFAULT 0,
    decay_updated INTEGER DEFAULT 0,
    decay_pruned INTEGER DEFAULT 0,
    llm_calls_by_provider JSONB DEFAULT '{}'::jsonb,
    llm_calls_by_model JSONB DEFAULT '{}'::jsonb,
    llm_latency_ms_by_model JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Add indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_system_metrics_created_at ON system_metrics(created_at DESC);

-- Add comment to table
COMMENT ON TABLE system_metrics IS 'Persistent storage for system metrics including LLM usage and memory operations';

-- Sample initial values (optional)
INSERT INTO system_metrics (
    llm_calls_total, errors_total, summaries_created, 
    consolidations_added, consolidations_updated, decay_updated, decay_pruned,
    llm_calls_by_provider, llm_calls_by_model, llm_latency_ms_by_model
) 
VALUES (
    0, 0, 0, 0, 0, 0, 0,
    '{}', '{}', '{}'
)
ON CONFLICT DO NOTHING;

-- Grant permissions (adjust according to your security requirements)
-- For public access (consider stricter permissions in production)
GRANT ALL PRIVILEGES ON TABLE system_metrics TO authenticated;
GRANT ALL PRIVILEGES ON TABLE system_metrics TO service_role;
