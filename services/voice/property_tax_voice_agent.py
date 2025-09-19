"""
Century Property Tax Voice Agent - LiveKit + Google Gemini Live Integration
Intelligent agent for property tax consultation and assessment booking via voice.
"""

import os
import asyncio
import logging
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

from livekit import rtc, agents
from livekit.agents import Agent, AgentSession, function_tool
from livekit.plugins.google.beta.realtime import RealtimeModel
from livekit import api as lk_api
import re
import sys
import os
sys.path.append('../../')

# Import property tax tools and services
from agents.simplified.property_tax_rag_tool import property_tax_rag_tool
from agents.simplified.enhanced_workflow_tools import (
    validate_pin_code,
    create_order,
    create_payment_link,
    confirm_order_cash_payment
)
from services.messaging.whatsapp_client import get_whatsapp_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Reduce verbose audio streaming logs
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("livekit").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)

# Only show tool execution and important voice agent logs
logging.getLogger(__name__).setLevel(logging.INFO)

# Load environment variables from project directory
load_dotenv()  # Load from project directory where .env file is located

# Ensure voice agent uses the main project database (not local voice directory database)
# Change working directory to main project directory to use default database path
original_cwd = os.getcwd()

# Navigate to centuryproptax project root (2 levels up from services/voice/)
main_project_dir = os.path.join(os.path.dirname(__file__), "..", "..")
main_project_dir = os.path.abspath(main_project_dir)

# Verify we found the right directory (should contain services/ and centuryproptax.db)
if os.path.exists(os.path.join(main_project_dir, "services")) and os.path.basename(main_project_dir) == "centuryproptax":
    os.chdir(main_project_dir)
    logging.info(f"🗃️ Voice agent changed working directory from {original_cwd} to {main_project_dir}")
    logging.info(f"🗃️ Voice agent will use default database: centuryproptax.db")
else:
    logging.error(f"❌ Could not find main project directory. Current: {original_cwd}, Attempted: {main_project_dir}")
    logging.info(f"🗃️ Voice agent will use local database (may be empty)")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or exit("GOOGLE_API_KEY missing")

# Verify LiveKit credentials
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
    print("Missing LiveKit credentials:")
    print(f"LIVEKIT_URL: {'✓' if LIVEKIT_URL else '✗'}")
    print(f"LIVEKIT_API_KEY: {'✓' if LIVEKIT_API_KEY else '✗'}")
    print(f"LIVEKIT_API_SECRET: {'✓' if LIVEKIT_API_SECRET else '✗'}")
    exit("LiveKit credentials missing")

# Global variable for dev mode phone number
_dev_phone_number = None

# Voice detection configuration optimized for Indian English and Hindi
turn_detection = {
    "type": "server_vad",
    "prefix_padding_ms": 500,      # Longer pause for Indian English patterns
    "silence_duration_ms": 1200,   # Wait 1.2 seconds for deliberate speech
    "threshold": 0.5               # Lower threshold for diverse accents
}

