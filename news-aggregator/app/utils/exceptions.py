"""
Custom exception classes for the News Aggregator application.
"""
from typing import Optional, Any, Dict


class NewsAggregatorException(Exception):
    """Base exception for all application-specific errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ExternalAPIError(NewsAggregatorException):
    """Raised when external API calls fail."""
    
    def __init__(self, service: str, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        self.service = service
        self.status_code = status_code
        super().__init__(message, details)


class TavilyAPIError(ExternalAPIError):
    """Raised when Tavily API calls fail."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__("tavily", message, status_code, details)


class GeminiAPIError(ExternalAPIError):
    """Raised when Gemini API calls fail."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__("gemini", message, status_code, details)


# class BraveAPIError(ExternalAPIError):
#     """Raised when Brave API calls fail."""
    
#     def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
#         super().__init__("brave", message, status_code, details)


class ContentProcessingError(NewsAggregatorException):
    """Raised when content processing fails."""
    pass


class AnalysisError(NewsAggregatorException):
    """Raised when analysis operations fail."""
    pass


class ValidationError(NewsAggregatorException):
    """Raised when input validation fails."""
    pass