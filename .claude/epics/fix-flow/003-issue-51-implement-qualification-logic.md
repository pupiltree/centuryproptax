---
title: Implement Qualification Logic
epic: fix-flow
priority: high
estimate: 3 days
dependencies: [001]
---

# Implement Qualification Logic

## Description
Add proper lead qualification questions and viability assessment to the conversation flow. This ensures the chatbot can identify viable property tax protest cases and provide appropriate recommendations, improving conversion quality and resource allocation.

## Acceptance Criteria
- [ ] Current assessed value vs. market value questions implemented
- [ ] Recent purchase price and date collection added
- [ ] Current exemption status inquiry integrated
- [ ] Previous protest history assessment included
- [ ] Property improvements/changes evaluation added
- [ ] Viability scoring logic embedded in conversation prompts
- [ ] Appropriate service recommendations based on qualification results

## Technical Details
**Files to Modify:**
- `agents/core/property_tax_assistant_v3.py` - Add qualification questions to conversation flow
- Update system prompts with qualification logic
- Enhance few-shot examples with proper qualification sequences

**Qualification Questions to Add:**
1. "What's your current assessed value compared to what you think the property is worth?"
2. "When did you purchase the property and what was the purchase price?"
3. "What exemptions do you currently have (homestead, over-65, disability)?"
4. "Have you protested your property taxes before? What was the outcome?"
5. "Have you made any major improvements or changes to the property recently?"

**Viability Assessment Logic:**
- High viability: Large assessment increase + recent comparable sales data + no recent improvements
- Medium viability: Moderate increase + some supporting evidence + proper exemptions claimed
- Low viability: Small increase + limited evidence + recent improvements justify increase

## Testing Requirements
- Test qualification flow with various property scenarios
- Verify appropriate service recommendations for each viability level
- Validate that qualification doesn't elongate conversation unnecessarily
- Check that non-viable cases are handled appropriately

## Definition of Done
- Qualification questions naturally integrated into conversation flow
- Viability assessment accurately identifies protest potential
- Service recommendations match case complexity
- Business team confirms qualification improves lead quality