# Developer Onboarding Guide

## Century Property Tax Intelligent Assistant API

Welcome to the Century Property Tax API! This guide will help you get started with integrating our intelligent WhatsApp-based property tax assistant into your applications.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Authentication Setup](#authentication-setup)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Integration Examples](#integration-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Support](#support)

## Overview

The Century Property Tax API powers an intelligent assistant that provides comprehensive property tax services through WhatsApp Business API integration. Key capabilities include:

### Core Features
- **WhatsApp Integration**: Native Business API support with intelligent message processing
- **Assessment Management**: Complete property assessment workflow and booking system
- **Document Processing**: AI-powered document analysis and verification
- **Payment Integration**: Secure payment processing with Razorpay
- **Report Generation**: Automated assessment report creation and delivery
- **Real-time Support**: 24/7 intelligent customer assistance

### Architecture
- **LangGraph Supervisor Pattern**: Intelligent message routing and processing
- **Message Batching**: Optimized response generation for complex queries
- **Redis State Management**: Persistent conversation and session storage
- **PostgreSQL Database**: Comprehensive data persistence
- **Circuit Breakers**: Resilient external service integration

## Prerequisites

Before you begin, ensure you have:

### Required Accounts
- **WhatsApp Business API**: Verified business account with Meta
- **Database Access**: PostgreSQL instance for data persistence
- **Redis Instance**: For conversation state management
- **Payment Gateway**: Razorpay account for payment processing (optional)

### Technical Requirements
- **Python 3.8+**: For running the API server
- **FastAPI Knowledge**: Familiarity with FastAPI framework
- **Webhook Development**: Basic understanding of webhook handling
- **Environment Variables**: Ability to configure environment variables

### Development Tools
- **API Testing**: Postman, curl, or similar tools
- **Code Editor**: VS Code, PyCharm, or preferred IDE
- **Git**: For version control and deployment

## Authentication Setup

### 1. WhatsApp Business API Configuration

```bash
# Required environment variables
WA_ACCESS_TOKEN=your_whatsapp_access_token
WA_PHONE_NUMBER_ID=your_phone_number_id
WA_BUSINESS_ACCOUNT_ID=your_business_account_id
VERIFY_TOKEN=your_webhook_verification_token
```

### 2. Database Configuration

```bash
# Database connection
DATABASE_URL=postgresql://user:password@localhost:5432/centuryproptax
REDIS_URL=redis://localhost:6379/0
```

### 3. Optional Services

```bash
# Payment processing (optional)
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret

# AI Services
GOOGLE_API_KEY=your_google_api_key
```

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/centuryproptax/api.git
cd centuryproptax-api

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your configuration
```

### 2. Run the Development Server

```bash
# Start the FastAPI development server
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# View interactive documentation
open http://localhost:8000/docs
```

### 4. Configure WhatsApp Webhook

1. **Set Webhook URL**: Configure your WhatsApp webhook URL to point to your server:
   ```
   https://your-domain.com/webhook
   ```

2. **Verify Webhook**: WhatsApp will send a GET request to verify your webhook:
   ```bash
   # Example verification request
   GET /webhook?hub.mode=subscribe&hub.verify_token=your_token&hub.challenge=123456
   ```

3. **Test Message Processing**: Send a test message to your WhatsApp Business number

## API Endpoints

### Core Webhook Endpoints

#### Webhook Verification
```http
GET /webhook
```
Verifies webhook ownership for WhatsApp setup.

**Query Parameters:**
- `hub.mode`: Should be "subscribe"
- `hub.verify_token`: Your verification token
- `hub.challenge`: Challenge string to return

#### Message Processing
```http
POST /webhook
```
Processes incoming WhatsApp messages and events.

**Request Body:** WhatsApp webhook payload
**Response:** Processing status and message ID

### Health and Monitoring

#### Health Check
```http
GET /health
```
Comprehensive system health check with component status.

#### System Statistics
```http
GET /stats
```
Real-time performance metrics and usage statistics.

### Assessment Management

#### Search Assessments
```http
GET /api/assessment-reports/search
```
Search for assessment reports with flexible filtering.

**Query Parameters:**
- `booking_id`: Specific assessment ID
- `phone`: Customer phone number
- `status`: Assessment status filter

#### Update Assessment Status
```http
POST /api/assessment-reports/update
```
Update assessment report status and details.

**Request Body:**
```json
{
  "booking_id": "CPT20250811_A1",
  "status": "ready",
  "report_url": "https://reports.example.com/report.pdf",
  "notes": "Assessment complete"
}
```

## Integration Examples

### Python Integration

```python
import requests
from typing import Dict, Any

class CenturyPropertyTaxAPI:
    def __init__(self, base_url: str = "https://api.centuryproptax.com"):
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def search_assessments(self, **filters) -> Dict[str, Any]:
        """Search for assessment reports."""
        response = self.session.get(
            f"{self.base_url}/api/assessment-reports/search",
            params=filters
        )
        response.raise_for_status()
        return response.json()

# Usage example
api = CenturyPropertyTaxAPI()
health = api.health_check()
print(f"API Status: {health['status']}")
```

### JavaScript/Node.js Integration

```javascript
class CenturyPropertyTaxAPI {
    constructor(baseUrl = 'https://api.centuryproptax.com') {
        this.baseUrl = baseUrl;
    }

    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/health`);
        if (!response.ok) {
            throw new Error(`Health check failed: ${response.statusText}`);
        }
        return await response.json();
    }

    async searchAssessments(filters = {}) {
        const params = new URLSearchParams(filters);
        const response = await fetch(
            `${this.baseUrl}/api/assessment-reports/search?${params}`
        );
        if (!response.ok) {
            throw new Error(`Search failed: ${response.statusText}`);
        }
        return await response.json();
    }
}

// Usage example
const api = new CenturyPropertyTaxAPI();
const health = await api.healthCheck();
console.log(`API Status: ${health.status}`);
```

### cURL Examples

```bash
# Health check
curl -X GET "https://api.centuryproptax.com/health" \
  -H "Accept: application/json"

# Search assessments
curl -X GET "https://api.centuryproptax.com/api/assessment-reports/search?status=pending" \
  -H "Accept: application/json"

# Update assessment status
curl -X POST "https://api.centuryproptax.com/api/assessment-reports/update" \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": "CPT20250811_A1",
    "status": "ready",
    "report_url": "https://reports.example.com/report.pdf"
  }'
```

## Best Practices

### Security
1. **Webhook Verification**: Always verify webhook signatures in production
2. **Environment Variables**: Store sensitive credentials in environment variables
3. **HTTPS**: Use HTTPS for all API communication
4. **Rate Limiting**: Implement client-side rate limiting to avoid API limits

### Error Handling
1. **HTTP Status Codes**: Check response status codes and handle errors appropriately
2. **Retry Logic**: Implement exponential backoff for transient failures
3. **Logging**: Log API requests and responses for debugging
4. **Circuit Breakers**: Implement circuit breakers for external service calls

### Performance
1. **Connection Pooling**: Use connection pooling for HTTP requests
2. **Caching**: Cache frequently accessed data when appropriate
3. **Async Processing**: Use asynchronous processing for webhook handling
4. **Monitoring**: Monitor API performance and response times

### Development Workflow
1. **Testing**: Test against development/staging environments first
2. **Versioning**: Use API versioning for backward compatibility
3. **Documentation**: Keep integration documentation up to date
4. **Monitoring**: Set up monitoring and alerting for production deployments

## Troubleshooting

### Common Issues

#### Webhook Verification Fails
- **Cause**: Incorrect `VERIFY_TOKEN` or webhook URL
- **Solution**: Verify environment variables and webhook configuration

#### Messages Not Processing
- **Cause**: Webhook not receiving events or processing errors
- **Solution**: Check webhook logs and API health status

#### Database Connection Errors
- **Cause**: Incorrect database configuration or connectivity issues
- **Solution**: Verify `DATABASE_URL` and database accessibility

#### Authentication Errors
- **Cause**: Invalid WhatsApp credentials or expired tokens
- **Solution**: Refresh WhatsApp access tokens and verify credentials

### Debugging Steps

1. **Check API Health**: Always start with `/health` endpoint
2. **Review Logs**: Check application logs for error details
3. **Test Webhooks**: Use webhook testing tools to verify delivery
4. **Validate Environment**: Ensure all required environment variables are set
5. **Network Connectivity**: Verify network access to external services

### Getting Help

1. **Documentation**: Check [API documentation](/docs) for detailed information
2. **Examples**: Review [integration examples](examples/) for reference code
3. **Support**: Contact support@centuryproptax.com for assistance
4. **Community**: Join our developer community for peer support

## Support

### Resources
- **API Documentation**: [/docs](/docs) - Interactive API documentation
- **ReDoc Documentation**: [/redoc](/redoc) - Alternative documentation format
- **System Status**: [/health](/health) - Real-time system status
- **OpenAPI Schema**: [/openapi.json](/openapi.json) - Machine-readable API specification

### Contact Information
- **Technical Support**: support@centuryproptax.com
- **Developer Portal**: https://developers.centuryproptax.com
- **Status Page**: https://status.centuryproptax.com
- **Community Forum**: https://community.centuryproptax.com

### SLA and Support Hours
- **API Uptime**: 99.9% availability guarantee
- **Support Hours**: 24/7 for critical issues, business hours for general support
- **Response Times**:
  - Critical: 1 hour
  - High: 4 hours
  - Medium: 24 hours
  - Low: 72 hours

---

**Note**: This is a living document. Please check back regularly for updates and new features. For the most current information, always refer to the interactive API documentation at `/docs`.