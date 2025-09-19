"""
Ticket management service for handling support tickets.
"""

import json
import random
import string
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog
import redis.asyncio as aioredis

from .models import SupportTicket, TicketMessage, TicketStatus, TicketPriority, TicketCategory, AgentSession

logger = structlog.get_logger()


class TicketService:
    """Service for managing support tickets."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize ticket service."""
        self.redis_url = redis_url
        self.logger = logger.bind(component="ticket_service")
        self.redis_client = None
    
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = await aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            self.logger.info("Redis connection established for ticket service")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
    
    def generate_ticket_id(self) -> str:
        """Generate unique ticket ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"TKT_{timestamp}_{random_suffix}"
    
    async def create_ticket(
        self,
        session: AsyncSession,
        instagram_id: str,
        subject: str,
        description: str,
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        category: Optional[TicketCategory] = None,
        priority: Optional[TicketPriority] = None,
        property_parcel_id: Optional[str] = None,
        assessment_year: Optional[int] = None,
        assessment_id: Optional[str] = None,
        appeal_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        conversation_context: Optional[Dict] = None
    ) -> SupportTicket:
        """
        Create a new support ticket.
        
        Args:
            session: Database session
            instagram_id: Customer's Instagram ID
            subject: Ticket subject
            description: Detailed description
            customer_name: Customer name
            customer_phone: Customer phone
            category: Ticket category
            priority: Ticket priority
            property_parcel_id: Related property parcel ID
            assessment_year: Related assessment year
            assessment_id: Related assessment ID
            appeal_id: Related appeal ID
            payment_id: Related payment ID
            conversation_context: Previous conversation history
            
        Returns:
            Created ticket
        """
        try:
            ticket_id = self.generate_ticket_id()
            
            # Determine category and priority if not provided
            if not category:
                category = self._determine_category(subject, description)
            
            if not priority:
                priority = self._determine_priority(subject, description, category)
            
            # Create ticket
            ticket = SupportTicket(
                ticket_id=ticket_id,
                instagram_id=instagram_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                subject=subject,
                description=description,
                category=category,
                priority=priority,
                property_parcel_id=property_parcel_id,
                assessment_year=assessment_year,
                assessment_id=assessment_id,
                appeal_id=appeal_id,
                payment_id=payment_id,
                conversation_context=json.dumps(conversation_context) if conversation_context else None,
                status=TicketStatus.OPEN
            )
            
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)
            
            # Store ticket status in Redis for quick access
            if self.redis_client:
                await self.redis_client.setex(
                    f"ticket_status:{instagram_id}",
                    86400,  # 24 hours TTL
                    json.dumps({
                        "ticket_id": ticket_id,
                        "status": TicketStatus.OPEN.value,
                        "created_at": datetime.now().isoformat()
                    })
                )
                
                # Add to active tickets set
                await self.redis_client.sadd("active_tickets", ticket_id)
            
            self.logger.info(
                f"Ticket created successfully",
                ticket_id=ticket_id,
                instagram_id=instagram_id,
                category=category.value if category else None
            )
            
            return ticket
            
        except Exception as e:
            self.logger.error(f"Failed to create ticket: {e}")
            await session.rollback()
            raise
    
    def _determine_category(self, subject: str, description: str) -> TicketCategory:
        """Determine ticket category based on property tax content."""
        content = f"{subject} {description}".lower()

        if any(word in content for word in ["payment", "pay", "bill", "charge", "refund", "money", "installment"]):
            return TicketCategory.PAYMENT_ISSUE
        elif any(word in content for word in ["appeal", "dispute", "challenge", "disagree", "unfair", "contest"]):
            return TicketCategory.APPEAL_PROCESS
        elif any(word in content for word in ["assessment", "assessed", "value", "valuation", "appraisal"]):
            return TicketCategory.ASSESSMENT_QUESTION
        elif any(word in content for word in ["tax", "calculate", "calculation", "rate", "amount", "how much"]):
            return TicketCategory.TAX_CALCULATION
        elif any(word in content for word in ["property", "address", "parcel", "ownership", "deed"]):
            return TicketCategory.PROPERTY_INFO
        elif any(word in content for word in ["exemption", "exempt", "senior", "disabled", "veteran", "homestead"]):
            return TicketCategory.EXEMPTION_REQUEST
        elif any(word in content for word in ["document", "certificate", "copy", "record", "statement"]):
            return TicketCategory.DOCUMENT_REQUEST
        elif any(word in content for word in ["bill", "billing", "invoice", "statement", "notice"]):
            return TicketCategory.BILLING_INQUIRY
        elif any(word in content for word in ["deadline", "extension", "late", "due date", "time"]):
            return TicketCategory.DEADLINE_EXTENSION
        elif any(word in content for word in ["error", "bug", "not working", "technical", "website", "portal"]):
            return TicketCategory.TECHNICAL_ISSUE
        else:
            return TicketCategory.GENERAL_COMPLAINT
    
    def _determine_priority(self, subject: str, description: str, category: TicketCategory) -> TicketPriority:
        """Determine ticket priority based on property tax content and category."""
        content = f"{subject} {description}".lower()

        # High priority categories for property tax
        if category == TicketCategory.DEADLINE_EXTENSION:
            if any(word in content for word in ["tomorrow", "today", "urgent", "deadline"]):
                return TicketPriority.URGENT
            return TicketPriority.HIGH
        elif category == TicketCategory.APPEAL_PROCESS:
            if any(word in content for word in ["deadline", "due", "urgent", "hearing"]):
                return TicketPriority.HIGH
            return TicketPriority.MEDIUM
        elif category == TicketCategory.PAYMENT_ISSUE:
            if any(word in content for word in ["urgent", "immediately", "asap", "penalty", "late fee"]):
                return TicketPriority.URGENT
            return TicketPriority.HIGH

        # Check for urgency keywords
        if any(word in content for word in ["urgent", "emergency", "critical", "asap"]):
            return TicketPriority.URGENT
        elif any(word in content for word in ["important", "soon", "quickly", "deadline"]):
            return TicketPriority.HIGH
        else:
            return TicketPriority.MEDIUM
    
    async def get_ticket(self, session: AsyncSession, ticket_id: str) -> Optional[SupportTicket]:
        """Get ticket by ID."""
        result = await session.execute(
            select(SupportTicket).where(SupportTicket.ticket_id == ticket_id)
        )
        return result.scalar_one_or_none()
    
    async def get_customer_tickets(
        self,
        session: AsyncSession,
        instagram_id: str,
        status: Optional[TicketStatus] = None
    ) -> List[SupportTicket]:
        """Get all tickets for a customer."""
        query = select(SupportTicket).where(SupportTicket.instagram_id == instagram_id)
        
        if status:
            query = query.where(SupportTicket.status == status)
        
        query = query.order_by(SupportTicket.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def update_ticket_status(
        self,
        session: AsyncSession,
        ticket_id: str,
        status: TicketStatus,
        resolution_notes: Optional[str] = None,
        resolved_by: Optional[str] = None
    ) -> bool:
        """Update ticket status."""
        try:
            ticket = await self.get_ticket(session, ticket_id)
            if not ticket:
                return False
            
            ticket.status = status
            ticket.updated_at = datetime.utcnow()
            
            if status == TicketStatus.RESOLVED:
                ticket.resolved_at = datetime.utcnow()
                ticket.resolution_notes = resolution_notes
                ticket.resolved_by = resolved_by
                
                # Remove from active tickets
                if self.redis_client:
                    await self.redis_client.srem("active_tickets", ticket_id)
            
            await session.commit()
            
            # Update Redis cache
            if self.redis_client:
                await self.redis_client.setex(
                    f"ticket_status:{ticket.instagram_id}",
                    86400,
                    json.dumps({
                        "ticket_id": ticket_id,
                        "status": status.value,
                        "updated_at": datetime.now().isoformat()
                    })
                )
            
            self.logger.info(f"Ticket status updated", ticket_id=ticket_id, status=status.value)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update ticket status: {e}")
            await session.rollback()
            return False
    
    async def add_message(
        self,
        session: AsyncSession,
        ticket_id: str,
        sender_type: str,
        message_text: str,
        sender_id: Optional[str] = None,
        sender_name: Optional[str] = None,
        instagram_message_id: Optional[str] = None
    ) -> Optional[TicketMessage]:
        """Add a message to a ticket."""
        try:
            ticket = await self.get_ticket(session, ticket_id)
            if not ticket:
                return None
            
            message = TicketMessage(
                ticket_id=ticket.id,
                sender_type=sender_type,
                sender_id=sender_id,
                sender_name=sender_name,
                message_text=message_text,
                instagram_message_id=instagram_message_id
            )
            
            session.add(message)
            await session.commit()
            await session.refresh(message)
            
            # Broadcast message via Redis for real-time updates
            if self.redis_client:
                await self.redis_client.publish(
                    f"ticket_messages:{ticket_id}",
                    json.dumps({
                        "sender_type": sender_type,
                        "sender_name": sender_name,
                        "message_text": message_text,
                        "created_at": message.created_at.isoformat()
                    })
                )
            
            return message
            
        except Exception as e:
            self.logger.error(f"Failed to add message: {e}")
            await session.rollback()
            return None
    
    async def assign_agent(
        self,
        session: AsyncSession,
        ticket_id: str,
        agent_id: str,
        agent_name: str
    ) -> bool:
        """Assign an agent to a ticket."""
        try:
            ticket = await self.get_ticket(session, ticket_id)
            if not ticket:
                return False
            
            ticket.assigned_agent_id = agent_id
            ticket.assigned_agent_name = agent_name
            ticket.assigned_at = datetime.utcnow()
            ticket.status = TicketStatus.IN_PROGRESS
            
            await session.commit()
            
            self.logger.info(f"Agent assigned to ticket", ticket_id=ticket_id, agent_name=agent_name)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to assign agent: {e}")
            await session.rollback()
            return False
    
    async def check_active_ticket(self, instagram_id: str) -> Optional[Dict[str, Any]]:
        """Check if customer has an active ticket."""
        if not self.redis_client:
            return None
        
        try:
            ticket_data = await self.redis_client.get(f"ticket_status:{instagram_id}")
            if ticket_data:
                data = json.loads(ticket_data)
                if data["status"] in [TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value]:
                    return data
            return None
        except Exception as e:
            self.logger.error(f"Failed to check active ticket: {e}")
            return None
    
    async def get_ticket_messages(
        self,
        session: AsyncSession,
        ticket_id: str,
        limit: int = 50
    ) -> List[TicketMessage]:
        """Get messages for a ticket."""
        ticket = await self.get_ticket(session, ticket_id)
        if not ticket:
            return []
        
        result = await session.execute(
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket.id)
            .order_by(TicketMessage.created_at.desc())
            .limit(limit)
        )
        
        messages = result.scalars().all()
        return list(reversed(messages))  # Return in chronological order


# Global instance
ticket_service = None


async def get_ticket_service() -> TicketService:
    """Get or create ticket service instance."""
    global ticket_service
    
    if ticket_service is None:
        from config.settings import settings
        ticket_service = TicketService(redis_url=settings.redis_url)
        await ticket_service.initialize()
    
    return ticket_service