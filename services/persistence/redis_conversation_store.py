"""
Simple Redis Conversation Storage using official redis-py.
Replaces the complex LangGraph RedisSaver with a straightforward conversation persistence.
"""

import json
import redis
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
from src.core.logging import get_logger

logger = get_logger("redis_conversation_store")


class RedisConversationStore:
    """Simple Redis-based conversation storage using official redis-py."""
    
    def __init__(self, redis_url: str, ttl_hours: int = 24):
        """
        Initialize Redis conversation store.
        
        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")
            ttl_hours: Time to live for conversations in hours
        """
        self.ttl_hours = ttl_hours
        self.ttl_seconds = ttl_hours * 3600
        self.logger = logger
        
        try:
            # Use official redis-py with decode_responses=True for easier handling
            self.redis_client = redis.from_url(
                redis_url, 
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            self.logger.info(f"✅ Redis conversation store connected successfully (TTL: {ttl_hours}h)")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    def _get_conversation_key(self, session_id: str) -> str:
        """Get Redis key for conversation."""
        return f"conversation:{session_id}"
    
    def _get_context_key(self, session_id: str) -> str:
        """Get Redis key for conversation context."""
        return f"context:{session_id}"
    
    def save_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save a single message to conversation history.
        
        Args:
            session_id: Unique session identifier
            role: Message role ("user", "assistant", "system")
            content: Message content
            metadata: Optional metadata (tool calls, etc.)
            
        Returns:
            True if saved successfully
        """
        try:
            conversation_key = self._get_conversation_key(session_id)
            
            message = {
                "timestamp": datetime.now().isoformat(),
                "role": role,
                "content": content,
                "metadata": metadata or {}
            }
            
            # Add message to conversation list and set TTL
            pipeline = self.redis_client.pipeline()
            pipeline.lpush(conversation_key, json.dumps(message))
            pipeline.expire(conversation_key, self.ttl_seconds)
            pipeline.execute()
            
            self.logger.debug(f"💾 Saved {role} message to {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save message: {e}")
            return False
    
    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of messages in chronological order (oldest first)
        """
        try:
            conversation_key = self._get_conversation_key(session_id)
            
            # Get messages (they're stored newest first, so reverse them)
            messages_json = self.redis_client.lrange(conversation_key, 0, limit - 1)
            
            messages = []
            for msg_json in reversed(messages_json):  # Reverse to get chronological order
                try:
                    message = json.loads(msg_json)
                    messages.append(message)
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to decode message: {msg_json}")
            
            self.logger.debug(f"📜 Retrieved {len(messages)} messages for {session_id}")
            return messages
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get conversation history: {e}")
            return []
    
    def save_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """
        Save conversation context (customer info, current state, etc.).
        
        Args:
            session_id: Session identifier
            context: Context dictionary
            
        Returns:
            True if saved successfully
        """
        try:
            context_key = self._get_context_key(session_id)
            context_data = {
                "updated_at": datetime.now().isoformat(),
                **context
            }
            
            # Save context and set TTL
            pipeline = self.redis_client.pipeline()
            pipeline.set(context_key, json.dumps(context_data))
            pipeline.expire(context_key, self.ttl_seconds)
            pipeline.execute()
            
            self.logger.debug(f"📋 Saved context for {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save context: {e}")
            return False
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get conversation context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context dictionary (empty if not found)
        """
        try:
            context_key = self._get_context_key(session_id)
            context_json = self.redis_client.get(context_key)
            
            if context_json:
                context = json.loads(context_json)
                self.logger.debug(f"📋 Retrieved context for {session_id}")
                return context
            else:
                self.logger.debug(f"📋 No context found for {session_id}")
                return {}
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get context: {e}")
            return {}
    
    def clear_conversation(self, session_id: str) -> bool:
        """
        Clear conversation history and context for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if cleared successfully
        """
        try:
            conversation_key = self._get_conversation_key(session_id)
            context_key = self._get_context_key(session_id)
            
            # Delete both keys
            deleted = self.redis_client.delete(conversation_key, context_key)
            
            self.logger.info(f"🗑️ Cleared conversation for {session_id} (deleted {deleted} keys)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to clear conversation: {e}")
            return False
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions."""
        try:
            # Get all conversation keys
            conversation_keys = self.redis_client.keys("conversation:*")
            context_keys = self.redis_client.keys("context:*")
            
            stats = {
                "active_conversations": len(conversation_keys),
                "stored_contexts": len(context_keys),
                "ttl_hours": self.ttl_hours,
                "redis_connected": True
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get session stats: {e}")
            return {
                "active_conversations": 0,
                "stored_contexts": 0,
                "ttl_hours": self.ttl_hours,
                "redis_connected": False,
                "error": str(e)
            }
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False


# Global instance - will be initialized when needed
_conversation_store = None

def get_conversation_store(redis_url: str = None) -> RedisConversationStore:
    """Get or create global conversation store instance."""
    global _conversation_store
    
    if _conversation_store is None:
        import os
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _conversation_store = RedisConversationStore(redis_url, ttl_hours=24)
    
    return _conversation_store

def reset_conversation_store():
    """Reset global conversation store instance."""
    global _conversation_store
    _conversation_store = None