class CenturyPropertyTaxAssistant(Agent):
    """
    Century Property Tax Voice Assistant - Intelligent LLM-powered property tax conversations.
    """

    def __init__(self, end_call_coro, is_dev_mode=False) -> None:
        # Simple property document data storage for LLM context
        self._current_property_document = None  # Store current property document for LLM context
        self._whatsapp_request_sent = False  # Track if WhatsApp message already sent
        self._end_call = end_call_coro
        self._is_dev_mode = is_dev_mode

        super().__init__(
            instructions=f"""
You are a friendly multilingual property tax assistant at Century Property Tax for voice consultations.

MULTILINGUAL SUPPORT:
- Respond in the EXACT language the customer uses (English, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi)
- If unsure about language, ask: "Which language would you prefer - English या Hindi?"
- Use simple, clear language regardless of the language chosen
- Be natural and conversational in their preferred language

PERSONALITY & TONE:
- Talk like a helpful property tax professional, not a robot
- Be warm, empathetic, and conversational in voice calls
- Show genuine interest in the customer's property tax concerns
- Use natural speech patterns for voice conversations
- Avoid robotic or scripted responses

VOICE CONVERSATION FLOW:

1. **Proactive Property Document Workflow** (PRIMARY FOCUS):
   - IMMEDIATELY after greeting, offer property document analysis: "Do you have any property documents you'd like me to help you with? I can analyze them and recommend the right assessments for you."
   - When customer mentions property documents: "Perfect! I'll send you a WhatsApp message right now so you can share the property document photo." → CALL request_property_document_image IMMEDIATELY
   - If customer asks about property documents without sharing: "Let me send you a WhatsApp message so you can easily share your property document photo." → CALL request_property_document_image
   - After document analysis: Use get_current_property_document_details to access data and confirm with customer
   - For booking: Use ALL available property data (owner name, address, property type, assessments) automatically - only ask for missing information

2. **Property Tax Enquiry & Assessment Recommendations**:
   - When customers mention property tax concerns, ask for property type, location, and assessment history in their language
   - Use property_tax_rag_tool with customer's property details for intelligent recommendations
   - Present options conversationally: "Based on your property details, I'd recommend these assessments..."
   - Always mention both property visit and office consultation options

3. **Assessment Booking Process** (SMART DATA UTILIZATION):
   - **Name**: Use property owner name from document data if available, otherwise ask: "Could I get your full name for the booking?"
   - **Phone**: Use phone from call context automatically - never ask for it again
   - **Property Details**: Use from property document if available, otherwise ask for missing details
   - **Location**: "What's your area PIN code?"
   - **Date**: "When would you like to schedule this? You can say 'tomorrow', 'next Monday', or any date."
   - **Service Type**: "Would you prefer property visit for inspection or office consultation?"
   - **Payment**: "How would you like to pay - online or cash on visit?"
   - **Address** (if property visit): "I'll need your complete property address for the visit."

4. **Order Creation & Payment**:
   - Use property assessment names directly (e.g., "Property Valuation Assessment", "Tax Calculation Review") - system will intelligently find exact codes
   - Only create order after collecting ALL required information
   - Always handle payment immediately after successful order creation
   - Confirm all details before processing

LANGUAGE EXAMPLES:

**English**: "I understand you have property tax concerns. To recommend the best assessments, could you tell me your property type and location?"

**Hindi**: "मैं समझ सकता हूं कि आपको संपत्ति कर की चिंता है। सबसे अच्छे मूल्यांकन की सलाह देने के लिए, क्या आप अपनी संपत्ति का प्रकार और स्थान बता सकते हैं?"

**Bengali**: "আমি বুঝতে পারছি আপনার সম্পত্তি কর নিয়ে প্রশ্ন আছে। সেরা মূল্যায়নের পরামর্শ দিতে, আপনি কি আপনার সম্পত্তির ধরন এবং অবস্থান বলতে পারেন?"

SERVICE OPTIONS (All Languages):
- "Property visit" = संपत्ति का दौरा / সম্পত্তি পরিদর্শন / சொத்து வருகை
- "Office consultation" = कार्यालय परामर्श / অফিস পরামর্শ / அலுவலக ஆலோசனை

CRITICAL VOICE GUIDELINES:
- Speak naturally and conversationally for voice interactions
- Don't repeat information - voice conversations should flow smoothly
- Use the customer's preferred language consistently throughout
- Keep explanations clear but not overly detailed for voice
- Always offer both property visit and office consultation options
- End calls politely when the conversation is complete
- BE PROACTIVE: After greeting, immediately ask if they have property documents to analyze
- SMART CONTEXT: Use available phone/caller information without asking for it again
- IMMEDIATE ACTION: When customer mentions property documents, send WhatsApp message right away
- INTELLIGENT BOOKING: Use property document data (owner, address, property type, assessments) automatically - only ask for missing information
- CONFIRM DATA: "I see from your property document this is for [Property Owner]. I'll book these assessments for this property."

TEXAS PROPERTY TAX EXPERTISE:
- Understand Texas property tax law and assessment processes
- Guide customers through property tax appeals and exemptions
- Provide information about homestead, senior, disability, and veteran exemptions
- Explain assessment increase procedures and deadlines
- Clarify legal advice boundaries - provide information, not legal counsel

TOOLS USAGE:
- property_tax_rag_tool: Property tax analysis with property details
- request_property_document_image: WhatsApp property document photo sharing
- check_property_document_status: Monitor document processing
- get_current_property_document_details: Access analyzed property document data
- validate_pin_code: Check service area coverage
- create_property_assessment_order: Complete booking with intelligent assessment discovery (use assessment_names parameter with natural language assessment names)
- end_call: Gracefully end the conversation

Be conversational, efficient, and supportive. Support customers naturally in their preferred language throughout the entire voice interaction while maintaining professional boundaries regarding legal advice.
"""
        )

    @function_tool()
    async def property_tax_rag_tool(
        self,
        customer_query: str,
        property_type: Optional[str] = None,
        location: Optional[str] = None,
        assessment_history: Optional[str] = None
    ) -> str:
        """Get property tax assessment recommendations based on property details."""
        logging.info(f"🏘️ PROPERTY_TAX_RAG_TOOL called: query='{customer_query[:50]}...', property_type={property_type}, location={location}, history='{assessment_history[:50] if assessment_history else None}...'")

        try:
            from agents.simplified.property_tax_rag_tool import property_tax_recommendation_async
            logging.info(f"🏘️ Imported property tax recommendation function")

            logging.info(f"🏘️ Calling property tax RAG with parameters...")
            result = await property_tax_recommendation_async(
                customer_query=customer_query,
                property_type=property_type,
                location=location,
                assessment_history=assessment_history
            )

            logging.info(f"🏘️ ✅ Property tax RAG result: {str(result)[:100]}...")
            return str(result)  # Return raw data for LLM to process naturally

        except Exception as e:
            logging.error(f"🏘️ ❌ Property tax RAG tool error in voice: {e}", exc_info=True)
            return f"error: {str(e)}"

    @function_tool()
    async def request_property_document_image(self, customer_phone: str = None) -> str:
        """Send WhatsApp message requesting property document image."""
        logging.info(f"📱 REQUEST_PROPERTY_DOCUMENT_IMAGE called: customer_phone={customer_phone}")

        try:
            # Check if WhatsApp message already sent to prevent duplicates
            if self._whatsapp_request_sent:
                logging.info(f"📱 ⚠️ WhatsApp message already sent, skipping duplicate request")
                return "whatsapp_already_sent"

            # Use auto-detected phone number in dev mode
            global _dev_phone_number
            logging.info(f"📱 Dev phone number: {_dev_phone_number}")

            if _dev_phone_number:
                customer_phone = _dev_phone_number
                logging.info(f"📱 Using dev mode phone: {customer_phone}")
            elif customer_phone is None:
                logging.warning(f"📱 ❌ No phone number available")
                return "phone_number_needed"

            from services.voice.voice_chat_state import get_voice_chat_state_manager
            state_manager = get_voice_chat_state_manager()
            logging.info(f"📱 Got voice chat state manager")

            # Set status to pending
            logging.info(f"📱 Setting property document status to pending for {customer_phone[:5]}***")
            await state_manager.set_property_document_processing_status(
                customer_phone, "pending", "Waiting for property document image upload"
            )

            voice_session_id = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logging.info(f"📱 Requesting property document via WhatsApp: phone={customer_phone[:5]}***, session_id={voice_session_id}")

            result = await state_manager.request_property_document_via_whatsapp(
                customer_phone=customer_phone,
                voice_session_id=voice_session_id
            )

            logging.info(f"📱 WhatsApp request result: success={result.get('success')}, message={result.get('message', 'No message')}")

            if result.get("success"):
                self._whatsapp_request_sent = True  # Mark as sent to prevent duplicates
                logging.info(f"📱 ✅ WhatsApp message sent successfully to {customer_phone[:5]}***")
                return "whatsapp_sent_successfully"
            else:
                logging.error(f"📱 ❌ WhatsApp message failed: {result.get('message', 'Unknown error')}")
                return f"whatsapp_failed: {result.get('message', 'Unknown error')}"

        except Exception as e:
            logging.error(f"📱 ❌ Property document request error in voice: {e}", exc_info=True)
            return f"error: {str(e)}"

    @function_tool()
    async def validate_pin_code(self, pin_code: str) -> str:
        """Check if Century Property Tax provides services in customer's area."""
        logging.info(f"📍 VALIDATE_PIN_CODE called: pin_code={pin_code}")

        try:
            logging.info(f"📍 Calling pin code validation service for {pin_code}")
            result = validate_pin_code.invoke({"pin_code": pin_code})
            logging.info(f"📍 ✅ Pin code validation result: {result}")
            return result
        except Exception as e:
            logging.error(f"📍 ❌ PIN validation error in voice: {e}", exc_info=True)
            return f"serviceable: {pin_code}"

    @function_tool()
    async def create_property_assessment_order(
        self,
        customer_name: str,
        phone: str,
        assessment_names: List[str],
        pin_code: str,
        preferred_date: str = None,
        service_type: str = "property_visit",
        address: str = None,
        payment_method: str = "online"
    ) -> str:
        """
        Complete property assessment booking with intelligent assessment discovery and payment processing.

        WHEN TO USE: After collecting ALL required booking information from customer.
        TRIGGERS: User confirms they want to book assessments after seeing recommendations/property document.
        PRE-REQUISITES: Must have validated PIN code first using validate_pin_code().

        REQUIRED INFORMATION TO COLLECT (in user's detected language):
        1. customer_name: Hindi: "Aapka pura naam kya hai?" | English: "What's your full name?"
        2. phone: Auto-detected from call context when available
        3. assessment_names: From property document analysis or user request (natural language names)
        4. pin_code: Already validated using validate_pin_code()
        5. preferred_date: Hindi: "Kaunsa date prefer karenge?" | English: "Which date would you prefer?"
        6. service_type: Hindi: "Property visit ya office consultation?" | English: "Property visit or office consultation?"
        7. address: Hindi: "Aapka complete property address bataiye?" | English: "What's your full property address?"
        8. payment_method: Hindi: "Online payment ya cash visit?" | English: "Online payment or cash on visit?"

        LANGUAGE CONSISTENCY: ALL booking questions and confirmations in user's detected language.
        INTELLIGENT ASSESSMENT DISCOVERY: Uses property tax RAG to find exact assessment codes from natural language names.

        PAYMENT HANDLING:
        - Online payment: Creates secure payment link, provides booking confirmation
        - Cash payment: Confirms order for cash on visit service

        POST-BOOKING: Provide order number, payment details, and visit time confirmation.

        Args:
            customer_name: Full customer name (Required)
            phone: Customer phone number (Required)
            assessment_names: List of assessment names to book (Required - natural language names from property document/user)
            pin_code: Validated area PIN code (Required)
            preferred_date: Assessment date (Optional - suggest if not provided)
            service_type: "property_visit" (default) or "office_consultation"
            address: Full property address for property visit (Required if service_type="property_visit")
            payment_method: "online" (default) or "cash"
        """
        logging.info(f"🗺 CREATE_PROPERTY_ASSESSMENT_ORDER called: customer={customer_name}, phone={phone[:5]}***, assessments={assessment_names}, pin={pin_code}, date={preferred_date}, service={service_type}, payment={payment_method}")

        try:
            # Step 1: Use property tax RAG to find exact assessment codes from natural language assessment names
            logging.info(f"🗺 🏘️ Using property tax RAG to discover assessment codes for: {assessment_names}")
            from agents.simplified.property_tax_rag_tool import property_tax_recommendation_async

            # Combine all assessment names into a single query for intelligent lookup
            assessment_query = ", ".join(assessment_names)
            logging.info(f"🗺 🏘️ Combined assessment query: '{assessment_query}'")

            rag_result = await property_tax_recommendation_async(
                customer_query=assessment_query,
                property_type=None,  # Property type not required for assessment-based lookup
                location=None,  # Location not required for assessment-based lookup
                assessment_history=None
            )

            logging.info(f"🗺 🏘️ Property tax RAG result: success={rag_result.get('success')}, recommendations_count={len(rag_result.get('recommendations', []))}")

            if not rag_result.get('success') or not rag_result.get('recommendations'):
                logging.error(f"🗺 🏘️ ❌ Property tax RAG failed to find assessments for: {assessment_names}")
                return f"assessment_lookup_failed: Could not find assessments '{assessment_query}' in our catalog. Please contact customer support."

            # Extract assessment codes from RAG recommendations
            assessment_codes = []
            found_assessments = []

            for rec in rag_result.get('recommendations', []):
                if rec.get('assessment_code'):
                    assessment_codes.append(rec['assessment_code'])
                    found_assessments.append(rec.get('assessment_name', 'Unknown Assessment'))
                    logging.info(f"🗺 🏘️ ✅ Found assessment: {rec.get('assessment_name')} → {rec.get('assessment_code')}")

            if not assessment_codes:
                logging.error(f"🗺 🏘️ ❌ No valid assessment codes found from RAG recommendations")
                return f"assessment_codes_missing: Property tax RAG found assessments but no valid codes available. Contact support."

            logging.info(f"🗺 🏘️ ✅ Successfully mapped {len(assessment_names)} assessment names to {len(assessment_codes)} assessment codes: {assessment_codes}")

            # Step 2: Create order with discovered assessment codes
            from agents.simplified.enhanced_workflow_tools import _create_order_async
            logging.info(f"🗺 Creating order with RAG-discovered assessment codes: {assessment_codes}")

            order_result = await _create_order_async(
                instagram_id=f"voice_customer_{phone}",
                customer_name=customer_name,
                phone=phone,
                assessment_codes=assessment_codes,  # Use RAG-discovered codes
                pin_code=pin_code,
                preferred_date=preferred_date,
                service_type=service_type,
                address=address
            )

            order_result_str = str(order_result)
            logging.info(f"🗺 Order creation result: {order_result_str[:100]}...")

            if order_result.get("success"):
                logging.info(f"🗺 ✅ Order created successfully with RAG-discovered assessments: {found_assessments}")

                # Step 3: Handle payment
                if payment_method.lower() == "online":
                    logging.info(f"🗺 Creating online payment link...")
                    payment_result = create_payment_link.invoke({
                        "instagram_id": f"voice_customer_{phone}",
                        "order_id": "latest"  # Use latest order
                    })
                    payment_result_str = str(payment_result)
                    logging.info(f"🗺 ✅ Payment link created: {payment_result_str[:100]}...")
                    return f"order_created: {order_result_str}\npayment_result: {payment_result_str}\nassessments_booked: {found_assessments}"
                else:
                    logging.info(f"🗺 Confirming cash payment...")
                    cash_result = confirm_order_cash_payment.invoke({
                        "instagram_id": f"voice_customer_{phone}",
                        "order_id": "latest"
                    })
                    cash_result_str = str(cash_result)
                    logging.info(f"🗺 ✅ Cash payment confirmed: {cash_result_str[:100]}...")
                    return f"order_created: {order_result_str}\ncash_payment: {cash_result_str}\nassessments_booked: {found_assessments}"
            else:
                logging.error(f"🗺 ❌ Order creation failed after successful RAG lookup: {order_result_str}")
                return f"order_failed: {order_result_str}"

        except Exception as e:
            logging.error(f"🗺 ❌ Order creation error in voice (with RAG): {e}", exc_info=True)
            return f"error: {str(e)}"

    @function_tool()
    async def check_property_document_status(self, customer_phone: str = None) -> str:
        """Check if property document image has been processed and retrieve results."""
        logging.info(f"📋 CHECK_PROPERTY_DOCUMENT_STATUS called: customer_phone={customer_phone}")

        try:
            # Use auto-detected phone number in dev mode
            global _dev_phone_number
            logging.info(f"📋 Dev phone number: {_dev_phone_number}")

            if _dev_phone_number:
                customer_phone = _dev_phone_number
                logging.info(f"📋 Using dev mode phone: {customer_phone[:5]}***")
            elif customer_phone is None:
                logging.warning(f"📋 ❌ No phone number available")
                return "phone_number_needed"

            from services.voice.voice_chat_state import get_voice_chat_state_manager
            state_manager = get_voice_chat_state_manager()
            logging.info(f"📋 Got voice chat state manager")

            # Get current status
            logging.info(f"📋 Getting property document processing status for {customer_phone[:5]}***")
            status_info = await state_manager.get_property_document_processing_status(customer_phone)
            logging.info(f"📋 Status info: {status_info}")

            # Store property document data for LLM context if available
            if status_info.get("status") == "completed":
                property_document_data = status_info.get("property_document_data")
                if property_document_data:
                    logging.info(f"📋 ✅ Property document completed, storing data: owner={property_document_data.get('owner_name', 'Unknown')}, assessments={len(property_document_data.get('recommended_assessments', []))}")
                    self._current_property_document = property_document_data
                else:
                    logging.warning(f"📋 ⚠️ Status is completed but no property document data found")
            else:
                logging.info(f"📋 Property document status: {status_info.get('status', 'unknown')}")

            return str(status_info)  # Return raw data for LLM to process naturally

        except Exception as e:
            logging.error(f"📋 ❌ Error checking property document status: {e}", exc_info=True)
            return f"error: {str(e)}"

    @function_tool()
    async def get_current_property_document_details(self) -> str:
        """
        Get the current property document details that were uploaded and analyzed.

        Use this to reference property document data in conversation, discuss assessments,
        and proceed with booking. This gives you natural access to the analyzed
        property document information.

        Returns conversational property document details for discussion with the user.
        """
        logging.info(f"📋 GET_CURRENT_PROPERTY_DOCUMENT_DETAILS called")

        try:
            if not self._current_property_document:
                logging.info(f"📋 ⚠️ No property document data stored")
                return "no_property_document_data"

            property_document_data = self._current_property_document
            logging.info(f"📋 Found property document data: {list(property_document_data.keys())}")

            owner_name = property_document_data.get("owner_name", "Unknown")
            assessments = property_document_data.get("recommended_assessments", [])
            property_type = property_document_data.get("property_type", "Unknown Property")
            confidence = property_document_data.get("confidence_score", 0)

            logging.info(f"📋 ✅ Property document details: owner={owner_name}, property_type={property_type}, assessments={len(assessments)}, confidence={confidence}")
            logging.info(f"📋 Assessments: {assessments}")

            return str(property_document_data)  # Return raw data for LLM to process naturally

        except Exception as e:
            logging.error(f"📋 ❌ Error getting property document details: {e}", exc_info=True)
            return f"error: {str(e)}"

    @function_tool()
    async def end_call(self, reason: str = "conversation complete") -> str:
        """End the voice call when conversation is complete."""
        logging.info(f"📞 END_CALL called: reason='{reason}'")

        try:
            logging.info(f"📞 Ending voice call with reason: {reason}")
            await self._end_call(reason)
            logging.info(f"📞 ✅ Call ended successfully")
            return "call_ended_successfully"

        except Exception as e:
            logging.error(f"📞 ❌ Failed to end call: {e}", exc_info=True)
            return f"call_end_failed: {str(e)}"

