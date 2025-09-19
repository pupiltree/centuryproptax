"""
Mock Razorpay Payment System for Testing
Creates realistic payment links using ngrok URL when Razorpay credentials are not available.
"""

import os
import json
import uuid
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import structlog

from langchain_core.tools import tool

logger = structlog.get_logger()

# Mock payment storage (in production, use Redis/Database)
MOCK_PAYMENTS = {}
MOCK_PAYMENT_LINKS = {}

# Base URL configuration (from environment)
BASE_URL = os.getenv("BASE_URL", "https://valid-immensely-martin.ngrok-free.app")

# Payment configuration from environment
PAYMENT_LINK_EXPIRY_HOURS = int(os.getenv("PAYMENT_LINK_EXPIRY_HOURS", "24"))
MOCK_PAYMENT_SUCCESS_DELAY = int(os.getenv("MOCK_PAYMENT_SUCCESS_DELAY", "2"))
WEBHOOK_TIMEOUT = int(os.getenv("WEBHOOK_TIMEOUT", "20"))


class MockRazorpayService:
    """Mock Razorpay service that mimics real Razorpay behavior."""
    
    def __init__(self):
        self.logger = logger.bind(component="mock_razorpay")
        self.mock_webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "mock_webhook_secret_2025")
        
    def create_payment_link(
        self,
        amount: float,
        customer_name: str,
        customer_phone: str,
        customer_email: str = None,
        description: str = "Payment for property tax services",
        reference_id: str = None,
        callback_url: str = None,
        notes: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Create a mock payment link that redirects to our ngrok URL."""
        
        try:
            # Generate mock payment link ID
            payment_link_id = f"plink_mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8].upper()}"
            
            # Create mock payment link URL using configurable BASE_URL
            payment_link_url = f"{BASE_URL}/mock-payment/{payment_link_id}"
            
            # Calculate expiry (configurable hours)
            expires_at = datetime.now() + timedelta(hours=PAYMENT_LINK_EXPIRY_HOURS)
            
            # Store payment link details for verification
            payment_link_data = {
                "id": payment_link_id,
                "amount": amount,
                "currency": "INR",
                "customer": {
                    "name": customer_name,
                    "phone": customer_phone,
                    "email": customer_email
                },
                "description": description,
                "reference_id": reference_id,
                "status": "created",
                "created_at": datetime.now().timestamp(),
                "expire_by": expires_at.timestamp(),
                "short_url": payment_link_url,
                "notes": notes or {}
            }
            
            MOCK_PAYMENT_LINKS[payment_link_id] = payment_link_data
            
            self.logger.info(f"Mock payment link created: {payment_link_id}")
            
            return {
                "success": True,
                "payment_link_id": payment_link_id,
                "payment_link": payment_link_url,
                "amount": amount,
                "currency": "INR",
                "status": "created",
                "expires_at": int(expires_at.timestamp()),
                "created_at": int(datetime.now().timestamp()),
                "customer": payment_link_data["customer"]
            }
            
        except Exception as e:
            self.logger.error(f"Mock payment link creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_payment_details(self, payment_id: str) -> Dict[str, Any]:
        """Get mock payment details."""
        
        if payment_id in MOCK_PAYMENTS:
            payment = MOCK_PAYMENTS[payment_id]
            return {
                "success": True,
                "payment_id": payment["id"],
                "order_id": payment.get("order_id"),
                "amount": payment["amount"],
                "currency": payment["currency"],
                "status": payment["status"],
                "method": payment.get("method", "card"),
                "email": payment.get("email"),
                "contact": payment.get("contact"),
                "created_at": payment["created_at"],
                "captured": payment["status"] == "captured"
            }
        else:
            return {
                "success": False,
                "error": "Payment not found"
            }
    
    def get_payment_link_details(self, payment_link_id: str) -> Dict[str, Any]:
        """Get mock payment link details."""
        
        if payment_link_id in MOCK_PAYMENT_LINKS:
            link = MOCK_PAYMENT_LINKS[payment_link_id]
            return {
                "success": True,
                "payment_link_id": link["id"],
                "amount": link["amount"],
                "amount_paid": link.get("amount_paid", 0),
                "status": link["status"],
                "description": link["description"],
                "reference_id": link.get("reference_id"),
                "short_url": link["short_url"],
                "customer": link["customer"],
                "created_at": link["created_at"],
                "expire_by": link.get("expire_by"),
                "payments": link.get("payments", [])
            }
        else:
            return {
                "success": False,
                "error": "Payment link not found"
            }
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify mock webhook signature."""
        try:
            expected_signature = hmac.new(
                self.mock_webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False
    
    def simulate_payment_success(
        self, 
        payment_link_id: str, 
        customer_name: str = None,
        payment_method: str = "card"
    ) -> Dict[str, Any]:
        """Simulate successful payment for testing."""
        
        if payment_link_id not in MOCK_PAYMENT_LINKS:
            return {"success": False, "error": "Payment link not found"}
        
        link_data = MOCK_PAYMENT_LINKS[payment_link_id]
        
        # Create mock payment
        payment_id = f"pay_mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8].upper()}"
        
        payment_data = {
            "id": payment_id,
            "amount": link_data["amount"],
            "currency": "INR",
            "status": "captured",
            "method": payment_method,
            "order_id": link_data.get("reference_id"),
            "email": link_data["customer"].get("email"),
            "contact": link_data["customer"]["phone"],
            "created_at": datetime.now().timestamp(),
            "payment_link_id": payment_link_id
        }
        
        MOCK_PAYMENTS[payment_id] = payment_data
        
        # Update payment link status
        MOCK_PAYMENT_LINKS[payment_link_id]["status"] = "paid"
        MOCK_PAYMENT_LINKS[payment_link_id]["amount_paid"] = link_data["amount"]
        MOCK_PAYMENT_LINKS[payment_link_id]["payments"] = [payment_data]
        
        self.logger.info(f"Mock payment completed: {payment_id} for link {payment_link_id}")
        
        return {
            "success": True,
            "payment_id": payment_id,
            "payment_link_id": payment_link_id,
            "amount": payment_data["amount"],
            "status": "captured",
            "method": payment_method
        }


# Initialize mock service
mock_razorpay_service = MockRazorpayService()


@tool
async def create_mock_razorpay_payment_link(
    order_id: str,
    amount: float,
    customer_name: str,
    customer_phone: str,
    customer_email: str = None,
    description: str = "Payment for property tax services"
) -> Dict[str, Any]:
    """
    Create mock Razorpay payment link using ngrok URL.
    
    This is used when real Razorpay credentials are not available.
    Creates a realistic payment experience for testing.
    
    Args:
        order_id: Internal order ID for reference
        amount: Payment amount in INR
        customer_name: Customer's name
        customer_phone: Customer's phone number
        customer_email: Customer's email (optional)
        description: Payment description
        
    Returns:
        Mock payment link creation result
    """
    try:
        result = mock_razorpay_service.create_payment_link(
            amount=amount,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            description=description,
            reference_id=order_id,
            callback_url=f"{BASE_URL}/webhook/mock-razorpay/callback",
            notes={
                "order_id": order_id,
                "service": "century_property_tax",
                "created_by": "chatbot_mock"
            }
        )
        
        if result["success"]:
            return {
                "success": True,
                "payment_link_id": result["payment_link_id"],
                "payment_link": result["payment_link"],
                "amount": result["amount"],
                "order_id": order_id,
                "status": "created",
                "expires_at": result["expires_at"],
                "message": f"🧪 TEST Payment link: {result['payment_link']}",
                "instructions": [
                    "This is a TEST payment link - no real money charged",
                    "Click the link to simulate payment",
                    "Use test data for payment simulation",
                    "Payment will be processed instantly"
                ],
                "security_note": "Mock payment system with webhook simulation",
                "test_mode": True
            }
        else:
            return result
            
    except Exception as e:
        logger.error(f"Mock payment link creation error: {e}")
        return {
            "success": False,
            "error": "Failed to create mock payment link"
        }


@tool
async def verify_mock_payment_completion(
    order_id: str,
    payment_id: Optional[str] = None,
    instagram_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify mock payment completion for anti-fraud testing.
    
    Args:
        order_id: Internal order ID
        payment_id: Mock payment ID (if provided)
        instagram_id: Customer's Instagram ID
        
    Returns:
        Payment verification result
    """
    try:
        if payment_id and payment_id in MOCK_PAYMENTS:
            payment = MOCK_PAYMENTS[payment_id]
            
            if payment["status"] == "captured":
                return {
                    "success": True,
                    "verified": True,
                    "payment_status": "completed",
                    "payment_id": payment_id,
                    "amount": payment["amount"],
                    "method": payment["method"],
                    "message": "✅ Mock payment verified successfully!",
                    "anti_fraud_check": "passed_mock",
                    "test_mode": True
                }
            else:
                return {
                    "success": True,
                    "verified": False,
                    "payment_status": payment["status"],
                    "message": "Payment not completed yet",
                    "anti_fraud_check": "payment_incomplete_mock"
                }
        else:
            return {
                "success": True,
                "verified": False,
                "payment_status": "pending",
                "message": "No payment found for this order. Please complete payment using the link provided.",
                "anti_fraud_check": "no_payment_reference_mock",
                "instruction": "This is test mode - click the payment link to simulate payment"
            }
            
    except Exception as e:
        logger.error(f"Mock payment verification error: {e}")
        return {
            "success": False,
            "error": "Unable to verify mock payment status",
            "verified": False
        }


def get_mock_payment_data(payment_link_id: str) -> Optional[Dict[str, Any]]:
    """Get payment link data for rendering payment page."""
    return MOCK_PAYMENT_LINKS.get(payment_link_id)


def complete_mock_payment(payment_link_id: str, customer_name: str = None) -> Dict[str, Any]:
    """Complete mock payment (called when user clicks Pay button)."""
    return mock_razorpay_service.simulate_payment_success(
        payment_link_id=payment_link_id,
        customer_name=customer_name,
        payment_method="mock_card"
    )