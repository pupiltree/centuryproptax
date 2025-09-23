"""
Property Tax Assistant v3 - Workflow-Compliant LangGraph Implementation
Following the exact workflow adapted for property tax consultations
and TRUE LangGraph patterns from https://langchain-ai.github.io/langgraph/tutorials/customer-support/customer-support/

This implementation maps directly to workflow nodes:
F - Collect PIN, date, assessment type
G - Explain assessment prep, duration, pricing
H - Lookup recent assessment or report
I - Create ticket via /tickets
J - Handover to agent via /handover
K - Suggest advanced assessment services
O - Mark consultation as confirmed (Cash)
Q - Create consultation order via /orders
T - Create Razorpay link via /payments/link
"""

from typing import Annotated, Any, Dict
from typing_extensions import TypedDict
import structlog
from datetime import datetime

from langchain_core.messages import AnyMessage, ToolMessage, AIMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, add_messages
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import InMemorySaver
from services.persistence.redis_conversation_store import get_conversation_store
from langchain_core.prompts import ChatPromptTemplate

# Import new AI configuration and guardrails
from config.ai_configuration import get_ai_config, PropertyTaxDomain
from agents.core.guardrails import get_guardrails, apply_guardrails
from config.response_templates import get_template, PropertyTaxScenario, detect_language_from_message
from src.core.logging import get_logger

logger = get_logger("property_tax_assistant")

# Import workflow-compliant tools
from agents.simplified.enhanced_workflow_tools import (
    # F: Book Assessment - Collect PIN, date, assessment type
    validate_pin_code,

    # G: Assessment Enquiry - Explain assessment prep, duration, pricing
    # (We'll use RAG system for this)

    # H: Lookup recent assessment or report
    check_report_status,
    
    # I: Create ticket via /tickets
    # (We'll use complaint handling)
    
    # J: Handover to agent via /handover
    # (We'll use escalation)
    
    
    # O: Mark order as confirmed (Cash)
    confirm_order_cash_payment,
    
    # Q: Create order via /orders
    create_order,
    
    # T: Create Razorpay link via /payments/link
    create_payment_link,
    
    # Additional workflow support tools
    verify_customer_payment
    # REMOVED: get_payment_options - LLM handles payment options naturally
)

# Import Unified Property Tax RAG system for intelligent assessment enquiries (workflow node G)
from agents.simplified.property_tax_rag_tool import property_tax_rag_tool
from langchain_core.tools import tool

# Import ticket management for complaints (workflow node I)  
from agents.simplified.ticket_tools import create_support_ticket

# Import property document analysis tools
from agents.simplified.property_document_tools import (
    analyze_property_document_tool,
    confirm_property_assessment_booking
    # REMOVED: format_document_summary - LLM handles formatting naturally
)

# Escalation tool for human handover (moved from generic assistant)
@tool
def escalate_to_human_agent(reason: str, customer_info: str = None) -> str:
    """
    Escalate conversation to a human agent.
    
    Args:
        reason: Reason for escalation (complex query, complaint, etc.)
        customer_info: Customer information for context
        
    Returns:
        Escalation confirmation and next steps
    """
    try:
        escalation_id = f"ESC_{int(datetime.now().timestamp())}"
        
        return f"""👨‍💼 Connecting you to a property tax specialist...
Escalation ID: {escalation_id}
Reason: {reason}
{f'Customer Info: {customer_info}' if customer_info else ''}
A property tax specialist will be with you shortly to provide personalized assistance. Please hold on while I transfer your conversation.
Average wait time: 2-3 minutes"""
        
    except Exception as e:
        logger.error(
            "Error escalating to human agent",
            log_event="escalation_error",
            error_type=type(e).__name__,
            error_message=str(e)
        )
        return "I'm arranging for a specialist to help you. Please give me a moment to connect you with the right person."


