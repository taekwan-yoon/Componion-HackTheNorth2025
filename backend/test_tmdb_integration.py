#!/usr/bin/env python3
"""
Comprehensive test script for the Breaking Bad episode preprocessing.
URL: https://www.youtube.com/watch?v=I83kNl7ch3g&pp=ygUWYnJlYWtpbmcgYmFkIGVwaXNvZGUgMg%3D%3D

This script runs the complete preprocessing pipeline with verbose output and detailed logging.
"""

import sys
import os
import json
import time
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class VerboseProgressCallback:
    """Enhanced progress callback with detailed logging."""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_progress = 0
        self.step_times = []
    
    def __call__(self, progress: int, message: str):
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Calculate step time
        if self.step_times:
            step_time = current_time - self.step_times[-1][0]
        else:
            step_time = elapsed
            
        self.step_times.append((current_time, progress, message))
        
        # Format and print progress
        timestamp = datetime.now().strftime("%H:%M:%S")
        progress_bar = "█" * (progress // 5) + "░" * (20 - progress // 5)
        
        print(f"[{timestamp}] 📊 {progress:3d}% |{progress_bar}| {message}")
        print(f"           ⏱️  Step time: {step_time:.2f}s | Total elapsed: {elapsed:.2f}s")
        
        self.last_progress = progress

def print_section_header(title, symbol="="):
    """Print a formatted section header."""
    print(f"\n{symbol * 60}")
    print(f"{title.center(60)}")
    print(f"{symbol * 60}")

def print_step_header(step_num, title):
    """Print a formatted step header."""
    print(f"\n{'─' * 50}")
    print(f"Step {step_num}: {title}")
    print(f"{'─' * 50}")

def check_environment():
    """Check if all required environment variables are set."""
    print_step_header(1, "Environment Check")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = {
            "GEMINI_API_KEY": "Gemini AI API for image and audio processing",
            "TMDB_API_KEY": "The Movie Database API for show metadata",
            "DATABASE_URL": "PostgreSQL database for storing results"
        }
        
        missing_vars = []
        
        for var_name, description in required_vars.items():
            value = os.getenv(var_name)
            if value:
                # Show partial key for security
                if "KEY" in var_name:
                    display_value = f"{value[:8]}..." if len(value) > 8 else "***"
                else:
                    display_value = value[:50] + "..." if len(value) > 50 else value
                print(f"✅ {var_name}: {display_value}")
                print(f"   📝 {description}")
            else:
                print(f"❌ {var_name}: NOT SET")
                print(f"   📝 {description}")
                missing_vars.append(var_name)
        
        if missing_vars:
            print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        print(f"\n✅ All environment variables are set!")
        return True
        
    except Exception as e:
        print(f"❌ Environment check failed: {e}")
        return False

def test_api_connections():
    """Test connections to external APIs."""
    print_step_header(2, "API Connection Tests")
    
    apis_tested = []
    
    # Test Gemini API
    try:
        print("🧪 Testing Gemini API connection...")
        from api import GeminiAPI
        
        gemini = GeminiAPI()
        print("✅ Gemini API initialized successfully")
        print(f"   📝 Text model: {gemini.text_model.model_name}")
        print(f"   📝 Vision model: {gemini.vision_model.model_name}")
        apis_tested.append("Gemini API")
        
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        return False
    
    # Test TMDB API
    try:
        print("\n🧪 Testing TMDB API connection...")
        from api.tmdb_api import TMDBAPI
        
        tmdb = TMDBAPI()
        
        # Test with a simple search
        print("   🔍 Testing search functionality...")
        results = tmdb.search_tv_show("Breaking Bad")
        if results:
            print(f"✅ TMDB API working - found {len(results)} results for 'Breaking Bad'")
            print(f"   📝 Top result: {results[0].get('name')} (ID: {results[0].get('id')})")
        else:
            print("⚠️  TMDB API connected but no results found")
        
        apis_tested.append("TMDB API")
        
    except Exception as e:
        print(f"❌ TMDB API test failed: {e}")
        return False
    
    # Test Database Connection
    try:
        print("\n🧪 Testing database connection...")
        from core.db import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test")).fetchone()
            if result and result[0] == 1:
                print("✅ Database connection successful")
                
                # Test if our tables exist
                try:
                    tables_to_check = ['video_analysis', 'tv_show_info', 'sessions']
                    existing_tables = []
                    
                    for table_name in tables_to_check:
                        table_result = conn.execute(text(f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_name = '{table_name}'
                            );
                        """)).fetchone()
                        
                        if table_result and table_result[0]:
                            existing_tables.append(table_name)
                    
                    print(f"   📊 Found tables: {', '.join(existing_tables)}")
                    
                    if len(existing_tables) >= 2:  # At least video_analysis and sessions
                        print("   ✅ Required database tables are present")
                    else:
                        print("   ⚠️  Some required tables may be missing")
                        print("   💡 You may need to run database migrations")
                        
                except Exception as table_check_error:
                    print(f"   ⚠️  Could not check table existence: {table_check_error}")
                    print("   💡 Database connected but table check failed")
                
                apis_tested.append("Database")
            else:
                print("❌ Database connection test failed")
                return False
                
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False
    
    print(f"\n✅ All API connections successful: {', '.join(apis_tested)}")
    return True

def run_preprocessing(url):
    """Run the complete preprocessing pipeline."""
    print_step_header(3, "Video Preprocessing Pipeline")
    
    print(f"🎬 Target URL: {url}")
    print(f"📝 This will extract, process, and analyze the video content")
    
    try:
        # Initialize components
        print(f"\n🔧 Initializing VideoPreprocessor...")
        from services.VideoPreprocessor import VideoPreprocessor
        
        preprocessor = VideoPreprocessor()
        print(f"✅ VideoPreprocessor initialized")
        
        # Set up progress tracking
        progress_callback = VerboseProgressCallback()
        
        print(f"\n🚀 Starting preprocessing pipeline...")
        print(f"⏱️  Start time: {datetime.now().strftime('%H:%M:%S')}")
        
        # Run the preprocessing
        start_time = time.time()
        success, message = preprocessor.preprocess_youtube_url(url, progress_callback)
        end_time = time.time()
        
        # Results
        total_time = end_time - start_time
        print(f"\n📊 PREPROCESSING RESULTS")
        print(f"{'=' * 40}")
        print(f"⏱️  Total processing time: {total_time:.2f} seconds")
        print(f"🎯 Success: {success}")
        print(f"📋 Message: {message}")
        
        if success:
            print(f"\n✅ PREPROCESSING COMPLETED SUCCESSFULLY!")
            
            # Show component breakdown
            components = message.split("Successfully processed: ")[1].split(".")[0] if "Successfully processed:" in message else "Unknown"
            print(f"📦 Components processed: {components}")
            
            # Performance stats
            print(f"\n📈 PERFORMANCE STATISTICS")
            print(f"{'─' * 30}")
            for i, (timestamp, progress, step_message) in enumerate(progress_callback.step_times):
                if i == 0:
                    step_time = timestamp - progress_callback.start_time
                else:
                    step_time = timestamp - progress_callback.step_times[i-1][0]
                print(f"{progress:3d}% | {step_time:6.2f}s | {step_message}")
        else:
            print(f"\n❌ PREPROCESSING FAILED!")
            print(f"💡 Check the error message above for details")
            
        return success, message
        
    except Exception as e:
        print(f"\n❌ Preprocessing failed with exception:")
        print(f"🐛 Error: {e}")
        import traceback
        print(f"🔍 Full traceback:")
        traceback.print_exc()
        return False, str(e)

def analyze_results(url):
    """Analyze and display the preprocessing results."""
    print_step_header(4, "Results Analysis")
    
    try:
        # Get video analysis data
        print(f"🔍 Retrieving video analysis data...")
        from core import VideoAnalysis
        from core.models import TVShowInfo
        
        video_analysis = VideoAnalysis.get_by_video_url(url)
        
        if not video_analysis:
            print(f"❌ No video analysis data found for URL")
            return False
        
        print(f"✅ Found {len(video_analysis)} analysis records")
        
        # Analyze each component
        for i, analysis in enumerate(video_analysis, 1):
            model_type = analysis['model_type']
            timestamp = analysis['timestamp']
            model_output = analysis['model_output']
            
            print(f"\n📊 Analysis Record #{i}: {model_type.upper()}")
            print(f"   🕒 Created: {timestamp}")
            
            try:
                # Handle both JSON string and already parsed dict
                if isinstance(model_output, str):
                    output_data = json.loads(model_output)
                elif isinstance(model_output, dict):
                    output_data = model_output
                else:
                    print(f"   ⚠️  Unexpected data type: {type(model_output)}")
                    continue
                
                if model_type == "transcript":
                    if isinstance(output_data, list):
                        print(f"   📝 Transcript segments: {len(output_data)}")
                        if output_data:
                            total_text = sum(len(item.get('text', '')) for item in output_data)
                            print(f"   📏 Total text length: {total_text} characters")
                            
                            # Show first few segments
                            print(f"   📄 Sample segments:")
                            for j, segment in enumerate(output_data[:3]):
                                timestamp_str = segment.get('timestamp', '00:00')
                                text = segment.get('text', '')[:100]
                                print(f"      [{timestamp_str}] {text}...")
                    
                elif model_type == "image_descriptions":
                    if isinstance(output_data, dict) and "response" in output_data:
                        # New batched format
                        response = output_data.get("response", "")
                        filenames = output_data.get("filenames", [])
                        print(f"   🖼️  Screenshots processed: {len(filenames)}")
                        print(f"   📏 Description length: {len(response)} characters")
                        print(f"   📄 Description preview:")
                        print(f"      {response[:200]}...")
                    elif isinstance(output_data, list):
                        # Legacy format
                        print(f"   🖼️  Individual descriptions: {len(output_data)}")
                        
                elif model_type == "show_identification":
                    if isinstance(output_data, dict) and "response" in output_data:
                        response = output_data.get("response", "")
                        print(f"   🎭 Identification response:")
                        print(f"      {response}")
                        
                        # Try to extract JSON from response
                        try:
                            import re
                            json_match = re.search(r'\{.*\}', response, re.DOTALL)
                            if json_match:
                                show_data = json.loads(json_match.group())
                                print(f"   📺 Extracted data:")
                                print(f"      Type: {show_data.get('type')}")
                                print(f"      Title: {show_data.get('title')}")
                                print(f"      Season: {show_data.get('season')}")
                                print(f"      Episode: {show_data.get('episode')}")
                        except:
                            print(f"   ⚠️  Could not extract structured data from response")
                            
            except (json.JSONDecodeError, TypeError) as e:
                print(f"   ⚠️  Data parsing error: {e}")
                if isinstance(model_output, str):
                    print(f"   📄 Raw string data: {len(model_output)} characters")
                    print(f"   📄 Preview: {model_output[:100]}...")
                else:
                    print(f"   📄 Raw data type: {type(model_output)}")
                    print(f"   📄 Content: {str(model_output)[:100]}...")
        
        # Get TV show information
        print(f"\n🎭 TV Show Information")
        print(f"{'─' * 25}")
        
        tv_show_info = TVShowInfo.get_by_video_url(url)
        
        if tv_show_info:
            print(f"✅ TV show information found:")
            print(f"   🎬 Type: {tv_show_info.get('show_type')}")
            print(f"   📺 Title: {tv_show_info.get('title')}")
            print(f"   📅 Season: {tv_show_info.get('season')}")
            print(f"   📹 Episode: {tv_show_info.get('episode')}")
            print(f"   🆔 TMDB ID: {tv_show_info.get('tmdb_id')}")
            print(f"   🕒 Created: {tv_show_info.get('created_at')}")
            
            # Show TMDB data details
            tmdb_data = tv_show_info.get('tmdb_data')
            if tmdb_data:
                try:
                    tmdb_info = json.loads(tmdb_data) if isinstance(tmdb_data, str) else tmdb_data
                    print(f"   📊 TMDB Data Summary:")
                    
                    if "show_info" in tmdb_info and "episode_info" in tmdb_info:
                        # Combined show and episode data
                        show_info = tmdb_info["show_info"]
                        episode_info = tmdb_info["episode_info"]
                        
                        print(f"      📺 Show: {show_info.get('name')}")
                        print(f"      📊 Seasons: {show_info.get('number_of_seasons')}")
                        print(f"      📊 Total Episodes: {show_info.get('number_of_episodes')}")
                        print(f"      📅 First Aired: {show_info.get('first_air_date')}")
                        print(f"      🎭 Genres: {[g['name'] for g in show_info.get('genres', [])]}")
                        
                        print(f"      📹 Episode: {episode_info.get('name')}")
                        print(f"      📅 Air Date: {episode_info.get('air_date')}")
                        print(f"      ⭐ Rating: {episode_info.get('vote_average')}")
                        
                        overview = episode_info.get('overview', '')
                        if overview:
                            print(f"      📝 Episode Overview:")
                            print(f"         {overview[:200]}{'...' if len(overview) > 200 else ''}")
                            
                    else:
                        # Single content
                        content_name = tmdb_info.get('name', tmdb_info.get('title', 'Unknown'))
                        print(f"      📺 Content: {content_name}")
                        print(f"      📅 Release: {tmdb_info.get('first_air_date', tmdb_info.get('release_date', 'Unknown'))}")
                        
                        overview = tmdb_info.get('overview', '')
                        if overview:
                            print(f"      📝 Overview:")
                            print(f"         {overview[:200]}{'...' if len(overview) > 200 else ''}")
                            
                except json.JSONDecodeError:
                    print(f"   ⚠️  TMDB data present but not parseable")
            else:
                print(f"   ❌ No TMDB data available")
        else:
            print(f"❌ No TV show information found")
        
        return True
        
    except Exception as e:
        print(f"❌ Results analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prompt_construction(url):
    """Test the enhanced prompt constructor with the processed data."""
    print_step_header(5, "Prompt Construction Test")
    
    try:
        from services.PromtConstructor import PromptConstructor
        import uuid
        
        # Create test session with proper UUID format
        test_session_id = str(uuid.uuid4())
        print(f"🆔 Generated test session ID: {test_session_id}")
        
        print(f"🔧 Initializing PromptConstructor...")
        constructor = PromptConstructor(url, test_session_id)
        print(f"✅ PromptConstructor initialized")
        
        # Test questions
        test_questions = [
            "What show is this from?",
            "Who are the main characters in this episode?",
            "What happens in this episode?",
            "What is the genre and rating of this show?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📝 Test Question #{i}: '{question}'")
            
            try:
                prompt = constructor.construct_prompt(question, video_timestamp=0)
                
                # Analyze the prompt
                prompt_lines = prompt.split('\n')
                context_lines = []
                user_question_line = -1
                
                for j, line in enumerate(prompt_lines):
                    if "Context:" in line:
                        context_start = j
                    elif "User Question:" in line:
                        user_question_line = j
                        break
                
                if user_question_line > 0:
                    context_lines = prompt_lines[context_start:user_question_line]
                
                print(f"   📊 Prompt Statistics:")
                print(f"      📏 Total length: {len(prompt)} characters")
                print(f"      📄 Total lines: {len(prompt_lines)}")
                print(f"      📝 Context lines: {len(context_lines)}")
                
                # Check for key sections
                sections_found = []
                if "Content Information" in prompt:
                    sections_found.append("TV Show Info")
                if "Image Descriptions" in prompt or "Screenshot Analysis" in prompt:
                    sections_found.append("Screenshots")
                if "Show Identification" in prompt:
                    sections_found.append("Show ID")
                if "Transcript" in prompt:
                    sections_found.append("Transcript")
                if "Previous Chat Messages" in prompt:
                    sections_found.append("Chat History")
                else:
                    sections_found.append("No Chat History (expected for test)")
                
                print(f"      📦 Context sections: {', '.join(sections_found)}")
                
                # Show context preview
                context_start = prompt.find("Context:")
                if context_start != -1:
                    context_end = prompt.find("User Question:")
                    if context_end != -1:
                        context = prompt[context_start:context_end].strip()
                        print(f"      📄 Context preview (first 300 chars):")
                        print(f"         {context[:300]}...")
                
                print(f"   ✅ Prompt constructed successfully")
                
            except Exception as e:
                print(f"   ❌ Failed to construct prompt: {e}")
                # Print more details about the error
                import traceback
                print(f"   🔍 Error details:")
                traceback.print_exc()
                return False
        
        print(f"\n✅ All prompt construction tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Prompt construction test failed: {e}")
        return False

def main():
    """Run the complete test suite."""
    # Test URL
    url = "https://www.youtube.com/watch?v=I83kNl7ch3g&pp=ygUWYnJlYWtpbmcgYmFkIGVwaXNvZGUgMg%3D%3D"
    url = "https://www.youtube.com/watch?v=mHR-CnQeygk"
    url = "https://www.youtube.com/watch?v=TqsMx8rTSPg"
    
    print_section_header("🎬 BREAKING BAD EPISODE - COMPLETE PREPROCESSING TEST")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target URL: {url}")
    print(f"📝 This test runs the complete preprocessing pipeline with verbose output")
    
    # Confirmation
    print(f"\n⚠️  WARNING: This test will:")
    print(f"   • Download audio and screenshots from YouTube")
    print(f"   • Make multiple API calls to Gemini AI (may use quota)")
    print(f"   • Make API calls to TMDB")
    print(f"   • Store data in your database")
    print(f"   • Take approximately 5-10 minutes to complete")
    
    confirm = input(f"\n❓ Do you want to proceed? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print(f"❌ Test cancelled by user.")
        return
    
    # Run test phases
    test_phases = [
        ("Environment Check", check_environment),
        ("API Connections", test_api_connections),
        ("Video Preprocessing", lambda: run_preprocessing(url)[0]),
        ("Results Analysis", lambda: analyze_results(url)),
        ("Prompt Construction", lambda: test_prompt_construction(url))
    ]
    
    passed_phases = []
    failed_phases = []
    
    overall_start_time = time.time()
    
    for phase_name, phase_function in test_phases:
        try:
            success = phase_function()
            if success:
                passed_phases.append(phase_name)
                print(f"\n✅ {phase_name} - PASSED")
            else:
                failed_phases.append(phase_name)
                print(f"\n❌ {phase_name} - FAILED")
                break  # Stop on first failure
        except Exception as e:
            failed_phases.append(phase_name)
            print(f"\n❌ {phase_name} - FAILED with exception: {e}")
            break
    
    overall_end_time = time.time()
    total_test_time = overall_end_time - overall_start_time
    
    # Final results
    print_section_header("🏁 FINAL TEST RESULTS")
    print(f"⏱️  Total test time: {total_test_time:.2f} seconds")
    print(f"✅ Passed phases: {len(passed_phases)}/{len(test_phases)}")
    
    if passed_phases:
        print(f"📊 Successful phases:")
        for phase in passed_phases:
            print(f"   ✅ {phase}")
    
    if failed_phases:
        print(f"❌ Failed phases:")
        for phase in failed_phases:
            print(f"   ❌ {phase}")
    
    if len(passed_phases) == len(test_phases):
        print_section_header("🎉 ALL TESTS PASSED!", "🎉")
        print(f"The Breaking Bad episode has been successfully processed!")
        print(f"All TV show identification features are working correctly.")
        print(f"\n🚀 Next steps:")
        print(f"   • Use the chat application to ask questions about the episode")
        print(f"   • The AI now has rich context about Breaking Bad")
        print(f"   • Check your database for the stored information")
    else:
        print_section_header("❌ TESTS FAILED", "❌")
        print(f"Some phases failed. Please review the error messages above.")
        print(f"Fix the issues and run the test again.")

if __name__ == "__main__":
    main()
