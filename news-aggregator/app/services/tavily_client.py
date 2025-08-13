"""
Tavily API client for news search functionality.
"""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.utils.logger import get_logger, log_external_api_call
from app.utils.exceptions import TavilyAPIError
from app.models.response_models import ArticleSource

logger = get_logger(__name__)


class TavilyClient:
    """Client for Tavily Search API."""
    
    def __init__(self):
        self.api_key = settings.tavily_api_key
        self.base_url = "https://api.tavily.com"
        self.timeout = settings.request_timeout
        
    async def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make an authenticated request to Tavily API."""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        logger.info(**log_external_api_call("tavily", endpoint, payload_size=len(str(payload))))
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            raise TavilyAPIError(f"Request timeout after {self.timeout} seconds")
        except httpx.HTTPStatusError as e:
            raise TavilyAPIError(
                f"HTTP {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code
            )
        except Exception as e:
            raise TavilyAPIError(f"Unexpected error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(TavilyAPIError)
    )
    async def search_news(
        self, 
        query: str, 
        max_results: Optional[int] = None,
        time_range: str = "24h",
        include_sources: Optional[List[str]] = None,
        exclude_sources: Optional[List[str]] = None
    ) -> List[ArticleSource]:
        """
        Search for news articles using Tavily API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            time_range: Time range for articles (1h, 6h, 24h, 48h, 7d)
            include_sources: List of sources to include
            exclude_sources: List of sources to exclude
            
        Returns:
            List of ArticleSource objects
        """
        
        max_results = max_results or settings.tavily_max_results
        
        # Convert time_range to days for Tavily API
        time_mapping = {
            "1h": 0.04,   # ~1 hour
            "6h": 0.25,   # ~6 hours  
            "12h": 0.5,   # ~12 hours
            "24h": 1,     # 1 day
            "48h": 2,     # 2 days
            "7d": 7,      # 1 week
            "30d": 30     # 1 month
        }
        
        days = time_mapping.get(time_range, 1)
        
        # Build search payload
        payload = {
            "query": query,
            "search_depth": settings.tavily_search_depth,
            "include_answer": False,
            "include_images": False,
            "include_raw_content": True,
            "max_results": max_results,
            "days": days
        }
        
        # Add source filtering if specified
        if include_sources:
            payload["include_domains"] = include_sources
        if exclude_sources:
            payload["exclude_domains"] = exclude_sources
            
        try:
            response_data = await self._make_request("/search", payload)
            articles = self._parse_search_response(response_data)
            
            logger.info(
                "Tavily search completed",
                query=query,
                results_found=len(articles),
                max_requested=max_results
            )
            
            return articles
            
        except Exception as e:
            logger.error(
                "Tavily search failed",
                query=query,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    def _parse_search_response(self, response_data: Dict[str, Any]) -> List[ArticleSource]:
        """Parse Tavily API response into ArticleSource objects."""
        
        articles = []
        results = response_data.get("results", [])
        
        for result in results:
            try:
                # Extract publication date
                published_at = None
                if "published_date" in result:
                    try:
                        published_at = datetime.fromisoformat(result["published_date"].replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass
                
                # Extract domain from URL
                url = result.get("url", "")
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc.replace("www.", "")
                except:
                    domain = "unknown"
                
                article = ArticleSource(
                    title=result.get("title", "").strip(),
                    url=url,
                    source_name=result.get("source", domain),
                    source_domain=domain,
                    published_at=published_at,
                    snippet=result.get("content", "")[:500] if result.get("content") else None
                )
                
                articles.append(article)
                
            except Exception as e:
                logger.warning(
                    "Failed to parse article result",
                    result_url=result.get("url", "unknown"),
                    error=str(e)
                )
                continue
        
        return articles
    
    async def health_check(self) -> bool:
        """Check if Tavily API is accessible."""
        
        try:
            # Make a minimal search request to check connectivity
            payload = {
                "query": "test",
                "max_results": 1,
                "search_depth": "basic",
                "include_answer": False,
                "include_raw_content": False
            }
            
            await self._make_request("/search", payload)
            return True
            
        except Exception as e:
            logger.error("Tavily health check failed", error=str(e))
            return False