# Custom tool node that automatically injects Instagram ID
class PropertyTaxToolNode:
    """Custom tool node that automatically injects Instagram ID from config."""
    
    def __init__(self, tools):
        self.tools = {tool.name: tool for tool in tools}
    
    def __call__(self, state: "PropertyTaxState", config: RunnableConfig):
        """Execute tools with automatic Instagram ID injection."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # Get Instagram ID from config (same as customer_id)
        instagram_id = config.get("configurable", {}).get("customer_id")
        
        tool_calls = last_message.tool_calls if hasattr(last_message, 'tool_calls') else []
        
        if not tool_calls:
            return {"messages": []}
        
        tool_messages = []
        
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"].copy()
            
            # Automatically inject instagram_id for tools that need it
            if tool_name in ["create_order", "confirm_order_cash_payment", "create_support_ticket"]:
                if instagram_id and "instagram_id" not in tool_args:
                    tool_args["instagram_id"] = instagram_id
            
            try:
                tool = self.tools[tool_name]
                result = tool.invoke(tool_args, config)
                
                tool_messages.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"],
                        name=tool_name
                    )
                )
                
            except Exception as e:
                logger.error(
                    "Tool execution error",
                    log_event="tool_error",
                    tool_name=tool_name,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                tool_messages.append(
                    ToolMessage(
                        content=f"Tool execution failed: {str(e)}",
                        tool_call_id=tool_call["id"],
                        name=tool_name
                    )
                )
        
        return {"messages": tool_messages}


# Workflow nodes K & G: Assessment recommendations now handled by Agentic RAG system
# - agentic_property_tax_rag_recommendation for intelligent property tax recommendations
# - agentic_conversation_explorer for unclear requests


# Simple conversation state following LangGraph tutorial patterns
class PropertyTaxState(TypedDict):
    """Property tax conversation state focused on workflow compliance."""
    messages: Annotated[list[AnyMessage], add_messages]


# Workflow-compliant property tax assistant following LangGraph tutorial patterns
class WorkflowAssistant:
    """
    Property tax assistant that follows the exact workflow adapted for property tax consultations.
    Uses TRUE LangGraph patterns with simple 2-node graph and dynamic tool selection.
    """
    
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: PropertyTaxState, config: RunnableConfig):
        """Main assistant logic following customer support tutorial pattern."""
        while True:
            try:
                # Get customer_id from config for prompt formatting
                customer_id = config.get("configurable", {}).get("customer_id", "unknown")
                
                # Create input with prompt variables
                input_data = {
                    "messages": state["messages"],
                    "customer_id": customer_id
                }
                
                # Add detailed logging before LLM call
                last_message = state["messages"][-1] if state["messages"] else None
                logger.info("🔍 LLM INPUT DEBUG", 
                           customer_id=customer_id,
                           message_count=len(state["messages"]),
                           last_message_type=type(last_message).__name__ if last_message else None,
                           last_message_content=last_message.content if hasattr(last_message, 'content') else str(last_message)[:100])
                
                # Invoke the LLM with formatted input
                result = self.runnable.invoke(input_data, config)
                
                # Enhanced logging for LLM output
                logger.info("🔍 LLM OUTPUT DEBUG",
                           has_tool_calls=bool(result.tool_calls),
                           tool_count=len(result.tool_calls) if result.tool_calls else 0,
                           tool_names=[tc["name"] for tc in result.tool_calls] if result.tool_calls else [],
                           response_content=result.content[:200] if result.content else "No content")
                
                if result.tool_calls:
                    for i, tc in enumerate(result.tool_calls):
                        logger.info(f"🔧 TOOL_CALL_{i+1} DEBUG",
                                   tool_name=tc["name"],
                                   tool_args=tc["args"])
                
                # Ensure proper responses
                if not result.tool_calls and (not result.content or len(result.content.strip()) < 10):
                    # Re-prompt for better response
                    messages = state["messages"] + [("user", "Please provide a helpful response about our property tax services.")]
                    state = {**state, "messages": messages}
                    continue
                else:
                    break
                    
            except Exception as e:
                logger.error(f"Error in property tax assistant: {e}")
                # Fallback response
                from langchain_core.messages import AIMessage
                result = AIMessage(content="I'm here to help you with our property tax services. How can I assist you today?")
                break
        
        return {"messages": [result]}


def create_property_tax_assistant():
    """Create workflow-compliant property tax assistant following TRUE LangGraph patterns."""
    import os
    
    # Initialize LLM for text processing (Gemini-2.5-Flash for efficient text conversations)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3,  # Lower temperature for more focused responses
    )
    
    # Note: Property document analysis uses Gemini-2.5-Pro via the property_document_tools
    # This is handled automatically by the analyze_property_document_tool

    # Workflow-compliant tools mapped to workflow diagram nodes
    property_tax_tools = [
        # F: Book Assessment workflow - PIN validation
        validate_pin_code,

        # G: Assessment Enquiry workflow - Using Unified Property Tax RAG for intelligent recommendations
        property_tax_rag_tool,
        
        
        # H: Report Retrieval workflow
        check_report_status,
        
        # I: File Complaint workflow  
        create_support_ticket,
        
        # J: Human Handover workflow
        escalate_to_human_agent,
        
        
        # O: Cash Payment Confirmation workflow
        confirm_order_cash_payment,
        
        # Q: Create Order workflow
        create_order,
        
        # T: Online Payment workflow
        create_payment_link,
        
        # Additional workflow support
        verify_customer_payment,
        # REMOVED: get_payment_options - LLM handles payment options naturally

        # Property document analysis workflow
        analyze_property_document_tool,
        confirm_property_assessment_booking
        # REMOVED: format_document_summary - LLM handles formatting naturally
    ]
    
    # Enhanced property tax assistant prompt with Texas domain expertise
    property_tax_prompt = """You are a friendly multilingual property tax assistant at Century Property Tax specializing in Texas property tax law and procedures. Communicate efficiently while being personal and caring.

CRITICAL RESPONSE RULES:
- Maximum 40 words per response - ULTRA BRIEF and COMPLETE sentences only
- One clear question or statement - NO multiple concepts
- Direct actionable requests only - NO explanations or context
- Use simple language - NO complex technical terms unless essential
- End sentences properly - NEVER cut off mid-sentence
- Ask ONE specific question at a time - NO lists or options

PROPERTY TAX DOMAIN EXPERTISE:
- Texas Property Tax Code (Title 1, Subtitle E) knowledge and application
- County appraisal district procedures and timelines
- Property valuation methods (cost, market, income approaches)
- Exemption programs: Homestead ($40,000 minimum), Senior (65+), Disability, Veteran
- Appeal process: Informal review → ARB hearing → District court → State appeals
- Tax year calendar: Jan 1 assessment → May notices → July protests → Jan 31 payment
- Common property types: Residential, Commercial, Agricultural, Industrial
- Market value vs. assessed value distinctions

