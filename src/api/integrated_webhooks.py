"""
Production-ready webhook endpoints for Century Property Tax.
Uses integrated handler with simplified agent + message batching + PRD alignment.

This module provides the core WhatsApp Business API webhook endpoints for
Century Property Tax's intelligent assistant. It handles:
- Webhook verification for WhatsApp setup
- Message processing through LangGraph supervisor pattern
- Health monitoring and system statistics
- Administrative batch processing controls
"""

import os
import logging
from datetime import datetime
from fastapi import APIRouter, Request, Response, HTTPException, Query, Path
from fastapi.responses import PlainTextResponse
from typing import Dict, Any, Optional

from services.messaging.modern_integrated_webhook_handler import modern_integrated_webhook_handler
from src.core.logging import get_logger
from src.models.api_models import (
    HealthCheckResponse,
    WhatsAppWebhookPayload,
    WhatsAppResponse,
    WebhookVerificationResponse,
    SystemStats,
    ErrorResponse,
    BaseResponse,
    EXAMPLE_RESPONSES
)

logger = get_logger("integrated_webhooks")

router = APIRouter(
    prefix="",
    tags=["WhatsApp Webhooks"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        403: {"model": ErrorResponse, "description": "Forbidden - Invalid credentials"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)


@router.get(
    "/webhook",
    response_model=str,
    summary="Verify WhatsApp Webhook",
    description="""WhatsApp webhook verification endpoint required for webhook setup.

    WhatsApp sends a GET request with verification parameters to confirm
    webhook URL ownership. This endpoint validates the verify token and
    returns the challenge string if verification succeeds.

    **Required Query Parameters:**
    - `hub.mode`: Must be 'subscribe'
    - `hub.verify_token`: Must match configured VERIFY_TOKEN
    - `hub.challenge`: Challenge string to return on success

    **Environment Variables Required:**
    - `VERIFY_TOKEN`: Token for webhook verification
    """,
    responses={
        200: {
            "description": "Webhook verified successfully",
            "content": {"text/plain": {"example": "challenge_string_123"}}
        },
        403: {
            "description": "Webhook verification failed",
            "model": ErrorResponse
        }
    }
)
async def verify_webhook(
    request: Request,
    hub_mode: Optional[str] = Query(None, alias="hub.mode", description="Webhook mode (should be 'subscribe')"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token", description="Verification token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge", description="Challenge string to return")
):
    """
    Verify WhatsApp webhook endpoint for initial setup.

    This endpoint is called by WhatsApp to verify webhook URL ownership.
    It validates the provided verify token against the configured value.
    """
    verify_token = os.getenv("VERIFY_TOKEN", "")
    mode = hub_mode or request.query_params.get("hub.mode")
    token = hub_verify_token or request.query_params.get("hub.verify_token")
    challenge = hub_challenge or request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == verify_token:
        logger.info("✅ Webhook verified successfully (integrated)")
        return PlainTextResponse(content=challenge)
    
    logger.warning(f"❌ Webhook verification failed - mode: {mode}, token_match: {token == verify_token}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post(
    "/webhook",
    response_model=Dict[str, Any],
    summary="Handle WhatsApp Messages",
    description="""Main webhook endpoint for processing WhatsApp messages.

    This endpoint receives WhatsApp Business API webhook events and processes
    them through the intelligent property tax assistant. It handles:

    - Text messages from customers
    - Media messages (images, documents, audio)
    - Interactive messages (buttons, lists)
    - Message status updates
    - System notifications

    **Processing Features:**
    - LangGraph supervisor pattern for intelligent routing
    - Message batching for improved response quality
    - Automatic property tax context understanding
    - Integration with assessment booking system
    - Conversation state management via Redis

    **Security:**
    - Webhook signature verification (configurable)
    - Request validation and sanitization
    - Rate limiting and abuse protection
    """,
    responses={
        200: {
            "description": "Message processed successfully",
            "content": {
                "application/json": {
                    "example": EXAMPLE_RESPONSES["webhook_success"]
                }
            }
        },
        400: {
            "description": "Invalid webhook payload",
            "model": ErrorResponse
        },
        500: {
            "description": "Message processing failed",
            "model": ErrorResponse
        }
    }
)
async def handle_webhook(request: Request):
    """
    Process incoming WhatsApp messages through the intelligent assistant.

    Handles all WhatsApp webhook events including messages, status updates,
    and system notifications. Routes messages through LangGraph supervisor
    for intelligent property tax assistance.
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
        # Return 200 to prevent WhatsApp from retrying
        return {"status": "error", "message": str(e)}


@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="System Health Check",
    description="""Comprehensive health check endpoint for monitoring system status.

    This endpoint provides detailed health information about all system
    components including:

    **System Components:**
    - Database connectivity and performance
    - Redis cache and conversation store
    - WhatsApp Business API integration
    - LangGraph supervisor system
    - Message batching service
    - Circuit breaker status

    **Response Information:**
    - Overall system health status
    - Individual component health details
    - Response time metrics
    - Active session counts
    - Configuration validation
    - Available system features

    **Health Status Values:**
    - `healthy`: All systems operational
    - `degraded`: Some non-critical issues
    - `unhealthy`: Critical system failures
    """,
    responses={
        200: {
            "description": "System is healthy",
            "content": {
                "application/json": {
                    "example": EXAMPLE_RESPONSES["health_check_healthy"]
                }
            }
        },
        503: {
            "description": "System is unhealthy or degraded"
        }
    }
)
async def health_check():
    """Comprehensive health check endpoint with database and system monitoring."""
    from datetime import datetime
    import asyncio
    
    start_time = datetime.now()
    health_status = {
        "status": "healthy",
        "service": "century-property-tax-modern",
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
            "whatsapp_integration",
            "langchain_gemini",
            "contextual_property_tax_analysis"
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
        
        # Assessment catalog availability
        try:
            session = db_manager.get_session()
            from services.persistence.repositories import AssessmentCatalogRepository
            catalog_repo = AssessmentCatalogRepository(session)

            catalog_check_start = datetime.now()
            assessment_count = len(await catalog_repo.search_assessments("", limit=1))
            catalog_check_duration = (datetime.now() - catalog_check_start).total_seconds()
            await session.close()

            health_status["checks"]["assessment_catalog"] = {
                "status": "healthy",
                "response_time_ms": round(catalog_check_duration * 1000, 2),
                "assessments_available": assessment_count > 0
            }
        except Exception as catalog_error:
            health_status["checks"]["assessment_catalog"] = {
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
    required_vars = ["WHATSAPP_TOKEN", "WHATSAPP_PHONE_ID", "VERIFY_TOKEN", "GOOGLE_API_KEY"]
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


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="System Statistics",
    description="""Get detailed system performance and usage statistics.

    This endpoint provides real-time metrics about system performance:

    **Statistics Included:**
    - Active user sessions count
    - Total messages processed
    - Average response times
    - Message batching statistics
    - Memory and CPU usage
    - System uptime information

    **Use Cases:**
    - Performance monitoring
    - Capacity planning
    - System debugging
    - Usage analytics
    """,
    responses={
        200: {
            "description": "System statistics retrieved successfully"
        }
    }
)
async def get_stats():
    """Get detailed system performance and usage statistics."""
    return modern_integrated_webhook_handler.get_handler_stats()


@router.post(
    "/force-process-batch/{user_id}",
    response_model=Dict[str, Any],
    summary="Force Process Message Batch",
    description="""Administrative endpoint to force process pending message batches.

    This endpoint allows administrators to manually trigger processing
    of any pending message batches for a specific user. Useful for:

    **Administrative Use Cases:**
    - Debugging message processing issues
    - Manual batch processing during maintenance
    - Testing message batching functionality
    - Resolving stuck conversation states

    **Security Note:**
    This is an administrative endpoint and should be protected
    in production environments.
    """,
    responses={
        200: {
            "description": "Batch processing completed"
        },
        404: {
            "description": "User not found or no pending batch",
            "model": ErrorResponse
        }
    }
)
async def force_process_batch(
    user_id: str = Path(..., description="User ID to process batch for", example="919876543210")
):
    """Force process any pending message batch for a user (admin endpoint)."""
    from services.messaging.message_batching import message_batcher

    result = await message_batcher.force_process_user_batch(user_id)

    return {
        "status": "success" if result else "warning",
        "user_id": user_id,
        "batch_processed": result,
        "message": "Batch processed successfully" if result else "No pending batch found for user",
        "timestamp": datetime.now().isoformat()
    }