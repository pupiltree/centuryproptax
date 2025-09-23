---
title: Update Timeline Expectations
epic: fix-flow
priority: medium
estimate: 2 days
dependencies: [001]
---

# Update Timeline Expectations

## Description
Replace unrealistic immediate service promises with accurate 6-12 month property tax protest timelines. This sets proper expectations about the ARB hearing process, seasonal deadlines, and overall protest duration to align with Texas property tax law requirements.

## Acceptance Criteria
- [ ] May 15 protest filing deadline communicated clearly
- [ ] 6-12 month overall process timeline explained
- [ ] ARB hearing scheduling (August-October) mentioned
- [ ] Evidence gathering period expectations set
- [ ] Seasonal workflow patterns explained to customers
- [ ] All "immediate" or "tomorrow" service promises removed

## Technical Details
**Files to Modify:**
- `agents/core/property_tax_assistant_v3.py` - Update timeline references in prompts
- Replace immediate scheduling language with realistic timelines
- Add seasonal deadline awareness to conversation templates

**Specific Timeline Updates:**
- Replace: "Schedule tomorrow" → "Process typically takes 6-8 months with hearings in August-October"
- Add: "Important: Protests must be filed by May 15 for the current tax year"
- Include: "Evidence gathering and preparation period: 2-4 months"
- Explain: "ARB hearings are typically scheduled between August and October"
- Clarify: "Final resolution can take 6-12 months depending on case complexity"

**Seasonal Context:**
- January-May: Peak filing season, consultation scheduling
- June-July: Evidence preparation and case building
- August-October: ARB hearing season
- November-December: Resolution and follow-up

## Testing Requirements
- Verify all timeline references are realistic and accurate
- Test that customers understand the process duration
- Validate seasonal deadline communication is clear
- Check that no unrealistic promises remain

## Definition of Done
- All conversation flows contain accurate timeline information
- Customers receive proper expectations about process duration
- Seasonal deadlines are clearly communicated
- Business reduces complaints about service delivery timing