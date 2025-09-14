import requests
import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudflareTTSAPI:
    """Cloudflare Text-to-Speech API integration"""
    
    def __init__(self):
        # Get from environment variables
        self.api_token = os.getenv('CLOUDFLARE_API_TOKEN')
        self.account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID')
        
        if not self.api_token:
            raise ValueError("CLOUDFLARE_API_TOKEN environment variable is required")
        if not self.account_id:
            raise ValueError("CLOUDFLARE_ACCOUNT_ID environment variable is required")
        
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/@cf/deepgram/aura-1"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Initialized CloudflareTTSAPI with account ID: {self.account_id}")
    
    def text_to_speech(self, text: str, speaker: str = "luna", encoding: str = "linear16", container: str = "wav") -> Optional[bytes]:
        """
        Convert text to speech using Cloudflare's TTS API
        
        Args:
            text (str): The text to convert to speech
            speaker (str): Voice type - options include 'luna', 'stella', etc.
            encoding (str): Audio encoding format - 'linear16' for WAV
            container (str): Audio container format - 'wav' for WAV files
            
        Returns:
            bytes: Audio data in the specified format, or None if failed
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to TTS")
            return None
            
        try:
            payload = {
                "text": text.strip()[:1000],  # Limit to 1000 characters for safety
                "speaker": speaker,
                "encoding": encoding,
                "container": container
            }
            
            logger.info(f"Making TTS request for text: '{text[:50]}...' with speaker: {speaker}")
            
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                audio_size = len(response.content)
                logger.info(f"TTS request successful, generated {audio_size} bytes of audio")
                return response.content
            else:
                logger.error(f"TTS API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error calling TTS API: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling TTS API: {str(e)}")
            return None
    
    def get_available_speakers(self) -> list:
        """Get list of available speakers/voices"""
        # Available speakers from Cloudflare's Aura model
        return [
            "asteria",   # Female voice
            "arcas",     # Male voice
            "orion",     # Male voice
            "orpheus",   # Male voice
            "athena",    # Female voice
            "luna",      # Female voice (default)
            "zeus",      # Male voice
            "perseus",   # Male voice
            "helios",    # Male voice
            "hera",      # Female voice
            "stella"     # Female voice
        ]