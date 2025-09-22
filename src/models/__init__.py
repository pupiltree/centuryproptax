"""
API Models package for Century Property Tax system.
Contains all Pydantic models for request/response validation and OpenAPI documentation.
"""

from .api_models import (
    # Base models
    BaseResponse,
    ErrorResponse,

    # Enums
    ResponseStatus,
    BookingStatus,
    MessageType,

    # Health check models
    ComponentStatus,
    HealthCheckResponse,

    # Customer models
    CustomerBase,
    CustomerCreate,
    CustomerResponse,

    # Booking models
    BookingCreate,
    BookingResponse,

    # Report management models
    ReportSearchRequest,
    ReportUpdateRequest,
    ReportSearchResponse,
    ReportUpdateResponse,

    # WhatsApp models
    WhatsAppMessage,
    WhatsAppWebhookEntry,
    WhatsAppWebhookPayload,
    WhatsAppResponse,
    WebhookVerificationResponse,

    # System models
    SystemStats,

    # Error models
    ValidationError,
    NotFoundError,
    AuthenticationError,
    RateLimitError,

    # Example responses
    EXAMPLE_RESPONSES
)

__all__ = [
    # Base models
    "BaseResponse",
    "ErrorResponse",

    # Enums
    "ResponseStatus",
    "BookingStatus",
    "MessageType",

    # Health check models
    "ComponentStatus",
    "HealthCheckResponse",

    # Customer models
    "CustomerBase",
    "CustomerCreate",
    "CustomerResponse",

    # Booking models
    "BookingCreate",
    "BookingResponse",

    # Report management models
    "ReportSearchRequest",
    "ReportUpdateRequest",
    "ReportSearchResponse",
    "ReportUpdateResponse",

    # WhatsApp models
    "WhatsAppMessage",
    "WhatsAppWebhookEntry",
    "WhatsAppWebhookPayload",
    "WhatsAppResponse",
    "WebhookVerificationResponse",

    # System models
    "SystemStats",

    # Error models
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "RateLimitError",

    # Example responses
    "EXAMPLE_RESPONSES"
]