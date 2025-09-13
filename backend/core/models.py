from sqlalchemy import text
from .db import engine
from datetime import datetime
import uuid

class Session:
    @staticmethod
    def create(name, video_url=None, video_file='sample_video.mp4', is_master=False):
        """Create a new session"""
        session_id = str(uuid.uuid4())
        
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO sessions (id, name, video_file, video_url, is_master, created_at, active)
                    VALUES (:id, :name, :video_file, :video_url, :is_master, NOW(), true)
                """),
                {
                    "id": session_id,
                    "name": name,
                    "video_file": video_file,
                    "video_url": video_url,
                    "is_master": is_master
                }
            )
            
            # Get the created session
            result = conn.execute(
                text("""
                    SELECT id, name, video_file, video_url, is_master, created_at, active
                    FROM sessions 
                    WHERE id = :id
                """),
                {"id": session_id}
            ).fetchone()
            
            session_data = {
                'id': str(result[0]),
                'name': result[1],
                'video_file': result[2],
                'video_url': result[3],
                'is_master': result[4],
                'created_at': result[5].isoformat(),
                'active': result[6]
            }
            
            # Check for existing video analysis data if video_url is provided
            if video_url:
                video_analysis_data = VideoAnalysis.get_by_video_url(video_url)
                if video_analysis_data:
                    print(f"Found {len(video_analysis_data)} video analysis records for URL: {video_url}")
                    session_data['video_processed'] = True
                else:
                    print(f"No video analysis data found for URL: {video_url}")
                    session_data['video_processed'] = False
                    # Note: Video processing is now handled via separate API endpoint
            
            return session_data
    
    @staticmethod
    def get_all_active():
        """Get all active sessions with user counts"""
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT s.id, s.name, s.video_file, s.video_url, s.is_master, s.created_at, s.active,
                           COUNT(su.user_id) as user_count
                    FROM sessions s
                    LEFT JOIN session_users su ON s.id = su.session_id
                    WHERE s.active = true
                    GROUP BY s.id, s.name, s.video_file, s.video_url, s.is_master, s.created_at, s.active
                    ORDER BY s.created_at DESC
                """)
            ).fetchall()
            
            return [{
                'id': str(row[0]),
                'name': row[1],
                'video_file': row[2],
                'video_url': row[3],
                'is_master': row[4],
                'created_at': row[5].isoformat(),
                'active': row[6],
                'user_count': row[7]
            } for row in results]
    
    @staticmethod
    def get_by_id(session_id):
        """Get session by ID"""
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, name, video_file, video_url, is_master, created_at, active
                    FROM sessions 
                    WHERE id = :id AND active = true
                """),
                {"id": session_id}
            ).fetchone()
            
            if result:
                return {
                    'id': str(result[0]),
                    'name': result[1],
                    'video_file': result[2],
                    'video_url': result[3],
                    'is_master': result[4],
                    'created_at': result[5].isoformat(),
                    'active': result[6]
                }
            return None
    
    @staticmethod
    def deactivate_empty_sessions():
        """Deactivate sessions with no users"""
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE sessions 
                    SET active = false 
                    WHERE id NOT IN (
                        SELECT DISTINCT session_id 
                        FROM session_users
                    ) AND active = true
                """)
            )

