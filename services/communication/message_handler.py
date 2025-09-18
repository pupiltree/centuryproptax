"""
Generic Message Handler for Business Communication
Handles incoming messages from various channels (Instagram, WhatsApp, Web, etc.)
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
# Use workflow-compliant healthcare assistant
from agents.core.healthcare_assistant_v3 import process_healthcare_message
from config.settings import settings

logger = structlog.get_logger()


async def fetch_instagram_user_info(user_id: str) -> Dict[str, Any]:
    """
    Fetch Instagram user information using Graph API.
    Returns user details like username, name, etc.
    """
    try:
        import aiohttp
        import os
        
        access_token = os.getenv("IG_TOKEN")
        if not access_token:
            logger.warning("Instagram access token not configured")
            return {"username": f"user_{user_id}", "name": "User"}
        
        # Instagram Graph API endpoint for user info
        url = f"https://graph.instagram.com/{user_id}"
        params = {
            "fields": "username,name",
            "access_token": access_token
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    user_data = await response.json()
                    logger.info(f"📱 Fetched Instagram user info: {user_data.get('username', 'unknown')}")
                    return user_data
                else:
                    logger.warning(f"Failed to fetch Instagram user info: {response.status}")
                    return {"username": f"user_{user_id}", "name": "User"}
    
    except Exception as e:
        logger.error(f"Error fetching Instagram user info: {e}")
        return {"username": f"user_{user_id}", "name": "User"}


class UniversalMessageHandler:
    """
    Universal message handler supporting multiple communication channels.
    
    Features:
    - Message batching to prevent rate limits
    - Intelligent payload interpretation
    - Multi-channel support (Instagram, WhatsApp, Web, etc.)
    - Business workflow integration
    """
    
    def __init__(self):
        self.logger = logger.bind(component="message_handler")
        
        # Track sessions for all channels
        self.sessions = {}
        
        # Register with message batcher 
        message_batcher.add_message_handler(self._handle_batched_message)
        
        self.logger.info(
            "Universal message handler initialized",
            features=["multi_channel", "message_batching", "intelligent_processing"]
        )
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature for security."""
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
    
    async def handle_incoming_message(self, data: Dict[str, Any], source: str = "instagram") -> Dict[str, str]:
        """Handle incoming messages from any source."""
        try:
            self.logger.debug(f"Message received from {source}", entries=len(data.get("entry", [])))
            
            for entry in data.get("entry", []):
                messaging_events = entry.get("messaging", [])
                
                for messaging_event in messaging_events:
                    self.logger.info(
                        "Processing messaging event",
                        source=source,
                        sender_id=messaging_event.get("sender", {}).get("id"),
                        has_message=bool(messaging_event.get("message"))
                    )
                    
                    message = self._parse_messaging_event(messaging_event)
                    if message:
                        # Skip business account messages (prevent loops)
                        if message.sender_id == settings.ig_user_id:
                            self.logger.info("Ignoring business account message")
                            continue
                            
                        await message_batcher.process_message(message)
            
            return {"status": "ok"}
            
        except Exception as e:
            self.logger.error(f"Message handling error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _parse_messaging_event(self, event: Dict[str, Any]) -> Optional[InstagramMessage]:
        """Parse messaging event from any source."""
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
        """Handle batched messages with intelligent business processing."""
        try:
            self.logger.info(
                "Processing customer message with intelligent assistant",
                sender_id=message.sender_id,
                is_batched=batch_info.get("is_batched", False)
            )
            
            # Check for active support tickets (business escalation)
            from services.ticket_management.webhook_interceptor import get_webhook_interceptor
            interceptor = await get_webhook_interceptor()
            intercept_info = await interceptor.should_intercept(message.sender_id)
            
            if intercept_info["should_intercept"]:
                self.logger.info("Message intercepted for active support ticket")
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
            
            # Fetch Instagram user info on first message or if not cached
            if message.sender_id not in self.sessions or 'instagram_info' not in self.sessions[message.sender_id]:
                instagram_info = await fetch_instagram_user_info(message.sender_id)
                if message.sender_id in self.sessions:
                    self.sessions[message.sender_id]['instagram_info'] = instagram_info
                    logger.info(f"📱 Stored Instagram info for user: {instagram_info.get('username', 'unknown')}")
            
            # Prepare message with intelligent interpretation
            message_text = await self._intelligent_message_preparation(message)
            
            if not message_text:
                return
            
            # Process with workflow-compliant healthcare assistant
            response = await process_healthcare_message(
                message=message_text,
                session_id=session_id,
                customer_id=message.sender_id
            )
            
            # Send response
            await self._send_response(message.sender_id, response)
            
        except Exception as e:
            self.logger.error(f"Error processing batched message: {e}", sender_id=message.sender_id)
            
            # Fallback response
            try:
                await send_reply(
                    message.sender_id,
                    "I'm here to help you with our services. How can I assist you today?"
                )
            except Exception as send_error:
                self.logger.error(f"Failed to send fallback message: {send_error}")
    
    def _get_session_id(self, sender_id: str) -> str:
        """Get persistent session ID for conversation tracking."""
        persistent_session_id = f"session_{sender_id}_business"
        
        if sender_id not in self.sessions:
            self.sessions[sender_id] = {
                "session_id": persistent_session_id,
                "created_at": datetime.now(),
                "last_message": datetime.now()
            }
            self.logger.info(f"Created session for {sender_id}: {persistent_session_id}")
        else:
            self.sessions[sender_id]["last_message"] = datetime.now()
        
        return persistent_session_id
    
    async def _intelligent_message_preparation(self, message: InstagramMessage) -> Optional[str]:
        """Prepare message with intelligent quick reply interpretation."""
        if message.quick_reply_payload:
            return await self._interpret_quick_reply(message.quick_reply_payload, message.text)
        
        return message.text
    
    async def _interpret_quick_reply(self, payload: str, original_text: Optional[str]) -> str:
        """Intelligently interpret quick reply payloads using LLM."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import SystemMessage, HumanMessage
            import os
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.1
            )
            
            interpretation_prompt = f"""
            Convert this quick reply payload into natural customer language.
            
            Payload: "{payload}"
            Original text: "{original_text or 'None'}"
            
            Context: Customer clicked a quick reply button in a business conversation.
            Convert the payload to what the customer actually means.
            
            Examples:
            - "BOOK_SERVICE" → "I want to book a service"
            - "GET_REPORT" → "I want to get my report"
            - "YES" → "Yes"
            - "PAY_ONLINE" → "I want to pay online"
            - "COMPLAINT" → "I have a complaint"
            
            Return only the natural language interpretation.
            """
            
            response = llm.invoke([
                SystemMessage(content=interpretation_prompt),
                HumanMessage(content=f"Interpret: {payload}")
            ])
            
            interpreted_message = response.content.strip()
            
            self.logger.info(
                f"Payload interpretation",
                original_payload=payload,
                interpreted_message=interpreted_message
            )
            
            return interpreted_message
            
        except Exception as e:
            self.logger.error(f"Payload interpretation failed: {e}")
            # Fallback to payload as-is
            return payload
    
    def _prepare_message_text(self, message: InstagramMessage) -> Optional[str]:
        """Prepare message text for ticket system compatibility."""
        if message.quick_reply_payload:
            # Basic conversions for ticket system
            basic_conversions = {
                "YES": "Yes",
                "NO": "No",
                "AGENT_HANDOFF": "I want to talk to a human agent"
            }
            return basic_conversions.get(message.quick_reply_payload, message.quick_reply_payload)
        
        return message.text
    
    async def _send_response(self, recipient_id: str, response: Dict[str, Any]):
        """Send response to customer."""
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
                text_length=len(response["text"])
            )
            
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
            
            if "cannot be found" in str(e).lower():
                self.logger.info(f"Customer not found - likely test message: {recipient_id}")
    
    def get_handler_statistics(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            "active_sessions": len(self.sessions),
            "handler_type": "universal_business_assistant",
            "features": ["intelligent_processing", "multi_channel", "business_workflows"],
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


# Global handler instance
message_handler = UniversalMessageHandler()