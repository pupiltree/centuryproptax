"""
Message Batching Service
Handles rapid user messages by batching them for better context processing.
Based on patterns from reference implementations.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog

from services.messaging.whatsapp_types import WhatsAppMessage as InstagramMessage
from src.core.logging import get_logger

logger = get_logger("message_batching")


@dataclass
class MessageBatch:
    """Represents a batch of messages from the same user."""
    user_id: str
    messages: List[InstagramMessage]
    created_at: datetime
    timeout: float
    
    def add_message(self, message: InstagramMessage) -> None:
        """Add a message to the batch."""
        self.messages.append(message)
    
    def is_expired(self) -> bool:
        """Check if batch has expired based on timeout."""
        return (datetime.now() - self.created_at).total_seconds() > self.timeout
    
    def get_combined_text(self) -> str:
        """Combine all message texts into one."""
        texts = [msg.text for msg in self.messages if msg.text]
        return " ".join(texts)
    
    def get_latest_message(self) -> InstagramMessage:
        """Get the most recent message with combined text."""
        latest = self.messages[-1]
        
        # Create combined message
        combined_message = InstagramMessage(
            sender_id=latest.sender_id,
            message_id=f"batch_{int(time.time())}",
            timestamp=int(time.time()),
            message_type=latest.message_type,
            text=self.get_combined_text(),
            quick_reply_payload=latest.quick_reply_payload,
            attachments=latest.attachments
        )
        
        return combined_message


class MessageBatcher:
    """
    Batches rapid messages from users to improve conversation quality.
    Based on reference implementation patterns.
    """
    
    def __init__(
        self, 
        batch_timeout: float = 3.0,  # Wait 3 seconds for additional messages
        max_batch_size: int = 5,     # Max messages per batch
        cleanup_interval: float = 60.0  # Clean expired batches every minute
    ):
        self.batch_timeout = batch_timeout
        self.max_batch_size = max_batch_size
        self.cleanup_interval = cleanup_interval
        
        # Active batches per user
        self.batches: Dict[str, MessageBatch] = {}
        
        # Processing locks per user to prevent race conditions
        self.processing_locks: Dict[str, asyncio.Lock] = {}
        
        # Message processing callbacks
        self.message_handlers: List[callable] = []
        
        # Start cleanup task (lazily to avoid event loop issues during import)
        self.cleanup_task = None
        
        logger.info(
            "Message batcher initialized", 
            timeout=batch_timeout,
            max_batch_size=max_batch_size
        )
    
    def add_message_handler(self, handler: callable) -> None:
        """Add a handler for processed message batches."""
        self.message_handlers.append(handler)
    
    async def _ensure_cleanup_task(self):
        """Ensure cleanup task is running."""
        if self.cleanup_task is None:
            try:
                self.cleanup_task = asyncio.create_task(self._cleanup_expired_batches())
                logger.debug("Cleanup task started")
            except RuntimeError:
                # No event loop running yet
                logger.debug("No event loop available for cleanup task")
    
    async def process_message(self, message: InstagramMessage) -> bool:
        """
        Process an incoming message with batching logic.
        Returns True if message was batched, False if processed immediately.
        """
        # Ensure cleanup task is running
        await self._ensure_cleanup_task()
        
        user_id = message.sender_id
        
        # Get or create processing lock for this user
        if user_id not in self.processing_locks:
            self.processing_locks[user_id] = asyncio.Lock()
        
        async with self.processing_locks[user_id]:
            return await self._handle_message_internal(message)
    
    async def _handle_message_internal(self, message: InstagramMessage) -> bool:
        """Internal message handling with batching logic."""
        user_id = message.sender_id
        
        # Check if user already has an active batch
        if user_id in self.batches:
            existing_batch = self.batches[user_id]
            
            # Add to existing batch if not expired and under size limit
            if not existing_batch.is_expired() and len(existing_batch.messages) < self.max_batch_size:
                existing_batch.add_message(message)
                logger.info(
                    "Message added to batch",
                    user_id=user_id,
                    batch_size=len(existing_batch.messages)
                )
                return True
            else:
                # Process expired batch and start new one
                await self._process_batch(existing_batch)
                del self.batches[user_id]
        
        # Handle special message types immediately (no batching)
        if self._should_process_immediately(message):
            await self._process_single_message(message)
            return False
        
        # Create new batch
        new_batch = MessageBatch(
            user_id=user_id,
            messages=[message],
            created_at=datetime.now(),
            timeout=self.batch_timeout
        )
        
        self.batches[user_id] = new_batch
        
        # Schedule batch processing after timeout
        asyncio.create_task(self._schedule_batch_processing(user_id, new_batch.created_at))
        
        logger.info("New message batch created", user_id=user_id)
        return True
    
    def _should_process_immediately(self, message: InstagramMessage) -> bool:
        """Determine if message should bypass batching."""
        if message.quick_reply_payload:
            return True  # Quick replies should be immediate
        
        if message.attachments:
            return True  # Media messages should be immediate
        
        if message.text:
            # Process commands immediately
            immediate_keywords = ['cancel', 'stop', 'help', 'report', 'status']
            text_lower = message.text.lower()
            if any(keyword in text_lower for keyword in immediate_keywords):
                return True
        
        return False
    
    async def _schedule_batch_processing(self, user_id: str, batch_created_at: datetime) -> None:
        """Schedule batch processing after timeout."""
        await asyncio.sleep(self.batch_timeout)
        
        # Check if batch still exists and hasn't been processed
        if user_id in self.batches:
            batch = self.batches[user_id]
            if batch.created_at == batch_created_at:  # Same batch
                async with self.processing_locks.get(user_id, asyncio.Lock()):
                    if user_id in self.batches:  # Double check after acquiring lock
                        await self._process_batch(self.batches[user_id])
                        del self.batches[user_id]
    
    async def _process_batch(self, batch: MessageBatch) -> None:
        """Process a complete message batch."""
        logger.info(
            "Processing message batch",
            user_id=batch.user_id,
            message_count=len(batch.messages),
            combined_text_length=len(batch.get_combined_text())
        )
        
        # Create combined message for processing
        combined_message = batch.get_latest_message()
        
        # Call all registered handlers
        for handler in self.message_handlers:
            try:
                await handler(combined_message, batch_info={
                    'is_batched': True,
                    'message_count': len(batch.messages),
                    'batch_duration': (datetime.now() - batch.created_at).total_seconds()
                })
            except Exception as e:
                logger.error(
                    "Error in message handler",
                    handler=handler.__name__,
                    error=str(e),
                    user_id=batch.user_id
                )
    
    async def _process_single_message(self, message: InstagramMessage) -> None:
        """Process a single message immediately."""
        logger.info("Processing single message immediately", user_id=message.sender_id)
        
        # Call all registered handlers
        for handler in self.message_handlers:
            try:
                await handler(message, batch_info={
                    'is_batched': False,
                    'message_count': 1,
                    'batch_duration': 0
                })
            except Exception as e:
                logger.error(
                    "Error in message handler",
                    handler=handler.__name__,
                    error=str(e),
                    user_id=message.sender_id
                )
    
    async def _cleanup_expired_batches(self) -> None:
        """Periodically clean up expired batches."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                expired_users = []
                for user_id, batch in self.batches.items():
                    if batch.is_expired():
                        expired_users.append(user_id)
                
                # Process expired batches
                for user_id in expired_users:
                    if user_id in self.processing_locks:
                        async with self.processing_locks[user_id]:
                            if user_id in self.batches:
                                await self._process_batch(self.batches[user_id])
                                del self.batches[user_id]
                
                if expired_users:
                    logger.info(f"Processed {len(expired_users)} expired batches")
                    
            except Exception as e:
                logger.error("Error in batch cleanup", error=str(e))
    
    async def force_process_user_batch(self, user_id: str) -> bool:
        """Force process any pending batch for a user."""
        if user_id in self.batches:
            async with self.processing_locks.get(user_id, asyncio.Lock()):
                if user_id in self.batches:
                    await self._process_batch(self.batches[user_id])
                    del self.batches[user_id]
                    return True
        return False
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """Get current batching statistics."""
        return {
            'active_batches': len(self.batches),
            'processing_locks': len(self.processing_locks),
            'batch_timeout': self.batch_timeout,
            'max_batch_size': self.max_batch_size,
            'batch_details': [
                {
                    'user_id': batch.user_id,
                    'message_count': len(batch.messages),
                    'age_seconds': (datetime.now() - batch.created_at).total_seconds(),
                    'expired': batch.is_expired()
                }
                for batch in self.batches.values()
            ]
        }
    
    async def shutdown(self) -> None:
        """Graceful shutdown - process all pending batches."""
        logger.info("Shutting down message batcher")
        
        # Cancel cleanup task if it exists
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # Process all remaining batches
        remaining_users = list(self.batches.keys())
        for user_id in remaining_users:
            await self.force_process_user_batch(user_id)
        
        logger.info(f"Processed {len(remaining_users)} remaining batches during shutdown")


# Global message batcher instance
message_batcher = MessageBatcher()