from flask import Blueprint, request, jsonify, send_from_directory
from core import Session, SessionUser, ChatMessage, VideoAnalysis, VideoProcessingStatus
from utils.name_generator import generate_random_name, generate_user_id
from datetime import datetime
import os

api = Blueprint('api', __name__)

@api.route('/sessions', methods=['GET'])
def get_sessions():
    """Get all active sessions"""
    try:
        sessions = Session.get_all_active()
        return jsonify(sessions)
    except Exception as e:
        print(f"Error getting sessions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/sessions', methods=['POST'])
def create_session():
    """Create a new session with video URL and master controls"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Session name is required'}), 400
        
        video_url = data.get('video_url')
        video_file = data.get('video_file', 'sample_video.mp4')
        is_master = data.get('is_master', True)  # Default to master session
        
        session = Session.create(
            name=data['name'],
            video_url=video_url,
            video_file=video_file,
            is_master=is_master
        )
        
        return jsonify({
            'session': session,
            'join_code': session['id'],
            'join_url': f"/join/{session['id']}",
            'master_controls': is_master
        }), 201
    except Exception as e:
        print(f"Error creating session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session details"""
    try:
        session = Session.get_by_id(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get users and recent messages
        users = SessionUser.get_session_users(session_id)
        messages = ChatMessage.get_session_messages(session_id)
        
        session['users'] = users
        session['messages'] = messages
        
        return jsonify(session)
    except Exception as e:
        print(f"Error getting session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/sessions/<session_id>/join', methods=['POST'])
def join_session(session_id):
    """Join an existing session as participant"""
    try:
        data = request.get_json()
        user_name = data.get('user_name', generate_random_name())
        
        session = Session.get_by_id(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Generate user ID
        user_id = generate_user_id()
        
        # Add user to session
        SessionUser.add_user(session_id, user_id, user_name)
        
        return jsonify({
            'session': session,
            'user': {
                'user_id': user_id,
                'display_name': user_name
            },
            'master_controls': False
        })
    except Exception as e:
        print(f"Error joining session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/ask', methods=['POST'])
def ask_ai():
    """Enhanced AI endpoint with video timestamp context"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data or 'session_id' not in data:
            return jsonify({'error': 'Message and session_id are required'}), 400
        
        # Get current video timestamp from request
        video_timestamp = data.get('video_timestamp', 0)
        
        # Verify session exists
        session = Session.get_by_id(data['session_id'])
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Check if session has a video URL
        video_url = session.get('video_url')
        if not video_url:
            return jsonify({'error': 'Session does not have a video URL'}), 400
        
        try:
            # Initialize PromptConstructor and GeminiAPI
            from services import PromptConstructor
            from api import GeminiAPI
            
            prompt_constructor = PromptConstructor(video_url, data['session_id'])
            gemini_api = GeminiAPI()
            
            # Construct the prompt with video context
            full_prompt = prompt_constructor.construct_prompt(
                user_message=data['message'], 
                video_timestamp=video_timestamp
            )
            
            # Generate AI response using Gemini API
            response = gemini_api.llm_inference(full_prompt)
            
            # Store the question and response in chat with proper flags
            user_id = data.get('user_id', 'anonymous')
            
            # Create user message marked as AI-directed
            user_message = ChatMessage.create(
                session_id=data['session_id'],
                user_id=user_id,
                message=data['message'],
                message_type='user',
                is_ai_directed=True
            )
            
            # Create AI response that replies to the user message
            ai_message = ChatMessage.create(
                session_id=data['session_id'],
                user_id='ai_assistant',
                message=response,
                message_type='ai',
                reply_to_message_id=user_message['id']
            )

            return jsonify({
                'message': data['message'],
                'session_id': data['session_id'],
                'answer': response,
                'video_timestamp': video_timestamp,
                'timestamp': datetime.now().isoformat()
            })
            
        except ValueError as e:
            # Handle missing video analysis data
            error_msg = f"Video analysis not ready: {str(e)}"
            return jsonify({
                'error': error_msg,
                'message': 'Please wait for video processing to complete and try again.'
            }), 503
            
        except Exception as e:
            # Handle other errors (API issues, etc.)
            print(f"Error in AI processing: {str(e)}")
            return jsonify({
                'error': f'AI processing failed: {str(e)}',
                'message': 'There was an issue processing your request. Please try again.'
            }), 500
        
    except Exception as e:
        print(f"Error in AI endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/video/<filename>')
def serve_video(filename):
    """Serve video files"""
    try:
        video_dir = os.path.join(os.path.dirname(__file__), 'static')
        return send_from_directory(video_dir, filename)
    except Exception as e:
        print(f"Error serving video: {str(e)}")
        return jsonify({'error': 'Video not found'}), 404

@api.route('/sessions/<session_id>/context', methods=['GET'])
def get_session_context(session_id):
    """Get video context and chat history for AI"""
    try:
        session = Session.get_by_id(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        messages = ChatMessage.get_session_messages(session_id)
        users = SessionUser.get_session_users(session_id)
        
        return jsonify({
            'session': session,
            'messages': messages,
            'users': users
        })
    except Exception as e:
        print(f"Error getting context: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/sessions/<session_id>/messages', methods=['POST'])
def add_message_to_session(session_id):
    """Add a message to the session for context"""
    try:
        data = request.get_json()
        
        if not data or 'content' not in data or 'message_type' not in data:
            return jsonify({'error': 'Content and message_type are required'}), 400
        
        user_id = data.get('user_id', 'anonymous')
        
        # Store message in session
        message = ChatMessage.create(
            session_id=session_id,
            user_id=user_id,
            message=data['content'],
            message_type=data['message_type']  # 'user' or 'ai'
        )
        
        return jsonify(message), 201
    except Exception as e:
        print(f"Error adding message: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/video-analysis/<path:video_url>', methods=['GET'])
def get_video_analysis(video_url):
    """Get video analysis data for a specific video URL"""
    try:
        analysis_data = VideoAnalysis.get_by_video_url(video_url)
        
        if analysis_data:
            return jsonify({
                'video_url': video_url,
                'analysis_count': len(analysis_data),
                'analysis_data': analysis_data
            })
        else:
            return jsonify({
                'video_url': video_url,
                'analysis_count': 0,
                'analysis_data': [],
                'message': 'No analysis data found for this video'
            })
    except Exception as e:
        print(f"Error getting video analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/video/process', methods=['POST'])
def process_video():
    """Start video processing for a URL"""
    try:
        data = request.get_json()
        
        if not data or 'video_url' not in data or 'session_id' not in data:
            return jsonify({'error': 'video_url and session_id are required'}), 400
        
        video_url = data['video_url']
        session_id = data['session_id']
        
        # Check if video is already processed
        analysis_data = VideoAnalysis.get_by_video_url(video_url)
        if analysis_data:
            return jsonify({
                'message': 'Video already processed',
                'status': 'completed'
            })
        
        # Check if processing is already in progress
        processing_status = VideoProcessingStatus.get_by_video_url(video_url)
        if processing_status and processing_status['status'] in ['pending', 'processing']:
            return jsonify({
                'message': 'Video processing already in progress',
                'status': processing_status['status'],
                'progress': processing_status.get('progress', 0)
            })
        
        # Start new processing
        VideoProcessingStatus.create(video_url, session_id, 'pending')
        
        # Process video in background thread
        import threading
        def process_video_background():
            try:
                VideoProcessingStatus.update_status(video_url, 'processing', 10)
                
                from services import VideoPreprocessor
                preprocessor = VideoPreprocessor()
                
                # Create progress callback
                def update_progress(progress, message=None):
                    VideoProcessingStatus.update_status(video_url, 'processing', progress)
                    if message:
                        print(f"Progress {progress}%: {message}")
                
                # Start processing with progress callback
                VideoProcessingStatus.update_status(video_url, 'processing', 20)
                update_progress(30, "Starting video extraction...")
                
                success, message = preprocessor.preprocess_youtube_url(video_url, progress_callback=update_progress)
                
                if success:
                    VideoProcessingStatus.update_status(video_url, 'completed', 100)
                    print(f"✅ Video preprocessing completed: {message}")
                else:
                    VideoProcessingStatus.update_status(video_url, 'failed', error_message=message)
                    print(f"⚠️ Video preprocessing failed: {message}")
                    
            except Exception as e:
                error_msg = f"Error during video preprocessing: {str(e)}"
                VideoProcessingStatus.update_status(video_url, 'failed', error_message=error_msg)
                print(f"❌ {error_msg}")
        
        thread = threading.Thread(target=process_video_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Video processing started',
            'status': 'pending'
        }), 202
        
    except Exception as e:
        print(f"Error starting video processing: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/video/status/<path:video_url>', methods=['GET'])
def get_video_processing_status(video_url):
    """Get video processing status"""
    try:
        # Check processing status first - this is the authoritative source
        processing_status = VideoProcessingStatus.get_by_video_url(video_url)
        if processing_status:
            # Only return the processing status - don't override with analysis data check
            return jsonify(processing_status)
        
        # If no processing status exists, check if video is already processed
        analysis_data = VideoAnalysis.get_by_video_url(video_url)
        if analysis_data:
            return jsonify({
                'status': 'completed',
                'progress': 100,
                'message': 'Video analysis available'
            })
        else:
            return jsonify({
                'status': 'not_started',
                'progress': 0,
                'message': 'Video processing not started'
            })
            
    except Exception as e:
        print(f"Error getting video processing status: {str(e)}")
        return jsonify({'error': str(e)}), 500
