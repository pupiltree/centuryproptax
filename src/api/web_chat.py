"""
Web Chat API endpoints for Century Property Tax demo.
Provides WebSocket-based chat interface and web UI serving.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Set
import json
import uuid
from datetime import datetime
import asyncio

from services.messaging.modern_integrated_webhook_handler import ModernIntegratedWebhookHandler
from src.core.logging import get_logger

logger = get_logger("web_chat")
router = APIRouter(prefix="/chat", tags=["Web Chat"])

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}
user_sessions: Dict[str, str] = {}  # websocket_id -> session_id mapping

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Initialize message handler
webhook_handler = ModernIntegratedWebhookHandler()


class ConnectionManager:
    """Manages WebSocket connections for chat sessions."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str):
        """Remove WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")

    async def send_message(self, session_id: str, message: dict):
        """Send message to specific session."""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {session_id}: {e}")
                self.disconnect(session_id)

manager = ConnectionManager()


@router.get("/", response_class=HTMLResponse)
async def get_chat_interface(request: Request):
    """Serve the main chat interface."""
    return templates.TemplateResponse("chat.html", {"request": request})


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    await manager.connect(websocket, session_id)

    try:
        # Send welcome message
        await manager.send_message(session_id, {
            "type": "system",
            "message": "Connected to Century Property Tax Assistant",
            "timestamp": datetime.now().isoformat()
        })

        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Extract user message
            user_message = message_data.get("message", "").strip()
            logger.info(f"Received message from {session_id}: {user_message}")
            if not user_message:
                continue

            # Send typing indicator
            await manager.send_message(session_id, {
                "type": "typing",
                "timestamp": datetime.now().isoformat()
            })

            # Process message through property tax assistant
            try:
                # Use web session format for consistency
                web_session_id = f"session_{session_id}_web_property_tax"

                # Create mock WhatsApp-style message data for compatibility
                mock_message_data = {
                    "id": str(uuid.uuid4()),
                    "from": session_id,
                    "text": {"body": user_message},
                    "type": "text",
                    "timestamp": str(int(datetime.now().timestamp()))
                }

                # Process through the integrated handler
                response = await webhook_handler._handle_web_message(
                    message_data=mock_message_data,
                    session_id=web_session_id,
                    platform="web"
                )

                # Send assistant response
                if response:
                    # Ensure response is a proper string
                    response_text = str(response) if response else "I'm here to help you with property tax inquiries. How can I assist you today?"
                    logger.info(f"Sending response: {response_text[:100]}...")

                    await manager.send_message(session_id, {
                        "type": "assistant",
                        "message": response_text,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    await manager.send_message(session_id, {
                        "type": "assistant",
                        "message": "I'm here to help you with property tax inquiries. How can I assist you today?",
                        "timestamp": datetime.now().isoformat()
                    })

            except Exception as e:
                logger.error(f"Error processing message from {session_id}: {e}")
                await manager.send_message(session_id, {
                    "type": "assistant",
                    "message": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}")
        manager.disconnect(session_id)


@router.post("/reset/{session_id}")
async def reset_session(session_id: str):
    """Reset chat session for fresh start."""
    try:
        web_session_id = f"session_{session_id}_web_property_tax"

        # Clear Redis conversation history
        from services.conversation.redis_store import RedisConversationStore
        conversation_store = RedisConversationStore()
        await conversation_store.clear_conversation(web_session_id)

        # Notify connected client if any
        if session_id in manager.active_connections:
            await manager.send_message(session_id, {
                "type": "system",
                "message": "Chat session reset. How can I help you today?",
                "timestamp": datetime.now().isoformat()
            })

        return {"status": "success", "message": "Session reset successfully"}

    except Exception as e:
        logger.error(f"Error resetting session {session_id}: {e}")
        return {"status": "error", "message": "Failed to reset session"}


@router.get("/health")
async def chat_health():
    """Health check for web chat system."""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }