---
title: Add TDLR Compliance
epic: fix-flow
priority: high
estimate: 1 day
dependencies: [001]
---

# Add TDLR Compliance

## Description
Integrate Texas Department of Licensing and Regulation (TDLR) compliance requirements into the chatbot conversation flows. This ensures legal compliance for property tax consulting services and protects the business from regulatory violations.

## Acceptance Criteria
- [ ] TDLR registration disclosure added to initial conversations
- [ ] Scope of representation clearly defined and communicated
- [ ] Legal advice limitations properly disclaimed
- [ ] Texas Tax Code references included where appropriate
- [ ] All required regulatory disclaimers integrated naturally into conversation flow

## Technical Details
**Files to Modify:**
- `agents/core/property_tax_assistant_v3.py` - Add compliance disclaimers to system prompts
- Add legal disclaimers to conversation templates
- Update service descriptions with scope limitations

**Specific Changes:**
- Add TDLR registration disclosure: "Century Property Tax is registered with the Texas Department of Licensing and Regulation"
- Include scope disclaimer: "We provide property tax protest representation. For complex legal matters, additional attorney consultation may be recommended"
- Add limitations: "This consultation provides professional guidance on your property tax situation under Texas Tax Code"
- Reference relevant Texas Tax Code sections in explanations

## Testing Requirements
- Verify disclaimers appear in appropriate conversation contexts
- Test that legal language is clear and understandable
- Validate compliance with TDLR requirements
- Ensure disclaimers don't disrupt conversation flow

## Definition of Done
- Legal team confirms TDLR compliance requirements are met
- All required disclaimers appear in natural conversation contexts
- No regulatory gaps remain in service descriptions
- Business risk from compliance violations eliminated