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
    """Model for component analysis insights."""
    
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
    """Model for chart visualization data."""
    
    chart_type: str = Field(..., description="Type of chart (bar, timeline, pie)")
    data: List[Dict[str, Any]] = Field(..., description="Chart data points")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional chart metadata")


class SearchResponse(BaseModel):
    """Model for complete search analysis response."""
    
    query: str = Field(..., description="Original search query")
    processing_time_ms: float = Field(..., ge=0, description="Processing time in milliseconds")
    articles_processed: int = Field(..., ge=0, description="Total number of articles processed")
    
    # Main Analysis Results
    summary: str = Field(..., description="Comprehensive news summary")
    key_insights: List[ComponentInsight] = Field(..., description="Key insights with frequency analysis")
    
    # Visualization Data
    source_breakdown: ChartData = Field(..., description="Source contribution chart data")
    timeline: ChartData = Field(..., description="Timeline chart data")
    
    # Additional Data
    sources_used: List[ArticleSource] = Field(..., description="List of articles processed")
    total_sources: int = Field(..., ge=0, description="Total number of unique sources")
    date_range: str = Field(..., description="Date range of processed articles")
    
    # Quality Metrics
    analysis_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall analysis confidence")
    coverage_score: float = Field(..., ge=0.0, le=1.0, description="Topic coverage score")


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