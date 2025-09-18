---
name: ai-customer-support-chatbot
description: AI-powered WhatsApp chatbot to convert property tax protest prospects into customers for Century Property Tax
status: backlog
created: 2025-09-18T13:34:29Z
---

# PRD: AI Customer Support Chatbot

## Executive Summary

Century Property Tax will deploy an AI-powered customer support chatbot on WhatsApp to address the massive 53% awareness deficit in property tax protests. The chatbot will convert prospects into customers by educating them about their rights, calculating potential savings, and guiding them through Century's no-risk consultation process. This solution leverages proven LangGraph architecture from Krishna Diagnostics to achieve 70-90% containment rates while targeting the $190M+ annual market opportunity.

## Problem Statement

### Core Problem
Only 5% of property owners appeal their assessments despite 30-60% being over-assessed with 65% average success rates. Century Property Tax needs an AI agent to overcome the awareness gap and convert educated prospects into customers.

### Market Opportunity
- **$190M+ saved annually** by leading firms demonstrates market size
- **53% awareness deficit** - most don't know they can protest
- **46% vs 11% appeal rates** between high/low income areas shows education impact
- **12.3% conversion rates** achievable with professional services approach

### Customer Pain Points
1. **Bureaucratic intimidation** - process complexity fears
2. **Time investment concerns** - despite 15-30 minute consultations
3. **Retaliation fears** - though only 5% risk of increases
4. **Cost-benefit skepticism** - despite no-win-no-fee models
5. **Previous negative experiences** creating lasting skepticism

## User Stories

### Primary Persona: Property Owner Prospect
**Demographics:** Property owners receiving assessment notices, particularly those with 45%+ increases

#### User Journey 1: Awareness & Education
- **As a** property owner who received a high tax assessment
- **I want to** understand if I can challenge it and what it costs
- **So that** I can make an informed decision without fear or confusion

**Acceptance Criteria:**
- Bot explains protest rights within first 3 exchanges
- Calculates potential savings using property details
- Addresses common fears (retaliation, complexity, cost)
- Provides specific local success metrics for credibility

#### User Journey 2: Lead Qualification & Conversion
- **As a** qualified prospect (property value >$75K, timeline urgency)
- **I want to** understand Century's specific value proposition
- **So that** I can decide whether to engage their services

**Acceptance Criteria:**
- Bot qualifies based on property value, assessment increase, deadline proximity
- Presents no-risk value proposition with specific ROI calculations
- Routes high-value leads ($500K+ properties) to human agents
- Schedules consultation within 24 hours for qualified leads

#### User Journey 3: Objection Handling & Risk Mitigation
- **As a** skeptical property owner with concerns
- **I want to** understand guarantees and risk mitigation
- **So that** I feel confident proceeding without financial risk

**Acceptance Criteria:**
- Bot addresses "taxes aren't that high" with comparable data
- Explains no-win-no-fee structure clearly
- Provides county-specific success rates
- Offers immediate consultation for complex cases

## Requirements

### Functional Requirements

#### Core Conversational AI
- **Two-node LangGraph workflow** (preserve from Krishna Diagnostics)
- **Multilingual support** (English, Spanish minimum for Texas market)
- **Conversation persistence** across sessions using Redis
- **Dynamic tool selection** based on LLM routing (no hardcoded flows)

#### WhatsApp Integration
- **Webhook handler** for WhatsApp Business API
- **Message verification** and signature validation
- **Rich media support** (images, documents, location sharing)
- **Business profile integration** with Century branding

#### Property Tax Domain Tools
1. **Property Validation Tool**
   - Validate property PIN/address against county records
   - Retrieve current assessment and historical data
   - Calculate assessment increase percentage

2. **Savings Calculator Tool**
   - Estimate potential tax savings based on property details
   - Use comparable sales data from county records
   - Factor in Century's historical success rates by county

3. **Deadline Tracking Tool**
   - Calculate days remaining until May 15 deadline
   - Send automated reminders for urgent cases
   - Route time-sensitive leads to human agents

4. **Lead Qualification Tool**
   - Score leads based on property value, timeline, assessment increase
   - Auto-disqualify properties under $75K assessed value
   - Flag high-value properties for priority handling

5. **Document Processing Tool**
   - Process uploaded property tax notices
   - Extract key data (property details, assessment amounts, deadlines)
   - Validate information against county records

6. **Consultation Scheduling Tool**
   - Integration with Century's calendar system
   - Schedule 15-30 minute initial consultations
   - Send confirmation and reminder messages

#### Knowledge Base Integration
- **RAG system** for Texas property tax law and procedures (real data from comptroller.texas.gov)
- **County-specific data** (success rates, filing procedures, contacts) (mock data for demo)
- **Century service information** (process, pricing, guarantees)
- **Comparable sales database** for property valuation (mock data for demo)

### Non-Functional Requirements

#### Performance
- **Response time:** <5 seconds for initial acknowledgment
- **Conversation processing:** <30 seconds for complex queries
- **Concurrent users:** Support 1000+ simultaneous conversations
- **Uptime:** 99.9% availability during business hours

