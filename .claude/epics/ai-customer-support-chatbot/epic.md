---
name: ai-customer-support-chatbot
status: backlog
created: 2025-09-18T19:27:30Z
progress: 0%
prd: .claude/prds/ai-customer-support-chatbot.md
github: https://github.com/pupiltree/centuryproptax/issues/1
---

# Epic: AI Customer Support Chatbot

## Overview

Implement an AI-powered WhatsApp chatbot for Century Property Tax by adapting the proven Krishna Diagnostics LangGraph architecture. The solution leverages the existing two-node workflow, FastAPI infrastructure, and Redis persistence while replacing medical domain logic with property tax expertise. This approach minimizes development time by reusing 80% of the core architecture while delivering a specialized property tax protest conversion system.

## Architecture Decisions

- **Preserve Krishna Diagnostics Core**: Two-node LangGraph workflow (Assistant → Tools) remains unchanged
- **Model Selection**: Continue using Gemini-2.5-Flash for cost efficiency and proven performance
- **Infrastructure**: Leverage existing FastAPI, SQLAlchemy, Redis stack
- **Channel Focus**: WhatsApp-only integration (remove Instagram components)
- **Data Strategy**: Real legal data from comptroller.texas.gov + mock property/customer data for demo
- **Compliance**: SOC2 + TDLR regulatory requirements using existing patterns

## Technical Approach

### Frontend Components
- **WhatsApp Business Profile**: Century branding with business verification
- **Rich Media Support**: Property document upload, location sharing, assessment images
- **Conversation UI**: Leverage existing WhatsApp native interface (no custom UI needed)

### Backend Services

**Core LangGraph System (Preserved)**
- Two-node workflow: `PropertyTaxAssistant` → `ToolNode`
- State management: `PropertyTaxState` with message history
- Conversation persistence: Redis checkpointer
- Dynamic tool routing: LLM-driven tool selection

**Property Tax Domain Tools (New)**
- Property Validation Tool: PIN/address lookup with mock county data
- Savings Calculator Tool: ROI estimation using comparable sales scenarios
- Deadline Tracking Tool: May 15 deadline management with automated alerts
- Lead Qualification Tool: Scoring based on property value ($75K+), timeline urgency
- Document Processing Tool: Property tax notice extraction and validation
- Consultation Scheduling Tool: Mock calendar integration for demo

**Data Models (Adapted)**
- PropertyProfile: Property details, assessment history, protest eligibility
- CustomerProfile: Contact info, property portfolio, consultation preferences
- PropertyTaxInteraction: Conversation tracking, qualification status, outcomes
- TaxCalculation: Savings estimates, scenarios, supporting data

### Infrastructure

**Deployment**: Docker containers using existing Krishna Diagnostics patterns
**Scaling**: Horizontal scaling with Redis state distribution
**Monitoring**: Preserve existing health check and logging infrastructure
**Security**: Webhook verification, PII encryption, audit trails

## Implementation Strategy

**Adaptation Over Recreation**: Modify existing Krishna Diagnostics codebase rather than building from scratch
**Incremental Testing**: Test each adapted component against property tax scenarios
**Demo Focus**: Prioritize realistic demo scenarios over production data integration
**Compliance First**: Ensure TDLR regulatory compliance throughout development

## Task Breakdown Preview

High-level task categories that will be created:
- [ ] **Codebase Adaptation**: Clone and modify Krishna Diagnostics for property tax domain
- [ ] **WhatsApp Integration**: Configure messaging and remove Instagram components
- [ ] **Property Tax Tools**: Develop 6 domain-specific tools with mock data
- [ ] **Knowledge Base**: Create RAG system with real Texas property tax law data
- [ ] **Database Schema**: Adapt models for property tax entities and workflows
- [ ] **System Prompts**: Replace medical expertise with property tax guidance
- [ ] **Demo Environment**: Setup mock data scenarios and test conversations
- [ ] **Compliance & Testing**: TDLR compliance validation and performance testing

## Dependencies

**External Service Dependencies**
- WhatsApp Business API access and verification
- Google AI API for Gemini model access
- Texas Comptroller data sources for legal/procedural information

**Internal Dependencies**
- Krishna Diagnostics codebase analysis and adaptation rights
- Century Property Tax business rules and consultation workflows
- Legal review of automated advice boundaries for TDLR compliance

**Infrastructure Dependencies**
- Redis cluster for conversation state persistence
- PostgreSQL database for property and customer data
- Docker deployment environment for containerized services

## Success Criteria (Technical)

**Performance Benchmarks**
- <5 second response time for 95% of interactions
- 1000+ concurrent conversation support
- 99.9% uptime during business hours
- <30 second processing for complex property calculations

**Quality Gates**
- 95%+ accuracy in property data retrieval and validation
- 100% TDLR regulatory compliance in automated advice
- <2% critical error rate requiring human intervention
- 70-90% conversation containment without escalation

**Acceptance Criteria**
- Complete property tax conversation flow from initial contact to consultation scheduling
- Accurate savings calculations using realistic property scenarios
- Proper escalation to human agents for complex cases
- Comprehensive audit trail for regulatory compliance

## Estimated Effort

**Overall Timeline**: 4 weeks (aligned with demo requirements)
- Week 1: Architecture adaptation and basic tool development (40% effort)
- Week 2-3: Advanced tools, knowledge base, and compliance features (45% effort)
- Week 4: Demo preparation, testing, and optimization (15% effort)

**Resource Requirements**
- 1 Senior Developer: Core architecture adaptation and LangGraph modifications
- Development focus: Maximize code reuse, minimize net new development

**Critical Path Items**
1. Krishna Diagnostics codebase analysis and adaptation planning
2. Property tax domain tools development with mock data integration
3. WhatsApp Business API configuration and webhook testing
4. TDLR compliance validation and legal boundary establishment

**Risk Mitigation**
- Early validation of Krishna Diagnostics adaptation feasibility
- Parallel development of tools and knowledge base components
- Continuous testing with realistic property tax scenarios
- Fallback to simplified demo if complex integrations face delays

## Tasks Created
- [ ] #2 - Codebase Adaptation - Clone and modify Krishna Diagnostics for property tax domain (parallel: false)
- [ ] #3 - Database Schema Adaptation - Adapt models for property tax entities (parallel: true)
- [ ] #4 - WhatsApp Integration Setup - Configure messaging and remove Instagram components (parallel: true)
- [ ] #5 - Property Tax Tools Development - Develop 6 domain-specific tools with mock data (parallel: true)
- [ ] #6 - System Prompts and AI Configuration - Replace medical expertise with property tax guidance (parallel: true)
- [ ] #7 - Knowledge Base and RAG System - Create RAG system with real Texas property tax law data (parallel: true)
- [ ] #8 - Demo Environment and Mock Data Setup (parallel: false)
- [ ] #9 - Compliance Testing and Demo Preparation (parallel: false)

Total tasks: 8
Parallel tasks: 5
Sequential tasks: 3
