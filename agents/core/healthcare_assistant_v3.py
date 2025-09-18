"""
Healthcare Assistant v3 - Workflow-Compliant LangGraph Implementation
Following the exact workflow from docs/krsnaa_chatbot_workflow.mermaid
and TRUE LangGraph patterns from https://langchain-ai.github.io/langgraph/tutorials/customer-support/customer-support/

This implementation maps directly to workflow nodes:
F - Collect PIN, date, test type
G - Explain test prep, duration, pricing  
H - Lookup recent test or report
I - Create ticket via /tickets
J - Handover to agent via /handover
K - Suggest advanced test panel
O - Mark order as confirmed (Cash)
Q - Create order via /orders
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

# Import workflow-compliant tools
from agents.simplified.enhanced_workflow_tools import (
    # F: Book Test - Collect PIN, date, test type
    validate_pin_code,
    
    # G: Test Enquiry - Explain test prep, duration, pricing
    # (We'll use RAG system for this)
    
    # H: Lookup recent test or report  
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
    schedule_sample_collection,
    verify_customer_payment
    # REMOVED: get_payment_options - LLM handles payment options naturally
)

# Import Unified Medical RAG system for intelligent test enquiries (workflow node G)
from agents.simplified.medical_rag_tool import medical_rag_tool
from langchain_core.tools import tool

# Import ticket management for complaints (workflow node I)  
from agents.simplified.ticket_tools import create_support_ticket

# Import prescription image analysis tools
from agents.simplified.prescription_tools import (
    analyze_prescription_image_tool,
    confirm_prescription_booking
    # REMOVED: format_prescription_summary - LLM handles formatting naturally
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
        
        return f"""👨‍💼 Connecting you to a human agent...
Escalation ID: {escalation_id}
Reason: {reason}
{f'Customer Info: {customer_info}' if customer_info else ''}
A specialist agent will be with you shortly to provide personalized assistance. Please hold on while I transfer your conversation.
Average wait time: 2-3 minutes"""
        
    except Exception as e:
        logger.error(f"Error escalating to human agent: {e}")
        return "I'm arranging for a specialist to help you. Please give me a moment to connect you with the right person."

logger = structlog.get_logger()


# Custom tool node that automatically injects Instagram ID
class HealthcareToolNode:
    """Custom tool node that automatically injects Instagram ID from config."""
    
    def __init__(self, tools):
        self.tools = {tool.name: tool for tool in tools}
    
    def __call__(self, state: "HealthcareState", config: RunnableConfig):
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
                logger.error(f"Tool {tool_name} error: {e}")
                tool_messages.append(
                    ToolMessage(
                        content=f"Tool execution failed: {str(e)}",
                        tool_call_id=tool_call["id"],
                        name=tool_name
                    )
                )
        
        return {"messages": tool_messages}


# Workflow nodes K & G: Test recommendations now handled by Agentic RAG system
# - agentic_medical_rag_recommendation for intelligent medical recommendations
# - agentic_conversation_explorer for unclear requests


# Simple conversation state following LangGraph tutorial patterns
class HealthcareState(TypedDict):
    """Healthcare conversation state focused on workflow compliance."""
    messages: Annotated[list[AnyMessage], add_messages]


# Workflow-compliant healthcare assistant following LangGraph tutorial patterns
class WorkflowAssistant:
    """
    Healthcare assistant that follows the exact workflow from krsnaa_chatbot_workflow.mermaid.
    Uses TRUE LangGraph patterns with simple 2-node graph and dynamic tool selection.
    """
    
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: HealthcareState, config: RunnableConfig):
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
                    messages = state["messages"] + [("user", "Please provide a helpful response about our healthcare services.")]
                    state = {**state, "messages": messages}
                    continue
                else:
                    break
                    
            except Exception as e:
                logger.error(f"Error in healthcare assistant: {e}")
                # Fallback response
                from langchain_core.messages import AIMessage
                result = AIMessage(content="I'm here to help you with our healthcare services. How can I assist you today?")
                break
        
        return {"messages": [result]}


def create_healthcare_assistant():
    """Create workflow-compliant healthcare assistant following TRUE LangGraph patterns."""
    import os
    
    # Initialize LLM for text processing (Gemini-2.5-Flash for efficient text conversations)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.1
    )
    
    # Note: Prescription image analysis uses Gemini-2.5-Pro via the prescription_tools
    # This is handled automatically by the analyze_prescription_image_tool
    
    # Workflow-compliant tools mapped to mermaid diagram nodes
    healthcare_tools = [
        # F: Book Test workflow - PIN validation
        validate_pin_code,
        
        # G: Test Enquiry workflow - Using Unified Medical RAG for intelligent recommendations
        medical_rag_tool,
        
        
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
        schedule_sample_collection,
        verify_customer_payment,
        # REMOVED: get_payment_options - LLM handles payment options naturally
        
        # Prescription image analysis workflow
        analyze_prescription_image_tool,
        confirm_prescription_booking
        # REMOVED: format_prescription_summary - LLM handles formatting naturally
    ]
    
    # Natural, human-like healthcare assistant prompt
    healthcare_prompt = """You are a friendly multilingual healthcare assistant at Krsnaa Diagnostics. Communicate efficiently while being personal and caring.