class SessionUser:
    @staticmethod
    def add_user(session_id, user_id, display_name):
        """Add user to session"""
        with engine.begin() as conn:
            # Remove existing user entry if exists
            conn.execute(
                text("""
                    DELETE FROM session_users 
                    WHERE session_id = :session_id AND user_id = :user_id
                """),
                {"session_id": session_id, "user_id": user_id}
            )
            
            # Add new user entry
            conn.execute(
                text("""
                    INSERT INTO session_users (session_id, user_id, display_name, joined_at, last_seen)
                    VALUES (:session_id, :user_id, :display_name, NOW(), NOW())
                """),
                {
                    "session_id": session_id,
                    "user_id": user_id,
                    "display_name": display_name
                }
            )
    
    @staticmethod
    def remove_user(session_id, user_id):
        """Remove user from session"""
        with engine.begin() as conn:
            conn.execute(
                text("""
                    DELETE FROM session_users 
                    WHERE session_id = :session_id AND user_id = :user_id
                """),
                {"session_id": session_id, "user_id": user_id}
            )
    
    @staticmethod
    def get_session_users(session_id):
        """Get all users in a session"""
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT user_id, display_name, joined_at, last_seen
                    FROM session_users 
                    WHERE session_id = :session_id
                    ORDER BY joined_at
                """),
                {"session_id": session_id}
            ).fetchall()
            
            return [{
                'user_id': row[0],
                'display_name': row[1],
                'joined_at': row[2].isoformat(),
                'last_seen': row[3].isoformat()
            } for row in results]
    
    @staticmethod
    def update_last_seen(session_id, user_id):
        """Update user's last seen timestamp"""
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE session_users 
                    SET last_seen = NOW()
                    WHERE session_id = :session_id AND user_id = :user_id
                """),
                {"session_id": session_id, "user_id": user_id}
            )

class ChatMessage:
    @staticmethod
    def create(session_id, user_id, message, message_type='user', is_ai_directed=False, reply_to_message_id=None):
        """Create a new chat message"""
        message_id = str(uuid.uuid4())
        
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO chat_messages (id, session_id, user_id, message, message_type, is_ai_directed, reply_to_message_id, created_at)
                    VALUES (:id, :session_id, :user_id, :message, :message_type, :is_ai_directed, :reply_to_message_id, NOW())
                """),
                {
                    "id": message_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    "message": message,
                    "message_type": message_type,
                    "is_ai_directed": is_ai_directed,
                    "reply_to_message_id": reply_to_message_id
                }
            )
            
            # Get the created message
            result = conn.execute(
                text("""
                    SELECT id, session_id, user_id, message, message_type, is_ai_directed, reply_to_message_id, created_at
                    FROM chat_messages 
                    WHERE id = :id
                """),
                {"id": message_id}
            ).fetchone()
            
            return {
                'id': str(result[0]),
                'session_id': str(result[1]),
                'user_id': result[2],
                'message': result[3],
                'message_type': result[4],
                'is_ai_directed': result[5],
                'reply_to_message_id': str(result[6]) if result[6] else None,
                'created_at': result[7].isoformat()
            }
    
    @staticmethod
    def get_session_messages(session_id, limit=50):
        """Get recent messages for a session with reply information"""
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT cm.id, cm.session_id, cm.user_id, cm.message, cm.message_type, cm.is_ai_directed, 
                           cm.reply_to_message_id, cm.created_at,
                           COALESCE(su.display_name, 'Unknown User') as display_name,
                           reply_msg.message as reply_to_message
                    FROM chat_messages cm
                    LEFT JOIN session_users su ON cm.session_id = su.session_id AND cm.user_id = su.user_id
                    LEFT JOIN chat_messages reply_msg ON cm.reply_to_message_id = reply_msg.id
                    WHERE cm.session_id = :session_id
                    ORDER BY cm.created_at DESC
                    LIMIT :limit
                """),
                {"session_id": session_id, "limit": limit}
            ).fetchall()
            
            messages = [{
                'id': str(row[0]),
                'session_id': str(row[1]),
                'user_id': row[2],
                'message': row[3],
                'message_type': row[4],
                'is_ai_directed': row[5] if row[5] is not None else False,
                'reply_to_message_id': str(row[6]) if row[6] else None,
                'created_at': row[7].isoformat(),
                'display_name': 'AI Assistant' if row[4] == 'ai' else row[8],
                'reply_to_message': row[9] if row[9] else None
            } for row in results]
            
            # Return in chronological order
            return list(reversed(messages))

class VideoProcessingStatus:
    @staticmethod
    def create(video_url, session_id, status='pending'):
        """Create a new video processing status entry"""
        status_id = str(uuid.uuid4())
        
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO video_processing_status (id, video_url, session_id, status, started_at)
                    VALUES (:id, :video_url, :session_id, :status, NOW())
                    ON CONFLICT (video_url) 
                    DO UPDATE SET 
                        status = EXCLUDED.status,
                        session_id = EXCLUDED.session_id,
                        started_at = CURRENT_TIMESTAMP
                """),
                {
                    "id": status_id,
                    "video_url": video_url,
                    "session_id": session_id,
                    "status": status
                }
            )
            return status_id
    
    @staticmethod
    def update_status(video_url, status, progress=None, error_message=None):
        """Update video processing status"""
        with engine.begin() as conn:
            if status == 'completed':
                conn.execute(
                    text("""
                        UPDATE video_processing_status 
                        SET status = :status, progress = :progress, completed_at = NOW()
                        WHERE video_url = :video_url
                    """),
                    {"status": status, "progress": progress, "video_url": video_url}
                )
            elif status == 'failed':
                conn.execute(
                    text("""
                        UPDATE video_processing_status 
                        SET status = :status, error_message = :error_message, completed_at = NOW()
                        WHERE video_url = :video_url
                    """),
                    {"status": status, "error_message": error_message, "video_url": video_url}
                )
            else:
                conn.execute(
                    text("""
                        UPDATE video_processing_status 
                        SET status = :status, progress = :progress
                        WHERE video_url = :video_url
                    """),
                    {"status": status, "progress": progress, "video_url": video_url}
                )
    
    @staticmethod
    def get_by_video_url(video_url):
        """Get processing status for a video URL"""
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, video_url, session_id, status, progress, error_message, started_at, completed_at
                    FROM video_processing_status 
                    WHERE video_url = :video_url
                """),
                {"video_url": video_url}
            ).fetchone()
            
            if result:
                return {
                    'id': str(result[0]),
                    'video_url': result[1],
                    'session_id': str(result[2]),
                    'status': result[3],
                    'progress': result[4],
                    'error_message': result[5],
                    'started_at': result[6].isoformat() if result[6] else None,
                    'completed_at': result[7].isoformat() if result[7] else None
                }
            return None

class VideoAnalysis:
    @staticmethod
    def get_by_video_url(video_url):
        """Get all video analysis data for a given video URL"""
        if not video_url:
            return []
            
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT id, video_id, model_type, model_output, timestamp
                    FROM video_analysis 
                    WHERE video_id = :video_url
                    ORDER BY timestamp DESC
                """),
                {"video_url": video_url}
            ).fetchall()
            
            return [{
                'id': row[0],
                'video_id': row[1],
                'model_type': row[2],
                'model_output': row[3],
                'timestamp': row[4].isoformat()
            } for row in results]
    
    @staticmethod
    def create(video_id, model_type, model_output):
        """Create a new video analysis entry and also populate normalized table"""
        with engine.begin() as conn:
            # Insert into legacy table
            conn.execute(
                text("""
                    INSERT INTO video_analysis (video_id, model_type, model_output)
                    VALUES (:video_id, :model_type, :model_output)
                    ON CONFLICT (video_id, model_type) 
                    DO UPDATE SET 
                        model_output = EXCLUDED.model_output,
                        timestamp = CURRENT_TIMESTAMP
                """),
                {
                    "video_id": video_id,
                    "model_type": model_type,
                    "model_output": model_output
                }
            )
            
            # Also populate the new normalized table if applicable
            if model_type in ['transcript', 'image_descriptions']:
                content_type = 'transcript' if model_type == 'transcript' else 'description'
                VideoTranscript.create_from_json_array(video_id, content_type, model_output)

