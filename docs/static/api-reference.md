# Century Property Tax - Intelligent Assistant API Reference

Comprehensive API for Century Property Tax's intelligent WhatsApp assistant.

    ## Overview
    This API powers an intelligent property tax assistant that provides:
    - **WhatsApp Integration**: Native WhatsApp Business API support
    - **Assessment Management**: Complete property assessment workflow
    - **Document Processing**: Intelligent document analysis and verification
    - **Payment Integration**: Secure payment processing with Razorpay
    - **Report Generation**: Automated assessment report creation
    - **Real-time Support**: 24/7 intelligent customer assistance

    ## Architecture
    - **LangGraph Supervisor Pattern**: Intelligent message routing and processing
    - **Message Batching**: Optimized response generation for complex queries
    - **Redis State Management**: Persistent conversation and session storage
    - **PostgreSQL Database**: Comprehensive data persistence
    - **Circuit Breakers**: Resilient external service integration

    ## Authentication
    - WhatsApp webhook verification via VERIFY_TOKEN
    - Signature verification for webhook security
    - Admin endpoints require additional authorization

    ## Rate Limiting
    - Webhook endpoints: 1000 requests/minute
    - Search endpoints: 100 requests/minute
    - Management endpoints: 50 requests/minute

    ## Support
    - Documentation: [/documentation](/documentation)
    - Health Check: [/health](/health)
    - System Stats: [/stats](/stats)
    - Interactive API Docs: [/docs](/docs)
    

**Version:** 4.0.0

## Overview

This API provides comprehensive functionality for Century Property Tax's intelligent assistant system.

## Base URLs

- **Production server**: `https://api.centuryproptax.com`
- **Staging server**: `https://staging.centuryproptax.com`
- **Development server**: `http://localhost:8000`

## Authentication

This API uses webhook verification tokens for WhatsApp integration and signature verification for security.

## Endpoints

### /webhook

#### GET /webhook

**Summary:** Verify WhatsApp Webhook

WhatsApp webhook verification endpoint required for webhook setup.

    WhatsApp sends a GET request with verification parameters to confirm
    webhook URL ownership. This endpoint validates the verify token and
    returns the challenge string if verification succeeds.

    **Required Query Parameters:**
    - `hub.mode`: Must be 'subscribe'
    - `hub.verify_token`: Must match configured VERIFY_TOKEN
    - `hub.challenge`: Challenge string to return on success

    **Environment Variables Required:**
    - `VERIFY_TOKEN`: Token for webhook verification

**Parameters:**

- `hub.mode` (optional): string - Webhook mode (should be 'subscribe')
- `hub.verify_token` (optional): string - Verification token
- `hub.challenge` (optional): string - Challenge string to return

**Responses:**

- `200`: Webhook verified successfully
- `400`: Bad Request
- `403`: Webhook verification failed
- `500`: Internal Server Error
- `422`: Validation Error

---

#### POST /webhook

**Summary:** Handle WhatsApp Messages

Main webhook endpoint for processing WhatsApp messages.

    This endpoint receives WhatsApp Business API webhook events and processes
    them through the intelligent property tax assistant. It handles:

    - Text messages from customers
    - Media messages (images, documents, audio)
    - Interactive messages (buttons, lists)
    - Message status updates
    - System notifications

    **Processing Features:**
    - LangGraph supervisor pattern for intelligent routing
    - Message batching for improved response quality
    - Automatic property tax context understanding
    - Integration with assessment booking system
    - Conversation state management via Redis

    **Security:**
    - Webhook signature verification (configurable)
    - Request validation and sanitization
    - Rate limiting and abuse protection

**Responses:**

- `200`: Message processed successfully
- `400`: Invalid webhook payload
- `403`: Forbidden - Invalid credentials
- `500`: Message processing failed

---

### /health

#### GET /health

**Summary:** System Health Check

Comprehensive health check endpoint for monitoring system status.

    This endpoint provides detailed health information about all system
    components including:

    **System Components:**
    - Database connectivity and performance
    - Redis cache and conversation store
    - WhatsApp Business API integration
    - LangGraph supervisor system
    - Message batching service
    - Circuit breaker status

    **Response Information:**
    - Overall system health status
    - Individual component health details
    - Response time metrics
    - Active session counts
    - Configuration validation
    - Available system features

    **Health Status Values:**
    - `healthy`: All systems operational
    - `degraded`: Some non-critical issues
    - `unhealthy`: Critical system failures

