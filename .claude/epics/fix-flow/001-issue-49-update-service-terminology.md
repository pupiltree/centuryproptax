---
title: Update Service Terminology
epic: fix-flow
priority: high
estimate: 2 days
dependencies: none
---

# Update Service Terminology

## Description
Replace all "assessment" terminology with proper "protest/appeal" language throughout the property tax chatbot system. This foundational change aligns the chatbot with authentic Texas property tax consulting practices and forms the basis for all subsequent improvements.

## Acceptance Criteria
- [ ] All instances of "Property Tax Assessment Review" changed to "Property Tax Protest Representation"
- [ ] "Assessment" replaced with "protest" or "appeal" in conversation prompts
- [ ] Service offerings updated to use industry-standard terminology
- [ ] Conversation examples reflect proper protest language
- [ ] No remaining generic "assessment" language in user-facing content

## Technical Details
**Files to Modify:**
- `agents/core/property_tax_assistant_v3.py` - System prompts and conversation examples
- `agents/simplified/enhanced_workflow_tools.py` - Service definitions and descriptions
- `config/response_templates.py` - Response templates (if exists)

**Specific Changes:**
- Replace "Property Tax Assessment Review" → "Property Tax Protest Representation"
- Replace "assessment booking" → "protest consultation scheduling"
- Replace "assessment team" → "protest representative"
- Update few-shot examples to use protest terminology
- Modify service recommendations to mention "protest" and "appeal"

## Testing Requirements
- Verify all conversation flows use consistent protest terminology
- Test that no "assessment" language appears in responses
- Validate that service descriptions match industry standards
- Check that conversation examples reflect proper terminology

## Definition of Done
- Legal/business team approves updated terminology
- All automated tests pass with new language
- No assessment-related terminology remains in user-facing content
- Conversation flows sound authentic to property tax industry