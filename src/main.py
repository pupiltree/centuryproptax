"""Main FastAPI application for Century Property Tax Intelligent Assistant.

This application provides a comprehensive WhatsApp-based intelligent assistant
for property tax services, including:
- Assessment booking and management
- Document processing and analysis
- Payment integration and tracking
- Report generation and delivery
- Real-time customer support

The system uses LangGraph supervisor pattern for intelligent message routing
and processing, with comprehensive API documentation available at /docs.
"""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv
import uvicorn
import structlog

# Import production middleware and optimization modules
from src.middleware.performance import setup_performance_middleware
from src.middleware.security import setup_security_middleware
from src.middleware.monitoring import setup_monitoring_middleware
from src.seo.optimization import setup_seo_routes

# Load environment variables
load_dotenv()

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# Configure structlog properly to work with standard logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

from src.core.logging import get_logger
logger = get_logger("main_app")

# Import webhook routers  
from src.api.integrated_webhooks import router as integrated_webhooks_router
from src.api.whatsapp_webhooks import router as whatsapp_webhooks_router

# Import payment system routers
try:
    from app.routes.mock_payment_routes import router as mock_payment_router
    from app.webhooks.razorpay_webhook import router as razorpay_webhook_router
    PAYMENT_ROUTES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Payment routes not available: {e}")
    PAYMENT_ROUTES_AVAILABLE = False

