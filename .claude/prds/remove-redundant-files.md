---
name: remove-redundant-files
description: Systematic removal of unused Krishna Diagnostics components to create clean Century Property Tax codebase
status: backlog
created: 2025-09-19T12:05:51Z
---

# PRD: Remove Redundant Files

## Executive Summary

Century Property Tax codebase contains extensive unused components inherited from the Krishna Diagnostics clone. Despite successful domain transformation, the repository retains entire service directories, tools, and dependencies that serve no purpose for the property tax chatbot requirements. This PRD establishes a systematic approach to identify, validate, and remove redundant files while preserving the essential LangGraph architecture and required functionality defined in the AI Customer Support Chatbot PRD.

**Impact**: Reduce repository size by 40-60%, improve developer onboarding, eliminate security risks from unused code, and create a focused codebase aligned with actual business requirements.

## Problem Statement

### Core Problem
The Century Property Tax codebase is bloated with unused Krishna Diagnostics components that create maintenance overhead, security risks, and developer confusion. The complete cloning approach brought medical domain services that have no relevance to property tax operations.

### Specific Issues Identified
1. **Voice Processing Services** (`/services/voice/`) - PRD explicitly excludes voice/audio processing
2. **Image Analysis Services** (`/services/image_analysis/`) - No computer vision requirements for property tax
3. **Instagram Integration** - PRD focuses "WhatsApp only", Instagram components unused
4. **Medical Domain Tools** - Remnant medical tools and configurations not applicable
5. **Advanced Analytics** - Complex dashboards marked as "future consideration" in PRD
6. **Redundant Dependencies** - Package dependencies for unused services
7. **Orphaned Test Files** - Medical domain tests with no equivalent property tax coverage

### Business Impact
- **Developer Confusion**: 60%+ of codebase irrelevant to property tax domain
- **Security Risk**: Unused code paths create potential vulnerabilities
- **Maintenance Overhead**: Updates and patches applied to unused components
- **Repository Bloat**: Slower clones, larger deployments, increased storage costs
- **Onboarding Friction**: New developers must navigate irrelevant medical code

## User Stories

### Primary Persona: Development Team

#### User Story 1: Clean Development Environment
- **As a** developer working on Century Property Tax features
- **I want** a codebase containing only relevant property tax components
- **So that** I can focus on business logic without navigating medical domain code

**Acceptance Criteria:**
- All directories contain only property tax or shared infrastructure components
- No medical terminology in active code paths
- Import statements resolve to valid, used modules
- README and documentation reflect actual codebase contents

#### User Story 2: Efficient Onboarding
- **As a** new developer joining the property tax team
- **I want** clear codebase structure with predictable organization
- **So that** I can contribute productively within first week

**Acceptance Criteria:**
- Directory structure matches business requirements (no orphaned services)
- All documented features have corresponding implementation
- Test coverage reflects actual functionality (no medical test remnants)
- Development setup includes only required dependencies

#### User Story 3: Secure Deployment
- **As a** DevOps engineer managing production deployments
- **I want** minimal attack surface with only required code
- **So that** I can maintain security and reduce monitoring complexity

**Acceptance Criteria:**
- No unused endpoints or API routes in production
- Dependencies limited to required packages
- No dead code paths that could contain vulnerabilities
- Clear audit trail of what code serves business purposes

### Secondary Persona: Security Team

#### User Story 4: Compliance Assurance
- **As a** security auditor reviewing the Century Property Tax system
- **I want** assurance that all code serves documented business purposes
- **So that** I can approve the system for production use

**Acceptance Criteria:**
- Every service directory maps to PRD requirements
- No remnant medical data handling code (HIPAA irrelevant)
- Clean separation between property tax and shared infrastructure
- Documentation matches actual implementation

## Requirements

### Functional Requirements

#### FR1: Unused Service Identification
**Requirement**: Systematically identify Krishna Diagnostics services not required by property tax PRD
**Acceptance Criteria**:
- Compare all `/services/` subdirectories against PRD requirements
- Identify services with zero usage in property tax workflows
- Document business justification for retained services
- Flag services marked as "future consideration" in PRD

