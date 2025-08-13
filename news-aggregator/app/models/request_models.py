"""
Pydantic models for API request validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import re


class SearchRequest(BaseModel):
    """Model for news search requests."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Search query for news articles"
    )

    max_articles: Optional[int] = Field(
        20,
        ge=5,
        le=50,
        description="Maximum number of articles to process (5-50)"
    )

    include_sources: Optional[List[str]] = Field(
        None,
        description="Optional list of specific news sources to include"
    )

    exclude_sources: Optional[List[str]] = Field(
        None,
        description="Optional list of news sources to exclude"
    )

    time_range: Optional[str] = Field(
        "24h",
        description="Time range for articles: 1h, 6h, 24h, 48h, 7d"
    )

    # Use @field_validator instead of @validator
    @field_validator('query', mode='before')
    @classmethod
    def validate_query(cls, v: str):
        """Validate and clean the search query."""
        # Remove excessive whitespace
        v = re.sub(r'\s+', ' ', v.strip())

        # Check for minimum meaningful content
        if len(v.replace(' ', '')) < 2:
            raise ValueError('Query must contain at least 2 non-space characters')

        return v

    @field_validator('time_range')
    @classmethod
    def validate_time_range(cls, v: str):
        """Validate time range format."""
        valid_ranges = ['1h', '6h', '12h', '24h', '48h', '7d', '30d']
        if v not in valid_ranges:
            raise ValueError(f'Time range must be one of: {", ".join(valid_ranges)}')
        return v

    @field_validator('include_sources', 'exclude_sources', mode='before')
    @classmethod
    def validate_sources(cls, v: Optional[List[str]]):
        """Validate source lists."""
        if v is not None:
            # Remove duplicates and empty strings
            v = [source.strip().lower() for source in v if source.strip()]
            v = list(set(v))  # Remove duplicates
        return v

class HealthCheckRequest(BaseModel):
    """Model for health check requests (if needed)."""
    
    include_external_services: Optional[bool] = Field(
        False,
        description="Whether to check external API connectivity"
    )