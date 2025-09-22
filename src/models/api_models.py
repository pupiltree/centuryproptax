"""
Comprehensive Pydantic models for FastAPI documentation and validation.
Used across all API endpoints for consistent request/response schemas.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, validator


class ResponseStatus(str, Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class BookingStatus(str, Enum):
    """Assessment booking status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class MessageType(str, Enum):
    """WhatsApp message types."""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACTS = "contacts"
    INTERACTIVE = "interactive"


# Base Response Models
class BaseResponse(BaseModel):
    """Base response model for all API endpoints."""
    status: ResponseStatus = Field(..., description="Response status indicator")
    message: str = Field(..., description="Human-readable response message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class ErrorResponse(BaseResponse):
    """Error response model with additional error details."""
    status: ResponseStatus = ResponseStatus.ERROR
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


# Health Check Models
class ComponentStatus(BaseModel):
    """Health status for individual system components."""
    status: str = Field(..., description="Component health status", example="healthy")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    connection: Optional[str] = Field(None, description="Connection status")


class HealthCheckResponse(BaseModel):
    """Comprehensive health check response."""
    status: str = Field(..., description="Overall system health", example="healthy")
    service: str = Field(..., description="Service name", example="century-property-tax-modern")
    version: str = Field(..., description="Service version", example="4.0.0")
    architecture: str = Field(..., description="System architecture", example="langgraph-supervisor-pattern")
    timestamp: str = Field(..., description="Health check timestamp")
    response_time_ms: float = Field(..., description="Total health check duration")
    components: Dict[str, Union[ComponentStatus, Any]] = Field(..., description="Individual component status")
    checks: Dict[str, ComponentStatus] = Field(..., description="Health check results")
    features: List[str] = Field(..., description="Available system features")


# Customer Models
class CustomerBase(BaseModel):
    """Base customer information."""
    name: str = Field(..., description="Customer full name", example="John Smith")
    phone: str = Field(..., description="Customer phone number", example="9876543210")


class CustomerCreate(CustomerBase):
    """Customer creation request model."""
    email: Optional[str] = Field(None, description="Customer email address", example="john@example.com")


class CustomerResponse(CustomerBase):
    """Customer response model."""
    id: int = Field(..., description="Customer unique identifier")
    email: Optional[str] = Field(None, description="Customer email address")
    created_at: datetime = Field(..., description="Customer registration date")


# Assessment Booking Models
class BookingCreate(BaseModel):
    """Assessment booking creation request."""
    customer_id: int = Field(..., description="Customer ID from registration")
    test_id: str = Field(..., description="Assessment type identifier", example="property_valuation")
    property_address: str = Field(..., description="Property address for assessment", example="123 Main St, Dallas, TX")
    notes: Optional[str] = Field(None, description="Additional booking notes")


class BookingResponse(BaseModel):
    """Assessment booking response model."""
    booking_id: str = Field(..., description="Unique booking identifier", example="CPT20250811_A1")
    customer_id: int = Field(..., description="Customer ID")
    customer_name: str = Field(..., description="Customer name")
    phone: str = Field(..., description="Customer phone")
    test_id: str = Field(..., description="Assessment type")
    test_name: str = Field(..., description="Assessment type name")
    status: BookingStatus = Field(..., description="Current booking status")
    property_address: str = Field(..., description="Property address")
    total_amount: float = Field(..., description="Assessment cost", example=250.00)
    created_at: datetime = Field(..., description="Booking creation date")
    report_url: Optional[str] = Field(None, description="Assessment report download URL")


# Report Management Models
class ReportSearchRequest(BaseModel):
    """Assessment report search request."""
    booking_id: Optional[str] = Field(None, description="Specific booking ID to search", example="CPT20250811_A1")
    phone: Optional[str] = Field(None, description="Customer phone number", example="9876543210")
    status: Optional[BookingStatus] = Field(None, description="Booking status filter")
    date_from: Optional[str] = Field(None, description="Date range start (YYYY-MM-DD)", example="2025-01-01")
    date_to: Optional[str] = Field(None, description="Date range end (YYYY-MM-DD)", example="2025-12-31")


class ReportUpdateRequest(BaseModel):
    """Assessment report update request."""
    booking_id: str = Field(..., description="Booking ID to update", example="CPT20250811_A1")
    status: BookingStatus = Field(..., description="New booking status")
    report_url: Optional[str] = Field(None, description="Assessment report URL if available")
    notes: Optional[str] = Field(None, description="Status update notes")


class ReportSearchResponse(BaseResponse):
    """Assessment report search response."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    bookings: List[BookingResponse] = Field(..., description="Found assessment bookings")
    total_found: int = Field(..., description="Total number of matching records")


class ReportUpdateResponse(BaseResponse):
    """Assessment report update response."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    booking_id: str = Field(..., description="Updated booking ID")
    new_status: BookingStatus = Field(..., description="Updated status")
    updated_at: datetime = Field(..., description="Update timestamp")


# WhatsApp Webhook Models
class WhatsAppMessage(BaseModel):
    """WhatsApp message payload."""
    from_number: str = Field(..., description="Sender phone number", example="919876543210")
    message_type: MessageType = Field(..., description="Type of message received")
    text: Optional[str] = Field(None, description="Text content for text messages")
    media_url: Optional[str] = Field(None, description="Media URL for media messages")
    media_id: Optional[str] = Field(None, description="WhatsApp media ID")
    timestamp: str = Field(..., description="Message timestamp")


class WhatsAppWebhookEntry(BaseModel):
    """WhatsApp webhook entry structure."""
    id: str = Field(..., description="WhatsApp Business Account ID")
    changes: List[Dict[str, Any]] = Field(..., description="Webhook change events")


class WhatsAppWebhookPayload(BaseModel):
    """Complete WhatsApp webhook payload."""
    object: str = Field(..., description="Webhook object type", example="whatsapp_business_account")
    entry: List[WhatsAppWebhookEntry] = Field(..., description="Webhook entries")


class WhatsAppResponse(BaseResponse):
    """WhatsApp message processing response."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    from_number: str = Field(..., description="Message sender")
    message_id: Optional[str] = Field(None, description="Processed message ID")
    response_sent: bool = Field(..., description="Whether response was sent to user")


# Webhook Verification Models
class WebhookVerificationResponse(BaseModel):
    """Webhook verification response."""
    challenge: str = Field(..., description="WhatsApp challenge token")


# Statistics Models
class SystemStats(BaseModel):
    """System statistics response."""
    active_sessions: int = Field(..., description="Number of active user sessions")
    total_messages_processed: int = Field(..., description="Total messages processed")
    average_response_time_ms: float = Field(..., description="Average response time")
    uptime_seconds: int = Field(..., description="System uptime in seconds")
    message_batcher_stats: Dict[str, Any] = Field(..., description="Message batching statistics")


# Error Models for specific scenarios
class ValidationError(BaseModel):
    """Field validation error."""
    field: str = Field(..., description="Field name with validation error")
    message: str = Field(..., description="Validation error message")
    value: Any = Field(..., description="Invalid value provided")


class NotFoundError(ErrorResponse):
    """Resource not found error."""
    error_code: str = "RESOURCE_NOT_FOUND"
    resource_type: str = Field(..., description="Type of resource not found")
    resource_id: str = Field(..., description="ID of resource not found")


class AuthenticationError(ErrorResponse):
    """Authentication failure error."""
    error_code: str = "AUTHENTICATION_FAILED"


class RateLimitError(ErrorResponse):
    """Rate limit exceeded error."""
    error_code: str = "RATE_LIMIT_EXCEEDED"
    retry_after_seconds: int = Field(..., description="Seconds to wait before retry")


# Example response collections for documentation
EXAMPLE_RESPONSES = {
    "health_check_healthy": {
        "status": "healthy",
        "service": "century-property-tax-modern",
        "version": "4.0.0",
        "timestamp": "2025-09-22T12:00:00Z",
        "response_time_ms": 25.5,
        "components": {
            "webhook_handler": "operational",
            "database": "healthy",
            "redis": "healthy"
        }
    },

    "booking_search_results": {
        "status": "success",
        "message": "Found 2 assessment(s)",
        "bookings": [
            {
                "booking_id": "CPT20250811_A1",
                "customer_name": "John Smith",
                "phone": "9876543210",
                "test_name": "Property Valuation Assessment",
                "status": "ready",
                "created_at": "2025-08-11T10:30:00Z",
                "total_amount": 250.00,
                "report_url": "https://reports.example.com/CPT20250811_A1.pdf"
            }
        ],
        "total_found": 1
    },

    "webhook_success": {
        "status": "success",
        "message": "Message processed successfully",
        "from_number": "919876543210",
        "response_sent": True,
        "timestamp": "2025-09-22T12:00:00Z"
    }
}