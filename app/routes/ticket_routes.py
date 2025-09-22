"""
FastAPI routes for ticket management system.
Wraps the existing ticket management service.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from services.ticket_management.ticket_service import TicketService

router = APIRouter(
    prefix="/api/tickets",
    tags=["Ticket Management"],
    responses={404: {"description": "Not found"}}
)

# Initialize ticket service
ticket_service = TicketService()

@router.post("/create")
async def create_ticket(ticket_data: Dict[str, Any]):
    """Create a new ticket."""
    try:
        return ticket_service.create_ticket(
            title=ticket_data.get("title", ""),
            description=ticket_data.get("description", ""),
            priority=ticket_data.get("priority", "medium"),
            customer_id=ticket_data.get("customer_id")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_tickets(limit: int = 10, offset: int = 0):
    """List tickets with pagination."""
    try:
        return ticket_service.list_tickets(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get ticket by ID."""
    try:
        ticket = ticket_service.get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return ticket
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, status_data: Dict[str, str]):
    """Update ticket status."""
    try:
        return ticket_service.update_status(
            ticket_id=ticket_id,
            status=status_data.get("status")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def ticket_health():
    """Health check for ticket service."""
    return {"status": "healthy", "service": "ticket_management"}