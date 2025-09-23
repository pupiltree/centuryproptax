---
name: fix-flow
status: backlog
created: 2025-09-23T09:15:02Z
progress: 0%
prd: .claude/prds/fix-flow.md
github: https://github.com/pupiltree/centuryproptax/issues/48
---

# Epic: Fix Property Tax Chatbot Workflow

## Overview

Transform the existing property tax chatbot from a generic "assessment" service into an authentic Texas property tax protest representation tool. This epic focuses on leveraging the existing LangGraph architecture while updating prompts, conversation flows, and qualification logic to align with real-world property tax consulting practices. The approach prioritizes prompt engineering and configuration changes over architectural rebuilds to minimize complexity while maximizing impact.

## Architecture Decisions

**Leverage Existing Infrastructure**
- Keep current LangGraph-based conversation architecture
- Maintain existing tool structure (create_order, validate_pin_code, property_tax_rag_tool)
- Utilize existing WhatsApp integration and Redis conversation storage
- Preserve PostgreSQL customer data management

**Prompt-Driven Approach**
- Primary changes implemented through prompt updates in property_tax_assistant_v3.py
- Service terminology corrections via string replacements
- Qualification logic embedded in conversation prompts rather than new tools
- Regulatory compliance through disclaimer additions

**Configuration-Based Improvements**
- Update serviceable ZIP codes and area descriptions
- Modify conversation examples and few-shot prompts
- Enhance RAG knowledge base with protest-specific information
- Adjust response templates for industry accuracy

## Technical Approach

### Frontend Components
**No Changes Required**
- WhatsApp interface remains unchanged
- Existing message handling and formatting preserved
- Current response length optimizations maintained

### Backend Services

**Core Conversation Engine (property_tax_assistant_v3.py)**
- Update system prompts with industry-correct terminology
- Replace "assessment" language with "protest/appeal" terminology
- Add TDLR compliance disclaimers to conversation templates
- Implement qualification question sequences in prompt logic
- Update timeline expectations throughout conversation flows

**Knowledge Base (RAG System)**
- Enhance vector database with Texas protest procedures
- Add seasonal deadline information (May 15 protest deadline)
- Include ARB hearing process documentation
- Update service descriptions with realistic timelines

**Service Configuration (enhanced_workflow_tools.py)**
- Update service offerings from "assessments" to "protest representation"
- Modify service descriptions in ADVANCED_ASSESSMENT_SERVICES
- Add protest viability scoring logic
- Update area coverage information with protest context

### Infrastructure
**Existing Infrastructure Maintained**
- Current deployment pipeline unchanged
- Redis conversation storage adequate for enhanced flows
- PostgreSQL schema supports additional qualification data
- ChromaDB vector store handles expanded knowledge base

## Implementation Strategy

**Phase 1: Terminology & Compliance (Week 1)**
- Single-pass string replacement across all conversation prompts
- Add TDLR disclaimers to system prompts
- Update service names in configuration files
- Deploy and test terminology changes

**Phase 2: Qualification Enhancement (Week 2)**
- Add qualification questions to conversation prompts
- Update few-shot examples with proper qualification flows
- Enhance lead scoring logic in conversation templates
- Test qualification accuracy with sample scenarios

**Phase 3: Timeline & Process Education (Week 3)**
- Update all timeline references to realistic 6-12 month expectations
- Add seasonal deadline awareness to prompts
- Enhance process explanation in conversation flows
- Update RAG knowledge base with protest procedures

**Risk Mitigation**
- Staged deployment with feature flags
- A/B testing capability through prompt versioning
- Rollback plan via prompt reversion
- Shadow testing against real consultation outcomes

## Implementation Tasks

Created tasks for development execution:
- [x] **001-update-service-terminology.md**: Replace "assessment" with "protest" language (2 days, high priority)
- [x] **002-add-tdlr-compliance.md**: Integrate required disclaimers and licensing information (1 day, high priority)
- [x] **003-implement-qualification-logic.md**: Add proper qualifying questions and lead scoring (3 days, high priority)
- [x] **004-update-timeline-expectations.md**: Replace immediate service promises with realistic timelines (2 days, medium priority)
- [x] **005-enhance-process-education.md**: Improve explanation of ARB hearings and procedures (2 days, medium priority)
- [x] **006-expand-knowledge-base.md**: Add Texas-specific protest information to RAG system (3 days, high priority)
- [x] **007-update-service-descriptions.md**: Modify service offerings to reflect protest representation (1 day, medium priority)
- [x] **008-test-and-validate.md**: Comprehensive testing of new conversation flows (3 days, high priority)
- [x] **009-deploy-and-monitor.md**: Production deployment with monitoring (2 days, high priority)

**Total Estimated Effort**: 19 development days across 9 tasks

## Dependencies

**External Dependencies**
- Legal review of TDLR compliance language (2-3 days)
- Business stakeholder approval of terminology changes
- Texas Property Tax Code reference materials for RAG enhancement

**Internal Dependencies**
- Existing LangGraph conversation architecture
- Current ChromaDB vector database setup
- Redis conversation storage system
- WhatsApp Business API integration

**Technical Prerequisites**
- Current system must remain functional during transition
- Backup conversation prompts before modifications
- Test environment validation before production deployment

## Success Criteria (Technical)

**Performance Benchmarks**
- Conversation response time remains under 3 seconds
- Qualification completion within 5-7 message exchanges
- 95% uptime during deployment phases

**Quality Gates**
- 100% terminology consistency across all conversation flows
- All TDLR compliance requirements included
- Qualification accuracy validated against real cases
- No regression in existing functionality

**Acceptance Criteria**
- Legal team approval of compliance language
- Business team approval of service descriptions
- User acceptance testing with property tax scenarios
- Performance testing under peak load conditions

## Estimated Effort

**Overall Timeline: 3 weeks**
- Week 1: Terminology and compliance updates (16 hours)
- Week 2: Qualification logic implementation (20 hours)
- Week 3: Testing, validation, and deployment (16 hours)
- Total: ~52 hours development effort

**Resource Requirements**
- 1 Senior Developer (primary implementation)
- 1 Business Analyst (terminology validation - 8 hours)
- 1 Legal Review (compliance validation - 4 hours)
- 1 QA Engineer (testing - 12 hours)

**Critical Path Items**
1. Legal review of TDLR compliance language (blocks compliance implementation)
2. Business approval of terminology changes (blocks all prompt updates)
3. Knowledge base enhancement (required for accurate process education)
4. End-to-end testing (required before production deployment)

**Low-Risk High-Impact Approach**
This epic prioritizes prompt engineering and configuration changes over architectural modifications, reducing implementation risk while delivering significant business value. The existing LangGraph framework provides sufficient flexibility for all required changes without system redesign.

---

**Implementation Priority: HIGH**
This epic addresses critical business risks (regulatory compliance, customer trust) while leveraging existing technical infrastructure for rapid, low-risk deployment.