LEGAL BOUNDARIES & DISCLAIMERS:
- ✅ PROVIDE: General information about Texas property tax procedures and timelines
- ✅ EXPLAIN: How exemptions work and basic qualification criteria
- ✅ GUIDE: Assessment appeal process steps and required documentation
- ✅ CLARIFY: Difference between market value and assessed value
- ❌ NEVER: Give specific legal advice or guarantee appeal outcomes
- ❌ AVOID: Interpreting complex legal statutes without professional review
- ❌ CANNOT: Provide official tax calculations or represent clients in legal proceedings
- 🔄 REFER: Complex legal questions to licensed property tax consultants or attorneys

PERSONALITY & TONE:
- Talk like a knowledgeable property tax professional, not a robot
- Be warm, empathetic, and conversational about taxpayer concerns
- GROUP related questions together to reduce conversation length
- Show genuine understanding of property tax stress and financial impact
- Use natural language and avoid technical jargon without explanation

MULTILINGUAL SUPPORT:
- Respond in the language the customer uses (English, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi)
- If unsure about language, ask: "Which language would you prefer - English या Hindi?"
- Use simple, clear language regardless of the language chosen
- Maintain professional property tax terminology consistency across all languages
- Provide cultural sensitivity when discussing property ownership and financial concerns

EFFICIENT CONVERSATION FLOW:
1. **Property Document Analysis**: When customers share property documents, use Gemini-2.5-Pro for analysis
   - IMMEDIATELY call analyze_property_document_tool with the document data
   - Review extracted information (property owner name, address, property type, assessment details)
   - Use property_tax_rag_tool for intelligent assessment recommendations with Google embeddings + LLM reasoning
   - Present findings naturally in a clear, professional format (owner info, property details, assessment type, date)
   - Always ask: "Is this information correct before we proceed with booking?"
   - If information is incomplete, ask for missing details conversationally
   - ALWAYS confirm before creating order: "Should I book these assessments with the details I found?"
   
**PROPERTY DOCUMENT BOOKING CONTEXT**: When property document information is available from previous analysis:
   - Use the provided property details (owner name, address, property type, assessments) naturally in conversation
   - Don't ask for information that's already available from the document
   - Only ask for missing booking details: phone, PIN code, date, payment method, service preference
   - Be contextually aware: "I see from your document that you need [assessment types] for [property address]. Let me help you book these assessments."
   
2. **Property Tax Enquiry**: When customers mention property tax concerns, gather key info together INCLUDING PROPERTY TYPE
   - "I understand you have questions about [property tax issue]. To provide the most accurate guidance under Texas property tax law, could you tell me your property type, county location, and what specific concerns you have about your assessment?"
   - MUST collect: property type, county location, AND specific concern (high assessment, missing exemption, appeal deadline, etc.)
   - THEN call property_tax_rag_tool with their property details for intelligent property tax recommendations
   - For unclear requests like "I need property assessment", ask intelligent clarifying questions about their specific property tax situation
   - Always acknowledge the complexity: "Property tax situations can be complex, so let me make sure I understand your specific concerns."
   
3. **Assessment Recommendations**: Present options with service preference
   - "Based on your property details, I'd recommend our [Assessment Package]. Would you like to book this assessment?"
   - "We offer two convenient options: property visit for inspection or office consultation. Which would you prefer?"

4. **Booking Process**: Collect details in manageable groups with property tax context
   - Start with: "Perfect! Let's book this property tax assessment for you. Can I get your full name and phone number?"
   - Next ask: "What's your property PIN code and preferred date (you can say 'tomorrow', 'next Friday', 'September 7th', etc.)?"
   - Then ask payment preference naturally: "How would you like to pay?"
     • **Pay Online** (Recommended): Secure payment via UPI, Cards, Net Banking - instant confirmation
     • **Cash on Visit**: Pay when our assessor arrives (property visit only)
   - Ask service preference: "Would you prefer property visit for detailed inspection or office consultation to review your documents?"
   - **FOR PROPERTY VISIT ONLY**: "For property inspection, I need your complete property address with house/flat number, building name, street, landmark, and area details."
   - **LEGAL DISCLAIMER**: Include appropriate disclaimers: "This assessment will provide professional guidance on your property tax situation, but for complex legal matters, we may recommend additional consultation with a property tax attorney."
   - VALIDATE all information before proceeding

5. **Information Validation**: Check completeness before booking
   - IF missing property type: "I also need to know your property type for accurate assessment recommendations"
   - IF missing phone: "I need your phone number to coordinate the appointment"
   - IF missing date: "When would you like to schedule this? You can say 'tomorrow', 'next Monday', or any date that works for you"
   - IF missing payment/service: "How would you like to pay, and do you prefer property visit for inspection or office consultation?"
   - IF property visit chosen but missing address: "For property inspection, I need your complete property address including house/flat number, building name, street, and any nearby landmark."

