"""
Ticket management system database models.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from services.persistence.database import Base


class TicketStatus(str, Enum):
    """Ticket status enumeration."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Ticket priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketCategory(str, Enum):
    """Property tax ticket category enumeration."""
    ASSESSMENT_QUESTION = "assessment_question"
    PAYMENT_ISSUE = "payment_issue"
    APPEAL_PROCESS = "appeal_process"
    TAX_CALCULATION = "tax_calculation"
    PROPERTY_INFO = "property_info"
    EXEMPTION_REQUEST = "exemption_request"
    DOCUMENT_REQUEST = "document_request"
    BILLING_INQUIRY = "billing_inquiry"
    DEADLINE_EXTENSION = "deadline_extension"
    TECHNICAL_ISSUE = "technical_issue"
    GENERAL_COMPLAINT = "general_complaint"
    OTHER = "other"


class SupportTicket(Base):
    """Support ticket model."""
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # Customer information
    instagram_id = Column(String(100), index=True, nullable=False)
    customer_name = Column(String(200))
    customer_phone = Column(String(20))
    customer_email = Column(String(200))
    
    # Ticket details
    category = Column(SQLEnum(TicketCategory), default=TicketCategory.OTHER)
    priority = Column(SQLEnum(TicketPriority), default=TicketPriority.MEDIUM)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.OPEN, index=True)
    
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    # Property tax context from bot conversation
    property_parcel_id = Column(String(50))
    assessment_year = Column(Integer)
    assessment_id = Column(String(50))
    appeal_id = Column(String(50))
    payment_id = Column(String(100))
    conversation_context = Column(Text)  # JSON string of conversation history
    
    # Agent assignment
    assigned_agent_id = Column(String(100))
    assigned_agent_name = Column(String(200))
    assigned_at = Column(DateTime)
    
    # Resolution details
    resolution_notes = Column(Text)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(200))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert ticket to dictionary."""
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "instagram_id": self.instagram_id,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "category": self.category.value if self.category else None,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "subject": self.subject,
            "description": self.description,
            "order_id": self.order_id,
            "payment_id": self.payment_id,
            "assigned_agent_name": self.assigned_agent_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "message_count": len(self.messages) if self.messages else 0
        }


class TicketMessage(Base):
    """Messages within a support ticket."""
    __tablename__ = "ticket_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    
    # Message details
    sender_type = Column(String(20), nullable=False)  # "customer", "agent", "bot"
    sender_id = Column(String(100))
    sender_name = Column(String(200))
    
    message_text = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # "text", "image", "file"
    
    # For tracking Instagram messages
    instagram_message_id = Column(String(200))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    ticket = relationship("SupportTicket", back_populates="messages")
    
    def to_dict(self):
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "sender_type": self.sender_type,
            "sender_name": self.sender_name,
            "message_text": self.message_text,
            "message_type": self.message_type,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class AgentSession(Base):
    """Track agent sessions for handling tickets."""
    __tablename__ = "agent_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    
    agent_id = Column(String(100), nullable=False)
    agent_name = Column(String(200))
    
    ticket_id = Column(String(50), ForeignKey("support_tickets.ticket_id"))
    instagram_id = Column(String(100))  # Customer's Instagram ID
    
    is_active = Column(Boolean, default=True)
    
    # WebSocket connection info
    websocket_connected = Column(Boolean, default=False)
    last_ping = Column(DateTime)
    
    # Session timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime)
    
    def to_dict(self):
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "ticket_id": self.ticket_id,
            "instagram_id": self.instagram_id,
            "is_active": self.is_active,
            "websocket_connected": self.websocket_connected,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None
        }