PERSONALITY & TONE:
- Talk like a helpful healthcare professional, not a robot
- Be warm, empathetic, and conversational 
- GROUP related questions together to reduce conversation length
- Show genuine interest in the customer's health
- Use natural language and avoid robotic responses

MULTILINGUAL SUPPORT:
- Respond in the language the customer uses (English, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi)
- If unsure about language, ask: "Which language would you prefer - English या Hindi?"
- Use simple, clear language regardless of the language chosen

EFFICIENT CONVERSATION FLOW:
1. **Prescription Image Analysis**: When customers share prescription images, use Gemini-2.5-Pro for analysis
   - IMMEDIATELY call analyze_prescription_image_tool with the image data
   - Review extracted information (patient name, age, gender, tests, doctor details)
   - Use medical_rag_tool for intelligent test recommendations with Google embeddings + LLM medical reasoning
   - Present findings naturally in a clear, professional format (patient info, tests, doctor, date)
   - Always ask: "Is this information correct before we proceed with booking?"
   - If information is incomplete, ask for missing details conversationally
   - ALWAYS confirm before creating order: "Should I book these tests with the details I found?"
   
**PRESCRIPTION BOOKING CONTEXT**: When prescription information is available from previous analysis:
   - Use the provided patient details (name, age, gender, tests) naturally in conversation
   - Don't ask for information that's already available from the prescription
   - Only ask for missing booking details: phone, PIN code, date, payment method, service preference
   - Be contextually aware: "I see from your prescription that you need [test names] for [patient name]. Let me help you book these tests."
   
2. **Health Enquiry**: When customers mention conditions, gather key info together INCLUDING GENDER
   - "I understand you're concerned about [condition]. To recommend the best tests, could you tell me your age, gender, and if you've had any recent tests for this?"
   - MUST collect: age AND gender for accurate test recommendations
   - THEN call medical_rag_tool with their symptoms/conditions, age, and gender for intelligent medical recommendations
   - For unclear requests like "I need blood tests", ask intelligent clarifying questions about their health concerns
   
3. **Test Recommendations**: Present options with service preference
   - "Based on your details, I'd recommend our [Test Panel]. Would you like to book this test?"
   - "We offer two convenient options: home sample collection or visit our test center. Which would you prefer?"

4. **Booking Process**: Collect details in manageable groups
   - Start with: "Perfect! Let's book this test for you. Can I get your full name and phone number?"
   - Next ask: "What's your area PIN code and preferred date (you can say 'tomorrow', 'next Friday', 'September 7th', etc.)?"
   - Then ask payment preference naturally: "How would you like to pay?"
     • **Pay Online** (Recommended): Secure payment via UPI, Cards, Net Banking - instant confirmation
     • **Cash on Collection**: Pay when our technician arrives (home collection only)
   - Ask service preference: "Would you prefer home collection or test center visit?"
   - **FOR HOME COLLECTION ONLY**: "For home collection, I need your complete address with house/flat number, building name, street, landmark, and area details."
   - VALIDATE all information before proceeding

5. **Information Validation**: Check completeness before booking
   - IF missing gender: "I also need to know your gender for accurate test recommendations"
   - IF missing phone: "I need your phone number to coordinate the appointment"
   - IF missing date: "When would you like to schedule this? You can say 'tomorrow', 'next Monday', or any date that works for you"
   - IF missing payment/service: "How would you like to pay, and do you prefer home collection or test center visit?"
   - IF home collection chosen but missing address: "For home collection, I need your complete address including house/flat number, building name, street, and any nearby landmark."

