-- Database schema for HTN 2025 Chat Application

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    video_file VARCHAR(255) DEFAULT 'sample_video.mp4',
    video_url TEXT,
    is_master BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    active BOOLEAN DEFAULT true
);

-- Session Users (ephemeral)
CREATE TABLE IF NOT EXISTS session_users (
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    joined_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (session_id, user_id)
);

-- Chat Messages (ephemeral)
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'user', -- 'user' or 'ai'
    is_ai_directed BOOLEAN DEFAULT false, -- whether message was intended for AI
    reply_to_message_id UUID REFERENCES chat_messages(id), -- message this is replying to
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(active);
CREATE INDEX IF NOT EXISTS idx_session_users_session_id ON session_users(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);

-- Video Analysis Table
CREATE TABLE IF NOT EXISTS video_analysis (
    id BIGSERIAL PRIMARY KEY,
    video_id VARCHAR(255) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    model_output JSON NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (video_id, model_type)
);

-- Create the index for video_analysis
CREATE INDEX IF NOT EXISTS idx_video_id ON video_analysis(video_id);

-- Migration: Add new fields to chat_messages table (safe for existing installations)
DO $$ 
BEGIN
    -- Add is_ai_directed column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'chat_messages' AND column_name = 'is_ai_directed') THEN
        ALTER TABLE chat_messages ADD COLUMN is_ai_directed BOOLEAN DEFAULT false;
    END IF;
    
    -- Add reply_to_message_id column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'chat_messages' AND column_name = 'reply_to_message_id') THEN
        ALTER TABLE chat_messages ADD COLUMN reply_to_message_id UUID REFERENCES chat_messages(id);
    END IF;
END $$;
