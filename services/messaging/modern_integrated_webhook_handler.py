"""
WhatsApp-only Webhook Handler for Century Property Tax.
Handles WhatsApp Business API messages with property tax focused conversations.
"""

import json
import structlog
from typing import Optional, Dict, Any
from datetime import datetime

from services.messaging.whatsapp_client import get_whatsapp_client
from services.messaging.message_batching import message_batcher
from agents.core.property_tax_assistant_v3 import process_property_tax_message

logger = structlog.get_logger()


class ModernIntegratedWebhookHandler:
    """
    WhatsApp-only webhook handler for property tax customer support.

    Features:
    - WhatsApp Business API integration
    - Property tax conversation handling
    - LLM-driven response generation
    - Session management for customer inquiries
    """

    def __init__(self):
        self.logger = logger.bind(component="whatsapp_webhook_handler")

        # Track sessions for metadata only
        self.sessions = {}

        # Initialize WhatsApp client
        self.whatsapp_client = get_whatsapp_client()

        self.logger.info(
            "WhatsApp webhook handler initialized",
            features=["whatsapp_business_api", "property_tax_focus", "llm_driven"]
        )

    def verify_webhook(self, verify_token: str, challenge: str) -> Optional[str]:
        """Verify WhatsApp webhook challenge."""
        return self.whatsapp_client.verify_webhook(verify_token, challenge)

    async def handle_webhook(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Handle incoming WhatsApp webhook."""
        try:
            self.logger.debug("WhatsApp webhook received", object_type=data.get("object"))

            # Parse message using WhatsApp client
            message_data = self.whatsapp_client.parse_webhook_message(data)
            if message_data:
                await self._handle_whatsapp_message(message_data)

            # Parse status updates
            status_data = self.whatsapp_client.parse_status_update(data)
            if status_data:
                self._handle_status_update(status_data)

            return {"status": "ok"}

        except Exception as e:
            self.logger.error(f"WhatsApp webhook handling error: {e}")
            return {"status": "error", "message": str(e)}

    async def _handle_whatsapp_message(self, message_data: Dict[str, Any]):
        """Handle incoming WhatsApp message."""
        try:
            sender_id = message_data.get("from")
            message_text = message_data.get("text", "")
            message_type = message_data.get("type", "text")

            if not sender_id:
                self.logger.warning("WhatsApp message missing sender ID")
                return

            self.logger.info(
                "Processing WhatsApp message",
                sender_id=sender_id[:5] + "***",
                message_type=message_type
            )

            # Handle non-text messages
            if message_type != "text":
                await self._handle_media_message(sender_id, message_data)
                return

            if not message_text.strip():
                self.logger.warning("Empty WhatsApp message received")
                return

            # Check for active ticket (keep this business logic)
            from services.ticket_management.webhook_interceptor import get_webhook_interceptor
            interceptor = await get_webhook_interceptor()
            intercept_info = await interceptor.should_intercept(sender_id)

            if intercept_info["should_intercept"]:
                self.logger.info("Message intercepted for active ticket")
                await interceptor.handle_customer_message(
                    instagram_id=sender_id,  # Legacy field name for compatibility
                    message_text=message_text,
                    ticket_id=intercept_info["ticket_id"],
                    customer_name=message_data.get("contact_name")
                )
                await interceptor.send_agent_response(
                    instagram_id=sender_id,
                    ticket_id=intercept_info["ticket_id"]
                )
                return

            # Get session ID
            session_id = self._get_session_id(sender_id, "whatsapp")

            # Process with property tax assistant
            response = await process_property_tax_message(
                message=message_text,
                customer_id=sender_id,
                session_id=session_id
            )

            # Send response via WhatsApp
            await self._send_whatsapp_response(sender_id, response)

        except Exception as e:
            self.logger.error(f"Error processing WhatsApp message: {e}", sender_id=sender_id)

            # Fallback response
            try:
                fallback_text = "I'm here to help you with property tax inquiries. How can I assist you today?"
                await self.whatsapp_client.send_text_message(sender_id, fallback_text)
            except Exception as send_error:
                self.logger.error(f"Failed to send fallback message: {send_error}")

    async def _handle_media_message(self, sender_id: str, message_data: Dict[str, Any]):
        """Handle non-text WhatsApp messages (images, documents, etc.)."""
        message_type = message_data.get("type")

        if message_type == "document":
            response_text = "I've received your document. I can help you with property tax questions related to this document."
        elif message_type == "image":
            response_text = "I've received your image. If this is related to property tax documentation, I can help explain what information you might need."
        else:
            response_text = f"I've received your {message_type}. I specialize in property tax assistance. How can I help you today?"

        await self.whatsapp_client.send_text_message(sender_id, response_text)

    def _handle_status_update(self, status_data: Dict[str, Any]):
        """Handle WhatsApp message status updates."""
        self.logger.debug(
            "WhatsApp status update",
            message_id=status_data.get("id"),
            status=status_data.get("status")
        )

    def _get_session_id(self, sender_id: str, platform: str = "whatsapp") -> str:
        """Get persistent session ID with platform support."""
        persistent_session_id = f"session_{sender_id}_{platform}_property_tax"

        if sender_id not in self.sessions:
            self.sessions[sender_id] = {
                "session_id": persistent_session_id,
                "created_at": datetime.now(),
                "last_message": datetime.now(),
                "platform": platform
            }
            self.logger.info(f"Created {platform} session for {sender_id[:5]}***: {persistent_session_id}")
        else:
            self.sessions[sender_id]["last_message"] = datetime.now()

        return persistent_session_id

    async def _send_whatsapp_response(self, recipient_id: str, response: Dict[str, Any]):
        """Send response to WhatsApp user."""
        try:
            # Extract response text
            response_text = response.get("response") or response.get("text") or "I apologize, but I'm having trouble processing your request right now."

            # Send message via WhatsApp Business API
            result = await self.whatsapp_client.send_text_message(recipient_id, response_text)

            if result["success"]:
                self.logger.info(
                    "WhatsApp response sent successfully",
                    recipient_id=recipient_id[:5] + "***",
                    text_length=len(response_text),
                    message_id=result.get("message_id")
                )
            else:
                self.logger.error(
                    "Failed to send WhatsApp response",
                    recipient_id=recipient_id[:5] + "***",
                    error=result.get("error")
                )

        except Exception as e:
            self.logger.error(f"Error sending WhatsApp response: {e}")

    async def handle_message(self, message_text: str, user_id: str, platform: str = "whatsapp",
                           user_name: str = None, raw_message_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle direct message for WhatsApp integration.
        Compatible interface with the old universal message handler.
        """
        try:
            self.logger.info(f"Processing {platform} message from {user_id[:5]}***",
                           text_length=len(message_text), platform=platform)

            # Get or create session
            session_id = self._get_session_id(user_id, platform)

            # Process message through property tax assistant
            response = await process_property_tax_message(
                message=message_text,
                customer_id=user_id,
                session_id=session_id
            )

            # Update session tracking
            if user_id not in self.sessions:
                self.sessions[user_id] = {
                    "created_at": datetime.now(),
                    "platform": platform,
                    "user_name": user_name
                }
            self.sessions[user_id]["last_message"] = datetime.now()

            # Return response in expected format
            response_text = response.get("response") or response.get("text") or "I apologize, but I'm having trouble processing your request right now. Please try again."
            return {
                "text": response_text,
                "platform": platform,
                "success": True
            }

        except Exception as e:
            self.logger.error(f"Error processing {platform} message: {e}")
            return {
                "text": "I apologize, but I'm experiencing technical difficulties. Please try again later.",
                "success": False,
                "error": str(e)
            }

    def get_handler_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            "active_sessions": len(self.sessions),
            "handler_type": "whatsapp_property_tax",
            "platform": "whatsapp_business_api",
            "configured": self.whatsapp_client.is_configured(),
            "session_details": [
                {
                    "sender_id": sender_id[:5] + "***",
                    "session_age_minutes": (datetime.now() - session["created_at"]).total_seconds() / 60,
                    "last_message_minutes_ago": (datetime.now() - session["last_message"]).total_seconds() / 60,
                    "platform": session.get("platform", "whatsapp")
                }
                for sender_id, session in self.sessions.items()
            ]
        }


# Global instance
modern_integrated_webhook_handler = ModernIntegratedWebhookHandler()