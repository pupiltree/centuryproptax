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
    CustomerProfile, PropertyAssessmentService, PropertyAssessmentRequest, MessageHistory,
    Property, PropertyOwner, TaxAssessment, Appeal, Payment, TaxBill
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

                self.logger.info(f"Property tax customer updated: {instagram_id}")
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

                self.logger.info(f"Property tax customer created: {instagram_id}")
                return new_customer
                
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to create/update customer: {e}")
            raise
    
    async def update_property_info(
        self,
        instagram_id: str,
        owned_properties: Optional[List[str]] = None,
        primary_property_parcel: Optional[str] = None,
        property_ownership_type: Optional[str] = None,
        zip_code: Optional[str] = None,
        county: Optional[str] = None,
    ) -> Optional[CustomerProfile]:
        """Update customer property ownership information."""
        try:
            customer = await self.get_by_instagram_id(instagram_id)
            if not customer:
                return None

            if owned_properties is not None:
                customer.owned_properties = owned_properties

            if primary_property_parcel is not None:
                customer.primary_property_parcel = primary_property_parcel

            if property_ownership_type is not None:
                customer.property_ownership_type = property_ownership_type

            if zip_code is not None:
                customer.zip_code = zip_code

            if county is not None:
                customer.county = county

            await self.session.commit()
            await self.session.refresh(customer)

            self.logger.info(f"Property info updated for customer: {instagram_id}")
            return customer

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to update property info: {e}")
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


