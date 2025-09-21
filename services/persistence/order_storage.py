"""
Order storage service for hybrid persistence approach.
Stores active orders in Redis and confirmed orders in SQLite.
"""

import json
import redis
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
import asyncio
from functools import wraps
from src.core.logging import get_logger

logger = get_logger("order_storage")


def async_to_sync(async_func):
    """Decorator to run async functions in sync context."""
    @wraps(async_func)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


class OrderStorageService:
    """
    Hybrid order storage service.
    - Redis: Active orders (with TTL)
    - SQLite: Confirmed/completed orders
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize order storage service."""
        self.redis_url = redis_url
        self.logger = logger
        
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            self.redis_client.ping()
            self.logger.info("Redis connection established for order storage")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def store_order(self, order_data: Dict[str, Any]) -> bool:
        """
        Store order in Redis with 24-hour TTL.
        
        Args:
            order_data: Order information including order_id
            
        Returns:
            Success status
        """
        if not self.redis_client:
            self.logger.error("Redis not available for order storage")
            return False
        
        try:
            order_id = order_data.get("order_id")
            if not order_id:
                self.logger.error("Order ID missing in order data")
                return False
            
            # Add timestamp
            order_data["created_at"] = datetime.now().isoformat()
            order_data["status"] = order_data.get("status", "pending")
            
            # Store in Redis with 24-hour TTL
            key = f"order:{order_id}"
            self.redis_client.setex(
                key,
                86400,  # 24 hours in seconds
                json.dumps(order_data)
            )
            
            # Also store in a list of recent orders for the customer
            instagram_id = order_data.get("instagram_id")
            if instagram_id:
                customer_key = f"customer_orders:{instagram_id}"
                self.redis_client.lpush(customer_key, order_id)
                self.redis_client.expire(customer_key, 86400)  # 24 hour TTL
            
            self.logger.info(
                f"Order stored successfully",
                order_id=order_id,
                customer=order_data.get("customer_name")
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store order: {e}")
            return False
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve order from Redis.
        
        Args:
            order_id: Order ID to retrieve
            
        Returns:
            Order data or None if not found
        """
        if not self.redis_client:
            self.logger.error("Redis not available")
            return None
        
        try:
            key = f"order:{order_id}"
            order_json = self.redis_client.get(key)
            
            if order_json:
                order_data = json.loads(order_json)
                self.logger.info(f"Order retrieved", order_id=order_id)
                return order_data
            else:
                self.logger.warning(f"Order not found", order_id=order_id)
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve order: {e}")
            return None
    
    def update_order_status(self, order_id: str, status: str, payment_data: Dict[str, Any] = None) -> bool:
        """
        Update order status and optionally add payment data.
        
        Args:
            order_id: Order ID to update
            status: New status
            payment_data: Optional payment information
            
        Returns:
            Success status
        """
        try:
            order_data = self.get_order(order_id)
            if not order_data:
                return False
            
            # Update status
            order_data["status"] = status
            order_data["updated_at"] = datetime.now().isoformat()
            
            # Add payment data if provided
            if payment_data:
                order_data["payment_data"] = payment_data
                order_data["payment_status"] = "completed"
            
            # Store updated order
            return self.store_order(order_data)
            
        except Exception as e:
            self.logger.error(f"Failed to update order status: {e}")
            return False
    
    def get_customer_orders(self, instagram_id: str, limit: int = 10) -> list:
        """
        Get recent orders for a customer.
        
        Args:
            instagram_id: Customer's Instagram ID
            limit: Maximum number of orders to retrieve
            
        Returns:
            List of order data
        """
        if not self.redis_client:
            return []
        
        try:
            customer_key = f"customer_orders:{instagram_id}"
            order_ids = self.redis_client.lrange(customer_key, 0, limit - 1)
            
            orders = []
            for order_id in order_ids:
                order_data = self.get_order(order_id)
                if order_data:
                    orders.append(order_data)
            
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get customer orders: {e}")
            return []
    
    async def persist_to_database(self, order_id: str) -> bool:
        """
        Persist confirmed order to SQLite database.
        This is called when payment is confirmed.
        
        Args:
            order_id: Order ID to persist
            
        Returns:
            Success status
        """
        try:
            # Get order from Redis
            order_data = self.get_order(order_id)
            if not order_data:
                self.logger.error(f"Order not found in Redis: {order_id}")
                return False
            
            # Import database components
            from services.persistence.database import get_db_session
            from services.persistence.repositories import CustomerRepository, BookingRepository
            
            async with get_db_session() as session:
                customer_repo = CustomerRepository(session)
                booking_repo = BookingRepository(session)
                
                # Create or update customer
                customer = await customer_repo.create_or_update(
                    instagram_id=order_data.get("instagram_id"),
                    name=order_data.get("customer_name"),
                    phone=order_data.get("phone"),
                    pin_code=order_data.get("pin_code")
                )
                
                # Create booking record
                from datetime import datetime, date
                
                # Convert string date to Python date object
                preferred_date_str = order_data.get("preferred_date")
                if preferred_date_str:
                    if isinstance(preferred_date_str, str):
                        preferred_date = datetime.strptime(preferred_date_str, "%Y-%m-%d").date()
                    else:
                        preferred_date = preferred_date_str
                else:
                    preferred_date = None
                
                booking = await booking_repo.create_booking(
                    customer_id=customer.id,
                    test_id=1,  # Would need proper test lookup in production
                    booking_id=order_id,
                    total_amount=order_data.get("total_amount", 0),
                    preferred_date=preferred_date,
                    preferred_time=order_data.get("preferred_time"),
                    collection_type=order_data.get("collection_type", "home"),
                    collection_address=order_data.get("address")
                )
                
                # Update payment status if paid
                if order_data.get("payment_status") == "completed":
                    await booking_repo.update_status(
                        booking_id=order_id,
                        status="confirmed",
                        payment_status="paid",
                        payment_id=order_data.get("payment_data", {}).get("payment_id")
                    )
                
                self.logger.info(f"Order persisted to database", order_id=order_id)
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to persist order to database: {e}")
            return False


# Global instance
order_storage = None


def get_order_storage() -> OrderStorageService:
    """Get or create order storage service instance."""
    global order_storage
    
    if order_storage is None:
        from config.settings import settings
        order_storage = OrderStorageService(redis_url=settings.redis_url)
    
    return order_storage