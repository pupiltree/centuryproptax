"""
FastAPI webhook routes for Razorpay integration.
Wraps the existing razorpay integration service.
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

router = APIRouter(
    prefix="/webhooks/razorpay",
    tags=["Razorpay Webhooks"],
    responses={404: {"description": "Not found"}}
)

@router.post("/payment")
async def razorpay_payment_webhook(request: Request):
    """Handle Razorpay payment webhooks."""
    try:
        # Get raw body for signature verification
        body = await request.body()

        # For now, just log and return success
        # In production, this should verify signature and process payment
        return {"status": "received", "message": "Webhook processed"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoint."""
    return {"status": "healthy", "service": "razorpay_webhook"}