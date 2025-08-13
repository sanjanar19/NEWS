"""
Enhanced content processor for cleaning and preparing news articles.
"""
import re
import html
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.models.response_models import ArticleSource
from app.utils.logger import get_logger
from app.utils.exceptions import ContentProcessingError

logger = get_logger(__name__)


class ContentProcessor:
    """Enhanced processor for cleaning and preparing news content."""
    
    def __init__(self):
        # Patterns for content cleaning
        self.html_tag_pattern = re.compile(r'<[^>]+>')
        self.extra_whitespace_pattern = re.compile(r'\s+')
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        
        # Common noise patterns in articles
        self.noise_patterns = [
        r'\(AP\)',
        r'\(Reuters\)',
        r'\(Bloomberg\)',
        r'Read more:.*',  # Comma added here
        r'Click here.*',  # Comma added here
        r'Subscribe.*',   # Comma added here
        r'Advertisement\s*',
        r'ADVERTISEMENT\s*',
        r'Sign up.*',    # Comma added here
        r'Follow us.*'
    ]
        
        # Known reliable news domains for quality scoring
        self.reliable_domains = {
            'reuters.com': 0.95,
            'apnews.com': 0.95,
            'bbc.com': 0.9,
            'npr.org': 0.9,
            'washingtonpost.com': 0.85,
            'nytimes.com': 0.85,
            'wsj.com': 0.85,
            'cnn.com': 0.8,
            'abcnews.go.com': 0.8,
            'nbcnews.com': 0.8,
            'cbsnews.com': 0.8,
            'theguardian.com': 0.8,
            'usatoday.com': 0.75,
            'foxnews.com': 0.7,
            'bloomberg.com': 0.85,
            'economist.com': 0.85
        }
    
    def process_articles(self, articles: List[ArticleSource]) -> List[ArticleSource]:
        """
        Process and clean a list of articles.
        
        Args:
            articles: Raw articles from news APIs
            
        Returns:
            Cleaned and processed articles
        """
        
        logger.info("Starting article processing", article_count=len(articles))
        
        processed_articles = []
        
        for i, article in enumerate(articles):
            try:
                processed_article = self._process_single_article(article)
                if processed_article and self._is_article_valid(processed_article):
                    processed_articles.append(processed_article)
                else:
                    logger.warning(
                        "Article filtered out during processing",
                        article_url=article.url,
                        reason="validation_failed"
                    )
            except Exception as e:
                logger.warning(
                    "Failed to process article",
                    article_url=getattr(article, 'url', 'unknown'),
                    error=str(e),
                    article_index=i
                )
                continue
        
        # Sort by quality score and publication date
        processed_articles = self._sort_articles_by_quality(processed_articles)
        
        logger.info(
            "Article processing completed",
            original_count=len(articles),
            processed_count=len(processed_articles),
            filtered_out=len(articles) - len(processed_articles)
        )
        
        return processed_articles
    
    def _process_single_article(self, article: ArticleSource) -> Optional[ArticleSource]:
        """Process a single article."""
        
        # Clean title
        clean_title = self._clean_text(article.title) if article.title else ""
        
        # Clean snippet/content
        clean_snippet = self._clean_text(article.snippet) if article.snippet else ""
        
        # Normalize source information
        clean_source_name, source_domain = self._normalize_source_info(
            article.source_name, 
            article.source_domain, 
            article.url
        )
        
        # Normalize publication date
        normalized_date = self._normalize_date(article.published_at)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            clean_title, clean_snippet, source_domain, normalized_date
        )
        
        # Create processed article
        processed_article = ArticleSource(
            title=clean_title,
            url=article.url,
            source_name=clean_source_name,
            source_domain=source_domain,
            published_at=normalized_date,
            snippet=clean_snippet[:500] if clean_snippet else None  # Limit snippet length
        )
        
        # Store quality score (we'll add this to the model later if needed)
        processed_article.__dict__['quality_score'] = quality_score
        
        return processed_article
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove HTML tags
        text = self.html_tag_pattern.sub(' ', text)
        
        # Remove URLs
        text = self.url_pattern.sub(' ', text)
        
        # Remove noise patterns
        for pattern in self.noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Normalize whitespace
        text = self.extra_whitespace_pattern.sub(' ', text)
        
        # Clean up quotes and punctuation
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()
    
    def _normalize_source_info(
        self, 
        source_name: Optional[str], 
        source_domain: Optional[str], 
        url: str
    ) -> Tuple[str, str]:
        """Normalize source name and domain information."""
        
        try:
            parsed_url = urlparse(url)
            domain_from_url = parsed_url.netloc.lower()
            
            # Remove www. prefix
            domain_from_url = domain_from_url.replace('www.', '')
            
            # Use domain from URL if not provided or if it's more reliable
            final_domain = source_domain or domain_from_url
            final_domain = final_domain.replace('www.', '')
            
            # Normalize source name
            if not source_name or source_name.lower() in ['unknown', 'n/a']:
                # Try to derive source name from domain
                final_source_name = self._derive_source_name_from_domain(final_domain)
            else:
                final_source_name = source_name.strip()
            
            return final_source_name, final_domain
            
        except Exception as e:
            logger.warning("Failed to normalize source info", url=url, error=str(e))
            return source_name or "Unknown", source_domain or "unknown.com"
    
    def _derive_source_name_from_domain(self, domain: str) -> str:
        """Derive a readable source name from domain."""
        
        domain_to_name = {
            'reuters.com': 'Reuters',
            'apnews.com': 'Associated Press',
            'bbc.com': 'BBC News',
            'npr.org': 'NPR',
            'washingtonpost.com': 'The Washington Post',
            'nytimes.com': 'The New York Times',
            'wsj.com': 'The Wall Street Journal',
            'cnn.com': 'CNN',
            'abcnews.go.com': 'ABC News',
            'nbcnews.com': 'NBC News',
            'cbsnews.com': 'CBS News',
            'theguardian.com': 'The Guardian',
            'usatoday.com': 'USA Today',
            'foxnews.com': 'Fox News',
            'bloomberg.com': 'Bloomberg',
            'economist.com': 'The Economist'
        }
        
        if domain in domain_to_name:
            return domain_to_name[domain]
        
        # Generic conversion: remove .com/.org/.net and capitalize
        base_name = domain.split('.')[0]
        return base_name.replace('-', ' ').replace('_', ' ').title()
    
    def _normalize_date(self, published_at: Optional[datetime]) -> Optional[datetime]:
        """Normalize publication date."""
        
        if not published_at:
            return None
        
        try:
            # Ensure timezone awareness
            if published_at.tzinfo is None:
                # Assume UTC if no timezone info
                published_at = published_at.replace(tzinfo=timezone.utc)
            
            # Convert to UTC
            normalized_date = published_at.astimezone(timezone.utc)
            
            return normalized_date
            
        except Exception as e:
            logger.warning("Failed to normalize date", date=published_at, error=str(e))
            return published_at
    
    def _calculate_quality_score(
        self, 
        title: str, 
        snippet: str, 
        domain: str, 
        published_at: Optional[datetime]
    ) -> float:
        """Calculate a quality score for the article."""
        
        score = 0.0
        
        # Source reliability (40% of score)
        source_score = self.reliable_domains.get(domain, 0.5)
        score += source_score * 0.4
        
        # Title quality (25% of score)
        if title:
            title_score = min(1.0, len(title) / 100)  # Prefer titles around 100 chars
            # Bonus for titles without excessive punctuation
            if title.count('!') <= 1 and title.count('?') <= 1:
                title_score += 0.2
            score += min(1.0, title_score) * 0.25
        
        # Content quality (20% of score)
        if snippet:
            content_score = min(1.0, len(snippet) / 200)  # Prefer substantial snippets
            # Penalty for very short snippets
            if len(snippet) < 50:
                content_score *= 0.5
            score += content_score * 0.20
        
        # Recency (15% of score)
        if published_at:
            now = datetime.now(timezone.utc)
            hours_ago = (now - published_at).total_seconds() / 3600
            
            if hours_ago <= 24:
                recency_score = 1.0
            elif hours_ago <= 48:
                recency_score = 0.8
            elif hours_ago <= 168:  # 1 week
                recency_score = 0.6
            else:
                recency_score = 0.3
            
            score += recency_score * 0.15
        
        return min(1.0, max(0.0, score))
    
    def _is_article_valid(self, article: ArticleSource) -> bool:
        """Check if article meets minimum quality standards."""
        
        # Must have title
        if not article.title or len(article.title.strip()) < 10:
            return False
        
        # Must have valid URL
        if not article.url or not article.url.startswith(('http://', 'https://')):
            return False
        
        # Must have reasonable source information
        if not article.source_domain or article.source_domain == 'unknown.com':
            return False
        
        # Check quality score if available
        quality_score = getattr(article, 'quality_score', 0.5)
        if quality_score < 0.3:
            return False
        
        return True
    
    def _sort_articles_by_quality(self, articles: List[ArticleSource]) -> List[ArticleSource]:
        """Sort articles by quality score and recency."""
        
        def sort_key(article):
            quality_score = getattr(article, 'quality_score', 0.5)
            
            # Recency factor
            recency_factor = 0.0
            if article.published_at:
                now = datetime.now(timezone.utc)
                hours_ago = (now - article.published_at).total_seconds() / 3600
                recency_factor = max(0, 1.0 - hours_ago / 168)  # Decay over 1 week
            
            # Combined score: 70% quality, 30% recency
            combined_score = quality_score * 0.7 + recency_factor * 0.3
            return combined_score
        
        return sorted(articles, key=sort_key, reverse=True)
    
    def deduplicate_articles(self, articles: List[ArticleSource]) -> List[ArticleSource]:
        """Remove duplicate articles using advanced techniques."""
        
        logger.info("Starting article deduplication", article_count=len(articles))
        
        unique_articles = []
        seen_urls = set()
        seen_title_hashes = set()
        
        for article in articles:
            # Skip if URL already seen
            if article.url in seen_urls:
                continue
            
            # Create title hash for similarity detection
            title_hash = self._create_title_hash(article.title)
            
            # Skip if very similar title already seen
            if title_hash in seen_title_hashes:
                continue
            
            # Check for content similarity with existing articles
            if not self._is_content_similar_to_existing(article, unique_articles):
                unique_articles.append(article)
                seen_urls.add(article.url)
                seen_title_hashes.add(title_hash)
        
        logger.info(
            "Article deduplication completed",
            original_count=len(articles),
            unique_count=len(unique_articles),
            duplicates_removed=len(articles) - len(unique_articles)
        )
        
        return unique_articles
    
    def _create_title_hash(self, title: str) -> str:
        """Create a normalized hash of the title for duplicate detection."""
        
        if not title:
            return ""
        
        # Normalize title for comparison
        normalized = title.lower().strip()
        
        # Remove common prefixes/suffixes
        prefixes = ['breaking:', 'update:', 'exclusive:', 'live:']
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
        
        # Remove punctuation and extra spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _is_content_similar_to_existing(
        self, 
        new_article: ArticleSource, 
        existing_articles: List[ArticleSource]
    ) -> bool:
        """Check if new article is too similar to existing ones."""
        
        if not existing_articles:
            return False
        
        new_title_words = set(self._create_title_hash(new_article.title).split())
        
        for existing in existing_articles[-10:]:  # Check against last 10 articles only
            existing_title_words = set(self._create_title_hash(existing.title).split())
            
            # Calculate Jaccard similarity
            if len(new_title_words) == 0 and len(existing_title_words) == 0:
                continue
            
            intersection = len(new_title_words.intersection(existing_title_words))
            union = len(new_title_words.union(existing_title_words))
            
            if union > 0:
                similarity = intersection / union
                if similarity > 0.7:  # 70% similarity threshold
                    return True
        
        return False