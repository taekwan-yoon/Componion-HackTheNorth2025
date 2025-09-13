from core import ChatMessage, VideoAnalysis
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

    # Verify that all expected video analysis data is present
    required_model_types = ["transcript", "image_descriptions"]
    found_model_types = [va['model_type'] for va in video_analysis]

    for required_model_type in required_model_types:
      if required_model_type not in found_model_types:
        raise ValueError(f"Missing expected video analysis data: {required_model_type}. Found: {found_model_types}")

    # Process video analysis data
    context_parts = []
    
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