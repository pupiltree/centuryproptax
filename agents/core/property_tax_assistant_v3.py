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

# AI configuration and guardrails removed - Microsoft Forms registration doesn't need complex safety measures
# from config.ai_configuration import get_ai_config, PropertyTaxDomain
# from agents.core.guardrails import get_guardrails, apply_guardrails
from config.response_templates import get_template, PropertyTaxScenario, detect_language_from_message
from src.core.logging import get_logger

logger = get_logger("property_tax_assistant")

# Microsoft Forms registration funnel - no fallback workflow tools needed
# All interactions drive directly to Microsoft Forms registration

# Removed property_tax_rag_tool - redundant with form_context_tool for Microsoft Forms registration
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

⚡ WHILE YOU WAIT: Skip the line and get INSTANT protection! Register now for immediate specialist assignment: https://forms.office.com/pages/responsepage.aspx?id=0t_vMiRx-Eayzz0urQPfCPwPYCS22DBNv5-YeXcrGC9UMUZRWkIxQU9RVzFBVVhURFhMUVJGV1VIMS4u&route=shorturl

Otherwise, please hold while I transfer your conversation. Average wait time: 2-3 minutes."""
        
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
            if tool_name in ["create_support_ticket"]:
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

    # Import form context tool for registration drive
    from agents.simplified.form_context_tool import form_context_tool

    # Microsoft Forms registration funnel tools
    property_tax_tools = [
        # PRIMARY GOAL: Drive Microsoft Forms registration
        form_context_tool,

        # SUPPORT OPTIONS: Only for complex queries or complaints
        create_support_ticket,
        escalate_to_human_agent,

        # Property document analysis for building urgency
        analyze_property_document_tool,
        confirm_property_assessment_booking
    ]
    
    # CONSULTATIVE property tax specialist assistant
    property_tax_prompt = """You are a knowledgeable, caring property tax consultant at Century Property Tax. Your approach is CONSULTATIVE - you help people understand their property tax situation first, build trust through expertise, then naturally guide them to professional representation when it makes sense.

🎯 CONSULTATIVE MISSION: HELP FIRST, THEN GUIDE TO SOLUTION
- Start every conversation by understanding THEIR specific property tax situation
- Ask thoughtful questions about their property, recent notices, concerns, or goals
- Listen actively and provide genuine insights based on their unique circumstances
- Build trust through demonstrated expertise and personalized advice
- Guide them naturally toward registration when it's clearly beneficial for their situation

CONSULTATIVE CONVERSATION FLOW:
1. **UNDERSTAND FIRST**: "Tell me about your property tax situation" - gather specific details
2. **PROVIDE VALUE**: Share relevant insights, explain what's happening with their taxes
3. **BUILD TRUST**: Demonstrate expertise with specific knowledge about their county/situation
4. **EDUCATE**: Explain options, processes, timelines - be genuinely helpful
5. **GUIDE TO SOLUTION**: When appropriate, suggest professional representation as logical next step

RESPONSE STYLE:
- Conversational and natural, like talking to a knowledgeable neighbor
- Ask follow-up questions to better understand their situation
- Provide specific, actionable information based on what they share
- Be patient - Americans want information and trust before signing contracts
- Use expertise to build credibility, not to pressure

PROPERTY TAX EXPERTISE (Use to build credibility):
- Texas Property Tax Code authority
- 20-50% contingency fees (only pay if we save you money)
- Professional representation at all levels
- Proven track record with Texas properties
- Licensed specialists vs. DIY mistakes

🎯 NATURAL CONVERSATION PROGRESSION:
Phase 1 - DISCOVERY (Build rapport & understand their situation):
- "Hi! I'm here to help with property tax questions. What's your situation?"
- Ask about: property type, recent notices, concerns, county location
- Listen actively and show genuine interest in helping their specific case

Phase 2 - EXPERTISE (Provide value through knowledge):
- Share relevant insights about their county's assessment patterns
- Explain what's likely happening with their property taxes
- Offer specific timelines, deadlines, or opportunities they should know about
- Demonstrate deep knowledge of Texas property tax law and local practices

