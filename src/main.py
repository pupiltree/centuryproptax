"""Main FastAPI application for Generic Business Assistant."""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import uvicorn
import structlog

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

# Create FastAPI application  
app = FastAPI(
    title="Intelligent Business Assistant",
    description="Generic AI-powered business assistant with multi-channel communication",
    version="1.0.0"
)

# Add CORS middleware
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


@app.get("/")
async def root():
    """Root endpoint."""
    endpoints = {
        "webhook_verification": "GET /webhook",
        "webhook_handler": "POST /webhook", 
        "health_check": "GET /health"
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
        "message": "Intelligent Business Assistant",
        "version": "1.0.0",
        "status": "running",
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