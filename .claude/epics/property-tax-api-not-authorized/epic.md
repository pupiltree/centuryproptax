---
name: property-tax-api-not-authorized
status: backlog
created: 2025-09-21T20:34:09Z
progress: 0%
prd: .claude/prds/property-tax-api-not-authorized.md
github: https://github.com/pupiltree/centuryproptax/issues/30
last_sync: 2025-09-23T10:30:00Z
---

# Epic: property-tax-api-not-authorized

## Overview

Replace unauthorized Texas Comptroller government API calls with a comprehensive mock data system that enables demo functionality and development workflows. Implement local API endpoints that mirror the structure of government APIs while providing realistic property tax data for demonstration and testing purposes.

## Architecture Decisions

- **Mock-First Design**: Create local FastAPI endpoints that mirror government API structure exactly
- **Environment-Based Switching**: Use configuration to toggle between mock and real APIs without code changes
- **Data-Driven Approach**: Generate realistic Texas property data using existing demographic and geographic patterns
- **Existing Infrastructure**: Leverage current FastAPI app structure and data models from the existing codebase
- **JSON Response Fidelity**: Ensure mock responses match expected government API formats for seamless integration

## Technical Approach

### Backend Services

**Mock API Endpoints** (`src/api/mock_property_tax.py`)
- Property tax calculator endpoint (`/api/mock/property/calculator`)
- Property records lookup (`/api/mock/property/records`)
- Tax notifications (`/api/mock/property/notifications`)
- Payment history (`/api/mock/property/payments`)
- Integrate with existing FastAPI app structure

**Data Generation Service** (`services/mock_data/property_tax_generator.py`)
- Generate realistic Texas property records using existing county/demographic data
- Create varied scenarios: residential, commercial, industrial properties
- Support different tax situations: current, delinquent, exemptions, appeals
- Leverage existing data patterns from Texas Comptroller scraper knowledge

**Configuration Management** (`config/api_settings.py`)
- Environment variable control for API mode switching
- Centralized API endpoint configuration
- Integration with existing settings.py structure
- Support for different mock data scenarios

### Data Models

**Enhanced Property Models** (extend existing models)
- Property record structure matching government API responses
- Tax calculation data with realistic formulas
- Payment history with transaction details
- Notification/alert structures for tax notices

### Infrastructure

**Environment Configuration**
- `PROPERTY_TAX_API_MODE`: "mock" or "production"
- `MOCK_DATA_SCENARIO`: Configure different demo scenarios
- Integrate with existing `.env` structure

**Response Caching**
- Cache generated mock data for consistent responses
- Pre-generate common lookup scenarios
- Optimize for <200ms response times

## Implementation Strategy

**Phase 1: Core Mock Infrastructure (Week 1)**
- Create basic mock API endpoints structure
- Implement property records and calculator endpoints
- Set up environment-based configuration switching
- Generate basic realistic property data

**Phase 2: Rich Demo Data (Week 2)**
- Expand mock data to cover diverse property scenarios
- Implement notifications and payment history endpoints
- Add realistic Texas geographic and demographic data
- Create configurable demo scenarios

**Phase 3: Integration & Polish (Week 3)**
- Replace existing government API calls with mock endpoints
- Comprehensive testing of all property tax workflows
- Performance optimization for demo requirements
- Documentation and setup guides

**Risk Mitigation**
- Maintain exact API response formats to ensure existing code compatibility
- Implement fallback mechanisms for API switching
- Validate mock data realism through stakeholder review

## Task Breakdown Preview

High-level task categories that will be created:
- [ ] **Mock API Infrastructure**: Create FastAPI endpoints mirroring government API structure
- [ ] **Property Data Generator**: Build realistic Texas property tax data generation system
- [ ] **Environment Configuration**: Implement API mode switching and configuration management
- [ ] **Data Models & Schemas**: Define mock data structures matching government API responses
- [ ] **Calculator Logic**: Implement realistic property tax calculation algorithms
- [ ] **Payment & History**: Create payment history and notification mock endpoints
- [ ] **Integration & Testing**: Replace government API calls and validate functionality
- [ ] **Demo Scenarios**: Create pre-configured demo data sets for presentations
- [ ] **Documentation**: Setup guides and API documentation for mock system

## Dependencies

**External Dependencies**
- FastAPI framework (existing)
- Existing Texas Comptroller scraper data patterns
- Property tax calculation methodologies (research)

**Internal Dependencies**
- Current application API structure (src/api/)
- Existing data models and database setup
- Environment configuration system (config/)
- Demo and sales team input for realistic scenarios

**Integration Points**
- Existing WhatsApp bot integration for property tax inquiries
- Current FastAPI routing and middleware
- Environment variable management system

## Success Criteria (Technical)

**Performance Benchmarks**
- Mock API responses under 200ms
- Support 100+ concurrent demo requests
- Minimal memory footprint for mock data storage

**Quality Gates**
- 100% functional replacement of government API calls
- Realistic demo data covering 95% of property tax scenarios
- Seamless switching between mock and production modes
- Zero breaking changes to existing application functionality

**Acceptance Criteria**
- All property tax features work with mock data
- Demo presentations run without API authorization errors
- Development workflows no longer blocked by government API dependencies
- Mock data maintains logical consistency and realistic relationships

## Estimated Effort

**Overall Timeline**: 3 weeks
- Week 1: Core infrastructure and basic endpoints (15-20 hours)
- Week 2: Rich data generation and full endpoint coverage (20-25 hours)
- Week 3: Integration, testing, and documentation (10-15 hours)

**Resource Requirements**
- 1 backend developer (primary)
- Sales/demo team consultation for realistic scenarios
- QA support for cross-scenario testing

**Critical Path Items**
1. Mock API endpoint structure (enables all other work)
2. Property data generator (provides realistic demo content)
3. Environment configuration (enables production deployment)
4. Integration testing (validates seamless replacement)

## Implementation Benefits

**Immediate Value**
- Unblocks demo presentations and sales workflows
- Enables development testing without external API dependencies
- Eliminates government API authorization concerns

**Long-term Value**
- Provides controlled demo environment with impressive property data
- Enables offline development and testing workflows
- Maintains option to integrate real APIs when authorized
- Supports A/B testing between different data scenarios

## Tasks Created
- [ ] #31 - Mock API Infrastructure - Create FastAPI endpoints structure (parallel: true)
- [ ] #32 - Environment Configuration - Implement API mode switching system (parallel: true)
- [ ] #33 - Data Models & Schemas - Define mock data structures (parallel: false)
- [ ] #34 - Property Data Generator - Realistic Texas Property Data Generation (parallel: false)
- [ ] #35 - Calculator Logic - Property Tax Calculation Algorithms (parallel: false)
- [ ] #36 - Payment & History - Payment and Notification Mock Endpoints (parallel: false)
- [ ] #37 - Integration & Testing - Replace Government API Calls with Mock Endpoints (parallel: false)
- [ ] #38 - Demo Scenarios & Documentation - Pre-configured Demo Data and Guides (parallel: false)

Total tasks: 8
Parallel tasks: 2
Sequential tasks: 6
Estimated total effort: 95-118 hours (12-15 working days)