class PropertyAssessmentServiceRepository:
    """Repository for property assessment service operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logger.bind(component="property_assessment_service_repository")

    async def search_services(
        self,
        query: str,
        category: Optional[str] = None,
        available_only: bool = True,
        limit: int = 20
    ) -> List[PropertyAssessmentService]:
        """Search services by name, description, or requirements."""
        try:
            # Build search conditions
            search_conditions = []

            if query:
                query_lower = f"%{query.lower()}%"
                search_conditions.append(
                    or_(
                        func.lower(PropertyAssessmentService.name).like(query_lower),
                        func.lower(PropertyAssessmentService.description).like(query_lower),
                        func.json_extract(PropertyAssessmentService.requirements, '$').like(f'%{query.lower()}%')  # JSON search
                    )
                )

            if category:
                search_conditions.append(PropertyAssessmentService.category == category)

            if available_only:
                search_conditions.append(PropertyAssessmentService.available == True)

            # Execute query
            stmt = select(PropertyAssessmentService)
            if search_conditions:
                stmt = stmt.where(and_(*search_conditions))

            stmt = stmt.order_by(PropertyAssessmentService.name).limit(limit)

            result = await self.session.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            self.logger.error(f"Failed to search services: {e}")
            return []

    async def get_by_code(self, service_code: str) -> Optional[PropertyAssessmentService]:
        """Get service by service code."""
        try:
            result = await self.session.execute(
                select(PropertyAssessmentService)
                .where(PropertyAssessmentService.service_code == service_code)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get service by code: {e}")
            return None

    async def get_by_category(self, category: str) -> List[PropertyAssessmentService]:
        """Get all services in a category."""
        try:
            result = await self.session.execute(
                select(PropertyAssessmentService)
                .where(
                    and_(
                        PropertyAssessmentService.category == category,
                        PropertyAssessmentService.available == True
                    )
                )
                .order_by(PropertyAssessmentService.name)
            )
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get services by category: {e}")
            return []

    async def get_applicable_for_property_type(
        self,
        property_type: str,
        limit: int = 10
    ) -> List[PropertyAssessmentService]:
        """Get services applicable for a property type."""
        try:
            result = await self.session.execute(
                select(PropertyAssessmentService)
                .where(
                    and_(
                        func.json_extract(PropertyAssessmentService.property_types_applicable, '$').like(f'%{property_type.lower()}%'),
                        PropertyAssessmentService.available == True
                    )
                )
                .order_by(PropertyAssessmentService.fee)  # Order by fee ascending
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get applicable services: {e}")
            return []


class PropertyAssessmentRequestRepository:
    """Repository for property assessment request operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logger.bind(component="property_assessment_request_repository")

    async def create_request(
        self,
        customer_id: int,
        service_id: int,
        request_id: str,
        total_amount: Decimal,
        description: str,
        request_type: str,
        property_parcel_id: Optional[str] = None,
        preferred_date: Optional[date] = None,
        preferred_time: Optional[str] = None,
        delivery_method: str = "online",
        delivery_address: Optional[Dict[str, Any]] = None,
        urgency_level: str = "normal",
    ) -> PropertyAssessmentRequest:
        """Create a new property assessment request."""
        try:
            request = PropertyAssessmentRequest(
                request_id=request_id,
                customer_id=customer_id,
                service_id=service_id,
                description=description,
                request_type=request_type,
                property_parcel_id=property_parcel_id,
                total_amount=total_amount,
                preferred_date=preferred_date,
                preferred_time=preferred_time,
                delivery_method=delivery_method,
                delivery_address=delivery_address,
                urgency_level=urgency_level,
                status="pending",
                payment_status="pending",
            )

            self.session.add(request)
            await self.session.commit()
            await self.session.refresh(request)

            self.logger.info(f"Property assessment request created: {request_id}")
            return request

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to create request: {e}")
            raise

    async def get_by_request_id(self, request_id: str) -> Optional[PropertyAssessmentRequest]:
        """Get request by request ID."""
        try:
            result = await self.session.execute(
                select(PropertyAssessmentRequest)
                .options(
                    selectinload(PropertyAssessmentRequest.customer),
                    selectinload(PropertyAssessmentRequest.service)
                )
                .where(PropertyAssessmentRequest.request_id == request_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get request: {e}")
            return None

    async def get_customer_requests(
        self,
        customer_id: int,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[PropertyAssessmentRequest]:
        """Get requests for a customer."""
        try:
            stmt = (
                select(PropertyAssessmentRequest)
                .options(selectinload(PropertyAssessmentRequest.service))
                .where(PropertyAssessmentRequest.customer_id == customer_id)
            )

            if status:
                stmt = stmt.where(PropertyAssessmentRequest.status == status)

            stmt = stmt.order_by(PropertyAssessmentRequest.created_at.desc()).limit(limit)

            result = await self.session.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            self.logger.error(f"Failed to get customer requests: {e}")
            return []

    async def update_status(
        self,
        request_id: str,
        status: str,
        payment_status: Optional[str] = None,
        payment_id: Optional[str] = None,
        internal_notes: Optional[str] = None,
        assigned_to: Optional[str] = None,
    ) -> Optional[PropertyAssessmentRequest]:
        """Update request status and payment information."""
        try:
            request = await self.get_by_request_id(request_id)
            if not request:
                return None

            request.status = status

            if payment_status is not None:
                request.payment_status = payment_status

            if payment_id is not None:
                request.payment_id = payment_id

            if internal_notes is not None:
                request.internal_notes = internal_notes

            if assigned_to is not None:
                request.assigned_to = assigned_to

            await self.session.commit()
            await self.session.refresh(request)

            self.logger.info(f"Request status updated: {request_id} -> {status}")
            return request

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to update request status: {e}")
            return None

    async def get_all_requests(self, limit: int = 50) -> List[PropertyAssessmentRequest]:
        """Get all requests with optional limit."""
        try:
            result = await self.session.execute(
                select(PropertyAssessmentRequest)
                .options(
                    selectinload(PropertyAssessmentRequest.customer),
                    selectinload(PropertyAssessmentRequest.service)
                )
                .order_by(PropertyAssessmentRequest.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get all requests: {e}")
            return []

    async def get_requests_by_property(
        self,
        property_parcel_id: str,
        limit: int = 20
    ) -> List[PropertyAssessmentRequest]:
        """Get requests for a specific property."""
        try:
            result = await self.session.execute(
                select(PropertyAssessmentRequest)
                .options(
                    selectinload(PropertyAssessmentRequest.customer),
                    selectinload(PropertyAssessmentRequest.service)
                )
                .where(PropertyAssessmentRequest.property_parcel_id == property_parcel_id)
                .order_by(PropertyAssessmentRequest.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get requests by property: {e}")
            return []


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
        property_parcel_mentioned: Optional[str] = None,
        assessment_year_mentioned: Optional[int] = None,
        service_type_discussed: Optional[str] = None,
        tax_amount_mentioned: Optional[Decimal] = None,
        related_request_id: Optional[str] = None,
        related_appeal_id: Optional[str] = None,
        related_payment_id: Optional[str] = None,
        resolved_customer_issue: Optional[bool] = None,
        instagram_message_id: Optional[str] = None,
        message_timestamp: Optional[datetime] = None,
    ) -> MessageHistory:
        """Save a property tax conversation message."""
        try:
            message = MessageHistory(
                customer_id=customer_id,
                thread_id=thread_id,
                message_type=message_type,
                message_text=message_text,
                intent=intent,
                conversation_stage=conversation_stage,
                entities_extracted=entities_extracted,
                property_parcel_mentioned=property_parcel_mentioned,
                assessment_year_mentioned=assessment_year_mentioned,
                service_type_discussed=service_type_discussed,
                tax_amount_mentioned=tax_amount_mentioned,
                related_request_id=related_request_id,
                related_appeal_id=related_appeal_id,
                related_payment_id=related_payment_id,
                resolved_customer_issue=resolved_customer_issue,
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