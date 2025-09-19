"""
Generic message types for WhatsApp Business API integration.
Renamed from legacy Instagram naming conventions.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class WhatsAppMessage:
    """
    WhatsApp Business API message data structure.
    Used for all incoming messages from WhatsApp Business API.
    """
    sender_id: str  # WhatsApp user ID
    message_id: str
    timestamp: int
    message_type: str  # "text", "quick_reply", "attachment", "postback"
    text: Optional[str] = None
    quick_reply_payload: Optional[str] = None
    attachments: Optional[list] = None


# Backwards compatibility alias - will be removed
InstagramMessage = WhatsAppMessage