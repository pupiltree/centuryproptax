"""
Ticket management system for handling support tickets.
"""

from .models import (
    SupportTicket,
    TicketMessage,
    AgentSession,
    TicketStatus,
    TicketPriority,
    TicketCategory
)

from .ticket_service import (
    TicketService,
    get_ticket_service
)

from .webhook_interceptor import (
    WebhookInterceptor,
    get_webhook_interceptor
)

__all__ = [
    # Models
    "SupportTicket",
    "TicketMessage",
    "AgentSession",
    "TicketStatus",
    "TicketPriority",
    "TicketCategory",
    
    # Services
    "TicketService",
    "get_ticket_service",
    "WebhookInterceptor",
    "get_webhook_interceptor",
]