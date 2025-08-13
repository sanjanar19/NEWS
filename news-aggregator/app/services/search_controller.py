"""
Main search controller that orchestrates the entire news analysis pipeline.
"""
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import collections

from app.services.tavily_client import TavilyClient
from app.services.gemini_client import GeminiClient
from app.services.content_processor import ContentProcessor
from app.services.analysis_engine import AnalysisEngine
from app.models.response_models import (
    SearchResponse, ArticleSource, ComponentInsight,
    SourceContribution, TimelinePoint, ChartData
)
from app.utils.logger import get_logger
from app.utils.exceptions import NewsAggregatorException, ContentProcessingError
from app.config import settings

logger = get_logger(__name__)


class SearchController:
    """Main controller for orchestrating news search and analysis pipeline."""
    
    def __init__(self):
        self.tavily_client = TavilyClient()
        self.gemini_client = GeminiClient()
        self.content_processor = ContentProcessor()
        self.analysis_engine = AnalysisEngine()
        # Note: Brave client will be added in Phase 3
    
    async def process_search_request(
        self,
        query: str,
        max_articles: int,
        time_range: str,
        include_sources: Optional[List[str]] = None,
        exclude_sources: Optional[List[str]] = None
    ) -> SearchResponse:
        """
        Process complete search request through the entire AI-powered pipeline.
        
        Args:
            query: Search query string
            max_articles: Maximum articles to process
            time_range: Time range for search
            include_sources: Sources to include
            exclude_sources: Sources to exclude
            
        Returns:
            Complete SearchResponse with AI analysis
        """
        
        start_time = time.time()
        
        logger.info(
            "Starting enhanced search pipeline with AI",
            query=query,
            max_articles=max_articles,
            time_range=time_range
        )
        
        try:
            # Phase 1: Data Collection
            raw_articles = await self._collect_articles(
                query=query,
                max_articles=max_articles,
                time_range=time_range,
                include_sources=include_sources,
                exclude_sources=exclude_sources
            )
            
            if not raw_articles:
                raise ContentProcessingError(
                    "No articles found for the given query and filters",
                    details={"query": query, "time_range": time_range}
                )
            
            # Phase 2: Enhanced Content Processing
            processed_articles = self._enhanced_content_processing(raw_articles)
            
            if not processed_articles:
                raise ContentProcessingError(
                    "No articles passed content quality filters",
                    details={"query": query, "raw_articles_count": len(raw_articles)}
                )
            
            # Phase 3: AI-Powered Analysis
            ai_analysis = await self._generate_ai_analysis(query, processed_articles)
            
            # Phase 4: Enhanced Analysis with Additional Processing
            enhanced_analysis = self.analysis_engine.enhance_ai_analysis(ai_analysis, processed_articles)
            
            # Phase 5: Generate Visualization Data
            chart_data = self._generate_enhanced_chart_data(processed_articles, enhanced_analysis)
            
            processing_time = (time.time() - start_time) * 1000
            
            # Construct comprehensive response
            response = SearchResponse(
                query=query,
                processing_time_ms=round(processing_time, 2),
                articles_processed=len(processed_articles),
                summary=enhanced_analysis["summary"],
                key_insights=enhanced_analysis["insights"],
                source_breakdown=chart_data["source_breakdown"],
                timeline=chart_data["timeline"],
                sources_used=processed_articles[:10],
                total_sources=len(set(article.source_domain for article in processed_articles)),
                date_range=self._calculate_date_range(processed_articles),
                analysis_confidence=enhanced_analysis["confidence_score"],
                coverage_score=enhanced_analysis.get("coverage_metrics", {}).get("source_diversity_score", 0.7)
            )
            
            logger.info(
                "Enhanced search pipeline completed successfully",
                query=query,
                processing_time_ms=round(processing_time, 2),
                articles_processed=len(processed_articles),
                insights_generated=len(enhanced_analysis["insights"]),
                ai_analysis_used=True
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Enhanced search pipeline failed",
                query=query,
                processing_time_ms=round((time.time() - start_time) * 1000, 2),
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def _collect_articles(
        self,
        query: str,
        max_articles: int,
        time_range: str,
        include_sources: Optional[List[str]],
        exclude_sources: Optional[List[str]]
    ) -> List[ArticleSource]:
        """Collect articles from all available sources."""
        
        logger.info("Collecting articles from sources", sources=["tavily"])
        
        try:
            # Primary source: Tavily
            tavily_articles = await self.tavily_client.search_news(
                query=query,
                max_results=settings.tavily_max_results,  # Use configured max results
                time_range=time_range,
                include_sources=include_sources,
                exclude_sources=exclude_sources
            )
            
            # Note: In Phase 4, we'll add Brave API as secondary source
            all_articles = tavily_articles
            
            # Remove duplicates (basic implementation)
            unique_articles = self._remove_duplicate_articles(all_articles)
            
            # Sort by publication date (newest first)
            unique_articles.sort(
                key=lambda x: x.published_at or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )
            
            # Limit to max_articles
            final_articles = unique_articles[:max_articles]
            
            logger.info(
                "Article collection completed",
                total_found=len(all_articles),
                after_deduplication=len(unique_articles),
                final_count=len(final_articles)
            )
            
            return final_articles
            
        except Exception as e:
            logger.error("Article collection failed", error=str(e))
            raise ContentProcessingError(f"Failed to collect articles: {str(e)}")
    
    def _remove_duplicate_articles(self, articles: List[ArticleSource]) -> List[ArticleSource]:
        """Remove duplicate articles based on URL and title similarity."""
        
        seen_urls = set()
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            # Check URL duplicates
            if article.url in seen_urls:
                continue
                
            # Check title similarity (basic implementation)
            title_lower = article.title.lower().strip()
            if title_lower in seen_titles:
                continue
            
            seen_urls.add(article.url)
            seen_titles.add(title_lower)
            unique_articles.append(article)
        
        return unique_articles
    
    def _process_articles(self, articles: List[ArticleSource]) -> List[ArticleSource]:
        """Basic article processing (will be enhanced in later phases)."""
        
        processed_articles = []
        
        for article in articles:
            # Basic content cleaning
            if article.title:
                # Clean title
                article.title = article.title.strip()
                
            if article.snippet:
                # Clean snippet
                article.snippet = article.snippet.strip()
                # Limit snippet length
                if len(article.snippet) > 300:
                    article.snippet = article.snippet[:297] + "..."
            
            processed_articles.append(article)
        
        return processed_articles
    
    def _enhanced_content_processing(self, raw_articles: List[ArticleSource]) -> List[ArticleSource]:
        """Enhanced content processing with AI-ready preparation."""
        
        logger.info("Starting enhanced content processing", article_count=len(raw_articles))
        
        # Step 1: Basic processing and cleaning
        processed_articles = self.content_processor.process_articles(raw_articles)
        
        # Step 2: Advanced deduplication
        unique_articles = self.content_processor.deduplicate_articles(processed_articles)
        
        # Step 3: Select best articles based on quality scores
        final_articles = unique_articles[:settings.max_articles_per_search]
        
        logger.info(
            "Enhanced content processing completed",
            original_count=len(raw_articles),
            after_processing=len(processed_articles),
            after_deduplication=len(unique_articles),
            final_count=len(final_articles)
        )
        
        return final_articles
    
    async def _generate_ai_analysis(
        self,
        query: str,
        articles: List[ArticleSource]
    ) -> Dict[str, Any]:
        """Generate AI-powered analysis using Gemini."""
        
        logger.info("Starting AI analysis", query=query, article_count=len(articles))
        
        try:
            # Use Gemini for comprehensive analysis
            ai_result = await self.gemini_client.analyze_news_content(query, articles)
            
            logger.info(
                "AI analysis completed successfully",
                insights_count=len(ai_result.get("insights", [])),
                confidence_score=ai_result.get("confidence_score", 0.0)
            )
            
            return ai_result
            
        except Exception as e:
            logger.warning(
                "AI analysis failed, falling back to basic analysis",
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Fallback to basic analysis if AI fails
            return await self._generate_basic_analysis(query, articles)
    
    async def _generate_basic_analysis(
        self,
        query: str,
        articles: List[ArticleSource]
    ) -> Dict[str, Any]:
        """Generate basic analysis (fallback when AI fails)."""
        
        # Enhanced basic summary
        summary = self._create_enhanced_basic_summary(query, articles)
        
        # Enhanced basic insights
        insights = self._extract_enhanced_basic_insights(articles)
        
        # Calculate enhanced confidence scores
        confidence = min(1.0, len(articles) / 15)  # Improved confidence calculation
        coverage_score = min(1.0, len(set(article.source_domain for article in articles)) / 8)
        
        return {
            "summary": summary,
            "insights": insights,
            "confidence_score": confidence,
            "coverage_assessment": "enhanced_basic",
            "conflicting_viewpoints": False,
            "source_analysis": {},
            "timeline_events": []
        }
    
    def _create_enhanced_basic_summary(self, query: str, articles: List[ArticleSource]) -> str:
        """Create an enhanced basic summary."""
        
        total_articles = len(articles)
        unique_sources = len(set(article.source_domain for article in articles))
        
        # Get top sources with counts
        source_counts = collections.Counter(article.source_name for article in articles if article.source_name)
        top_sources = source_counts.most_common(3)
        
        # Time analysis
        recent_articles = [a for a in articles if a.published_at and
                         (datetime.now(timezone.utc) - a.published_at).days == 0]
        
        # Quality sources analysis
        quality_sources = [a for a in articles if
                         hasattr(a, 'quality_score') and getattr(a, 'quality_score', 0) > 0.8]
        
        summary = f"""Analysis of {total_articles} articles regarding "{query}" from {unique_sources} sources reveals significant coverage across multiple news outlets.
        
Top sources include {top_sources[0][0]} ({top_sources[0][1]} articles)"""
        
        if len(top_sources) > 1:
            summary += f", {top_sources[1][0]} ({top_sources[1][1]} articles)"
        
        if len(top_sources) > 2:
            summary += f", and {top_sources[2][0]} ({top_sources[2][1]} articles)"
        
        summary += f"""

There are {len(recent_articles)} articles published within the last 24 hours, indicating a timely and ongoing discussion of the topic.
Additionally, {len(quality_sources)} articles were identified from high-quality sources."""
        
        return summary
    
    def _extract_enhanced_basic_insights(self, articles: List[ArticleSource]) -> List[ComponentInsight]:
        """Extract enhanced basic insights (fallback when AI fails)."""
        
        insights = []
        
        # Source diversity insight
        unique_sources = set(article.source_domain for article in articles)
        insights.append(ComponentInsight(
            point=f"Coverage from {len(unique_sources)} different news sources",
            frequency=len(unique_sources),
            confidence=0.9,
            sources=list(unique_sources)[:5],
            category="coverage"
        ))
        
        # Timeline insight
        recent_articles = [a for a in articles if a.published_at and
                         (datetime.now(timezone.utc) - a.published_at).days == 0]
        if recent_articles:
            insights.append(ComponentInsight(
                point=f"{len(recent_articles)} articles published within the last 24 hours",
                frequency=len(recent_articles),
                confidence=0.8,
                sources=[a.source_domain for a in recent_articles[:3]],
                category="timeline"
            ))
        
        # Source prominence insight
        source_counts = collections.Counter(article.source_domain for article in articles if article.source_domain)
        if source_counts:
            top_source = source_counts.most_common(1)[0]
            insights.append(ComponentInsight(
                point=f"Most coverage from {top_source[0]} with {top_source[1]} articles",
                frequency=top_source[1],
                confidence=0.7,
                sources=[top_source[0]],
                category="source_analysis"
            ))
        
        return insights
    
    def _generate_enhanced_chart_data(self, articles: List[ArticleSource], enhanced_analysis: Dict[str, Any]) -> Dict[str, ChartData]:
        """Generate enhanced data for visualization charts."""
        
        # Source breakdown chart
        source_counts = collections.Counter(article.source_name or article.source_domain for article in articles)
        total_articles = len(articles)
        source_chart_data = []
        
        for source, count in source_counts.most_common():
            contribution = (count / total_articles) * 100
            source_chart_data.append(SourceContribution(
                source=source,
                contribution=round(contribution, 1),
                articles_count=count,
                reliability_score=None
            ))
        
        # Timeline chart
        timeline_data = collections.defaultdict(int)
        for article in articles:
            if article.published_at:
                hour_key = article.published_at.replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
                timeline_data[hour_key] += 1
        
        timeline_chart_data = []
        for timestamp, count in sorted(timeline_data.items()):
            timeline_chart_data.append(TimelinePoint(
                timestamp=timestamp.isoformat(),
                article_count=count,
                key_events=None
            ))
        
        # Enhance with AI analysis timeline events if available
        if "timeline_events" in enhanced_analysis and enhanced_analysis["timeline_events"]:
            for event in enhanced_analysis["timeline_events"]:
                for point in timeline_chart_data:
                    # Simple matching, could be more robust
                    if point.timestamp.startswith(event["timestamp"]):
                        point.key_events = event["event_summary"]
        
        return {
            "source_breakdown": ChartData(
                chart_type="bar",
                data=[sc.dict() for sc in source_chart_data],  # <-- fix here
                metadata={"total_sources": len(source_counts)}
            ),
            "timeline": ChartData(
                chart_type="timeline",
                data=timeline_chart_data,
                metadata={"total_timepoints": len(timeline_chart_data)}
            )
        }
    
    def _calculate_date_range(self, articles: List[ArticleSource]) -> str:
        """Calculate the date range of processed articles."""
        
        dates = [article.published_at for article in articles if article.published_at]
        
        if not dates:
            return "Unknown date range"
        
        min_date = min(dates)
        max_date = max(dates)
        
        # Ensure dates are timezone-aware for comparison
        if min_date.tzinfo is None:
            min_date = min_date.replace(tzinfo=timezone.utc)
        if max_date.tzinfo is None:
            max_date = max_date.replace(tzinfo=timezone.utc)
        
        if min_date.date() == max_date.date():
            return min_date.strftime("%Y-%m-%d")
        else:
            return f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"