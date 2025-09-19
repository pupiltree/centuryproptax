"""
Krishna Diagnostics Voice Agent - LiveKit + Google Gemini Live Integration
Simplified agent that uses LLM intelligence for healthcare conversations.
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

# Import healthcare tools and services
from agents.simplified.medical_rag_tool import medical_rag_tool
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

# Navigate to krishna-diagnostics project root (2 levels up from services/voice/)
main_project_dir = os.path.join(os.path.dirname(__file__), "..", "..")
main_project_dir = os.path.abspath(main_project_dir)

# Verify we found the right directory (should contain services/ and krishna_diagnostics.db)
if os.path.exists(os.path.join(main_project_dir, "services")) and os.path.basename(main_project_dir) == "krishna-diagnostics":
    os.chdir(main_project_dir)
    logging.info(f"🗃️ Voice agent changed working directory from {original_cwd} to {main_project_dir}")
    logging.info(f"🗃️ Voice agent will use default database: krishna_diagnostics.db")
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

class KrishnaHealthcareAssistant(Agent):
    """
    Krishna Diagnostics Voice Assistant - Intelligent LLM-powered healthcare conversations.
    """

    def __init__(self, end_call_coro, is_dev_mode=False) -> None:
        # Simple prescription data storage for LLM context
        self._current_prescription = None  # Store current prescription for LLM context
        self._whatsapp_request_sent = False  # Track if WhatsApp message already sent
        self._end_call = end_call_coro
        self._is_dev_mode = is_dev_mode

        super().__init__(
            instructions=f"""
You are Maya from Krishna Diagnostics, a friendly multilingual healthcare assistant for voice consultations.

MULTILINGUAL SUPPORT:
- Respond in the EXACT language the customer uses (English, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi)
- If unsure about language, ask: "Which language would you prefer - English या Hindi?"
- Use simple, clear language regardless of the language chosen
- Be natural and conversational in their preferred language

PERSONALITY & TONE:
- Talk like a helpful healthcare professional, not a robot
- Be warm, empathetic, and conversational in voice calls
- Show genuine interest in the customer's health
- Use natural speech patterns for voice conversations
- Avoid robotic or scripted responses

VOICE CONVERSATION FLOW:

1. **Proactive Prescription Workflow** (PRIMARY FOCUS):
   - IMMEDIATELY after greeting, offer prescription analysis: "Do you have a doctor's prescription you'd like me to help you with? I can analyze it and book the tests for you."
   - When customer mentions prescription: "Perfect! I'll send you a WhatsApp message right now so you can share the prescription photo." → CALL request_prescription_image IMMEDIATELY
   - If customer asks about prescription without sharing: "Let me send you a WhatsApp message so you can easily share your prescription photo." → CALL request_prescription_image
   - After prescription analysis: Use get_current_prescription_details to access data and confirm with customer
   - For booking: Use ALL available prescription data (patient name, age, gender, tests) automatically - only ask for missing information

2. **Health Enquiry & Test Recommendations**:
   - When customers mention health conditions, ask for age, gender, and symptoms in their language
   - Use medical_rag_tool with customer's symptoms, age, and gender for intelligent recommendations
   - Present options conversationally: "Based on your symptoms, I'd recommend these tests..."
   - Always mention both home collection and lab visit options

3. **Booking Process** (SMART DATA UTILIZATION):
   - **Name**: Use patient name from prescription data if available, otherwise ask: "Could I get your full name for the booking?"
   - **Phone**: Use phone from call context automatically - never ask for it again
   - **Age/Gender**: Use from prescription if available, otherwise ask for missing details
   - **Location**: "What's your area PIN code?"
   - **Date**: "When would you like to schedule this? You can say 'tomorrow', 'next Monday', or any date."
   - **Service Type**: "Would you prefer home collection or visiting our test center?"
   - **Payment**: "How would you like to pay - online or cash on collection?"
   - **Address** (if home collection): "I'll need your complete address for home collection."