6. **Order Creation**: Only after ALL information is complete
   - Before calling create_order, ensure you have collected all necessary information naturally through conversation
   - For home collection: Ask for address in a conversational way before booking
   - For test center visits: Address not required
   - Call create_order with ALL collected details including collection_type parameter  
   - If create_order fails due to missing information, ask for the missing details naturally
   - IMMEDIATELY after successful order creation, handle payment:
     * If online payment chosen → CALL create_payment_link
     * If cash payment chosen → CALL confirm_order_cash_payment

7. **Payment Processing**: MANDATORY after order creation
   - For online: "Creating your payment link now..." then CALL create_payment_link
   - For cash: "Confirming your cash payment booking..." then CALL confirm_order_cash_payment

USER EXPERIENCE RULES:
- NEVER mention technical backend codes (like GLU_F, HBA1C) to customers
- Always use friendly names: "Fasting Glucose Test", "HbA1c Test", "Complete Blood Count"
- **MANDATORY**: For home collection, ALWAYS ask for complete address before creating order
- If booking fails, don't expose technical details - offer to retry or escalate to human agent
- Keep responses conversational and friendly, not robotic

EFFICIENCY RULES:
- Group 2-4 related questions together instead of asking one by one
- Essential groupings:
  * Personal info: Name + Phone + Location together
  * Health details: Age + condition + recent tests together  
  * Service preferences: Payment method + collection type together
- Only separate questions if they depend on previous answers

TECHNICAL INSTRUCTIONS:
- Customer ID: {customer_id} (use for instagram_id parameter)

REQUIRED INFORMATION CHECKLIST:
✓ Age (for test recommendations)
✓ Gender (MANDATORY for accurate test suggestions)
✓ Full name (for booking)
✓ Phone number (for coordination)
✓ PIN code (for serviceability)
✓ Preferred date (YYYY-MM-DD format)
✓ Payment preference (online/cash)
✓ Service type (home collection/test center visit)
✓ **Complete address (MANDATORY for home collection): House/Flat number, Building name, Street, Landmark, Area**

TOOL CALLING SEQUENCE:
1. **Prescription Image Received** → analyze_prescription_image_tool → format results naturally → confirm_prescription_booking
2. **Health conditions/symptoms** → Ask age + gender + condition history → agentic_medical_rag_recommendation_v2 (intelligent Agentic RAG with decision-making workflow)
3. **Unclear requests** ("I need tests", "blood work") → Ask clarifying questions about health concerns and symptoms
4. PIN code provided → validate_pin_code
5. Ready to book → create_order (with collection_type parameter)
6. Order created successfully → IMMEDIATELY call payment tool:
   - Online payment: create_payment_link
   - Cash payment: confirm_order_cash_payment

CRITICAL: Never say "creating payment link" without actually calling the create_payment_link tool. Always follow order creation with immediate payment processing.

MULTILINGUAL EXAMPLES:

**English**: "I understand you're concerned about diabetes. To recommend the best tests, could you tell me your age, gender, and if you've had any recent tests for this?"

**Hindi**: "मैं समझ सकता हूं कि आपको मधुमेह की चिंता है। सबसे अच्छे टेस्ट की सलाह देने के लिए, क्या आप अपनी उम्र, लिंग और हाल के टेस्ट के बारे में बता सकते हैं?"

**Bengali**: "আমি বুঝতে পারছি আপনি ডায়াবেটিস নিয়ে চিন্তিত। সেরা পরীক্ষার পরামর্শ দিতে, আপনি কি আপনার বয়স, লিঙ্গ এবং সাম্প্রতিক পরীক্ষার কথা বলতে পারেন?"

SERVICE OPTIONS (All Languages):
- "Home collection" = घर पर संग्रह / বাড়িতে সংগ্রহ / வீட்டில் சேகரிப்பு
- "Test center visit" = टेस्ट सेंटर विजिट / পরীক্ষা কেন্দ্র পরিদর্শন / சோதனை மையம் வருகை

