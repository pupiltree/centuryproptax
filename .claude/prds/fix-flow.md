---
name: fix-flow
description: Align property tax chatbot workflow with real-world consulting practices and industry standards
status: backlog
created: 2025-09-23T08:56:47Z
---

# PRD: Fix Property Tax Chatbot Workflow

## Executive Summary

The Century Property Tax chatbot currently misrepresents industry practices, uses incorrect terminology, and lacks proper qualification processes. This PRD outlines comprehensive changes to align the chatbot workflow with authentic Texas property tax consulting practices, including proper lead qualification, realistic timelines, regulatory compliance, and industry-standard terminology.

The goal is to transform the chatbot from a generic "assessment" service into an authentic property tax protest representation tool that accurately reflects how licensed property tax consultants actually operate in Texas.

## Problem Statement

### What problem are we solving?
The current chatbot workflow contains multiple critical discrepancies that could mislead customers and damage business credibility:

1. **Service Misrepresentation**: Positions services as "assessments" when the business is actually "protest representation"
2. **Poor Lead Qualification**: Missing essential questions that determine protest viability
3. **Unrealistic Expectations**: Promises immediate service when actual processes take 6-12 months
4. **Regulatory Non-Compliance**: Lacks required TDLR licensing disclaimers
5. **Industry Misalignment**: Uses terminology and processes that don't match real property tax consulting

### Why is this important now?
- **Legal Risk**: Misrepresenting services could violate TDLR regulations
- **Customer Trust**: Unrealistic promises damage long-term relationships
- **Conversion Quality**: Poor qualification leads to unviable cases and wasted resources
- **Competitive Disadvantage**: Authentic competitors sound more professional and trustworthy

## User Stories

### Primary User Personas

**Persona 1: Frustrated Homeowner**
- Texas residential property owner
- Received tax assessment increase of 15-40%
- Limited knowledge of appeal process
- Wants to understand if protest is viable

**Persona 2: Commercial Property Owner**
- Business owner with commercial real estate
- Sophisticated understanding of property values
- Time-sensitive due to business impact
- Needs expert representation for complex appeals

**Persona 3: Investment Property Owner**
- Owns multiple rental properties
- Cost-conscious about professional fees
- Experienced with previous protests
- Evaluating service providers

### Detailed User Journeys

**Journey 1: Initial Property Tax Concern**
1. User receives high tax assessment notice
2. Searches for help online, finds WhatsApp chatbot
3. Expresses concern: "My property tax went up 30%"
4. Chatbot qualifies the case with proper questions
5. Determines protest viability and explains realistic process
6. Schedules consultation if viable, or explains why not viable

**Journey 2: Exemption Questions**
1. User unsure about available exemptions
2. Chatbot asks qualifying questions about property use, age, income
3. Identifies missing exemptions or confirms current exemptions
4. Explains application process and deadlines
5. Offers to help with applications or exemption reviews

**Journey 3: Previous Protest Experience**
1. User mentions previous unsuccessful protest
2. Chatbot asks about previous representation, evidence used
3. Evaluates if new evidence or approach could succeed
4. Provides realistic assessment of chances for appeal
5. Schedules consultation if new strategy viable

### Pain Points Being Addressed

- **Current**: "I can get an assessment tomorrow" → **Fixed**: "Property protests typically take 6-8 months, with hearings scheduled from August-October"
- **Current**: "Pay $999 upfront" → **Fixed**: "No upfront fees - we only charge if we successfully reduce your taxes (typically 30-40% of savings)"
- **Current**: "Property Assessment Review" → **Fixed**: "Property Tax Protest Representation"

## Requirements

### Functional Requirements

#### Core Features and Capabilities

**1. Proper Lead Qualification System**
- Ask current assessed value vs. estimated market value
- Inquire about recent purchase price and date
- Check current exemptions (homestead, over-65, disability, etc.)
- Identify recent property improvements or changes
- Assess previous protest history and outcomes
- Determine property type and use classification

**2. Industry-Accurate Service Descriptions**
- Replace "Property Tax Assessment Review" with "Property Tax Protest Representation"
- Use "Appeal" instead of "Assessment" in service offerings
- Reference "Appraisal Review Board (ARB)" hearings
- Mention "Notice of Appraised Value" and protest deadlines

**3. Realistic Timeline Communication**
- Explain May 15 protest filing deadline
- Communicate 6-12 month process timeline
- Describe ARB hearing scheduling (typically August-October)
- Set expectations for evidence gathering period

**4. Regulatory Compliance Integration**
- Include TDLR registration disclosure
- Explain scope of representation services
- Provide proper disclaimers about legal advice limitations
- Reference Texas Tax Code sections when relevant

**5. Contingency Fee Structure Clarity**
- Emphasize "no upfront fees" consistently
- Explain contingency percentage (typically 30-40% of savings)
- Clarify when fees are charged (only after successful reduction)
- Describe what constitutes "success" in protest representation

#### User Interactions and Flows

**Qualification Flow:**
1. Property tax concern expressed
2. Current assessment value inquiry
3. Property purchase information
4. Recent improvements/changes
5. Current exemption status
6. Previous protest history
7. Viability assessment
8. Service recommendation or decline explanation

**Service Selection Flow:**
1. Viable case confirmed
2. Explain available services:
   - Informal Review (simple cases)
   - Formal Protest (complex cases)
   - ARB Hearing Representation
   - Exemption Applications
3. Match service to case complexity
4. Set realistic expectations

