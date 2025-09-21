"""
Database models and operations for Century Property Tax.
SQLAlchemy async models for customer data, property assessments, and tax records.
"""

import asyncio
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum

import structlog
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    Numeric, Date, JSON, ForeignKey, Index, UniqueConstraint, Float,
    Enum as SQLEnum, Table
)
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from src.core.logging import get_logger

logger = get_logger("database_manager")


class PropertyType(str, Enum):
    """Property type enumeration."""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    AGRICULTURAL = "agricultural"
    VACANT_LAND = "vacant_land"
    MIXED_USE = "mixed_use"


class ZoningType(str, Enum):
    """Zoning type enumeration."""
    RESIDENTIAL_SINGLE = "residential_single"
    RESIDENTIAL_MULTI = "residential_multi"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    AGRICULTURAL = "agricultural"
    MIXED_USE = "mixed_use"
    PUBLIC = "public"


class OwnershipType(str, Enum):
    """Ownership type enumeration."""
    SOLE = "sole"
    JOINT = "joint"
    TENANT_COMMON = "tenant_common"
    TRUST = "trust"
    CORPORATION = "corporation"
    LLC = "llc"


class AppealStatus(str, Enum):
    """Appeal status enumeration."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    EVIDENCE_REQUESTED = "evidence_requested"
    SCHEDULED_HEARING = "scheduled_hearing"
    DECISION_PENDING = "decision_pending"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"


class AppealReason(str, Enum):
    """Appeal reason enumeration."""
    OVERVALUATION = "overvaluation"
    INCORRECT_PROPERTY_DATA = "incorrect_property_data"
    UNEQUAL_ASSESSMENT = "unequal_assessment"
    EXEMPTION_DENIED = "exemption_denied"
    CLASSIFICATION_ERROR = "classification_error"
    CALCULATION_ERROR = "calculation_error"
    OTHER = "other"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL = "partial"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ACH = "ach"
    WIRE_TRANSFER = "wire_transfer"
    MONEY_ORDER = "money_order"
    ONLINE_PORTAL = "online_portal"


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class CustomerProfile(Base):
    """Customer profile for property owners and taxpayers."""

    __tablename__ = "customer_profiles"

    # Primary identification
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    whatsapp_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    # Personal information
    name: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    email: Mapped[Optional[str]] = mapped_column(String(200))

    # Property ownership information
    owned_properties: Mapped[Optional[List[str]]] = mapped_column(JSON)  # List of parcel IDs
    primary_property_parcel: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    is_property_owner: Mapped[bool] = mapped_column(Boolean, default=True)
    property_ownership_type: Mapped[Optional[str]] = mapped_column(String(50))  # sole, joint, business

    # Location and preferences
    zip_code: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    county: Mapped[Optional[str]] = mapped_column(String(100))
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    preferred_contact_method: Mapped[str] = mapped_column(String(20), default="instagram")  # instagram, email, phone, mail
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)

    # Communication preferences
    receive_tax_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    receive_assessment_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    receive_appeal_updates: Mapped[bool] = mapped_column(Boolean, default=True)
    receive_payment_confirmations: Mapped[bool] = mapped_column(Boolean, default=True)

    # Conversation tracking
    last_interaction: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    conversation_count: Mapped[int] = mapped_column(Integer, default=0)

    # Business Intelligence & Analytics for Property Tax
    total_property_assessments: Mapped[int] = mapped_column(Integer, default=0)
    total_tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)  # Total annual tax liability
    average_response_time: Mapped[Optional[int]] = mapped_column(Integer)  # in minutes
    last_activity_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    inquiry_to_resolution_rate: Mapped[Optional[float]] = mapped_column(Float)  # inquiries to successful resolutions
    customer_satisfaction_score: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 rating

    # Property tax specific metrics
    appeals_filed_count: Mapped[int] = mapped_column(Integer, default=0)
    successful_appeals_count: Mapped[int] = mapped_column(Integer, default=0)
    payment_timeliness_score: Mapped[Optional[int]] = mapped_column(Integer)  # 1-100, payment history
    last_payment_date: Mapped[Optional[date]] = mapped_column(Date)

    # Support and service tracking
    total_inquiries_count: Mapped[int] = mapped_column(Integer, default=0)
    resolved_inquiries_count: Mapped[int] = mapped_column(Integer, default=0)
    open_tickets_count: Mapped[int] = mapped_column(Integer, default=0)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    assessment_requests: Mapped[List["PropertyAssessmentRequest"]] = relationship("PropertyAssessmentRequest", back_populates="customer")
    messages: Mapped[List["MessageHistory"]] = relationship("MessageHistory", back_populates="customer")

    __table_args__ = (
        Index("idx_customer_phone_zip", "phone", "zip_code"),
        Index("idx_customer_last_interaction", "last_interaction"),
        Index("idx_customer_primary_property", "primary_property_parcel"),
    )


class PropertyAssessmentService(Base):
    """Property tax assessment services and fee catalog."""

    __tablename__ = "property_assessment_services"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Service identification
    service_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)  # assessment_appeal, document_request, certification

    # Service details
    description: Mapped[Optional[str]] = mapped_column(Text)
    requirements: Mapped[Optional[List[str]]] = mapped_column(JSON)  # List of required documents/info
    processing_time: Mapped[Optional[str]] = mapped_column(String(100))  # "5-10 business days"

    # Pricing
    fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    rush_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    # Availability
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    online_available: Mapped[bool] = mapped_column(Boolean, default=True)
    in_person_required: Mapped[bool] = mapped_column(Boolean, default=False)

    # Property type applicability
    property_types_applicable: Mapped[Optional[List[str]]] = mapped_column(JSON)
    deadlines: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Seasonal deadlines, etc.

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    requests: Mapped[List["PropertyAssessmentRequest"]] = relationship("PropertyAssessmentRequest", back_populates="service")

    __table_args__ = (
        Index("idx_service_category_fee", "category", "fee"),
        Index("idx_service_available", "available", "category"),
    )


class PropertyAssessmentRequest(Base):
    """Property assessment and service requests from customers."""

    __tablename__ = "property_assessment_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Request identification
    request_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    # Relationships
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer_profiles.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("property_assessment_services.id"), nullable=False)
    property_parcel_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)

    # Request details
    request_type: Mapped[str] = mapped_column(String(50), index=True)  # appeal, document_request, assessment_review
    description: Mapped[str] = mapped_column(Text, nullable=False)
    urgency_level: Mapped[str] = mapped_column(String(20), default="normal")  # low, normal, high, urgent

    # Scheduling
    preferred_date: Mapped[Optional[date]] = mapped_column(Date)
    preferred_time: Mapped[Optional[str]] = mapped_column(String(20))
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Service delivery
    delivery_method: Mapped[str] = mapped_column(String(20), default="online")  # online, mail, pickup
    delivery_address: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Request status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    # pending, under_review, additional_info_needed, approved, denied, completed, cancelled

    # Payment
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    payment_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Property context
    property_address: Mapped[Optional[str]] = mapped_column(String(500))
    assessment_year: Mapped[Optional[int]] = mapped_column(Integer)
    current_assessed_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    # Documents and attachments
    supporting_documents: Mapped[Optional[List[str]]] = mapped_column(JSON)  # List of document paths
    document_requirements_met: Mapped[bool] = mapped_column(Boolean, default=False)

    # Communication
    special_instructions: Mapped[Optional[str]] = mapped_column(Text)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(200))

    # Completion details
    resolution_date: Mapped[Optional[date]] = mapped_column(Date)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    customer_satisfaction: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 rating

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    customer: Mapped["CustomerProfile"] = relationship("CustomerProfile", back_populates="assessment_requests")
    service: Mapped["PropertyAssessmentService"] = relationship("PropertyAssessmentService", back_populates="requests")

    __table_args__ = (
        Index("idx_request_status_date", "status", "preferred_date"),
        Index("idx_request_customer_status", "customer_id", "status"),
        Index("idx_request_property", "property_parcel_id", "status"),
        Index("idx_request_payment", "payment_status", "created_at"),
    )


class MessageHistory(Base):
    """Conversation message history for property tax customer support."""

    __tablename__ = "message_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Message identification
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer_profiles.id"), nullable=False)
    thread_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    # Message content
    message_type: Mapped[str] = mapped_column(String(20), index=True)  # user, assistant, system
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(String(50), index=True)

    # Property tax conversation context
    conversation_stage: Mapped[Optional[str]] = mapped_column(String(50))
    conversation_stage_detailed: Mapped[Optional[str]] = mapped_column(String(50))  # inquiry/information/assessment/appeal/payment/completion
    entities_extracted: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Property tax specific context
    property_parcel_mentioned: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    assessment_year_mentioned: Mapped[Optional[int]] = mapped_column(Integer)
    service_type_discussed: Mapped[Optional[str]] = mapped_column(String(50))  # appeal, payment, information, assessment
    tax_amount_mentioned: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    # Related records context
    related_request_id: Mapped[Optional[str]] = mapped_column(String(100))  # PropertyAssessmentRequest.request_id
    related_appeal_id: Mapped[Optional[str]] = mapped_column(String(50))  # Appeal.appeal_id
    related_payment_id: Mapped[Optional[str]] = mapped_column(String(100))  # Payment.payment_id

    # Behavioral Analytics
    response_time_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    error_occurred: Mapped[bool] = mapped_column(Boolean, default=False)
    user_satisfaction_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 if collected
    language_detected: Mapped[Optional[str]] = mapped_column(String(10))
    resolved_customer_issue: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Instagram metadata
    instagram_message_id: Mapped[Optional[str]] = mapped_column(String(100))
    message_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    customer: Mapped["CustomerProfile"] = relationship("CustomerProfile", back_populates="messages")

    __table_args__ = (
        Index("idx_message_customer_thread", "customer_id", "thread_id"),
        Index("idx_message_type_timestamp", "message_type", "message_timestamp"),
        Index("idx_message_intent", "intent", "created_at"),
        Index("idx_message_property_context", "property_parcel_mentioned", "assessment_year_mentioned"),
        Index("idx_message_service_type", "service_type_discussed", "created_at"),
    )


class UserAnalytics(Base):
    """User journey and conversion funnel analytics."""
    
    __tablename__ = "user_analytics"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Relationships
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer_profiles.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    
    # Journey Tracking
    journey_stage: Mapped[str] = mapped_column(String(50), index=True)  # inquiry/recommendation/booking/payment/completed/abandoned
    conversion_time_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    drop_off_point: Mapped[Optional[str]] = mapped_column(String(50))
    total_messages_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Business Metrics
    test_recommended: Mapped[Optional[str]] = mapped_column(String(100))
    service_type_chosen: Mapped[Optional[str]] = mapped_column(String(20))  # home/lab
    payment_method_chosen: Mapped[Optional[str]] = mapped_column(String(50))
    order_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    # Technical Metrics
    average_response_time: Mapped[Optional[float]] = mapped_column(Float)  # seconds
    errors_encountered: Mapped[int] = mapped_column(Integer, default=0)
    language_used: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Timestamps
    journey_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    journey_ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    customer: Mapped["CustomerProfile"] = relationship("CustomerProfile")
    
    __table_args__ = (
        Index("idx_analytics_customer_session", "customer_id", "session_id"),
        Index("idx_analytics_journey_stage", "journey_stage", "created_at"),
        Index("idx_analytics_conversion", "journey_stage", "conversion_time_minutes"),
    )


# Junction table for property ownership
property_ownership = Table(
    'property_ownership',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('property_id', Integer, ForeignKey('properties.id'), nullable=False),
    Column('owner_id', Integer, ForeignKey('property_owners.id'), nullable=False),
    Column('ownership_percentage', Numeric(5, 2), default=100.00),  # Percentage of ownership
    Column('ownership_type', SQLEnum(OwnershipType), default=OwnershipType.SOLE),
    Column('start_date', Date, nullable=False),
    Column('end_date', Date),  # For tracking ownership changes
    Column('is_primary_residence', Boolean, default=False),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    Column('updated_at', DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    Index("idx_property_ownership_property", "property_id"),
    Index("idx_property_ownership_owner", "owner_id"),
    UniqueConstraint("property_id", "owner_id", "start_date", name="uq_property_owner_date")
)


class Property(Base):
    """Property records with assessments and tax information."""

    __tablename__ = "properties"

    # Primary identification
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    parcel_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    # Property address
    street_address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="CA")
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    county: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Property characteristics
    property_type: Mapped[PropertyType] = mapped_column(SQLEnum(PropertyType), index=True, nullable=False)
    zoning: Mapped[Optional[ZoningType]] = mapped_column(SQLEnum(ZoningType))
    square_footage: Mapped[Optional[int]] = mapped_column(Integer)
    lot_size: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))  # in acres
    year_built: Mapped[Optional[int]] = mapped_column(Integer)
    bedrooms: Mapped[Optional[int]] = mapped_column(Integer)
    bathrooms: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 1))

    # Legal description
    legal_description: Mapped[Optional[str]] = mapped_column(Text)
    subdivision: Mapped[Optional[str]] = mapped_column(String(200))
    block: Mapped[Optional[str]] = mapped_column(String(50))
    lot: Mapped[Optional[str]] = mapped_column(String(50))

    # Status and notes
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_tax_exempt: Mapped[bool] = mapped_column(Boolean, default=False)
    exemption_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    special_assessments: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    owners: Mapped[List["PropertyOwner"]] = relationship(
        "PropertyOwner",
        secondary=property_ownership,
        back_populates="properties"
    )
    assessments: Mapped[List["TaxAssessment"]] = relationship("TaxAssessment", back_populates="property")
    appeals: Mapped[List["Appeal"]] = relationship("Appeal", back_populates="property")

    __table_args__ = (
        Index("idx_property_address", "city", "zip_code"),
        Index("idx_property_type_county", "property_type", "county"),
        Index("idx_property_active", "is_active", "county"),
    )


class PropertyOwner(Base):
    """Property owner information and contact details."""

    __tablename__ = "property_owners"

    # Primary identification
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Owner identification
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_initial: Mapped[Optional[str]] = mapped_column(String(1))
    suffix: Mapped[Optional[str]] = mapped_column(String(10))  # Jr, Sr, III, etc.

    # Business information (for corporate owners)
    business_name: Mapped[Optional[str]] = mapped_column(String(200))
    business_type: Mapped[Optional[str]] = mapped_column(String(50))  # LLC, Corp, Trust, etc.

    # Contact information
    mailing_address: Mapped[Optional[str]] = mapped_column(String(500))
    mailing_city: Mapped[Optional[str]] = mapped_column(String(100))
    mailing_state: Mapped[Optional[str]] = mapped_column(String(50))
    mailing_zip: Mapped[Optional[str]] = mapped_column(String(10))

    phone: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), index=True)
    preferred_contact_method: Mapped[Optional[str]] = mapped_column(String(20), default="mail")  # mail, email, phone

    # Preferences and tracking
    receive_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    language_preference: Mapped[str] = mapped_column(String(10), default="en")

    # Customer service integration
    instagram_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)  # Link to CustomerProfile if they use chat

    # Business Intelligence
    total_properties_owned: Mapped[int] = mapped_column(Integer, default=1)
    total_assessed_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    total_annual_tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    payment_history_score: Mapped[Optional[int]] = mapped_column(Integer)  # 1-100 payment reliability
    last_contact_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    properties: Mapped[List["Property"]] = relationship(
        "Property",
        secondary=property_ownership,
        back_populates="owners"
    )

    __table_args__ = (
        Index("idx_owner_name", "last_name", "first_name"),
        Index("idx_owner_contact", "email", "phone"),
        Index("idx_owner_business", "business_name"),
    )


class TaxAssessment(Base):
    """Annual tax assessments for properties."""

    __tablename__ = "tax_assessments"

    # Primary identification
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)

    # Assessment period
    assessment_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    assessment_date: Mapped[date] = mapped_column(Date, nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Valuation
    land_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    improvement_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_assessed_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    market_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    # Tax calculation
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(8, 6), nullable=False)  # Per $100 or per $1000
    tax_rate_type: Mapped[str] = mapped_column(String(20), default="per_100")  # per_100, per_1000
    base_tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Additional assessments
    special_assessments: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    exemptions_applied: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    total_exemption_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    final_tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Payment schedule
    installments: Mapped[int] = mapped_column(Integer, default=2)  # Number of payment installments
    due_dates: Mapped[List[str]] = mapped_column(JSON)  # List of due dates

    # Status tracking
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)
    is_appealed: Mapped[bool] = mapped_column(Boolean, default=False)
    appeal_deadline: Mapped[Optional[date]] = mapped_column(Date)

    # Assessor information
    assessed_by: Mapped[Optional[str]] = mapped_column(String(200))
    assessment_method: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="assessments")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="assessment")
    bills: Mapped[List["TaxBill"]] = relationship("TaxBill", back_populates="assessment")

    __table_args__ = (
        Index("idx_assessment_property_year", "property_id", "assessment_year"),
        Index("idx_assessment_year", "assessment_year"),
        Index("idx_assessment_final", "is_final", "assessment_year"),
        UniqueConstraint("property_id", "assessment_year", name="uq_property_assessment_year")
    )


class Appeal(Base):
    """Property tax assessment appeals."""

    __tablename__ = "appeals"

    # Primary identification
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    appeal_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    # Relationships
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("tax_assessments.id"), nullable=False)

    # Appeal details
    status: Mapped[AppealStatus] = mapped_column(SQLEnum(AppealStatus), default=AppealStatus.DRAFT, index=True)
    reason: Mapped[AppealReason] = mapped_column(SQLEnum(AppealReason), nullable=False)
    reason_description: Mapped[str] = mapped_column(Text, nullable=False)

    # Submission information
    submitted_by_name: Mapped[str] = mapped_column(String(200), nullable=False)
    submitted_by_phone: Mapped[Optional[str]] = mapped_column(String(20))
    submitted_by_email: Mapped[Optional[str]] = mapped_column(String(200))
    relationship_to_property: Mapped[str] = mapped_column(String(100))  # owner, agent, attorney

    # Important dates
    submission_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    deadline_date: Mapped[date] = mapped_column(Date, nullable=False)
    hearing_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    decision_date: Mapped[Optional[date]] = mapped_column(Date)

    # Values being appealed
    current_assessed_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    requested_assessed_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    current_tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    requested_tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Decision information
    decision_assessed_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    decision_tax_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    decision_notes: Mapped[Optional[str]] = mapped_column(Text)
    decided_by: Mapped[Optional[str]] = mapped_column(String(200))

    # Processing information
    assigned_to: Mapped[Optional[str]] = mapped_column(String(200))
    priority_level: Mapped[int] = mapped_column(Integer, default=3)  # 1-5, 1 being highest
    internal_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="appeals")
    assessment: Mapped["TaxAssessment"] = relationship("TaxAssessment")
    documents: Mapped[List["AppealDocument"]] = relationship("AppealDocument", back_populates="appeal")

    __table_args__ = (
        Index("idx_appeal_property_year", "property_id", "submission_date"),
        Index("idx_appeal_status_deadline", "status", "deadline_date"),
        Index("idx_appeal_assigned", "assigned_to", "status"),
    )


class AppealDocument(Base):
    """Documents attached to appeals for evidence."""

    __tablename__ = "appeal_documents"

    # Primary identification
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    appeal_id: Mapped[int] = mapped_column(ForeignKey("appeals.id"), nullable=False)

    # Document information
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)  # appraisal, photos, survey, etc.
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer)  # in bytes
    mime_type: Mapped[str] = mapped_column(String(100))

    # Document metadata
    description: Mapped[Optional[str]] = mapped_column(Text)
    uploaded_by: Mapped[str] = mapped_column(String(200), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)  # Can be shared with public records

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    appeal: Mapped["Appeal"] = relationship("Appeal", back_populates="documents")

    __table_args__ = (
        Index("idx_appeal_doc_appeal", "appeal_id"),
        Index("idx_appeal_doc_type", "document_type"),
    )


class Payment(Base):
    """Tax payments and payment history."""

    __tablename__ = "payments"

    # Primary identification
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    payment_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    # Relationships
    assessment_id: Mapped[int] = mapped_column(ForeignKey("tax_assessments.id"), nullable=False)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)

    # Payment details
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(SQLEnum(PaymentMethod), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, index=True)

    # Payment processing
    transaction_id: Mapped[Optional[str]] = mapped_column(String(200), index=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100))
    confirmation_number: Mapped[Optional[str]] = mapped_column(String(100))

    # Dates
    payment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    processed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[Optional[date]] = mapped_column(Date)

    # Installment information
    installment_number: Mapped[Optional[int]] = mapped_column(Integer)  # Which installment (1, 2, etc.)
    total_installments: Mapped[Optional[int]] = mapped_column(Integer)

    # Fees and penalties
    late_fee: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    penalty: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    interest: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    processing_fee: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)

    # Payer information
    payer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    payer_address: Mapped[Optional[str]] = mapped_column(String(500))
    payer_phone: Mapped[Optional[str]] = mapped_column(String(20))
    payer_email: Mapped[Optional[str]] = mapped_column(String(200))

    # Notes and additional info
    notes: Mapped[Optional[str]] = mapped_column(Text)
    receipt_number: Mapped[Optional[str]] = mapped_column(String(100), index=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    assessment: Mapped["TaxAssessment"] = relationship("TaxAssessment", back_populates="payments")
    property: Mapped["Property"] = relationship("Property")

    __table_args__ = (
        Index("idx_payment_assessment", "assessment_id"),
        Index("idx_payment_property_date", "property_id", "payment_date"),
        Index("idx_payment_status_date", "status", "payment_date"),
        Index("idx_payment_method", "payment_method", "payment_date"),
    )


class TaxBill(Base):
    """Generated tax bills and billing history."""

    __tablename__ = "tax_bills"

    # Primary identification
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bill_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    # Relationships
    assessment_id: Mapped[int] = mapped_column(ForeignKey("tax_assessments.id"), nullable=False)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)

    # Bill details
    bill_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    bill_type: Mapped[str] = mapped_column(String(50), default="annual")  # annual, supplemental, delinquent
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Installment breakdown
    installment_1_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    installment_1_due_date: Mapped[Optional[date]] = mapped_column(Date)
    installment_2_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    installment_2_due_date: Mapped[Optional[date]] = mapped_column(Date)

    # Payment tracking
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    balance_due: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_paid_in_full: Mapped[bool] = mapped_column(Boolean, default=False)
    last_payment_date: Mapped[Optional[date]] = mapped_column(Date)

    # Penalties and fees
    penalty_amount: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    interest_amount: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    penalty_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4))  # Monthly penalty rate

    # Bill generation
    generated_date: Mapped[date] = mapped_column(Date, nullable=False)
    mailed_date: Mapped[Optional[date]] = mapped_column(Date)
    is_electronic: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status tracking
    is_delinquent: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    delinquent_date: Mapped[Optional[date]] = mapped_column(Date)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(200))

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    assessment: Mapped["TaxAssessment"] = relationship("TaxAssessment", back_populates="bills")
    property: Mapped["Property"] = relationship("Property")

    __table_args__ = (
        Index("idx_bill_assessment", "assessment_id"),
        Index("idx_bill_property_year", "property_id", "bill_year"),
        Index("idx_bill_delinquent", "is_delinquent", "delinquent_date"),
        Index("idx_bill_due_dates", "installment_1_due_date", "installment_2_due_date"),
    )


class DatabaseManager:
    """Database manager for async operations."""
    
    def __init__(self, database_url: str):
        """
        Initialize database manager.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self.logger = logger
        
        # Create async engine
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            future=True,
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections after 1 hour
        )
        
        # Create session factory
        self.SessionLocal = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
    async def create_tables(self):
        """Create all database tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create database tables: {e}")
            raise
    
    def get_session(self) -> AsyncSession:
        """Get database session."""
        self.logger.debug("Creating new database session")
        session = self.SessionLocal()
        self.logger.debug(f"Created session: {type(session)}")
        return session
    
    async def close(self):
        """Close database connection."""
        await self.engine.dispose()
        self.logger.info("Database connection closed")
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            from sqlalchemy import text
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


async def get_database_manager() -> DatabaseManager:
    """Get or create database manager instance."""
    global db_manager
    
    if db_manager is None:
        from config.settings import settings
        db_manager = DatabaseManager(settings.database_url)
        
        # Create tables if they don't exist
        await db_manager.create_tables()
        
    return db_manager


from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_session():
    """Get database session as async context manager for tools."""
    logger.debug("Getting database manager...")
    manager = await get_database_manager()
    
    logger.debug("Getting database session...")
    session = manager.get_session()  # Remove await since get_session is now sync
    logger.debug(f"Got session: {type(session)}")
    
    try:
        logger.debug("Yielding session to tool...")
        yield session
        logger.debug("Tool completed, committing session...")
        await session.commit()
        logger.debug("Session committed successfully")
    except Exception as e:
        logger.error(f"Error in session, rolling back: {e}")
        await session.rollback()
        raise
    finally:
        logger.debug("Closing session...")
        await session.close()
        logger.debug("Session closed")