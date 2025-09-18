#!/usr/bin/env python3
"""
Clear only session data (Redis) while preserving order/ticket history.
This clears:
- All conversation state and checkpoints
- Active sessions and batches
- Cached order data
- But keeps: SQLite customer/booking/ticket records
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger()


async def clear_session_data():
    """Clear only session-related Redis data."""
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
        
        # Categorize keys
        session_keys = []
        checkpoint_keys = []
        order_cache_keys = []
        ticket_keys = []
        other_keys = []
        
        for key in all_keys:
            if key.startswith("session_") or key.startswith("user_batch_"):
                session_keys.append(key)
            elif key.startswith("checkpoint:") or key.startswith("langgraph:"):
                checkpoint_keys.append(key)
            elif key.startswith("order:") or key.startswith("customer_orders:"):
                order_cache_keys.append(key)
            elif key.startswith("ticket_status:") or key.startswith("active_tickets") or key.startswith("agent_response:"):
                ticket_keys.append(key)
            else:
                other_keys.append(key)
        
        # Show what we found
        logger.info(f"📊 Found keys:")
        logger.info(f"   🔄 Session keys: {len(session_keys)}")
        logger.info(f"   💾 Checkpoint keys: {len(checkpoint_keys)}")
        logger.info(f"   📦 Order cache keys: {len(order_cache_keys)}")
        logger.info(f"   🎫 Ticket keys: {len(ticket_keys)}")
        logger.info(f"   ❓ Other keys: {len(other_keys)}")
        
        # Delete session and checkpoint keys
        keys_to_delete = session_keys + checkpoint_keys
        
        if keys_to_delete:
            await redis_client.delete(*keys_to_delete)
            logger.info(f"🗑️ Deleted {len(keys_to_delete)} session/checkpoint keys")
        
        # Optionally clear order cache (ask user)
        if order_cache_keys:
            logger.info(f"❓ Found {len(order_cache_keys)} order cache keys")
            logger.info("   (These are temporary cached orders, safe to delete)")
            await redis_client.delete(*order_cache_keys)
            logger.info("🗑️ Cleared order cache keys")
        
        # Keep ticket keys (they're needed for active tickets)
        if ticket_keys:
            logger.info(f"✅ Preserved {len(ticket_keys)} ticket-related keys")
        
        # Show other keys but don't delete
        if other_keys:
            logger.info(f"ℹ️ Other keys preserved: {other_keys}")
        
        logger.info("✅ Session cleanup completed successfully")
        await redis_client.aclose()
        
    except Exception as e:
        logger.error(f"❌ Error clearing session data: {e}")


async def main():
    """Main session cleanup function."""
    logger.info("🚀 Starting session cleanup...")
    logger.info("🔄 This will clear conversation state and sessions only")
    logger.info("💾 Database records (customers, orders, tickets) will be preserved")
    
    await clear_session_data()
    
    logger.info("✅ Session cleanup completed!")
    logger.info("🔄 All conversation state cleared - users will start fresh conversations")
    logger.info("💾 Order history and tickets preserved in database")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("❌ Cleanup interrupted by user")
    except Exception as e:
        logger.error(f"❌ Session cleanup failed: {e}")
        sys.exit(1)