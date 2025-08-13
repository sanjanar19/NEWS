"""
Configuration management for the News Aggregator application.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    tavily_api_key: str = Field(..., env="TAVILY_API_KEY")
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    brave_api_key: Optional[str] = Field(None, env="BRAVE_API_KEY")
    
    # Application Settings
    app_name: str = "News Aggregator API"
    app_version: str = "1.0.0"
    debug: bool = Field(False, env="DEBUG")
    
    # API Limits
    max_articles_per_search: int = Field(20, env="MAX_ARTICLES_PER_SEARCH")
    request_timeout: int = Field(30, env="REQUEST_TIMEOUT")
    max_retries: int = Field(3, env="MAX_RETRIES")
    
    # Tavily Settings
    tavily_max_results: int = Field(15, env="TAVILY_MAX_RESULTS")
    tavily_search_depth: str = Field("basic", env="TAVILY_SEARCH_DEPTH")  # basic or advanced
    
    # Gemini Settings
    gemini_model: str = Field("gemini-pro", env="GEMINI_MODEL")
    gemini_temperature: float = Field(0.3, env="GEMINI_TEMPERATURE")
    gemini_max_tokens: int = Field(2048, env="GEMINI_MAX_TOKENS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()