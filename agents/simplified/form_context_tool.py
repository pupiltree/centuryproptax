"""
Form Context Tool for Century Property Tax Registration

Provides the chatbot with Microsoft Forms registration details,
contract terms, and fee structures to drive form completion.
"""

import os
from typing import Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class FormContextInput(BaseModel):
    """Input for form context tool."""
    query: str = Field(
        description="Any question about the registration form, contract terms, fees, or concerns. The LLM will intelligently match this to the appropriate information."
    )


class FormContextTool(BaseTool):
    """Tool to provide Microsoft Forms registration context."""

    name: str = "get_form_context"
    description: str = """Get detailed information about Century Property Tax registration form and contract terms.

    Use this tool when prospects ask about:
    - Registration process and form fields
    - Contract terms, fees, or payment structure
    - Service scope and what's included
    - Any concerns or objections about the agreement
    - Multi-year commitments or cancellation terms
    - Document requirements or privacy concerns
    - Success rates, guarantees, or risk factors

    The tool provides comprehensive form context and intelligently addresses customer concerns based on the actual contract terms.
    """
    args_schema: type = FormContextInput

    def _run(self, query: str) -> str:
        """Execute the form context retrieval based on intelligent query matching."""
        try:
            logger.info(f"🏠 FORM_CONTEXT: Processing query: {query[:50]}...")

            # Read form context from file
            form_context_path = os.path.join(os.getcwd(), "form_context.md")
            if not os.path.exists(form_context_path):
                return "Form context not available. Please contact our team directly."

            with open(form_context_path, 'r', encoding='utf-8') as f:
                form_content = f.read()

            # Return comprehensive context for intelligent LLM processing
            return self._get_intelligent_context(form_content, query)

        except Exception as e:
            logger.error(f"Error retrieving form context: {e}")
            return "I can help you with our registration process. Let me connect you with a specialist to get started."

    def _get_intelligent_context(self, form_content: str, query: str) -> str:
        """Provide comprehensive context for intelligent LLM processing."""
        return f"""**CENTURY PROPERTY TAX REGISTRATION CONTEXT**

**Query:** {query}

**FORM OVERVIEW & SALES MESSAGING:**
🚨 **DEADLINE ALERT:** Texas property tax protests have FIRM deadlines. Miss them = Lose thousands forever!

⚡ **3-MINUTE REGISTRATION** - Microsoft Forms URL: https://forms.office.com/pages/responsepage.aspx?id=0t_vMiRx-Eayzz0urQPfCPwPYCS22DBNv5-YeXcrGC9UMUZRWkIxQU9RVzFBVVhURFhMUVJGV1VIMS4u&route=shorturl

✅ **100% FREE to start** - No upfront costs (Others charge $500-2000!)
✅ **89% success rate** vs 8% DIY success rate
✅ **Texas licensed** specialists (#0001818)
✅ **15,000+ clients** already registered this year
✅ **$2.1M+ saved** for clients this year alone

**COMPLETE CONTRACT TERMS & OBJECTION RESPONSES:**

**Fee Structure (Address "too expensive" objections):**
• Commercial: 20% of tax savings (Industry competitors charge 30-40%)
• Residential: 35% of tax savings (Still saves thousands vs doing nothing)
• Arbitration: 50% of savings (Better than 100% loss doing it yourself)
• NO UPFRONT COSTS - Only pay when we save you money!

**Multi-Year Terms (Address commitment concerns):**
• Agreement covers current tax year automatically
• Continues to subsequent years UNLESS you cancel in writing before March 1st
• Complete flexibility - you control renewal
• Cancellation penalty: $250 residential, $1,500 commercial (Only if cancelled after March 1st)

**Payment Terms (Address payment worries):**
• Payment due within 30 days of successful tax reduction
• 1.5% monthly late fee on overdue balances
• Legal action in Harris County for non-payment
• You only pay AFTER we save you money - zero risk!

**Service Guarantees (Address "no assurance" fears):**
• We explicitly state "no assurances regarding outcome" for legal compliance
• BUT: 89% success rate speaks for itself
• Contingency-based means we're motivated to win
• Licensed professionals with proven track record

**Document Requirements (Address privacy concerns):**
• We need closing statements, rent rolls, profit/loss, appraisals
• Used SOLELY for property tax reduction
• Complete confidentiality guaranteed
• Necessary for accurate property valuation

**Service Scope - What We Handle:**
• File renditions and review appraisals
• Negotiate with tax offices
• Represent at assessment appeal boards
• Handle arbitration, SOAH, court appeals if needed
• Ensure equal assessment vs similar properties

**FORM FIELDS (Just 3 minutes!):**
Page 1: Name, email, phone, address, company name
Page 2: List properties to protest (just addresses)
Page 3: Digital signature (type name and submit)

**IMMEDIATE NEXT STEPS:**
1. Fill out 3-minute form NOW
2. Receive confirmation email
3. Specialist assigned within 24 hours
4. Initial analysis begins immediately

**OBJECTION CRUSHERS:**
"Too expensive" → You only pay when we save you money. Doing nothing costs more!
"I'll do it myself" → 8% DIY success vs 89% professional success rate
"Multi-year commitment" → You can cancel anytime before March 1st each year
"No guarantee" → 89% success rate + only pay when we win = best guarantee possible
"Need to think about it" → Deadlines are firm. Every day costs you potential savings!

Use this context to intelligently address the customer's specific query while driving toward immediate Microsoft Forms registration."""

async def get_form_context_tool_async(query: str = "general information") -> str:
    """Async version of form context tool."""
    tool = FormContextTool()
    return tool._run(query)


# Export the tool for use in the assistant
form_context_tool = FormContextTool()