**Consultation Scheduling Flow:**
1. Service selected
2. Explain consultation process
3. Document requirements list
4. Scheduling with realistic availability
5. Confirmation with next steps
6. Pre-consultation preparation instructions

### Non-Functional Requirements

#### Performance Expectations
- Qualification process completion within 5-7 exchanges
- Response time under 3 seconds for all interactions
- Support for concurrent users during peak seasons (January-May)

#### Security Considerations
- Secure handling of property assessment documents
- Privacy protection for financial information
- Compliance with Texas privacy regulations

#### Scalability Needs
- Handle increased volume during protest season (Jan-May)
- Support multiple languages (Spanish, Vietnamese common in Texas)
- Integration with CRM for lead tracking

## Success Criteria

### Measurable Outcomes

**Lead Quality Metrics**
- Increase viable case conversion rate from current ~40% to 75%
- Reduce consultation no-shows from 25% to under 10%
- Improve client satisfaction scores to above 4.5/5

**Business Metrics**
- Increase qualified leads by 60% while maintaining quality
- Reduce time spent on non-viable consultations by 50%
- Achieve 90%+ accuracy in service recommendations

**Compliance Metrics**
- Zero regulatory violations or complaints
- 100% inclusion of required disclaimers
- Full alignment with TDLR requirements

### Key Performance Indicators

- **Qualification Accuracy**: % of chatbot-qualified cases that result in successful protests
- **Timeline Accuracy**: % of cases completed within communicated timeframes
- **Client Expectation Alignment**: Survey scores on "service matched expectations"
- **Conversion Rate**: Qualified consultations → signed representation agreements

## Constraints & Assumptions

### Technical Limitations
- Current LangGraph architecture must be maintained
- WhatsApp Business API message limits
- Existing database schema constraints

### Timeline Constraints
- Changes must be implemented before peak season (January 2025)
- Phased rollout to minimize disruption
- Testing period required before full deployment

### Resource Limitations
- Single developer for implementation
- Limited budget for new tools or services
- Reliance on existing AI models and infrastructure

### Regulatory Constraints
- Must comply with Texas Department of Licensing and Regulation rules
- Cannot provide legal advice beyond representation scope
- Required disclaimers must be included

### Business Assumptions
- Property tax protest season patterns will continue
- Contingency fee model remains industry standard
- Texas property tax law remains relatively stable

## Out of Scope

**Explicitly NOT Building:**
- Legal document preparation beyond standard forms
- Property valuation or appraisal services
- Tax payment processing or escrow services
- Multi-state property tax services (Texas only)
- Real estate transaction services
- Property management services

**Phase 2 Considerations (Future):**
- AI-powered document analysis
- Automated comparable property research
- Integration with county appraisal district systems
- Mobile app development

## Dependencies

### External Dependencies
- Texas Department of Licensing and Regulation (TDLR) requirements
- County appraisal district processes and timelines
- Texas Property Tax Code regulations
- WhatsApp Business API capabilities

### Internal Team Dependencies
- Legal review of new disclaimers and compliance language
- Business development team for service descriptions
- Customer service team for consultation scheduling
- Marketing team for terminology consistency across all channels

### Technical Dependencies
- Current LangGraph framework
- Google Gemini AI model capabilities
- Redis conversation storage system
- PostgreSQL database for customer data
- ChromaDB vector database for knowledge retrieval

## Implementation Phases

### Phase 1: Critical Fixes (Week 1-2)
- Update service terminology throughout system
- Add TDLR compliance disclaimers
- Remove any remaining payment collection references
- Fix timeline expectations in conversation examples

### Phase 2: Qualification System (Week 3-4)
- Implement proper qualification questions
- Add lead scoring and viability assessment
- Create decision trees for service recommendations
- Update conversation flows with new qualification process

### Phase 3: Enhanced User Experience (Week 5-6)
- Improve explanation of protest process
- Add timeline visualization in conversations
- Enhance service descriptions with realistic expectations
- Implement proper case complexity assessment

### Phase 4: Testing & Validation (Week 7-8)
- A/B testing of new qualification flow
- Validation against real case outcomes
- Performance optimization
- User acceptance testing

## Quality Assurance

### Testing Requirements
- Conversation flow testing with real property tax scenarios
- Compliance validation with legal team
- Performance testing under peak load conditions
- Multi-language testing for Spanish integration

### Success Validation
- Shadow testing with actual consultations
- Feedback collection from licensed property tax consultants
- Comparison of chatbot-qualified vs. manually-qualified cases
- Client satisfaction surveys post-implementation

## Risk Mitigation

### High-Risk Items
- **Regulatory Compliance**: Legal review required for all changes
- **Customer Confusion**: Clear communication about changes needed
- **Performance Impact**: Load testing required before deployment

### Mitigation Strategies
- Staged rollout with monitoring
- Fallback to previous version if issues arise
- Comprehensive testing in staging environment
- Documentation of all changes for audit trail

## Post-Launch Monitoring

### Metrics to Track
- Qualification accuracy rates
- Client satisfaction with new flow
- Conversion rates at each funnel stage
- System performance under load

### Continuous Improvement
- Monthly analysis of conversation patterns
- Quarterly review of qualification effectiveness
- Annual compliance audit
- Ongoing optimization based on user feedback

---

**Next Steps:**
1. Legal review of compliance requirements
2. Technical implementation planning
3. Stakeholder approval and resource allocation
4. Development sprint planning and execution