6. **Order Creation**: Only after ALL information is complete
   - Before calling create_order, ensure you have collected all necessary information naturally through conversation
   - For property visit: Ask for address in a conversational way before booking
   - For office consultation: Property address not required
   - Call create_order with ALL collected details including service_type parameter
   - If create_order fails due to missing information, ask for the missing details naturally
   - IMMEDIATELY after successful order creation, handle payment:
     * If online payment chosen → CALL create_payment_link
     * If cash payment chosen → CALL confirm_order_cash_payment

7. **Payment Processing**: MANDATORY after order creation
   - For online: "Creating your payment link now..." then CALL create_payment_link
   - For cash: "Confirming your cash payment booking..." then CALL confirm_order_cash_payment

USER EXPERIENCE RULES:
- NEVER mention technical backend codes (like PROP_TAX_001, VAL_ASSESS) to customers
- Always use friendly names: "Property Tax Assessment Review", "Exemption Analysis", "Appeal Preparation Consultation"
- Use Texas-specific terminology: "County Appraisal District", "Appraisal Review Board (ARB)", "Homestead Exemption"
- **MANDATORY**: For property visit, ALWAYS ask for complete address before creating order
- If booking fails, don't expose technical details - offer to retry or escalate to specialist
- Keep responses conversational and friendly, not robotic
- Always include appropriate disclaimers about service limitations and legal advice boundaries

EFFICIENCY RULES:
- Group 2-4 related questions together instead of asking one by one
- Essential groupings:
  * Personal info: Name + Phone + Location together
  * Property details: Property type + location + recent assessments together
  * Service preferences: Payment method + service type together
- Only separate questions if they depend on previous answers

TECHNICAL INSTRUCTIONS:
- Customer ID: {customer_id} (use for instagram_id parameter)

REQUIRED INFORMATION CHECKLIST:
✓ Property type (for assessment recommendations)
✓ Property location (MANDATORY for accurate assessment suggestions)
✓ Full name (for booking)
✓ Phone number (for coordination)
✓ PIN code (for serviceability)
✓ Preferred date (YYYY-MM-DD format)
✓ Payment preference (online/cash)
✓ Service type (property visit/office consultation)
✓ **Complete property address (MANDATORY for property visit): House/Flat number, Building name, Street, Landmark, Area**

TOOL CALLING SEQUENCE:
1. **Property Document Received** → analyze_property_document_tool → format results naturally → confirm_property_assessment_booking
2. **Property tax concerns/questions** → Ask property type + location + assessment history → property_tax_rag_tool (intelligent Property Tax RAG with decision-making workflow)
3. **Unclear requests** ("I need assessment", "property tax help") → Ask clarifying questions about property tax concerns and needs
4. PIN code provided → validate_pin_code
5. Ready to book → create_order (with service_type parameter)
6. Order created successfully → IMMEDIATELY call payment tool:
   - Online payment: create_payment_link
   - Cash payment: confirm_order_cash_payment

CRITICAL: Never say "creating payment link" without actually calling the create_payment_link tool. Always follow order creation with immediate payment processing.

MULTILINGUAL EXAMPLES:

**English**: "I understand you have questions about property tax. To provide the best guidance under Texas property tax law, could you tell me your property type, county, and what specific concerns you have about your assessment?"

**Hindi**: "मैं समझ सकता हूं कि आपको संपत्ति कर की चिंता है। टेक्सास संपत्ति कर कानून के तहत सबसे अच्छी सलाह देने के लिए, क्या आप अपनी संपत्ति का प्रकार, काउंटी और अपने मूल्यांकन के बारे में विशिष्ट चिंताओं के बारे में बता सकते हैं?"

**Bengali**: "আমি বুঝতে পারছি আপনার সম্পত্তি কর নিয়ে প্রশ্ন আছে। টেক্সাস সম্পত্তি কর আইনের অধীনে সেরা পরামর্শ দিতে, আপনি কি আপনার সম্পত্তির ধরন, কাউন্টি এবং আপনার মূল্যায়ন সম্পর্কে নির্দিষ্ট উদ্বেগের কথা বলতে পারেন?"

FEW-SHOT CONVERSATION EXAMPLES:

**Example 1: Property Tax Assessment Inquiry**
User: "I think my property tax is too high"
Assistant: "I understand your concern about high property taxes - this is very common. To provide the best guidance under Texas property tax law, could you tell me your property type (residential/commercial), county location, and what makes you feel the assessment is too high?"

User: "It's a residential property in Harris County, they increased it by 30% this year"
Assistant: "A 30% increase is definitely significant and worth reviewing. Based on your Harris County residential property, I'd recommend our Property Tax Assessment Review to analyze your valuation and identify potential grounds for appeal. Would you like to book this assessment? We offer property visit for detailed inspection or office consultation to review your documents."

**Example 2: Homestead Exemption Question**
User: "Do I qualify for homestead exemption?"
Assistant: "Great question! In Texas, you may qualify for homestead exemption if this is your primary residence. To check your eligibility and current exemption status, could you tell me your property type, county, and whether you currently live in the property as your main home?"

User: "Yes it's my main home in Dallas County, single family house"
Assistant: "Perfect! As a Dallas County homeowner using the property as your primary residence, you should qualify for homestead exemption (minimum $40,000 reduction). I'd recommend our Exemption Analysis to review your current exemptions and ensure you're getting all benefits available. Would you like to book this assessment?"

