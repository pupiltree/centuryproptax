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
        """Provide concise, conversational context."""
        # Map queries to short, conversational responses
        query_lower = query.lower()

        if any(word in query_lower for word in ['what', 'this', 'form', 'registration']):
            return "This is our property tax appeal registration form. It connects you with a licensed specialist who can review your property and potentially save you money on taxes. We only get paid if we successfully reduce your property taxes."

        elif any(word in query_lower for word in ['fee', 'cost', 'price', 'payment']):
            return "We work on contingency - you pay nothing upfront. Our fee is 35% of the tax savings we achieve for residential properties. If we can't save you money, you owe us nothing."

        elif any(word in query_lower for word in ['cancel', 'commitment', 'contract', 'understand', 'explain']):
            return """Here are the key contract points:
• **No upfront costs** - You pay nothing until we save you money
• **35% fee** for residential properties (only if we succeed)
• **Cancel anytime** before March 1st each year with no penalty
• **Auto-renewal** unless you cancel in writing by March 1st
• **Risk-free** - If we can't help, you owe us nothing"""

        elif any(word in query_lower for word in ['process', 'how', 'work']):
            return "Simple 3-step process: 1) Fill out the form with your property details, 2) A specialist reviews your case within 24 hours, 3) If we can help, we handle everything and you pay only after we save you money."

        elif any(word in query_lower for word in ['guarantee', 'success', 'results']):
            return "We can't guarantee specific results, but we're Texas licensed professionals with a strong track record. Since we only get paid when you save money, we're motivated to get the best outcome."

        else:
            return "We help Texas property owners appeal high property taxes. Our licensed specialists work on contingency - you only pay if we save you money. [Get started here](https://forms.office.com/pages/responsepage.aspx?id=0t_vMiRx-Eayzz0urQPfCPwPYCS22DBNv5-YeXcrGC9UMUZRWkIxQU9RVzFBVVhURFhMUVJGV1VIMS4u&route=shorturl)"

async def get_form_context_tool_async(query: str = "general information") -> str:
    """Async version of form context tool."""
    tool = FormContextTool()
    return tool._run(query)


# Export the tool for use in the assistant
form_context_tool = FormContextTool()