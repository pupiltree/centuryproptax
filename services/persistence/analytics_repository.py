"""
Analytics Repository for User Journey and Behavioral Tracking
Handles conversion funnel analytics, user journey tracking, and business intelligence metrics.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
import structlog

from .database import UserAnalytics, CustomerProfile, MessageHistory
from .repositories import CustomerRepository

logger = structlog.get_logger()


class AnalyticsRepository:
    """Repository for analytics and user journey tracking."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logger.bind(component="analytics_repository")
    
    async def start_user_journey(
        self,
        customer_id: int,
        session_id: str,
        journey_stage: str = "inquiry",
        language_used: Optional[str] = None
    ) -> UserAnalytics:
        """Start tracking a user's journey through the conversion funnel."""
        try:
            analytics = UserAnalytics(
                customer_id=customer_id,
                session_id=session_id,
                journey_stage=journey_stage,
                journey_started_at=datetime.now(),
                language_used=language_used,
                total_messages_count=1
            )
            
            self.session.add(analytics)
            await self.session.flush()
            
            self.logger.info("Started user journey tracking", 
                           customer_id=customer_id, 
                           session_id=session_id, 
                           stage=journey_stage)
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to start user journey: {e}")
            raise
    
    async def update_journey_stage(
        self,
        session_id: str,
        new_stage: str,
        test_recommended: Optional[str] = None,
        service_type_chosen: Optional[str] = None,
        payment_method_chosen: Optional[str] = None,
        order_value: Optional[Decimal] = None
    ) -> Optional[UserAnalytics]:
        """Update user's journey stage with business metrics."""
        try:
            result = await self.session.execute(
                select(UserAnalytics)
                .where(UserAnalytics.session_id == session_id)
                .order_by(UserAnalytics.created_at.desc())
                .limit(1)
            )
            analytics = result.scalar_one_or_none()
            
            if not analytics:
                self.logger.warning("No analytics record found for session", session_id=session_id)
                return None
            
            # Update stage and metrics
            analytics.journey_stage = new_stage
            
            if test_recommended:
                analytics.test_recommended = test_recommended
            if service_type_chosen:
                analytics.service_type_chosen = service_type_chosen
            if payment_method_chosen:
                analytics.payment_method_chosen = payment_method_chosen
            if order_value:
                analytics.order_value = order_value
            
            # Calculate conversion time for completed journeys
            if new_stage in ["completed", "abandoned"]:
                analytics.journey_ended_at = datetime.now()
                time_diff = analytics.journey_ended_at - analytics.journey_started_at
                analytics.conversion_time_minutes = int(time_diff.total_seconds() / 60)
            
            await self.session.flush()
            
            self.logger.info("Updated journey stage", 
                           session_id=session_id, 
                           stage=new_stage, 
                           metrics_updated=bool(test_recommended or service_type_chosen))
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to update journey stage: {e}")
            raise
    
    async def record_drop_off(self, session_id: str, drop_off_point: str) -> None:
        """Record where in the funnel a user dropped off."""
        try:
            result = await self.session.execute(
                select(UserAnalytics)
                .where(UserAnalytics.session_id == session_id)
                .order_by(UserAnalytics.created_at.desc())
                .limit(1)
            )
            analytics = result.scalar_one_or_none()
            
            if analytics:
                analytics.drop_off_point = drop_off_point
                analytics.journey_stage = "abandoned"
                analytics.journey_ended_at = datetime.now()
                
                time_diff = analytics.journey_ended_at - analytics.journey_started_at
                analytics.conversion_time_minutes = int(time_diff.total_seconds() / 60)
                
                await self.session.flush()
                
                self.logger.info("Recorded drop-off", session_id=session_id, drop_off_point=drop_off_point)
            
        except Exception as e:
            self.logger.error(f"Failed to record drop-off: {e}")
            raise
    
    async def update_customer_analytics(
        self,
        customer_id: int,
        service_preference: Optional[str] = None,
        booking_count_increment: int = 0,
        revenue_increment: Decimal = Decimal('0'),
        new_response_time: Optional[int] = None
    ) -> None:
        """Update customer profile analytics."""
        try:
            result = await self.session.execute(
                select(CustomerProfile).where(CustomerProfile.id == customer_id)
            )
            customer = result.scalar_one_or_none()
            
            if not customer:
                self.logger.warning("Customer not found for analytics update", customer_id=customer_id)
                return
            
            # Update service preference if provided
            if service_preference:
                customer.preferred_service_type = service_preference
            
            # Update booking metrics
            if booking_count_increment > 0:
                customer.total_bookings_count += booking_count_increment
                customer.total_revenue += revenue_increment
                customer.customer_lifetime_value = customer.total_revenue
            
            # Update response time (running average)
            if new_response_time is not None:
                if customer.average_response_time is None:
                    customer.average_response_time = new_response_time
                else:
                    # Simple running average
                    customer.average_response_time = int(
                        (customer.average_response_time + new_response_time) / 2
                    )
            
            # Update activity tracking
            customer.last_activity_date = datetime.now()
            customer.last_interaction = datetime.now()
            
            await self.session.flush()
            
            self.logger.info("Updated customer analytics", 
                           customer_id=customer_id, 
                           booking_increment=booking_count_increment,
                           revenue_increment=float(revenue_increment))
            
        except Exception as e:
            self.logger.error(f"Failed to update customer analytics: {e}")
            raise
    
    async def get_conversion_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get conversion funnel metrics for the specified period."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get journey stage counts
            result = await self.session.execute(
                select(
                    UserAnalytics.journey_stage,
                    func.count(UserAnalytics.id).label('count')
                )
                .where(UserAnalytics.created_at >= cutoff_date)
                .group_by(UserAnalytics.journey_stage)
            )
            
            stage_counts = {row.journey_stage: row.count for row in result}
            
            # Calculate conversion rates
            total_inquiries = stage_counts.get('inquiry', 0)
            total_completed = stage_counts.get('completed', 0)
            
            conversion_rate = (total_completed / total_inquiries * 100) if total_inquiries > 0 else 0
            
            # Get average conversion time
            result = await self.session.execute(
                select(func.avg(UserAnalytics.conversion_time_minutes))
                .where(
                    and_(
                        UserAnalytics.created_at >= cutoff_date,
                        UserAnalytics.journey_stage == 'completed'
                    )
                )
            )
            avg_conversion_time = result.scalar() or 0
            
            # Get most common drop-off points
            result = await self.session.execute(
                select(
                    UserAnalytics.drop_off_point,
                    func.count(UserAnalytics.id).label('count')
                )
                .where(
                    and_(
                        UserAnalytics.created_at >= cutoff_date,
                        UserAnalytics.drop_off_point.isnot(None)
                    )
                )
                .group_by(UserAnalytics.drop_off_point)
                .order_by(func.count(UserAnalytics.id).desc())
                .limit(5)
            )
            
            drop_off_points = {row.drop_off_point: row.count for row in result}
            
            return {
                "period_days": days,
                "stage_counts": stage_counts,
                "conversion_rate_percent": round(conversion_rate, 2),
                "average_conversion_time_minutes": round(avg_conversion_time, 2),
                "top_drop_off_points": drop_off_points,
                "total_users": sum(stage_counts.values())
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get conversion metrics: {e}")
            raise
    
    async def get_business_intelligence_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get business intelligence summary with key metrics."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Service preference distribution
            result = await self.session.execute(
                select(
                    UserAnalytics.service_type_chosen,
                    func.count(UserAnalytics.id).label('count')
                )
                .where(
                    and_(
                        UserAnalytics.created_at >= cutoff_date,
                        UserAnalytics.service_type_chosen.isnot(None)
                    )
                )
                .group_by(UserAnalytics.service_type_chosen)
            )
            
            service_preferences = {row.service_type_chosen: row.count for row in result}
            
            # Revenue and test popularity
            result = await self.session.execute(
                select(
                    UserAnalytics.test_recommended,
                    func.count(UserAnalytics.id).label('bookings'),
                    func.sum(UserAnalytics.order_value).label('revenue')
                )
                .where(
                    and_(
                        UserAnalytics.created_at >= cutoff_date,
                        UserAnalytics.test_recommended.isnot(None),
                        UserAnalytics.journey_stage == 'completed'
                    )
                )
                .group_by(UserAnalytics.test_recommended)
                .order_by(func.count(UserAnalytics.id).desc())
                .limit(10)
            )
            
            test_popularity = []
            for row in result:
                test_popularity.append({
                    "test_name": row.test_recommended,
                    "bookings": row.bookings,
                    "revenue": float(row.revenue or 0)
                })
            
            # Language distribution
            result = await self.session.execute(
                select(
                    UserAnalytics.language_used,
                    func.count(UserAnalytics.id).label('count')
                )
                .where(
                    and_(
                        UserAnalytics.created_at >= cutoff_date,
                        UserAnalytics.language_used.isnot(None)
                    )
                )
                .group_by(UserAnalytics.language_used)
                .order_by(func.count(UserAnalytics.id).desc())
            )
            
            language_distribution = {row.language_used: row.count for row in result}
            
            return {
                "period_days": days,
                "service_preferences": service_preferences,
                "top_tests": test_popularity,
                "language_distribution": language_distribution,
                "total_completed_bookings": sum(service_preferences.values()),
                "total_revenue": sum(test["revenue"] for test in test_popularity)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get business intelligence summary: {e}")
            raise