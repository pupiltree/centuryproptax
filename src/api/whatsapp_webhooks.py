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
            # Still return 200 OK to prevent retries - log security incident
            return {"status": "received", "warning": "signature_verification_failed"}

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
    """Handle WhatsApp image message for prescription analysis."""
    try:
        logger.info(f"🖼️ Processing prescription image from WhatsApp user {user_id[:5]}***")

        # Import image handler
        from services.messaging.whatsapp_image_handler import WhatsAppImageHandler
        from agents.simplified.prescription_tools import analyze_prescription_image_tool_async
        import base64
        
        # Download image from WhatsApp
        image_handler = WhatsAppImageHandler()
        image_result = await image_handler.download_image_from_whatsapp_message(message_data)
        
        if not image_result:
            logger.error("Failed to download WhatsApp image")
            whatsapp_client = get_whatsapp_client()
            await whatsapp_client.send_text_message(
                to=user_id,
                message="I couldn't download your image. Please try uploading it again."
            )
            return
        
        image_bytes, image_format = image_result
        logger.info(f"📷 Downloaded prescription image ({len(image_bytes)} bytes, {image_format})")
        
        # Convert to base64 for analysis
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Analyze prescription image
        logger.info("🔍 Starting prescription image analysis...")
        analysis_result = await analyze_prescription_image_tool_async(
            image_data_b64=image_b64,
            image_format=image_format,
            customer_id=user_id
        )
        
        # Process analysis result
        whatsapp_client = get_whatsapp_client()
        
        if analysis_result.get("success"):
            # Successful analysis - format with LLM intelligence
            prescription_data = analysis_result.get("prescription_data", {})

            # Format summary naturally without redundant tool
            summary_parts = []
            if prescription_data.get("patient_name"):
                summary_parts.append(f"**Patient:** {prescription_data['patient_name']}")
            if prescription_data.get("age") or prescription_data.get("gender"):
                age_gender = []
                if prescription_data.get("age"): age_gender.append(f"{prescription_data['age']} years")
                if prescription_data.get("gender"): age_gender.append(prescription_data['gender'])
                summary_parts.append(f"**Patient Info:** {', '.join(age_gender)}")

            tests = prescription_data.get("prescribed_tests", [])
            if tests:
                if len(tests) == 1:
                    summary_parts.append(f"**Test:** {tests[0]}")
                else:
                    summary_parts.append(f"**Tests:** {', '.join(tests)}")

            if prescription_data.get("doctor_name"):
                doctor_info = f"**Prescribed by:** Dr. {prescription_data['doctor_name']}"
                if prescription_data.get("hospital_clinic"):
                    doctor_info += f" ({prescription_data['hospital_clinic']})"
                summary_parts.append(doctor_info)

            if prescription_data.get("prescription_date"):
                summary_parts.append(f"**Date:** {prescription_data['prescription_date']}")

            summary = "\n".join(summary_parts) + "\n\nIs this information correct?" if summary_parts else "I found some prescription information but need clarification on the details."
            
            confidence_text = ""
            confidence = analysis_result.get("confidence_score", 0)
            if confidence >= 0.7:
                confidence_text = "✅ High confidence analysis"
            elif confidence >= 0.4:
                confidence_text = "⚠️ Partial information extracted"
            else:
                confidence_text = "⚡ Basic information found"
            
            response_message = f"""📋 **Prescription Analysis Complete**

{summary}

{confidence_text}

Reply with "Yes" to confirm and book these tests, or tell me what needs to be corrected."""
            
        else:
            # Analysis failed or low quality
            error_message = analysis_result.get("message", "Could not analyze prescription")
            user_friendly = analysis_result.get("user_friendly_error", "")
            
            response_message = f"""🔍 **Prescription Analysis**

{error_message}

{user_friendly if user_friendly else ''}

You can:
• Upload a clearer image
• Tell me which tests you need
• Ask for help with specific concerns"""
        
        # Save prescription data to session context for follow-up confirmation
        try:
            from services.persistence.redis_conversation_store import get_conversation_store
            conv_store = get_conversation_store()
            whatsapp_session_id = f"session_{user_id}_whatsapp_healthcare"
            
            if analysis_result.get("success"):
                # Save prescription data for confirmation workflow
                prescription_context = {
                    "type": "prescription_analysis",
                    "prescription_data": analysis_result.get("prescription_data", {}),
                    "confidence_score": analysis_result.get("confidence_score", 0),
                    "awaiting_confirmation": True,
                    "timestamp": str(datetime.now())
                }
                
                # Store in Redis context
                current_context = conv_store.get_context(whatsapp_session_id) or {}
                current_context["prescription_analysis"] = prescription_context
                conv_store.save_context(whatsapp_session_id, current_context)
                
                logger.info(f"💾 Saved prescription context for session {whatsapp_session_id}")
                
        except Exception as ctx_error:
            logger.warning(f"Failed to save prescription context: {ctx_error}")
        
        # Send response
        send_result = await whatsapp_client.send_text_message(
            to=user_id,
            message=response_message
        )
        
        if send_result.get("success"):
            logger.info(f"✅ Prescription analysis response sent to {user_id[:5]}***")
        else:
            logger.error(f"❌ Failed to send prescription analysis: {send_result}")
            
    except Exception as e:
        logger.error(f"WhatsApp image processing error: {e}")
        # Send error message to user
        try:
            whatsapp_client = get_whatsapp_client()
            await whatsapp_client.send_text_message(
                to=user_id,
                message="I had trouble analyzing your prescription image. Please try again or tell me which tests you'd like to book."
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
            # Process image message for prescription analysis
            await _handle_whatsapp_image_message(message_data, message_handler, user_id, contact_name)
            return
        elif message_type != "text":
            # Handle other non-text message types
            whatsapp_client = get_whatsapp_client()
            await whatsapp_client.send_text_message(
                to=user_id,
                message="I can process text messages and prescription images. Please send your message as text or upload a prescription image."
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
        from services.messaging.property_tax_templates import get_property_tax_templates
        templates = get_property_tax_templates()

        # Remove any formatting from phone number
        clean_phone = phone_number.replace("+", "").replace("-", "").replace(" ", "")

        if template_type == "menu":
            result = await templates.send_service_options_menu(clean_phone)
        elif template_type == "assessment_buttons":
            result = await templates.send_quick_actions_buttons(clean_phone, "assessment")
        elif template_type == "payment_buttons":
            result = await templates.send_quick_actions_buttons(clean_phone, "payment")
        elif template_type == "appeal_checklist":
            result = await templates.send_appeal_document_checklist(clean_phone)
        elif template_type == "property_lookup":
            # Test with sample property data
            sample_property = {
                "address": "123 Main St, Anytown, TX 75001",
                "owner": "John Doe",
                "assessed_value": 250000,
                "tax_year": "2024",
                "due_amount": 3500,
                "due_date": "December 31, 2024"
            }
            result = await templates.send_property_lookup_result(clean_phone, sample_property)
        elif template_type == "payment_options":
            result = await templates.send_payment_options(clean_phone, "3,500", "December 31, 2024")
        else:
            return {
                "error": "Invalid template type",
                "available_types": ["menu", "assessment_buttons", "payment_buttons", "appeal_checklist", "property_lookup", "payment_options"]
            }

        return {
            "template_type": template_type,
            "phone_number": clean_phone,
            "result": result
        }

    except Exception as e:
        logger.error(f"Template test error: {e}")
        return {
            "error": str(e),
            "template_type": template_type,
            "phone_number": phone_number
        }