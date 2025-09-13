import os
import json
import glob
from typing import Tuple, List, Dict, Any
from youtube.scripts.YoutubeExtractor import YoutubeExtractor
from api import GeminiAPI
from core import VideoAnalysis


class VideoPreprocessor:
    def __init__(self):
        """Initialize the VideoPreprocessor with necessary components."""
        self.gemini_api = None
        self.youtube_extractor = None
        
    def _initialize_gemini_api(self) -> bool:
        """Initialize Gemini API. Returns True if successful, False otherwise."""
        try:
            self.gemini_api = GeminiAPI()
            return True
        except Exception as e:
            print(f"Failed to initialize Gemini API: {e}")
            return False
    
    def _parse_transcript_to_json(self, transcript_path: str) -> List[Dict[str, Any]]:
        """
        Parse the transcript file into JSON format for easier querying.
        
        Args:
            transcript_path: Path to the transcript file
            
        Returns:
            List of dictionaries with timestamp and text
        """
        transcript_json = []
        
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line and line.startswith('[') and ']' in line:
                    # Parse format: [MM:SS] text
                    timestamp_end = line.find(']')
                    timestamp = line[1:timestamp_end]
                    text = line[timestamp_end + 1:].strip()
                    
                    # Convert timestamp to seconds for easier querying
                    time_parts = timestamp.split(':')
                    seconds = int(time_parts[0]) * 60 + int(time_parts[1])
                    
                    transcript_json.append({
                        "timestamp": timestamp,
                        "seconds": seconds,
                        "text": text
                    })
        except Exception as e:
            print(f"Error parsing transcript: {e}")
            
        return transcript_json
    
    def _process_screenshots(self, screenshot_dir: str, video_id: str, progress_callback=None) -> List[Dict[str, Any]]:
        """
        Process all screenshots using Gemini API image2text.
        
        Args:
            screenshot_dir: Directory containing screenshots
            video_id: Video ID for filtering files
            
        Returns:
            List of dictionaries with screenshot info and descriptions
        """
        image_descriptions = []
        
        # Find all screenshot files for this video
        screenshot_pattern = os.path.join(screenshot_dir, f"{video_id}_screenshot_*.jpg")
        screenshot_files = sorted(glob.glob(screenshot_pattern))
        
        if not screenshot_files:
            print(f"No screenshots found for video {video_id}")
            return image_descriptions
        
        print(f"Processing {len(screenshot_files)} screenshots...")
        
        for i, screenshot_path in enumerate(screenshot_files):
            try:
                # Extract timestamp from filename
                filename = os.path.basename(screenshot_path)
                # Format: {video_id}_screenshot_{seconds:04}.jpg
                timestamp_str = filename.split('_screenshot_')[1].split('.')[0]
                seconds = int(timestamp_str)
                
                # Convert seconds to MM:SS format
                minutes, secs = divmod(seconds, 60)
                timestamp = f"{minutes:02d}:{secs:02d}"
                
                # Update progress during screenshot processing
                if progress_callback and len(screenshot_files) > 0:
                    # Progress from 75% to 85% during screenshot processing
                    screenshot_progress = 75 + (10 * (i + 1) / len(screenshot_files))
                    progress_callback(int(screenshot_progress), f"Processing screenshot {i + 1}/{len(screenshot_files)}")
                
                # Process image with Gemini API
                prompt = "Describe this screenshot from a TV Show in detail. Focus on the main subjects and find out their names, actions, text visible, and overall scene composition. Consider the context of the show. Use the internet"
                description = self.gemini_api.image2text(screenshot_path, prompt)
                
                image_descriptions.append({
                    "timestamp": timestamp,
                    "seconds": seconds,
                    "filename": filename,
                    "description": description
                })
                
                print(f"Processed screenshot at {timestamp}")
                
            except Exception as e:
                print(f"Error processing screenshot {screenshot_path}: {e}")
                # Continue processing other screenshots
                continue
        
        return image_descriptions
    
    def _cleanup_generated_files(self, video_id: str) -> None:
        """
        Clean up generated files for a specific video ID after processing.
        Removes audio, screenshot, and transcript files to save disk space.
        
        Args:
            video_id: The video ID whose files should be cleaned up
        """
        try:
            base_path = os.path.join("youtube", "data")
            files_deleted = 0
            
            # Clean up audio files
            audio_pattern = os.path.join(base_path, "audio", f"{video_id}_audio.*")
            for audio_file in glob.glob(audio_pattern):
                os.remove(audio_file)
                files_deleted += 1
                print(f"🗑️ Deleted audio file: {os.path.basename(audio_file)}")
            
            # Clean up screenshot files
            screenshot_pattern = os.path.join(base_path, "screenshots", f"{video_id}_screenshot_*.jpg")
            for screenshot_file in glob.glob(screenshot_pattern):
                os.remove(screenshot_file)
                files_deleted += 1
                print(f"🗑️ Deleted screenshot: {os.path.basename(screenshot_file)}")
            
            # Clean up transcript files
            transcript_pattern = os.path.join(base_path, "transcripts", f"{video_id}_transcript.*")
            for transcript_file in glob.glob(transcript_pattern):
                os.remove(transcript_file)
                files_deleted += 1
                print(f"🗑️ Deleted transcript: {os.path.basename(transcript_file)}")
            
            if files_deleted > 0:
                print(f"✅ Cleanup completed: {files_deleted} files deleted for video {video_id}")
            else:
                print(f"ℹ️ No files found to clean up for video {video_id}")
                
        except Exception as e:
            print(f"⚠️ Error during cleanup for video {video_id}: {e}")
    
    def preprocess_youtube_url(self, youtube_url: str, progress_callback=None) -> Tuple[bool, str]:
        """
        Main function to preprocess a YouTube URL.
        Extracts data using YoutubeExtractor and processes it with Gemini API.
        
        Args:
            youtube_url: The YouTube URL to process
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Initialize Gemini API
        if not self._initialize_gemini_api():
            return False, "Failed to initialize Gemini API"
        
        try:
            # Initialize YouTube extractor
            if progress_callback:
                progress_callback(35, "Initializing YouTube extractor...")
            
            self.youtube_extractor = YoutubeExtractor(youtube_url)
            
            # Extract video ID
            video_id = self.youtube_extractor.extract_video_id_from_url()
            if not video_id:
                return False, "Failed to extract video ID from URL"
            
            if progress_callback:
                progress_callback(40, "Setting up extraction paths...")
            
            # Set up paths
            self.youtube_extractor.set_video_id(video_id)
            base_path = os.path.join("youtube", "data")
            self.youtube_extractor.set_audio_path(os.path.join(base_path, "audio"))
            self.youtube_extractor.set_screenshot_path(os.path.join(base_path, "screenshots"))
            self.youtube_extractor.set_transcript_path(os.path.join(base_path, "transcripts"))
            
            # Track what was successfully processed
            processed_components = []
            errors = []
            
            # 1. Extract and process transcript
            try:
                if progress_callback:
                    progress_callback(45, "Extracting transcript...")
                
                transcript_success = self.youtube_extractor.extract_and_save_transcript()
                if transcript_success:
                    # Parse transcript to JSON format
                    transcript_path = os.path.join(
                        self.youtube_extractor.get_transcript_path(), 
                        f"{video_id}_transcript.txt"
                    )
                    
                    if progress_callback:
                        progress_callback(55, "Processing transcript...")
                    
                    transcript_json = self._parse_transcript_to_json(transcript_path)
                    
                    # Save to database
                    VideoAnalysis.create(
                        video_id=youtube_url,  # Using URL as video_id as per existing code
                        model_type="transcript",
                        model_output=json.dumps(transcript_json)
                    )
                    processed_components.append("transcript")
                    print("✅ Transcript processed and saved")
                else:
                    # Try extracting audio as fallback
                    audio_success = self.youtube_extractor.extract_and_save_audio()
                    if audio_success:
                        audio_path = os.path.join(
                            self.youtube_extractor.get_audio_path(),
                            f"{video_id}_audio.mp3"
                        )
                        # Process audio with Gemini API
                        transcript_text = self.gemini_api.audio2text(
                            audio_path, 
                            "Transcribe this audio recording with timestamps if possible."
                        )
                        
                        # Save transcription result
                        transcript_data = [{
                            "timestamp": "00:00",
                            "seconds": 0,
                            "text": transcript_text
                        }]
                        
                        VideoAnalysis.create(
                            video_id=youtube_url,
                            model_type="transcript",
                            model_output=json.dumps(transcript_data)
                        )
                        processed_components.append("audio_transcription")
                        print("✅ Audio transcription processed and saved")
                    else:
                        errors.append("Failed to extract transcript or audio")
                        
            except Exception as e:
                errors.append(f"Transcript/audio processing error: {str(e)}")
            
            # 2. Extract and process screenshots
            try:
                if progress_callback:
                    progress_callback(65, "Extracting screenshots...")
                
                screenshot_success = self.youtube_extractor.extract_and_save_screenshot(interval=10)
                if screenshot_success:
                    if progress_callback:
                        progress_callback(75, "Processing screenshots with AI...")
                    
                    # Process screenshots with Gemini API
                    image_descriptions = self._process_screenshots(
                        self.youtube_extractor.get_screenshot_path(),
                        video_id,
                        progress_callback
                    )
                    
                    if image_descriptions:
                        if progress_callback:
                            progress_callback(90, "Saving image analysis to database...")
                        # Save to database as single JSON array
                        VideoAnalysis.create(
                            video_id=youtube_url,
                            model_type="image_descriptions",
                            model_output=json.dumps(image_descriptions)
                        )
                        processed_components.append("image_descriptions")
                        print(f"✅ {len(image_descriptions)} image descriptions processed and saved")
                    else:
                        errors.append("No screenshots were successfully processed")
                else:
                    errors.append("Failed to extract screenshots")
                    
            except Exception as e:
                errors.append(f"Screenshot processing error: {str(e)}")
            
            # Determine overall success
            if processed_components:
                if progress_callback:
                    progress_callback(95, "Cleaning up temporary files...")
                
                # Clean up generated files after successful processing
                print("🧹 Starting cleanup of generated files...")
                self._cleanup_generated_files(video_id)
                
                success_msg = f"Successfully processed: {', '.join(processed_components)}"
                if errors:
                    success_msg += f". Errors encountered: {'; '.join(errors)}"
                return True, success_msg
            else:
                error_msg = f"Failed to process any components. Errors: {'; '.join(errors)}"
                return False, error_msg
                
        except Exception as e:
            return False, f"Unexpected error during preprocessing: {str(e)}"


# Sample run
def main():
    """Test the VideoPreprocessor with a sample YouTube URL."""
    preprocessor = VideoPreprocessor()
    
    # Test URL - replace with actual YouTube URL
    test_url = "https://www.youtube.com/watch?v=nBpPe9UweWs"
    test_url = "https://www.youtube.com/watch?v=SXOHCiukZPw&pp=ygUMYnJlYWtpbmcgYmFk"
    
    print(f"Starting preprocessing for: {test_url}")
    success, message = preprocessor.preprocess_youtube_url(test_url)
    
    if success:
        print(f"✅ Preprocessing successful: {message}")
    else:
        print(f"❌ Preprocessing failed: {message}")


if __name__ == "__main__":
    main()
