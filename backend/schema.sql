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

-- Video Analysis Table (legacy - keeping for backward compatibility)
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

-- New normalized video transcript/analysis table
CREATE TABLE IF NOT EXISTS video_transcript (
    id BIGSERIAL PRIMARY KEY,
    video_id VARCHAR(255) NOT NULL,
    timestamp_text VARCHAR(10) NOT NULL, -- "00:04" format
    timestamp_seconds INTEGER NOT NULL, -- 4 seconds
    text_content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'transcript', -- 'transcript', 'description', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (video_id, content_type, timestamp_seconds)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_video_transcript_video_id ON video_transcript(video_id);
CREATE INDEX IF NOT EXISTS idx_video_transcript_timestamp_seconds ON video_transcript(timestamp_seconds);
CREATE INDEX IF NOT EXISTS idx_video_transcript_video_timestamp ON video_transcript(video_id, timestamp_seconds);
CREATE INDEX IF NOT EXISTS idx_video_transcript_content_type ON video_transcript(content_type);

-- TV Show Information Table
CREATE TABLE IF NOT EXISTS tv_show_info (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_url TEXT UNIQUE NOT NULL,
    show_type VARCHAR(50) NOT NULL, -- 'TV Show', 'Movie', 'Other', etc.
    title VARCHAR(255),
    season INTEGER,
    episode INTEGER,
    tmdb_id INTEGER, -- The Movie Database ID
    tmdb_data JSONB, -- Full TMDB response data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for tv_show_info
CREATE INDEX IF NOT EXISTS idx_tv_show_info_video_url ON tv_show_info(video_url);
CREATE INDEX IF NOT EXISTS idx_tv_show_info_tmdb_id ON tv_show_info(tmdb_id);

-- Video Processing Status Table
CREATE TABLE IF NOT EXISTS video_processing_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_url TEXT UNIQUE NOT NULL,
    session_id UUID REFERENCES sessions(id),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    progress INTEGER DEFAULT 0, -- 0-100
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create index for video_processing_status
CREATE INDEX IF NOT EXISTS idx_video_processing_status_video_url ON video_processing_status(video_url);
CREATE INDEX IF NOT EXISTS idx_video_processing_status_session_id ON video_processing_status(session_id);

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

CREATE TABLE IT NOT EXISTS video_processing_status (
    id UUID PRIMARY KEY,
    video_url TEXT UNIQUE NOT NULL,
    session_id UUID NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add index for faster lookups
CREATE INDEX idx_video_processing_status_video_url ON video_processing_status(video_url);
CREATE INDEX idx_video_processing_status_status ON video_processing_status(status);