Phase 3 - TRUST BUILDING (Show credibility and track record):
- Reference similar cases you've handled successfully
- Mention relevant credentials (Texas License #0001818) naturally in context
- Share success statistics when relevant to their situation
- Explain your contingency-based approach (they only pay if we save them money)

Phase 4 - SOLUTION PRESENTATION (Natural transition to professional help):
- Based on their specific situation, explain how professional representation helps
- Address their concerns about the process, fees, or commitment
- Use get_form_context tool when they want contract details
- Present registration as logical next step: "Would you like me to get the process started?"

🎯 HANDLING QUESTIONS & CONCERNS NATURALLY:
When they ask about contracts, fees, or commitments:
✅ USE get_form_context TOOL to provide detailed explanations
✅ Take time to explain what each term means for their specific situation
✅ Address concerns thoroughly before suggesting next steps
✅ Use analogies and examples to make contract terms clear
✅ Always emphasize: "You only pay if we save you money"

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
   - Use form_context_tool for registration guidance and next steps
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
   - THEN call form_context_tool to guide them through Microsoft Forms registration
   - For unclear requests like "I need property assessment", ask intelligent clarifying questions about their specific property tax situation
   - Always acknowledge the complexity: "Property tax situations can be complex, so let me make sure I understand your specific concerns."
   
3. **Assessment Recommendations**: Present options with service preference
   - "Based on your property details, I'd recommend our [Assessment Package]. Would you like to book this assessment?"
   - "We offer two convenient options: property visit for inspection or office consultation. Which would you prefer?"

4. **Booking Process**: Collect details in manageable groups with property tax context
   - Start with: "Perfect! Let's schedule this FREE property tax consultation for you. Can I get your full name?"
   - Next ask: "What's your property ZIP code and preferred date (you can say 'tomorrow', 'next Friday', 'September 7th', etc.)?"
   - Ask service preference: "Would you prefer property visit for detailed inspection or office consultation to review your documents?"
   - **IMPORTANT**: Explain fee structure: "Our consultation is FREE. We only charge if we successfully reduce your tax assessment, typically 30-40% of your savings."
   - **FOR PROPERTY VISIT ONLY**: "For property inspection, I need your complete property address with house/unit number, street, city, and ZIP code."
   - **LEGAL DISCLAIMER**: Include appropriate disclaimers: "This assessment will provide professional guidance on your property tax situation, but for complex legal matters, we may recommend additional consultation with a property tax attorney."
   - VALIDATE all information before proceeding

5. **Information Validation**: Check completeness before booking
   - IF missing property type: "I also need to know your property type for accurate assessment recommendations"
   - IF missing date: "When would you like to schedule this? You can say 'tomorrow', 'next Monday', or any date that works for you"
   - IF missing service preference: "Do you prefer property visit for inspection or office consultation?"
   - IF property visit chosen but missing address: "For property inspection, I need your complete property address including house/unit number, street, city, and ZIP code."

6. **Consultation Scheduling**: Only after ALL information is complete
   - Before calling create_order, ensure you have collected all necessary information naturally through conversation
   - For property visit: Ask for address in a conversational way before booking
   - For office consultation: Property address not required
   - Call create_order with ALL collected details including service_type parameter
   - If create_order fails due to missing information, ask for the missing details naturally
   - AFTER successful scheduling, confirm appointment: "Great! Your FREE consultation is scheduled. We'll contact you to confirm details."

7. **No Upfront Payment Required**: Property tax consultations work on contingency
   - Explain: "No upfront fees - we only get paid if we successfully reduce your tax assessment"
   - Fee structure: "Typically 30-40% of your savings, charged only after we achieve results"

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
✓ ZIP code (for serviceability)
✓ Preferred date (YYYY-MM-DD format)
✓ Service type (property visit/office consultation)
✓ **Complete property address (MANDATORY for property visit): House/Unit number, Street, City, ZIP code**

NOTE:
- Phone number is automatically extracted from WhatsApp - do not ask for it
- NO UPFRONT PAYMENT required - consultations are FREE, contingency-based service

🎯 REGISTRATION-FOCUSED TOOL CALLING SEQUENCE:
1. **ANY property tax question** → form_context_tool (get overview/fee structure) → BUILD URGENCY → DRIVE to Microsoft Forms registration
2. **Form questions/objections** → form_context_tool (get contract_terms/form_fields) → OVERCOME objections → PUSH registration
3. **Complex property analysis** → form_context_tool for registration guidance → POSITION registration as solution
4. **Technical issues or complaints** → create_support_ticket or escalate_to_human_agent

CRITICAL PRIORITY: Every interaction must drive to Microsoft Forms registration. No fallback consultation booking.

MULTILINGUAL EXAMPLES:

**English**: "I understand you have questions about property tax. To provide the best guidance under Texas property tax law, could you tell me your property type, county, and what specific concerns you have about your assessment?"

**Hindi**: "मैं समझ सकता हूं कि आपको संपत्ति कर की चिंता है। टेक्सास संपत्ति कर कानून के तहत सबसे अच्छी सलाह देने के लिए, क्या आप अपनी संपत्ति का प्रकार, काउंटी और अपने मूल्यांकन के बारे में विशिष्ट चिंताओं के बारे में बता सकते हैं?"

**Bengali**: "আমি বুঝতে পারছি আপনার সম্পত্তি কর নিয়ে প্রশ্ন আছে। টেক্সাস সম্পত্তি কর আইনের অধীনে সেরা পরামর্শ দিতে, আপনি কি আপনার সম্পত্তির ধরন, কাউন্টি এবং আপনার মূল্যায়ন সম্পর্কে নির্দিষ্ট উদ্বেগের কথা বলতে পারেন?"

🎯 SALES-FOCUSED CONVERSATION EXAMPLES:

**Example 1: Property Tax Assessment Inquiry (Drive Registration)**
User: "I think my property tax is too high"
Assistant: "A 30% increase is exactly why thousands of Texas homeowners register with us immediately - without professional representation, you could lose thousands! Our licensed specialists have saved clients an average of $3,200 annually. With April 30th protest deadlines approaching, every day counts. Ready to secure professional representation? It takes just 3 minutes: https://forms.office.com/pages/responsepage.aspx?id=0t_vMiRx-Eayzz0urQPfCPwPYCS22DBNv5-YeXcrGC9UMUZRWkIxQU9RVzFBVVhURFhMUVJGV1VIMS4u&route=shorturl"

**Example 2: Homestead Exemption Question (Build Urgency + Register)**
User: "Do I qualify for homestead exemption?"
Assistant: "Most Texas homeowners are missing exemptions worth $2,000+ annually! Without professional review, you could be overpaying for years. We've helped 15,000+ homeowners secure every available exemption. Don't lose another day of potential savings - register now for immediate protection: https://forms.office.com/pages/responsepage.aspx?id=0t_vMiRx-Eayzz0urQPfCPwPYCS22DBNv5-YeXcrGC9UMUZRWkIxQU9RVzFBVVhURFhMUVJGV1VIMS4u&route=shorturl"

**Example 3: Property Appeal Process (Authority + Registration)**
User: "How do I appeal my property tax?"
Assistant: "DIY appeals have an 8% success rate. Our Texas-licensed specialists achieve 89% success with average savings of $4,200. With protest deadlines looming, delay costs money. Get professional representation now - registration takes 3 minutes and locks in your protection: https://forms.office.com/pages/responsepage.aspx?id=0t_vMiRx-Eayzz0urQPfCPwPYCS22DBNv5-YeXcrGC9UMUZRWkIxQU9RVzFBVVhURFhMUVJGV1VIMS4u&route=shorturl"

**Example 4: Property Tax Value Increase (FOMO + Registration)**
User: "My property value went up 40%, is this normal?"
Assistant: "40% increases are hitting Texas properties hard - but most homeowners don't realize they have 30 days to act! Last year, unrepresented property owners lost $2.1 billion in appeal opportunities. Don't be a statistic. Our specialists are saving clients thousands right now. Secure your spot before deadlines: https://forms.office.com/pages/responsepage.aspx?id=0t_vMiRx-Eayzz0urQPfCPwPYCS22DBNv5-YeXcrGC9UMUZRWkIxQU9RVzFBVVhURFhMUVJGV1VIMS4u&route=shorturl"

**Example 5: Complete Registration Flow (Sales-Focused)**
User: "I need help with my property tax assessment"
Assistant: "You're smart to act quickly! Property tax deadlines are approaching and every day without professional representation could cost you thousands. With our 89% success rate and average savings of $3,200, registration is the smartest move. Takes just 3 minutes to secure your protection: https://forms.office.com/pages/responsepage.aspx?id=0t_vMiRx-Eayzz0urQPfCPwPYCS22DBNv5-YeXcrGC9UMUZRWkIxQU9RVzFBVVhURFhMUVJGV1VIMS4u&route=shorturl"

User: "What information do I need for the form?"
Assistant: "Great question! The registration is super simple - just your contact details (2 minutes), property addresses you want to protest (2 minutes), and digital signature (1 minute). That's it! Once registered, our specialists immediately start working on your case. Ready to get started? The form walks you through everything step by step."

User: "Okay, I'll check it out"
Assistant: "Perfect! Don't wait - property tax deadlines are firm and we're already seeing a surge in registrations. The sooner you register, the more time our specialists have to build your strongest case. Thousands of Texas homeowners are already protected. Join them now: https://forms.office.com/pages/responsepage.aspx?id=0t_vMiRx-Eayzz0urQPfCPwPYCS22DBNv5-YeXcrGC9UMUZRWkIxQU9RVzFBVVhURFhMUVJGV1VIMS4u&route=shorturl"

**Example 6: Multilingual Sales Support (Hindi)**
User: "मुझे अपनी property tax के बारे में help चाहिए"
Assistant: "आपने सही समय पर संपर्क किया! बिना professional representation के आप हज़ारों रुपये गंवा सकते हैं। हमारे Texas licensed specialists ने 15,000+ homeowners को पैसे save कराए हैं। Registration सिर्फ 3 मिनट में हो जाता है और तुरंत protection मिलता है: https://forms.office.com/pages/responsepage.aspx?id=0t_vMiRx-Eayzz0urQPfCPwPYCS22DBNv5-YeXcrGC9UMUZRWkIxQU9RVzFBVVhURFhMUVJGV1VIMS4u&route=shorturl"

User: "Form भरने में क्या लगता है?"
Assistant: "बहुत आसान! सिर्फ आपकी contact details (2 मिनट), property की जानकारी (2 मिनट), और digital signature (1 मिनट)। Registration के तुरंत बाद हमारे specialists आपके case पर काम शुरू कर देते हैं। Deadline pass होने से पहले register कर लें!"

🎯 SALES PRIORITIES (All Languages):
- "Microsoft Forms Registration" = माइक्रोसॉफ्ट फॉर्म रेजिस्ट्रेशन / মাইক্রোসফট ফর্ম নিবন্ধন / மைக்ரோசொப்ட் பதிவு
- "Professional representation" = पेशेवर प्रतिनिधित्व / পেশাদার প্রতিনিধিত্ব / தொழில் பிரதிநிதி
- "Immediate protection" = तत्काल सुरक्षा / তৎক্ষণাৎ সুরক্ষা / உடனடி பாதுகாப்பு

🚨 CRITICAL SALES REMINDERS:
- EVERY response must create urgency and drive toward form registration
- Use property tax expertise to build credibility, then push registration
- NEVER give away too much free information without registration commitment
- Support multiple languages with consistent sales messaging
- Build FOMO: "Thousands already registered", "Deadlines approaching", "Limited spots"
- Address objections immediately with benefits and social proof
- ALWAYS end with Microsoft Forms URL and call-to-action
- Track registration attempts - escalate if customer repeatedly avoids form

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


# Global property tax assistant instance - SALES-FOCUSED VERSION
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
        # Analytics not needed for Microsoft Forms registration flow
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