4. **Order Creation & Payment**:
   - Use prescription test names directly (e.g., "HLA B27 PCR", "MRI DL Spine") - system will intelligently find exact codes
   - Only create order after collecting ALL required information
   - Always handle payment immediately after successful order creation
   - Confirm all details before processing

LANGUAGE EXAMPLES:

**English**: "I understand you're concerned about diabetes. To recommend the best tests, could you tell me your age and gender?"

**Hindi**: "मैं समझ सकता हूं कि आपको मधुमेह की चिंता है। सबसे अच्छे टेस्ट की सलाह देने के लिए, क्या आप अपनी उम्र और लिंग बता सकते हैं?"

**Bengali**: "আমি বুঝতে পারছি আপনি ডায়াবেটিস নিয়ে চিন্তিত। সেরা পরীক্ষার পরামর্শ দিতে, আপনার বয়স এবং লিঙ্গ বলতে পারেন?"

SERVICE OPTIONS (All Languages):
- "Home collection" = घर पर संग्रह / বাড়িতে সংগ্রহ / வீட்டில் சேகரிப்பு
- "Test center visit" = टेस्ट सेंटर विजिट / পরীক্ষা কেন্দ্র পরিদর্শন / சோதனை மையம் வருகை

CRITICAL VOICE GUIDELINES:
- Speak naturally and conversationally for voice interactions
- Don't repeat information - voice conversations should flow smoothly
- Use the customer's preferred language consistently throughout
- Keep explanations clear but not overly detailed for voice
- Always offer both home collection and lab visit options
- End calls politely when the conversation is complete
- BE PROACTIVE: After greeting, immediately ask if they have a prescription to analyze
- SMART CONTEXT: Use available phone/caller information without asking for it again
- IMMEDIATE ACTION: When customer mentions prescription, send WhatsApp message right away
- INTELLIGENT BOOKING: Use prescription data (name, age, gender, tests) automatically - only ask for missing information
- CONFIRM DATA: "I see from your prescription this is for [Patient Name]. I'll book these tests for them."

TOOLS USAGE:
- medical_rag_tool: Health condition analysis with age/gender
- request_prescription_image: WhatsApp prescription photo sharing
- check_prescription_status: Monitor prescription processing
- get_current_prescription_details: Access analyzed prescription data
- validate_pin_code: Check service area coverage
- create_test_order: Complete booking with intelligent test discovery (use test_names parameter with natural language test names)
- end_call: Gracefully end the conversation

