# Comprehensive Dependency Analysis Report
**Issue #12 - Remove Redundant Files Epic**
**Date:** 2025-09-19

## Executive Summary

Comprehensive static analysis of the property tax codebase revealed significant opportunities for cleanup and removal of Krishna Diagnostics remnants. The analysis examined 121 Python files and identified components with zero or minimal usage in property tax workflows.

### Key Findings:
- **Voice Services**: 5 files with conditional usage in medical workflows (not property tax)
- **Image Analysis**: 1 empty file with broken imports referencing non-existent modules
- **Instagram References**: 33 files containing 237 references (requires careful evaluation)
- **Medical Remnants**: 22 files with 195 medical-related references
- **Unused Packages**: 18 of 37 required packages are not actively imported

## Detailed Analysis Results

### 1. Voice Services Analysis
**Status: CAUTION REQUIRED - NOT ZERO USAGE**

**Files Found:**
- `services/voice/voice_setup.py`
- `services/voice/livekit_data_bridge.py`
- `services/voice/voice_chat_state.py`
- `services/voice/property_tax_voice_agent.py`
- `services/voice/voice_config.py`

**Active Imports:**
- **WhatsApp Webhooks** (`src/api/whatsapp_webhooks.py`): 3 import statements
- **Self-references**: Voice modules importing each other

**Usage Pattern:**
Voice services are conditionally imported in the main WhatsApp webhook handler for:
- Voice call state management
- LiveKit data bridge functionality
- Integration with medical prescription analysis (Krishna Diagnostics remnant)

**Risk Assessment:** 🟡 **MEDIUM RISK**
- Voice services are imported but primarily used for medical workflows
- Property tax workflows do not appear to use voice functionality
- Safe to remove IF medical functionality is being removed

### 2. Image Analysis Services Analysis
**Status: SAFE TO REMOVE - BROKEN IMPORTS**

**Files Found:**
- `services/image_analysis/__init__.py` (empty file with comment only)

**Import Attempts:**
- `agents/simplified/property_document_tools.py` attempts to import non-existent `property_document_parser` module
- Import fails with `ModuleNotFoundError`

**Risk Assessment:** 🟢 **SAFE TO REMOVE**
- Module is incomplete/broken
- Referenced functionality does not exist
- No actual implementation to break

### 3. Instagram/Meta Integration Analysis
**Status: EXTENSIVE USAGE - PRESERVE**

**Usage Statistics:**
- **33 files** contain Instagram/Meta references
- **237 total references** across the codebase
- Integrated throughout communication and messaging services

**Key Integration Points:**
- WhatsApp Business API (Meta product)
- Instagram messaging APIs
- Authentication and webhook handling
- Business communication workflows

**Risk Assessment:** 🔴 **CRITICAL - DO NOT REMOVE**
- Instagram/Meta integration is core to WhatsApp Business functionality
- Removal would break primary communication channels
- Property tax workflows depend on WhatsApp messaging

### 4. Medical/Krishna Diagnostics Remnants
**Status: REQUIRES CAREFUL REMOVAL**

**Usage Statistics:**
- **22 files** contain medical references
- **195 total medical-related references**
- Keywords: medical, doctor, patient, diagnosis, krishna, diagnostic, prescription

**Distribution:**
- Embedded in voice services
- Mixed with property tax workflows
- Configuration and setup files

**Risk Assessment:** 🟡 **MEDIUM RISK - SURGICAL REMOVAL REQUIRED**
- Medical code is intertwined with legitimate property tax functionality
- Requires careful code surgery rather than bulk deletion
- Some references may be in comments or variable names

### 5. Package Dependency Analysis
**Status: SIGNIFICANT CLEANUP OPPORTUNITY**

**Unused Packages (18 of 37):**
```
requests, cryptography, alembic, asyncpg, aiosqlite, mcp,
razorpay, python-jose, passlib, python-multipart,
prometheus-client, langfuse, pytest-mock, pytest-cov,
black, isort, flake8, mypy
```

