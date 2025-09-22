"""
WhatsApp Business Cloud API Client for Century Property Tax
Handles sending and receiving messages via WhatsApp Business API.
"""

import os
import asyncio
import json
from typing import Dict, Any, Optional, List
import aiohttp
import structlog
from datetime import datetime
from src.core.logging import get_logger

logger = get_logger("whatsapp_client")

class WhatsAppClient:
    """WhatsApp Business Cloud API client for sending and receiving messages."""
    
    def __init__(self):
        self.logger = logger

        # WhatsApp Business API configuration
        self.phone_number_id = os.getenv("WA_PHONE_NUMBER_ID", "668229953048351")
        self.business_account_id = os.getenv("WA_BUSINESS_ACCOUNT_ID", "2150712978774203")
        self.access_token = os.getenv("WA_ACCESS_TOKEN")
        self.verify_token = os.getenv("WA_VERIFY_TOKEN", "century_whatsapp_webhook_secure_2024")

        # Business API enhanced configuration
        self.app_id = os.getenv("WA_APP_ID")
        self.app_secret = os.getenv("WA_APP_SECRET")
        self.business_phone_number = os.getenv("WA_BUSINESS_PHONE_NUMBER")

        # API endpoints
        self.base_url = "https://graph.facebook.com/v20.0"
        self.messages_url = f"{self.base_url}/{self.phone_number_id}/messages"
        self.templates_url = f"{self.base_url}/{self.business_account_id}/message_templates"
        self.phone_url = f"{self.base_url}/{self.phone_number_id}"

        # Request session
        self.session = None

        # Rate limiting
        self.rate_limit_tier = os.getenv("WA_RATE_LIMIT_TIER", "1")  # Default tier 1
        self.messaging_limit = self._get_messaging_limit()

        if not self.access_token:
            self.logger.warning("WhatsApp access token not configured - messages will not be sent")

        self.logger.info(
            "WhatsApp Business API client initialized",
            phone_number_id=self.phone_number_id,
            business_account_id=self.business_account_id,
            business_phone=self.business_phone_number,
            rate_limit_tier=self.rate_limit_tier
        )
    
    async def _get_session(self):
        """Get or create aiohttp session."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    def _get_messaging_limit(self) -> int:
        """Get messaging limit based on rate limit tier."""
        limits = {
            "1": 1000,    # 1,000 conversations per day
            "2": 10000,   # 10,000 conversations per day
            "3": 100000,  # 100,000 conversations per day
            "4": 1000000  # 1,000,000 conversations per day
        }
        return limits.get(self.rate_limit_tier, 1000)
    
    def is_configured(self) -> bool:
        """Check if WhatsApp client is properly configured."""
        return bool(self.access_token and self.phone_number_id)
    
    async def send_text_message(self, to: str, message: str) -> Dict[str, Any]:
        """
        Send a text message via WhatsApp Business API.
        
        Args:
            to: Recipient phone number (with country code, no +)
            message: Message text content
            
        Returns:
            Dict with success status and response data
        """
        if not self.is_configured():
            self.logger.error("WhatsApp client not configured - cannot send message")
            return {
                "success": False,
                "error": "WhatsApp client not configured",
                "reason": "missing_access_token"
            }
        
        try:
            # Prepare message payload
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": message
                }
            }
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            message_type = "text"  # Define message type based on payload
            self.logger.info(
                "Sending WhatsApp message",
                log_event="message_send_request",
                recipient=f"{to[:5]}***",
                message_type=message_type
            )
            
            session = await self._get_session()
            async with session.post(
                self.messages_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    self.logger.info(
                        "WhatsApp message sent successfully",
                        log_event="message_sent",
                        recipient=f"{to[:5]}***",
                        message_id=response_data.get('messages', [{}])[0].get('id', 'unknown')
                    )
                    return {
                        "success": True,
                        "message_id": response_data.get("messages", [{}])[0].get("id"),
                        "response": response_data
                    }
                else:
                    self.logger.error(
                        "WhatsApp API error",
                        log_event="api_error",
                        status_code=response.status,
                        error_details=response_data,
                        recipient=f"{to[:5]}***"
                    )
                    return {
                        "success": False,
                        "error": f"WhatsApp API error: {response.status}",
                        "details": response_data,
                        "status_code": response.status
                    }
                    
        except asyncio.TimeoutError:
            self.logger.error("WhatsApp API request timeout")
            return {
                "success": False,
                "error": "Request timeout",
                "reason": "api_timeout"
            }
        except Exception as e:
            self.logger.error(f"WhatsApp send error: {e}")
            return {
                "success": False,
                "error": str(e),
                "reason": "send_exception"
            }
    
    def verify_webhook(self, verify_token: str, challenge: str) -> Optional[str]:
        """
        Verify WhatsApp webhook challenge.
        
        Args:
            verify_token: Token sent by WhatsApp
            challenge: Challenge string to return
            
        Returns:
            Challenge string if verification succeeds, None otherwise
        """
        if verify_token == self.verify_token:
            self.logger.info("WhatsApp webhook verification successful")
            return challenge
        else:
            self.logger.warning(f"WhatsApp webhook verification failed: {verify_token}")
            return None
    
    def parse_webhook_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse WhatsApp webhook message data.
        
        Args:
            webhook_data: Raw webhook payload
            
        Returns:
            Parsed message data or None if not a message
        """
        try:
            # Check if this is a WhatsApp business account event
            if webhook_data.get("object") != "whatsapp_business_account":
                return None
            
            # Extract entry data
            entries = webhook_data.get("entry", [])
            if not entries:
                return None
            
            entry = entries[0]
            changes = entry.get("changes", [])
            if not changes:
                return None
            
            change = changes[0]
            value = change.get("value", {})
            
            # Check if this is a message event
            if "messages" not in value:
                self.logger.debug("WhatsApp webhook: Not a message event")
                return None
            
            messages = value.get("messages", [])
            if not messages:
                return None
            
            message = messages[0]
            contacts = value.get("contacts", [{}])
            contact = contacts[0] if contacts else {}
            
            # Extract message details
            parsed_message = {
                "id": message.get("id"),
                "from": message.get("from"),
                "timestamp": message.get("timestamp"),
                "type": message.get("type"),
                "phone_number_id": value.get("metadata", {}).get("phone_number_id"),
                "contact_name": contact.get("profile", {}).get("name", "Unknown"),
                "raw_webhook": webhook_data
            }
            
            # Extract message content based on type
            if message.get("type") == "text":
                parsed_message["text"] = message.get("text", {}).get("body", "")
            elif message.get("type") == "image":
                parsed_message["image"] = message.get("image", {})
            elif message.get("type") == "document":
                parsed_message["document"] = message.get("document", {})
            elif message.get("type") == "audio":
                parsed_message["audio"] = message.get("audio", {})
            elif message.get("type") == "video":
                parsed_message["video"] = message.get("video", {})
            elif message.get("type") == "location":
                parsed_message["location"] = message.get("location", {})
            elif message.get("type") == "contacts":
                parsed_message["contacts"] = message.get("contacts", [])
            elif message.get("type") == "interactive":
                # Parse interactive message (button clicks, list selections)
                interactive = message.get("interactive", {})
                parsed_message["interactive"] = interactive

                # Extract the actual interaction data for easy access
                if "button_reply" in interactive:
                    button_reply = interactive["button_reply"]
                    parsed_message["text"] = f"Button: {button_reply.get('title', button_reply.get('id', 'Unknown'))}"
                elif "list_reply" in interactive:
                    list_reply = interactive["list_reply"]
                    parsed_message["text"] = f"Selected: {list_reply.get('title', list_reply.get('id', 'Unknown'))}"
            
            self.logger.info(f"Parsed WhatsApp message from {parsed_message['from'][:5]}*** ({parsed_message['type']})")
            return parsed_message
            
        except Exception as e:
            self.logger.error(f"Error parsing WhatsApp webhook: {e}")
            return None
    
    def parse_status_update(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse WhatsApp status update webhook.
        
        Args:
            webhook_data: Raw webhook payload
            
        Returns:
            Parsed status data or None
        """
        try:
            if webhook_data.get("object") != "whatsapp_business_account":
                return None
            
            entries = webhook_data.get("entry", [])
            if not entries:
                return None
            
            entry = entries[0]
            changes = entry.get("changes", [])
            if not changes:
                return None
            
            change = changes[0]
            value = change.get("value", {})
            
            # Check if this is a status event
            if "statuses" not in value:
                return None
            
            statuses = value.get("statuses", [])
            if not statuses:
                return None
            
            status = statuses[0]
            
            parsed_status = {
                "id": status.get("id"),
                "recipient_id": status.get("recipient_id"),
                "status": status.get("status"),  # sent, delivered, read, failed
                "timestamp": status.get("timestamp"),
                "phone_number_id": value.get("metadata", {}).get("phone_number_id")
            }
            
            # Add pricing info if available
            if "pricing" in status:
                parsed_status["pricing"] = status["pricing"]
            
            # Add error info for failed messages
            if status.get("status") == "failed" and "errors" in status:
                parsed_status["errors"] = status["errors"]
            
            self.logger.info(f"Parsed WhatsApp status: {parsed_status['id']} -> {parsed_status['status']}")
            return parsed_status
            
        except Exception as e:
            self.logger.error(f"Error parsing WhatsApp status: {e}")
            return None

    async def get_business_profile(self) -> Dict[str, Any]:
        """Get business profile information."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "WhatsApp client not configured"
            }

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            session = await self._get_session()
            async with session.get(
                f"{self.phone_url}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_data = await response.json()

                if response.status == 200:
                    self.logger.info("Business profile retrieved successfully")
                    return {
                        "success": True,
                        "profile": response_data
                    }
                else:
                    self.logger.error(f"Failed to get business profile: {response.status} - {response_data}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "details": response_data
                    }

        except Exception as e:
            self.logger.error(f"Error getting business profile: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def update_business_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update business profile information."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "WhatsApp client not configured"
            }

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            session = await self._get_session()
            async with session.post(
                f"{self.phone_url}",
                headers=headers,
                json=profile_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_data = await response.json()

                if response.status == 200:
                    self.logger.info("Business profile updated successfully")
                    return {
                        "success": True,
                        "response": response_data
                    }
                else:
                    self.logger.error(f"Failed to update business profile: {response.status} - {response_data}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "details": response_data
                    }

        except Exception as e:
            self.logger.error(f"Error updating business profile: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def send_template_message(self, to: str, template_name: str, language_code: str = "en_US",
                                   components: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Send a pre-approved template message.

        Args:
            to: Recipient phone number
            template_name: Name of the approved template
            language_code: Language code (default: en_US)
            components: Template components (parameters, buttons, etc.)
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "WhatsApp client not configured"
            }

        try:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    }
                }
            }

            if components:
                payload["template"]["components"] = components

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            self.logger.info(f"Sending WhatsApp template message to {to[:5]}***", template_name=template_name)

            session = await self._get_session()
            async with session.post(
                self.messages_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_data = await response.json()

                if response.status == 200:
                    self.logger.info(f"Template message sent successfully to {to[:5]}***")
                    return {
                        "success": True,
                        "message_id": response_data.get("messages", [{}])[0].get("id"),
                        "response": response_data
                    }
                else:
                    self.logger.error(f"WhatsApp template API error: {response.status} - {response_data}")
                    return {
                        "success": False,
                        "error": f"WhatsApp API error: {response.status}",
                        "details": response_data
                    }

        except Exception as e:
            self.logger.error(f"WhatsApp template send error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_message_templates(self) -> Dict[str, Any]:
        """Get list of approved message templates."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "WhatsApp client not configured"
            }

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            session = await self._get_session()
            async with session.get(
                self.templates_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_data = await response.json()

                if response.status == 200:
                    templates = response_data.get("data", [])
                    self.logger.info(f"Retrieved {len(templates)} message templates")
                    return {
                        "success": True,
                        "templates": templates,
                        "count": len(templates)
                    }
                else:
                    self.logger.error(f"Failed to get templates: {response.status} - {response_data}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "details": response_data
                    }

        except Exception as e:
            self.logger.error(f"Error getting templates: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature using app secret for enhanced security.

        Args:
            payload: Raw webhook payload
            signature: X-Hub-Signature-256 header value
        """
        if not self.app_secret or not signature:
            self.logger.warning("App secret or signature missing - signature verification skipped")
            return True  # Allow if not configured for backward compatibility

        try:
            import hmac
            import hashlib

            # Remove 'sha256=' prefix if present
            signature = signature.replace('sha256=', '')

            # Generate expected signature
            expected = hmac.new(
                self.app_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()

            # Secure comparison
            is_valid = hmac.compare_digest(expected, signature)

            if is_valid:
                self.logger.debug("Webhook signature verification successful")
            else:
                self.logger.warning("Webhook signature verification failed")

            return is_valid

        except Exception as e:
            self.logger.error(f"Signature verification error: {e}")
            return False

    async def send_interactive_message(self, to: str, interactive_type: str,
                                     interactive_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send interactive message (buttons, lists, etc.).

        Args:
            to: Recipient phone number
            interactive_type: Type of interactive message (button, list, etc.)
            interactive_data: Interactive message data
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "WhatsApp client not configured"
            }

        try:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": interactive_type,
                    **interactive_data
                }
            }

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            self.logger.info(f"Sending interactive message to {to[:5]}***", interactive_type=interactive_type)

            session = await self._get_session()
            async with session.post(
                self.messages_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_data = await response.json()

                if response.status == 200:
                    self.logger.info(f"Interactive message sent successfully to {to[:5]}***")
                    return {
                        "success": True,
                        "message_id": response_data.get("messages", [{}])[0].get("id"),
                        "response": response_data
                    }
                else:
                    self.logger.error(f"Interactive message API error: {response.status} - {response_data}")
                    return {
                        "success": False,
                        "error": f"WhatsApp API error: {response.status}",
                        "details": response_data
                    }

        except Exception as e:
            self.logger.error(f"Interactive message send error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_business_configuration(self) -> Dict[str, Any]:
        """Get current business configuration."""
        return {
            "phone_number_id": self.phone_number_id,
            "business_account_id": self.business_account_id,
            "business_phone_number": self.business_phone_number,
            "app_id": self.app_id,
            "rate_limit_tier": self.rate_limit_tier,
            "messaging_limit": self.messaging_limit,
            "is_configured": self.is_configured(),
            "webhook_security_enabled": bool(self.app_secret)
        }


# Global WhatsApp client instance
_whatsapp_client = None

def get_whatsapp_client() -> WhatsAppClient:
    """Get global WhatsApp client instance."""
    global _whatsapp_client
    if _whatsapp_client is None:
        _whatsapp_client = WhatsAppClient()
    return _whatsapp_client

async def cleanup_whatsapp_client():
    """Cleanup global WhatsApp client."""
    global _whatsapp_client
    if _whatsapp_client:
        await _whatsapp_client.close()
        _whatsapp_client = None