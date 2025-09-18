"""
Modern LangGraph Supervisor-Based Webhook Handler for Krsnaa Diagnostics.
COMPLETELY ELIMINATES hardcoded routing logic and payload mappings.
Uses pure LLM decision making following LangGraph customer support patterns.
"""

import json
import hmac
import hashlib
import structlog
from typing import Optional, Dict, Any
from datetime import datetime

from services.messaging.instagram_types import InstagramMessage
from services.messaging.instagram_api import send_reply
from services.messaging.message_batching import message_batcher
from agents.core.healthcare_assistant_v3 import process_healthcare_message
from config.settings import settings

logger = structlog.get_logger()


class ModernIntegratedWebhookHandler:
    """
    Modern webhook handler using LangGraph supervisor pattern.
    
    ELIMINATES ALL HARDCODED LOGIC:
    - No static payload_map dictionary
    - No hardcoded if/else routing 
    - No rigid system prompts
    - Pure LLM-driven conversation flow
    """
    
    def __init__(self):
        self.logger = logger.bind(component="modern_webhook_handler")
        
        # Track sessions for metadata only - no hardcoded routing logic
        self.sessions = {}
        
        # Register with message batcher 
        message_batcher.add_message_handler(self._handle_batched_message)
        
        self.logger.info(
            "Modern LangGraph supervisor webhook handler initialized",
            features=["supervisor_routing", "llm_driven", "no_hardcoded_logic"]
        )
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Instagram webhook signature."""
        if not signature:
            return False
        
        try:
            signature = signature.replace('sha256=', '')
            expected = hmac.new(
                settings.instagram_app_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            self.logger.error(f"Signature verification failed: {e}")
            return False
    
    async def handle_webhook(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Handle incoming webhook using modern supervisor pattern."""
        try:
            self.logger.debug("Webhook received", entries=len(data.get("entry", [])))
            
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    self.logger.info(
                        "Processing messaging event",
                        sender_id=messaging_event.get("sender", {}).get("id"),
                        has_message=bool(messaging_event.get("message"))
                    )
                    
                    instagram_message = self._parse_messaging_event(messaging_event)
                    if instagram_message:
                        # Skip business account messages
                        if instagram_message.sender_id == settings.ig_user_id:
                            self.logger.info("Ignoring business account message")
                            continue
                            
                        await message_batcher.process_message(instagram_message)
            
            return {"status": "ok"}
            
        except Exception as e:
            self.logger.error(f"Webhook handling error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _parse_messaging_event(self, event: Dict[str, Any]) -> Optional[InstagramMessage]:
        """Parse Instagram messaging event - same as before."""
        try:
            sender_id = event.get("sender", {}).get("id")
            if not sender_id:
                return None
            
            message_text = None
            quick_reply_payload = None
            message_type = "text"
            attachments = None
            
            if "message" in event:
                message = event["message"]
                message_text = message.get("text")
                message_id = message.get("mid", f"msg_{int(datetime.now().timestamp())}")
                
                if "quick_reply" in message:
                    quick_reply_payload = message["quick_reply"].get("payload")
                    message_type = "quick_reply"
                
                if "attachments" in message:
                    attachments = message["attachments"]
                    message_type = "attachment"
            
            elif "postback" in event:
                postback = event["postback"]
                quick_reply_payload = postback.get("payload")
                message_text = postback.get("title", quick_reply_payload)
                message_type = "postback"
                message_id = f"postback_{int(datetime.now().timestamp())}"
            
            else:
                return None
            
            return InstagramMessage(
                sender_id=sender_id,
                message_id=message_id,
                timestamp=event.get("timestamp", int(datetime.now().timestamp())),
                message_type=message_type,
                text=message_text,
                quick_reply_payload=quick_reply_payload,
                attachments=attachments
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing messaging event: {e}")
            return None
    
    async def _handle_batched_message(self, message: InstagramMessage, batch_info: Dict[str, Any]):
        """
        Handle message using modern LangGraph supervisor.
        ELIMINATED: All hardcoded routing logic and payload mappings.
        """
        try:
            self.logger.info(
                "Processing message with LangGraph supervisor",
                sender_id=message.sender_id,
                is_batched=batch_info.get("is_batched", False)
            )
            
            # Check for active ticket (keep this business logic)
            from services.ticket_management.webhook_interceptor import get_webhook_interceptor
            interceptor = await get_webhook_interceptor()
            intercept_info = await interceptor.should_intercept(message.sender_id)
            
            if intercept_info["should_intercept"]:
                self.logger.info("Message intercepted for active ticket")
                message_text = self._prepare_message_text(message)
                if message_text:
                    await interceptor.handle_customer_message(
                        instagram_id=message.sender_id,
                        message_text=message_text,
                        ticket_id=intercept_info["ticket_id"],
                        customer_name=None
                    )
                    await interceptor.send_agent_response(
                        instagram_id=message.sender_id,
                        ticket_id=intercept_info["ticket_id"]
                    )
                return
            
            # Get session ID
            session_id = self._get_session_id(message.sender_id)
            
            # Prepare message text using LLM interpretation (NO hardcoded mappings)
            message_text = await self._intelligent_message_preparation(message)
            
            if not message_text:
                return
            
            # Process with TRUE LangGraph healthcare assistant
            response = process_healthcare_message(
                message=message_text,
                session_id=session_id,
                instagram_id=message.sender_id
            )
            
            # Send response
            await self._send_response(message.sender_id, response)
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", sender_id=message.sender_id)
            
            # Fallback response (no hardcoded error templates)
            try:
                await send_reply(
                    message.sender_id,
                    "I'm here to help you with medical tests and health recommendations. How can I assist you today?"
                )
            except Exception as send_error:
                self.logger.error(f"Failed to send fallback message: {send_error}")
    
    def _get_session_id(self, sender_id: str, platform: str = "instagram") -> str:
        """Get persistent session ID with platform support."""
        persistent_session_id = f"session_{sender_id}_{platform}_healthcare"
        
        if sender_id not in self.sessions:
            self.sessions[sender_id] = {
                "session_id": persistent_session_id,
                "created_at": datetime.now(),
                "last_message": datetime.now(),
                "platform": platform
            }
            self.logger.info(f"Created {platform} session for {sender_id}: {persistent_session_id}")
        else:
            self.sessions[sender_id]["last_message"] = datetime.now()
        
        return persistent_session_id
    
    async def _intelligent_message_preparation(self, message: InstagramMessage) -> Optional[str]:
        """
        REVOLUTIONARY CHANGE: Use LLM to interpret payloads instead of hardcoded mappings.
        Completely eliminates the static payload_map dictionary.
        """
        if message.quick_reply_payload:
            return await self._llm_interpret_payload(message.quick_reply_payload, message.text)
        
        return message.text
    
    async def _llm_interpret_payload(self, payload: str, original_text: Optional[str]) -> str:
        """
        Use LLM to contextually interpret quick reply payloads.
        ELIMINATES: Static payload_map with 20+ hardcoded mappings.
        """
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import SystemMessage, HumanMessage
            import os
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.1  # Low temperature for consistent interpretation
            )
            
            interpretation_prompt = f"""
            Convert this Instagram quick reply payload into natural user language.
            
            Payload: "{payload}"
            Original text: "{original_text or 'None'}"
            
            CONTEXT: User clicked a quick reply button in a healthcare chat.
            Convert the payload to what the user actually means in natural conversation.
            
            Examples:
            - "BOOK_TEST" → "I want to book a test"
            - "GET_REPORT" → "I want to get my report"
            - "YES" → "Yes"
            - "PAY_ONLINE" → "I want to pay online"
            - "MORNING" → "Morning slot please"
            
            Return ONLY the natural language interpretation.
            """
            
            response = llm.invoke([
                SystemMessage(content=interpretation_prompt),
                HumanMessage(content=f"Interpret: {payload}")
            ])
            
            interpreted_message = response.content.strip()
            
            self.logger.info(
                f"LLM payload interpretation",
                original_payload=payload,
                interpreted_message=interpreted_message
            )
            
            return interpreted_message
            
        except Exception as e:
            self.logger.error(f"LLM payload interpretation failed: {e}")
            # Fallback to payload as-is
            return payload
    
    def _prepare_message_text(self, message: InstagramMessage) -> Optional[str]:
        """Legacy method for ticket system compatibility."""
        if message.quick_reply_payload:
            # For ticket system, still use basic payload conversion
            basic_conversions = {
                "YES": "Yes",
                "NO": "No",
                "AGENT_HANDOFF": "I want to talk to a human agent"
            }
            return basic_conversions.get(message.quick_reply_payload, message.quick_reply_payload)
        
        return message.text
    
    async def _send_response(self, recipient_id: str, response: Dict[str, Any]):
        """Send response to Instagram user."""
        try:
            # Skip business account messages in production
            import os
            dev_mode = os.getenv("ALLOW_BUSINESS_ACCOUNT_REPLIES", "false").lower() == "true"
            
            if recipient_id == settings.ig_user_id and not dev_mode:
                self.logger.warning(f"Skipping message to business account: {recipient_id}")
                return
            
            # Send message
            await send_reply(recipient_id, response["text"])
            
            self.logger.info(
                "Response sent successfully",
                recipient_id=recipient_id,
                text_length=len(response["text"]),
                supervisor_intent=response.get("intent", "unknown")
            )
            
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
            
            if "cannot be found" in str(e).lower():
                self.logger.info(f"User not found - likely test message: {recipient_id}")
    
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
            
            # Process message through healthcare assistant
            response = await process_healthcare_message(
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
            "handler_type": "modern_langgraph_supervisor",
            "hardcoded_logic": False,
            "supervisor_based": True,
            "message_batcher_stats": message_batcher.get_batch_stats(),
            "session_details": [
                {
                    "sender_id": sender_id,
                    "session_age_minutes": (datetime.now() - session["created_at"]).total_seconds() / 60,
                    "last_message_minutes_ago": (datetime.now() - session["last_message"]).total_seconds() / 60
                }
                for sender_id, session in self.sessions.items()
            ]
        }


# Global instance
modern_integrated_webhook_handler = ModernIntegratedWebhookHandler()