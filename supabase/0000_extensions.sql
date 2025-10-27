-- 0000_extensions.sql
-- Enable required extensions for UUID generation
create extension if not exists pgcrypto; -- for gen_random_uuid()
