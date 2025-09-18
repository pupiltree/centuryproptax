"""
Repository pattern for database operations.
Provides clean interface for customer data, bookings, and test catalog operations.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

import structlog
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .database import (
    CustomerProfile, TestCatalog, TestBooking, MessageHistory
)

logger = structlog.get_logger()


class CustomerRepository:
    """Repository for customer profile operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logger.bind(component="customer_repository")
    
    async def get_by_instagram_id(self, instagram_id: str) -> Optional[CustomerProfile]:
        """Get customer by Instagram ID."""
        try:
            result = await self.session.execute(
                select(CustomerProfile)
                .where(CustomerProfile.instagram_id == instagram_id)
                .options(selectinload(CustomerProfile.bookings))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get customer by Instagram ID: {e}")
            return None
    
    async def get_by_phone(self, phone: str) -> Optional[CustomerProfile]:
        """Get customer by phone number."""
        try:
            result = await self.session.execute(
                select(CustomerProfile)
                .where(CustomerProfile.phone == phone)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get customer by phone: {e}")
            return None
    
    async def create_or_update(
        self,
        instagram_id: str,
        **profile_data
    ) -> CustomerProfile:
        """Create or update customer profile."""
        try:
            # Check if customer exists
            existing = await self.get_by_instagram_id(instagram_id)
            
            if existing:
                # Update existing customer
                for key, value in profile_data.items():
                    if value is not None and hasattr(existing, key):
                        setattr(existing, key, value)
                
                existing.last_interaction = datetime.utcnow()
                existing.conversation_count += 1
                
                await self.session.commit()
                await self.session.refresh(existing)
                
                self.logger.info(f"Customer updated: {instagram_id}")
                return existing
            
            else:
                # Create new customer
                new_customer = CustomerProfile(
                    instagram_id=instagram_id,
                    last_interaction=datetime.utcnow(),
                    conversation_count=1,
                    **profile_data
                )
                
                self.session.add(new_customer)
                await self.session.commit()
                await self.session.refresh(new_customer)
                
                self.logger.info(f"Customer created: {instagram_id}")
                return new_customer
                
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to create/update customer: {e}")
            raise
    
    async def update_medical_info(
        self,
        instagram_id: str,
        medical_conditions: Optional[List[str]] = None,
        medications: Optional[List[str]] = None,
        allergies: Optional[List[str]] = None,
    ) -> Optional[CustomerProfile]:
        """Update customer medical information."""
        try:
            customer = await self.get_by_instagram_id(instagram_id)
            if not customer:
                return None
            
            if medical_conditions is not None:
                customer.medical_conditions = {
                    "conditions": medical_conditions,
                    "updated_at": datetime.utcnow().isoformat()
                }
            
            if medications is not None:
                customer.medications = {
                    "medications": medications,
                    "updated_at": datetime.utcnow().isoformat()
                }
            
            if allergies is not None:
                customer.allergies = allergies
            
            await self.session.commit()
            await self.session.refresh(customer)
            
            self.logger.info(f"Medical info updated for customer: {instagram_id}")
            return customer
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to update medical info: {e}")
            return None
    
    async def get_recent_customers(self, limit: int = 50) -> List[CustomerProfile]:
        """Get recently active customers."""
        try:
            result = await self.session.execute(
                select(CustomerProfile)
                .order_by(CustomerProfile.last_interaction.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get recent customers: {e}")
            return []
    
    async def get_by_id(self, customer_id: int) -> Optional[CustomerProfile]:
        """Get customer by ID."""
        try:
            return await self.session.get(CustomerProfile, customer_id)
        except Exception as e:
            self.logger.error(f"Failed to get customer by ID: {e}")
            return None


class TestCatalogRepository:
    """Repository for test catalog operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logger.bind(component="test_catalog_repository")
    
    async def search_tests(
        self,
        query: str,
        category: Optional[str] = None,
        available_only: bool = True,
        limit: int = 20
    ) -> List[TestCatalog]:
        """Search tests by name, description, or includes."""
        try:
            # Build search conditions
            search_conditions = []
            
            if query:
                query_lower = f"%{query.lower()}%"
                search_conditions.append(
                    or_(
                        func.lower(TestCatalog.name).like(query_lower),
                        func.lower(TestCatalog.description).like(query_lower),
                        func.json_extract(TestCatalog.includes, '$').like(f'%{query.lower()}%')  # JSON search
                    )
                )
            
            if category:
                search_conditions.append(TestCatalog.category == category)
            
            if available_only:
                search_conditions.append(TestCatalog.available == True)
            
            # Execute query
            stmt = select(TestCatalog)
            if search_conditions:
                stmt = stmt.where(and_(*search_conditions))
            
            stmt = stmt.order_by(TestCatalog.name).limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error(f"Failed to search tests: {e}")
            return []
    
    async def get_by_code(self, test_code: str) -> Optional[TestCatalog]:
        """Get test by test code."""
        try:
            result = await self.session.execute(
                select(TestCatalog)
                .where(TestCatalog.test_code == test_code)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get test by code: {e}")
            return None
    
    async def get_by_category(self, category: str) -> List[TestCatalog]:
        """Get all tests in a category."""
        try:
            result = await self.session.execute(
                select(TestCatalog)
                .where(
                    and_(
                        TestCatalog.category == category,
                        TestCatalog.available == True
                    )
                )
                .order_by(TestCatalog.name)
            )
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get tests by category: {e}")
            return []
    
    async def get_recommended_for_condition(
        self,
        condition: str,
        limit: int = 10
    ) -> List[TestCatalog]:
        """Get tests recommended for a medical condition."""
        try:
            result = await self.session.execute(
                select(TestCatalog)
                .where(
                    and_(
                        func.json_extract(TestCatalog.conditions_recommended_for, '$').like(f'%{condition.lower()}%'),
                        TestCatalog.available == True
                    )
                )
                .order_by(TestCatalog.price)  # Order by price ascending
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get recommended tests: {e}")
            return []


class BookingRepository:
    """Repository for booking operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logger.bind(component="booking_repository")
    
    async def create_booking(
        self,
        customer_id: int,
        test_id: int,
        booking_id: str,
        total_amount: Decimal,
        preferred_date: Optional[date] = None,
        preferred_time: Optional[str] = None,
        collection_type: str = "home",
        collection_address: Optional[Dict[str, Any]] = None,
    ) -> TestBooking:
        """Create a new booking."""
        try:
            booking = TestBooking(
                booking_id=booking_id,
                customer_id=customer_id,
                test_id=test_id,
                total_amount=total_amount,
                preferred_date=preferred_date,
                preferred_time=preferred_time,
                collection_type=collection_type,
                collection_address=collection_address,
                status="pending",
                payment_status="pending",
            )
            
            self.session.add(booking)
            await self.session.commit()
            await self.session.refresh(booking)
            
            self.logger.info(f"Booking created: {booking_id}")
            return booking
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to create booking: {e}")
            raise
    
    async def get_by_booking_id(self, booking_id: str) -> Optional[TestBooking]:
        """Get booking by booking ID."""
        try:
            result = await self.session.execute(
                select(TestBooking)
                .options(
                    selectinload(TestBooking.customer),
                    selectinload(TestBooking.test)
                )
                .where(TestBooking.booking_id == booking_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get booking: {e}")
            return None
    
    async def get_customer_bookings(
        self,
        customer_id: int,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[TestBooking]:
        """Get bookings for a customer."""
        try:
            stmt = (
                select(TestBooking)
                .options(selectinload(TestBooking.test))
                .where(TestBooking.customer_id == customer_id)
            )
            
            if status:
                stmt = stmt.where(TestBooking.status == status)
            
            stmt = stmt.order_by(TestBooking.created_at.desc()).limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error(f"Failed to get customer bookings: {e}")
            return []
    
    async def update_status(
        self,
        booking_id: str,
        status: str,
        payment_status: Optional[str] = None,
        payment_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[TestBooking]:
        """Update booking status and payment information."""
        try:
            booking = await self.get_by_booking_id(booking_id)
            if not booking:
                return None
            
            booking.status = status
            
            if payment_status is not None:
                booking.payment_status = payment_status
            
            if payment_id is not None:
                booking.payment_id = payment_id
            
            if notes is not None:
                booking.notes = notes
            
            await self.session.commit()
            await self.session.refresh(booking)
            
            self.logger.info(f"Booking status updated: {booking_id} -> {status}")
            return booking
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to update booking status: {e}")
            return None
    
    async def get_all_bookings(self, limit: int = 50) -> List[TestBooking]:
        """Get all bookings with optional limit."""
        try:
            result = await self.session.execute(
                select(TestBooking)
                .options(
                    selectinload(TestBooking.customer),
                    selectinload(TestBooking.test)
                )
                .order_by(TestBooking.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get all bookings: {e}")
            return []
    
    async def update_booking_status(
        self,
        booking_id: int,
        status: str,
        notes: Optional[str] = None
    ) -> Optional[TestBooking]:
        """Update booking status by booking database ID."""
        try:
            booking = await self.session.get(TestBooking, booking_id)
            if not booking:
                return None
            
            booking.status = status
            if notes is not None:
                booking.notes = notes
            
            await self.session.commit()
            await self.session.refresh(booking)
            
            self.logger.info(f"Booking status updated: ID {booking_id} -> {status}")
            return booking
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to update booking status: {e}")
            return None


class MessageHistoryRepository:
    """Repository for message history operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logger.bind(component="message_history_repository")
    
    async def save_message(
        self,
        customer_id: int,
        thread_id: str,
        message_type: str,
        message_text: str,
        intent: Optional[str] = None,
        conversation_stage: Optional[str] = None,
        entities_extracted: Optional[Dict[str, Any]] = None,
        instagram_message_id: Optional[str] = None,
        message_timestamp: Optional[datetime] = None,
    ) -> MessageHistory:
        """Save a conversation message."""
        try:
            message = MessageHistory(
                customer_id=customer_id,
                thread_id=thread_id,
                message_type=message_type,
                message_text=message_text,
                intent=intent,
                conversation_stage=conversation_stage,
                entities_extracted=entities_extracted,
                instagram_message_id=instagram_message_id,
                message_timestamp=message_timestamp or datetime.utcnow(),
            )
            
            self.session.add(message)
            await self.session.commit()
            await self.session.refresh(message)
            
            return message
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to save message: {e}")
            raise
    
    async def get_conversation_history(
        self,
        customer_id: int,
        thread_id: str,
        limit: int = 50
    ) -> List[MessageHistory]:
        """Get conversation history for a customer and thread."""
        try:
            result = await self.session.execute(
                select(MessageHistory)
                .where(
                    and_(
                        MessageHistory.customer_id == customer_id,
                        MessageHistory.thread_id == thread_id
                    )
                )
                .order_by(MessageHistory.message_timestamp.desc())
                .limit(limit)
            )
            return list(reversed(list(result.scalars().all())))  # Return chronological order
        except Exception as e:
            self.logger.error(f"Failed to get conversation history: {e}")
            return []