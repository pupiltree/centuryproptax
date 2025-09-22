"""
FastAPI routes for mock payment system.
Wraps the existing mock_razorpay service.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.payments.mock_razorpay import create_mock_razorpay_payment_link, verify_mock_payment_completion, get_mock_payment_data, complete_mock_payment

router = APIRouter(
    prefix="/api/payments",
    tags=["Mock Payments"],
    responses={404: {"description": "Not found"}}
)

@router.post("/create")
async def create_payment_link(payment_data: Dict[str, Any]):
    """Create a mock payment link."""
    try:
        return await create_mock_razorpay_payment_link(
            order_id=payment_data.get("order_id", f"order_{payment_data.get('amount', 0)}"),
            amount=payment_data.get("amount", 0),
            currency=payment_data.get("currency", "INR"),
            description=payment_data.get("description", "Property Tax Payment"),
            customer_name=payment_data.get("customer_name", "Customer"),
            customer_email=payment_data.get("customer_email", "customer@example.com"),
            customer_phone=payment_data.get("customer_phone", "+1234567890")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify/{order_id}")
async def verify_payment(order_id: str):
    """Verify a mock payment."""
    try:
        return await verify_mock_payment_completion(order_id=order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{payment_id}")
async def get_payment_status(payment_id: str):
    """Get payment status."""
    # Import MOCK_PAYMENTS from the service
    from services.payments.mock_razorpay import MOCK_PAYMENTS

    if payment_id not in MOCK_PAYMENTS:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {"payment_id": payment_id, "status": MOCK_PAYMENTS[payment_id]["status"]}