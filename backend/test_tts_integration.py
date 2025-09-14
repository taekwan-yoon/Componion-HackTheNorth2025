#!/usr/bin/env python3
"""
Test script for the TTS integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.tts_api import CloudflareTTSAPI

def test_tts():
    """Test the TTS API functionality"""
    print("Testing Cloudflare TTS API...")
    
    tts_api = CloudflareTTSAPI()
    
    # Test text
    test_text = "Hello! This is a test of the Cloudflare text-to-speech integration."
    
    print(f"Converting text: '{test_text}'")
    
    # Generate audio
    audio_data = tts_api.text_to_speech(test_text)
    
    if audio_data:
        print(f"✅ Success! Generated {len(audio_data)} bytes of audio data")
        
        # Save test file
        with open("test_tts_output.wav", "wb") as f:
            f.write(audio_data)
        print("📁 Saved test audio to 'test_tts_output.wav'")
        
        return True
    else:
        print("❌ Failed to generate audio")
        return False

def test_speakers():
    """Test getting available speakers"""
    print("\nTesting available speakers...")
    
    tts_api = CloudflareTTSAPI()
    speakers = tts_api.get_available_speakers()
    
    print(f"Available speakers: {speakers}")
    return speakers

if __name__ == "__main__":
    print("🎵 TTS Integration Test")
    print("=" * 40)
    
    # Test TTS generation
    tts_success = test_tts()
    
    # Test speakers
    speakers = test_speakers()
    
    print("\n" + "=" * 40)
    if tts_success:
        print("✅ TTS integration test PASSED")
    else:
        print("❌ TTS integration test FAILED")