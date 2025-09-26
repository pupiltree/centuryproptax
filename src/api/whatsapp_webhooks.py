"""
WhatsApp Business API webhook handlers for Century Property Tax.
Handles webhook verification and message processing.
"""

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from typing import Dict, Any, Optional
import structlog
from datetime import datetime
from services.messaging.whatsapp_client import get_whatsapp_client
from services.messaging.modern_integrated_webhook_handler import modern_integrated_webhook_handler
from src.core.logging import get_logger

logger = get_logger("whatsapp_webhooks")

# In-memory cache for processed message IDs (prevents duplicate processing)
processed_messages = set()
MAX_PROCESSED_CACHE = 1000  # Prevent memory growth

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

@router.get("/webhook")
async def whatsapp_webhook_verify(
    request: Request,
    verify_token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge"),
    mode: str = Query(..., alias="hub.mode")
):
    """
    WhatsApp webhook verification endpoint.

    This endpoint is called by WhatsApp to verify the webhook URL.
    Must return the challenge parameter if verification succeeds.
    """
    logger.info("WhatsApp webhook verification request",
                mode=mode, verify_token=verify_token[:10] + "***")

    try:
        whatsapp_client = get_whatsapp_client()

        # Verify the webhook
        if mode == "subscribe":
            verified_challenge = whatsapp_client.verify_webhook(verify_token, challenge)
            if verified_challenge:
                logger.info("WhatsApp webhook verification successful")
                return PlainTextResponse(verified_challenge)

        logger.warning("WhatsApp webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")

    except Exception as e:
        logger.error(f"WhatsApp webhook verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification error")