#### Security & Compliance
- **SOC2 compliance** for customer data protection
- **TDLR regulatory compliance** for property tax consulting
- **PII encryption** for sensitive customer information
- **Audit trails** for all customer interactions and decisions

#### Scalability
- **Horizontal scaling** for increased conversation volume
- **Database optimization** for fast property data retrieval
- **Cache strategy** for frequently accessed county data
- **Rate limiting** to prevent abuse and manage costs

## Success Criteria

### Primary Metrics
1. **Conversion Rate:** 12%+ prospect-to-customer conversion
2. **Containment Rate:** 70-90% queries resolved without human intervention
3. **Response Time:** <5 minutes average first response
4. **Lead Quality:** 80%+ qualified leads meet minimum criteria

### Secondary Metrics
1. **Engagement Rate:** 60%+ complete qualification flow
2. **Customer Satisfaction:** 4.5+ star rating for bot interactions
3. **Cost Reduction:** 50% reduction in initial consultation time
4. **Revenue Impact:** $500K+ additional revenue from bot-generated leads

### Quality Assurance
1. **Accuracy Rate:** 95%+ accurate property data retrieval
2. **Compliance Rate:** 100% regulatory compliance for tax consulting
3. **Error Rate:** <2% critical errors requiring human intervention
4. **Escalation Rate:** <10% conversations require human takeover

## Constraints & Assumptions

### Technical Constraints
- **Preserve Krishna Diagnostics architecture:** Two-node LangGraph workflow must remain unchanged
- **WhatsApp only:** No Instagram integration required for this use case
- **Existing infrastructure:** Leverage FastAPI, SQLAlchemy, Redis architecture
- **Model selection:** Continue using Gemini-2.5-Flash for cost efficiency

### Business Constraints
- **Demo timeline:** Must be ready for demonstration within 4 weeks
- **Budget limitations:** Maximize reuse of existing codebase components
- **TDLR compliance:** Must meet Texas Department of Licensing requirements
- **Demo environment:** Use mock data for customer database and proprietary county data (real legal/procedural data from public sources)

### Assumptions
- **WhatsApp adoption:** Target customers actively use WhatsApp for business communication
- **Data availability:** County property records accessible via APIs or web scraping
- **Legal framework:** Current Texas property tax protest laws remain stable
- **Market demand:** Research findings reflect actual prospect behavior

## Out of Scope

### Excluded Features
- **Instagram integration** (focus on WhatsApp only)
- **Voice/audio processing** (text-only for MVP)
- **Payment processing** (handled by existing Century systems)
- **Document preparation** (bot guides to human agents for filing)
- **Multi-tenant architecture** (single-tenant for Century only)

### Future Considerations
- **Advanced analytics dashboard** for conversation insights
- **A/B testing framework** for prompt optimization
- **Integration with CRM systems** beyond basic lead capture
- **Mobile app version** of the chatbot interface
- **Automated document filing** with county systems

## Dependencies

### External Dependencies
1. **WhatsApp Business API** - Meta's messaging platform access
2. **County property databases** - Assessment and comparable sales data
3. **Texas state systems** - TDLR registration verification
4. **Google AI API** - Gemini model access for LLM functionality
5. **Century internal systems** - Calendar, CRM, and lead management

### Internal Dependencies
1. **Krishna Diagnostics codebase** - Core LangGraph architecture
2. **Database migration** - Adapt schema for property tax domain
3. **System prompt development** - Property tax expertise integration
4. **Tool development** - Custom property tax calculation tools
5. **Compliance review** - Legal validation of automated advice limits

### Technical Dependencies
- **Redis cluster** for conversation state persistence
- **PostgreSQL database** for property and customer data
- **FastAPI framework** for webhook and API endpoints
- **Docker containers** for deployment and scaling
- **Monitoring infrastructure** for performance and error tracking

## Implementation Strategy

### Phase 1: Architecture Adaptation (Week 1)
- Preserve core LangGraph workflow from Krishna Diagnostics
- Adapt database schema for property tax domain
- Configure WhatsApp integration (remove Instagram)
- Develop basic property validation tools with mock data

### Phase 2: Domain Intelligence (Week 2-3)
- Create property tax knowledge base and RAG system using real legal data from comptroller.texas.gov
- Develop savings calculator and lead qualification tools with mock property scenarios
- Implement Texas-specific legal compliance features using actual regulations
- Build consultation scheduling integration with mock calendar

### Phase 3: Demo Preparation (Week 4)
- Comprehensive testing with realistic property tax scenarios using mock data
- Performance optimization for demo load
- Documentation and training materials
- Demo environment setup and validation with sample conversations

### Risk Mitigation
- **Compliance risk:** Early legal review of automated advice boundaries
- **Demo data risk:** Ensure mock data represents realistic property tax scenarios
- **Performance risk:** Load testing with realistic conversation volumes
- **Integration risk:** Fallback mechanisms for external API failures in production