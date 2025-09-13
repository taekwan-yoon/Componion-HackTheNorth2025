from core import ChatMessage, VideoAnalysis, TVShowInfo
import json


class PromptConstructor:
  def __init__(self, video_url: str, session_id: str):
    self.video_url = video_url
    self.session_id = session_id
  
  def _transcript_to_text(self, transcript_data) -> str:
    """Parse transcript data and convert to readable text format"""
    try:
      # Handle both JSON string and already parsed data
      if isinstance(transcript_data, str):
        transcript_data = json.loads(transcript_data)
      
      formatted_lines = []
      for item in transcript_data:
        timestamp = item.get('timestamp', '00:00')
        text = item.get('text', '')
        formatted_lines.append(f"[{timestamp}] {text}")
      return "\n".join(formatted_lines)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
      return f"Error parsing transcript: {e}"
  
  def _image_descriptions_to_text(self, image_descriptions_data) -> str:
    """Parse image descriptions data and convert to readable text format"""
    try:
      # Handle both JSON string and already parsed data
      if isinstance(image_descriptions_data, str):
        image_descriptions_data = json.loads(image_descriptions_data)
      
      formatted_lines = []
      for item in image_descriptions_data:
        timestamp = item.get('timestamp', '00:00')
        description = item.get('description', '')
        formatted_lines.append(f"[{timestamp}] Screenshot: {description}")
      return "\n".join(formatted_lines)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
      return f"Error parsing image descriptions: {e}"

  def _show_identification_to_text(self, show_identification_data) -> str:
    """Parse show identification data and convert to readable text format"""
    try:
      # Handle both JSON string and already parsed data
      if isinstance(show_identification_data, str):
        show_identification_data = json.loads(show_identification_data)
      
      # Extract the response from the batched format
      if isinstance(show_identification_data, dict) and "response" in show_identification_data:
        response = show_identification_data.get("response", "")
        return f"Content Identification: {response}"
      else:
        # Fallback for any other format
        return f"Content Identification: {str(show_identification_data)}"
    except (json.JSONDecodeError, TypeError) as e:
      return f"Error parsing show identification: {e}"

  def _tv_show_info_to_text(self, tv_show_info) -> str:
    """Convert TV show information to readable text format"""
    try:
      if not tv_show_info:
        return ""
      
      parts = []
      
      # Basic information
      show_type = tv_show_info.get('show_type', 'Unknown')
      title = tv_show_info.get('title')
      season = tv_show_info.get('season')
      episode = tv_show_info.get('episode')
      
      if title:
        parts.append(f"Content Type: {show_type}")
        parts.append(f"Title: {title}")
        
        if season and episode:
          parts.append(f"Season {season}, Episode {episode}")
        elif season:
          parts.append(f"Season {season}")
      
      # TMDB data if available
      tmdb_data = tv_show_info.get('tmdb_data')
      if tmdb_data:
        try:
          tmdb_info = json.loads(tmdb_data) if isinstance(tmdb_data, str) else tmdb_data
          
          # Handle combined show and episode data
          if "show_info" in tmdb_info and "episode_info" in tmdb_info:
            show_info = tmdb_info["show_info"]
            episode_info = tmdb_info["episode_info"]
            
            # Show information
            if show_info.get('overview'):
              parts.append(f"Show Overview: {show_info['overview']}")
            if show_info.get('genres'):
              genres = [g['name'] for g in show_info['genres']]
              parts.append(f"Genres: {', '.join(genres)}")
            if show_info.get('first_air_date'):
              parts.append(f"First Aired: {show_info['first_air_date']}")
            
            # Episode information
            if episode_info.get('name'):
              parts.append(f"Episode Title: {episode_info['name']}")
            if episode_info.get('overview'):
              parts.append(f"Episode Overview: {episode_info['overview']}")
            if episode_info.get('air_date'):
              parts.append(f"Episode Air Date: {episode_info['air_date']}")
              
          else:
            # Single content (show or movie)
            if tmdb_info.get('overview'):
              parts.append(f"Overview: {tmdb_info['overview']}")
            if tmdb_info.get('genres'):
              genres = [g['name'] for g in tmdb_info['genres']]
              parts.append(f"Genres: {', '.join(genres)}")
            if tmdb_info.get('first_air_date'):
              parts.append(f"First Aired: {tmdb_info['first_air_date']}")
            elif tmdb_info.get('release_date'):
              parts.append(f"Release Date: {tmdb_info['release_date']}")
              
        except (json.JSONDecodeError, TypeError, KeyError) as e:
          parts.append(f"Additional information available (parsing error: {e})")
      
      return "\n".join(parts) if parts else ""
      
    except Exception as e:
      return f"Error parsing TV show information: {e}"

  def _session_messages_to_text(self, messages: list) -> str:
    formatted_messages = []
    for msg in messages:
      role = "User" if msg['message_type'] == 'user' else "AI"
      formatted_messages.append(f"{role}: {msg['message']}")
    return "\n".join(formatted_messages)

  def _model_output_to_text(self, model_output, model_type: str) -> str:
    """Convert model output to text based on model type"""
    if model_type == "transcript":
      return self._transcript_to_text(model_output)
    elif model_type == "image_descriptions":
      return self._image_descriptions_to_text(model_output)
    elif model_type == "show_identification":
      return self._show_identification_to_text(model_output)
    return ""
    return ""

  def construct_prompt(self, user_message: str, video_timestamp: int = 0) -> str:
    """
    Construct the prompt for the AI model including video context and chat history.
    
    Args:
      user_message: The user's question
      video_timestamp: Current video position in seconds
      
    Returns:
      str: The constructed prompt for the AI model
      
    Raises:
      ValueError: If required video analysis data is missing
    """
    # Get session messages
    session_messages = ChatMessage.get_session_messages(self.session_id, limit=20)

    # Get video analysis data
    video_analysis = VideoAnalysis.get_by_video_url(self.video_url)

    # Get TV show information if available
    tv_show_info = TVShowInfo.get_by_video_url(self.video_url)

    # Verify that all expected video analysis data is present
    required_model_types = ["transcript", "image_descriptions"]
    found_model_types = [va['model_type'] for va in video_analysis]

    for required_model_type in required_model_types:
      if required_model_type not in found_model_types:
        raise ValueError(f"Missing expected video analysis data: {required_model_type}. Found: {found_model_types}")

    # Process video analysis data
    context_parts = []

    # Add TV show information first if available
    if tv_show_info:
      tv_show_context = self._tv_show_info_to_text(tv_show_info)
      if tv_show_context:
        context_parts.append(f"\n--- Content Information ---\n{tv_show_context}")
    
    # Add video timestamp context
    if video_timestamp > 0:
      # Ensure video_timestamp is treated as an integer for divmod
      timestamp_seconds = int(video_timestamp)
      minutes, seconds = divmod(timestamp_seconds, 60)
      timestamp_str = f"{minutes:02d}:{seconds:02d}"
      context_parts.append(f"Current video timestamp: {timestamp_str} ({video_timestamp} seconds)")
    
    # Add video analysis context
    for analysis in video_analysis:
      model_output = analysis['model_output']
      model_type = analysis['model_type']
      context_part = self._model_output_to_text(model_output, model_type)
      if context_part:
        context_parts.append(f"\n--- {model_type.replace('_', ' ').title()} ---\n{context_part}")

    # Add session messages context
    if session_messages:
      formatted_messages = self._session_messages_to_text(session_messages)
      if formatted_messages:
        context_parts.append(f"\n--- Previous Chat Messages ---\n{formatted_messages}")

    context = "\n".join(context_parts)

    prompt = f"""You are an AI assistant for a video viewing application. Use the following context from the video and prior chat messages to answer the user's question.

Context:
{context}

User Question: {user_message}

Please provide a helpful and accurate response based on the video content and context provided."""

    return prompt