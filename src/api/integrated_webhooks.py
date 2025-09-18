"""
Production-ready webhook endpoints for Krsnaa Diagnostics.
Uses integrated handler with simplified agent + message batching + PRD alignment.
"""

import os
import logging
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import PlainTextResponse

from services.messaging.modern_integrated_webhook_handler import modern_integrated_webhook_handler

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Instagram webhook verification endpoint.
    Instagram sends a GET request to verify the webhook URL.
    """
    verify_token = os.getenv("VERIFY_TOKEN", "")
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token") 
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == verify_token:
        logger.info("✅ Webhook verified successfully (integrated)")
        return PlainTextResponse(content=challenge)
    
    logger.warning(f"❌ Webhook verification failed - mode: {mode}, token_match: {token == verify_token}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def handle_webhook(request: Request):
    """
    Instagram webhook handler endpoint.
    Uses integrated handler with simplified agent + message batching.
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Get signature header
        signature = request.headers.get("X-Hub-Signature-256", "")
        
        # Verify signature (uncomment for production)
        # if not modern_integrated_webhook_handler.verify_signature(body, signature):
        #     logger.warning("Invalid webhook signature")
        #     raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Parse JSON
        data = await request.json()
        
        # Log webhook data
        logger.info(f"📨 Webhook received (integrated): {data.get('object', 'unknown')}")
        
        # Handle through modern LangGraph supervisor system
        result = await modern_integrated_webhook_handler.handle_webhook(data)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error handling webhook: {e}", exc_info=True)
        # Return 200 to prevent Instagram from retrying
        return {"status": "error", "message": str(e)}


@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint with database and system monitoring."""
    from datetime import datetime
    import asyncio
    
    start_time = datetime.now()
    health_status = {
        "status": "healthy",
        "service": "krsnaa-diagnostics-modern",
        "version": "4.0.0",
        "architecture": "langgraph-supervisor-pattern",
        "timestamp": start_time.isoformat(),
        "components": {},
        "checks": {},
        "features": [
            "langgraph_supervisor_pattern",
            "llm_driven_routing",
            "no_hardcoded_logic",
            "intelligent_payload_interpretation",
            "message_batching", 
            "instagram_integration",
            "langchain_gemini",
            "contextual_medical_analysis"
        ]
    }
    
    # Component status from modern handler
    stats = modern_integrated_webhook_handler.get_handler_stats()
    health_status["components"] = {
        "webhook_handler": "operational",
        "modern_supervisor": "operational",
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
        
        # Test catalog availability
        try:
            session = db_manager.get_session()
            from services.persistence.repositories import TestCatalogRepository
            catalog_repo = TestCatalogRepository(session)
            
            catalog_check_start = datetime.now()
            test_count = len(await catalog_repo.search_tests("", limit=1))
            catalog_check_duration = (datetime.now() - catalog_check_start).total_seconds()
            await session.close()
            
            health_status["checks"]["test_catalog"] = {
                "status": "healthy",
                "response_time_ms": round(catalog_check_duration * 1000, 2),
                "tests_available": test_count > 0
            }
        except Exception as catalog_error:
            health_status["checks"]["test_catalog"] = {
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
        from services.persistence.redis_conversation_store import get_conversation_store
        
        redis_check_start = datetime.now()
        # Test Redis connection using conversation store
        conv_store = get_conversation_store()
        redis_healthy = conv_store.health_check()
        redis_check_duration = (datetime.now() - redis_check_start).total_seconds()
        
        if not redis_healthy:
            raise Exception("Redis health check failed")
        
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
    import os
    required_vars = ["IG_TOKEN", "IG_USER_ID", "VERIFY_TOKEN", "GOOGLE_API_KEY"]
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
    
    from fastapi import Response
    import json
    return Response(
        content=json.dumps(health_status),
        status_code=status_code,
        media_type="application/json"
    )


@router.get("/stats")
async def get_stats():
    """Get detailed system statistics."""
    return modern_integrated_webhook_handler.get_handler_stats()


@router.post("/force-process-batch/{user_id}")
async def force_process_batch(user_id: str):
    """Force process any pending message batch for a user (admin endpoint)."""
    from services.messaging.message_batching import message_batcher
    
    result = await message_batcher.force_process_user_batch(user_id)
    
    return {
        "user_id": user_id,
        "batch_processed": result,
        "message": "Batch processed" if result else "No pending batch found"
    }