import os
import yt_dlp

class YoutubeExtractor:
    def __init__(self, url):      
        # Options for yt-dlp to extract audio 
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192', # Standard quality
            }],
            'outtmpl': None, # Will be set dynamically
            'noplaylist': True,
            'quiet': False,
            # The following options might be needed if youtube is blocking downloads due to bot detection
            # 'cookies-from-browser': 'chrome', # or 'firefox', etc. - requires browser access
            # 'cookiefile': '/path/to/your/cookies.txt', # export cookies from your browser
        }
        
        # URL of the YouTube video to process
        self.url = url

        # Video ID of the YouTube video to process
        self.video_id = None

        # Paths to store extracted data
        self.audio_path = None
        self.screenshot_path = None
        self.transcript_path = None

        # to check if the subtitles exist in youtube already
        self.youtube_transcript_exists = False

    #region Getters and Setters
    def set_url(self, url: str): 
        self.url = url

    def get_url(self) -> str:
        return self.url
    
    def set_video_id(self, video_id: str):
        self.video_id = video_id

    def get_video_id(self) -> str | None:
        return self.video_id
    
    def set_audio_path(self, path: str):
        self.audio_path = path

    def get_audio_path(self) -> str | None:
        return self.audio_path
    
    def set_screenshot_path(self, path: str):
        self.screenshot_path = path

    def get_screenshot_path(self) -> str | None:
        return self.screenshot_path

    def set_transcript_path(self, path: str):
        self.transcript_path = path
    
    def get_transcript_path(self) -> str | None:
        return self.transcript_path
    
    def set_youtube_transcript_exists(self, exists: bool):
        self.youtube_transcript_exists = exists
    
    def get_youtube_transcript_exists(self) -> bool:
        return self.youtube_transcript_exists
    #endregion

    def extract_video_id_from_url(self) -> str | None:
        """
        Extracts the video ID from a YouTube URL using regex.
        This handles various URL formats (e.g., /watch, /embed, youtu.be).
        """
        import re
        
        url = self.get_url()

        regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
        match = re.search(regex, url)

        # if url matches the expected formats
        if match: 
            return match.group(1)
        
        # if not, return None
        print("Could not find video ID in the URL.")
        return None 
    
    def extract_and_save_transcript(self) -> bool:
        """
        Attempts to extract and save the transcript for a given YouTube video ID. 
        It prioritizes manually created English transcripts, then generated English,
        and finally any other available transcript.
        """
        from youtube_transcript_api import YouTubeTranscriptApi, _errors

        transcript_path = self.get_transcript_path()
        video_id = self.get_video_id()
        
        os.makedirs(transcript_path, exist_ok=True)
        try:
            # Instantiate the API class
            ytt_api = YouTubeTranscriptApi()
            # Use the .list() method to get the list of available transcripts
            transcript_list = ytt_api.list(video_id)
            transcript = None

            try:
                # Prioritize English transcripts that were manually created
                transcript = transcript_list.find_manually_created_transcript(['en', 'en-US'])
                print("✅ Found a manually created English transcript.")
            except _errors.NoTranscriptFound:
                print("ℹ️ No manual English transcript found. Checking for generated transcripts.")
                try:
                    # Check for auto-generated transcripts
                    transcript = transcript_list.find_generated_transcript(['en', 'en-US'])
                    print("✅ Found an auto-generated English transcript.")
                except _errors.NoTranscriptFound:
                    print("ℹ️ No generated English transcript found. Checking for any other language.")
                    # If English is not available, just get the first one in the list
                    transcript = next(iter(transcript_list))
                    print(f"✅ Found a transcript in language: '{transcript.language_code}'")

            # Fetch and format the transcript text
            transcript_data = transcript.fetch()

            # TODO: Think of how to pass on the extracted data to the model (based on model input)
            formatted_lines = []
            # Fix this section:
            for item in transcript_data:
                minutes, seconds = divmod(int(item.start), 60)  # Use dot notation
                timestamp = f"{minutes:02d}:{seconds:02d}"
                formatted_lines.append(f"[{timestamp}] {item.text}")  # Use dot notation
            full_transcript = "\n".join(formatted_lines)

            # Save the transcript to a file
            # TODO: for now, we will save to a file, but consider passing on the data to model directly
            filename = os.path.join(transcript_path, f"{video_id}_transcript.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(full_transcript)
            print(f"Transcript saved to: {filename}")
            self.set_youtube_transcript_exists(True)
            return True

        except (_errors.NoTranscriptFound, _errors.TranscriptsDisabled):
            print("❌ No pre-existing transcripts found for this video.")
            self.set_youtube_transcript_exists(False)
            return False
        except Exception as e:
            print(f"An unexpected error occurred while fetching the transcript: {e}")
            self.set_youtube_transcript_exists(False)
            return False
    
    def extract_and_save_audio(self) -> bool:
        """
        Extracts audio from a YouTube URL and saves it as an MP3 file.
        This function is called as a fallback if no transcript is found. 
        """        

        url = self.get_url()
        video_id = self.get_video_id()
        audio_path = self.get_audio_path()

        # TODO: consider saving as .wav instead (since many models take .wav instead)
        os.makedirs(audio_path, exist_ok=True)
        output_filename = os.path.join(audio_path, f"{video_id}_audio")
        self.ydl_opts['outtmpl'] = output_filename

        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                print(f"Downloading audio for '{url}'...")
                ydl.download([url])
            print(f"Audio downloaded successfully: {output_filename}.mp3")
            return True
        
        except Exception as e:
            print(f"An error occurred while extracting audio: {e}.")

        return False
    
    def extract_and_save_screenshot(self, interval: int = 5) -> bool:
        """
        Extracts screenshots from a YouTube video at a given interval and saves them as JPG files.
        """
        # TODO: Check the actual format of the screenshot files (i.e. JPG or PNG, etc.)
        # TODO: Double check if the timing (timestamps) are precise

        import cv2
        url = self.get_url()
        video_id = self.get_video_id()
        screenshot_path = self.get_screenshot_path()

        print(f"Starting screenshot extraction for video ID: {video_id}")

        ydl_opts = {'format': 'best'}

        os.makedirs(screenshot_path, exist_ok=True)

        try: 
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_url = info_dict.get("url", None)
        except Exception as e:
            print(f"An error occurred while extracting video information: {e}")
            return False

        if not video_url:
            print("❌ No video URL found.")
            return False
        
        cap = cv2.VideoCapture(video_url)
        if not cap.isOpened():
            print("❌ Failed to open video stream.")
            return False
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            print("❌ Failed to retrieve video FPS.")
            return False
        
        screenshot_interval = int(fps * interval)
        screenshot_count = 0
        saved_screenshot_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break # End of video

            if screenshot_count % screenshot_interval == 0:
                # Calculate timestamp for the filename
                current_seconds = round(screenshot_count / fps)

                # Create a unique filename for each screenshot
                screenshot_filename = os.path.join(screenshot_path, f"{video_id}_screenshot_{current_seconds:04}.jpg")

                # Save the frame as a JGP file
                cv2.imwrite(screenshot_filename, frame)
                saved_screenshot_count += 1
            
            screenshot_count += 1
        
        cap.release()
        print(f"Extracted {saved_screenshot_count} screenshots and saved to {self.screenshot_path}")

        return True

def main():
    video_url = "https://www.youtube.com/watch?v=nBpPe9UweWs" # example with caption
    # video_url = "https://www.youtube.com/watch?v=0yZcDeVsj_Y" # example without caption

    # Initialize the extractor
    extractor = YoutubeExtractor(video_url)

    # Extract video ID from the URL
    video_id = extractor.extract_video_id_from_url()

    # Validate video ID
    if not video_id:
        print("Invalid YouTube URL. Exiting.")
        return
    
    # Set paths and video ID
    extractor.set_video_id(video_id)
    extractor.set_audio_path("../data/audio")
    extractor.set_screenshot_path("../data/screenshots")
    extractor.set_transcript_path("../data/transcripts")

    # First, try to extract and save the transcript
    # if extractor.extract_and_save_transcript():
    if not extractor.extract_and_save_transcript():
        print("No transcript found. Falling back to audio extraction.")
        # If no transcript, extract audio as a fallback
        # if extractor.extract_and_save_audio():
        if not extractor.extract_and_save_audio():
            print("Audio extraction failed.")
        else:
            print("Audio extraction succeeded.")
    else:
        print("Transcript extraction succeeded.")

    # Always try to extract screenshots
    if not extractor.extract_and_save_screenshot(interval=5):
        print("Screenshot extraction failed.")
    else:
        print("Screenshot extraction succeeded.")

if __name__ == "__main__":
    main()