#### FR2: Dependency Analysis
**Requirement**: Analyze package dependencies for unused services
**Acceptance Criteria**:
- Map each dependency to consuming services
- Identify dependencies only used by removed services
- Preserve dependencies used by retained components
- Update requirements.txt to reflect actual usage

#### FR3: Safe File Removal
**Requirement**: Remove identified redundant files without breaking functionality
**Acceptance Criteria**:
- All property tax functionality remains operational after removal
- No broken import statements in active code paths
- Database migrations and schemas remain intact
- Configuration files updated to remove unused service references

#### FR4: Import Chain Validation
**Requirement**: Ensure all import statements resolve after file removal
**Acceptance Criteria**:
- Python import errors reduced to zero
- Circular import dependencies eliminated
- Dead import statements removed from retained files
- Module __all__ exports updated for cleanliness

### Non-Functional Requirements

#### NFR1: Preservation of Core Architecture
**Requirement**: LangGraph two-node workflow must remain unchanged
**Acceptance Criteria**:
- Assistant → Tools workflow preserved
- State management and Redis persistence intact
- Message handling and conversation flow operational
- Tool routing and selection mechanism preserved

#### NFR2: Backward Compatibility
**Requirement**: Essential APIs and interfaces remain stable
**Acceptance Criteria**:
- WhatsApp webhook endpoints continue functioning
- Database schema migration paths preserved
- Configuration file format remains compatible
- Docker deployment process unchanged

#### NFR3: Documentation Alignment
**Requirement**: Documentation reflects actual codebase contents
**Acceptance Criteria**:
- README files updated to remove medical references
- API documentation matches implemented endpoints
- Architecture diagrams reflect simplified structure
- Deployment guides reference only retained components

## Success Criteria

### Quantitative Metrics
1. **Repository Size Reduction**: 40-60% decrease in total codebase size
2. **Service Count**: Reduce from 15+ services to 6-8 core services
3. **Dependency Reduction**: 30%+ fewer package dependencies
4. **Import Statements**: Zero broken imports after cleanup

### Qualitative Metrics
1. **Developer Experience**: Clean, focused codebase structure
2. **Documentation Accuracy**: 100% alignment between docs and implementation
3. **Business Alignment**: Every retained component serves PRD requirements
4. **Security Posture**: Minimal attack surface with justified code paths

### Quality Assurance
1. **Functionality Preservation**: All property tax features operational
2. **Test Coverage**: Test suite reflects actual implementation
3. **Code Quality**: No dead code or unreachable branches
4. **Configuration Validity**: All config references point to existing components

## Constraints & Assumptions

### Technical Constraints
- **Preserve LangGraph Core**: Two-node workflow architecture must remain unchanged
- **Database Integrity**: Property tax data and schemas must be preserved
- **WhatsApp Integration**: Messaging functionality cannot be disrupted
- **Redis State**: Conversation persistence must continue operating

### Business Constraints
- **No Downtime**: Cleanup must not impact running demo environment
- **Rapid Execution**: Complete cleanup within 2-3 days maximum
- **Reversibility**: Changes must be trackable via git for rollback capability
- **Documentation**: Changes must be documented for compliance audit

### Assumptions
- **Usage Analysis**: Static analysis sufficient to identify unused components
- **Test Coverage**: Existing tests cover all critical property tax functionality
- **Dependencies**: Package management tools can safely remove unused dependencies
- **Import Resolution**: Python import system will clearly indicate missing modules

## Out of Scope

### Explicitly Excluded from Removal
- **Core LangGraph Components**: Assistant and tool execution engine
- **Database Infrastructure**: SQLAlchemy models and migration system
- **Redis Integration**: State persistence and conversation management
- **FastAPI Framework**: Web server and API endpoint handling
- **WhatsApp Integration**: Business API handlers and webhook processing
- **Property Tax Tools**: All 6 domain-specific tools developed for the chatbot

