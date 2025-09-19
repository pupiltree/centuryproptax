#!/usr/bin/env python3
"""
Clear all user data from SQLite and Redis databases.
This script will remove:
- All customer profiles
- All bookings and orders  
- All support tickets and messages
- All Redis keys (sessions, orders, tickets)
- All conversation state
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import structlog

# Try to import dependencies with better error handling
try:
    import redis.asyncio as aioredis
except ImportError:
    print("❌ Error: redis package not found. Please install with: pip install redis")
    sys.exit(1)

try:
    from sqlalchemy import text
    from services.persistence.database import get_db_session, get_database_manager
    SQLALCHEMY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Database dependencies not found: {e}")
    print("   Redis clearing will work, but SQLite clearing will be skipped")
    SQLALCHEMY_AVAILABLE = False

logger = structlog.get_logger()


async def clear_redis_data():
    """Clear all Redis data."""
    try:
        logger.info("🔄 Connecting to Redis...")
        
        # Try to get settings, fallback to default if not available
        try:
            from config.settings import settings
            redis_url = settings.redis_url
        except ImportError:
            redis_url = "redis://localhost:6379/0"
            logger.warning("⚠️ Could not import settings, using default Redis URL")
        
        redis_client = await aioredis.from_url(redis_url, decode_responses=True)
        
        # Get all keys
        all_keys = await redis_client.keys("*")
        
        if not all_keys:
            logger.info("✅ Redis is already empty")
            return
        
        logger.info(f"🗑️ Found {len(all_keys)} Redis keys to delete")
        
        # Delete all keys
        await redis_client.delete(*all_keys)
        
        # Verify deletion
        remaining_keys = await redis_client.keys("*")
        
        if remaining_keys:
            logger.warning(f"⚠️ {len(remaining_keys)} keys still remain in Redis")
        else:
            logger.info("✅ Redis cleared successfully")
        
        await redis_client.aclose()
        
    except Exception as e:
        logger.error(f"❌ Error clearing Redis: {e}")


async def clear_sqlite_data():
    """Clear all SQLite data."""
    if not SQLALCHEMY_AVAILABLE:
        logger.warning("⚠️ SQLite clearing skipped - database dependencies not available")
        return
        
    try:
        logger.info("🔄 Clearing SQLite database...")
        
        async with get_db_session() as session:
            # List of tables to clear (in dependency order)
            tables_to_clear = [
                "ticket_messages",      # Has foreign key to support_tickets
                "agent_sessions",       # Has foreign key to support_tickets  
                "support_tickets",      # Has foreign key to customers
                "test_bookings",        # Has foreign key to customers
                "customers",            # Base table
                "medical_tests",        # Independent table
                "service_areas"         # Independent table
            ]
            
            total_deleted = 0
            
            for table in tables_to_clear:
                try:
                    # Check if table exists
                    result = await session.execute(
                        text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                    )
                    
                    if result.fetchone():
                        # Get count before deletion
                        count_result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = count_result.scalar()
                        
                        if count > 0:
                            # Delete all records
                            await session.execute(text(f"DELETE FROM {table}"))
                            logger.info(f"🗑️ Cleared {count} records from {table}")
                            total_deleted += count
                        else:
                            logger.info(f"✅ Table {table} was already empty")
                    else:
                        logger.info(f"ℹ️ Table {table} does not exist (skipping)")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error clearing table {table}: {e}")
                    continue
            
            # Reset auto-increment sequences
            try:
                await session.execute(text("UPDATE sqlite_sequence SET seq = 0"))
                logger.info("🔄 Reset auto-increment sequences")
            except Exception as e:
                logger.info(f"ℹ️ No sequences to reset: {e}")
            
            await session.commit()
            logger.info(f"✅ SQLite cleared successfully - {total_deleted} total records deleted")
            
    except Exception as e:
        logger.error(f"❌ Error clearing SQLite: {e}")


async def verify_cleanup():
    """Verify that all data has been cleared."""
    logger.info("🔍 Verifying cleanup...")
    
    # Check Redis
    try:
        from config.settings import settings
        redis_client = await aioredis.from_url(settings.redis_url, decode_responses=True)
        redis_keys = await redis_client.keys("*")
        logger.info(f"📊 Redis keys remaining: {len(redis_keys)}")
        
        if redis_keys:
            logger.info(f"🔍 Remaining Redis keys: {redis_keys[:10]}...")  # Show first 10
        
        await redis_client.aclose()
    except Exception as e:
        logger.error(f"❌ Error checking Redis: {e}")
    
    # Check SQLite
    if not SQLALCHEMY_AVAILABLE:
        logger.info("📊 SQLite check skipped - database dependencies not available")
        return
        
    try:
        async with get_db_session() as session:
            tables = ["customers", "test_bookings", "support_tickets", "ticket_messages", "agent_sessions"]
            
            for table in tables:
                try:
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    logger.info(f"📊 {table}: {count} records")
                except Exception as e:
                    logger.info(f"📊 {table}: table not found")
                    
    except Exception as e:
        logger.error(f"❌ Error checking SQLite: {e}")


async def main():
    """Main cleanup function."""
    logger.info("🚀 Starting database cleanup...")
    logger.info("⚠️  This will delete ALL user data from SQLite and Redis!")
    
    # Confirmation prompt
    if len(sys.argv) < 2 or sys.argv[1] != "--confirm":
        logger.info("❌ Please run with --confirm flag to proceed:")
        logger.info("   python scripts/clear-all-data.py --confirm")
        return
    
    logger.info("🔄 Proceeding with data cleanup...")
    
    # Clear Redis first
    await clear_redis_data()
    
    # Clear SQLite
    await clear_sqlite_data()
    
    # Verify cleanup
    await verify_cleanup()
    
    logger.info("✅ Database cleanup completed!")
    logger.info("🔄 All user sessions, orders, tickets, and conversation state cleared")
    logger.info("🚀 System is now ready for fresh start")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("❌ Cleanup interrupted by user")
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        sys.exit(1)