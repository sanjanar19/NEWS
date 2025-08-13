"""
API route definitions for the News Aggregator.
"""
import time
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import Dict, Any
from datetime import datetime

from app.models.request_models import SearchRequest, HealthCheckRequest
from app.models.response_models import SearchResponse, HealthCheckResponse, ErrorResponse
from app.services.search_controller import SearchController
from app.services.tavily_client import TavilyClient
from app.services.gemini_client import GeminiClient
from app.utils.logger import get_logger
from app.utils.exceptions import NewsAggregatorException, ExternalAPIError
from app.config import settings

logger = get_logger(__name__)
router = APIRouter()

# Initialize services (will be dependency-injected in production)
search_controller = SearchController()
tavily_client = TavilyClient()
gemini_client = GeminiClient()


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search and analyze news with AI",
    description="""
    Perform real-time news search with comprehensive AI-powered analysis.
    
    **Enhanced Features in Phase 2:**
    - AI-powered content analysis using Gemini
    - Advanced component analysis with frequency tracking
    - Enhanced content processing and quality scoring
    - Improved visualization data with quality metrics
    - Sentiment analysis and temporal insights
    """
)
async def search_news(request: SearchRequest) -> SearchResponse:
    """
    Main endpoint for AI-powered news search and analysis.
    
    This endpoint now includes:
    1. Searches for news articles using Tavily API
    2. Advanced content processing and quality filtering
    3. AI-powered analysis with Gemini for deep insights
    4. Component analysis with bullet points and frequency tracking
    5. Enhanced visualization data for charts with quality metrics
    6. Comprehensive response with confidence scoring
    """
    
    start_time = time.time()
    
    logger.info(
        "Starting AI-powered news search",
        query=request.query,
        max_articles=request.max_articles,
        time_range=request.time_range
    )
    
    try:
        # Execute the complete AI-powered search and analysis pipeline
        result = await search_controller.process_search_request(
            query=request.query,
            max_articles=request.max_articles,
            time_range=request.time_range,
            include_sources=request.include_sources,
            exclude_sources=request.exclude_sources
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(
            "AI-powered news search completed successfully",
            query=request.query,
            processing_time_ms=round(processing_time, 2),
            articles_processed=result.articles_processed,
            insights_found=len(result.key_insights),
            analysis_confidence=result.analysis_confidence
        )
        
        return result
        
    except NewsAggregatorException as e:
        processing_time = (time.time() - start_time) * 1000
        
        logger.error(
            "AI-powered news search failed with application error",
            query=request.query,
            processing_time_ms=round(processing_time, 2),
            error=e.message,
            error_type=type(e).__name__
        )
        raise
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        
        logger.error(
            "AI-powered news search failed with unexpected error",
            query=request.query,
            processing_time_ms=round(processing_time, 2),
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during AI-powered news search"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check with AI services",
    description="Comprehensive health check including AI services (Gemini) and search APIs"
)
async def detailed_health_check(
    include_external: bool = False
) -> HealthCheckResponse:
    """
    Detailed health check endpoint for monitoring all services.
    
    Args:
        include_external: Whether to check external API connectivity (Tavily, Gemini)
    """
    
    logger.info("Performing comprehensive health check", include_external=include_external)
    
    response_data = {
        "status": "healthy",
        "version": settings.app_version,
        "uptime_seconds": None  # Could implement uptime tracking if needed
    }
    
    if include_external:
        external_services = {}
        overall_healthy = True
        
        # Check Tavily API
        try:
            tavily_healthy = await tavily_client.health_check()
            external_services["tavily"] = "healthy" if tavily_healthy else "unhealthy"
            if not tavily_healthy:
                overall_healthy = False
        except Exception as e:
            logger.warning("Tavily health check failed", error=str(e))
            external_services["tavily"] = "unhealthy"
            overall_healthy = False
        
        # Check Gemini API
        try:
            gemini_healthy = await gemini_client.health_check()
            external_services["gemini"] = "healthy" if gemini_healthy else "unhealthy"
            if not gemini_healthy:
                overall_healthy = False
        except Exception as e:
            logger.warning("Gemini health check failed", error=str(e))
            external_services["gemini"] = "unhealthy"
            overall_healthy = False
        
        response_data["external_services"] = external_services
        
        # Update overall status based on critical services
        if not overall_healthy:
            # If either Tavily or Gemini is down, mark as degraded
            response_data["status"] = "degraded"
            logger.warning(
                "Health check shows degraded status",
                external_services=external_services
            )
    
    logger.info(
        "Health check completed",
        status=response_data["status"],
        external_checked=include_external
    )
    
    return HealthCheckResponse(**response_data)


@router.get(
    "/metrics",
    summary="Application metrics with AI insights",
    description="Get application metrics including AI processing statistics"
)
async def get_metrics() -> Dict[str, Any]:
    """
    Get application metrics including AI service status.
    Enhanced in Phase 2 with AI-related metrics.
    """
    
    return {
        "version": settings.app_version,
        "phase": "2 - AI Integration Complete",
        "features": {
            "ai_analysis": "enabled",
            "gemini_integration": "active",
            "enhanced_processing": "active",
            "quality_scoring": "enabled"
        },
        "uptime_seconds": None,  # Would implement proper uptime tracking
        "memory_usage": None,    # Could add memory monitoring
        "requests_total": None,  # Could add request counting
        "ai_services": {
            "gemini_model": settings.gemini_model,
            "content_processing": "enhanced"
        },
        "timestamp": datetime.now().isoformat()
    }