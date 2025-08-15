"""
Pydantic models for API response serialization.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class ArticleSource(BaseModel):
    """Model for article source information."""
    
    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")
    source_name: str = Field(..., description="Name of the news source")
    source_domain: str = Field(..., description="Domain of the news source")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    snippet: Optional[str] = Field(None, description="Article snippet/excerpt")


class ComponentInsight(BaseModel):
    """Represents a key insight with frequency analysis"""
    
    point: str = Field(..., description="Key insight or bullet point")
    frequency: int = Field(..., ge=1, description="Number of sources mentioning this point")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    sources: List[str] = Field(..., description="List of source domains mentioning this point")
    category: Optional[str] = Field(None, description="Category of the insight")


class SourceContribution(BaseModel):
    """Model for source contribution data."""
    
    source: str = Field(..., description="Source domain or name")
    contribution: float = Field(..., ge=0.0, le=100.0, description="Percentage contribution")
    articles_count: int = Field(..., ge=1, description="Number of articles from this source")
    reliability_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Source reliability score")


class TimelinePoint(BaseModel):
    """Model for timeline data points."""
    
    timestamp: datetime = Field(..., description="Timestamp of the data point")
    article_count: int = Field(..., ge=0, description="Number of articles at this timestamp")
    key_events: Optional[List[str]] = Field(None, description="Key events at this time")


class ChartData(BaseModel):
    """Base chart data structure"""
    
    chart_type: str = Field(..., description="Type of chart (bar, timeline, pie)")
    data: Dict[str, Any] = Field(..., description="Chart data points")
    metadata: Dict[str, Any] = Field(..., description="Additional chart metadata")


class TimelineEvent(BaseModel):
    """Single timeline event"""
    
    timestamp: datetime = Field(..., description="Timestamp of the event")
    title: str = Field(..., description="Title or description of the event")
    source: str = Field(..., description="Source of the event")
    relevance: float = Field(..., ge=0.0, le=1.0, description="Relevance score of the event")


class ArticleMetrics(BaseModel):
    """Article-level metrics and analysis"""
    
    source_reliability: float = Field(..., description="Reliability of the source")
    publish_time: datetime = Field(..., description="Publication time of the article")
    relevance_score: float = Field(..., description="Relevance score of the article")
    content_overlap: float = Field(..., description="Content overlap with other articles")


class VisualizationData(BaseModel):
    """Combined visualization data"""
    
    source_breakdown: Dict[str, float] = Field(..., description="Distribution of articles by source")
    timeline: List[TimelineEvent] = Field(..., description="Timeline of article publications")
    component_frequencies: Dict[str, int] = Field(..., description="Frequencies of components")
    reliability_scores: Dict[str, float] = Field(..., description="Reliability scores of sources")


class SearchResponse(BaseModel):
    """Enhanced search response with component analysis"""
    
    query: str = Field(..., description="Original search query")
    summary: str = Field(..., description="Comprehensive news summary")
    key_insights: List[str] = Field(..., description="Key insights")
    articles_processed: int = Field(..., ge=0, description="Total number of articles processed")
    processing_time_ms: float = Field(..., ge=0, description="Processing time in milliseconds")
    analysis_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall analysis confidence")
    coverage_score: float = Field(..., ge=0.0, le=1.0, description="Coverage score of the response")
    visualization_data: VisualizationData = Field(..., description="Data for generating visualizations")


class ErrorResponse(BaseModel):
    """Model for error responses."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class HealthCheckResponse(BaseModel):
    """Model for health check responses."""
    
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    version: str = Field(..., description="Application version")
    external_services: Optional[Dict[str, str]] = Field(None, description="External service status")
    uptime_seconds: Optional[float] = Field(None, description="Application uptime in seconds")