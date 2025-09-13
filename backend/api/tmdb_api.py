import os
import requests
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv, find_dotenv


class TMDBAPI:
    """
    The Movie Database (TMDB) API client for searching TV shows and movies.
    """
    
    def __init__(self):
        # Load environment variables
        load_dotenv(find_dotenv())
        self.api_key = os.getenv("TMDB_API_KEY")
        
        if not self.api_key:
            raise ValueError("Error: TMDB_API_KEY environment variable not set.")
        
        self.base_url = "https://api.themoviedb.org/3"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        print("Initialized TMDB API client")
    
    def search_tv_show(self, query: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for TV shows by name.
        
        Args:
            query: The TV show name to search for
            year: Optional year to filter results
            
        Returns:
            List of TV show results from TMDB
        """
        try:
            url = f"{self.base_url}/search/tv"
            params = {
                "query": query,
                "include_adult": False,
                "language": "en-US",
                "page": 1
            }
            
            if year:
                params["first_air_date_year"] = year
            
            print(f"Searching TMDB for TV show: '{query}'")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            print(f"Found {len(results)} TV show results")
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching TV shows: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error during TV show search: {e}")
            return []
    
    def search_movie(self, query: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for movies by name.
        
        Args:
            query: The movie name to search for
            year: Optional year to filter results
            
        Returns:
            List of movie results from TMDB
        """
        try:
            url = f"{self.base_url}/search/movie"
            params = {
                "query": query,
                "include_adult": False,
                "language": "en-US",
                "page": 1
            }
            
            if year:
                params["year"] = year
            
            print(f"Searching TMDB for movie: '{query}'")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            print(f"Found {len(results)} movie results")
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching movies: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error during movie search: {e}")
            return []
    
    def get_tv_show_details(self, tv_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific TV show.
        
        Args:
            tv_id: The TMDB TV show ID
            
        Returns:
            Detailed TV show information
        """
        try:
            url = f"{self.base_url}/tv/{tv_id}"
            params = {
                "language": "en-US"
            }
            
            print(f"Getting TV show details for ID: {tv_id}")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting TV show details: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error getting TV show details: {e}")
            return None
    
    def get_tv_episode_details(self, tv_id: int, season_number: int, episode_number: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific TV episode.
        
        Args:
            tv_id: The TMDB TV show ID
            season_number: Season number
            episode_number: Episode number
            
        Returns:
            Detailed episode information
        """
        try:
            url = f"{self.base_url}/tv/{tv_id}/season/{season_number}/episode/{episode_number}"
            params = {
                "language": "en-US"
            }
            
            print(f"Getting episode details for TV ID: {tv_id}, S{season_number}E{episode_number}")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting episode details: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error getting episode details: {e}")
            return None
    
    def get_movie_details(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific movie.
        
        Args:
            movie_id: The TMDB movie ID
            
        Returns:
            Detailed movie information
        """
        try:
            url = f"{self.base_url}/movie/{movie_id}"
            params = {
                "language": "en-US"
            }
            
            print(f"Getting movie details for ID: {movie_id}")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting movie details: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error getting movie details: {e}")
            return None
    
    def search_and_get_best_match(self, title: str, content_type: str = "tv", year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Search for content and return the best match with detailed information.
        
        Args:
            title: The title to search for
            content_type: Either "tv" or "movie"
            year: Optional year to filter results
            
        Returns:
            Best match with detailed information, or None if no good match found
        """
        try:
            # Search for the content
            if content_type.lower() == "tv":
                search_results = self.search_tv_show(title, year)
            elif content_type.lower() == "movie":
                search_results = self.search_movie(title, year)
            else:
                print(f"Unknown content type: {content_type}")
                return None
            
            if not search_results:
                print(f"No {content_type} results found for '{title}'")
                return None
            
            # Get the first (best) match
            best_match = search_results[0]
            content_id = best_match.get("id")
            
            if not content_id:
                print("No valid ID found in search results")
                return None
            
            # Get detailed information
            if content_type.lower() == "tv":
                detailed_info = self.get_tv_show_details(content_id)
            else:
                detailed_info = self.get_movie_details(content_id)
            
            if detailed_info:
                # Add search metadata
                detailed_info["_search_metadata"] = {
                    "search_query": title,
                    "search_year": year,
                    "content_type": content_type,
                    "total_results": len(search_results)
                }
            
            return detailed_info
            
        except Exception as e:
            print(f"Error in search_and_get_best_match: {e}")
            return None


# Example usage and testing
if __name__ == "__main__":
    try:
        # Create TMDB API instance
        tmdb = TMDBAPI()
        
        # Test TV show search
        print("\n--- Testing TV Show Search ---")
        tv_results = tmdb.search_tv_show("Breaking Bad")
        if tv_results:
            print(f"Found TV show: {tv_results[0].get('name')} ({tv_results[0].get('first_air_date', 'N/A')[:4]})")
            
            # Get detailed info
            tv_details = tmdb.get_tv_show_details(tv_results[0]["id"])
            if tv_details:
                print(f"Seasons: {tv_details.get('number_of_seasons')}")
                print(f"Episodes: {tv_details.get('number_of_episodes')}")
                print(f"Overview: {tv_details.get('overview', 'N/A')[:100]}...")
        
        # Test movie search
        print("\n--- Testing Movie Search ---")
        movie_results = tmdb.search_movie("The Dark Knight")
        if movie_results:
            print(f"Found movie: {movie_results[0].get('title')} ({movie_results[0].get('release_date', 'N/A')[:4]})")
        
        # Test best match search
        print("\n--- Testing Best Match Search ---")
        best_match = tmdb.search_and_get_best_match("Friends", "tv")
        if best_match:
            print(f"Best match: {best_match.get('name')} - {best_match.get('number_of_seasons')} seasons")
    
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"Unexpected error: {e}")
