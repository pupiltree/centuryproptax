---
issue: 6
analyzed: 2025-09-19T16:45:00Z
status: closed
streams: 4
---

# Issue #6 Analysis: System Prompts and AI Configuration - Replace medical expertise with property tax guidance

## Overview
Transform all AI prompts, conversation flows, and configuration from Krishna Diagnostics' medical expertise domain to Century Property Tax's property tax guidance domain. This involves comprehensive replacement of system prompts, response templates, conversation logic, and AI persona configuration while maintaining the sophisticated multilingual capabilities and tool integration architecture.

## Current State Analysis

### Existing AI Components Found:
1. **Main Property Tax Assistant**: `/home/glitch/Projects/Active/centuryproptax/agents/core/property_tax_assistant_v3.py`
   - Already partially converted from medical to property tax domain
   - Contains comprehensive property tax conversation flows
   - Includes multilingual support and tool integration

2. **Voice Agent**: `/home/glitch/Projects/Active/centuryproptax/services/voice/krishna_voice_agent.py`
   - Still contains medical/healthcare prompts and workflows
   - References Krishna Diagnostics branding
   - Uses medical RAG tools and prescription analysis

3. **Configuration**: `/home/glitch/Projects/Active/centuryproptax/config/settings.py`
   - Already updated for property tax domain
   - Contains property tax API endpoints

4. **Legacy Medical Components**: Several files still reference medical tools and workflows

## Parallel Streams

### Stream A: Core AI Prompt Transformation
- **Scope**: Replace all medical expertise system prompts with property tax domain knowledge in main assistant
- **Files**:
  - `agents/core/property_tax_assistant_v3.py` (ENHANCE existing prompts)
  - `agents/simplified/enhanced_workflow_tools.py` (UPDATE any embedded prompts)
  - `agents/simplified/property_document_tools.py` (UPDATE analysis prompts)
- **Key Changes**:
  - Refine existing property tax prompt for better domain expertise
  - Add Texas property tax law knowledge integration
  - Implement property tax terminology and definitions
  - Configure legal advice boundaries and disclaimers
  - Enhance county-specific information handling
- **Duration**: 6-8 hours
- **Dependencies**: None - can start immediately

### Stream B: Voice Agent Complete Overhaul
- **Scope**: Transform Krishna Diagnostics voice agent to Century Property Tax voice assistant
- **Files**:
  - `services/voice/krishna_voice_agent.py` (COMPLETE REWRITE → property_tax_voice_agent.py)
  - `services/voice/voice_config.py` (UPDATE configuration)
  - `services/voice/voice_setup.py` (UPDATE references)
  - `services/voice/voice_chat_state.py` (UPDATE state management)
- **Transformation Tasks**:
  - Replace Maya/Krishna branding with Century Property Tax persona
  - Convert medical consultation flows to property tax inquiry workflows
  - Replace prescription analysis with property document analysis
  - Update medical RAG tools to property tax RAG tools
  - Transform test booking to assessment booking workflows
- **New Voice Conversation Flows**:
  - Property tax assessment inquiries
  - Appeal process guidance
  - Exemption qualification discussions
  - Payment deadline consultations
  - Document requirement explanations
- **Duration**: 8-10 hours
- **Dependencies**: Requires Stream C completion for updated RAG tools

### Stream C: Response Templates and Conversation Logic
- **Scope**: Create comprehensive property tax response templates and conversation flows
- **Files**:
  - Create: `config/response_templates.py` (NEW - property tax specific templates)
  - Create: `agents/core/conversation_flows.py` (NEW - standardized flows)
  - Update: `services/messaging/modern_integrated_webhook_handler.py` (UPDATE fallback responses)
- **Template Categories**:
  - **Assessment Inquiries**: Property value questions, assessment increases
  - **Appeal Process**: Filing deadlines, required documents, success factors
  - **Exemptions**: Homestead, senior, disability, veteran exemptions
  - **Payment Options**: Installment plans, online payment methods
  - **Deadlines**: Tax payment dates, appeal filing deadlines
  - **Documentation**: Required forms, supporting evidence
