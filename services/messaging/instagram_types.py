"""Instagram messaging types and data classes."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class InstagramMessage:
    """Parsed Instagram message data."""
    sender_id: str
    message_id: str
    timestamp: int
    message_type: str  # "text", "quick_reply", "attachment", "postback"
    text: Optional[str] = None
    quick_reply_payload: Optional[str] = None
    attachments: Optional[list] = None


@dataclass
class IncomingMessage:
    """Incoming message from Instagram."""
    sender_id: str
    text: Optional[str] = None
    message_type: str = "text"
    payload: Optional[str] = None
    quick_reply_payload: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        # Ensure payload and quick_reply_payload are synced
        if self.payload and not self.quick_reply_payload:
            self.quick_reply_payload = self.payload
        elif self.quick_reply_payload and not self.payload:
            self.payload = self.quick_reply_payload


@dataclass 
class OutgoingResponse:
    """Outgoing response to Instagram."""
    text: str
    quick_replies: Optional[List[Dict[str, str]]] = None
    messaging_type: str = "RESPONSE"
    attachments: Optional[List[Dict[str, Any]]] = None