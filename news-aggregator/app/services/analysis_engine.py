"""
Enhanced analysis engine for component analysis and insight processing.
"""
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re

from app.models.response_models import ArticleSource, ComponentInsight, TimelinePoint
from app.utils.logger import get_logger
from app.utils.exceptions import AnalysisError

logger = get_logger(__name__)


class AnalysisEngine:
    """Advanced analysis engine for news content processing."""
    
    def __init__(self):
        # Keywords that indicate important news categories
        self.category_keywords = {
            "politics": ["election", "government", "policy", "congress", "senate", "parliament", "vote", "political"],
            "business": ["economy", "market", "stock", "financial", "company", "business", "economic", "trade"],
            "technology": ["ai", "artificial intelligence", "tech", "software", "digital", "cyber", "innovation"],
            "health": ["health", "medical", "hospital", "disease", "treatment", "vaccine", "pandemic"],
            "environment": ["climate", "environment", "carbon", "emission", "sustainability", "green"],
            "sports": ["sport", "game", "team", "player", "championship", "league", "match"],
            "entertainment": ["movie", "music", "celebrity", "entertainment", "film", "show"]
        }
    
    def enhance_ai_analysis(
        self, 
        ai_analysis: Dict[str, Any], 
        articles: List[ArticleSource]
    ) -> Dict[str, Any]:
        """Enhance AI analysis with additional processing."""
        
        logger.info("Enhancing AI analysis with additional processing", 
                   articles_count=len(articles))
        
        try:
            # Enhance insights with additional analysis
            enhanced_insights = self._enhance_insights(ai_analysis.get("insights", []), articles)
            
            # Add sentiment analysis (basic implementation)
            sentiment_analysis = self._analyze_sentiment(articles)
            
            # Generate timeline insights
            timeline_insights = self._generate_timeline_insights(articles)
            
            # Analyze source credibility patterns
            credibility_analysis = self._analyze_source_credibility(articles)
            
            # Calculate coverage metrics
            coverage_metrics = self._calculate_coverage_metrics(articles, ai_analysis)
            
            enhanced_analysis = {
                **ai_analysis,
                "insights": enhanced_insights,
                "sentiment_analysis": sentiment_analysis,
                "timeline_insights": timeline_insights,
                "credibility_analysis": credibility_analysis,
                "coverage_metrics": coverage_metrics
            }
            
            logger.info("Analysis enhancement completed", 
                       original_insights=len(ai_analysis.get("insights", [])),
                       enhanced_insights=len(enhanced_insights))
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error("Failed to enhance AI analysis", error=str(e))
            # Return original analysis if enhancement fails
            return ai_analysis
    
    def _enhance_insights(
        self, 
        original_insights: List[ComponentInsight], 
        articles: List[ArticleSource]
    ) -> List[ComponentInsight]:
        """Enhance insights with additional analysis."""
        
        enhanced_insights = list(original_insights)
        
        # Add frequency-based insights
        frequency_insights = self._extract_frequency_insights(articles)
        enhanced_insights.extend(frequency_insights)
        
        # Add temporal insights
        temporal_insights = self._extract_temporal_insights(articles)
        enhanced_insights.extend(temporal_insights)
        
        # Add source diversity insights
        diversity_insights = self._extract_diversity_insights(articles)
        enhanced_insights.extend(diversity_insights)
        
        # Remove duplicates and sort by confidence
        unique_insights = self._deduplicate_insights(enhanced_insights)
        
        return sorted(unique_insights, key=lambda x: x.confidence, reverse=True)[:15]  # Limit to top 15
    
    def _extract_frequency_insights(self, articles: List[ArticleSource]) -> List[ComponentInsight]:
        """Extract insights based on word frequency analysis."""
        
        insights = []
        
        # Combine all titles and snippets
        all_text = " ".join([
            f"{article.title} {article.snippet or ''}" 
            for article in articles
        ]).lower()
        
        # Extract meaningful keywords (simple implementation)
        words = re.findall(r'\b[a-z]{4,}\b', all_text)  # Words with 4+ letters
        word_counts = Counter(words)
        
        # Filter out common words
        stop_words = {
            'news', 'said', 'says', 'also', 'after', 'that', 'this', 'with', 
            'from', 'they', 'their', 'have', 'been', 'were', 'will', 'would',
            'could', 'should', 'about', 'other', 'which', 'what', 'when'
        }
        
        significant_words = [
            (word, count) for word, count in word_counts.most_common(20)
            if word not in stop_words and count >= 2
        ]
        
        for word, count in significant_words[:5]:  # Top 5 frequent terms
            if count >= 3:  # Only if mentioned in multiple articles
                sources = []
                for article in articles:
                    article_text = f"{article.title} {article.snippet or ''}".lower()
                    if word in article_text:
                        sources.append(article.source_domain)
                
                unique_sources = list(set(sources))[:3]
                
                insights.append(ComponentInsight(
                    point=f"Frequent mention of '{word}' across multiple sources",
                    frequency=count,
                    confidence=min(0.8, count / len(articles)),
                    sources=unique_sources,
                    category="keyword_analysis"
                ))
        
        return insights
    
    def _extract_temporal_insights(self, articles: List[ArticleSource]) -> List[ComponentInsight]:
        """Extract insights based on temporal patterns."""
        
        insights = []
        
        # Articles with timestamps
        dated_articles = [a for a in articles if a.published_at]
        
        if not dated_articles:
            return insights
        
        now = datetime.now()
        
        # Recent articles (last 6 hours)
        recent_articles = [
            a for a in dated_articles 
            if (now - a.published_at.replace(tzinfo=None)).total_seconds() < 6 * 3600
        ]
        
        if recent_articles:
            insights.append(ComponentInsight(
                point=f"Breaking: {len(recent_articles)} articles published in last 6 hours",
                frequency=len(recent_articles),
                confidence=0.9,
                sources=[a.source_domain for a in recent_articles[:3]],
                category="breaking_news"
            ))
        
        # Publication pattern analysis
        hourly_counts = defaultdict(int)
        for article in dated_articles:
            hour = article.published_at.hour
            hourly_counts[hour] += 1
        
        if hourly_counts:
            peak_hour = max(hourly_counts.items(), key=lambda x: x[1])
            if peak_hour[1] >= 3:
                insights.append(ComponentInsight(
                    point=f"Peak coverage during {peak_hour[0]:02d}:00 hour",
                    frequency=peak_hour[1],
                    confidence=0.7,
                    sources=[a.source_domain for a in dated_articles if a.published_at.hour == peak_hour[0]][:3],
                    category="temporal_pattern"
                ))
        
        return insights
    
    def _extract_diversity_insights(self, articles: List[ArticleSource]) -> List[ComponentInsight]:
        """Extract insights based on source diversity."""
        
        insights = []
        
        # Source domain analysis
        domain_counts = Counter(article.source_domain for article in articles)
        unique_domains = len(domain_counts)
        
        if unique_domains >= 5:
            insights.append(ComponentInsight(
                point=f"Comprehensive coverage from {unique_domains} different news sources",
                frequency=unique_domains,
                confidence=0.85,
                sources=list(domain_counts.keys())[:5],
                category="source_diversity"
            ))
        
        # Geographic diversity (basic implementation)
        international_indicators = ['reuters.com', 'bbc.com', 'aljazeera.com', 'dw.com', 'france24.com']
        international_sources = [
            article for article in articles 
            if any(indicator in article.source_domain for indicator in international_indicators)
        ]
        
        if international_sources:
            insights.append(ComponentInsight(
                point=f"International perspective from {len(international_sources)} global sources",
                frequency=len(international_sources),
                confidence=0.8,
                sources=[a.source_domain for a in international_sources[:3]],
                category="international_coverage"
            ))
        
        return insights
    
    def _analyze_sentiment(self, articles: List[ArticleSource]) -> Dict[str, Any]:
        """Basic sentiment analysis of articles."""
        
        # Simple keyword-based sentiment analysis
        positive_keywords = ['success', 'growth', 'improvement', 'progress', 'positive', 'good', 'better']
        negative_keywords = ['crisis', 'problem', 'decline', 'negative', 'bad', 'worse', 'concern', 'threat']
        
        positive_count = 0
        negative_count = 0
        
        for article in articles:
            text = f"{article.title} {article.snippet or ''}".lower()
            
            for keyword in positive_keywords:
                positive_count += text.count(keyword)
            
            for keyword in negative_keywords:
                negative_count += text.count(keyword)
        
        total_sentiment_indicators = positive_count + negative_count
        
        if total_sentiment_indicators > 0:
            sentiment_score = (positive_count - negative_count) / total_sentiment_indicators
        else:
            sentiment_score = 0.0
        
        return {
            "overall_sentiment": "positive" if sentiment_score > 0.1 else "negative" if sentiment_score < -0.1 else "neutral",
            "sentiment_score": sentiment_score,
            "positive_indicators": positive_count,
            "negative_indicators": negative_count,
            "confidence": min(1.0, total_sentiment_indicators / len(articles))
        }
    
    def _generate_timeline_insights(self, articles: List[ArticleSource]) -> List[TimelinePoint]:
        """Generate timeline insights from articles."""
        
        timeline_points = []
        
        # Group articles by publication time (hourly buckets)
        dated_articles = [a for a in articles if a.published_at]
        
        if not dated_articles:
            return timeline_points
        
        hourly_groups = defaultdict(list)
        for article in dated_articles:
            # Round to nearest hour
            hour_bucket = article.published_at.replace(minute=0, second=0, microsecond=0)
            hourly_groups[hour_bucket].append(article)
        
        # Create timeline points
        for timestamp, articles_in_hour in sorted(hourly_groups.items()):
            # Extract key events (simplified)
            key_events = []
            if len(articles_in_hour) >= 3:
                key_events.append(f"High coverage period - {len(articles_in_hour)} articles")
            
            timeline_points.append(TimelinePoint(
                timestamp=timestamp,
                article_count=len(articles_in_hour),
                key_events=key_events if key_events else None
            ))
        
        return timeline_points
    
    def _analyze_source_credibility(self, articles: List[ArticleSource]) -> Dict[str, Any]:
        """Analyze source credibility patterns."""
        
        # Simple credibility scoring based on known reliable sources
        high_credibility_domains = [
            'reuters.com', 'apnews.com', 'bbc.com', 'npr.org', 
            'washingtonpost.com', 'nytimes.com', 'wsj.com'
        ]
        
        credibility_scores = {}
        
        for article in articles:
            domain = article.source_domain
            if domain in high_credibility_domains:
                credibility_scores[domain] = 0.9
            elif domain.endswith('.gov') or domain.endswith('.edu'):
                credibility_scores[domain] = 0.85
            else:
                # Default score for unknown sources
                credibility_scores[domain] = 0.7
        
        avg_credibility = sum(credibility_scores.values()) / len(credibility_scores) if credibility_scores else 0.7
        
        return {
            "average_credibility": avg_credibility,
            "high_credibility_sources": len([d for d in credibility_scores.keys() if d in high_credibility_domains]),
            "source_scores": credibility_scores,
            "reliability_assessment": "high" if avg_credibility > 0.8 else "medium" if avg_credibility > 0.6 else "low"
        }
    
    def _calculate_coverage_metrics(self, articles: List[ArticleSource], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate coverage quality metrics."""
        
        unique_sources = len(set(article.source_domain for article in articles))
        
        # Time span coverage
        dated_articles = [a for a in articles if a.published_at]
        if dated_articles:
            time_span = (max(a.published_at for a in dated_articles) - 
                        min(a.published_at for a in dated_articles)).total_seconds() / 3600  # hours
        else:
            time_span = 0
        
        # Content diversity (based on unique titles)
        unique_titles = len(set(article.title for article in articles))
        content_diversity = unique_titles / len(articles) if articles else 0
        
        return {
            "source_diversity_score": min(1.0, unique_sources / 10),  # Normalize to 10 sources
            "temporal_coverage_hours": time_span,
            "content_diversity_score": content_diversity,
            "total_insights": len(ai_analysis.get("insights", [])),
            "coverage_quality": "excellent" if unique_sources >= 8 else "good" if unique_sources >= 5 else "fair"
        }
    
    def _deduplicate_insights(self, insights: List[ComponentInsight]) -> List[ComponentInsight]:
        """Remove duplicate insights based on similarity."""
        
        unique_insights = []
        seen_points = set()
        
        for insight in insights:
            # Simple deduplication based on point text
            point_key = insight.point.lower().strip()
            
            # Check for similar existing insights
            is_duplicate = False
            for seen_point in seen_points:
                # Simple similarity check (can be enhanced with more sophisticated methods)
                if self._points_are_similar(point_key, seen_point):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_insights.append(insight)
                seen_points.add(point_key)
        
        return unique_insights
    
    def _points_are_similar(self, point1: str, point2: str) -> bool:
        """Check if two insight points are similar."""
        
        # Simple similarity check
        words1 = set(point1.split())
        words2 = set(point2.split())
        
        # If they share more than 60% of words, consider them similar
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union
        return similarity > 0.6