**Responses:**

- `200`: System is healthy
- `400`: Bad Request
- `403`: Forbidden - Invalid credentials
- `500`: Internal Server Error
- `503`: System is unhealthy or degraded

---

### /stats

#### GET /stats

**Summary:** System Statistics

Get detailed system performance and usage statistics.

    This endpoint provides real-time metrics about system performance:

    **Statistics Included:**
    - Active user sessions count
    - Total messages processed
    - Average response times
    - Message batching statistics
    - Memory and CPU usage
    - System uptime information

    **Use Cases:**
    - Performance monitoring
    - Capacity planning
    - System debugging
    - Usage analytics

**Responses:**

- `200`: System statistics retrieved successfully
- `400`: Bad Request
- `403`: Forbidden - Invalid credentials
- `500`: Internal Server Error

---

### /force-process-batch/{user_id}

#### POST /force-process-batch/{user_id}

**Summary:** Force Process Message Batch

Administrative endpoint to force process pending message batches.

    This endpoint allows administrators to manually trigger processing
    of any pending message batches for a specific user. Useful for:

    **Administrative Use Cases:**
    - Debugging message processing issues
    - Manual batch processing during maintenance
    - Testing message batching functionality
    - Resolving stuck conversation states

    **Security Note:**
    This is an administrative endpoint and should be protected
    in production environments.

**Parameters:**

- `user_id` (required): string - User ID to process batch for

**Responses:**

- `200`: Batch processing completed
- `400`: Bad Request
- `403`: Forbidden - Invalid credentials
- `500`: Internal Server Error
- `404`: User not found or no pending batch
- `422`: Validation Error

---

### /whatsapp/webhook

#### GET /whatsapp/webhook

**Summary:** Whatsapp Webhook Verify

WhatsApp webhook verification endpoint.

This endpoint is called by WhatsApp to verify the webhook URL.
Must return the challenge parameter if verification succeeds.

**Parameters:**

- `hub.verify_token` (required): string - 
- `hub.challenge` (required): string - 
- `hub.mode` (required): string - 

**Responses:**

- `200`: Successful Response
- `422`: Validation Error

---

#### POST /whatsapp/webhook

**Summary:** Whatsapp Webhook Handler

WhatsApp webhook message handler with enhanced security.

Processes incoming messages and status updates from WhatsApp Business API.
Includes signature verification for enhanced security.
IMPORTANT: Always returns 200 OK to prevent WhatsApp retries.

**Responses:**

- `200`: Successful Response

---

### /whatsapp/health

#### GET /whatsapp/health

**Summary:** Whatsapp Health

WhatsApp Business API integration health check.

**Responses:**

- `200`: Successful Response

---

### /whatsapp/test-template/{phone_number}

#### POST /whatsapp/test-template/{phone_number}

**Summary:** Test Template Message

Test property tax template messages (development endpoint).

**Parameters:**

- `phone_number` (required): string - 
- `template_type` (optional): string - 

**Responses:**

- `200`: Successful Response
- `422`: Validation Error

---

### /

#### GET /

**Summary:** API Information

Root endpoint providing API overview and available endpoints.

    Returns comprehensive information about all available API endpoints,
    system status, and configuration details.

**Responses:**

- `200`: API information retrieved successfully

---

### /test

#### GET /test

**Summary:** Test Whatsapp Api

Test WhatsApp API configuration.

**Responses:**

- `200`: Successful Response

---

## Data Models

### ErrorResponse

Error response model with additional error details.

**Properties:**

- `status`: unknown - 
- `message`: string - Human-readable response message
- `timestamp`: string - Response timestamp
- `error_code`: unknown - Machine-readable error code
- `error_details`: unknown - Additional error context

### HTTPValidationError

**Properties:**

- `detail`: array - 

### ResponseStatus

Standard response status values.

### ValidationError

**Properties:**

- `loc`: array - 
- `msg`: string - 
- `type`: string - 