CRITICAL: Be conversational but efficient. Group questions to reduce back-and-forth. Always offer both home collection and test center options. Support multiple languages naturally."""
    
    # Create assistant runnable with healthcare system prompt
    healthcare_system_prompt = ChatPromptTemplate.from_messages([
        ("system", healthcare_prompt),
        ("placeholder", "{messages}")
    ])
    
    assistant_runnable = healthcare_system_prompt | llm.bind_tools(healthcare_tools)
    
    # Simple 2-node graph pattern following tutorial
    builder = StateGraph(HealthcareState)
    
    # Add nodes
    builder.add_node("assistant", WorkflowAssistant(assistant_runnable))
    builder.add_node("tools", ToolNode(healthcare_tools))
    
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


# Global healthcare assistant instance
_global_healthcare_assistant = None

def get_healthcare_assistant():
    """Get or create the global workflow-compliant healthcare assistant instance."""
    global _global_healthcare_assistant
    if _global_healthcare_assistant is None:
        _global_healthcare_assistant = create_healthcare_assistant()
        logger.info("🏥 Created workflow-compliant healthcare assistant following TRUE LangGraph patterns")
    return _global_healthcare_assistant

def reset_healthcare_assistant():
    """Reset the global assistant instance - useful for testing or configuration changes."""
    global _global_healthcare_assistant
    _global_healthcare_assistant = None
    logger.info("🔄 Healthcare assistant instance reset")


async def process_healthcare_message(message: str, session_id: str, customer_id: str) -> Dict[str, Any]:
    """
    Process healthcare message with Redis conversation persistence.
    Maps to workflow nodes: F, G, H, I, J, K, O, Q, T
    """
    # Get assistant instance and conversation store
    assistant = get_healthcare_assistant()
    
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
                "text": "I didn't receive your message clearly. How can I help you with our healthcare services?",
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
                
                # Check for pending prescription confirmation
                prescription_context = conversation_context.get("prescription_analysis") if conversation_context else None
                if prescription_context and prescription_context.get("awaiting_confirmation"):
                    logger.info(f"📋 Found pending prescription confirmation for session {session_id}")
                    
                    # Check if this is a confirmation response
                    message_lower = message.lower().strip()
                    if message_lower in ['yes', 'y', 'confirm', 'correct', 'book', 'proceed']:
                        logger.info(f"✅ User confirmed prescription booking: '{message}'")
                        
                        # Process prescription booking confirmation
                        return await _handle_prescription_confirmation(
                            prescription_context=prescription_context,
                            session_id=session_id,
                            customer_id=customer_id,
                            conv_store=conv_store
                        )
                    elif message_lower in ['no', 'n', 'wrong', 'incorrect', 'change']:
                        logger.info(f"❌ User rejected prescription: '{message}'")
                        
                        # Clear prescription context and ask for manual input
                        conversation_context.pop("prescription_analysis", None)
                        conv_store.save_context(session_id, conversation_context)
                        
                        return {
                            "text": "I understand the prescription information wasn't correct. Please tell me which tests you'd like to book and any patient details I should know.",
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
        
        # Check for active prescription booking context
        prescription_booking_context = None
        if conversation_context and "prescription_booking" in conversation_context:
            prescription_booking_context = conversation_context["prescription_booking"]
            if prescription_booking_context.get("confirmed") and prescription_booking_context.get("awaiting_details"):
                logger.info(f"📋 Found active prescription booking context for session {session_id}")
                
                # Enhance the message with prescription context for LLM
                prescription_data = prescription_booking_context
                enhanced_message = f"""{message}

[CONTEXT: User has confirmed prescription booking for: {', '.join(prescription_data.get('tests', []))}]
[PATIENT: {prescription_data.get('patient_name', 'Unknown')} (Age: {prescription_data.get('age', 'Not provided')}, Gender: {prescription_data.get('gender', 'Not provided')})]
[DOCTOR: {prescription_data.get('doctor_name', 'Not provided')}]
[PRESCRIPTION DATE: {prescription_data.get('prescription_date', 'Not provided')}]