**Example 3: Property Appeal Process**
User: "How do I appeal my property tax?"
Assistant: "I can help guide you through the Texas appeal process. To provide specific guidance, could you tell me your property type, county, and what concerns you have about your current assessment?"

User: "Commercial property in Collin County, assessment seems way too high compared to similar properties"
Assistant: "For commercial properties in Collin County, you have specific appeal rights. The process is: informal review → ARB hearing → district court if needed. I'd recommend our Appeal Preparation Consultation to analyze comparable properties and prepare your case. This assessment includes professional guidance, but for complex legal strategies, we may recommend a property tax attorney. Would you like to book this consultation?"

**Example 4: Complete Booking Flow**
User: "I need help with my property tax assessment"
Assistant: "I'd be happy to help with your property tax concerns. To provide the most accurate recommendations under Texas property tax law, could you tell me your property type, county location, and what specific concerns you have about your assessment?"

User: "Residential property in Austin, Travis County. Got a notice saying value went up a lot"
Assistant: "Significant value increases are definitely worth reviewing. Based on your Travis County residential property, I'd recommend our Property Tax Assessment Review. Would you like to book this assessment? We offer property visit for detailed inspection or office consultation to review your documents."

User: "Property visit sounds good"
Assistant: "Perfect! Let's book this property tax assessment for you. Can I get your full name and phone number?"

User: "John Smith, 512-555-0123"
Assistant: "Thank you, John. What's your property PIN code and preferred date? You can say 'tomorrow', 'next Friday', or any date that works for you."

User: "ZIP is 78701, can we do it this Friday?"
Assistant: "Excellent! How would you like to pay? We offer secure online payment (UPI, cards, net banking) for instant confirmation, or cash payment when our assessor arrives."

User: "Cash on visit works for me"
Assistant: "Perfect! For property inspection, I need your complete property address with house number, street, and any landmark to help our assessor locate you."

User: "123 Main Street, Apartment 4B, near Central Market downtown"
Assistant: "Got it! Let me create your booking now..."
[Tool: create_order]
"Excellent! Your property tax assessment is booked for Friday. Confirming your cash payment..."
[Tool: confirm_order_cash_payment]
"✅ All set! Your assessment is confirmed for Friday. Our certified property tax specialist will visit 123 Main Street, Apt 4B at your scheduled time. This professional assessment will help you understand your property tax situation, but for complex legal matters involving appeals, we may recommend consultation with a property tax attorney."

**Example 5: Multilingual Support (Hindi)**
User: "मुझे अपनी property tax के बारे में help चाहिए"
Assistant: "मैं आपकी संपत्ति कर की समस्या में मदद कर सकता हूं। टेक्सास संपत्ति कर कानून के तहत सबसे अच्छी सलाह देने के लिए, क्या आप बता सकते हैं कि आपकी संपत्ति का प्रकार क्या है, कौन सी काउंटी में है, और आपकी मुख्य चिंता क्या है?"

User: "Residential house है Tarrant County में, tax बहुत ज्यादा लग रहा है"
Assistant: "यह बहुत common concern है। आपकी Tarrant County residential property के लिए, मैं Property Tax Assessment Review suggest करूंगा। क्या आप यह assessment book करना चाहेंगे? हम property visit (detailed inspection) या office consultation (documents review) दोनों offer करते हैं।"

SERVICE OPTIONS (All Languages):
- "Property tax assessment" = संपत्ति कर मूल्यांकन / সম্পত্তি কর মূল্যায়ন / சொத்து வரி மதிப்பீடு
- "Property visit" = संपत्ति का दौरा / সম্পত্তি পরিদর্শন / சொத்து வருகை
- "Office consultation" = कार्यालय परामर्श / অফিস পরামর্শ / அலுவலக ஆலோசனை

CRITICAL REMINDERS:
- Be conversational but efficient with property tax expertise
- Group questions to reduce back-and-forth while maintaining accuracy
- Always offer both property visit and office consultation options
- Support multiple languages naturally with consistent terminology
- Include legal disclaimers when discussing complex property tax matters
- Always clarify that you provide guidance, not legal advice
- Refer complex legal questions to licensed professionals
- Acknowledge the stress and financial impact of property tax issues with empathy

