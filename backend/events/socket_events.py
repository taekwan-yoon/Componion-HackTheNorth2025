from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
from core import Session, SessionUser, ChatMessage
from utils.name_generator import generate_random_name, generate_user_id
from datetime import datetime
import time

# Dictionary to store user sessions and master information
user_sessions = {}  # user_id -> {'session_id': str, 'display_name': str, 'is_master': bool}
session_masters = {}  # session_id -> user_id

def init_socket_events(socketio):
    """Initialize socket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        print(f'User connected: {request.sid}')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        user_id = request.sid
        if user_id in user_sessions:
            session_info = user_sessions[user_id]
            session_id = session_info['session_id']
            display_name = session_info['display_name']
            is_master = session_info.get('is_master', False)
            
            try:
                # Remove user from session
                SessionUser.remove_user(session_id, user_id)
                
                # If this was the master, remove from session_masters
                if is_master and session_id in session_masters:
                    del session_masters[session_id]
                    emit('master_disconnected', {
                        'session_id': session_id,
                        'timestamp': datetime.now().isoformat()
                    }, room=session_id)
                
                # Notify other users
                emit('user_left', {
                    'user_id': user_id,
                    'display_name': display_name,
                    'is_master': is_master,
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
                
                # Update user list
                users = SessionUser.get_session_users(session_id)
                emit('session_users', users, room=session_id)
                
                # Clean up
                del user_sessions[user_id]
                
                # Deactivate empty sessions
                Session.deactivate_empty_sessions()
                
            except Exception as e:
                print(f"Error in disconnect handler: {str(e)}")
        
        print(f'User disconnected: {user_id}')
    
    @socketio.on('join_session')
    def handle_join_session(data):
        session_id = data.get('session_id')
        user_id = request.sid
        is_master = data.get('is_master', False)
        display_name = data.get('display_name')
        
        # Ensure display_name is not None or empty
        if not display_name:
            display_name = generate_random_name()
        
        if not session_id:
            emit('error', {'message': 'Session ID is required'})
            return
        
        try:
            # Verify session exists
            session = Session.get_by_id(session_id)
            if not session:
                emit('error', {'message': 'Session not found'})
                return
            
            # Check if this should be a master session
            if is_master and session['is_master']:
                session_masters[session_id] = user_id
            
            # Add user to session
            SessionUser.add_user(session_id, user_id, display_name)
            user_sessions[user_id] = {
                'session_id': session_id,
                'display_name': display_name,
                'is_master': is_master
            }
            
            # Join socket room
            join_room(session_id)
            
            # Notify other users
            emit('user_joined', {
                'user_id': user_id,
                'display_name': display_name,
                'is_master': is_master,
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
            # Send current user list to all users in session
            users = SessionUser.get_session_users(session_id)
            emit('session_users', users, room=session_id)
            
            # Send recent messages to the joining user
            messages = ChatMessage.get_session_messages(session_id)
            emit('chat_history', messages)
            
            # Confirm join
            emit('join_confirmed', {
                'session_id': session_id,
                'user_id': user_id,
                'display_name': display_name,
                'is_master': is_master,
                'session': session
            })
            
        except Exception as e:
            print(f"Error in join_session: {str(e)}")
            emit('error', {'message': 'Failed to join session'})
    
    @socketio.on('send_message')
    def handle_send_message(data):
        user_id = request.sid
        message_text = data.get('message', '').strip()
        video_timestamp = data.get('video_timestamp', 0)
        query_mode = data.get('query_mode', 'omniscient')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if not message_text:
            emit('error', {'message': 'Message cannot be empty'})
            return
        
        if user_id not in user_sessions:
            emit('error', {'message': 'User not in any session'})
            return
        
        try:
            session_info = user_sessions[user_id]
            session_id = session_info['session_id']
            display_name = session_info['display_name']
            
            # Check if message is AI-directed
            message_lower = message_text.lower()
            is_ai_directed = (
                message_lower.startswith('@componion') or
                'hey componion' in message_lower or
                'componion' in message_lower or
                'companion' in message_lower
            )
            
            # Create message in database with AI-directed flag
            message = ChatMessage.create(
                session_id=session_id,
                user_id=user_id,
                message=message_text,
                message_type='user',
                is_ai_directed=is_ai_directed
            )
            
            # Add display name to message
            message['display_name'] = display_name
            
            # Update user's last seen
            SessionUser.update_last_seen(session_id, user_id)
            
            # Broadcast message to all users in session
            emit('new_message', message, room=session_id)
            
            # If message is AI-directed, trigger AI processing
            if is_ai_directed:
                try:
                    # Extract the actual question from AI-directed message
                    question = message_text
                    if message_lower.startswith('@componion'):
                        question = message_text.replace('@componion', '', 1).strip()
                    elif 'hey componion' in message_lower:
                        question = message_text.replace('hey componion', '', 1).strip(' ,')
                    elif 'componion' in message_lower:
                        question = message_text.replace('componion', '', 1).strip(' ,')
                    elif 'companion' in message_lower:
                        question = message_text.replace('companion', '', 1).strip(' ,')
                    
                    # If no meaningful question after extraction, use the whole message
                    if not question or len(question.strip()) < 3:
                        question = message_text
                    
                    # Get session for context
                    session = Session.get_by_id(session_id)
                    if session and session.get('video_url'):
                        try:
                            # Import AI services
                            from services import PromptConstructor
                            from api import GeminiAPI
                            
                            # Use the video timestamp from the frontend
                            # video_timestamp is already defined from data.get('video_timestamp', 0)
                            
                            # Initialize AI services
                            prompt_constructor = PromptConstructor(session['video_url'], session_id)
                            gemini_api = GeminiAPI()
                            
                            # Construct the prompt with video context
                            full_prompt = prompt_constructor.construct_prompt(
                                user_message=question, 
                                video_timestamp=video_timestamp,
                                query_mode=query_mode,
                                start_time=start_time,
                                end_time=end_time
                            )
                            
                            # Generate AI response using Gemini API
                            ai_response = gemini_api.llm_inference(full_prompt)
                            
                            print(f"AI processed question via socket: '{question}' -> '{ai_response[:100]}...'")
                            
                        except Exception as ai_error:
                            print(f"Error in AI processing: {ai_error}")
                            ai_response = f"I understand you're asking about: '{question}'. I'm having trouble accessing the video context right now, but I'm here to help!"
                    else:
                        # Simple response when no video context is available
                        ai_response = f"I received your question: '{question}'. I need video context to provide detailed answers, but I'm ready to help when video is available!"
                    
                    # Create AI response message
                    ai_message = ChatMessage.create(
                        session_id=session_id,
                        user_id='ai_assistant',
                        message=ai_response,
                        message_type='ai',
                        reply_to_message_id=message['id']
                    )
                    ai_message['display_name'] = 'AI Assistant'
                    ai_message['reply_to_message'] = question[:50] + ('...' if len(question) > 50 else '')
                    
                    # Broadcast AI response
                    emit('new_message', ai_message, room=session_id)
                        
                except Exception as ai_error:
                    print(f"Error in AI processing: {ai_error}")
                    # Don't emit error to user, just log it
            
        except Exception as e:
            print(f"Error in send_message: {str(e)}")
            emit('error', {'message': 'Failed to send message'})
    
    @socketio.on('ask_question')
    def handle_ask_question(data):
        user_id = request.sid
        question = data.get('question', '').strip()
        video_timestamp = data.get('video_timestamp', 0)
        
        if not question:
            emit('error', {'message': 'Question cannot be empty'})
            return
        
        if user_id not in user_sessions:
            emit('error', {'message': 'User not in any session'})
            return
        
        try:
            session_info = user_sessions[user_id]
            session_id = session_info['session_id']
            display_name = session_info['display_name']
            
            # Create user question message
            user_message = ChatMessage.create(
                session_id=session_id,
                user_id=user_id,
                message=question,
                message_type='user',
                is_ai_directed=True
            )
            user_message['display_name'] = display_name
            
            # Broadcast user question
            emit('new_message', user_message, room=session_id)
            
            # Get session for context
            session = Session.get_by_id(session_id)
            recent_messages = ChatMessage.get_session_messages(session_id, limit=10)
            
            # Enhanced context with video timing
            context_lines = []
            if video_timestamp:
                context_lines.append(f"Current video time: {video_timestamp} seconds")
            if session and session.get('video_url'):
                context_lines.append(f"Video URL: {session['video_url']}")
            
            context_lines.extend([f"{msg['display_name']}: {msg['message']}" for msg in recent_messages[-5:]])
            context = "\n".join(context_lines)
            
            # Prepare prompt for AI (using mock response for now)
            mock_responses = [
                f"Based on the video content at {video_timestamp} seconds, this is an interesting question about the topic being discussed.",
                f"At timestamp {video_timestamp}s, the video shows relevant information that helps answer your question.",
                f"Great observation! At this point in the video ({video_timestamp}s), we can see how this concept applies.",
                f"Your question relates well to what's happening at {video_timestamp} seconds in the video.",
                f"According to the video context around {video_timestamp}s, here's what I can tell you about this topic."
            ]
            import random
            ai_response = random.choice(mock_responses)
            
            # Create AI response message
            ai_message = ChatMessage.create(
                session_id=session_id,
                user_id='ai_assistant',
                message=ai_response,
                message_type='ai',
                reply_to_message_id=user_message['id']
            )
            ai_message['display_name'] = 'AI Assistant'
            
            # Broadcast AI response
            emit('ai_response', ai_message, room=session_id)
            emit('new_message', ai_message, room=session_id)
            
        except Exception as e:
            print(f"Error in ask_question: {str(e)}")
            emit('error', {'message': 'Failed to process question'})
    
    @socketio.on('video_time_update')
    def handle_video_time_update(data):
        """Master session broadcasts current video time"""
        user_id = request.sid
        session_id = data.get('session_id')
        video_time = data.get('video_time', 0)
        
        if user_id not in user_sessions:
            emit('error', {'message': 'User not in any session'})
            return
        
        session_info = user_sessions[user_id]
        if not session_info.get('is_master', False):
            emit('error', {'message': 'Only master can send time updates'})
            return
        
        try:
            # Broadcast video time to all participants (not master)
            emit('sync_video_time', {
                'video_time': video_time,
                'timestamp': time.time()
            }, room=session_id, include_self=False)
            
        except Exception as e:
            print(f"Error in video_time_update: {str(e)}")
            emit('error', {'message': 'Failed to sync video time'})
    
    @socketio.on('request_current_time')
    def handle_request_current_time(data):
        """Participant requests current video time from master"""
        user_id = request.sid
        session_id = data.get('session_id')
        
        if user_id not in user_sessions:
            emit('error', {'message': 'User not in any session'})
            return
        
        try:
            # Send request to master if one exists
            if session_id in session_masters:
                master_id = session_masters[session_id]
                emit('time_requested', {
                    'requester_id': user_id,
                    'session_id': session_id
                }, room=master_id)
            else:
                emit('error', {'message': 'No master found for this session'})
                
        except Exception as e:
            print(f"Error in request_current_time: {str(e)}")
            emit('error', {'message': 'Failed to request time'})
    
    @socketio.on('send_current_time')
    def handle_send_current_time(data):
        """Master responds with current video time to a specific user"""
        user_id = request.sid
        requester_id = data.get('requester_id')
        video_time = data.get('video_time', 0)
        
        if user_id not in user_sessions:
            emit('error', {'message': 'User not in any session'})
            return
        
        session_info = user_sessions[user_id]
        if not session_info.get('is_master', False):
            emit('error', {'message': 'Only master can send time updates'})
            return
        
        try:
            # Send current time to the requesting user
            emit('sync_video_time', {
                'video_time': video_time,
                'timestamp': time.time()
            }, room=requester_id)
            
        except Exception as e:
            print(f"Error in send_current_time: {str(e)}")
            emit('error', {'message': 'Failed to send current time'})