# Create FastAPI application with comprehensive OpenAPI configuration
app = FastAPI(
    title="Century Property Tax - Intelligent Assistant API",
    description="""Comprehensive API for Century Property Tax's intelligent WhatsApp assistant.

    ## Overview
    This API powers an intelligent property tax assistant that provides:
    - **WhatsApp Integration**: Native WhatsApp Business API support
    - **Assessment Management**: Complete property assessment workflow
    - **Document Processing**: Intelligent document analysis and verification
    - **Payment Integration**: Secure payment processing with Razorpay
    - **Report Generation**: Automated assessment report creation
    - **Real-time Support**: 24/7 intelligent customer assistance

    ## Architecture
    - **LangGraph Supervisor Pattern**: Intelligent message routing and processing
    - **Message Batching**: Optimized response generation for complex queries
    - **Redis State Management**: Persistent conversation and session storage
    - **PostgreSQL Database**: Comprehensive data persistence
    - **Circuit Breakers**: Resilient external service integration

    ## Authentication
    - WhatsApp webhook verification via VERIFY_TOKEN
    - Signature verification for webhook security
    - Admin endpoints require additional authorization

    ## Rate Limiting
    - Webhook endpoints: 1000 requests/minute
    - Search endpoints: 100 requests/minute
    - Management endpoints: 50 requests/minute

    ## Support
    - Documentation: [/documentation](/documentation)
    - Health Check: [/health](/health)
    - System Stats: [/stats](/stats)
    - Interactive API Docs: [/docs](/docs)
    """,
    version="4.0.0",
    contact={
        "name": "Century Property Tax Support",
        "url": "https://centuryproptax.com/support",
        "email": "support@centuryproptax.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://centuryproptax.com/license"
    },
    servers=[
        {
            "url": "https://api.centuryproptax.com",
            "description": "Production server"
        },
        {
            "url": "https://staging.centuryproptax.com",
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Production environment detection
is_production = os.getenv("ENVIRONMENT") == "production"

# Set up production middleware and optimizations
if is_production:
    # Security middleware (includes CORS configuration)
    setup_security_middleware(app)

    # Performance optimization middleware
    setup_performance_middleware(app)

    # Monitoring and metrics middleware
    setup_monitoring_middleware(app)

    # SEO optimization routes
    setup_seo_routes(app)

    logger.info("✅ Production middleware and optimizations enabled")
else:
    # Development CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

# Include webhook routers  
app.include_router(integrated_webhooks_router)  # Production: Integrated LangGraph agent with Redis persistence
app.include_router(whatsapp_webhooks_router)  # WhatsApp Business API integration

# Include payment system routers
if PAYMENT_ROUTES_AVAILABLE:
    app.include_router(mock_payment_router)  # Mock Razorpay payment system
    app.include_router(razorpay_webhook_router)  # Real Razorpay webhook handler
    logger.info("✅ Payment system routes loaded")
else:
    logger.warning("⚠️ Payment system routes not loaded")

# Include ticket management routes
try:
    from app.routes.ticket_routes import router as ticket_router
    app.include_router(ticket_router)
    logger.info("✅ Ticket management system loaded")
except ImportError as e:
    logger.warning(f"⚠️ Ticket management routes not loaded: {e}")

# Include report management routes
try:
    from src.api.report_management import router as report_router
    app.include_router(report_router)
    logger.info("✅ Report management system loaded")
except ImportError as e:
    logger.warning(f"⚠️ Report management routes not loaded: {e}")

# Mount static files for documentation portal
import os
if os.path.exists("docs/static"):
    app.mount("/documentation", StaticFiles(directory="docs/static", html=True), name="documentation")
    logger.info("✅ Documentation portal mounted at /documentation")
else:
    logger.warning("⚠️ Documentation portal not available - docs/static directory not found")

@app.on_event("startup")
async def startup_event():
    """Application startup."""
    logger.info("🚀 Starting Intelligent Business Assistant")
    logger.info(f"📱 WhatsApp Token: {'✅ Configured' if os.getenv('WA_ACCESS_TOKEN') else '❌ Missing'}")
    logger.info(f"📞 WhatsApp Phone: {os.getenv('WA_PHONE_NUMBER_ID')}")
    logger.info(f"🔐 VERIFY_TOKEN: {'✅ Configured' if os.getenv('WA_VERIFY_TOKEN') else '❌ Missing'}")
    
    # Initialize database tables (including ticket tables)
    try:
        from services.persistence.database import get_database_manager
        db_manager = await get_database_manager()
        await db_manager.create_tables()
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
    
    # Payment system status
    razorpay_configured = bool(os.getenv('RAZORPAY_KEY_ID') and os.getenv('RAZORPAY_KEY_SECRET'))
    logger.info(f"💳 Razorpay: {'✅ Configured' if razorpay_configured else '🧪 Mock Mode'}")
    
    if PAYMENT_ROUTES_AVAILABLE:
        base_url = os.getenv('BASE_URL', 'https://localhost:8000')
        if razorpay_configured:
            logger.info("🔒 Real Razorpay integration active with anti-fraud protection")
            logger.info(f"🌐 Base URL: {base_url}")
        else:
            logger.info("🧪 Mock Razorpay system active")
            logger.info(f"🔗 Mock payment URL: {base_url}")
            logger.info("💡 Update BASE_URL environment variable to change payment domain")


@app.get(
    "/",
    summary="API Information",
    description="""Root endpoint providing API overview and available endpoints.

    Returns comprehensive information about all available API endpoints,
    system status, and configuration details.
    """,
    responses={
        200: {
            "description": "API information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Century Property Tax - Intelligent Assistant API",
                        "version": "4.0.0",
                        "status": "running",
                        "endpoints": {
                            "webhook_verification": "GET /webhook",
                            "webhook_handler": "POST /webhook",
                            "health_check": "GET /health"
                        }
                    }
                }
            }
        }
    }
)
async def root():
    """API root endpoint with comprehensive system information."""
    endpoints = {
        "api_documentation": "GET /docs",
        "redoc_documentation": "GET /redoc",
        "documentation_portal": "GET /documentation",
        "openapi_schema": "GET /openapi.json",
        "webhook_verification": "GET /webhook",
        "webhook_handler": "POST /webhook",
        "health_check": "GET /health",
        "system_statistics": "GET /stats"
    }
    
    # Add payment endpoints if available
    if PAYMENT_ROUTES_AVAILABLE:
        endpoints.update({
            "mock_payment_page": "GET /mock-payment/{payment_link_id}",
            "complete_mock_payment": "POST /mock-payment/{payment_link_id}/complete",
            "payment_status": "GET /mock-payment/{payment_link_id}/status",
            "razorpay_webhook": "POST /webhook/razorpay/callback",
            "test_payment_system": "GET /mock-payment/test"
        })
    
    # Add ticket management endpoints
    endpoints.update({
        "ticket_dashboard": "GET /tickets/dashboard",
        "active_tickets": "GET /tickets/active",
        "ticket_messages": "GET /tickets/{ticket_id}/messages",
        "resolve_ticket": "POST /tickets/{ticket_id}/resolve",
        "ticket_websocket": "WS /tickets/ws/{session_id}"
    })
    
    razorpay_configured = bool(os.getenv('RAZORPAY_KEY_ID') and os.getenv('RAZORPAY_KEY_SECRET'))
    
    return {
        "message": "Century Property Tax - Intelligent Assistant API",
        "version": "4.0.0",
        "status": "running",
        "architecture": "LangGraph Supervisor Pattern",
        "features": [
            "WhatsApp Business API Integration",
            "Intelligent Message Processing",
            "Assessment Booking System",
            "Document Analysis",
            "Payment Processing",
            "Report Generation",
            "Real-time Health Monitoring"
        ],
        "documentation": {
            "interactive_docs": "/docs",
            "redoc": "/redoc",
            "documentation_portal": "/documentation",
            "openapi_schema": "/openapi.json"
        },
        "payment_system": {
            "mode": "production" if razorpay_configured else "mock",
            "anti_fraud": "enabled",
            "base_url": os.getenv('BASE_URL', 'https://localhost:8000'),
            "configurable": "Set BASE_URL environment variable to change"
        },
        "endpoints": endpoints
    }


@app.get("/test")
async def test_whatsapp_api():
    """Test WhatsApp API configuration."""
    from services.messaging.whatsapp_client import get_whatsapp_client

    client = get_whatsapp_client()
    return {
        "configured": client.is_configured(),
        "phone_number_id": client.phone_number_id,
        "business_account_id": client.business_account_id,
        "status": "WhatsApp Business API ready" if client.is_configured() else "WhatsApp not configured"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "path": request.url.path
        }
    )


if __name__ == "__main__":
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    logger.info("📋 Starting Century Property Tax AI Assistant...")
    logger.info("📍 Production Endpoints:")
    logger.info("   GET  /webhook - WhatsApp webhook verification")
    logger.info("   POST /webhook - WhatsApp message handler")
    logger.info("   GET  /health - Health check with statistics")
    logger.info("   GET  /stats - Detailed system statistics")
    logger.info("   GET  /test - Test WhatsApp API")
    logger.info("")
    logger.info("📍 WhatsApp Business API - Property Tax Focus")
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )