"""
Database models and operations for Century Property Tax.
SQLAlchemy async models for customer data, property assessments, and tax records.
"""

import asyncio
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

import structlog
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    Numeric, Date, JSON, ForeignKey, Index, UniqueConstraint, Float
)
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.sql import func

logger = structlog.get_logger()


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class CustomerProfile(Base):
    """Customer profile with medical history and preferences."""
    
    __tablename__ = "customer_profiles"
    
    # Primary identification
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    instagram_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    # Personal information
    name: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    email: Mapped[Optional[str]] = mapped_column(String(200))
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Medical information (encrypted in production)
    medical_conditions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    medications: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    allergies: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Location and preferences
    pin_code: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Conversation tracking
    last_interaction: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    conversation_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Business Intelligence & Analytics
    preferred_service_type: Mapped[Optional[str]] = mapped_column(String(20))  # home/lab preference history
    total_bookings_count: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    average_response_time: Mapped[Optional[int]] = mapped_column(Integer)  # in minutes
    last_activity_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    conversion_rate: Mapped[Optional[float]] = mapped_column(Float)  # inquiries to bookings
    customer_lifetime_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bookings: Mapped[List["TestBooking"]] = relationship("TestBooking", back_populates="customer")
    messages: Mapped[List["MessageHistory"]] = relationship("MessageHistory", back_populates="customer")
    
    __table_args__ = (
        Index("idx_customer_phone_pin", "phone", "pin_code"),
        Index("idx_customer_last_interaction", "last_interaction"),
    )


class TestCatalog(Base):
    """Medical test catalog with pricing and requirements."""
    
    __tablename__ = "test_catalog"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Test identification
    test_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    
    # Test details
    description: Mapped[Optional[str]] = mapped_column(Text)
    includes: Mapped[Optional[List[str]]] = mapped_column(JSON)  # List of sub-tests
    sample_type: Mapped[Optional[str]] = mapped_column(String(50))  # Blood, Urine, etc.
    fasting_required: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Pricing
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discounted_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    # Availability
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    home_collection: Mapped[bool] = mapped_column(Boolean, default=True)
    lab_visit_required: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Medical relevance
    conditions_recommended_for: Mapped[Optional[List[str]]] = mapped_column(JSON)
    age_group: Mapped[Optional[str]] = mapped_column(String(50))
    gender_specific: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bookings: Mapped[List["TestBooking"]] = relationship("TestBooking", back_populates="test")
    
    __table_args__ = (
        Index("idx_test_category_price", "category", "price"),
        Index("idx_test_available", "available", "category"),
    )


class TestBooking(Base):
    """Test booking records with payment and scheduling."""
    
    __tablename__ = "test_bookings"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Booking identification
    booking_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    # Relationships
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer_profiles.id"), nullable=False)
    test_id: Mapped[int] = mapped_column(ForeignKey("test_catalog.id"), nullable=False)
    
    # Scheduling
    preferred_date: Mapped[Optional[date]] = mapped_column(Date)
    preferred_time: Mapped[Optional[str]] = mapped_column(String(20))
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Collection details
    collection_type: Mapped[str] = mapped_column(String(20), default="home")  # home, lab
    collection_address: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Booking status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    # pending, confirmed, sample_collected, processing, completed, cancelled
    
    # Payment
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    payment_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Communication
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    customer: Mapped["CustomerProfile"] = relationship("CustomerProfile", back_populates="bookings")
    test: Mapped["TestCatalog"] = relationship("TestCatalog", back_populates="bookings")
    
    __table_args__ = (
        Index("idx_booking_status_date", "status", "preferred_date"),
        Index("idx_booking_customer_status", "customer_id", "status"),
        Index("idx_booking_payment", "payment_status", "created_at"),
    )


class MessageHistory(Base):
    """Conversation message history for context and compliance."""
    
    __tablename__ = "message_history"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Message identification
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer_profiles.id"), nullable=False)
    thread_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    
    # Message content
    message_type: Mapped[str] = mapped_column(String(20), index=True)  # user, assistant, system
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    
    # Context
    conversation_stage: Mapped[Optional[str]] = mapped_column(String(50))
    conversation_stage_detailed: Mapped[Optional[str]] = mapped_column(String(50))  # inquiry/recommendation/booking/payment/completion
    entities_extracted: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Behavioral Analytics
    response_time_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    error_occurred: Mapped[bool] = mapped_column(Boolean, default=False)
    user_satisfaction_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 if collected
    language_detected: Mapped[Optional[str]] = mapped_column(String(10))
    
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


class DatabaseManager:
    """Database manager for async operations."""
    
    def __init__(self, database_url: str):
        """
        Initialize database manager.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self.logger = logger.bind(component="database_manager")
        
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