-- Create table for persona greetings
-- These are random opening messages that personas can use to start conversations
-- instead of the fixed preloaded conversation

CREATE TABLE IF NOT EXISTS persona_greetings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    greeting_text TEXT NOT NULL,
    greeting_type VARCHAR(50) DEFAULT 'general',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert diverse greeting options
INSERT INTO persona_greetings (greeting_text, greeting_type, is_active) VALUES
-- Casual/friendly greetings
('Hi there! Good to see you today. How are things going?', 'casual', true),
('Hello! Nice to connect with you. What''s on your mind?', 'casual', true),
('Hey! Thanks for taking the time to chat. How has your day been?', 'casual', true),
('Hi! It''s good to sit down together. How are you feeling today?', 'casual', true),

-- Professional/workplace greetings  
('Good to see you. What would you like to focus on today?', 'professional', true),
('Hello. I''m glad we could find time to chat. What''s been on your mind lately?', 'professional', true),
('Hi there. Thanks for setting aside time for this conversation. How are things?', 'professional', true),
('Good to connect with you today. What would be most helpful to talk about?', 'professional', true),

-- Warm/supportive greetings
('Hi! I''m really glad you''re here. How are you doing today?', 'supportive', true),
('Hello! It''s wonderful to see you. What''s been happening in your world?', 'supportive', true),
('Hi there! I''ve been looking forward to our chat. How are you feeling?', 'supportive', true),
('Good to see you! I hope you''re doing well. What would you like to talk about?', 'supportive', true),

-- Reflective/thoughtful greetings
('Hi. I''m curious to hear what''s been on your mind lately. How are things?', 'reflective', true),
('Hello. Sometimes it''s good to step back and reflect. How has everything been going?', 'reflective', true),
('Hi there. I find these conversations really valuable. What''s been significant for you recently?', 'reflective', true),
('Good to see you. I''m interested to hear your perspective on how things have been.', 'reflective', true);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_persona_greetings_active ON persona_greetings(is_active);
CREATE INDEX IF NOT EXISTS idx_persona_greetings_type ON persona_greetings(greeting_type);