Be conversational, efficient, and supportive. Support customers naturally in their preferred language throughout the entire voice interaction.
"""
        )

    @function_tool()
    async def medical_rag_tool(
        self,
        customer_query: str,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        symptoms: Optional[str] = None
    ) -> str:
        """Get medical test recommendations based on symptoms/conditions."""
        logging.info(f"🔬 MEDICAL_RAG_TOOL called: query='{customer_query[:50]}...', age={age}, gender={gender}, symptoms='{symptoms[:50] if symptoms else None}...'")

        try:
            from agents.simplified.medical_rag_tool import medical_test_recommendation_async
            logging.info(f"🔬 Imported medical test recommendation function")

            logging.info(f"🔬 Calling medical RAG with parameters...")
            result = await medical_test_recommendation_async(
                customer_query=customer_query,
                age=age,
                gender=gender,
                symptoms=symptoms
            )

            logging.info(f"🔬 ✅ Medical RAG result: {str(result)[:100]}...")
            return str(result)  # Return raw data for LLM to process naturally

        except Exception as e:
            logging.error(f"🔬 ❌ Medical RAG tool error in voice: {e}", exc_info=True)
            return f"error: {str(e)}"

    @function_tool()
    async def request_prescription_image(self, customer_phone: str = None) -> str:
        """Send WhatsApp message requesting prescription image."""
        logging.info(f"📱 REQUEST_PRESCRIPTION_IMAGE called: customer_phone={customer_phone}")

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
            logging.info(f"📱 Setting prescription status to pending for {customer_phone[:5]}***")
            await state_manager.set_prescription_processing_status(
                customer_phone, "pending", "Waiting for prescription image upload"
            )

            voice_session_id = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logging.info(f"📱 Requesting prescription via WhatsApp: phone={customer_phone[:5]}***, session_id={voice_session_id}")

            result = await state_manager.request_prescription_via_whatsapp(
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
            logging.error(f"📱 ❌ Prescription request error in voice: {e}", exc_info=True)
            return f"error: {str(e)}"

    @function_tool()
    async def validate_pin_code(self, pin_code: str) -> str:
        """Check if Krishna Diagnostics provides services in customer's area."""
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
    async def create_test_order(
        self,
        customer_name: str,
        phone: str,
        test_names: List[str],
        pin_code: str,
        preferred_date: str = None,
        collection_type: str = "home",
        address: str = None,
        payment_method: str = "online"
    ) -> str:
        """
        Complete medical test booking with intelligent test discovery and payment processing.

        WHEN TO USE: After collecting ALL required booking information from customer.
        TRIGGERS: User confirms they want to book tests after seeing recommendations/prescription.
        PRE-REQUISITES: Must have validated PIN code first using validate_pin_code().

        REQUIRED INFORMATION TO COLLECT (in user's detected language):
        1. customer_name: Hindi: "Aapka pura naam kya hai?" | English: "What's your full name?"
        2. phone: Auto-detected from call context when available
        3. test_names: From prescription analysis or user request (natural language names)
        4. pin_code: Already validated using validate_pin_code()
        5. preferred_date: Hindi: "Kaunsa date prefer karenge?" | English: "Which date would you prefer?"
        6. collection_type: Hindi: "Home collection ya lab visit?" | English: "Home collection or lab visit?"
        7. address: Hindi: "Aapka complete address bataiye?" | English: "What's your full address?"
        8. payment_method: Hindi: "Online payment ya cash collection?" | English: "Online payment or cash on collection?"

        LANGUAGE CONSISTENCY: ALL booking questions and confirmations in user's detected language.
        INTELLIGENT TEST DISCOVERY: Uses medical RAG to find exact test codes from natural language names.

        PAYMENT HANDLING:
        - Online payment: Creates secure payment link, provides booking confirmation
        - Cash payment: Confirms order for cash on collection service

        POST-BOOKING: Provide order number, payment details, and collection time confirmation.

        Args:
            customer_name: Full customer name (Required)
            phone: Customer phone number (Required)
            test_names: List of test names to book (Required - natural language names from prescription/user)
            pin_code: Validated area PIN code (Required)
            preferred_date: Collection date (Optional - suggest if not provided)
            collection_type: "home" (default) or "lab"
            address: Full address for home collection (Required if collection_type="home")
            payment_method: "online" (default) or "cash"
        """
        logging.info(f"🗺 CREATE_TEST_ORDER called: customer={customer_name}, phone={phone[:5]}***, test_names={test_names}, pin={pin_code}, date={preferred_date}, collection={collection_type}, payment={payment_method}")

        try:
            # Step 1: Use medical RAG to find exact test codes from natural language test names
            logging.info(f"🗺 🔬 Using medical RAG to discover test codes for: {test_names}")
            from agents.simplified.medical_rag_tool import medical_test_recommendation_async

            # Combine all test names into a single query for intelligent lookup
            test_query = ", ".join(test_names)
            logging.info(f"🗺 🔬 Combined test query: '{test_query}'")

            rag_result = await medical_test_recommendation_async(
                customer_query=test_query,
                age=None,  # Age not required for prescription-based lookup
                gender=None,  # Gender not required for prescription-based lookup
                symptoms=None
            )

            logging.info(f"🗺 🔬 Medical RAG result: success={rag_result.get('success')}, recommendations_count={len(rag_result.get('recommendations', []))}")

            if not rag_result.get('success') or not rag_result.get('recommendations'):
                logging.error(f"🗺 🔬 ❌ Medical RAG failed to find tests for: {test_names}")
                return f"test_lookup_failed: Could not find tests '{test_query}' in our catalog. Please contact customer support."

            # Extract test codes from RAG recommendations
            test_codes = []
            found_tests = []

            for rec in rag_result.get('recommendations', []):
                if rec.get('test_code'):
                    test_codes.append(rec['test_code'])
                    found_tests.append(rec.get('test_name', 'Unknown Test'))
                    logging.info(f"🗺 🔬 ✅ Found test: {rec.get('test_name')} → {rec.get('test_code')}")

            if not test_codes:
                logging.error(f"🗺 🔬 ❌ No valid test codes found from RAG recommendations")
                return f"test_codes_missing: Medical RAG found tests but no valid codes available. Contact support."

            logging.info(f"🗺 🔬 ✅ Successfully mapped {len(test_names)} test names to {len(test_codes)} test codes: {test_codes}")

            # Step 2: Create order with discovered test codes
            from agents.simplified.enhanced_workflow_tools import _create_order_async
            logging.info(f"🗺 Creating order with RAG-discovered test codes: {test_codes}")

            order_result = await _create_order_async(
                instagram_id=f"voice_customer_{phone}",
                customer_name=customer_name,
                phone=phone,
                test_codes=test_codes,  # Use RAG-discovered codes
                pin_code=pin_code,
                preferred_date=preferred_date,
                collection_type=collection_type,
                address=address
            )

            order_result_str = str(order_result)
            logging.info(f"🗺 Order creation result: {order_result_str[:100]}...")

            if order_result.get("success"):
                logging.info(f"🗺 ✅ Order created successfully with RAG-discovered tests: {found_tests}")

                # Step 3: Handle payment
                if payment_method.lower() == "online":
                    logging.info(f"🗺 Creating online payment link...")
                    payment_result = create_payment_link.invoke({
                        "instagram_id": f"voice_customer_{phone}",
                        "order_id": "latest"  # Use latest order
                    })
                    payment_result_str = str(payment_result)
                    logging.info(f"🗺 ✅ Payment link created: {payment_result_str[:100]}...")
                    return f"order_created: {order_result_str}\npayment_result: {payment_result_str}\ntests_booked: {found_tests}"
                else:
                    logging.info(f"🗺 Confirming cash payment...")
                    cash_result = confirm_order_cash_payment.invoke({
                        "instagram_id": f"voice_customer_{phone}",
                        "order_id": "latest"
                    })
                    cash_result_str = str(cash_result)
                    logging.info(f"🗺 ✅ Cash payment confirmed: {cash_result_str[:100]}...")
                    return f"order_created: {order_result_str}\ncash_payment: {cash_result_str}\ntests_booked: {found_tests}"
            else:
                logging.error(f"🗺 ❌ Order creation failed after successful RAG lookup: {order_result_str}")
                return f"order_failed: {order_result_str}"

        except Exception as e:
            logging.error(f"🗺 ❌ Order creation error in voice (with RAG): {e}", exc_info=True)
            return f"error: {str(e)}"

    @function_tool()
    async def check_prescription_status(self, customer_phone: str = None) -> str:
        """Check if prescription image has been processed and retrieve results."""
        logging.info(f"📋 CHECK_PRESCRIPTION_STATUS called: customer_phone={customer_phone}")

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
            logging.info(f"📋 Getting prescription processing status for {customer_phone[:5]}***")
            status_info = await state_manager.get_prescription_processing_status(customer_phone)
            logging.info(f"📋 Status info: {status_info}")

            # Store prescription data for LLM context if available
            if status_info.get("status") == "completed":
                prescription_data = status_info.get("prescription_data")
                if prescription_data:
                    logging.info(f"📋 ✅ Prescription completed, storing data: patient={prescription_data.get('patient_name', 'Unknown')}, tests={len(prescription_data.get('prescribed_tests', []))}")
                    self._current_prescription = prescription_data
                else:
                    logging.warning(f"📋 ⚠️ Status is completed but no prescription data found")
            else:
                logging.info(f"📋 Prescription status: {status_info.get('status', 'unknown')}")

            return str(status_info)  # Return raw data for LLM to process naturally

        except Exception as e:
            logging.error(f"📋 ❌ Error checking prescription status: {e}", exc_info=True)
            return f"error: {str(e)}"

    async def _auto_monitor_prescription(self, customer_phone: str):
        """
        Automatically monitor prescription processing status in the background.
        This runs separately from the conversation flow.
        """
        try:
            from services.voice.voice_chat_state import get_voice_chat_state_manager
            state_manager = get_voice_chat_state_manager()

            # Monitor for up to 60 seconds with 3-second intervals (per user request)
            max_attempts = 20  # 60 seconds / 3 seconds = 20 attempts
            attempt = 0

            logging.info(f"🔍 Starting auto-monitoring for {customer_phone[:5]}*** - looking for completed prescription")

            while attempt < max_attempts:
                await asyncio.sleep(3)  # Wait 3 seconds between checks (user requested)
                attempt += 1

                try:
                    status_info = await state_manager.get_prescription_processing_status(customer_phone)
                    current_status = status_info.get("status", "none")

                    logging.info(f"🔍 Auto-monitoring prescription for {customer_phone[:5]}***: attempt {attempt}/{max_attempts}, status: {current_status}")

                    if current_status == "completed":
                        # Prescription is ready! Log the success
                        prescription_data = status_info.get("prescription_data")
                        if prescription_data:
                            patient_name = prescription_data.get("patient_name", "Unknown")
                            tests = prescription_data.get("prescribed_tests", [])
                            logging.info(f"✅ Auto-monitoring found completed prescription for {patient_name}, tests: {tests}")
                            await self._announce_prescription_results(prescription_data)
                        else:
                            logging.warning(f"⚠️ Prescription completed but no data found for {customer_phone[:5]}***")
                        break
                    elif current_status == "failed":
                        logging.warning(f"❌ Prescription processing failed for {customer_phone[:5]}***")
                        await self._announce_prescription_failure(status_info.get("message", "Processing failed"))
                        break
                    elif current_status in ["none", "pending"]:
                        # Still waiting for image upload
                        logging.info(f"⏳ Still waiting for prescription image upload from {customer_phone[:5]}***")
                        continue
                    elif current_status == "processing":
                        # Still processing, continue waiting
                        logging.info(f"⚙️ Prescription still being processed for {customer_phone[:5]}***")
                        continue

                except Exception as e:
                    logging.error(f"Error during auto-monitoring attempt {attempt}: {e}")
                    continue

            if attempt >= max_attempts:
                # Timeout - offer alternative
                logging.warning(f"⏰ Prescription monitoring timeout for {customer_phone[:5]}***")
                # Could optionally announce timeout here

        except Exception as e:
            logging.error(f"Error in auto prescription monitoring: {e}")

    async def _announce_prescription_results(self, prescription_data: Dict[str, Any]):
        """Announce prescription results naturally during the conversation."""
        try:
            patient_name = prescription_data.get("patient_name", "")
            prescribed_tests = prescription_data.get("prescribed_tests", [])
            doctor_name = prescription_data.get("doctor_name", "")

            # Create a natural announcement
            announcement = "Great! I've analyzed your prescription. "

            if patient_name:
                announcement += f"This is for {patient_name}. "

            if prescribed_tests:
                tests_str = ', '.join(prescribed_tests) if len(prescribed_tests) <= 3 else f"{', '.join(prescribed_tests[:3])} and others"
                announcement += f"I can see the doctor has prescribed {tests_str}. "

            if doctor_name:
                announcement += f"The prescription is from Dr. {doctor_name}. "

            announcement += "Would you like me to book these tests for you?"

            # Use session to generate this as a natural interruption
            logging.info(f"🎙️ Auto-announcing prescription results: {announcement}")
            # Note: In a real implementation, we'd need access to the session to generate this
            # For now, we'll rely on the user asking for status

        except Exception as e:
            logging.error(f"Error announcing prescription results: {e}")

    async def _announce_prescription_failure(self, error_message: str):
        """Announce prescription processing failure."""
        try:
            announcement = f"I had trouble analyzing your prescription image. {error_message}. Could you try sending a clearer photo or tell me the details verbally?"
            logging.info(f"🎙️ Auto-announcing prescription failure: {announcement}")

        except Exception as e:
            logging.error(f"Error announcing prescription failure: {e}")

    async def _auto_wait_prescription_with_announcement(self, customer_phone: str):
        """
        Automatically wait for prescription results via LiveKit data stream.
        This is the fallback when LLM timing automation doesn't work.
        """
        try:
            # Wait 15 seconds as instructed
            await asyncio.sleep(15)

            logging.info(f"🤖 BACKGROUND REAL-TIME: Starting auto-wait for {customer_phone[:5]}*** - LLM timing fallback")

            # Use the same real-time waiting mechanism as the tool
            global _dev_phone_number
            if _dev_phone_number:
                customer_phone = _dev_phone_number

            # Wait for LiveKit data stream (90 second timeout)
            prescription_result = await self._wait_for_livekit_prescription_data(customer_phone, 90)

            if prescription_result:
                message_type = prescription_result.get("message_type")

                if message_type == "prescription_ready":
                    data = prescription_result.get("data", {})
                    prescription_data = data.get("prescription_data", {})

                    if prescription_data:
                        patient_name = prescription_data.get("patient_name", "Unknown")
                        tests = prescription_data.get("prescribed_tests", [])
                        doctor = prescription_data.get("doctor_name", "Unknown")

                        logging.info(f"🎉 BACKGROUND REAL-TIME SUCCESS: Received prescription for {patient_name}")
                        logging.info(f"🎉 Tests: {tests}")
                        logging.info(f"🎉 Doctor: {doctor}")
                        logging.info(f"🎉 Data ready via LiveKit - no more polling needed!")

                        # Store prescription data for LLM context
                        self._current_prescription = prescription_data

                        # Let LLM know data is available
                        await self._announce_prescription_results(patient_name, tests, doctor)

                elif message_type == "prescription_failed":
                    logging.warning(f"🤖 Background real-time: Prescription failed for {customer_phone[:5]}***")

            else:
                logging.warning(f"🤖 Background real-time: Timeout waiting for LiveKit data for {customer_phone[:5]}***")

        except Exception as e:
            logging.error(f"Error in background prescription real-time wait: {e}")

    async def _announce_prescription_results(self, patient_name: str, tests: list, doctor: str):
        """Simple logging for prescription data arrival"""
        logging.info(f"🎙️ Prescription data available for {patient_name} - LLM can use get_current_prescription_details()")

    @function_tool()
    async def get_current_prescription_details(self) -> str:
        """
        Get the current prescription details that were uploaded and analyzed.

        Use this to reference prescription data in conversation, discuss tests,
        and proceed with booking. This gives you natural access to the analyzed
        prescription information.

        Returns conversational prescription details for discussion with the user.
        """
        logging.info(f"📋 GET_CURRENT_PRESCRIPTION_DETAILS called")

        try:
            if not self._current_prescription:
                logging.info(f"📋 ⚠️ No prescription data stored")
                return "no_prescription_data"

            prescription_data = self._current_prescription
            logging.info(f"📋 Found prescription data: {list(prescription_data.keys())}")

            patient_name = prescription_data.get("patient_name", "Unknown")
            tests = prescription_data.get("prescribed_tests", [])
            doctor = prescription_data.get("doctor_name", "Unknown Doctor")
            confidence = prescription_data.get("confidence_score", 0)

            logging.info(f"📋 ✅ Prescription details: patient={patient_name}, doctor={doctor}, tests={len(tests)}, confidence={confidence}")
            logging.info(f"📋 Tests: {tests}")

            return str(prescription_data)  # Return raw data for LLM to process naturally

        except Exception as e:
            logging.error(f"📋 ❌ Error getting prescription details: {e}", exc_info=True)
            return f"error: {str(e)}"


    # Store room name for LiveKit data bridge registration
    def _set_room_context(self, room_name: str):
        """Set the current room name for LiveKit data bridge"""
        self._current_room_name = room_name
        logging.info(f"🏠 Set room context: {room_name}")

    def _handle_livekit_prescription_message(self, phone_number: str, message_data: Dict[str, Any]):
        """
        Handle prescription message received via LiveKit data stream.
        Store data and trigger proactive announcement to user.
        """
        logging.info(f"📡 LIVEKIT_PRESCRIPTION_MESSAGE received: phone={phone_number[:5]}***, data_keys={list(message_data.keys())}")

        try:
            message_type = message_data.get("message_type")
            logging.info(f"📡 Message type: {message_type}")

            if message_type == "prescription_ready":
                data = message_data.get("data", {})
                prescription_data = data.get("prescription_data", {})
                confidence_score = data.get("confidence_score", 0)

                logging.info(f"📡 Prescription ready data: patient={prescription_data.get('patient_name', 'Unknown')}, tests={len(prescription_data.get('prescribed_tests', []))}, confidence={confidence_score}")

                if prescription_data:
                    # Store for LLM context
                    self._current_prescription = prescription_data
                    logging.info(f"📡 ✅ Stored prescription data for LLM context: {phone_number[:5]}***, patient={prescription_data.get('patient_name', 'Unknown')}")

                    # Trigger proactive announcement via session
                    asyncio.create_task(self._trigger_prescription_announcement(prescription_data))
                else:
                    logging.warning(f"📡 ⚠️ Prescription ready but no data found")

            elif message_type == "prescription_failed":
                error_message = message_data.get("data", {}).get("error_message", "Unknown error")
                logging.warning(f"📡 ❌ Prescription analysis failed for {phone_number[:5]}***: {error_message}")

                # Trigger failure announcement
                asyncio.create_task(self._trigger_prescription_failure(error_message))

            else:
                logging.warning(f"📡 ⚠️ Unknown message type: {message_type}")

        except Exception as e:
            logging.error(f"📡 ❌ Error handling LiveKit prescription message: {e}", exc_info=True)

    async def _trigger_prescription_announcement(self, prescription_data: Dict[str, Any]):
        """Trigger proactive prescription announcement via session."""
        try:
            patient_name = prescription_data.get("patient_name", "")
            prescribed_tests = prescription_data.get("prescribed_tests", [])
            doctor_name = prescription_data.get("doctor_name", "")

            # Create natural announcement
            announcement = "Perfect! I've analyzed your prescription. "
            if patient_name:
                announcement += f"This is for {patient_name}. "
            if prescribed_tests:
                tests_str = ', '.join(prescribed_tests) if len(prescribed_tests) <= 3 else f"{', '.join(prescribed_tests[:3])} and others"
                announcement += f"I can see the doctor has prescribed {tests_str}. "
            if doctor_name:
                announcement += f"The prescription is from Dr. {doctor_name}. "
            announcement += "Would you like me to book these tests for you?"

            logging.info(f"🎙️ Triggering proactive prescription announcement: {announcement[:100]}...")

            # This would need access to the session to generate - for now just log
            # In a full implementation, we'd store session reference and call session.generate_reply()

        except Exception as e:
            logging.error(f"❌ Error triggering prescription announcement: {e}")

    async def _trigger_prescription_failure(self, error_message: str):
        """Trigger proactive prescription failure announcement."""
        try:
            announcement = f"I had trouble analyzing your prescription image. {error_message}. Could you try sending a clearer photo or tell me the details verbally?"
            logging.info(f"🎙️ Triggering prescription failure announcement: {announcement}")

        except Exception as e:
            logging.error(f"❌ Error triggering failure announcement: {e}")



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
    Krishna Diagnostics Voice Agent Entry Point
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

    logging.info(f"Krishna Healthcare voice agent joining room: {ctx.room.name}")

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

    # Register this room for receiving prescription data
    if dev_phone_number:
        await data_bridge.register_voice_room(dev_phone_number, ctx.room.name)
        logging.info(f"📡 Registered LiveKit data bridge for room {ctx.room.name}")

    # Global agent instance for data stream handling
    agent_instance = None

    async def _end_call_impl(reason: str):
        logging.info(f"Krishna Healthcare agent requested call end. Reason: {reason}")

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
        logging.info(f"Healthcare room '{ctx.room.name}' deleted by end_call.")
        ctx.shutdown(reason=f"Healthcare call ended: {reason}")

    # Create healthcare voice agent session
    session = AgentSession(
        llm=RealtimeModel(
            api_key=GOOGLE_API_KEY,
            voice="Kore",  # Professional, clear female voice for healthcare (Maya)
            language="en-IN",  # Indian English with Hindi support
            modalities=["AUDIO"],
            temperature=0.2,  # Conservative for healthcare accuracy
        )
    )

    # Create the Krishna healthcare assistant instance
    agent_instance = KrishnaHealthcareAssistant(end_call_coro=_end_call_impl, is_dev_mode=is_dev_mode)
    agent_instance._set_room_context(ctx.room.name)

    # Set up LiveKit data stream handler for prescription data
    @ctx.room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        """Handle real-time prescription data from chat server via LiveKit data streams"""
        logging.info(f"📡 DATA_RECEIVED: topic={data.topic}, data_size={len(data.data)} bytes")

        try:
            if data.topic in ["prescription_analysis", "prescription_status"]:
                logging.info(f"📡 Processing prescription data stream: topic={data.topic}")

                message_json = data.data.decode('utf-8')
                logging.info(f"📡 Raw message JSON: {message_json[:200]}...")  # First 200 chars

                message_data = json.loads(message_json)
                phone_number = message_data.get("phone_number")
                message_type = message_data.get("message_type")

                logging.info(f"📡 ✅ Received LiveKit data stream: type={message_type}, phone={phone_number[:5] if phone_number else 'unknown'}***, data_keys={list(message_data.keys())}")

                if phone_number and agent_instance:
                    # Forward to agent for processing
                    logging.info(f"📡 Forwarding to agent: phone={phone_number[:5]}***")
                    agent_instance._handle_livekit_prescription_message(phone_number, message_data)
                    logging.info(f"📡 ✅ Forwarded LiveKit data to agent for {phone_number[:5]}***")
                else:
                    logging.warning(f"📡 ⚠️ Cannot forward - phone_number={phone_number}, agent_instance={agent_instance is not None}")
            else:
                logging.info(f"📡 Ignoring non-prescription data stream: topic={data.topic}")

        except Exception as e:
            logging.error(f"📡 ❌ Error handling LiveKit data stream: {e}", exc_info=True)

    # Start the Krishna healthcare assistant (using existing workflow system)
    await session.start(
        agent=agent_instance,
        room=ctx.room
    )

    # Natural proactive greeting with prescription focus
    await session.generate_reply(
        instructions="Greet the customer as Maya from Krishna Diagnostics. Be warm and friendly. Immediately ask if they have a doctor's prescription they'd like you to analyze and book tests for. If not, ask how you can help with their healthcare needs today."
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
                logging.info(f"Healthcare voice room '{ctx.room.name}' deleted (call ended).")
                ctx.shutdown(reason="All participants left - room cleaned up")
            asyncio.create_task(_cleanup())

if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)
    )