DISCLAIMER TEMPLATES:
- For assessments: "This professional assessment will help you understand your property tax situation, but for complex legal matters involving appeals or disputes, we may recommend consultation with a property tax attorney."
- For appeals: "I can guide you through the general appeal process, but specific legal strategies should be discussed with a qualified property tax consultant or attorney."
- For calculations: "These are estimates based on general Texas property tax procedures. Official calculations should be verified with your county appraisal district."
"""
    
    # Create assistant runnable with property tax system prompt
    property_tax_system_prompt = ChatPromptTemplate.from_messages([
        ("system", property_tax_prompt),
        ("placeholder", "{messages}")
    ])

    assistant_runnable = property_tax_system_prompt | llm.bind_tools(property_tax_tools)
    
    # Simple 2-node graph pattern following tutorial
    builder = StateGraph(PropertyTaxState)

    # Add nodes
    builder.add_node("assistant", WorkflowAssistant(assistant_runnable))
    builder.add_node("tools", ToolNode(property_tax_tools))
    
    # Simple edges - let LLM decide tool usage dynamically
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant", 
        tools_condition
    )
    builder.add_edge("tools", "assistant")
    
    # Use InMemorySaver for LangGraph (simple and reliable)
    # Conversation persistence is handled separately with Redis
    logger.info("📝 Using InMemorySaver for LangGraph with separate Redis conversation persistence")
    checkpointer = InMemorySaver()

    return builder.compile(checkpointer=checkpointer)


# Global property tax assistant instance
_global_property_tax_assistant = None

def get_property_tax_assistant():
    """Get or create the global workflow-compliant property tax assistant instance."""
    global _global_property_tax_assistant
    if _global_property_tax_assistant is None:
        _global_property_tax_assistant = create_property_tax_assistant()
        logger.info("🏢 Created workflow-compliant property tax assistant following TRUE LangGraph patterns")
    return _global_property_tax_assistant

def reset_property_tax_assistant():
    """Reset the global assistant instance - useful for testing or configuration changes."""
    global _global_property_tax_assistant
    _global_property_tax_assistant = None
    logger.info("🔄 Property tax assistant instance reset")


async def process_property_tax_message(message: str, session_id: str, customer_id: str) -> Dict[str, Any]:
    """
    Process property tax message with Redis conversation persistence.
    Maps to workflow nodes: F, G, H, I, J, K, O, Q, T
    """
    # Get assistant instance and conversation store
    assistant = get_property_tax_assistant()
    
    # Get Redis conversation store
    try:
        conv_store = get_conversation_store()
        redis_available = conv_store.health_check()
    except Exception as e:
        logger.warning(f"Redis conversation store unavailable: {e}")
        redis_available = False
    
    # Configuration for conversation thread - CRITICAL: use proper thread_id format
    config = {
        "configurable": {
            "thread_id": f"conversation-{session_id}",  # Ensure unique thread ID
            "customer_id": customer_id
        }
    }
    
    try:
        # Input validation
        if not message or not message.strip():
            return {
                "text": "I didn't receive your message clearly. How can I help you with our property tax services?",
                "session_id": session_id,
                "error": "empty_message"
            }
        
        # Load conversation history from Redis for context
        conversation_context = {}
        if redis_available:
            try:
                conversation_history = conv_store.get_conversation_history(session_id, limit=10)
                conversation_context = conv_store.get_context(session_id)
                
                if conversation_history:
                    logger.info(f"📜 Loaded {len(conversation_history)} messages from Redis for session {session_id}")
                
                # Check for pending property document confirmation
                document_context = conversation_context.get("document_analysis") if conversation_context else None
                if document_context and document_context.get("awaiting_confirmation"):
                    logger.info(f"📋 Found pending property document confirmation for session {session_id}")

                    # Check if this is a confirmation response
                    message_lower = message.lower().strip()
                    if message_lower in ['yes', 'y', 'confirm', 'correct', 'book', 'proceed']:
                        logger.info(f"✅ User confirmed property assessment booking: '{message}'")

                        # Process property document booking confirmation
                        return await _handle_property_document_confirmation(
                            document_context=document_context,
                            session_id=session_id,
                            customer_id=customer_id,
                            conv_store=conv_store
                        )
                    elif message_lower in ['no', 'n', 'wrong', 'incorrect', 'change']:
                        logger.info(f"❌ User rejected property document: '{message}'")

                        # Clear document context and ask for manual input
                        conversation_context.pop("document_analysis", None)
                        conv_store.save_context(session_id, conversation_context)

                        return {
                            "text": "I understand the property document information wasn't correct. Please tell me which assessments you'd like to book and any property details I should know.",
                            "session_id": session_id,
                            "customer_message": message
                        }
                
                # Save the incoming user message to Redis
                conv_store.save_message(
                    session_id=session_id,
                    role="user", 
                    content=message,
                    metadata={"customer_id": customer_id, "timestamp": str(datetime.now())}
                )
            except Exception as redis_error:
                logger.warning(f"Redis conversation loading failed: {redis_error}")
                conversation_history = []
        
        # Check for active property document booking context
        document_booking_context = None
        if conversation_context and "document_booking" in conversation_context:
            document_booking_context = conversation_context["document_booking"]
            if document_booking_context.get("confirmed") and document_booking_context.get("awaiting_details"):
                logger.info(f"📋 Found active property document booking context for session {session_id}")

                # Enhance the message with property document context for LLM
                document_data = document_booking_context
                enhanced_message = f"""{message}

[CONTEXT: User has confirmed property assessment booking for: {', '.join(document_data.get('assessments', []))}]
[PROPERTY OWNER: {document_data.get('owner_name', 'Unknown')} (Property Type: {document_data.get('property_type', 'Not provided')}, Location: {document_data.get('location', 'Not provided')})]
[ASSESSOR: {document_data.get('assessor_name', 'Not provided')}]
[DOCUMENT DATE: {document_data.get('document_date', 'Not provided')}]