### Future Optimization (Not This PRD)
- **Code Refactoring**: Improving existing retained components
- **Performance Optimization**: Enhancing speed of preserved functionality
- **Additional Feature Development**: New property tax capabilities
- **Advanced Analytics**: Future dashboard and reporting features

## Dependencies

### External Dependencies
1. **Git Repository**: Comprehensive commit history for rollback capability
2. **Testing Environment**: Ability to validate functionality after removal
3. **Development Tools**: Static analysis tools for dependency mapping
4. **Documentation Tools**: README and doc generation capabilities

### Internal Dependencies
1. **Property Tax Functionality**: Must remain operational throughout cleanup
2. **AI Customer Support Chatbot**: Core requirements from completed epic
3. **Database Schema**: Property tax data model preservation
4. **Configuration Management**: Environment and deployment settings

### Process Dependencies
- **Code Review**: Technical validation of removal decisions
- **Testing Validation**: Functional testing after each removal phase
- **Documentation Updates**: Real-time doc updates as files are removed
- **Backup Strategy**: Git commits for each major removal milestone

## Implementation Strategy

### Phase 1: Analysis and Mapping (Day 1)
**Objective**: Create comprehensive inventory of removable components

**Activities**:
- **Service Inventory**: List all `/services/` subdirectories with purpose analysis
- **Dependency Mapping**: Map package dependencies to consuming services
- **Import Analysis**: Trace import statements across codebase
- **Usage Validation**: Confirm zero usage of identified redundant services

**Deliverables**:
- Removal inventory spreadsheet with business justification
- Dependency removal plan with impact analysis
- Import statement cleanup checklist
- Risk assessment for each removal category

### Phase 2: Strategic Removal (Day 2)
**Objective**: Remove major unused service categories safely

**Activities**:
- **Voice Services Removal**: Delete `/services/voice/` and dependencies
- **Image Analysis Removal**: Delete `/services/image_analysis/` and related code
- **Instagram Integration**: Remove Instagram API handlers and configuration
- **Medical Domain Cleanup**: Final removal of medical terminology and tools

**Deliverables**:
- Git commits for each major service removal
- Updated dependency files (requirements.txt, package.json)
- Documentation updates for removed services
- Functional testing validation for retained services

### Phase 3: Refinement and Validation (Day 3)
**Objective**: Clean up remnants and validate complete system

**Activities**:
- **Import Chain Cleanup**: Remove dead imports and update __all__ exports
- **Configuration Cleanup**: Remove references to deleted services
- **Test Suite Cleanup**: Remove or update tests for removed functionality
- **Documentation Finalization**: Update README, API docs, and architecture guides

**Deliverables**:
- Final cleaned codebase with zero broken imports
- Updated comprehensive documentation
- Complete test suite covering retained functionality
- Deployment validation in clean environment

## Risk Assessment

### High Risk Items
1. **Accidental Removal of Required Components**
   - **Mitigation**: Comprehensive testing after each removal phase
   - **Rollback**: Git commits enable immediate restoration

2. **Breaking Import Dependencies**
   - **Mitigation**: Static analysis before removal, incremental testing
   - **Detection**: Automated import validation scripts

3. **Database Schema Corruption**
   - **Mitigation**: Database schema preserved in separate validation
   - **Backup**: Database dumps before any schema-related changes

### Medium Risk Items
1. **Configuration File Errors**
   - **Mitigation**: Configuration validation scripts
   - **Testing**: Environment startup testing after changes

2. **Documentation Inconsistency**
   - **Mitigation**: Documentation updates parallel to code changes
   - **Validation**: Documentation review process

### Low Risk Items
1. **Package Dependency Conflicts**
   - **Mitigation**: Virtual environment testing
   - **Resolution**: Package manager dependency resolution

## Detailed Removal Inventory

### High-Priority Removals (Confirmed Unused)

#### 1. Voice Processing Services
**Location**: `/services/voice/`
**Justification**: PRD explicitly excludes "voice/audio processing" for MVP
**Components to Remove**:
- Voice chat state management
- Audio processing pipelines
- Voice-to-text integrations
- Speech synthesis components
- Voice-specific configurations

