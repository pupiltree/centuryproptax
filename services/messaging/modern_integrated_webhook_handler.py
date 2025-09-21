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
from src.core.logging import get_logger

logger = get_logger("whatsapp_webhook_handler")


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
        self.logger = logger

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

            # Handle interactive messages (button clicks, list selections)
            if message_type == "interactive":
                await self._handle_interactive_message(sender_id, message_data)
                return

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

    async def _handle_interactive_message(self, sender_id: str, message_data: Dict[str, Any]):
        """Handle interactive message responses (button clicks, list selections)."""
        try:
            from services.messaging.property_tax_templates import get_property_tax_templates
            templates = get_property_tax_templates()

            interactive_data = message_data.get("interactive", {})
            interactive_type = interactive_data.get("type")

            if interactive_type == "button_reply":
                # Handle button clicks
                button_reply = interactive_data.get("button_reply", {})
                button_id = button_reply.get("id", "")
                button_title = button_reply.get("title", "")

                self.logger.info(f"Button clicked: {button_id} - {button_title}")

                # Route based on button ID
                if button_id == "view_assessment":
                    await templates.send_property_lookup_result(sender_id, {})
                elif button_id == "file_appeal":
                    await templates.send_appeal_document_checklist(sender_id)
                elif button_id == "schedule_review":
                    await self._handle_consultation_scheduling(sender_id)
                elif button_id == "pay_now":
                    await self._handle_payment_initiation(sender_id)
                elif button_id == "payment_plan":
                    await templates.send_payment_options(sender_id, "TBD", "TBD")
                elif button_id == "payment_info":
                    await templates.send_property_lookup_result(sender_id, {})
                elif button_id == "check_assessment":
                    await templates.send_property_lookup_result(sender_id, {})
                elif button_id == "payment_status":
                    await templates.send_payment_options(sender_id, "TBD", "TBD")
                elif button_id == "talk_to_expert":
                    await self._handle_expert_consultation(sender_id)
                else:
                    # Convert button click to text message for assistant processing
                    await self._process_converted_interactive(sender_id, button_title or button_id)

            elif interactive_type == "list_reply":
                # Handle list selections
                list_reply = interactive_data.get("list_reply", {})
                selection_id = list_reply.get("id", "")
                selection_title = list_reply.get("title", "")

                self.logger.info(f"List item selected: {selection_id} - {selection_title}")

                # Route based on selection ID
                if selection_id == "assessment_review":
                    await templates.send_property_lookup_result(sender_id, {})
                elif selection_id == "appeal_process":
                    await templates.send_appeal_guidance(sender_id, "Property Owner", "TBD", "TBD")
                elif selection_id == "payment_info":
                    await templates.send_payment_options(sender_id, "TBD", "TBD")
                elif selection_id == "payment_plans":
                    await templates.send_payment_options(sender_id, "TBD", "TBD")
                elif selection_id == "schedule_consultation":
                    await self._handle_consultation_scheduling(sender_id)
                elif selection_id == "document_review":
                    await templates.send_appeal_document_checklist(sender_id)
                else:
                    # Convert selection to text message for assistant processing
                    await self._process_converted_interactive(sender_id, selection_title or selection_id)

        except Exception as e:
            self.logger.error(f"Error handling interactive message: {e}")
            # Send fallback response
            await self.whatsapp_client.send_text_message(
                sender_id,
                "I understood your selection. How can I help you with your property tax needs?"
            )

    async def _process_converted_interactive(self, sender_id: str, interaction_text: str):
        """Process interactive message as text through the assistant."""
        try:
            # Get session ID
            session_id = self._get_session_id(sender_id, "whatsapp")

            # Process through property tax assistant
            response = await process_property_tax_message(
                message=f"User selected: {interaction_text}",
                customer_id=sender_id,
                session_id=session_id
            )

            # Send response
            await self._send_whatsapp_response(sender_id, response)

        except Exception as e:
            self.logger.error(f"Error processing converted interactive message: {e}")

    async def _handle_consultation_scheduling(self, sender_id: str):
        """Handle consultation scheduling request."""
        await self.whatsapp_client.send_text_message(
            sender_id,
            "I'd be happy to help you schedule a consultation with our property tax experts. What specific property tax issue would you like to discuss?"
        )

    async def _handle_payment_initiation(self, sender_id: str):
        """Handle payment initiation request."""
        await self.whatsapp_client.send_text_message(
            sender_id,
            "To process your payment, I'll need your property information. Please provide your property address or parcel number."
        )

    async def _handle_expert_consultation(self, sender_id: str):
        """Handle expert consultation request."""
        await self.whatsapp_client.send_text_message(
            sender_id,
            "I'll connect you with one of our property tax experts. Please describe your specific question or concern so I can route you to the right specialist."
        )

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

    async def _try_send_interactive_response(self, recipient_id: str, response: Dict[str, Any]) -> bool:
        """Try to send interactive response using templates. Returns True if interactive message was sent."""
        try:
            from services.messaging.property_tax_templates import get_property_tax_templates
            templates = get_property_tax_templates()

            response_text = response.get("response") or response.get("text") or ""
            response_lower = response_text.lower()

            # Check for service menu trigger
            if any(keyword in response_lower for keyword in ["how can i help", "what can i do", "services", "property tax services"]):
                result = await templates.send_service_options_menu(recipient_id)
                return result.get("success", False)

            # Check for assessment-related responses
            if any(keyword in response_lower for keyword in ["assessment", "property value", "evaluated", "appeal"]):
                result = await templates.send_quick_actions_buttons(recipient_id, "assessment")
                return result.get("success", False)

            # Check for payment-related responses
            if any(keyword in response_lower for keyword in ["payment", "pay", "due", "bill", "amount"]):
                result = await templates.send_quick_actions_buttons(recipient_id, "payment")
                return result.get("success", False)

            # Check for document checklist trigger
            if any(keyword in response_lower for keyword in ["appeal documents", "what documents", "document checklist"]):
                result = await templates.send_appeal_document_checklist(recipient_id)
                return result.get("success", False)

            # Check for property lookup results
            if "property information" in response_lower or "property details" in response_lower:
                # For now, send empty property data - this would be populated by actual property data
                result = await templates.send_property_lookup_result(recipient_id, {})
                return result.get("success", False)

            return False  # No interactive message sent

        except Exception as e:
            self.logger.error(f"Error trying to send interactive response: {e}")
            return False

    async def _send_whatsapp_response(self, recipient_id: str, response: Dict[str, Any]):
        """Send response to WhatsApp user with template support."""
        try:
            # Check if this response should trigger a template or interactive message
            interactive_sent = await self._try_send_interactive_response(recipient_id, response)

            if interactive_sent:
                self.logger.info(
                    "Interactive WhatsApp message sent",
                    recipient_id=recipient_id[:5] + "***",
                    interactive_type="template_or_buttons"
                )
                return

            # Extract response text
            response_text = response.get("response") or response.get("text") or "I apologize, but I'm having trouble processing your request right now."

            # Send regular text message
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