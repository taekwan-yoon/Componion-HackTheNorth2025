"""
Context Agent - Intelligent context enhancement for video chat assistant.

This agent analyzes user questions and decides what additional context
to fetch from external APIs (like TMDB) to provide better responses.
"""

from api.gemini_api import GeminiAPI
from api.tmdb_api import TMDBAPI
import json
import time


class ContextAgent:
    """
    An intelligent agent that analyzes user questions and TV show context
    to decide what additional information to fetch from TMDB.
    """
    
    def __init__(self, verbose=True):
        """
        Initialize the Context Agent.
        
        Args:
            verbose (bool): Enable detailed logging of decision-making process
        """
        self.verbose = verbose
        self.gemini_api = GeminiAPI()
        self.tmdb_api = TMDBAPI()
        
        if self.verbose:
            print("🤖 ContextAgent initialized with verbose logging")
    
    def _log(self, message: str, level: str = "INFO"):
        """Log messages with timestamps if verbose mode is enabled."""
        if self.verbose:
            timestamp = time.strftime("%H:%M:%S")
            emoji = {
                "INFO": "ℹ️",
                "DECISION": "🎯", 
                "API": "🔗",
                "SUCCESS": "✅",
                "ERROR": "❌",
                "THINKING": "🤔"
            }.get(level, "📝")
            print(f"{emoji} [{timestamp}] {message}")
    
    def analyze_and_enhance_context(self, user_question: str, tv_show_info: dict) -> str:
        """
        Main method: Analyze user question and fetch relevant TMDB context.
        
        Args:
            user_question: The user's question
            tv_show_info: Current TV show information from database
            
        Returns:
            str: Additional context from TMDB, or empty string if none needed
        """
        self._log("🚀 Starting context analysis and enhancement")
        self._log(f"User question: '{user_question}'")
        
        if not tv_show_info:
            self._log("No TV show info available, skipping enhancement", "INFO")
            return ""
        
        show_title = tv_show_info.get('title', 'Unknown')
        show_type = tv_show_info.get('show_type', 'tv')
        self._log(f"Analyzing context for: {show_title} ({show_type})")
        
        try:
            # Step 1: Analyze what type of context would be helpful
            context_type = self._analyze_question_intent(user_question, tv_show_info)
            
            # Step 2: Fetch additional context based on analysis
            if context_type == "none":
                self._log("Analysis determined no additional context needed", "DECISION")
                return ""
            
            additional_context = self._fetch_context_by_type(context_type, tv_show_info)
            
            if additional_context:
                self._log(f"Successfully enhanced context with {context_type} information", "SUCCESS")
                return additional_context
            else:
                self._log(f"No additional {context_type} context could be retrieved", "INFO")
                return ""
                
        except Exception as e:
            self._log(f"Error during context enhancement: {e}", "ERROR")
            return ""
    
    def _analyze_question_intent(self, user_question: str, tv_show_info: dict) -> str:
        """
        Use Gemini to analyze what type of additional context would be helpful.
        
        Returns:
            str: One of "cast", "similar", "seasons", "trivia", or "none"
        """
        self._log("Analyzing question intent with Gemini...", "THINKING")
        
        analysis_prompt = f"""You are analyzing a user's question about a TV show/movie to determine what additional information from TMDB (The Movie Database) would be helpful.

Current show information:
- Title: {tv_show_info.get('title', 'Unknown')}
- Type: {tv_show_info.get('show_type', 'Unknown')}
- Season: {tv_show_info.get('season', 'N/A')}
- Episode: {tv_show_info.get('episode', 'N/A')}

User's question: "{user_question}"

Based on the user's question, what specific TMDB information would be most helpful? Respond with ONE of these options:
1. "cast" - if they're asking about actors, characters, or who plays someone
2. "similar" - if they're asking for recommendations or similar shows
3. "seasons" - if they're asking about other seasons or episodes
4. "trivia" - if they're asking about production details, behind-the-scenes info
5. "none" - if the existing information is sufficient

Respond with ONLY the single word from the options above."""

        try:
            self._log("Sending analysis prompt to Gemini API...", "API")
            analysis_result = self.gemini_api.llm_inference(analysis_prompt).strip().lower()
            
            # Validate the response
            valid_responses = ["cast", "similar", "seasons", "trivia", "none"]
            if analysis_result not in valid_responses:
                self._log(f"Invalid Gemini response: '{analysis_result}', defaulting to 'none'", "ERROR")
                analysis_result = "none"
            
            self._log(f"Gemini analysis result: '{analysis_result}'", "DECISION")
            return analysis_result
            
        except Exception as e:
            self._log(f"Error during Gemini analysis: {e}", "ERROR")
            return "none"
    
    def _fetch_context_by_type(self, context_type: str, tv_show_info: dict) -> str:
        """
        Fetch specific type of context from TMDB.
        
        Args:
            context_type: Type of context to fetch ("cast", "similar", etc.)
            tv_show_info: TV show information
            
        Returns:
            str: Formatted context information
        """
        self._log(f"Fetching {context_type} context from TMDB...", "API")
        
        title = tv_show_info.get('title')
        show_type = tv_show_info.get('show_type', 'tv')
        tmdb_id = tv_show_info.get('tmdb_id')
        
        if not title:
            self._log("No title available, cannot fetch TMDB context", "ERROR")
            return ""
        
        # Get TMDB ID if not already available
        if not tmdb_id:
            self._log(f"No TMDB ID stored, searching for '{title}'...", "API")
            tmdb_data = self.tmdb_api.search_and_get_best_match(title, show_type)
            if tmdb_data and tmdb_data.get('id'):
                tmdb_id = tmdb_data['id']
                self._log(f"Found TMDB ID: {tmdb_id}", "SUCCESS")
            else:
                self._log("Could not find TMDB ID, context enhancement failed", "ERROR")
                return ""
        else:
            self._log(f"Using stored TMDB ID: {tmdb_id}", "INFO")
        
        # Fetch context based on type
        context_methods = {
            "cast": self._get_cast_info,
            "similar": self._get_similar_content,
            "seasons": self._get_seasons_info,
            "trivia": self._get_production_info
        }
        
        method = context_methods.get(context_type)
        if not method:
            self._log(f"Unknown context type: {context_type}", "ERROR")
            return ""
        
        try:
            if context_type == "seasons" and show_type != "tv":
                self._log("Seasons context requested for non-TV content, skipping", "INFO")
                return ""
            
            context_data = method(tmdb_id, show_type)
            
            if context_data:
                self._log(f"Successfully retrieved {context_type} context", "SUCCESS")
                return f"{context_type.replace('_', ' ').title()} Information:\n{context_data}"
            else:
                self._log(f"No {context_type} data available", "INFO")
                return ""
                
        except Exception as e:
            self._log(f"Error fetching {context_type} context: {e}", "ERROR")
            return ""
    
    def _get_cast_info(self, tmdb_id: int, content_type: str) -> str:
        """Get cast information from TMDB."""
        self._log(f"Fetching cast for TMDB ID {tmdb_id} ({content_type})", "API")
        
        try:
            if content_type.lower() == "tv":
                url = f"{self.tmdb_api.base_url}/tv/{tmdb_id}/credits"
            else:
                url = f"{self.tmdb_api.base_url}/movie/{tmdb_id}/credits"
            
            import requests
            response = requests.get(url, headers=self.tmdb_api.headers)
            
            if response.status_code == 200:
                data = response.json()
                cast = data.get('cast', [])[:6]  # Top 6 cast members
                
                self._log(f"Retrieved {len(cast)} cast members", "SUCCESS")
                
                cast_info = []
                for actor in cast:
                    name = actor.get('name', 'Unknown')
                    character = actor.get('character', 'Unknown')
                    cast_info.append(f"• {name} as {character}")
                
                return "\n".join(cast_info) if cast_info else ""
            else:
                self._log(f"TMDB API error: {response.status_code}", "ERROR")
                return ""
                
        except Exception as e:
            self._log(f"Error fetching cast info: {e}", "ERROR")
            return ""
    
    def _get_similar_content(self, tmdb_id: int, content_type: str) -> str:
        """Get similar content recommendations from TMDB."""
        self._log(f"Fetching similar content for TMDB ID {tmdb_id} ({content_type})", "API")
        
        try:
            if content_type.lower() == "tv":
                url = f"{self.tmdb_api.base_url}/tv/{tmdb_id}/similar"
            else:
                url = f"{self.tmdb_api.base_url}/movie/{tmdb_id}/similar"
            
            import requests
            response = requests.get(url, headers=self.tmdb_api.headers)
            
            if response.status_code == 200:
                data = response.json()
                similar = data.get('results', [])[:4]  # Top 4 similar items
                
                self._log(f"Retrieved {len(similar)} similar recommendations", "SUCCESS")
                
                similar_info = []
                for item in similar:
                    if content_type.lower() == "tv":
                        title = item.get('name', 'Unknown')
                        date = item.get('first_air_date', 'N/A')[:4]
                    else:
                        title = item.get('title', 'Unknown')
                        date = item.get('release_date', 'N/A')[:4]
                    
                    similar_info.append(f"• {title} ({date})")
                
                return "\n".join(similar_info) if similar_info else ""
            else:
                self._log(f"TMDB API error: {response.status_code}", "ERROR")
                return ""
                
        except Exception as e:
            self._log(f"Error fetching similar content: {e}", "ERROR")
            return ""
    
    def _get_seasons_info(self, tmdb_id: int, content_type: str = "tv") -> str:
        """Get seasons overview for TV shows."""
        self._log(f"Fetching seasons info for TMDB ID {tmdb_id}", "API")
        
        try:
            show_details = self.tmdb_api.get_tv_show_details(tmdb_id)
            
            if show_details and show_details.get('seasons'):
                seasons = show_details['seasons'][:5]  # First 5 seasons
                
                self._log(f"Retrieved info for {len(seasons)} seasons", "SUCCESS")
                
                seasons_info = []
                for season in seasons:
                    season_num = season.get('season_number', 'Unknown')
                    episode_count = season.get('episode_count', 'Unknown')
                    air_date = season.get('air_date', 'N/A')[:4]
                    
                    seasons_info.append(f"• Season {season_num}: {episode_count} episodes ({air_date})")
                
                return "\n".join(seasons_info) if seasons_info else ""
            else:
                self._log("No seasons data available", "INFO")
                return ""
                
        except Exception as e:
            self._log(f"Error fetching seasons info: {e}", "ERROR")
            return ""
    
    def _get_production_info(self, tmdb_id: int, content_type: str) -> str:
        """Get production details from TMDB."""
        self._log(f"Fetching production info for TMDB ID {tmdb_id} ({content_type})", "API")
        
        try:
            if content_type.lower() == "tv":
                details = self.tmdb_api.get_tv_show_details(tmdb_id)
            else:
                details = self.tmdb_api.get_movie_details(tmdb_id)
            
            if details:
                info_parts = []
                
                # Add creators/directors
                if content_type.lower() == "tv" and details.get('created_by'):
                    creators = [creator['name'] for creator in details['created_by'][:2]]
                    info_parts.append(f"Created by: {', '.join(creators)}")
                
                # Add production companies
                if details.get('production_companies'):
                    companies = [company['name'] for company in details['production_companies'][:2]]
                    info_parts.append(f"Production: {', '.join(companies)}")
                
                # Add network/runtime info
                if content_type.lower() == "tv":
                    if details.get('networks'):
                        network = details['networks'][0]['name']
                        info_parts.append(f"Network: {network}")
                    if details.get('episode_run_time'):
                        runtime = details['episode_run_time'][0]
                        info_parts.append(f"Episode Length: {runtime} minutes")
                
                self._log(f"Retrieved {len(info_parts)} production details", "SUCCESS")
                return "\n".join(info_parts) if info_parts else ""
            else:
                self._log("No production details available", "INFO")
                return ""
                
        except Exception as e:
            self._log(f"Error fetching production info: {e}", "ERROR")
            return ""


# Example usage and testing
if __name__ == "__main__":
    """Test the Context Agent with sample data."""
    
    # Sample TV show info (as would come from database)
    sample_tv_show = {
        'title': 'Breaking Bad',
        'show_type': 'tv',
        'season': 1,
        'episode': 1,
        'tmdb_id': None  # Will trigger search
    }
    
    # Initialize agent with verbose logging
    agent = ContextAgent(verbose=True)
    
    # Test different types of questions
    test_questions = [
        "Who plays Walter White?",
        "What shows are similar to this?", 
        "How many seasons are there?",
        "Who created this show?",
        "What happened in this scene?"
    ]
    
    print("🧪 Testing Context Agent with sample questions...\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*50}")
        print(f"TEST {i}: {question}")
        print('='*50)
        
        result = agent.analyze_and_enhance_context(question, sample_tv_show)
        
        if result:
            print(f"\n📋 Enhanced Context:")
            print(result)
        else:
            print(f"\n📋 No additional context provided")
        
        print(f"\n{'='*50}\n")
