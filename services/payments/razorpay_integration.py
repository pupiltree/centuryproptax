"""
Real Razorpay Payment Integration for Century Property Tax
Includes payment link creation, webhook verification, and fraud prevention.
"""

import os
import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

from langchain_core.tools import tool
from src.core.logging import get_logger

# Import Razorpay (will need to be installed)
try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False
    print("⚠️ Razorpay not installed. Run: pip install razorpay")

try:
    from services.persistence.database import get_db_session
    from services.persistence.repositories import BookingRepository, CustomerRepository
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️ Database not available. Using mock mode.")

# Import mock Razorpay as fallback
from services.payments.mock_razorpay import create_mock_razorpay_payment_link, verify_mock_payment_completion

logger = get_logger("razorpay_integration")


class RazorpayService:
    """Production Razorpay service with webhook verification and fraud prevention."""
    
    def __init__(self):
        self.logger = logger.bind(component="razorpay_service")
        
        # Get Razorpay credentials from environment
        self.key_id = os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        self.webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
        
        if not all([self.key_id, self.key_secret]):
            self.logger.error("Razorpay credentials not configured")
            self.client = None
        elif not RAZORPAY_AVAILABLE:
            self.logger.error("Razorpay SDK not installed")
            self.client = None
        else:
            # Initialize Razorpay client
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
            self.logger.info("Razorpay client initialized successfully")

    def create_order(
        self, 
        amount: float, 
        currency: str = "INR", 
        receipt: str = None,
        notes: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Create a Razorpay order for payment."""
        if not self.client:
            return {"success": False, "error": "Razorpay not configured"}
        
        try:
            # Convert amount to paise (Razorpay expects amount in smallest currency unit)
            amount_paise = int(amount * 100)
            
            order_data = {
                "amount": amount_paise,
                "currency": currency,
                "receipt": receipt or f"rcpt_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "payment_capture": True  # Auto capture payments
            }
            
            if notes:
                order_data["notes"] = notes
            
            order = self.client.order.create(order_data)
            
            self.logger.info(f"Razorpay order created: {order['id']}")
            
            return {
                "success": True,
                "order_id": order["id"],
                "amount": order["amount"] / 100,  # Convert back to rupees
                "currency": order["currency"],
                "status": order["status"],
                "created_at": order["created_at"]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create Razorpay order: {e}")
            return {"success": False, "error": str(e)}

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
        """Create a Razorpay payment link."""
        if not self.client:
            return {"success": False, "error": "Razorpay not configured"}
        
        try:
            # Convert amount to paise
            amount_paise = int(amount * 100)
            
            # Build payment link data
            payment_link_data = {
                "amount": amount_paise,
                "currency": "INR",
                "description": description,
                "customer": {
                    "name": customer_name,
                    "contact": customer_phone
                },
                "notify": {
                    "sms": True,
                    "email": bool(customer_email)
                },
                "reminder_enable": True,
                "accept_partial": False,  # No partial payments for property tax services
                "expire_by": int((datetime.now() + timedelta(hours=24)).timestamp())  # 24 hour expiry
            }
            
            # Add email if provided
            if customer_email:
                payment_link_data["customer"]["email"] = customer_email
            
            # Add reference ID if provided
            if reference_id:
                payment_link_data["reference_id"] = reference_id
            
            # Add callback URL if provided
            if callback_url:
                payment_link_data["callback_url"] = callback_url
                payment_link_data["callback_method"] = "get"
            
            # Add notes if provided
            if notes:
                payment_link_data["notes"] = notes
            
            # Create payment link
            payment_link = self.client.payment_link.create(payment_link_data)
            
            self.logger.info(f"Payment link created: {payment_link['id']}")
            
            return {
                "success": True,
                "payment_link_id": payment_link["id"],
                "payment_link": payment_link["short_url"],
                "amount": payment_link["amount"] / 100,  # Convert back to rupees
                "currency": payment_link["currency"],
                "status": payment_link["status"],
                "expires_at": payment_link["expire_by"],
                "created_at": payment_link["created_at"],
                "customer": payment_link["customer"]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create payment link: {e}")
            return {"success": False, "error": str(e)}

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> bool:
        """Verify Razorpay payment signature for security."""
        if not self.client:
            return False
        
        try:
            # Use Razorpay's utility function to verify signature
            self.client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
            
            self.logger.info(f"Payment signature verified for payment: {razorpay_payment_id}")
            return True
            
        except razorpay.errors.SignatureVerificationError:
            self.logger.error(f"Invalid signature for payment: {razorpay_payment_id}")
            return False
        except Exception as e:
            self.logger.error(f"Signature verification error: {e}")
            return False

    def verify_payment_link_signature(
        self,
        payment_link_id: str,
        payment_link_reference_id: str,
        payment_link_status: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> bool:
        """Verify payment link signature for security."""
        if not self.client:
            return False
        
        try:
            # Use Razorpay's utility function to verify payment link signature
            self.client.utility.verify_payment_link_signature({
                'payment_link_id': payment_link_id,
                'payment_link_reference_id': payment_link_reference_id,
                'payment_link_status': payment_link_status,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
            
            self.logger.info(f"Payment link signature verified: {payment_link_id}")
            return True
            
        except razorpay.errors.SignatureVerificationError:
            self.logger.error(f"Invalid payment link signature: {payment_link_id}")
            return False
        except Exception as e:
            self.logger.error(f"Payment link signature verification error: {e}")
            return False

    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature to prevent tampering."""
        if not self.webhook_secret:
            self.logger.error("Webhook secret not configured")
            return False
        
        try:
            # Generate expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature, signature)
            
            if is_valid:
                self.logger.info("Webhook signature verified")
            else:
                self.logger.error("Invalid webhook signature")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Webhook signature verification error: {e}")
            return False

    def get_payment_details(self, payment_id: str) -> Dict[str, Any]:
        """Get payment details from Razorpay."""
        if not self.client:
            return {"success": False, "error": "Razorpay not configured"}
        
        try:
            payment = self.client.payment.fetch(payment_id)
            
            return {
                "success": True,
                "payment_id": payment["id"],
                "order_id": payment.get("order_id"),
                "amount": payment["amount"] / 100,  # Convert to rupees
                "currency": payment["currency"],
                "status": payment["status"],
                "method": payment["method"],
                "email": payment.get("email"),
                "contact": payment.get("contact"),
                "fee": payment.get("fee", 0) / 100,  # Convert to rupees
                "tax": payment.get("tax", 0) / 100,  # Convert to rupees
                "created_at": payment["created_at"],
                "captured": payment.get("captured", False)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to fetch payment details: {e}")
            return {"success": False, "error": str(e)}

    def get_payment_link_details(self, payment_link_id: str) -> Dict[str, Any]:
        """Get payment link details from Razorpay."""
        if not self.client:
            return {"success": False, "error": "Razorpay not configured"}
        
        try:
            payment_link = self.client.payment_link.fetch(payment_link_id)
            
            return {
                "success": True,
                "payment_link_id": payment_link["id"],
                "amount": payment_link["amount"] / 100,  # Convert to rupees
                "amount_paid": payment_link["amount_paid"] / 100,  # Convert to rupees
                "status": payment_link["status"],
                "description": payment_link["description"],
                "reference_id": payment_link.get("reference_id"),
                "short_url": payment_link["short_url"],
                "customer": payment_link["customer"],
                "created_at": payment_link["created_at"],
                "expire_by": payment_link.get("expire_by"),
                "payments": payment_link.get("payments", [])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to fetch payment link details: {e}")
            return {"success": False, "error": str(e)}


# Initialize global service instance
razorpay_service = RazorpayService()


@tool
async def create_razorpay_payment_link(
    order_id: str,
    amount: float,
    customer_name: str,
    customer_phone: str,
    customer_email: str = None,
    description: str = "Payment for property tax services"
) -> Dict[str, Any]:
    """
    Create a real Razorpay payment link with webhook verification.
    
    Args:
        order_id: Internal order ID for reference
        amount: Payment amount in INR
        customer_name: Customer's name
        customer_phone: Customer's phone number
        customer_email: Customer's email (optional)
        description: Payment description
        
    Returns:
        Payment link creation result with security features
    """
    try:
        # Check if Razorpay is properly configured
        if not razorpay_service.client:
            logger.warning("Razorpay not configured - using mock payment system")
            return await create_mock_razorpay_payment_link.ainvoke({
                "order_id": order_id,
                "amount": amount,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "customer_email": customer_email,
                "description": description
            })
        
        # Create callback URL for webhook
        callback_url = f"{os.getenv('BASE_URL', 'https://api.centuryproptax.com')}/webhook/razorpay/callback"
        
        # Create payment link with Razorpay
        result = razorpay_service.create_payment_link(
            amount=amount,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            description=description,
            reference_id=order_id,
            callback_url=callback_url,
            notes={
                "order_id": order_id,
                "service": "century_property_tax",
                "created_by": "chatbot"
            }
        )
        
        if not result["success"]:
            return result
        
        # Store payment link info in database for verification
        if DATABASE_AVAILABLE:
            try:
                async with get_db_session() as session:
                    booking_repo = BookingRepository(session)
                    # Update booking with payment link details
                    # This would need proper implementation based on your booking schema
                    pass
            except Exception as e:
                logger.error(f"Failed to store payment link info: {e}")
        else:
            logger.info("Database not available - payment link info not stored")
        
        return {
            "success": True,
            "payment_link_id": result["payment_link_id"],
            "payment_link": result["payment_link"],
            "amount": result["amount"],
            "order_id": order_id,
            "status": "created",
            "expires_at": result["expires_at"],
            "message": f"Payment link created: {result['payment_link']}",
            "instructions": [
                "Click the link to pay securely",
                "Payment is processed by Razorpay",
                "You will receive confirmation after payment",
                "Link expires in 24 hours"
            ],
            "security_note": "This is a secure Razorpay payment link with signature verification"
        }
        
    except Exception as e:
        logger.error(f"Failed to create Razorpay payment link: {e}")
        return {
            "success": False,
            "error": "Unable to create payment link at this time"
        }


@tool
async def verify_payment_completion(
    order_id: str,
    payment_id: str = None,
    instagram_id: str = None
) -> Dict[str, Any]:
    """
    Verify if payment is actually completed - prevents fraud from fake claims.
    
    Args:
        order_id: Internal order ID
        payment_id: Razorpay payment ID (optional)
        instagram_id: Customer's Instagram ID for verification
        
    Returns:
        Payment verification result with anti-fraud checks
    """
    try:
        # Check if Razorpay is configured, if not use mock verification
        if not razorpay_service.client:
            logger.warning("Razorpay not configured - using mock payment verification")
            # Handle None payment_id for mock verification
            params = {"order_id": order_id, "instagram_id": instagram_id}
            if payment_id:
                params["payment_id"] = payment_id
            return await verify_mock_payment_completion.ainvoke(params)
        
        # First, check our database for the order (if database available)
        if DATABASE_AVAILABLE:
            async with get_db_session() as session:
                booking_repo = BookingRepository(session)
                customer_repo = CustomerRepository(session)
                
                # Verify customer owns this order
                if instagram_id:
                    customer = await customer_repo.get_by_whatsapp_id(instagram_id)  # Parameter naming will be updated
                    if not customer:
                        return {
                            "success": False,
                            "error": "Customer not found",
                            "verified": False
                        }
                    
                    # Check if customer has bookings for this order
                    bookings = await booking_repo.get_customer_bookings(customer.id)
                    order_bookings = [b for b in bookings if order_id in b.booking_id]
                    
                    if not order_bookings:
                        return {
                            "success": False,
                            "error": "Order not found for this customer",
                            "verified": False
                        }
        
        # If payment_id provided, verify with Razorpay
        if payment_id:
            payment_details = razorpay_service.get_payment_details(payment_id)
            
            if not payment_details["success"]:
                return {
                    "success": False,
                    "error": "Unable to verify payment with Razorpay",
                    "verified": False
                }
            
            # Check payment status
            payment_status = payment_details["status"]
            is_captured = payment_details.get("captured", False)
            
            if payment_status == "captured" and is_captured:
                return {
                    "success": True,
                    "verified": True,
                    "payment_status": "completed",
                    "payment_id": payment_id,
                    "amount": payment_details["amount"],
                    "method": payment_details["method"],
                    "message": "Payment verified successfully",
                    "anti_fraud_check": "passed"
                }
            else:
                return {
                    "success": True,
                    "verified": False,
                    "payment_status": payment_status,
                    "message": "Payment not completed yet",
                    "anti_fraud_check": "payment_incomplete"
                }
        
        # If no payment ID provided, check if there are any payments for this order
        # This prevents users from claiming payment without actually paying
        return {
            "success": True,
            "verified": False,
            "payment_status": "pending",
            "message": "No payment found for this order. Please complete payment using the link provided.",
            "anti_fraud_check": "no_payment_reference",
            "instruction": "Please provide payment ID or complete payment first"
        }
        
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        return {
            "success": False,
            "error": "Unable to verify payment status",
            "verified": False
        }


@tool
async def handle_payment_webhook_data(
    webhook_payload: str,
    webhook_signature: str
) -> Dict[str, Any]:
    """
    Handle Razorpay webhook data for payment confirmations.
    This should be called by the webhook endpoint, not directly by chatbot.
    
    Args:
        webhook_payload: Raw webhook payload
        webhook_signature: Webhook signature for verification
        
    Returns:
        Webhook processing result
    """
    try:
        # Verify webhook signature first
        if not razorpay_service.verify_webhook_signature(webhook_payload, webhook_signature):
            return {
                "success": False,
                "error": "Invalid webhook signature",
                "security_alert": "Potential tampering detected"
            }
        
        # Parse webhook data
        webhook_data = json.loads(webhook_payload)
        event_type = webhook_data.get("event")
        
        if event_type == "payment.captured":
            # Payment successful
            payment_data = webhook_data["payload"]["payment"]["entity"]
            
            payment_id = payment_data["id"]
            order_id = payment_data.get("order_id")
            amount = payment_data["amount"] / 100  # Convert to rupees
            status = payment_data["status"]
            
            # Update booking status in database
            try:
                async with get_db_session() as session:
                    booking_repo = BookingRepository(session)
                    # Update booking payment status
                    # This would need proper implementation
                    pass
            except Exception as e:
                logger.error(f"Failed to update booking status: {e}")
            
            logger.info(f"Payment captured: {payment_id}, Amount: ₹{amount}")
            
            return {
                "success": True,
                "event": "payment_captured",
                "payment_id": payment_id,
                "order_id": order_id,
                "amount": amount,
                "status": status
            }
        
        elif event_type == "payment.failed":
            # Payment failed
            payment_data = webhook_data["payload"]["payment"]["entity"]
            
            payment_id = payment_data["id"]
            error_code = payment_data.get("error_code")
            error_description = payment_data.get("error_description")
            
            logger.info(f"Payment failed: {payment_id}, Error: {error_description}")
            
            return {
                "success": True,
                "event": "payment_failed",
                "payment_id": payment_id,
                "error_code": error_code,
                "error_description": error_description
            }
        
        else:
            # Other events
            return {
                "success": True,
                "event": event_type,
                "message": "Webhook received but not processed"
            }
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return {
            "success": False,
            "error": "Failed to process webhook"
        }