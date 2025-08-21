"""
FastAPI application entry point for News Aggregator.
"""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse # Import HTMLResponse
from datetime import datetime

from app.config import settings
from app.utils.logger import configure_logging, get_logger, log_api_request, log_api_response
from app.utils.exceptions import NewsAggregatorException, ExternalAPIError
from app.api.routes import router
from app.models.response_models import ErrorResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Application startup/shutdown context
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    
    # Startup
    logger.info("Starting News Aggregator API", version=settings.app_version)
    
    # Validate required API keys
    missing_keys = []
    if not settings.tavily_api_key:
        missing_keys.append("TAVILY_API_KEY")
    if not settings.gemini_api_key:
        missing_keys.append("GEMINI_API_KEY")
    
    if missing_keys:
        logger.error("Missing required API keys", missing_keys=missing_keys)
        raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")
    
    logger.info("All required API keys configured")
    
    yield
    
    # Shutdown
    logger.info("Shutting down News Aggregator API")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Real-time news aggregator with AI-powered analysis and component breakdown",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # IMPORTANT: Configure this more securely for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    """Add request timing and logging."""
    
    start_time = time.time()
    
    # Log incoming request
    logger.info(**log_api_request(
        method=request.method,
        path=request.url.path,
        query_params=dict(request.query_params),
        user_agent=request.headers.get("user-agent", "unknown")
    ))
    
    try:
        response = await call_next(request)
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Log response
        logger.info(**log_api_response(
            status_code=response.status_code,
            processing_time_ms=round(processing_time, 2),
            path=request.url.path
        ))
        
        # Add timing header
        response.headers["X-Process-Time"] = str(round(processing_time, 2))
        
        return response
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        
        logger.error(
            "Request processing failed",
            path=request.url.path,
            processing_time_ms=round(processing_time, 2),
            error=str(e),
            error_type=type(e).__name__
        )
        raise


# Exception handlers
@app.exception_handler(NewsAggregatorException)
async def news_aggregator_exception_handler(request: Request, exc: NewsAggregatorException):
    """Handle application-specific exceptions."""
    
    logger.error(
        "Application error",
        error_type=type(exc).__name__,
        message=exc.message,
        details=exc.details,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error=type(exc).__name__,
            message=exc.message,
            details=exc.details
        ).dict()
    )


@app.exception_handler(ExternalAPIError)
async def external_api_exception_handler(request: Request, exc: ExternalAPIError):
    """Handle external API errors."""
    
    logger.error(
        "External API error",
        service=exc.service,
        error_type=type(exc).__name__,
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path
    )
    
    # Determine appropriate HTTP status code
    if exc.status_code and 400 <= exc.status_code < 500:
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_502_BAD_GATEWAY
    
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=f"{exc.service.title()}APIError",
            message=f"External service error: {exc.message}",
            details={"service": exc.service, "status_code": exc.status_code}
        ).dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTPException",
            message=exc.detail,
            details={"status_code": exc.status_code}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    
    logger.error(
        "Unexpected error",
        error_type=type(exc).__name__,
        message=str(exc),
        path=request.url.path,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred. Please try again later.",
            details={"error_type": type(exc).__name__} if settings.debug else None
        ).dict()
    )


# Include API routes
app.include_router(router, prefix="/api/v1")


# Serve HTML at root
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint to serve the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.now().isoformat()
    }