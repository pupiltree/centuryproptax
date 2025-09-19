"""
Demo Environment Reset Manager
Provides clean, isolated demo environment with reset capabilities and data management
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import psycopg2
import redis
from pathlib import Path

from demo.environment.demo_configuration import demo_config
from services.persistence.database import get_database_connection
from services.persistence.redis_conversation_store import get_conversation_store

logger = logging.getLogger(__name__)

@dataclass
class ResetOperation:
    """Details of a reset operation"""
    operation_id: str
    timestamp: datetime
    reset_type: str  # "full", "partial", "data_only", "sessions_only"
    duration_seconds: float
    components_reset: List[str]
    success: bool
    error_message: Optional[str] = None

class DemoResetManager:
    """Manages demo environment resets and clean state maintenance"""

    def __init__(self):
        self.config = demo_config
        self.reset_history: List[ResetOperation] = []
        self._db_connection = None
        self._redis_connection = None

    async def initialize_connections(self):
        """Initialize database and Redis connections for demo environment"""
        try:
            # Initialize demo database connection
            db_config = self.config.get_demo_database_config()
            self._db_connection = psycopg2.connect(
                host=db_config["host"],
                port=db_config["port"],
                database=db_config["database_name"],
                user=db_config["username"],
                password=db_config["password"]
            )

            # Initialize demo Redis connection
            redis_config = self.config.get_demo_redis_config()
            self._redis_connection = redis.Redis(
                host=redis_config["host"],
                port=redis_config["port"],
                db=redis_config["db"],
                password=redis_config.get("password"),
                decode_responses=redis_config["decode_responses"]
            )

            logger.info("Demo environment connections initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize demo connections: {e}")
            return False

    async def perform_full_reset(self) -> ResetOperation:
        """Perform complete demo environment reset"""
        operation_id = f"reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()

        try:
            logger.info(f"Starting full demo reset: {operation_id}")

            # Initialize connections if needed
            if not self._db_connection or not self._redis_connection:
                await self.initialize_connections()

            components_reset = []

            # Reset conversation data
            await self._reset_conversation_data()
            components_reset.append("conversation_data")

            # Reset demo user sessions
            await self._reset_demo_sessions()
            components_reset.append("demo_sessions")

            # Reset analytics data
            await self._reset_analytics_data()
            components_reset.append("analytics_data")

            # Reset demo property data to clean state
            await self._reset_demo_property_data()
            components_reset.append("demo_property_data")

            # Reset payment simulation data
            await self._reset_payment_simulation_data()
            components_reset.append("payment_simulation")

            # Reload fresh demo data
            await self._load_fresh_demo_data()
            components_reset.append("fresh_demo_data")

            # Clear any cached responses
            await self._clear_ai_response_cache()
            components_reset.append("ai_response_cache")

            duration = (datetime.now() - start_time).total_seconds()
            operation = ResetOperation(
                operation_id=operation_id,
                timestamp=start_time,
                reset_type="full",
                duration_seconds=duration,
                components_reset=components_reset,
                success=True
            )

            self.reset_history.append(operation)
            logger.info(f"Full demo reset completed successfully in {duration:.2f}s")
            return operation

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            operation = ResetOperation(
                operation_id=operation_id,
                timestamp=start_time,
                reset_type="full",
                duration_seconds=duration,
                components_reset=[],
                success=False,
                error_message=str(e)
            )

            self.reset_history.append(operation)
            logger.error(f"Full demo reset failed: {e}")
            return operation

    async def perform_quick_reset(self) -> ResetOperation:
        """Perform quick reset for between-demo cleanup"""
        operation_id = f"quick_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()

        try:
            logger.info(f"Starting quick demo reset: {operation_id}")

            components_reset = []

            # Clear active conversations only
            await self._clear_active_conversations()
            components_reset.append("active_conversations")

            # Reset demo user states
            await self._reset_demo_user_states()
            components_reset.append("demo_user_states")

            # Clear temporary session data
            await self._clear_temporary_session_data()
            components_reset.append("temporary_session_data")

            duration = (datetime.now() - start_time).total_seconds()
            operation = ResetOperation(
                operation_id=operation_id,
                timestamp=start_time,
                reset_type="quick",
                duration_seconds=duration,
                components_reset=components_reset,
                success=True
            )

            self.reset_history.append(operation)
            logger.info(f"Quick demo reset completed in {duration:.2f}s")
            return operation

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            operation = ResetOperation(
                operation_id=operation_id,
                timestamp=start_time,
                reset_type="quick",
                duration_seconds=duration,
                components_reset=[],
                success=False,
                error_message=str(e)
            )

            self.reset_history.append(operation)
            logger.error(f"Quick demo reset failed: {e}")
            return operation

    async def _reset_conversation_data(self):
        """Reset all conversation and chat history data"""
        try:
            # Clear Redis conversation store
            if self._redis_connection:
                # Find all demo conversation keys
                demo_keys = self._redis_connection.keys(f"{self.config.demo_settings.demo_user_prefix}*")
                if demo_keys:
                    self._redis_connection.delete(*demo_keys)

                # Clear conversation history
                history_keys = self._redis_connection.keys("conversation:*")
                if history_keys:
                    self._redis_connection.delete(*history_keys)

            logger.info("Conversation data reset completed")

        except Exception as e:
            logger.error(f"Failed to reset conversation data: {e}")
            raise

    async def _reset_demo_sessions(self):
        """Reset demo user sessions and authentication states"""
        try:
            if self._redis_connection:
                # Clear demo session keys
                session_keys = self._redis_connection.keys("session:demo_*")
                if session_keys:
                    self._redis_connection.delete(*session_keys)

                # Clear demo user authentication
                auth_keys = self._redis_connection.keys("auth:demo_*")
                if auth_keys:
                    self._redis_connection.delete(*auth_keys)

            logger.info("Demo sessions reset completed")

        except Exception as e:
            logger.error(f"Failed to reset demo sessions: {e}")
            raise

    async def _reset_analytics_data(self):
        """Reset demo analytics and performance tracking data"""
        try:
            if self._redis_connection:
                # Clear demo analytics
                analytics_keys = self._redis_connection.keys("analytics:demo_*")
                if analytics_keys:
                    self._redis_connection.delete(*analytics_keys)

                # Clear performance metrics
                metrics_keys = self._redis_connection.keys("metrics:demo_*")
                if metrics_keys:
                    self._redis_connection.delete(*metrics_keys)

            logger.info("Analytics data reset completed")

        except Exception as e:
            logger.error(f"Failed to reset analytics data: {e}")
            raise

    async def _reset_demo_property_data(self):
        """Reset demo property data to clean state"""
        try:
            if self._db_connection:
                cursor = self._db_connection.cursor()

                # Clear demo-specific property modifications
                cursor.execute("""
                    DELETE FROM property_modifications
                    WHERE session_id LIKE %s
                """, (f"{self.config.demo_settings.demo_user_prefix}%",))

                # Clear demo assessment appeals
                cursor.execute("""
                    DELETE FROM assessment_appeals
                    WHERE applicant_id LIKE %s
                """, (f"{self.config.demo_settings.demo_user_prefix}%",))

                # Clear demo exemption applications
                cursor.execute("""
                    DELETE FROM exemption_applications
                    WHERE applicant_id LIKE %s
                """, (f"{self.config.demo_settings.demo_user_prefix}%",))

                self._db_connection.commit()
                cursor.close()

            logger.info("Demo property data reset completed")

        except Exception as e:
            logger.error(f"Failed to reset demo property data: {e}")
            raise

    async def _reset_payment_simulation_data(self):
        """Reset payment simulation and transaction data"""
        try:
            if self._db_connection:
                cursor = self._db_connection.cursor()

                # Clear demo payment transactions
                cursor.execute("""
                    DELETE FROM payment_transactions
                    WHERE customer_id LIKE %s
                """, (f"{self.config.demo_settings.demo_user_prefix}%",))

                # Clear demo payment plans
                cursor.execute("""
                    DELETE FROM payment_plans
                    WHERE customer_id LIKE %s
                """, (f"{self.config.demo_settings.demo_user_prefix}%",))

                self._db_connection.commit()
                cursor.close()

            # Clear Redis payment cache
            if self._redis_connection:
                payment_keys = self._redis_connection.keys("payment:demo_*")
                if payment_keys:
                    self._redis_connection.delete(*payment_keys)

            logger.info("Payment simulation data reset completed")

        except Exception as e:
            logger.error(f"Failed to reset payment simulation data: {e}")
            raise

    async def _load_fresh_demo_data(self):
        """Load fresh demo data for clean presentation"""
        try:
            # This would load fresh mock data, demo personas, etc.
            # Implementation depends on your data loading strategy

            # Example: Reset demo customer personas to default state
            from mock_data.demo_customer_personas import demo_personas
            # Personas are read-only, so no reset needed

            # Reset property records to clean demo state
            from mock_data.property_records import get_sample_properties
            # These are also typically read-only

            logger.info("Fresh demo data loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load fresh demo data: {e}")
            raise

    async def _clear_ai_response_cache(self):
        """Clear cached AI responses for consistent demo experience"""
        try:
            if self._redis_connection:
                # Clear AI response cache
                ai_cache_keys = self._redis_connection.keys("ai_cache:*")
                if ai_cache_keys:
                    self._redis_connection.delete(*ai_cache_keys)

                # Clear model response cache
                model_cache_keys = self._redis_connection.keys("model_cache:*")
                if model_cache_keys:
                    self._redis_connection.delete(*model_cache_keys)

            logger.info("AI response cache cleared")

        except Exception as e:
            logger.error(f"Failed to clear AI response cache: {e}")
            raise

    async def _clear_active_conversations(self):
        """Clear only active conversation states for quick reset"""
        try:
            if self._redis_connection:
                # Clear current conversation state but keep history
                active_keys = self._redis_connection.keys("active_conversation:*")
                if active_keys:
                    self._redis_connection.delete(*active_keys)

            logger.info("Active conversations cleared")

        except Exception as e:
            logger.error(f"Failed to clear active conversations: {e}")
            raise

    async def _reset_demo_user_states(self):
        """Reset demo user states and preferences"""
        try:
            if self._redis_connection:
                # Clear demo user preferences
                user_state_keys = self._redis_connection.keys("user_state:demo_*")
                if user_state_keys:
                    self._redis_connection.delete(*user_state_keys)

            logger.info("Demo user states reset")

        except Exception as e:
            logger.error(f"Failed to reset demo user states: {e}")
            raise

    async def _clear_temporary_session_data(self):
        """Clear temporary session data and caches"""
        try:
            if self._redis_connection:
                # Clear temporary data
                temp_keys = self._redis_connection.keys("temp:*")
                if temp_keys:
                    self._redis_connection.delete(*temp_keys)

            logger.info("Temporary session data cleared")

        except Exception as e:
            logger.error(f"Failed to clear temporary session data: {e}")
            raise

    def get_reset_history(self, limit: int = 10) -> List[ResetOperation]:
        """Get recent reset operation history"""
        return sorted(self.reset_history, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_last_reset_time(self) -> Optional[datetime]:
        """Get timestamp of last reset operation"""
        if self.reset_history:
            return max(op.timestamp for op in self.reset_history)
        return None

    async def schedule_automatic_reset(self):
        """Schedule automatic reset based on configuration"""
        if not self.config.demo_settings.auto_reset_enabled:
            return

        while True:
            try:
                reset_interval = timedelta(hours=self.config.demo_settings.reset_interval_hours)
                last_reset = self.get_last_reset_time()

                if not last_reset or datetime.now() - last_reset >= reset_interval:
                    logger.info("Performing scheduled automatic reset")
                    await self.perform_full_reset()

                # Check every hour
                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"Error in automatic reset scheduler: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    def get_demo_environment_status(self) -> Dict[str, Any]:
        """Get current demo environment status"""
        last_reset = self.get_last_reset_time()

        return {
            "demo_mode": self.config.demo_settings.demo_mode,
            "environment_name": self.config.demo_settings.demo_environment_name,
            "last_reset": last_reset.isoformat() if last_reset else None,
            "auto_reset_enabled": self.config.demo_settings.auto_reset_enabled,
            "reset_interval_hours": self.config.demo_settings.reset_interval_hours,
            "total_resets": len(self.reset_history),
            "successful_resets": len([op for op in self.reset_history if op.success]),
            "database_connected": self._db_connection is not None,
            "redis_connected": self._redis_connection is not None,
            "uptime_since_reset": (datetime.now() - last_reset).total_seconds() if last_reset else None
        }

    async def validate_demo_environment(self) -> Dict[str, Any]:
        """Validate demo environment readiness"""
        validation = {
            "ready": True,
            "issues": [],
            "warnings": []
        }

        try:
            # Check database connection
            if not self._db_connection:
                validation["issues"].append("Database connection not established")
                validation["ready"] = False

            # Check Redis connection
            if not self._redis_connection:
                validation["issues"].append("Redis connection not established")
                validation["ready"] = False

            # Check for stale data
            last_reset = self.get_last_reset_time()
            if last_reset and datetime.now() - last_reset > timedelta(hours=24):
                validation["warnings"].append("Demo environment not reset in 24+ hours")

            # Check demo configuration
            config_validation = self.config.validate_demo_environment()
            if not config_validation["valid"]:
                validation["issues"].extend(config_validation["errors"])
                validation["ready"] = False

        except Exception as e:
            validation["issues"].append(f"Validation error: {str(e)}")
            validation["ready"] = False

        return validation

# Global demo reset manager
demo_reset_manager = DemoResetManager()