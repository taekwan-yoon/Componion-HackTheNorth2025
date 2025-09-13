import os
import json
import glob
from typing import Tuple, List, Dict, Any
from youtube.scripts.YoutubeExtractor import YoutubeExtractor
from api import GeminiAPI
from api.tmdb_api import TMDBAPI
from core import VideoAnalysis
from core.models import TVShowInfo


class VideoPreprocessor:
    """
    VideoPreprocessor handles the extraction and analysis of YouTube videos.
    
    Recent Updates:
    - Refactored _process_screenshots to batch multiple images in a single Gemini API call
    - Added describe_screenshots() wrapper for detailed screenshot descriptions
    - Added identify_show_from_screenshots() wrapper for TV show identification
    - Updated main preprocessing flow to use the new batched approach
    """
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
    
    def _process_screenshots(
        self,
        screenshot_dir: str,
        video_id: str,
        prompt: str,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Process multiple screenshots together using Gemini API (single call).
        
        Args:
            screenshot_dir: Directory containing screenshots
            video_id: Video ID for filtering files
            prompt: Prompt to send to Gemini
            progress_callback: Optional progress update callback
            
        Returns:
            Dictionary with video_id, filenames, and Gemini's combined response
        """
        # Find all screenshot files for this video
        screenshot_pattern = os.path.join(screenshot_dir, f"{video_id}_screenshot_*.jpg")
        screenshot_files = sorted(glob.glob(screenshot_pattern))
        
        if not screenshot_files:
            print(f"No screenshots found for video {video_id}")
            return {"video_id": video_id, "filenames": [], "response": None}
        
        print(f"Processing {len(screenshot_files)} screenshots in one Gemini call...")

        try:
            # Progress update before sending to Gemini
            if progress_callback:
                progress_callback(80, f"Sending {len(screenshot_files)} screenshots to Gemini...")

            # Call Gemini API with multiple images in one request
            response = self.gemini_api.images2text(screenshot_files, prompt)

            if progress_callback:
                progress_callback(85, f"Processed all screenshots for {video_id}")

            return {
                "video_id": video_id,
                "filenames": [os.path.basename(f) for f in screenshot_files],
                "response": response
            }

        except Exception as e:
            print(f"Error processing screenshots for video {video_id}: {e}")
            return {"video_id": video_id, "filenames": [], "response": None}

    def describe_screenshots(self, screenshot_dir: str, video_id: str, progress_callback=None):
        """
        Describe screenshots in detail: subjects, actions, text, and composition.
        Returns individual descriptions with timestamps like the original format.
        """
        # Find all screenshot files for this video
        screenshot_pattern = os.path.join(screenshot_dir, f"{video_id}_screenshot_*.jpg")
        screenshot_files = sorted(glob.glob(screenshot_pattern))
        
        if not screenshot_files:
            print(f"No screenshots found for video {video_id}")
            return {"video_id": video_id, "descriptions": []}
        
        print(f"Processing {len(screenshot_files)} screenshots with individual descriptions...")

        # Create a prompt that asks for individual descriptions in a structured format
        prompt = (
            "Analyze these screenshots from a TV show or video. For each image, provide a detailed description "
            "focusing on main subjects, their names if recognizable, their actions, visible text, and overall scene composition. "
            "Return your response as a JSON array where each element corresponds to one screenshot in order, with this structure: "
            "[{\"description\": \"detailed description of first image\"}, {\"description\": \"detailed description of second image\"}, ...]"
        )

        try:
            # Progress update before sending to Gemini
            if progress_callback:
                progress_callback(80, f"Sending {len(screenshot_files)} screenshots to Gemini for individual descriptions...")

            # Call Gemini API with multiple images in one request
            response = self.gemini_api.images2text(screenshot_files, prompt)

            if progress_callback:
                progress_callback(85, f"Processing descriptions for {video_id}")

            # Parse the response to extract individual descriptions
            descriptions = []
            try:
                import re
                
                # Try to extract JSON array from response
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    parsed_descriptions = json.loads(json_match.group())
                    
                    # Create the timestamp-based format
                    for i, screenshot_file in enumerate(screenshot_files):
                        filename = os.path.basename(screenshot_file)
                        
                        # Extract timestamp from filename (e.g., "video_screenshot_0030.jpg" -> 30 seconds)
                        timestamp_match = re.search(r'_(\d{4})\.jpg$', filename)
                        if timestamp_match:
                            seconds = int(timestamp_match.group(1))
                            minutes = seconds // 60
                            seconds_remainder = seconds % 60
                            timestamp = f"{minutes:02d}:{seconds_remainder:02d}"
                        else:
                            # Fallback: assume 10-second intervals
                            seconds = i * 10
                            minutes = seconds // 60
                            seconds_remainder = seconds % 60
                            timestamp = f"{minutes:02d}:{seconds_remainder:02d}"
                        
                        # Get description for this image (if available)
                        description_text = ""
                        if i < len(parsed_descriptions) and "description" in parsed_descriptions[i]:
                            description_text = parsed_descriptions[i]["description"]
                        else:
                            description_text = f"Description not available for image {i+1}"
                        
                        descriptions.append({
                            "timestamp": timestamp,
                            "seconds": seconds if timestamp_match else i * 10,
                            "filename": filename,
                            "description": description_text
                        })
                else:
                    # Fallback: split response by common separators and assign to images
                    print("Could not parse JSON from response, attempting to split descriptions...")
                    
                    # Try to split the response into parts
                    parts = re.split(r'\n\n+|\d+\.\s+|Image \d+:', response)
                    parts = [part.strip() for part in parts if part.strip()]
                    
                    for i, screenshot_file in enumerate(screenshot_files):
                        filename = os.path.basename(screenshot_file)
                        
                        # Extract timestamp from filename
                        timestamp_match = re.search(r'_(\d{4})\.jpg$', filename)
                        if timestamp_match:
                            seconds = int(timestamp_match.group(1))
                            minutes = seconds // 60
                            seconds_remainder = seconds % 60
                            timestamp = f"{minutes:02d}:{seconds_remainder:02d}"
                        else:
                            seconds = i * 10
                            minutes = seconds // 60
                            seconds_remainder = seconds % 60
                            timestamp = f"{minutes:02d}:{seconds_remainder:02d}"
                        
                        # Get description for this image
                        description_text = parts[i] if i < len(parts) else f"Description not available for {filename}"
                        
                        descriptions.append({
                            "timestamp": timestamp,
                            "seconds": seconds if timestamp_match else i * 10,
                            "filename": filename,
                            "description": description_text
                        })
                        
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error parsing individual descriptions: {e}")
                # Ultimate fallback: create basic structure
                for i, screenshot_file in enumerate(screenshot_files):
                    filename = os.path.basename(screenshot_file)
                    seconds = i * 10
                    minutes = seconds // 60
                    seconds_remainder = seconds % 60
                    timestamp = f"{minutes:02d}:{seconds_remainder:02d}"
                    
                    descriptions.append({
                        "timestamp": timestamp,
                        "seconds": seconds,
                        "filename": filename,
                        "description": f"Could not process description for {filename}"
                    })

            return {
                "video_id": video_id,
                "descriptions": descriptions,
                "raw_response": response  # Keep the raw response for debugging
            }

        except Exception as e:
            print(f"Error processing screenshots for video {video_id}: {e}")
            return {"video_id": video_id, "descriptions": [], "error": str(e)}

    def identify_show_from_screenshots(self, screenshot_dir: str, video_id: str, progress_callback=None):
        """
        Try to identify the TV show from screenshots.
        Note: It may not be a TV show at all (could be a movie, ad, or something else).
        """
        prompt = (
            "These are multiple screenshots from a video. Identify if this is a TV show. "
            "If yes, provide the show's title and, if possible, the season and episode. "
            "If it's not a TV show, say clearly what it most likely is (e.g., a movie, commercial, YouTube video, etc.). "
            "Return your answer in JSON: {\"type\": \"TV Show/Movie/Other\", \"title\": \"...\", \"season\": ..., \"episode\": ...}."
        )
        return self._process_screenshots(screenshot_dir, video_id, prompt, progress_callback)
    
    def _process_show_identification_with_tmdb(self, youtube_url: str, show_identification_result: Dict[str, Any]) -> bool:
        """
        Process show identification result and fetch TMDB data if it's a TV show or movie.
        
        Args:
            youtube_url: The YouTube URL
            show_identification_result: Result from identify_show_from_screenshots
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            response = show_identification_result.get("response", "")
            if not response:
                print("No show identification response to process")
                return False
            
            # Try to parse JSON from the response
            try:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    show_data = json.loads(json_match.group())
                else:
                    # If no JSON found, create a basic structure
                    show_data = {
                        "type": "Other",
                        "title": None,
                        "season": None,
                        "episode": None
                    }
                    print("No JSON found in show identification response, using default structure")
            except json.JSONDecodeError:
                print("Failed to parse JSON from show identification response")
                show_data = {
                    "type": "Other", 
                    "title": None,
                    "season": None,
                    "episode": None
                }
            
            show_type = show_data.get("type", "Other")
            title = show_data.get("title")
            season = show_data.get("season")
            episode = show_data.get("episode")
            
            print(f"Identified content: Type={show_type}, Title={title}, Season={season}, Episode={episode}")
            
            # Initialize TMDB data variables
            tmdb_id = None
            tmdb_data = None
            
            # If it's a TV show or movie with a title, try to get TMDB data
            if title and show_type.lower() in ["tv show", "movie"]:
                try:
                    print(f"Searching TMDB for {show_type}: {title}")
                    tmdb_api = TMDBAPI()
                    
                    content_type = "tv" if "tv" in show_type.lower() else "movie"
                    tmdb_result = tmdb_api.search_and_get_best_match(title, content_type)
                    
                    if tmdb_result:
                        tmdb_id = tmdb_result.get("id")
                        tmdb_data = json.dumps(tmdb_result)
                        print(f"✅ Found TMDB data for {title} (ID: {tmdb_id})")
                        
                        # If it's a TV show and we have season/episode info, get episode details
                        if content_type == "tv" and season and episode and tmdb_id:
                            try:
                                episode_details = tmdb_api.get_tv_episode_details(tmdb_id, int(season), int(episode))
                                if episode_details:
                                    # Add episode details to TMDB data
                                    combined_data = {
                                        "show_info": tmdb_result,
                                        "episode_info": episode_details
                                    }
                                    tmdb_data = json.dumps(combined_data)
                                    print(f"✅ Found episode details for S{season}E{episode}")
                            except (ValueError, TypeError) as e:
                                print(f"Error getting episode details: {e}")
                    else:
                        print(f"❌ No TMDB data found for {title}")
                        
                except Exception as e:
                    print(f"Error fetching TMDB data: {e}")
            
            # Save to TV show info database
            TVShowInfo.create(
                video_url=youtube_url,
                show_type=show_type,
                title=title,
                season=season,
                episode=episode,
                tmdb_id=tmdb_id,
                tmdb_data=tmdb_data
            )
            
            print(f"✅ Saved TV show information to database")
            return True
            
        except Exception as e:
            print(f"Error processing show identification with TMDB: {e}")
            return False
    
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
                    
                    # Process screenshots with Gemini API - both description and show identification
                    screenshot_description = self.describe_screenshots(
                        self.youtube_extractor.get_screenshot_path(),
                        video_id,
                        progress_callback
                    )
                    
                    # Also identify if this is a TV show
                    show_identification = self.identify_show_from_screenshots(
                        self.youtube_extractor.get_screenshot_path(),
                        video_id,
                        progress_callback
                    )
                    
                    screenshots_processed = False
                    
                    if screenshot_description and screenshot_description.get("descriptions"):
                        if progress_callback:
                            progress_callback(88, "Saving image descriptions to database...")
                        # Save screenshot descriptions to database - use the descriptions array
                        VideoAnalysis.create(
                            video_id=youtube_url,
                            model_type="image_descriptions",
                            model_output=json.dumps(screenshot_description.get("descriptions", []))
                        )
                        processed_components.append("image_descriptions")
                        screenshots_processed = True
                        print(f"✅ {len(screenshot_description.get('descriptions', []))} screenshots described and saved")
                    
                    if show_identification and show_identification.get("response"):
                        if progress_callback:
                            progress_callback(90, "Saving show identification to database...")
                        # Save show identification to database
                        VideoAnalysis.create(
                            video_id=youtube_url,
                            model_type="show_identification",
                            model_output=json.dumps(show_identification)
                        )
                        processed_components.append("show_identification")
                        screenshots_processed = True
                        print(f"✅ Show identification processed and saved")
                        
                        # Process with TMDB to get additional show information
                        if progress_callback:
                            progress_callback(92, "Fetching additional show information from TMDB...")
                        
                        tmdb_success = self._process_show_identification_with_tmdb(youtube_url, show_identification)
                        if tmdb_success:
                            processed_components.append("tmdb_enrichment")
                            print(f"✅ TMDB enrichment completed")
                    
                    if not screenshots_processed:
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