class VideoTranscript:
    @staticmethod
    def create_from_json_array(video_id, content_type, json_data):
        """Create multiple transcript entries from JSON array (migration helper)"""
        import json
        
        # Parse JSON if it's a string
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        
        with engine.begin() as conn:
            # First, delete existing entries for this video and content type
            conn.execute(
                text("""
                    DELETE FROM video_transcript 
                    WHERE video_id = :video_id AND content_type = :content_type
                """),
                {"video_id": video_id, "content_type": content_type}
            )
            
            # Insert individual timestamp records
            for item in json_data:
                timestamp_text = item.get('timestamp', '00:00')
                timestamp_seconds = item.get('seconds', 0)
                text_content = item.get('text') or item.get('description', '')
                
                conn.execute(
                    text("""
                        INSERT INTO video_transcript (video_id, timestamp_text, timestamp_seconds, text_content, content_type)
                        VALUES (:video_id, :timestamp_text, :timestamp_seconds, :text_content, :content_type)
                        ON CONFLICT (video_id, content_type, timestamp_seconds) 
                        DO UPDATE SET 
                            timestamp_text = EXCLUDED.timestamp_text,
                            text_content = EXCLUDED.text_content
                    """),
                    {
                        "video_id": video_id,
                        "timestamp_text": timestamp_text,
                        "timestamp_seconds": timestamp_seconds,
                        "text_content": text_content,
                        "content_type": content_type
                    }
                )
    
    @staticmethod
    def get_by_video_url(video_url, content_type=None, mode='omniscient', start_seconds=0, end_seconds=None):
        """
        Get video transcript data with different modes
        
        Args:
            video_url: Video URL identifier
            content_type: Filter by content type ('transcript', 'description', etc.)
            mode: 'omniscient' (all data), 'temporal' (up to end_seconds), 'window' (start to end)
            start_seconds: Start timestamp for temporal/window modes
            end_seconds: End timestamp for temporal/window modes
        """
        if not video_url:
            return []
        
        # Build the query based on mode
        query = """
            SELECT id, video_id, timestamp_text, timestamp_seconds, text_content, content_type, created_at
            FROM video_transcript 
            WHERE video_id = :video_url
        """
        params = {"video_url": video_url}
        
        # Add content type filter if specified
        if content_type:
            query += " AND content_type = :content_type"
            params["content_type"] = content_type
        
        # Add temporal filtering based on mode
        if mode == 'temporal' and end_seconds is not None:
            query += " AND timestamp_seconds <= :end_seconds"
            params["end_seconds"] = end_seconds
        elif mode == 'window' and start_seconds is not None and end_seconds is not None:
            query += " AND timestamp_seconds >= :start_seconds AND timestamp_seconds <= :end_seconds"
            params["start_seconds"] = start_seconds
            params["end_seconds"] = end_seconds
        
        query += " ORDER BY timestamp_seconds ASC"
        
        with engine.connect() as conn:
            results = conn.execute(text(query), params).fetchall()
            
            return [{
                'id': row[0],
                'video_id': row[1],
                'timestamp_text': row[2],
                'timestamp_seconds': row[3],
                'text_content': row[4],
                'content_type': row[5],
                'created_at': row[6].isoformat()
            } for row in results]
    
    @staticmethod
    def get_legacy_format(video_url, content_type=None, mode='omniscient', start_seconds=0, end_seconds=None):
        """
        Get transcript data in the legacy JSON array format for backward compatibility
        """
        transcripts = VideoTranscript.get_by_video_url(video_url, content_type, mode, start_seconds, end_seconds)
        
        # Convert to legacy format grouped by content type
        result = {}
        for transcript in transcripts:
            ct = transcript['content_type']
            if ct not in result:
                result[ct] = []
            
            # Format for legacy compatibility
            if ct == 'transcript':
                result[ct].append({
                    'timestamp': transcript['timestamp_text'],
                    'seconds': transcript['timestamp_seconds'],
                    'text': transcript['text_content']
                })
            elif ct == 'description':
                result[ct].append({
                    'timestamp': transcript['timestamp_text'],
                    'seconds': transcript['timestamp_seconds'],
                    'description': transcript['text_content']
                })
        
        return result
    
    @staticmethod
    def migrate_from_video_analysis():
        """Migration function to convert existing video_analysis data to new format"""
        with engine.connect() as conn:
            # Get all existing video analysis data
            results = conn.execute(
                text("""
                    SELECT video_id, model_type, model_output 
                    FROM video_analysis 
                    WHERE model_type IN ('transcript', 'image_descriptions')
                """)
            ).fetchall()
            
            for row in results:
                video_id, model_type, model_output = row
                
                # Map model types to content types
                content_type = 'transcript' if model_type == 'transcript' else 'description'
                
                # Create individual records
                VideoTranscript.create_from_json_array(video_id, content_type, model_output)