Please process this information naturally and only ask for missing booking details needed to complete the order. Don't ask for information that's already available in the context above."""

                message = enhanced_message
                logger.info(f"🔍 Enhanced message with property document context for better LLM understanding")
        
        # CRITICAL FIX: Use stream() instead of invoke() for better conversation handling
        from langchain_core.messages import HumanMessage
        
        # Stream the conversation - this properly handles checkpointer state
        try:
            events = list(assistant.stream(
                {"messages": [HumanMessage(content=message)]}, 
                config=config,
                stream_mode="values"  # Get the full state at each step
            ))
        except Exception as stream_error:
            logger.error(f"Stream error details: {type(stream_error).__name__}: {str(stream_error)}")
            # Try invoke() as fallback
            try:
                result = assistant.invoke(
                    {"messages": [HumanMessage(content=message)]},
                    config=config
                )
                events = [result]
            except Exception as invoke_error:
                logger.error(f"Both stream and invoke failed:")
                logger.error(f"  - Invoke error: {type(invoke_error).__name__}: {str(invoke_error)}")
                logger.error(f"  - Stream error: {type(stream_error).__name__}: {str(stream_error)}")
                events = []
        
        # Extract the final response from the stream
        if events:
            final_state = events[-1]
            messages = final_state.get("messages", [])
            
            if messages:
                # Get the last AI message  
                from langchain_core.messages import HumanMessage as HM
                for msg in reversed(messages):
                    if hasattr(msg, 'content') and msg.content and not isinstance(msg, HM):
                        response_text = msg.content
                        break
                else:
                    # More contextual fallback based on message content
                    if any(word in message.lower() for word in ['thanks', 'thank', 'ok', 'okay']):
                        response_text = "You're welcome! Is there anything else I can help you with regarding our property tax services?"
                    elif any(word in message.lower() for word in ['hi', 'hello', 'hey']):
                        response_text = f"Hello! I'm here to help you with Century Property Tax services. Are you looking for any specific property assessments?"
                    else:
                        response_text = "I understand you're reaching out. Could you please tell me how I can help you with our property tax services today?"
            else:
                response_text = "I'm ready to assist you with our property tax services. How can I help you today?"
        else:
            response_text = "I apologize for the technical issue. Please let me know what property tax services you need assistance with."
        
        logger.info(
            "Property tax message processed successfully",
            session_id=session_id,
            thread_id=config["configurable"]["thread_id"],
            message_length=len(message),
            response_length=len(response_text),
            events_count=len(events)
        )
        
        # Save assistant response to Redis for conversation continuity
        if redis_available:
            try:
                conv_store.save_message(
                    session_id=session_id,
                    role="assistant",
                    content=response_text,
                    metadata={"customer_id": customer_id, "timestamp": str(datetime.now())}
                )
                
                # Update conversation context with current state
                updated_context = {
                    **conversation_context,
                    "last_interaction": str(datetime.now()),
                    "message_count": conversation_context.get("message_count", 0) + 2,  # user + assistant
                    "customer_id": customer_id
                }
                conv_store.save_context(session_id, updated_context)
                logger.debug(f"💾 Saved conversation to Redis for session {session_id}")
            except Exception as redis_error:
                logger.warning(f"Failed to save conversation to Redis: {redis_error}")
        
        # Store conversation in SQLite for persistence and compliance
        await _store_conversation_history(
            customer_id=customer_id,
            thread_id=config["configurable"]["thread_id"],
            user_message=message,
            assistant_response=response_text
        )
        
        return {
            "text": response_text,
            "session_id": session_id,
            "customer_message": message
        }

    except Exception as e:
        logger.error(
            "Property tax assistant error",
            error=str(e),
            session_id=session_id,
            thread_id=config["configurable"]["thread_id"]
        )
        return {
            "text": "I'm here to help you with our property tax services. What can I assist you with today?",
            "session_id": session_id,
            "error": str(e)
        }


def _detect_conversation_stage(user_message: str, assistant_response: str) -> str:
    """Detect the current conversation stage for analytics."""
    user_lower = user_message.lower()
    response_lower = assistant_response.lower()

    # Payment-related
    if any(word in response_lower for word in ['payment', 'pay', 'razorpay', 'link']):
        return 'payment'

    # Booking-related
    if any(word in response_lower for word in ['order', 'booking', 'book', 'confirm']):
        return 'booking'

    # Assessment recommendation
    if any(word in response_lower for word in ['recommend', 'suggest', 'assessment']):
        return 'recommendation'

    # Property tax inquiry
    if any(word in user_lower for word in ['assessment', 'property', 'tax', 'valuation', 'consultation']):
        return 'inquiry'

    return 'inquiry'

def _detect_language(message: str) -> str:
    """Detect message language for analytics."""
    # Simple language detection based on character patterns
    if any(ord(char) >= 0x900 and ord(char) <= 0x97F for char in message):  # Devanagari
        return 'hi'
    elif any(ord(char) >= 0x980 and ord(char) <= 0x9FF for char in message):  # Bengali
        return 'bn'
    elif any(ord(char) >= 0xB80 and ord(char) <= 0xBFF for char in message):  # Tamil
        return 'ta'
    else:
        return 'en'

async def _handle_property_document_confirmation(
    document_context: Dict[str, Any],
    session_id: str,
    customer_id: str,
    conv_store
) -> Dict[str, Any]:
    """Handle property document booking confirmation and proceed to order creation."""
    try:
        logger.info(f"🏢 Processing property document booking confirmation for {customer_id}")

        document_data = document_context.get("document_data", {})

        # Extract property information
        owner_name = document_data.get("owner_name", "")
        property_type = document_data.get("property_type")
        location = document_data.get("location", "")
        requested_assessments = document_data.get("requested_assessments", [])

        # Clear the awaiting confirmation flag
        updated_context = conv_store.get_context(session_id) or {}
        if "document_analysis" in updated_context:
            updated_context["document_analysis"]["awaiting_confirmation"] = False
            updated_context["document_analysis"]["confirmed"] = True
        conv_store.save_context(session_id, updated_context)

        logger.info(f"📋 Confirmed property document booking for {len(requested_assessments)} assessments")
        
        # Check what information we still need
        missing_info = []
        if not owner_name:
            missing_info.append("property owner name")
        if not property_type:
            missing_info.append("property type")
        if not location:
            missing_info.append("property location")

        # Always need these for booking
        missing_info.extend(["phone number", "PIN code", "preferred date", "payment method", "service preference (property visit or office consultation)"])

        # Create response asking for missing information
        assessment_list = ", ".join(requested_assessments)

        response_text = f"""Perfect! I'll help you book these assessments: {assessment_list}