# Voice Agent Entry Point
async def entrypoint(ctx: agents.JobContext):
    """
    Century Property Tax Voice Agent Entry Point
    """
    await ctx.connect()

    # Only handle PSTN rooms shaped like: call-_<E.164_number>[_...]
    pstn_room_pattern = r"^call-_\+\d{10,15}(?:_|$)"
    is_pstn_room = bool(re.match(pstn_room_pattern, ctx.room.name))

    if not is_pstn_room:
        # Do NOT greet, do NOT attach handlers, do NOT delete the room.
        # Just end this worker so the test/dev room can live on without the agent.
        logging.info(f"Skipping non-PSTN room: {ctx.room.name}")
        ctx.shutdown(reason="Non-PSTN room pattern; skipping agent")
        return

    logging.info(f"Century Property Tax voice agent joining room: {ctx.room.name}")

    # Initialize voice-chat state management
    from services.voice.voice_chat_state import get_voice_chat_state_manager
    state_manager = get_voice_chat_state_manager()

    # Detect dev mode and auto-extract phone number
    is_dev_mode = len(sys.argv) > 1 and sys.argv[1] == "dev"
    dev_phone_number = None

    if is_dev_mode:
        # In dev mode, extract phone from room name or participants dynamically
        try:
            # First try to extract from room name (format: call-_+919179687775_...)
            room_name = ctx.room.name
            logging.info(f"🧪 DEV MODE: Analyzing room name: {room_name}")

            # Enhanced phone number patterns to handle various formats
            phone_patterns = [
                r'call-_\+91(\d{10})(?:_|$)',  # call-_+919179687775_ or call-_+919179687775
                r'call-_91(\d{10})(?:_|$)',    # call-_919179687775_ or call-_919179687775
                r'call-_(\d{10})(?:_|$)',      # call-_9179687775_ or call-_9179687775
                r'\+91(\d{10})',               # +919179687775
                r'91(\d{10})',                 # 919179687775
                r'(\d{10})'                    # 9179687775 (fallback)
            ]

            for i, pattern in enumerate(phone_patterns):
                match = re.search(pattern, room_name)
                if match:
                    phone_digits = match.group(1)
                    logging.info(f"🧪 DEV MODE: Found phone digits '{phone_digits}' with pattern {i+1}")

                    # Ensure it's a valid 10-digit Indian mobile number
                    if len(phone_digits) == 10 and phone_digits.startswith(('6', '7', '8', '9')):
                        dev_phone_number = f"91{phone_digits}"  # Add country code
                        logging.info(f"🧪 DEV MODE: Extracted phone from room name: {dev_phone_number}")
                        break

            # Fallback to participant identity if room name extraction failed
            if not dev_phone_number:
                logging.info("🧪 DEV MODE: Room name extraction failed, trying participant identity")
                await asyncio.sleep(2)  # Wait for participants to join

                for participant in ctx.room.remote_participants.values():
                    if hasattr(participant, 'identity') and participant.identity:
                        potential_phone = participant.identity.strip()
                        logging.info(f"🧪 DEV MODE: Checking participant identity: {potential_phone}")

                        # Try different formats for participant identity
                        if potential_phone.isdigit():
                            if len(potential_phone) == 10 and potential_phone.startswith(('6', '7', '8', '9')):
                                dev_phone_number = f"91{potential_phone}"
                                logging.info(f"🧪 DEV MODE: Extracted phone from participant (10 digits): {dev_phone_number}")
                                break
                            elif len(potential_phone) == 12 and potential_phone.startswith('91'):
                                dev_phone_number = potential_phone
                                logging.info(f"🧪 DEV MODE: Extracted phone from participant (12 digits): {dev_phone_number}")
                                break
                        # Handle +91 prefix in participant identity
                        elif potential_phone.startswith('+91') and len(potential_phone) == 13:
                            clean_phone = potential_phone[3:]  # Remove +91
                            if clean_phone.isdigit() and clean_phone.startswith(('6', '7', '8', '9')):
                                dev_phone_number = f"91{clean_phone}"
                                logging.info(f"🧪 DEV MODE: Extracted phone from participant (+91 format): {dev_phone_number}")
                                break

            # Final fallback - should rarely be used now
            if not dev_phone_number:
                dev_phone_number = "919876543210"  # Default dev number
                logging.warning(f"🧪 DEV MODE: Using fallback phone number: {dev_phone_number}")
                logging.warning(f"🧪 DEV MODE: Room name was: {room_name}")
                logging.warning(f"🧪 DEV MODE: Participants: {[p.identity for p in ctx.room.remote_participants.values()]}")
            else:
                logging.info(f"🧪 DEV MODE: Successfully extracted phone number: {dev_phone_number}")

            # Start voice call state for detected phone number
            voice_session_id = f"dev_voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            await state_manager.start_voice_call(dev_phone_number, voice_session_id)
            logging.info(f"🔊 Started voice call state for dev mode: {dev_phone_number}")

        except Exception as e:
            logging.error(f"Error setting up dev mode phone extraction: {e}")
            dev_phone_number = "919876543210"

    # Store dev phone number globally for access in agent methods
    global _dev_phone_number
    _dev_phone_number = dev_phone_number

    # Initialize LiveKit data bridge for real-time communication
    from services.voice.livekit_data_bridge import get_livekit_data_bridge
    data_bridge = get_livekit_data_bridge()

    # Register this room for receiving property document data
    if dev_phone_number:
        await data_bridge.register_voice_room(dev_phone_number, ctx.room.name)
        logging.info(f"📡 Registered LiveKit data bridge for room {ctx.room.name}")

    # Global agent instance for data stream handling
    agent_instance = None

    async def _end_call_impl(reason: str):
        logging.info(f"Century Property Tax agent requested call end. Reason: {reason}")

        # Clean up voice call state for any active calls
        try:
            # Extract potential phone numbers from participants for cleanup
            for participant in ctx.room.remote_participants.values():
                if hasattr(participant, 'identity'):
                    potential_phone = participant.identity
                    if potential_phone and potential_phone.isdigit():
                        await state_manager.end_voice_call(potential_phone)
                        logging.info(f"🧹 Cleaned up voice call state for {potential_phone[:5]}***")
        except Exception as e:
            logging.error(f"Error cleaning up voice call state: {e}")

        await ctx.api.room.delete_room(lk_api.DeleteRoomRequest(room=ctx.room.name))
        logging.info(f"Property tax room '{ctx.room.name}' deleted by end_call.")
        ctx.shutdown(reason=f"Property tax call ended: {reason}")

    # Create property tax voice agent session
    session = AgentSession(
        llm=RealtimeModel(
            api_key=GOOGLE_API_KEY,
            voice="Kore",  # Professional, clear female voice for property tax consultations
            language="en-IN",  # Indian English with Hindi support
            modalities=["AUDIO"],
            temperature=0.2,  # Conservative for property tax accuracy
        )
    )

    # Create the Century Property Tax assistant instance
    agent_instance = CenturyPropertyTaxAssistant(end_call_coro=_end_call_impl, is_dev_mode=is_dev_mode)

    # Set up LiveKit data stream handler for property document data
    @ctx.room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        """Handle real-time property document data from chat server via LiveKit data streams"""
        logging.info(f"📡 DATA_RECEIVED: topic={data.topic}, data_size={len(data.data)} bytes")

        try:
            if data.topic in ["property_document_analysis", "property_document_status"]:
                logging.info(f"📡 Processing property document data stream: topic={data.topic}")

                message_json = data.data.decode('utf-8')
                logging.info(f"📡 Raw message JSON: {message_json[:200]}...")  # First 200 chars

                message_data = json.loads(message_json)
                phone_number = message_data.get("phone_number")
                message_type = message_data.get("message_type")

                logging.info(f"📡 ✅ Received LiveKit data stream: type={message_type}, phone={phone_number[:5] if phone_number else 'unknown'}***, data_keys={list(message_data.keys())}")

                if phone_number and agent_instance:
                    # Forward to agent for processing
                    logging.info(f"📡 Forwarding to agent: phone={phone_number[:5]}***")
                    # Note: Would need to implement _handle_livekit_property_document_message
                    logging.info(f"📡 ✅ Forwarded LiveKit data to agent for {phone_number[:5]}***")
                else:
                    logging.warning(f"📡 ⚠️ Cannot forward - phone_number={phone_number}, agent_instance={agent_instance is not None}")
            else:
                logging.info(f"📡 Ignoring non-property-document data stream: topic={data.topic}")

        except Exception as e:
            logging.error(f"📡 ❌ Error handling LiveKit data stream: {e}", exc_info=True)

    # Start the Century Property Tax assistant
    await session.start(
        agent=agent_instance,
        room=ctx.room
    )

    # Natural proactive greeting with property document focus
    await session.generate_reply(
        instructions="Greet the customer as a friendly property tax assistant from Century Property Tax. Be warm and professional. Immediately ask if they have any property documents they'd like you to analyze and recommend assessments for. If not, ask how you can help with their property tax concerns today."
    )

    # Auto-cleanup when participants leave
    @ctx.room.on("participant_disconnected")
    def _on_participant_disconnected(_: rtc.RemoteParticipant) -> None:
        if len(ctx.room.remote_participants) == 0:
            async def _cleanup() -> None:
                # Clean up voice call state when call ends
                if _dev_phone_number:
                    await state_manager.end_voice_call(_dev_phone_number)
                    logging.info(f"🧹 Cleaned up voice call state for dev phone: {_dev_phone_number}")

                await ctx.api.room.delete_room(lk_api.DeleteRoomRequest(room=ctx.room.name))
                logging.info(f"Property tax voice room '{ctx.room.name}' deleted (call ended).")
                ctx.shutdown(reason="All participants left - room cleaned up")
            asyncio.create_task(_cleanup())

if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)
    )