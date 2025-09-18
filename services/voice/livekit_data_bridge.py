"""
LiveKit Data Bridge - Real-time communication between chat and voice servers.
Replaces database polling with instant LiveKit data streams.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
import os
from dotenv import load_dotenv

from livekit import api as lk_api
from livekit.protocol.models import DataPacket

load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class PrescriptionMessage:
    """Structured message for prescription data"""
    message_type: str  # "prescription_ready", "prescription_failed", "status_update"
    phone_number: str
    data: Dict[str, Any]
    timestamp: str
    session_id: Optional[str] = None

class LiveKitDataBridge:
    """
    Real-time data bridge between chat and voice servers using LiveKit data streams.
    Replaces inefficient database polling with instant communication.
    """

    def __init__(self):
        self.livekit_url = os.getenv("LIVEKIT_URL")
        self.livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        self.livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")

        if not all([self.livekit_url, self.livekit_api_key, self.livekit_api_secret]):
            raise ValueError("Missing LiveKit credentials for data bridge")

        self.api = lk_api.LiveKitAPI(
            url=self.livekit_url,
            api_key=self.livekit_api_key,
            api_secret=self.livekit_api_secret
        )

        # Simple in-memory room registry - LiveKit handles the complexity
        self._active_rooms: Dict[str, str] = {}  # phone_number -> room_name

        logger.info("✅ LiveKit Data Bridge initialized with simple room registry")

    async def register_voice_room(self, phone_number: str, room_name: str):
        """Register an active voice call room for data streaming"""
        self._active_rooms[phone_number] = room_name
        logger.info(f"🔊 Registered voice room for {phone_number[:5]}***: {room_name}")

    async def unregister_voice_room(self, phone_number: str):
        """Unregister voice room when call ends"""
        room_name = self._active_rooms.pop(phone_number, None)
        if room_name:
            logger.info(f"🔇 Unregistered voice room for {phone_number[:5]}***: {room_name}")

    async def _get_room_name(self, phone_number: str) -> Optional[str]:
        """Get room name for phone number"""
        return self._active_rooms.get(phone_number)

    async def send_prescription_data(
        self,
        phone_number: str,
        prescription_data: Dict[str, Any],
        confidence_score: float = 0.0
    ) -> bool:
        """
        Send prescription analysis results directly to voice agent via LiveKit data stream.
        Uses pattern matching to find PSTN voice rooms instead of registry.
        """
        try:
            # PSTN rooms follow pattern: call-_+{phone_number}_*
            # Extract the 10-digit number from full phone (e.g., 919179687775 -> 9179687775)
            if len(phone_number) >= 10:
                short_phone = phone_number[-10:]  # Last 10 digits
                room_pattern = f"call-_+91{short_phone}_"

                # Get list of active rooms and find matching PSTN room
                try:
                    rooms_response = await self.api.room.list_rooms(lk_api.ListRoomsRequest())

                    target_room = None
                    for room in rooms_response.rooms:
                        if room.name.startswith(room_pattern):
                            target_room = room.name
                            logger.info(f"🎯 Found PSTN voice room: {target_room} for {phone_number[:5]}***")
                            break

                    if not target_room:
                        logger.warning(f"❌ No active PSTN voice room found for pattern {room_pattern} (phone: {phone_number[:5]}***)")
                        return False

                    room_name = target_room

                except Exception as e:
                    logger.error(f"❌ Failed to list LiveKit rooms: {e}")
                    return False
            else:
                logger.warning(f"❌ Invalid phone number format: {phone_number[:5]}***")
                return False

            # Create prescription message
            message = PrescriptionMessage(
                message_type="prescription_ready",
                phone_number=phone_number,
                data={
                    "prescription_data": prescription_data,
                    "confidence_score": confidence_score,
                    "analysis_complete": True
                },
                timestamp=datetime.now().isoformat(),
                session_id=f"whatsapp_{phone_number}"
            )

            # Send via LiveKit data stream to voice room
            await self._send_data_to_room(room_name, "prescription_analysis", message)

            logger.info(f"✅ Sent prescription data to voice room {room_name} for {phone_number[:5]}***")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send prescription data via LiveKit: {e}")
            return False

    async def send_prescription_failure(
        self,
        phone_number: str,
        error_message: str,
        user_friendly_error: str = ""
    ) -> bool:
        """Send prescription analysis failure to voice agent"""
        try:
            room_name = await self._get_room_name(phone_number)
            if not room_name:
                logger.warning(f"❌ No active voice room for {phone_number[:5]}*** - cannot send failure")
                return False

            message = PrescriptionMessage(
                message_type="prescription_failed",
                phone_number=phone_number,
                data={
                    "error_message": error_message,
                    "user_friendly_error": user_friendly_error,
                    "analysis_complete": False
                },
                timestamp=datetime.now().isoformat()
            )

            await self._send_data_to_room(room_name, "prescription_analysis", message)

            logger.info(f"✅ Sent prescription failure to voice room {room_name} for {phone_number[:5]}***")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send prescription failure via LiveKit: {e}")
            return False

    async def send_status_update(
        self,
        phone_number: str,
        status: str,
        message: str = ""
    ) -> bool:
        """Send prescription processing status update to voice agent"""
        try:
            room_name = await self._get_room_name(phone_number)
            if not room_name:
                return False  # No active voice room, skip silently

            status_message = PrescriptionMessage(
                message_type="status_update",
                phone_number=phone_number,
                data={
                    "status": status,
                    "message": message
                },
                timestamp=datetime.now().isoformat()
            )

            await self._send_data_to_room(room_name, "prescription_status", status_message)

            logger.info(f"📊 Sent status update '{status}' to voice room {room_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send status update via LiveKit: {e}")
            return False

    async def _send_data_to_room(self, room_name: str, topic: str, message: PrescriptionMessage):
        """Internal method to send data to LiveKit room"""
        try:
            # Convert message to JSON
            message_json = json.dumps({
                "topic": topic,
                "message_type": message.message_type,
                "phone_number": message.phone_number,
                "data": message.data,
                "timestamp": message.timestamp,
                "session_id": message.session_id
            })

            # Send data to all participants in the room (including voice agent)
            await self.api.room.send_data(
                lk_api.SendDataRequest(
                    room=room_name,
                    data=message_json.encode('utf-8'),
                    kind=DataPacket.Kind.RELIABLE,  # Ensure delivery
                    topic=topic
                )
            )

            logger.info(f"📡 Sent LiveKit data to room {room_name}, topic: {topic}")

        except Exception as e:
            logger.error(f"❌ Failed to send data to LiveKit room {room_name}: {e}")
            raise

    async def is_voice_call_active(self, phone_number: str) -> bool:
        """Check if there's an active voice call for this phone number"""
        room_name = await self._get_room_name(phone_number)
        return room_name is not None

    async def get_active_voice_rooms(self) -> Dict[str, str]:
        """Get all active voice call rooms"""
        return self._active_rooms.copy()

# Global instance
_data_bridge: Optional[LiveKitDataBridge] = None

def get_livekit_data_bridge() -> LiveKitDataBridge:
    """Get singleton instance of LiveKit data bridge"""
    global _data_bridge
    if _data_bridge is None:
        _data_bridge = LiveKitDataBridge()
    return _data_bridge

async def notify_prescription_ready(
    phone_number: str,
    prescription_data: Dict[str, Any],
    confidence_score: float = 0.0
) -> bool:
    """
    Convenience function to notify voice agent that prescription is ready.
    Replaces: Redis polling and state management complexity
    """
    bridge = get_livekit_data_bridge()
    return await bridge.send_prescription_data(
        phone_number, prescription_data, confidence_score
    )

async def notify_prescription_failed(
    phone_number: str,
    error_message: str,
    user_friendly_error: str = ""
) -> bool:
    """Convenience function to notify voice agent of prescription analysis failure"""
    bridge = get_livekit_data_bridge()
    return await bridge.send_prescription_failure(
        phone_number, error_message, user_friendly_error
    )