class TVShowInfo:
    @staticmethod
    def create(video_url, show_type, title, season=None, episode=None, tmdb_id=None, tmdb_data=None):
        """Create or update TV show information entry"""
        tv_show_id = str(uuid.uuid4())
        
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO tv_show_info (id, video_url, show_type, title, season, episode, tmdb_id, tmdb_data, created_at)
                    VALUES (:id, :video_url, :show_type, :title, :season, :episode, :tmdb_id, :tmdb_data, NOW())
                    ON CONFLICT (video_url) 
                    DO UPDATE SET 
                        show_type = EXCLUDED.show_type,
                        title = EXCLUDED.title,
                        season = EXCLUDED.season,
                        episode = EXCLUDED.episode,
                        tmdb_id = EXCLUDED.tmdb_id,
                        tmdb_data = EXCLUDED.tmdb_data,
                        updated_at = CURRENT_TIMESTAMP
                """),
                {
                    "id": tv_show_id,
                    "video_url": video_url,
                    "show_type": show_type,
                    "title": title,
                    "season": season,
                    "episode": episode,
                    "tmdb_id": tmdb_id,
                    "tmdb_data": tmdb_data
                }
            )
            return tv_show_id
    
    @staticmethod
    def get_by_video_url(video_url):
        """Get TV show information for a video URL"""
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, video_url, show_type, title, season, episode, tmdb_id, tmdb_data, created_at, updated_at
                    FROM tv_show_info 
                    WHERE video_url = :video_url
                """),
                {"video_url": video_url}
            ).fetchone()
            
            if result:
                return {
                    'id': str(result[0]),
                    'video_url': result[1],
                    'show_type': result[2],
                    'title': result[3],
                    'season': result[4],
                    'episode': result[5],
                    'tmdb_id': result[6],
                    'tmdb_data': result[7],
                    'created_at': result[8].isoformat() if result[8] else None,
                    'updated_at': result[9].isoformat() if result[9] else None
                }
            return None
    
    @staticmethod
    def get_all():
        """Get all TV show information entries"""
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT id, video_url, show_type, title, season, episode, tmdb_id, tmdb_data, created_at, updated_at
                    FROM tv_show_info 
                    ORDER BY created_at DESC
                """)
            ).fetchall()
            
            return [{
                'id': str(row[0]),
                'video_url': row[1],
                'show_type': row[2],
                'title': row[3],
                'season': row[4],
                'episode': row[5],
                'tmdb_id': row[6],
                'tmdb_data': row[7],
                'created_at': row[8].isoformat() if row[8] else None,
                'updated_at': row[9].isoformat() if row[9] else None
            } for row in results]