Please process this information naturally and only ask for missing booking details needed to complete the order. Don't ask for information that's already available in the context above."""
                
                message = enhanced_message
                logger.info(f"🔍 Enhanced message with prescription context for better LLM understanding")
        
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
                        response_text = "You're welcome! Is there anything else I can help you with regarding our healthcare services?"
                    elif any(word in message.lower() for word in ['hi', 'hello', 'hey']):
                        response_text = f"Hello! I'm here to help you with Krsnaa Diagnostics services. Are you looking for any specific health tests?"
                    else:
                        response_text = "I understand you're reaching out. Could you please tell me how I can help you with our healthcare services today?"
            else:
                response_text = "I'm ready to assist you with our healthcare services. How can I help you today?"
        else:
            response_text = "I apologize for the technical issue. Please let me know what healthcare services you need assistance with."
        
        logger.info(
            "Healthcare message processed successfully",
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
            "Healthcare assistant error",
            error=str(e),
            session_id=session_id,
            thread_id=config["configurable"]["thread_id"]
        )
        return {
            "text": "I'm here to help you with our healthcare services. What can I assist you with today?",
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
    
    # Test recommendation
    if any(word in response_lower for word in ['recommend', 'suggest', 'test']):
        return 'recommendation'
    
    # Health inquiry
    if any(word in user_lower for word in ['test', 'health', 'diabetes', 'blood', 'check']):
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

async def _handle_prescription_confirmation(
    prescription_context: Dict[str, Any],
    session_id: str,
    customer_id: str,
    conv_store
) -> Dict[str, Any]:
    """Handle prescription booking confirmation and proceed to order creation."""
    try:
        logger.info(f"🏥 Processing prescription booking confirmation for {customer_id}")
        
        prescription_data = prescription_context.get("prescription_data", {})
        
        # Extract patient information
        patient_name = prescription_data.get("patient_name", "")
        age = prescription_data.get("age")
        gender = prescription_data.get("gender", "")
        prescribed_tests = prescription_data.get("prescribed_tests", [])
        
        # Clear the awaiting confirmation flag
        updated_context = conv_store.get_context(session_id) or {}
        if "prescription_analysis" in updated_context:
            updated_context["prescription_analysis"]["awaiting_confirmation"] = False
            updated_context["prescription_analysis"]["confirmed"] = True
        conv_store.save_context(session_id, updated_context)
        
        logger.info(f"📋 Confirmed prescription booking for {len(prescribed_tests)} tests")
        
        # Check what information we still need
        missing_info = []
        if not patient_name:
            missing_info.append("patient name")
        if not age:
            missing_info.append("age")
        if not gender:
            missing_info.append("gender")
        
        # Always need these for booking
        missing_info.extend(["phone number", "PIN code", "preferred date", "payment method", "service preference (home collection or test center visit)"])
        
        # Create response asking for missing information
        test_list = ", ".join(prescribed_tests)
        
        response_text = f"""Perfect! I'll help you book these tests: {test_list}

To complete your booking, I need the following information:
"""
        
        # Group missing info logically
        patient_info = [info for info in missing_info if info in ["patient name", "age", "gender"]]
        booking_info = [info for info in missing_info if info not in ["patient name", "age", "gender"]]
        
        if patient_info:
            response_text += f"\n**Patient Details:** {', '.join(patient_info)}"
        
        if booking_info:
            response_text += f"\n**Booking Details:** {', '.join(booking_info)}"
        
        response_text += "\n\nPlease provide these details so I can complete your test booking."
        
        # Store prescription data in context for order creation
        updated_context["prescription_booking"] = {
            "confirmed": True,
            "patient_name": patient_name,
            "age": age,
            "gender": gender,
            "tests": prescribed_tests,
            "doctor_name": prescription_data.get("doctor_name"),
            "prescription_date": prescription_data.get("prescription_date"),
            "awaiting_details": True
        }
        conv_store.save_context(session_id, updated_context)
        
        # Save conversation messages
        await _store_prescription_conversation(
            customer_id=customer_id,
            session_id=session_id,
            prescription_data=prescription_data,
            action="confirmed"
        )
        
        return {
            "text": response_text,
            "session_id": session_id,
            "prescription_confirmed": True,
            "tests": prescribed_tests
        }
        
    except Exception as e:
        logger.error(f"Error handling prescription confirmation: {e}")
        return {
            "text": "Great! I'll help you book those tests. Let me gather the information I need. Could you please tell me your phone number and preferred date for the tests?",
            "session_id": session_id,
            "error": str(e)
        }


async def _store_prescription_conversation(
    customer_id: str,
    session_id: str,
    prescription_data: Dict[str, Any],
    action: str
) -> None:
    """Store prescription confirmation in conversation history."""
    try:
        from services.persistence.database import get_db_session
        from services.persistence.repositories import CustomerRepository, MessageHistoryRepository
        
        async with get_db_session() as db_session:
            customer_repo = CustomerRepository(db_session)
            message_repo = MessageHistoryRepository(db_session)
            
            # Get or create customer
            customer_profile = await customer_repo.create_or_update(
                instagram_id=customer_id,
                name=prescription_data.get("patient_name", "Unknown User")
            )
            
            if customer_profile:
                # Store confirmation message
                confirmation_text = f"Prescription {action}: {', '.join(prescription_data.get('prescribed_tests', []))}"
                await message_repo.save_message(
                    customer_id=customer_profile.id,
                    thread_id=f"conversation-{session_id}",
                    message_type="system",
                    message_text=confirmation_text,
                    message_timestamp=datetime.now()
                )
                
    except Exception as e:
        logger.error(f"Failed to store prescription conversation: {e}")


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
                instagram_id=customer_id,
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