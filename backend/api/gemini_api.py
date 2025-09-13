import os
import google.generativeai as genai
from PIL import Image
import time
from dotenv import load_dotenv, find_dotenv

class GeminiAPI:
    def __init__(self):
        # Get Gemini API Key from .env
        load_dotenv(find_dotenv())
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key: 
            raise ValueError("Error: GEMINI_API_KEY environment variable not set.")

        # Configure the API key
        genai.configure(api_key=self.api_key)

        # Initialize models
        # LLM (text2text)
        self.text_model = genai.GenerativeModel('gemini-1.5-flash')
        print("Initialized text model: gemini-1.5-flash")

        # image2text
        self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
        print("Initialized vision model: gemini-1.5-flash")

    def image2text(self, image_path: str, prompt: str) -> str:
        print(f"Analyzing image: {image_path}...")

        try:
            img = Image.open(image_path)
        except FileNotFoundError:
            return f"Error: The file '{image_path}' was not found."
        except Exception as e:
            return f"Error: {str(e)}"
        
        try:
            # Call API
            response = self.vision_model.generate_content([prompt, img])
        except Exception as e:
            return f"Error during image analysis: {str(e)}"

        return response.text

    def images2text(self, image_paths: list, prompt: str) -> str:
        """
        Analyze multiple images in a single API call.
        
        Args:
            image_paths: List of paths to image files
            prompt: Text prompt for analysis
            
        Returns:
            Combined analysis response from Gemini
        """
        print(f"Analyzing {len(image_paths)} images together...")

        if not image_paths:
            return "Error: No image paths provided."

        try:
            # Load all images
            images = []
            for image_path in image_paths:
                try:
                    img = Image.open(image_path)
                    images.append(img)
                except FileNotFoundError:
                    print(f"Warning: File '{image_path}' not found, skipping...")
                    continue
                except Exception as e:
                    print(f"Warning: Error loading '{image_path}': {e}, skipping...")
                    continue
            
            if not images:
                return "Error: No valid images could be loaded."
            
            # Build content array: [prompt, image1, image2, ...]
            content = [prompt] + images
            
            # Call API with multiple images
            response = self.vision_model.generate_content(content)
            
            print(f"Successfully analyzed {len(images)} images")
            return response.text
            
        except Exception as e:
            return f"Error during multi-image analysis: {str(e)}"

    def audio2text(self, audio_path: str, prompt: str):
        # TODO: Gemini API doesn't provide the option to put timestamps unless we use google-cloud-speech
        # Consider just using the local model because that was good enough. 

        # Upload the audio file to the Gemini API
        try:
            audio_file = genai.upload_file(path=audio_path)
        except FileNotFoundError:
            return f"Error: The file '{audio_path}' was not found."
        except Exception as e:
            return f"Error: {str(e)}"
        
        # Wait for the file to be processed
        while audio_file.state.name == "PROCESSING":
            print("Waiting for file processing...")
            time.sleep(2)
            audio_file = genai.get_file(audio_file.name)
        
        if audio_file.state.name == "FAILED":
            return f"Error: Audio file processing failed: {audio_file.state}"
    
        print("Transcribing audio...")
        try:
            response = self.text_model.generate_content([prompt, audio_file])

            # Delete the audio file after transcription
            genai.delete_file(audio_file.name)
            return response.text
        except Exception as e:
            return f"Error during audio transcription: {str(e)}"

    def llm_inference(self, prompt: str) -> str:
        print(f"Sending prompt to LLM: '{prompt[:30]}...'")
        try:
            response = self.text_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error during LLM inference: {str(e)}"
        
# Example usage
if __name__ == "__main__":
    pass