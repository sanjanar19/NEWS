"""
Google Gemini API client for AI-powered news analysis.
"""
import httpx
import json
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.utils.logger import get_logger, log_external_api_call
from app.utils.exceptions import GeminiAPIError
from app.models.response_models import ArticleSource, ComponentInsight

logger = get_logger(__name__)


class GeminiClient:
    """Client for Google Gemini AI API."""
    
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-2.0-flash"  # Update from gemini-pro to gemini-2.0-flash
        self.timeout = settings.request_timeout
        
    async def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make an authenticated request to Gemini API."""
        
        url = f"{self.base_url}/{endpoint}?key={self.api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        logger.info(**log_external_api_call("gemini", endpoint, payload_size=len(str(payload))))
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            raise GeminiAPIError(f"Request timeout after {self.timeout} seconds")
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(e))
            except:
                error_detail = e.response.text
                
            raise GeminiAPIError(
                f"HTTP {e.response.status_code}: {error_detail}",
                status_code=e.response.status_code
            )
        except Exception as e:
            raise GeminiAPIError(f"Unexpected error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(GeminiAPIError)
    )
    async def analyze_news_content(
        self, 
        query: str, 
        articles: List[ArticleSource]
    ) -> Dict[str, Any]:
        """
        Analyze news articles using Gemini AI.
        
        Args:
            query: Original search query
            articles: List of articles to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        
        if not articles:
            raise GeminiAPIError("No articles provided for analysis")
        
        # Prepare content for analysis
        article_content = self._prepare_article_content(articles)
        
        # Create analysis prompt
        prompt = self._create_analysis_prompt(query, article_content, articles)
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": settings.gemini_temperature,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": settings.gemini_max_tokens,
                "stopSequences": []
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
        
        try:
            response = await self._make_request(f"models/{self.model}:generateContent", payload)
            analysis_result = self._parse_analysis_response(response, articles)
            
            logger.info(
                "Gemini analysis completed",
                query=query,
                articles_analyzed=len(articles),
                insights_extracted=len(analysis_result.get("insights", []))
            )
            
            return analysis_result
            
        except Exception as e:
            logger.error(
                "Gemini analysis failed",
                query=query,
                articles_count=len(articles),
                error=str(e)
            )
            raise
    
    async def analyze_content(self, articles: List[Dict], query: str) -> Dict[str, Any]:
        """
        Comprehensive AI analysis:
        1. Extract key components
        2. Identify viewpoint differences
        3. Generate balanced summary
        4. Calculate confidence scores
        """
        prompt = self._construct_analysis_prompt(articles, query)
        
        try:
            response = await self._get_gemini_response(prompt)
            return self._structure_analysis(response, articles)
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            return self._create_fallback_analysis(articles)
    
    def _construct_analysis_prompt(self, articles: List[Dict], query: str) -> str:
        """Construct detailed prompt for analysis"""
        return f"""
        Analyze these news articles about '{query}' and provide:
        1. Key points with their frequency across sources
        2. Main viewpoints and any conflicts
        3. Timeline of events
        4. Source reliability assessment
        5. Confidence score for each insight
        
        Articles:
        {self._format_articles_for_prompt(articles)}
        """
    
    def _prepare_article_content(self, articles: List[ArticleSource]) -> str:
        """Prepare article content for AI analysis."""
        
        content_parts = []
        
        for i, article in enumerate(articles, 1):
            article_text = f"""
Article {i}:
Title: {article.title}
Source: {article.source_name} ({article.source_domain})
Published: {article.published_at.strftime('%Y-%m-%d %H:%M') if article.published_at else 'Unknown'}
URL: {article.url}
Content: {article.snippet if article.snippet else 'No content available'}
"""
            content_parts.append(article_text.strip())
        
        return "\n\n---\n\n".join(content_parts)
    
    def _create_analysis_prompt(self, query: str, article_content: str, articles: List[ArticleSource]) -> str:
        """Create comprehensive analysis prompt for Gemini."""
        
        source_domains = list(set(article.source_domain for article in articles))
        
        prompt = f"""You are an expert news analyst. Analyze the following {len(articles)} news articles about "{query}" and provide a comprehensive analysis.

ARTICLES TO ANALYZE:
{article_content}

ANALYSIS REQUIREMENTS:

1. COMPREHENSIVE SUMMARY (400-600 words):
   - Provide a detailed, coherent narrative of the current situation
   - Include key developments, trends, and implications
   - Maintain journalistic objectivity
   - Reference multiple sources naturally

2. COMPONENT ANALYSIS - Extract key insights as JSON array:
   For each significant point mentioned across articles, provide:
   {{
     "point": "Clear, specific insight or development",
     "frequency": number of articles mentioning this (1-{len(articles)}),
     "confidence": confidence score (0.0-1.0),
     "sources": ["domain1.com", "domain2.com"],
     "category": "politics|business|technology|health|other",
     "supporting_evidence": "Brief evidence from articles"
   }}

3. SOURCE CONTRIBUTION ANALYSIS:
   Analyze how much each source contributed to the overall understanding:
   - Which sources provided unique insights?
   - Which sources corroborated information?
   - Overall reliability assessment

4. KEY EVENTS TIMELINE:
   Identify chronological events mentioned in articles with timestamps when available.

IMPORTANT GUIDELINES:
- Focus on factual information, avoid speculation
- Identify conflicting viewpoints if they exist
- Prioritize insights mentioned by multiple sources
- Ensure frequency counts are accurate
- Use source domains: {', '.join(source_domains)}

Respond in this exact JSON format:
{{
  "summary": "Your comprehensive summary here",
  "insights": [
    {{
      "point": "insight text",
      "frequency": number,
      "confidence": 0.0-1.0,
      "sources": ["domain1", "domain2"],
      "category": "category",
      "supporting_evidence": "evidence text"
    }}
  ],
  "source_analysis": {{
    "unique_contributions": {{"source": "unique insight"}},
    "corroborations": ["commonly reported facts"],
    "reliability_notes": "assessment"
  }},
  "timeline_events": [
    {{
      "event": "event description",
      "timestamp": "ISO timestamp if available",
      "sources": ["source domains"]
    }}
  ],
  "analysis_metadata": {{
    "confidence_score": 0.0-1.0,
    "coverage_assessment": "comprehensive|partial|limited",
    "conflicting_viewpoints": true/false
  }}
}}"""
        
        return prompt
    
    def _parse_analysis_response(self, response: Dict[str, Any], articles: List[ArticleSource]) -> Dict[str, Any]:
        """Parse Gemini API response into structured analysis data."""
        
        try:
            # Extract generated content
            candidates = response.get("candidates", [])
            if not candidates:
                raise GeminiAPIError("No content generated by Gemini")
            
            content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            if not content:
                raise GeminiAPIError("Empty response from Gemini")
            
            # Try to parse JSON from response
            try:
                # Find JSON content (may be wrapped in markdown code blocks)
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start == -1 or json_end == 0:
                    raise ValueError("No JSON found in response")
                
                json_content = content[json_start:json_end]
                parsed_data = json.loads(json_content)
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning("Failed to parse JSON from Gemini response, using fallback", error=str(e))
                # Fallback to basic parsing
                return self._create_fallback_analysis(content, articles)
            
            # Validate and structure the response
            return self._structure_analysis_data(parsed_data, articles)
            
        except Exception as e:
            logger.error("Failed to parse Gemini response", error=str(e))
            # Return fallback analysis
            return self._create_fallback_analysis("Analysis parsing failed", articles)
    
    def _structure_analysis_data(self, parsed_data: Dict[str, Any], articles: List[ArticleSource]) -> Dict[str, Any]:
        """Structure parsed analysis data into standard format."""
        
        # Extract insights and convert to ComponentInsight objects
        insights = []
        raw_insights = parsed_data.get("insights", [])
        
        for insight_data in raw_insights:
            try:
                insight = ComponentInsight(
                    point=insight_data.get("point", ""),
                    frequency=max(1, min(insight_data.get("frequency", 1), len(articles))),
                    confidence=max(0.0, min(insight_data.get("confidence", 0.5), 1.0)),
                    sources=insight_data.get("sources", [])[:5],  # Limit to 5 sources
                    category=insight_data.get("category", "general")
                )
                insights.append(insight)
            except Exception as e:
                logger.warning("Failed to parse insight", insight_data=insight_data, error=str(e))
                continue
        
        # Extract metadata
        metadata = parsed_data.get("analysis_metadata", {})
        
        return {
            "summary": parsed_data.get("summary", "Summary not available"),
            "insights": insights,
            "source_analysis": parsed_data.get("source_analysis", {}),
            "timeline_events": parsed_data.get("timeline_events", []),
            "confidence_score": max(0.0, min(metadata.get("confidence_score", 0.7), 1.0)),
            "coverage_assessment": metadata.get("coverage_assessment", "partial"),
            "conflicting_viewpoints": metadata.get("conflicting_viewpoints", False)
        }
    
    def _create_fallback_analysis(self, content: str, articles: List[ArticleSource]) -> Dict[str, Any]:
        """Create fallback analysis when JSON parsing fails."""
        
        # Create basic insights
        basic_insights = [
            ComponentInsight(
                point=f"Analysis of {len(articles)} articles from multiple sources",
                frequency=len(articles),
                confidence=0.8,
                sources=list(set(article.source_domain for article in articles))[:3],
                category="general"
            )
        ]
        
        if len(set(article.source_domain for article in articles)) > 1:
            basic_insights.append(ComponentInsight(
                point=f"Coverage from {len(set(article.source_domain for article in articles))} different news sources",
                frequency=len(set(article.source_domain for article in articles)),
                confidence=0.9,
                sources=list(set(article.source_domain for article in articles)),
                category="coverage"
            ))
        
        summary = content[:500] + "..." if len(content) > 500 else content
        if not summary.strip():
            summary = f"Analysis of recent news articles covering the requested topic. {len(articles)} articles were processed "
        
        return {
            "summary": summary,
            "insights": basic_insights,
            "source_analysis": {},
            "timeline_events": [],
            "confidence_score": 0.5,
            "coverage_assessment": "partial",
            "conflicting_viewpoints": False
        }