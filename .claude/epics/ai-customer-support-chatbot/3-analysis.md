---
issue: 3
analyzed: 2025-09-19T04:03:25Z
status: closed
streams: 4
---

# Issue #3 Analysis: Database Schema Adaptation

## Overview
Transform Krishna Diagnostics medical database models to Century Property Tax property entities while preserving the repository pattern architecture. This involves adapting customer profiles, test catalogs, bookings, and message history to handle property records, tax assessments, appeals, and customer inquiries specific to property tax administration.

## Current Medical Schema Analysis
The existing schema includes:
- **CustomerProfile**: Medical history, bookings, preferences
- **TestCatalog**: Medical tests with pricing and requirements
- **TestBooking**: Test scheduling, payment, status tracking
- **MessageHistory**: Conversation history with medical context
- **TicketMessage/SupportTicket**: Support system with medical categories
- **AgentSession**: Agent handling system

## Parallel Streams

### Stream A: Core Property Entities
- **Scope**: Create fundamental property tax entities (Property, PropertyOwner, TaxAssessment)
- **Files**:
  - `/home/glitch/Projects/Active/centuryproptax/services/persistence/database.py` (add new models)
  - `/home/glitch/Projects/Active/centuryproptax/alembic/versions/[new]_create_property_entities.py` (migration)
- **Duration**: 6-8 hours
- **Dependencies**: None (can start immediately)
- **New Models**:
  - `Property`: parcel_id, address, property_type, square_footage, zoning
  - `PropertyOwner`: name, contact_info, ownership_percentage
  - `TaxAssessment`: year, assessed_value, tax_amount, due_dates, tax_rate
  - `PropertyOwnership`: junction table for property-owner relationships

### Stream B: Assessment & Appeals System
- **Scope**: Create assessment processing and appeals workflow models
- **Files**:
  - `/home/glitch/Projects/Active/centuryproptax/services/persistence/database.py` (add models)
  - `/home/glitch/Projects/Active/centuryproptax/alembic/versions/[new]_create_appeals_system.py` (migration)
- **Duration**: 6-8 hours
- **Dependencies**: Stream A (Property entities must exist)
- **New Models**:
  - `Appeal`: property_id, status, submission_date, reason, documents, outcomes
  - `AppealDocument`: file storage for appeal evidence
  - `Payment`: assessment_id, amount, date, method, reference_numbers
  - `TaxBill`: generated bills with payment tracking

### Stream C: Customer Adaptation
- **Scope**: Transform CustomerProfile and related models from medical to property tax context
- **Files**:
  - `/home/glitch/Projects/Active/centuryproptax/services/persistence/database.py` (modify existing)
  - `/home/glitch/Projects/Active/centuryproptax/services/persistence/repositories.py` (adapt methods)
  - `/home/glitch/Projects/Active/centuryproptax/alembic/versions/[new]_adapt_customer_models.py` (migration)
- **Duration**: 4-6 hours
- **Dependencies**: None (can run parallel with A/B)
- **Changes**:
  - Remove medical fields (medical_conditions, medications, allergies)
  - Add property owner fields (owned_properties, preferred_contact_method)
  - Update business intelligence fields for property tax metrics
  - Rename TestBooking → PropertyAssessmentRequest

### Stream D: Support System Adaptation
- **Scope**: Adapt support tickets and chat models for property tax categories
- **Files**:
  - `/home/glitch/Projects/Active/centuryproptax/services/ticket_management/models.py` (modify categories)
  - `/home/glitch/Projects/Active/centuryproptax/services/persistence/database.py` (adapt MessageHistory)
  - `/home/glitch/Projects/Active/centuryproptax/alembic/versions/[new]_adapt_support_system.py` (migration)
- **Duration**: 4-6 hours
- **Dependencies**: Stream A (needs Property entities for context)
- **Changes**:
  - Update TicketCategory enum (ASSESSMENT_QUESTION, PAYMENT_ISSUE, APPEAL_PROCESS, TAX_CALCULATION, PROPERTY_INFO)
  - Add property_id and assessment_id to context fields
  - Adapt MessageHistory for property tax conversation context
  - Update chat session to include property and assessment information

## Coordination Points
- **Model Relationships**: Streams A and B must coordinate on foreign key relationships between Property, Assessment, and Appeal models
- **Repository Pattern**: Stream C repository adaptations should align with new models from Streams A and B
- **Migration Dependencies**: Migrations must run in sequence (A → B → C → D) due to foreign key constraints

## Sequential Dependencies
1. **Stream A** must complete Property entity creation before Stream B can add Appeals
2. **Stream D** requires property_id from Stream A for support ticket context
3. **Repository updates** in Stream C should happen after core entities from Streams A & B are established
4. **Seed data** loading requires all models to be created and migrated

## Risk Mitigation
- **Backward Compatibility**: Preserve existing chat and AI functionality structures during migration
- **Data Migration**: Plan data transformation strategy for existing customers and bookings
- **Testing**: Each stream should include comprehensive tests for new models and relationships
- **Rollback Plan**: Ensure each migration can be safely reverted if issues arise

## Success Criteria
- [ ] All property tax entities created with proper relationships
- [ ] Medical context removed and replaced with property tax context
- [ ] Support system categories updated for property tax workflows
- [ ] Repository pattern maintained with updated methods
- [ ] Migrations tested and documented
- [ ] No breaking changes to core AI customer support functionality