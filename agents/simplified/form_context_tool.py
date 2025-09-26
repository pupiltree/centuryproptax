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
        return f"""**CENTURY PROPERTY TAX PROFESSIONAL SERVICES INFORMATION**

**Customer Question:** {query}

**ABOUT OUR REGISTRATION PROCESS:**
We help Texas property owners navigate the complex property tax system. Our registration form connects you with licensed specialists who can review your specific situation and determine if professional representation makes sense for your property.

**WHAT HAPPENS WHEN YOU REGISTER:**
1. You provide basic contact information and property details
2. A licensed specialist reviews your property's assessment history
3. We analyze potential savings opportunities specific to your property
4. If we can help, we explain exactly what we'll do and how much it might save you
5. You decide if you want professional representation - no pressure

**OUR SERVICE IS RISK-FREE:**
You never pay anything upfront. We only earn a fee if we successfully reduce your property taxes. If we can't save you money, you owe us nothing.

**DETAILED CONTRACT TERMS EXPLANATION:**

**How Our Fee Structure Works:**
We only charge a contingency fee if we successfully reduce your property taxes:
• Residential properties: 35% of the annual tax savings we achieve
• Commercial properties: 20% of the annual tax savings we achieve
• Complex cases requiring court/arbitration: 50% of the tax savings
Example: If we save you $1,000 per year on your residential property, our fee would be $350, and you keep $650 in savings every year going forward.

**Contract Duration and Flexibility:**
• The agreement covers the current tax year when you sign
• It automatically continues each year UNLESS you cancel in writing before March 1st
• You have complete control - you can cancel any time before the March 1st deadline
• If you cancel after March 1st (after we've already started working on your case), there's a cancellation fee: $250 for residential, $1,500 for commercial properties

**Payment Terms:**
• You pay our fee within 30 days after we successfully reduce your taxes
• If payment is late, there's a 1.5% monthly late fee
• You only pay AFTER we demonstrate actual savings on your tax bill

**What We Can and Cannot Guarantee:**
• We cannot legally guarantee a specific outcome (no one can)
• However, we have extensive experience with Texas property tax appeals
• We're Texas licensed professionals (License #0001818) with a strong track record
• Our contingency fee structure means we're motivated to get you the best possible result

**Information We'll Need:**
To properly evaluate your property and build a strong case, we may need:
• Property closing statements or purchase documents
• Recent appraisals or valuations
• For commercial properties: rent rolls, income/expense statements
• All information is kept strictly confidential and used only for your property tax case

**What We Handle For You:**
• Complete review of your property's assessed value vs. market data
• Filing all necessary paperwork and appeals on your behalf
• Negotiating directly with county tax offices
• Representing you at assessment appeal board hearings
• If necessary, handling state-level appeals (SOAH) or court proceedings
• Ensuring your property is assessed fairly compared to similar properties

**THE REGISTRATION FORM:**
The form takes just a few minutes to complete:
• Page 1: Basic contact information (name, email, phone, address)
• Page 2: Properties you'd like us to review (just the addresses)
• Page 3: Digital agreement (type your name to sign)

**WHAT HAPPENS AFTER YOU REGISTER:**
1. You'll receive a confirmation email right away
2. Within 24 hours, a specialist will be assigned to review your properties
3. We'll analyze your property's assessment history and comparable sales
4. Your specialist will contact you to discuss findings and potential savings
5. If we can help, we'll explain exactly what we'll do and estimated timeline

**COMMON QUESTIONS ADDRESSED:**
"Is the fee worth it?" - You only pay if we save you money, and you keep the savings year after year.
"Can I handle this myself?" - You certainly can try, but property tax law is complex and time-consuming.
"What if you can't help?" - You pay nothing, and you're free to try other approaches.
"Is this a long commitment?" - You can cancel any time before March 1st each year.

**GETTING STARTED:**
If this sounds like it could help your situation, the next step is to complete the registration form at: https://forms.office.com/pages/responsepage.aspx?id=0t_vMiRx-Eayzz0urQPfCPwPYCS22DBNv5-YeXcrGC9UMUZRWkIxQU9RVzFBVVhURFhMUVJGV1VIMS4u&route=shorturl

This connects you with a specialist who can give you specific insights about your property's potential for tax savings."""

async def get_form_context_tool_async(query: str = "general information") -> str:
    """Async version of form context tool."""
    tool = FormContextTool()
    return tool._run(query)


# Export the tool for use in the assistant
form_context_tool = FormContextTool()