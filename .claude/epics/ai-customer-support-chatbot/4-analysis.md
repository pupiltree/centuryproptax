---
issue: 4
analyzed: 2025-09-19T16:30:00Z
streams: 3
---

# Issue #4 Analysis: WhatsApp Integration Setup - Configure messaging and remove Instagram components

## Overview
Configure WhatsApp Business API as the sole messaging platform by removing all Instagram integration components from the Krishna Diagnostics system and implementing property tax-specific WhatsApp messaging features. This involves systematic removal of Instagram dependencies while enhancing WhatsApp functionality for property tax customer support workflows.

## Parallel Streams

### Stream A: Instagram Component Removal
- **Scope**: Systematically remove all Instagram API integration, handlers, and references from the codebase
- **Files**:
  - `services/messaging/instagram_api.py` (DELETE)
  - `services/messaging/instagram_image_handler.py` (DELETE)
  - `services/messaging/instagram_types.py` (DELETE)
  - `services/messaging/integrated_webhook_handler.py` (UPDATE - remove Instagram logic)
  - `services/messaging/modern_integrated_webhook_handler.py` (UPDATE - remove Instagram references)
  - `src/main.py` (UPDATE - remove Instagram test endpoints)
  - `src/api/business_webhooks.py` (UPDATE - remove Instagram-specific environment checks)
  - `services/messaging/__pycache__/*instagram*` (DELETE compiled files)
- **Environment Variables**:
  - Remove `IG_TOKEN`, `IG_USER_ID` references from health checks
  - Update environment validation to exclude Instagram variables
- **Duration**: 4-6 hours
- **Dependencies**: None - can start immediately

### Stream B: WhatsApp Business API Configuration
- **Scope**: Configure WhatsApp Business API authentication, webhook setup, and enhance existing WhatsApp client
- **Files**:
  - `services/messaging/whatsapp_client.py` (ENHANCE - add business features)
  - `src/api/whatsapp_webhooks.py` (ENHANCE - add business phone verification)
  - `config/settings.py` (ENHANCE - add WhatsApp business configuration)
  - `.env.example` (UPDATE - add WhatsApp Business API variables)
- **New Configuration**:
  - `WHATSAPP_BUSINESS_ACCOUNT_ID` - Business account identifier
  - `WHATSAPP_BUSINESS_PHONE_NUMBER` - Verified business phone number
  - `WHATSAPP_APP_ID` - Meta app configuration
  - `WHATSAPP_APP_SECRET` - App secret for enhanced security
- **Features to Implement**:
  - Business profile configuration
  - Message template management
  - Enhanced webhook security with app secret validation
  - Rate limiting and quota management
- **Duration**: 6-8 hours
- **Dependencies**: Requires Stream A completion to remove conflicts

### Stream C: Property Tax Message Templates & Workflows
- **Scope**: Create property tax-specific message templates and enhance messaging workflows for customer support
- **Files**:
  - `services/messaging/property_tax_templates.py` (CREATE)
  - `services/messaging/whatsapp_client.py` (ENHANCE - template support)
  - `agents/core/property_tax_assistant_v3.py` (UPDATE - WhatsApp-specific responses)
  - `services/communication/message_handler.py` (UPDATE - property tax context)
- **Templates to Create**:
  - Property tax assessment notifications
  - Payment reminder templates
  - Appeal process guidance templates
  - Documentation request templates
  - Consultation booking confirmations
- **Workflow Enhancements**:
  - Property owner verification via phone number
  - Document sharing for tax bills and forms
  - Session management for complex consultations
  - Integration with property tax database context
- **Duration**: 6-8 hours
- **Dependencies**: Requires Stream B completion for template infrastructure

## Key Components Analysis

### Instagram Components to Remove
1. **Core Instagram Files**:
   - `instagram_api.py` - 280 lines of Instagram Graph API client
   - `instagram_image_handler.py` - 189 lines of Instagram-specific image processing
   - `instagram_types.py` - Type definitions for Instagram API responses

2. **Integration Points**:
   - Instagram webhook handling in `modern_integrated_webhook_handler.py`
   - Instagram test endpoints in `src/main.py`
   - Instagram environment variable validation in health checks
   - Instagram-specific error handling and retry logic

3. **Environment Variables**:
   - `IG_TOKEN` - Instagram access token
   - `IG_USER_ID` - Instagram business account ID
   - References in health check validation

### WhatsApp Features to Enhance
1. **Business API Features**:
   - Business profile management
   - Message template creation and approval
   - Enhanced webhook security with app secret
   - Business phone number verification

2. **Property Tax Integrations**:
   - Property owner verification workflows
   - Tax assessment document sharing
   - Payment portal integration via messages
   - Consultation scheduling and management

3. **Advanced Messaging**:
   - Interactive button messages for common queries
   - List messages for service options
   - Quick reply suggestions for property tax topics
   - Rich media support for forms and documents

## Coordination Points
- **Stream A → Stream B**: Instagram removal must complete before WhatsApp enhancement to avoid conflicts
- **Stream B → Stream C**: WhatsApp Business API configuration must be complete before implementing templates
- **Stream A ↔ Stream C**: Ensure no Instagram references remain in property tax messaging workflows

## Sequential Dependencies
1. **Removal Phase** (Stream A): Complete Instagram component removal and codebase cleanup
2. **Configuration Phase** (Stream B): Configure WhatsApp Business API with enhanced features
3. **Enhancement Phase** (Stream C): Implement property tax-specific templates and workflows
4. **Integration Testing**: Verify WhatsApp-only messaging works with property tax workflows
5. **Business API Testing**: Test message templates, business features, and compliance

## Risk Mitigation
- **Webhook Continuity**: Ensure WhatsApp webhooks remain functional during Instagram removal
- **Message Handler Compatibility**: Verify message routing works after Instagram handler removal
- **Environment Variable Safety**: Update all configuration validation to exclude Instagram variables
- **Database Session Integrity**: Ensure conversation sessions continue working after platform changes

## Definition of Done Validation
- [ ] All Instagram files and references completely removed from codebase
- [ ] WhatsApp Business API successfully configured and authenticated
- [ ] Property tax message templates approved and functional
- [ ] Message routing to AI system works exclusively through WhatsApp
- [ ] Business phone number verified and webhook endpoints secured
- [ ] Rate limiting configured within WhatsApp Business API quotas
- [ ] Integration tested with sample property tax customer conversations
- [ ] Environment configuration updated and validated for WhatsApp-only setup