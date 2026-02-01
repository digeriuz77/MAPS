-- 0000_shared_extensions.sql
-- Enable required extensions for UUID generation and other features
-- This is a SHARED migration - required by both current and legacy applications

create extension if not exists pgcrypto; -- for gen_random_uuid()
