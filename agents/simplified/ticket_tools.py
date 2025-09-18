"""
Support ticket tools for the booking agent.
"""

from typing import Dict, Any
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
import structlog
import asyncio
from datetime import datetime

logger = structlog.get_logger()


class CreateTicketInput(BaseModel):
    """Input for creating a support ticket."""
    instagram_id: str = Field(description="Customer's Instagram ID")
    subject: str = Field(description="Brief subject of the issue")
    description: str = Field(description="Detailed description of the issue")
    customer_name: str = Field(default=None, description="Customer's name")
    customer_phone: str = Field(default=None, description="Customer's phone number")
    order_id: str = Field(default=None, description="Related order ID if applicable")
    payment_id: str = Field(default=None, description="Related payment ID if applicable")
    context: str = Field(default=None, description="Conversation context or additional information")


async def create_support_ticket_async(
    instagram_id: str,
    subject: str,
    description: str,
    customer_name: str = None,
    customer_phone: str = None,
    order_id: str = None,
    payment_id: str = None,
    context: str = None
) -> Dict[str, Any]:
    """
    Create a support ticket for customer complaints or issues.
    
    Args:
        instagram_id: Customer's Instagram ID
        subject: Brief subject of the issue
        description: Detailed description
        customer_name: Customer's name
        customer_phone: Customer's phone
        order_id: Related order ID
        payment_id: Related payment ID
        context: Additional context
        
    Returns:
        Ticket creation result
    """
    try:
        from services.ticket_management.ticket_service import get_ticket_service
        from services.ticket_management.models import TicketCategory, TicketPriority
        from services.persistence.database import get_db_session
        
        # Get ticket service
        ticket_service = await get_ticket_service()
        
        # Parse context if provided
        conversation_context = None
        if context:
            conversation_context = {
                "summary": context,
                "timestamp": datetime.now().isoformat()
            }
        
        # Create ticket in database
        async with get_db_session() as session:
            ticket = await ticket_service.create_ticket(
                session=session,
                instagram_id=instagram_id,
                subject=subject,
                description=description,
                customer_name=customer_name,
                customer_phone=customer_phone,
                order_id=order_id,
                payment_id=payment_id,
                conversation_context=conversation_context
            )
            
            # Add initial message from customer
            await ticket_service.add_message(
                session=session,
                ticket_id=ticket.ticket_id,
                sender_type="customer",
                message_text=description,
                sender_id=instagram_id,
                sender_name=customer_name
            )
            
            logger.info(
                f"Support ticket created",
                ticket_id=ticket.ticket_id,
                category=ticket.category.value if ticket.category else None,
                priority=ticket.priority.value if ticket.priority else None
            )
            
            return {
                "success": True,
                "ticket_id": ticket.ticket_id,
                "message": f"Support ticket {ticket.ticket_id} has been created. Our team will review this {ticket.priority.value if ticket.priority else 'medium'} priority issue and contact you shortly.",
                "category": ticket.category.value if ticket.category else "general",
                "priority": ticket.priority.value if ticket.priority else "medium",
                "status": "open"
            }
            
    except Exception as e:
        logger.error(f"Failed to create support ticket: {e}")
        return {
            "success": False,
            "message": "I apologize, but I couldn't create a support ticket at this moment. Please try again or contact our support directly.",
            "error": str(e)
        }


def create_support_ticket(
    instagram_id: str,
    subject: str,
    description: str,
    customer_name: str = None,
    customer_phone: str = None,
    order_id: str = None,
    payment_id: str = None,
    context: str = None
) -> Dict[str, Any]:
    """Sync wrapper for create_support_ticket_async."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        create_support_ticket_async(
            instagram_id=instagram_id,
            subject=subject,
            description=description,
            customer_name=customer_name,
            customer_phone=customer_phone,
            order_id=order_id,
            payment_id=payment_id,
            context=context
        )
    )


# Create the tool
create_ticket_tool = StructuredTool.from_function(
    func=create_support_ticket,
    name="create_support_ticket",
    description="""Create a support ticket when a customer has a complaint or issue that needs human assistance.
    Use this for:
    - Payment issues (wrong amount debited, refund requests)
    - Booking problems
    - Technical issues
    - General complaints
    - Any issue that requires human intervention
    
    This will create a trackable ticket and assign it to a human agent.""",
    args_schema=CreateTicketInput
)


class CheckTicketStatusInput(BaseModel):
    """Input for checking ticket status."""
    instagram_id: str = Field(description="Customer's Instagram ID")
    ticket_id: str = Field(default=None, description="Specific ticket ID to check")


async def check_ticket_status_async(
    instagram_id: str,
    ticket_id: str = None
) -> Dict[str, Any]:
    """
    Check the status of a support ticket.
    
    Args:
        instagram_id: Customer's Instagram ID
        ticket_id: Specific ticket ID (optional)
        
    Returns:
        Ticket status information
    """
    try:
        from services.ticket_management.ticket_service import get_ticket_service
        from services.persistence.database import get_db_session
        
        ticket_service = await get_ticket_service()
        
        # Check for active ticket in Redis first
        active_ticket = await ticket_service.check_active_ticket(instagram_id)
        
        if active_ticket:
            return {
                "success": True,
                "has_active_ticket": True,
                "ticket_id": active_ticket["ticket_id"],
                "status": active_ticket["status"],
                "message": f"You have an active support ticket {active_ticket['ticket_id']} which is currently {active_ticket['status']}."
            }
        
        # If specific ticket requested, check database
        if ticket_id:
            async with get_db_session() as session:
                ticket = await ticket_service.get_ticket(session, ticket_id)
                if ticket and ticket.instagram_id == instagram_id:
                    return {
                        "success": True,
                        "has_active_ticket": ticket.status.value in ["open", "in_progress"],
                        "ticket_id": ticket.ticket_id,
                        "status": ticket.status.value,
                        "message": f"Ticket {ticket.ticket_id} is currently {ticket.status.value}."
                    }
        
        return {
            "success": True,
            "has_active_ticket": False,
            "message": "You don't have any active support tickets."
        }
        
    except Exception as e:
        logger.error(f"Failed to check ticket status: {e}")
        return {
            "success": False,
            "message": "I couldn't check the ticket status at this moment.",
            "error": str(e)
        }


def check_ticket_status(
    instagram_id: str,
    ticket_id: str = None
) -> Dict[str, Any]:
    """Sync wrapper for check_ticket_status_async."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        check_ticket_status_async(
            instagram_id=instagram_id,
            ticket_id=ticket_id
        )
    )


# Create the tool
check_ticket_tool = StructuredTool.from_function(
    func=check_ticket_status,
    name="check_ticket_status",
    description="Check if the customer has any active support tickets or check the status of a specific ticket.",
    args_schema=CheckTicketStatusInput
)