#### 2. Image Analysis Services
**Location**: `/services/image_analysis/`
**Justification**: No computer vision requirements in property tax PRD
**Components to Remove**:
- Image processing algorithms
- Computer vision models
- OCR specific to medical documents
- Image classification systems
- Visual analytics tools

#### 3. Instagram Integration
**Location**: Various files in `/src/api/`, `/services/communication/`
**Justification**: PRD specifies "WhatsApp only" integration
**Components to Remove**:
- Instagram API handlers
- Instagram webhook processors
- Instagram-specific message formatting
- Instagram business profile management
- Instagram media handling

#### 4. Advanced Analytics and Dashboards
**Location**: `/services/analytics/`, `/monitoring/`, dashboard components
**Justification**: PRD lists "advanced analytics dashboard" as "future consideration"
**Components to Remove**:
- Complex reporting dashboards
- Advanced visualization components
- Business intelligence tools
- Custom analytics engines
- Report generation systems

### Medium-Priority Removals (Likely Unused)

#### 5. Medical Domain Test Files
**Location**: `/tests/` with medical references
**Justification**: Tests should reflect actual property tax functionality
**Components to Remove**:
- Medical workflow test cases
- Healthcare-specific test data
- Medical domain unit tests
- Health record processing tests
- Medical compliance test scenarios

#### 6. Redundant Configuration Files
**Location**: Various config directories
**Justification**: Simplify configuration to property tax requirements only
**Components to Remove**:
- Medical service configurations
- Instagram API configurations
- Voice service settings
- Image processing parameters
- Unused environment variables

### Low-Priority Removals (Validation Required)

#### 7. Development and Debugging Tools
**Location**: `/scripts/`, `/tools/`, development utilities
**Justification**: Retain only tools relevant to property tax development
**Components to Evaluate**:
- Medical data generation scripts
- Healthcare-specific debugging tools
- Development utilities for unused services
- Medical domain testing scripts
- Legacy migration tools

## Validation Checklist

### Pre-Removal Validation
- [ ] Inventory all files and directories in removal scope
- [ ] Confirm zero usage of targeted components in property tax workflows
- [ ] Create git branch for safe experimentation
- [ ] Document current functionality for regression testing
- [ ] Backup current database schema and sample data

### Post-Removal Validation
- [ ] All property tax chatbot functionality operational
- [ ] WhatsApp integration sending and receiving messages
- [ ] Property tax tools and calculations functioning
- [ ] Database operations and migrations working
- [ ] Redis conversation persistence operational
- [ ] Zero broken import statements in Python
- [ ] Configuration files valid and parseable
- [ ] Docker containers build and deploy successfully
- [ ] All tests pass in retained test suite
- [ ] Documentation reflects actual codebase contents

### Success Verification
- [ ] Repository size reduced by target percentage
- [ ] Service count matches business requirements
- [ ] Dependencies align with actual usage
- [ ] Code coverage reflects implemented functionality
- [ ] Security scan shows reduced attack surface
- [ ] Developer onboarding documentation accurate
- [ ] Production deployment process validated
- [ ] Rollback procedure tested and documented

## Conclusion

The removal of redundant Krishna Diagnostics files represents a critical step in establishing Century Property Tax as a focused, maintainable, and secure property tax chatbot system. By systematically eliminating unused voice processing, image analysis, Instagram integration, and medical domain components, we create a clean foundation that aligns codebase reality with business requirements.

This cleanup effort directly supports the AI Customer Support Chatbot success criteria by removing distractions, reducing security risks, and improving developer productivity. The aggressive but methodical approach ensures we preserve the proven LangGraph architecture while eliminating everything that doesn't serve property tax protest conversion objectives.

**Expected Outcome**: A lean, focused Century Property Tax codebase containing only components necessary for WhatsApp-based property tax consulting, enabling faster development, simpler maintenance, and cleaner compliance audits.