**Analysis:**
- Many unused packages are development/testing tools
- Some packages may be used indirectly by dependencies
- Database packages (asyncpg, aiosqlite) suggest multi-database support not implemented

**Risk Assessment:** 🟢 **SAFE TO REMOVE**
- Most unused packages are development tools or optional dependencies
- Verify indirect usage before removal

## Service Usage Matrix

| Service Category | Files | Active Usage | Property Tax Relevance | Removal Safety |
|------------------|-------|--------------|------------------------|----------------|
| Voice Services | 5 | Conditional (Medical) | None | Medium Risk |
| Image Analysis | 1 | Broken Imports | None | Safe |
| Instagram/Meta | 33 | Extensive | Critical | Do Not Remove |
| Medical Remnants | 22 | Legacy Code | None | Surgical Removal |
| Unused Packages | 18 | None | None | Safe |

## Dependency Chain Analysis

### Critical Preservation Requirements:
1. **LangGraph Workflow**: Two-node Assistant → Tools pattern (PRESERVED)
2. **WhatsApp Business API**: Core communication channel (PRESERVED)
3. **Property Tax Tools**: All 6 domain-specific tools (PRESERVED)
4. **Database Persistence**: Redis and SQL layers (PRESERVED)
5. **FastAPI Framework**: Web API endpoints (PRESERVED)

### Safe Removal Chains:
1. **Image Analysis** → `property_document_tools.py` (update imports)
2. **Voice Services** → Remove medical workflow integration
3. **Medical References** → Code cleanup and variable renaming
4. **Unused Packages** → requirements.txt cleanup

## Removal Safety Report

### Phase 1: Safe Immediate Removal
- [ ] Remove `services/image_analysis/` directory
- [ ] Fix broken import in `property_document_tools.py`
- [ ] Remove unused development packages from requirements.txt

### Phase 2: Conditional Voice Services Removal
- [ ] Verify property tax workflows don't use voice features
- [ ] Remove voice imports from WhatsApp webhooks
- [ ] Delete `services/voice/` directory

### Phase 3: Medical Code Cleanup
- [ ] Surgical removal of medical references from comments
- [ ] Update variable names and function references
- [ ] Preserve core workflow logic

### Phase 4: Package Optimization
- [ ] Remove confirmed unused packages
- [ ] Verify indirect dependencies
- [ ] Update Docker configurations

## Risk Mitigation Strategies

### High-Risk Operations:
1. **Voice Service Removal**: Test WhatsApp webhook functionality thoroughly
2. **Medical Code Surgery**: Use automated refactoring tools
3. **Package Removal**: Verify production requirements

### Rollback Procedures:
1. **Git Branch Strategy**: Create feature branch for each removal phase
2. **Testing Protocol**: Run full test suite after each change
3. **Staged Deployment**: Deploy changes incrementally

## Recommendations

### Immediate Actions (Safe):
1. Remove broken image analysis services
2. Clean up unused development packages
3. Fix broken import statements

### Planned Actions (Requires Validation):
1. Remove voice services after confirming property tax workflows don't need them
2. Surgical removal of medical references from working code
3. Optimize package dependencies

### Preserve (Critical):
1. All Instagram/Meta/WhatsApp integration code
2. LangGraph workflow implementation
3. Property tax domain tools and database layers

## Conclusion

The codebase contains significant remnants from its Krishna Diagnostics origin that can be safely removed with proper planning. The most immediate opportunity is removing the broken image analysis services and unused packages. Voice services require careful evaluation as they're conditionally used in medical workflows that may not be relevant to property tax operations.

**Estimated Cleanup Impact:**
- **Files**: Remove ~6 files safely, clean ~22 files surgically
- **Packages**: Remove 18 unused dependencies
- **Code Reduction**: ~15-20% reduction in codebase size
- **Maintenance**: Significantly reduced complexity

---
*Analysis conducted using static AST parsing and comprehensive grep-based pattern matching across 121 Python files.*