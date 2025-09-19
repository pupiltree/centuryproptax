---
name: remove-redundant-files
status: backlog
created: 2025-09-19T12:13:33Z
progress: 0%
prd: .claude/prds/remove-redundant-files.md
github: https://github.com/pupiltree/centuryproptax/issues/11
---

# Epic: Remove Redundant Files

## Overview

Systematically remove unused Krishna Diagnostics components from the Century Property Tax codebase to achieve 40-60% repository size reduction while preserving essential LangGraph architecture. This cleanup leverages static analysis and dependency mapping to safely eliminate voice processing, image analysis, Instagram integration, and medical domain remnants that serve no purpose for the WhatsApp-based property tax chatbot defined in the AI Customer Support Chatbot PRD.

## Architecture Decisions

- **Preservation Strategy**: Maintain LangGraph two-node workflow (Assistant → Tools) as core architecture
- **Removal Methodology**: Static analysis followed by incremental removal with functional validation
- **Safety Approach**: Git-branch-based experimentation with comprehensive rollback capability
- **Dependency Management**: Package dependency cleanup guided by actual import usage analysis
- **Documentation Alignment**: Real-time documentation updates to reflect cleaned codebase structure

## Technical Approach

### Frontend Components
**No Frontend Changes Required**
- WhatsApp integration remains unchanged (uses WhatsApp native interface)
- Property tax chatbot UI preserved through existing webhook handlers
- Remove Instagram-specific UI components and configurations

### Backend Services

**Services to Preserve**
- LangGraph core engine (Assistant → Tools workflow)
- WhatsApp Business API integration
- Property tax domain tools (6 tools developed for chatbot)
- Database and Redis persistence layers
- FastAPI web framework and core endpoints

**Services to Remove**
- Voice processing services (`/services/voice/`) - entire directory
- Image analysis services (`/services/image_analysis/`) - entire directory
- Instagram API handlers and webhook processors
- Medical domain test suites and configuration files
- Advanced analytics dashboards (marked as "future consideration")

**Dependency Cleanup**
- Remove packages only used by deleted services
- Preserve shared dependencies (FastAPI, SQLAlchemy, Redis, LangChain)
- Update requirements.txt to reflect actual usage
- Clean Docker configurations for removed services

### Infrastructure

**Deployment Simplification**
- Reduce Docker container complexity by removing unused service containers
- Simplify docker-compose configuration for remaining services
- Preserve existing deployment pipeline for core components
- Maintain Redis and PostgreSQL infrastructure unchanged

**Configuration Cleanup**
- Remove environment variables for deleted services
- Clean configuration files of Instagram and voice service references
- Preserve WhatsApp and property tax tool configurations
- Update health check endpoints to reflect actual services

## Implementation Strategy

**Phase 1: Analysis and Validation (Day 1)**
- Automated dependency analysis using import tracking tools
- Static analysis to identify zero-usage components
- Comprehensive testing of current functionality before changes
- Git branch creation for safe experimentation

**Phase 2: Major Service Removal (Day 2)**
- Remove entire unused service directories in order of risk (voice, image analysis, Instagram)
- Update import statements and package dependencies
- Validate core functionality after each major removal
- Commit changes incrementally for granular rollback capability

**Phase 3: Cleanup and Documentation (Day 3)**
- Remove orphaned configuration files and dead imports
- Update documentation to reflect cleaned architecture
- Final integration testing and deployment validation
- Measure and document achieved repository size reduction

**Risk Mitigation**
- Functional testing after each removal phase
- Git commits enable immediate rollback to any previous state
- Parallel validation environment for testing changes
- Comprehensive import resolution validation before final commit

## Tasks Created
- [ ] #12 - Dependency Analysis and Usage Mapping (parallel: false)
- [ ] #13 - Voice Services Complete Removal (parallel: true)
- [ ] #14 - Image Analysis Services Removal (parallel: true)
- [ ] #15 - Instagram Integration Cleanup (parallel: true)
- [ ] #16 - Medical Domain Final Cleanup (parallel: true)
- [ ] #17 - Configuration and Dependency Optimization (parallel: false)
- [ ] #18 - Documentation and Code Alignment (parallel: false)
- [ ] #19 - Comprehensive Testing and Validation (parallel: false)

Total tasks: 8
Parallel tasks: 4
Sequential tasks: 4
Estimated total effort: 32-44 hours across 3 days
## Dependencies

**External Service Dependencies**
- Git repository with full commit history for rollback capability
- Development environment for testing removed components
- Static analysis tools (Python AST, dependency parsers)
- Package management tools (pip, npm) for dependency cleanup

**Internal Dependencies**
- AI Customer Support Chatbot functionality must remain operational
- WhatsApp Business API integration cannot be disrupted
- Property tax tools and database schema must be preserved
- Redis conversation state persistence must continue functioning

**Process Dependencies**
- Code review process for validating removal decisions
- Testing validation after each removal phase
- Documentation update workflow parallel to code changes
- Backup and rollback procedures tested before major removals

## Success Criteria (Technical)

**Performance Benchmarks**
- Repository size reduced by 40-60% (measured by line count and file size)
- Package dependencies reduced by 30%+ (measured by requirements.txt)
- Docker image size reduced by 20%+ through service container removal
- Zero broken imports or import resolution errors

**Quality Gates**
- All property tax chatbot functionality operational after cleanup
- WhatsApp message sending and receiving tests pass
- Property tax tools and calculations function correctly
- Database operations and Redis persistence working
- Zero Python import errors or circular dependencies

**Acceptance Criteria**
- Complete property tax conversation flow from contact to consultation scheduling
- All 6 property tax domain tools operational and accessible
- WhatsApp webhook processing functional with message persistence
- Clean deployment process with only required services and dependencies

## Estimated Effort

**Overall Timeline**: 3 days (aligned with PRD implementation strategy)
- Day 1: Analysis and validation (30% effort) - Comprehensive dependency mapping
- Day 2: Major service removal (50% effort) - Voice, image analysis, Instagram cleanup
- Day 3: Refinement and documentation (20% effort) - Final cleanup and validation

**Resource Requirements**
- 1 Senior Developer: Static analysis, dependency mapping, and systematic removal
- Development focus: Maximize safety through incremental validation and git-based rollback

**Critical Path Items**
1. Comprehensive dependency analysis to avoid accidental removal of required components
2. Voice and image analysis service removal (highest impact on repository size)
3. Instagram integration cleanup (moderate complexity due to shared messaging patterns)
4. Final validation and documentation update to reflect cleaned architecture

**Risk Mitigation Strategy**
- Git branch experimentation prevents main branch corruption
- Incremental removal with functional testing after each phase
- Parallel validation environment for testing changes before commit
- Comprehensive rollback procedures tested before beginning removal process

**Expected Deliverables**
- Cleaned codebase with 40-60% size reduction
- Updated documentation reflecting actual implementation
- Validated deployment process with only required services
- Comprehensive removal log documenting what was eliminated and why
