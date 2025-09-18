"""
Webhook interceptor for handling human agent takeover during active tickets.
"""

import json
from typing import Dict, Any, Optional
import redis.asyncio as aioredis
import structlog
from datetime import datetime

from services.ticket_management.ticket_service import get_ticket_service
from services.persistence.database import get_db_session
from services.messaging.instagram_api import send_reply

logger = structlog.get_logger()


class WebhookInterceptor:
    """
    Intercepts webhook messages to check for active tickets.
    If a ticket is active and being handled by a human agent,
    it bypasses LangGraph and handles the conversation directly.
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        self.logger = logger.bind(component="webhook_interceptor")
    
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = await aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            self.logger.info("Redis connection established for webhook interceptor")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
    
    async def should_intercept(self, instagram_id: str) -> Dict[str, Any]:
        """
        Check if the message should be intercepted by human agent.
        
        Args:
            instagram_id: Customer's Instagram ID
            
        Returns:
            Dict with intercept status and ticket info
        """
        try:
            ticket_service = await get_ticket_service()
            
            # Check for active ticket
            active_ticket = await ticket_service.check_active_ticket(instagram_id)
            
            if active_ticket and active_ticket["status"] in ["open", "in_progress"]:
                self.logger.info(
                    f"Active ticket found for customer",
                    instagram_id=instagram_id,
                    ticket_id=active_ticket["ticket_id"]
                )
                
                return {
                    "should_intercept": True,
                    "ticket_id": active_ticket["ticket_id"],
                    "status": active_ticket["status"]
                }
            
            return {"should_intercept": False}
            
        except Exception as e:
            self.logger.error(f"Error checking for active ticket: {e}")
            return {"should_intercept": False}
    
    async def handle_customer_message(
        self,
        instagram_id: str,
        message_text: str,
        ticket_id: str,
        customer_name: Optional[str] = None
    ) -> bool:
        """
        Handle customer message when ticket is active.
        Store it and notify connected agents via WebSocket.
        
        Args:
            instagram_id: Customer's Instagram ID
            message_text: Customer's message
            ticket_id: Active ticket ID
            customer_name: Customer's name
            
        Returns:
            Success status
        """
        try:
            async with get_db_session() as db:
                ticket_service = await get_ticket_service()
                
                # Add message to ticket
                await ticket_service.add_message(
                    db,
                    ticket_id,
                    sender_type="customer",
                    message_text=message_text,
                    sender_id=instagram_id,
                    sender_name=customer_name
                )
                
                # Broadcast to connected agents via Redis pub/sub
                if self.redis_client:
                    await self.redis_client.publish(
                        f"ticket_messages:{ticket_id}",
                        json.dumps({
                            "type": "customer_message",
                            "customer_name": customer_name or "Customer",
                            "message": message_text,
                            "timestamp": datetime.now().isoformat()
                        })
                    )
                
                self.logger.info(
                    f"Customer message added to ticket",
                    ticket_id=ticket_id,
                    instagram_id=instagram_id
                )
                
                # Check if there's a pending agent response
                agent_response = await self.get_agent_response(instagram_id)
                if not agent_response:
                    # Send acknowledgment to customer
                    await send_reply(
                        instagram_id,
                        f"Your message has been received. A support agent is reviewing your ticket {ticket_id}. Please wait for their response."
                    )
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error handling customer message: {e}")
            return False
    
    async def get_agent_response(self, instagram_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if there's a pending agent response for the customer.
        
        Args:
            instagram_id: Customer's Instagram ID
            
        Returns:
            Agent response data if available
        """
        if not self.redis_client:
            return None
        
        try:
            key = f"agent_response:{instagram_id}"
            response_data = await self.redis_client.get(key)
            
            if response_data:
                # Delete the key after fetching
                await self.redis_client.delete(key)
                return json.loads(response_data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting agent response: {e}")
            return None
    
    async def send_agent_response(
        self,
        instagram_id: str,
        ticket_id: str
    ) -> bool:
        """
        Send pending agent response to customer via Instagram.
        
        Args:
            instagram_id: Customer's Instagram ID
            ticket_id: Ticket ID
            
        Returns:
            Success status
        """
        try:
            response_data = await self.get_agent_response(instagram_id)
            
            if response_data:
                # Send message to customer
                await send_reply(
                    instagram_id,
                    response_data["message"]
                )
                
                # Log the message in database
                async with get_db_session() as db:
                    ticket_service = await get_ticket_service()
                    await ticket_service.add_message(
                        db,
                        ticket_id,
                        sender_type="agent",
                        message_text=response_data["message"],
                        sender_name=response_data.get("agent_name", "Support Agent")
                    )
                
                self.logger.info(
                    f"Agent response sent to customer",
                    instagram_id=instagram_id,
                    ticket_id=ticket_id
                )
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error sending agent response: {e}")
            return False


# Global instance
interceptor = None


async def get_webhook_interceptor() -> WebhookInterceptor:
    """Get or create webhook interceptor instance."""
    global interceptor
    
    if interceptor is None:
        from config.settings import settings
        interceptor = WebhookInterceptor(redis_url=settings.redis_url)
        await interceptor.initialize()
    
    return interceptor