- **Multilingual Templates**:
  - English, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi
  - Consistent terminology across all languages
  - Cultural sensitivity for property tax concerns
- **Duration**: 6-8 hours
- **Dependencies**: Can run parallel with Stream A

### Stream D: AI Configuration and Guardrails
- **Scope**: Implement property tax domain-specific AI configuration, guardrails, and safety measures
- **Files**:
  - Create: `config/ai_configuration.py` (NEW - centralized AI settings)
  - Create: `agents/core/guardrails.py` (NEW - domain-specific safety measures)
  - Update: `config/settings.py` (ADD AI configuration variables)
- **Guardrails Implementation**:
  - Legal advice boundaries and disclaimers
  - Referral patterns for complex legal questions
  - Data privacy considerations for property information
  - Accuracy disclaimers for tax calculations and estimates
  - Professional consultation recommendations for appeals
- **AI Persona Configuration**:
  - Knowledge boundaries definition
  - Empathy calibration for taxpayer concerns
  - Professional tone while avoiding legal advice
  - Proactive information offering patterns
  - Multi-turn conversation context management
- **Domain Expertise Integration**:
  - Texas property tax law knowledge base
  - County-specific procedures and deadlines
  - Exemption criteria and application processes
  - Appeal timeline and requirement frameworks
  - Payment method and installment option details
- **Duration**: 4-6 hours
- **Dependencies**: Coordinates with Stream A for prompt integration

## Legacy Component Cleanup

### Files Requiring Medical→Property Tax Conversion:
1. `agents/simplified/medical_rag_tool.py` → Delete or convert to property_tax_rag_tool.py
2. `services/image_analysis/prescription_parser.py` → Update for property document analysis
3. Remove medical references from:
   - `services/messaging/modern_integrated_webhook_handler.py`
   - `scripts/validate-workflow.py`
   - Any remaining medical test booking workflows

## Coordination Points
- **Stream A ↔ Stream C**: Response templates must align with main assistant conversation flows
- **Stream B ↔ Stream C**: Voice agent responses must use same template structure as text assistant
- **Stream A ↔ Stream D**: AI guardrails must be integrated into main prompt configuration
- **Stream C ↔ Stream D**: Response templates must incorporate safety disclaimers and boundaries

## Technical Requirements

### Prompt Engineering Specifications:
- Clear, conversational tone appropriate for property owners
- Empathy for taxpayer concerns and frustrations
- Step-by-step guidance for complex processes (appeals, exemptions)
- Multiple option presentation (payment plans, appeal strategies)
- Time-sensitive information inclusion (deadlines, filing periods)
- Texas statute and regulation references when helpful

### AI Persona Characteristics:
- Knowledgeable property tax assistant (not advisor)
- Helpful without providing legal advice
- Empathetic to taxpayer financial concerns
- Proactive in offering relevant information
- Clear about limitations and professional referral needs

### Multilingual Consistency:
- Maintain exact language matching for user responses
- Consistent terminology across all supported languages
- Cultural sensitivity in property tax discussions
- Clear professional boundaries in all languages

## Sequential Dependencies
1. **Foundation** (Stream A): Update core property tax assistant prompts
2. **Parallel Execution**: Streams B, C, and D can execute simultaneously after Stream A provides prompt framework
3. **Integration Phase**: Coordinate all AI components to use consistent templates and guardrails
4. **Testing & Validation**: Comprehensive testing of AI responses across property tax scenarios in multiple languages
5. **Legacy Cleanup**: Remove remaining medical references and deprecated tools

## Success Criteria
- All medical references completely removed from AI prompts and responses
- Property tax expertise clearly established in AI behavior patterns
- Conversation flows handle common property tax scenarios appropriately
- AI provides helpful guidance while respecting legal advice boundaries
- Response quality validated across various property tax inquiry types
- Guardrails prevent inappropriate advice or recommendations
- AI persona consistent with Century Property Tax brand and services
- Multilingual support maintains quality across all supported languages