@router.post("/webhook")
async def whatsapp_webhook_handler(request: Request):
    """
    WhatsApp webhook message handler with enhanced security.

    Processes incoming messages and status updates from WhatsApp Business API.
    Includes signature verification for enhanced security.
    IMPORTANT: Always returns 200 OK to prevent WhatsApp retries.
    """
    try:
        # Get raw body for signature verification
        raw_body = await request.body()

        # Get signature header
        signature = request.headers.get("X-Hub-Signature-256", "")

        # Verify webhook signature for enhanced security
        whatsapp_client = get_whatsapp_client()
        if not whatsapp_client.verify_webhook_signature(raw_body, signature):
            logger.warning("WhatsApp webhook signature verification failed")
            # SECURITY: Reject invalid webhook requests
            raise HTTPException(status_code=403, detail="Webhook signature verification failed")

        # Parse JSON data
        webhook_data = await request.json() if raw_body else {}
        logger.info("WhatsApp webhook received",
                   object_type=webhook_data.get("object"),
                   entries_count=len(webhook_data.get("entry", [])),
                   signature_verified=bool(signature))

        # Use the modern integrated handler for WhatsApp messages
        handler = modern_integrated_webhook_handler

        # Try to parse as message
        message_data = whatsapp_client.parse_webhook_message(webhook_data)
        if message_data:
            message_id = message_data.get("id")

            # Check for duplicate messages
            if message_id and message_id in processed_messages:
                logger.info(f"Duplicate WhatsApp message ignored: {message_id}")
                return {"status": "received"}

            # Add to processed cache
            if message_id:
                processed_messages.add(message_id)
                # Prevent memory growth
                if len(processed_messages) > MAX_PROCESSED_CACHE:
                    # Remove oldest half of messages
                    old_messages = list(processed_messages)[:MAX_PROCESSED_CACHE // 2]
                    processed_messages.difference_update(old_messages)
                    logger.debug("Cleaned processed messages cache")

            # Process message in background to return 200 OK immediately
            import asyncio
            asyncio.create_task(_handle_whatsapp_message_safe(message_data, handler))
            logger.info("WhatsApp message queued for processing")
            return {"status": "received"}

        # Try to parse as status update
        status_data = whatsapp_client.parse_status_update(webhook_data)
        if status_data:
            # Process status update (these are lightweight)
            await _handle_whatsapp_status(status_data)
            return {"status": "received"}

        # Unknown webhook type - still return 200 OK
        logger.warning("Unknown WhatsApp webhook type", data=webhook_data)
        return {"status": "received"}

    except Exception as e:
        logger.error(f"WhatsApp webhook processing error: {e}")
        # CRITICAL: Always return 200 OK to prevent WhatsApp retries
        # Even if processing fails, we don't want WhatsApp to retry
        return {"status": "received"}


async def _handle_whatsapp_message_safe(message_data: Dict[str, Any], message_handler) -> None:
    """Handle WhatsApp message safely in background task."""
    try:
        await _handle_whatsapp_message(message_data, message_handler)
    except Exception as e:
        logger.error(f"Background WhatsApp message processing failed: {e}")
        # Send error message to user if possible
        try:
            whatsapp_client = get_whatsapp_client()
            await whatsapp_client.send_text_message(
                to=message_data["from"],
                message="I'm experiencing technical difficulties. Please try again in a moment."
            )
        except:
            logger.error("Failed to send error message to user")


async def _handle_whatsapp_image_message(
    message_data: Dict[str, Any],
    message_handler,
    user_id: str,
    contact_name: str
) -> None:
    """Handle WhatsApp image message for property tax document analysis."""
    try:
        logger.info(f"🖼️ Processing property document image from WhatsApp user {user_id[:5]}***")

        # For property tax consultations, we acknowledge document uploads
        # but redirect to conversational assistance rather than automated analysis
        whatsapp_client = get_whatsapp_client()

        response_message = """🏠 **Property Tax Document Received**

Thank you for sharing your property tax document! I can see you've uploaded an image.

For accurate property tax analysis, I'd recommend:

• **Schedule a FREE consultation** - Our property tax specialists can review your documents in detail
• **Tell me about your property** - Share your address, tax concerns, or questions
• **Describe what you're looking for** - Appeal help, exemption applications, or general consultation

📞 **Ready to help!** Just tell me about your property tax situation and I'll connect you with the right specialist.

What specific property tax concerns can I help you with today?"""

        # Store document context for follow-up
        try:
            from services.persistence.redis_conversation_store import get_conversation_store
            conv_store = get_conversation_store()
            whatsapp_session_id = f"session_{user_id}_whatsapp_property_tax"

            # Save document upload context
            document_context = {
                "type": "property_document_upload",
                "awaiting_consultation_booking": True,
                "timestamp": str(datetime.now())
            }

            # Store in Redis context
            current_context = conv_store.get_context(whatsapp_session_id) or {}
            current_context["document_upload"] = document_context
            conv_store.save_context(whatsapp_session_id, current_context)

            logger.info(f"💾 Saved document upload context for session {whatsapp_session_id}")

        except Exception as ctx_error:
            logger.warning(f"Failed to save document context: {ctx_error}")

        # Send response
        send_result = await whatsapp_client.send_text_message(
            to=user_id,
            message=response_message
        )

        if send_result.get("success"):
            logger.info(f"✅ Property document response sent to {user_id[:5]}***")
        else:
            logger.error(f"❌ Failed to send property document response: {send_result}")

    except Exception as e:
        logger.error(f"WhatsApp image processing error: {e}")
        # Send error message to user
        try:
            whatsapp_client = get_whatsapp_client()
            await whatsapp_client.send_text_message(
                to=user_id,
                message="I had trouble processing your property document image. Please tell me about your property tax concerns and I'll help you directly!"
            )
        except:
            logger.error("Failed to send error message for image processing")


async def _handle_whatsapp_message(message_data: Dict[str, Any], message_handler) -> None:
    """Handle incoming WhatsApp message."""
    try:
        # Extract message details
        user_id = message_data["from"]
        message_text = message_data.get("text", "")
        message_type = message_data.get("type", "text")
        contact_name = message_data.get("contact_name", "WhatsApp User")

        logger.info(f"Processing WhatsApp message from {user_id[:5]}***",
                   type=message_type, text_length=len(message_text))

        # Handle different message types
        if message_type == "image":
            # Process image message for property document analysis
            await _handle_whatsapp_image_message(message_data, message_handler, user_id, contact_name)
            return
        elif message_type != "text":
            # Handle other non-text message types
            whatsapp_client = get_whatsapp_client()
            await whatsapp_client.send_text_message(
                to=user_id,
                message="I can process text messages and property tax documents. Please send your message as text or upload a property tax document image."
            )
            return

        if not message_text.strip():
            logger.warning("Empty WhatsApp message received")
            return

        # Process through universal message handler (normal chat flow)
        response = await message_handler.handle_message(
            message_text=message_text,
            user_id=user_id,
            platform="whatsapp",
            user_name=contact_name,
            raw_message_data=message_data
        )

        if response and response.get("text"):
            # Send response back to WhatsApp
            whatsapp_client = get_whatsapp_client()
            send_result = await whatsapp_client.send_text_message(
                to=user_id,
                message=response["text"]
            )

            if not send_result.get("success"):
                logger.error(f"Failed to send WhatsApp response: {send_result}")
        else:
            logger.warning("No response generated for WhatsApp message")

    except Exception as e:
        logger.error(f"WhatsApp message handling error: {e}")
        # Try to send error message to user
        try:
            whatsapp_client = get_whatsapp_client()
            await whatsapp_client.send_text_message(
                to=message_data["from"],
                message="I'm experiencing technical difficulties. Please try again in a moment."
            )
        except:
            pass  # Don't fail if error message can't be sent


async def _handle_whatsapp_status(status_data: Dict[str, Any]) -> None:
    """Handle WhatsApp message status update."""
    try:
        message_id = status_data.get("id")
        status = status_data.get("status")
        recipient = status_data.get("recipient_id", "")

        logger.info(f"WhatsApp status update: {message_id} -> {status} for {recipient[:5]}***")

        # Log failed messages
        if status == "failed":
            errors = status_data.get("errors", [])
            logger.error(f"WhatsApp message failed: {message_id}", errors=errors)

        # Could store status updates in database for delivery tracking
        # For now, just log them

    except Exception as e:
        logger.error(f"WhatsApp status handling error: {e}")


@router.get("/health")
async def whatsapp_health():
    """WhatsApp Business API integration health check."""
    try:
        whatsapp_client = get_whatsapp_client()
        business_config = whatsapp_client.get_business_configuration()

        health_status = {
            "whatsapp_configured": whatsapp_client.is_configured(),
            "business_configuration": business_config,
            "webhook_url": "/whatsapp/webhook",
            "verification_token_configured": bool(whatsapp_client.verify_token),
            "features": {
                "signature_verification": business_config["webhook_security_enabled"],
                "template_messaging": whatsapp_client.is_configured(),
                "interactive_messages": whatsapp_client.is_configured(),
                "business_profile": whatsapp_client.is_configured()
            }
        }

        if whatsapp_client.is_configured():
            health_status["status"] = "healthy"

            # Test business profile access if configured
            profile_result = await whatsapp_client.get_business_profile()
            health_status["business_profile_access"] = profile_result["success"]

        else:
            health_status["status"] = "not_configured"
            health_status["message"] = "WhatsApp access token not configured"

        return health_status

    except Exception as e:
        logger.error(f"WhatsApp health check error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/test-template/{phone_number}")
async def test_template_message(phone_number: str, template_type: str = "menu"):
    """Test property tax template messages (development endpoint)."""
    try:
        # Property tax templates removed - using direct Microsoft Forms URLs
        # from services.messaging.property_tax_templates import get_property_tax_templates
        # templates = get_property_tax_templates()

        # Remove any formatting from phone number
        clean_phone = phone_number.replace("+", "").replace("-", "").replace(" ", "")

        # Templates disabled - Microsoft Forms registration flow uses direct URLs
        # Template functionality removed in favor of simple Microsoft Forms registration

        return {
            "status": "disabled",
            "template_type": template_type,
            "phone_number": clean_phone,
            "message": "WhatsApp templates disabled - Microsoft Forms registration flow uses direct messaging",
            "registration_url": "https://forms.office.com/pages/responsepage.aspx?id=0t_vMiRx-Eayzz0urQPfCPwPYCS22DBNv5-YeXcrGC9UMUZRWkIxQU9RVzFBVVhURFhMUVJGV1VIMS4u&route=shorturl"
        }

    except Exception as e:
        logger.error(f"Template test error: {e}")
        return {
            "error": str(e),
            "template_type": template_type,
            "phone_number": phone_number
        }