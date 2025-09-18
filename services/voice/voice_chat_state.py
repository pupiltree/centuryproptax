"""
Voice-Chat State Management System
Manages shared state between voice calls and chat system for prescription image processing.
"""

import asyncio
import json
import redis
import structlog
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = structlog.get_logger()

class VoiceChatStateManager:
    """Manages shared state between voice and chat systems using Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize with Redis connection for state management (same as chat server)."""
        self.redis_url = redis_url
        self.redis_client = None
        self.voice_call_prefix = "voice_call:"
        self.prescription_prefix = "prescription_context:"

        # Prescription data TTL (Time To Live) - expires after 2 hours
        self.prescription_ttl_seconds = 2 * 60 * 60  # 2 hours

    async def _get_redis_client(self):
        """Get or create Redis client."""
        if self.redis_client is None:
            import redis.asyncio as redis_async
            self.redis_client = redis_async.from_url(self.redis_url)
        return self.redis_client

    async def start_voice_call(self, customer_phone: str, voice_session_id: str) -> str:
        """Mark a voice call as active for a customer."""
        try:
            redis_client = await self._get_redis_client()

            call_state = {
                "customer_phone": customer_phone,
                "voice_session_id": voice_session_id,
                "call_active": True,
                "prescription_requested": False,
                "prescription_context": None,
                "started_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }

            # Store with 1 hour expiry
            await redis_client.setex(
                f"{self.voice_call_prefix}{customer_phone}",
                3600,
                json.dumps(call_state)
            )

            logger.info(f"🔊 Voice call started for {customer_phone[:5]}***",
                       session_id=voice_session_id)
            return voice_session_id

        except Exception as e:
            logger.error(f"Failed to start voice call state: {e}")
            return voice_session_id

    async def end_voice_call(self, customer_phone: str) -> bool:
        """Mark voice call as ended."""
        try:
            redis_client = await self._get_redis_client()
            await redis_client.delete(f"{self.voice_call_prefix}{customer_phone}")
            logger.info(f"🔊 Voice call ended for {customer_phone[:5]}***")
            return True
        except Exception as e:
            logger.error(f"Failed to end voice call state: {e}")
            return False

    async def is_voice_call_active(self, customer_phone: str) -> bool:
        """Check if a voice call is currently active for customer."""
        try:
            redis_client = await self._get_redis_client()
            call_data = await redis_client.get(f"{self.voice_call_prefix}{customer_phone}")

            if call_data:
                state = json.loads(call_data)
                return state.get("call_active", False)
            return False
        except Exception as e:
            logger.error(f"Failed to check voice call state: {e}")
            return False

    async def request_prescription_via_whatsapp(
        self,
        customer_phone: str,
        voice_session_id: str
    ) -> Dict[str, Any]:
        """Request prescription image via WhatsApp and update state."""
        try:
            redis_client = await self._get_redis_client()

            # Update voice call state
            call_data = await redis_client.get(f"{self.voice_call_prefix}{customer_phone}")
            if call_data:
                state = json.loads(call_data)
                state["prescription_requested"] = True
                state["prescription_request_time"] = datetime.now().isoformat()
                state["last_activity"] = datetime.now().isoformat()

                await redis_client.setex(
                    f"{self.voice_call_prefix}{customer_phone}",
                    3600,
                    json.dumps(state)
                )

            # Send WhatsApp message
            from services.messaging.whatsapp_client import get_whatsapp_client
            whatsapp_client = get_whatsapp_client()

            prescription_message = """📋 Hi! I'm Maya from Krishna Diagnostics.

You requested help with a prescription during our voice call. Please send me a clear photo of your prescription here, and I'll analyze it for you.

Make sure the prescription is clearly visible with:
✅ Doctor's name and signature
✅ Patient details
✅ Prescribed tests/medications
✅ Date of prescription

Send the image now and I'll get back to you on our voice call with the details! 📞"""

            if whatsapp_client.is_configured():
                result = await whatsapp_client.send_text_message(
                    to=customer_phone,
                    message=prescription_message
                )

                if result.get("success"):
                    logger.info(f"📱 Prescription request sent via WhatsApp to {customer_phone[:5]}***")
                    return {
                        "success": True,
                        "message": "I've sent you a WhatsApp message. Please check your phone and send me the prescription image there. I'll wait here while you do that.",
                        "whatsapp_sent": True
                    }
                else:
                    error_details = result.get("details", {})
                    error_code = error_details.get("error", {}).get("code")

                    # Handle specific WhatsApp API errors
                    if error_code == 131030:  # Phone number not in allowed list
                        logger.warning(f"📱 Phone number {customer_phone[:5]}*** not in WhatsApp allowed list (development mode)")
                        return {
                            "success": False,
                            "message": "Your phone number isn't set up for WhatsApp messaging in our test system yet. No worries! Please describe your prescription details to me verbally instead - I can help you just as well.",
                            "whatsapp_sent": False,
                            "error_code": "phone_not_allowed"
                        }
                    else:
                        logger.error(f"Failed to send WhatsApp message: {result}")
                        return {
                            "success": False,
                            "message": "I'm having trouble sending the WhatsApp message right now. Could you please tell me the prescription details verbally instead?",
                            "whatsapp_sent": False,
                            "error_code": "send_failed"
                        }
            else:
                logger.warning("WhatsApp client not configured")
                return {
                    "success": False,
                    "message": "I'm unable to send WhatsApp messages right now. Could you please describe the prescription details to me verbally?",
                    "whatsapp_sent": False
                }

        except Exception as e:
            logger.error(f"Failed to request prescription via WhatsApp: {e}")
            return {
                "success": False,
                "message": "I'm having technical difficulties. Could you please describe the prescription details verbally instead?",
                "error": str(e)
            }

    async def set_prescription_processing_status(
        self,
        customer_phone: str,
        status: str,
        message: str = None,
        prescription_data: Dict[str, Any] = None
    ) -> bool:
        """Set prescription processing status (pending, processing, completed, failed)."""
        try:
            redis_client = await self._get_redis_client()

            call_data = await redis_client.get(f"{self.voice_call_prefix}{customer_phone}")
            if call_data:
                state = json.loads(call_data)

                # Always overwrite previous prescription status
                old_status = state.get("prescription_status", "none")
                state["prescription_status"] = status
                state["prescription_status_message"] = message
                state["prescription_status_updated"] = datetime.now().isoformat()
                state["last_activity"] = datetime.now().isoformat()

                # Store prescription data with TTL if provided (overwrites previous data)
                if prescription_data:
                    state["prescription_data"] = prescription_data
                    state["prescription_created_at"] = datetime.now().isoformat()

                    # Log prescription overwrite if there was previous data
                    if old_status == "completed" and state.get("prescription_data"):
                        old_patient = state.get("prescription_data", {}).get("patient_name", "Unknown")
                        new_patient = prescription_data.get("patient_name", "Unknown")
                        logger.info(f"🔄 Overwriting prescription data for {customer_phone[:5]}***: {old_patient} → {new_patient}")

                # Set TTL based on prescription data presence
                ttl = self.prescription_ttl_seconds if prescription_data else 3600

                await redis_client.setex(
                    f"{self.voice_call_prefix}{customer_phone}",
                    ttl,
                    json.dumps(state)
                )

                logger.info(f"📊 Prescription status updated for {customer_phone[:5]}***: {status} (TTL: {ttl}s)")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to set prescription status: {e}")
            return False

    async def get_prescription_processing_status(self, customer_phone: str) -> Dict[str, Any]:
        """Get current prescription processing status with TTL expiry check from actual Redis schema."""
        try:
            redis_client = await self._get_redis_client()

            # Check the actual Redis key format used by chat server
            context_key = f"context:session_{customer_phone}_whatsapp_healthcare"
            context_data = await redis_client.get(context_key)

            logger.info(f"🔍 Looking for prescription in Redis key: {context_key}")

            if context_data:
                context = json.loads(context_data)
                prescription_analysis = context.get("prescription_analysis")

                if prescription_analysis and prescription_analysis.get("type") == "prescription_analysis":
                    prescription_data = prescription_analysis.get("prescription_data")
                    confidence_score = prescription_analysis.get("confidence_score", 0)
                    timestamp_str = prescription_analysis.get("timestamp")

                    logger.info(f"✅ Found prescription data for {prescription_data.get('patient_name', 'Unknown')} in Redis")

                    # Check if prescription data has expired (TTL check)
                    if timestamp_str:
                        try:
                            from datetime import datetime
                            # Parse timestamp format: "2025-09-16 12:49:03.666595"
                            created_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                            current_time = datetime.now()
                            age_seconds = (current_time - created_time).total_seconds()

                            if age_seconds > self.prescription_ttl_seconds:
                                # Prescription data expired
                                logger.info(f"⏰ Prescription data expired for {customer_phone[:5]}*** (age: {age_seconds:.0f}s > {self.prescription_ttl_seconds}s)")

                                # Delete expired data
                                await redis_client.delete(context_key)

                                return {
                                    "status": "none",
                                    "message": "Prescription data has expired. Please send a new prescription.",
                                    "updated_at": timestamp_str,
                                    "prescription_data": None,
                                    "expired": True
                                }
                        except Exception as e:
                            logger.error(f"Error checking prescription TTL: {e}")

                    # Add confidence_score to prescription_data for voice agent
                    if prescription_data:
                        prescription_data["confidence_score"] = confidence_score

                    return {
                        "status": "completed",
                        "message": "Analysis completed successfully",
                        "updated_at": timestamp_str,
                        "prescription_data": prescription_data,
                        "expired": False
                    }

            # Check voice call state as fallback (for voice-initiated prescriptions)
            call_data = await redis_client.get(f"{self.voice_call_prefix}{customer_phone}")
            if call_data:
                state = json.loads(call_data)
                prescription_data = state.get("prescription_data") or state.get("prescription_context")

                if prescription_data:
                    logger.info(f"✅ Found prescription data in voice call state for {prescription_data.get('patient_name', 'Unknown')}")
                    return {
                        "status": state.get("prescription_status", "completed"),
                        "message": state.get("prescription_status_message", "Found in voice call state"),
                        "updated_at": state.get("prescription_status_updated"),
                        "prescription_data": prescription_data,
                        "expired": False
                    }

            logger.info(f"❌ No prescription data found for {customer_phone[:5]}*** in Redis")
            return {"status": "none", "message": None, "updated_at": None, "prescription_data": None, "expired": False}

        except Exception as e:
            logger.error(f"Failed to get prescription status: {e}")
            return {"status": "error", "message": str(e), "updated_at": None, "prescription_data": None, "expired": False}

    async def save_prescription_context(
        self,
        customer_phone: str,
        prescription_data: Dict[str, Any]
    ) -> bool:
        """Save prescription analysis results for voice call with overwriting and TTL."""
        try:
            redis_client = await self._get_redis_client()

            # Update voice call state with prescription context
            call_data = await redis_client.get(f"{self.voice_call_prefix}{customer_phone}")
            if call_data:
                state = json.loads(call_data)

                # Check if overwriting existing prescription data
                old_prescription = state.get("prescription_data") or state.get("prescription_context")
                if old_prescription:
                    old_patient = old_prescription.get("patient_name", "Unknown")
                    new_patient = prescription_data.get("patient_name", "Unknown")
                    logger.info(f"🔄 Overwriting prescription context for {customer_phone[:5]}***: {old_patient} → {new_patient}")

                # Save new prescription data (overwrites any existing data)
                state["prescription_context"] = prescription_data
                state["prescription_data"] = prescription_data  # Ensure both keys are set
                state["prescription_analyzed"] = True
                state["prescription_analyzed_at"] = datetime.now().isoformat()
                state["prescription_created_at"] = datetime.now().isoformat()  # For TTL tracking
                state["prescription_status"] = "completed"
                state["prescription_status_message"] = "Analysis completed successfully"
                state["last_activity"] = datetime.now().isoformat()

                # Set prescription TTL
                await redis_client.setex(
                    f"{self.voice_call_prefix}{customer_phone}",
                    self.prescription_ttl_seconds,  # 2 hours TTL
                    json.dumps(state)
                )

                patient_name = prescription_data.get("patient_name", "Unknown")
                logger.info(f"💾 Prescription context saved for voice call {customer_phone[:5]}*** ({patient_name}, TTL: {self.prescription_ttl_seconds}s)")
                return True

            return False
        except Exception as e:
            logger.error(f"Failed to save prescription context: {e}")
            return False

    async def get_prescription_context(self, customer_phone: str) -> Optional[Dict[str, Any]]:
        """Get prescription analysis results for voice call."""
        try:
            redis_client = await self._get_redis_client()
            call_data = await redis_client.get(f"{self.voice_call_prefix}{customer_phone}")

            if call_data:
                state = json.loads(call_data)
                return state.get("prescription_context")
            return None
        except Exception as e:
            logger.error(f"Failed to get prescription context: {e}")
            return None

    async def get_voice_call_state(self, customer_phone: str) -> Optional[Dict[str, Any]]:
        """Get complete voice call state."""
        try:
            redis_client = await self._get_redis_client()
            call_data = await redis_client.get(f"{self.voice_call_prefix}{customer_phone}")

            if call_data:
                return json.loads(call_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get voice call state: {e}")
            return None

    async def update_activity(self, customer_phone: str) -> None:
        """Update last activity timestamp."""
        try:
            redis_client = await self._get_redis_client()
            call_data = await redis_client.get(f"{self.voice_call_prefix}{customer_phone}")

            if call_data:
                state = json.loads(call_data)
                state["last_activity"] = datetime.now().isoformat()

                await redis_client.setex(
                    f"{self.voice_call_prefix}{customer_phone}",
                    3600,
                    json.dumps(state)
                )
        except Exception as e:
            logger.error(f"Failed to update activity: {e}")

# Global instance
_voice_chat_state_manager = None

def get_voice_chat_state_manager() -> VoiceChatStateManager:
    """Get or create global voice-chat state manager."""
    global _voice_chat_state_manager
    if _voice_chat_state_manager is None:
        _voice_chat_state_manager = VoiceChatStateManager()
    return _voice_chat_state_manager