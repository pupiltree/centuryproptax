"""
Generic Business Webhook Endpoints
Supports any service-based business with the following workflows:
- Service enquiries and information
- Service booking and order management  
- Payment processing (online/cash)
- Report/document retrieval
- Complaint handling and ticketing
- Human agent escalation
"""

import os
import logging
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import PlainTextResponse

from services.communication.message_handler import message_handler

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/webhook")
async def verify_business_webhook(request: Request):
    """
    Webhook verification endpoint for business communications.
    Supports Instagram, WhatsApp, and other messaging platforms.
    """
    verify_token = os.getenv("VERIFY_TOKEN", "")
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token") 
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == verify_token:
        logger.info("✅ Business webhook verified successfully")
        return PlainTextResponse(content=challenge)
    
    logger.warning(f"❌ Business webhook verification failed - mode: {mode}, token_match: {token == verify_token}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def handle_business_webhook(request: Request):
    """
    Business webhook handler endpoint.
    Processes messages and handles all business workflows:
    - Service enquiries → Information and pricing
    - Service booking → Order creation and payment
    - Report requests → Document retrieval
    - Complaints → Ticket creation
    - Complex cases → Human escalation
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Get signature header
        signature = request.headers.get("X-Hub-Signature-256", "")
        
        # Verify signature (uncomment for production)
        # if not universal_message_handler.verify_webhook_signature(body, signature):
        #     logger.warning("Invalid webhook signature")
        #     raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Parse JSON
        data = await request.json()
        
        # Log webhook data
        logger.info(f"📨 Business webhook received: {data.get('object', 'unknown')}")
        
        # Handle through universal message system
        result = await message_handler.handle_incoming_message(data)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error handling business webhook: {e}", exc_info=True)
        # Return 200 to prevent platform retries
        return {"status": "error", "message": str(e)}


@router.get("/health")
async def business_health_check():
    """Comprehensive health check for business systems."""
    from datetime import datetime
    
    start_time = datetime.now()
    health_status = {
        "status": "healthy",
        "service": "intelligent-business-assistant",
        "version": "1.0.0",
        "architecture": "langgraph-generic-business",
        "timestamp": start_time.isoformat(),
        "components": {},
        "checks": {},
        "workflows": [
            "service_enquiry_and_information",
            "service_booking_and_orders",
            "payment_processing_online_and_cash",
            "report_and_document_retrieval", 
            "complaint_handling_and_ticketing",
            "human_agent_escalation"
        ]
    }
    
    # Component status from universal handler
    stats = message_handler.get_handler_statistics()
    health_status["components"] = {
        "message_handler": "operational",
        "healthcare_assistant": "operational",
        "message_batcher": "operational",
        "active_sessions": stats["active_sessions"],
        "active_batches": stats["message_batcher_stats"]["active_batches"]
    }
    
    # Database health check
    try:
        from services.persistence.database import get_database_manager
        db_manager = await get_database_manager()
        
        # Test database connectivity
        db_check_start = datetime.now()
        db_health = await db_manager.health_check()
        db_check_duration = (datetime.now() - db_check_start).total_seconds()
        
        health_status["checks"]["database"] = {
            "status": "healthy" if db_health else "unhealthy",
            "response_time_ms": round(db_check_duration * 1000, 2),
            "connection": "ok" if db_health else "failed"
        }
        
        if not db_health:
            health_status["status"] = "degraded"
        
        # Test service catalog availability
        try:
            session = db_manager.get_session()
            from services.persistence.repositories import TestCatalogRepository
            catalog_repo = TestCatalogRepository(session)
            
            catalog_check_start = datetime.now()
            service_count = len(await catalog_repo.search_tests("", limit=1))
            catalog_check_duration = (datetime.now() - catalog_check_start).total_seconds()
            await session.close()
            
            health_status["checks"]["service_catalog"] = {
                "status": "healthy",
                "response_time_ms": round(catalog_check_duration * 1000, 2),
                "services_available": service_count > 0
            }
        except Exception as catalog_error:
            health_status["checks"]["service_catalog"] = {
                "status": "unhealthy",
                "error": str(catalog_error)
            }
            health_status["status"] = "degraded"
            
    except Exception as db_error:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(db_error)
        }
        health_status["status"] = "unhealthy"
    
    # Redis health check
    try:
        import redis.asyncio as redis
        
        redis_check_start = datetime.now()
        redis_client = redis.from_url("redis://localhost:6379/0")
        await redis_client.ping()
        await redis_client.close()
        redis_check_duration = (datetime.now() - redis_check_start).total_seconds()
        
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "response_time_ms": round(redis_check_duration * 1000, 2),
            "connection": "ok"
        }
    except Exception as redis_error:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(redis_error)
        }
        health_status["status"] = "degraded"
    
    # Environment configuration check
    required_vars = ["WA_ACCESS_TOKEN", "WA_PHONE_NUMBER_ID", "WA_VERIFY_TOKEN", "GOOGLE_API_KEY"]
    env_status = "healthy"
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            env_status = "unhealthy"
    
    health_status["checks"]["environment"] = {
        "status": env_status,
        "required_vars": required_vars,
        "missing_vars": missing_vars
    }
    
    if env_status == "unhealthy":
        health_status["status"] = "unhealthy"
    
    # Circuit breaker status
    try:
        from services.utils.retry_handler import database_circuit_breaker, payment_circuit_breaker
        
        health_status["checks"]["circuit_breakers"] = {
            "status": "healthy",
            "database_breaker": {
                "state": database_circuit_breaker.state,
                "failure_count": database_circuit_breaker.failure_count
            },
            "payment_breaker": {
                "state": payment_circuit_breaker.state,
                "failure_count": payment_circuit_breaker.failure_count
            }
        }
    except Exception:
        # Circuit breakers are optional
        pass
    
    # Overall response time
    total_duration = (datetime.now() - start_time).total_seconds()
    health_status["response_time_ms"] = round(total_duration * 1000, 2)
    
    # Set appropriate HTTP status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content=health_status,
        status_code=status_code
    )


@router.get("/statistics")
async def get_business_statistics():
    """Get detailed business system statistics."""
    return message_handler.get_handler_statistics()


@router.post("/force-process-batch/{customer_id}")
async def force_process_customer_batch(customer_id: str):
    """Force process any pending message batch for a customer (admin endpoint)."""
    from services.messaging.message_batching import message_batcher
    
    result = await message_batcher.force_process_user_batch(customer_id)
    
    return {
        "customer_id": customer_id,
        "batch_processed": result,
        "message": "Batch processed" if result else "No pending batch found"
    }