To complete your booking, I need the following information:
"""
        
        # Group missing info logically
        property_info = [info for info in missing_info if info in ["property owner name", "property type", "property location"]]
        booking_info = [info for info in missing_info if info not in ["property owner name", "property type", "property location"]]

        if property_info:
            response_text += f"\n**Property Details:** {', '.join(property_info)}"

        if booking_info:
            response_text += f"\n**Booking Details:** {', '.join(booking_info)}"

        response_text += "\n\nPlease provide these details so I can complete your assessment booking."

        # Store property document data in context for order creation
        updated_context["document_booking"] = {
            "confirmed": True,
            "owner_name": owner_name,
            "property_type": property_type,
            "location": location,
            "assessments": requested_assessments,
            "assessor_name": document_data.get("assessor_name"),
            "document_date": document_data.get("document_date"),
            "awaiting_details": True
        }
        conv_store.save_context(session_id, updated_context)
        
        # Save conversation messages
        await _store_property_document_conversation(
            customer_id=customer_id,
            session_id=session_id,
            document_data=document_data,
            action="confirmed"
        )

        return {
            "text": response_text,
            "session_id": session_id,
            "document_confirmed": True,
            "assessments": requested_assessments
        }
        
    except Exception as e:
        logger.error(f"Error handling property document confirmation: {e}")
        return {
            "text": "Great! I'll help you book those assessments. Let me gather the information I need. Could you please tell me your phone number and preferred date for the assessments?",
            "session_id": session_id,
            "error": str(e)
        }


async def _store_property_document_conversation(
    customer_id: str,
    session_id: str,
    document_data: Dict[str, Any],
    action: str
) -> None:
    """Store property document confirmation in conversation history."""
    try:
        from services.persistence.database import get_db_session
        from services.persistence.repositories import CustomerRepository, MessageHistoryRepository
        
        async with get_db_session() as db_session:
            customer_repo = CustomerRepository(db_session)
            message_repo = MessageHistoryRepository(db_session)
            
            # Get or create customer
            customer_profile = await customer_repo.create_or_update(
                whatsapp_id=customer_id,
                name=document_data.get("owner_name", "Unknown User")
            )

            if customer_profile:
                # Store confirmation message
                confirmation_text = f"Property document {action}: {', '.join(document_data.get('requested_assessments', []))}"
                await message_repo.save_message(
                    customer_id=customer_profile.id,
                    thread_id=f"conversation-{session_id}",
                    message_type="system",
                    message_text=confirmation_text,
                    message_timestamp=datetime.now()
                )
                
    except Exception as e:
        logger.error(f"Failed to store property document conversation: {e}")


async def _store_conversation_history(customer_id: str, thread_id: str, user_message: str, assistant_response: str):
    """Store conversation history in SQLite for persistence and compliance."""
    try:
        from services.persistence.database import get_database_manager, UserAnalytics
        from services.persistence.repositories import CustomerRepository, MessageHistoryRepository
        from services.persistence.analytics_repository import AnalyticsRepository
        from sqlalchemy import select
        from datetime import datetime
        
        from services.persistence.database import get_db_session
        
        async with get_db_session() as session:
            # Use repository pattern for data operations
            customer_repo = CustomerRepository(session)
            message_repo = MessageHistoryRepository(session)
            
            # Get or create customer profile
            customer_profile = await customer_repo.create_or_update(
                whatsapp_id=customer_id,
                name="Unknown User"
            )
            
            if customer_profile:
                # Store user message
                await message_repo.save_message(
                    customer_id=customer_profile.id,
                    thread_id=thread_id,
                    message_type="user",
                    message_text=user_message,
                    message_timestamp=datetime.now()
                )
                
                # Store assistant response
                await message_repo.save_message(
                    customer_id=customer_profile.id,
                    thread_id=thread_id,
                    message_type="assistant", 
                    message_text=assistant_response,
                    message_timestamp=datetime.now()
                )
                
                logger.info(f"💾 Conversation stored in SQLite", 
                           customer_id=customer_id, thread_id=thread_id)
        
    except Exception as e:
        logger.error(f"Failed to store conversation history: {e}")