---
name: fix-log-issues
status: backlog
created: 2025-09-20T16:20:45Z
progress: 0%
prd: .claude/prds/fix-log-issues.md
github: https://github.com//issues/20
---

# Epic: fix-log-issues

## Overview

Consolidate logging infrastructure by standardizing on structlog, fixing critical configuration issues, and implementing robust logging practices. Focus on minimal code changes that leverage existing patterns while resolving deployment failures and mixed log formats.

## Architecture Decisions

- **Single Framework**: Standardize on structlog (already in use) and remove conflicting logging.basicConfig()
- **Configuration**: Environment-driven logging configuration with graceful fallbacks
- **File Handling**: Replace hardcoded paths with configurable locations using existing FastAPI startup patterns
- **Rotation**: Leverage Python's RotatingFileHandler to prevent disk exhaustion
- **Performance**: Maintain existing async patterns, no new threading or complex buffering

## Technical Approach

### Backend Services

**Core Logging Module** (`src/core/logging.py`)
- Centralized logging configuration function
- Environment variable handling with fallbacks
- Structured logger factory with consistent naming

**Configuration Integration** (`src/main.py`)
- Move logging setup to FastAPI startup event handler
- Remove hardcoded paths and conflicting configurations
- Integrate with existing environment variable patterns

**Logger Standardization** (Multiple files)
- Replace mixed logger creation patterns with single factory function
- Maintain existing component-specific context binding
- Preserve current log content and structure

### Infrastructure

**Environment Variables**
- `LOG_LEVEL`: Configure logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `LOG_DIR`: Override default log directory location
- `LOG_FILE_ENABLED`: Disable file logging for containerized deployments

**File Rotation**
- Size-based rotation (100MB max per file)
- Keep 10 historical files
- Automatic compression of rotated logs

## Implementation Strategy

**Phase 1: Critical Infrastructure (Week 1)**
- Fix hardcoded log directory and startup race condition
- Implement basic log rotation
- Test deployment reliability

**Phase 2: Standardization (Week 2)**
- Consolidate logging frameworks
- Implement centralized configuration
- Update all logger creation patterns

**Phase 3: Enhancement (Week 3)**
- Add structured logging standards
- Implement environment-based configuration
- Performance optimization and monitoring hooks

**Risk Mitigation**
- Maintain backward compatibility during transition
- Graceful degradation when logging fails
- Comprehensive testing across environments

## Task Breakdown Preview

High-level task categories that will be created:
- [ ] **Critical Fixes**: Resolve hardcoded paths and startup failures
- [ ] **Logging Module**: Create centralized logging configuration
- [ ] **Framework Consolidation**: Remove logging conflicts, standardize on structlog
- [ ] **Logger Standardization**: Update logger creation across all files
- [ ] **Configuration System**: Implement environment-based logging config
- [ ] **Log Rotation**: Add file rotation and compression
- [ ] **Performance Testing**: Benchmark logging overhead
- [ ] **Integration Testing**: Validate across deployment environments
- [ ] **Documentation**: Update logging practices and deployment guides

## Dependencies

**External Dependencies**
- structlog (already installed)
- Python logging.handlers.RotatingFileHandler (stdlib)
- Environment variable access patterns (existing)

**Internal Dependencies**
- FastAPI startup event system (existing)
- Current environment configuration patterns
- Existing component context binding in WhatsApp client

**Prerequisite Work**
- None - can proceed immediately with existing codebase

## Success Criteria (Technical)

**Performance Benchmarks**
- Logging overhead < 5ms per operation
- No degradation in API response times
- Memory usage remains stable

**Quality Gates**
- 100% deployment success rate
- Zero logging-related application crashes
- All logs parseable as valid JSON
- Backward compatibility maintained during transition

**Acceptance Criteria**
- Application starts in all environments regardless of log directory availability
- Consistent JSON log format across all components
- Log files automatically rotate before consuming excessive disk space
- Environment variables control logging behavior without code changes

## Estimated Effort

**Overall Timeline**: 3 weeks
- Week 1: Critical infrastructure fixes (2-3 days)
- Week 2: Framework standardization (4-5 days)
- Week 3: Enhancement and optimization (3-4 days)

**Resource Requirements**
- 1 developer (backend focus)
- DevOps support for environment variable configuration
- QA support for cross-environment testing

**Critical Path Items**
1. Fix hardcoded log directory (blocks deployments)
2. Resolve startup race condition (blocks application start)
3. Standardize logging framework (blocks monitoring integration)
4. Implement log rotation (prevents disk exhaustion)

## Tasks Created
- [ ] #21 - Fix hardcoded log directory path and startup race condition (parallel: true)
- [ ] #22 - Create centralized logging configuration module (parallel: false)
- [ ] #23 - Implement log rotation and compression (parallel: true)
- [ ] #24 - Remove logging framework conflicts from main.py (parallel: false)
- [ ] #25 - Standardize logger creation across all service files (parallel: true)
- [ ] #26 - Implement structured logging standards (parallel: true)
- [ ] #27 - Implement performance benchmarking for logging overhead (parallel: true)
- [ ] #28 - Create comprehensive integration tests for logging system (parallel: true)
- [ ] #29 - Update documentation and deployment guides (parallel: true)

Total tasks: 9
Parallel tasks: 6
Sequential tasks: 3
Estimated total effort: 40-49 hours (5-6 working days)
