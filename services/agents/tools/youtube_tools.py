"""
YouTube search tool for finding relevant videos
"""
import logging
import json
from typing import Dict, Any, Optional
from langchain_core.pydantic_v1 import BaseModel as LangchainBaseModel, Field
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.messages import ToolMessage
import requests
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class YouTubeSearchArgs(LangchainBaseModel):
    """Arguments for searching YouTube for relevant videos."""
    query: str = Field(..., description="The search query to find relevant YouTube videos")
    topic: str = Field(..., description="The topic category (must be 'youtube')")
    max_results: int = Field(3, description="Maximum number of results to return (default: 3)")

class YouTubeVideo:
    """Represents a YouTube video result."""
    def __init__(self, title: str, url: str, channel: str = None, description: str = None):
        self.title = title
        self.url = url
        self.channel = channel
        self.description = description

    def to_markdown(self) -> str:
        """Convert the video to a markdown representation."""
        result = f"- [{self.title}]({self.url})"
        if self.channel:
            result += f" by {self.channel}"
        if self.description:
            # Truncate description if it's too long
            desc = self.description[:100] + "..." if len(self.description) > 100 else self.description
            result += f"\n  {desc}"
        return result

def search_youtube_with_google(query: str, max_results: int = 3) -> list[YouTubeVideo]:
    """
    Search for YouTube videos using Google Search API.
    Requires proper API configuration.
    """
    try:
        # Add "youtube" to the query to focus on YouTube results
        search_query = f"{query} youtube"
        
        # Initialize Google Search API
        search = GoogleSearchAPIWrapper()
        
        # Add site restriction to only get YouTube results
        results = search.results(search_query, max_results * 2)  # Get more results to filter
        
        videos = []
        for result in results:
            # Filter for YouTube URLs
            if "youtube.com/watch" in result["link"]:
                video = YouTubeVideo(
                    title=result["title"],
                    url=result["link"],
                    description=result.get("snippet", "")
                )
                videos.append(video)
                
                if len(videos) >= max_results:
                    break
        
        return videos
    
    except Exception as e:
        logger.error(f"Error searching YouTube with Google API: {e}", exc_info=True)
        return []

def search_youtube_direct(query: str, max_results: int = 3) -> list[YouTubeVideo]:
    """
    Search for YouTube videos using a direct URL approach.
    This is a fallback method if API access is not available.
    """
    try:
        # Create a YouTube search URL
        encoded_query = quote_plus(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        videos = []
        
        # Since we can't scrape without browser automation, return a direct search link
        # This is a simple fallback that at least provides the user with a working search URL
        video = YouTubeVideo(
            title=f"YouTube Search Results for: {query}",
            url=search_url,
            description="Click this link to see the search results directly on YouTube"
        )
        videos.append(video)
        
        return videos
        
    except Exception as e:
        logger.error(f"Error creating YouTube search link: {e}", exc_info=True)
        return []

def execute_youtube_tool(tool_call: Dict[str, Any], state: Dict[str, Any]) -> str:
    """
    Execute the YouTube search tool and return formatted results.
    """
    logger.info("--- Running YouTube Search Tool ---")
    
    try:
        # Parse the tool arguments
        tool_args = tool_call['args']
        
        # Validate that the topic is 'youtube'
        if tool_args.get('topic', '').lower() != 'youtube':
            return "YouTube search tool can only be used when topic is 'youtube'."
            
        query = tool_args.get('query', '')
        if not query:
            return "Error: Search query is required for YouTube search."
            
        max_results = int(tool_args.get('max_results', 3))
        
        logger.info(f"Searching YouTube for: '{query}', max_results: {max_results}")
        
        # Try Google Search API first (if configured)
        try:
            videos = search_youtube_with_google(query, max_results)
        except Exception as e:
            logger.warning(f"Google Search API failed: {e}, falling back to direct search")
            videos = []
        
        # If no results or API failed, use direct search
        if not videos:
            videos = search_youtube_direct(query, max_results)
        
        if not videos:
            return "Sorry, I couldn't find any YouTube videos matching your query."
        
        # Format the results in Markdown
        result = f"## YouTube Videos for '{query}':\n\n"
        for video in videos:
            result += video.to_markdown() + "\n\n"
            
        result += f"I found these videos that might help with your query about '{query}'. Click on the links to watch them on YouTube."
        
        logger.info(f"YouTube Search Result found {len(videos)} videos")
        return result
        
    except Exception as e:
        logger.error(f"Error executing YouTube search: {e}", exc_info=True)
        return f"Error executing YouTube search: {str(e)}"