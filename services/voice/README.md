# Century Property Tax Voice Agent

Enterprise-grade voice integration for Century Property Tax services using LiveKit + Google Gemini Live API.

## 🎯 Features

### 🏛️ Property Tax-Focused Voice Assistant
- **Complete Workflow Integration**: Seamless assessment scheduling, payment, and status checking
- **Property Tax RAG System**: Intelligent tax assessment recommendations using Google embeddings
- **Priority Protocols**: Automated escalation for urgent property tax matters
- **Prescription Analysis**: Voice-guided prescription image submission workflow

### 🗣️ Advanced Voice Capabilities
- **Multi-language Support**: 10 Indian languages including Hindi, Bengali, Tamil, Telugu
- **Intelligent Healthcare Communication**: LLM-powered medical conversation, no keyword matching
- **AI Emergency Assessment**: Gemini-powered emergency triage without hardcoded patterns
- **Contextual Understanding**: Adapts responses based on conversation flow and patient needs
- **Real-time Processing**: Sub-second response times with Google Gemini Live

### 🔒 Enterprise Security & Compliance
- **DPDP Act 2023 Compliance**: Data protection and privacy compliance for Indian healthcare
- **Call Recording**: Quality assurance and compliance auditing
- **Secure Authentication**: Role-based access with secure token management
- **Healthcare Data Protection**: Encrypted transmission and storage

## 🚀 Quick Start

### Prerequisites
```bash
# Install voice-specific dependencies
pip install -r services/voice/requirements_voice.txt

# Set environment variables
export GOOGLE_API_KEY="your_google_ai_api_key"
export LIVEKIT_URL="wss://your-livekit-server.com"
export LIVEKIT_API_KEY="your_api_key"
export LIVEKIT_API_SECRET="your_api_secret"
```

### Run Voice Agent
```bash
# Test the voice agent connection
python services/voice/voice_setup.py test

# Deploy the voice agent
python services/voice/voice_setup.py deploy

# Run the voice agent
python services/voice/krishna_voice_agent.py
```

## 🏗️ Architecture

### Voice Processing Pipeline
```
Customer Call → LiveKit Room → Google STT → Gemini Live → Healthcare Tools → TTS → Customer
                      ↓
              Krishna Diagnostics Workflow
              (Booking, Payment, Reports, Escalation)
```

### Integration with Existing System
- **Workflow Compliance**: Full integration with `docs/krsnaa_chatbot_workflow.mermaid`
- **Tool Reuse**: Leverages all existing healthcare tools from `enhanced_workflow_tools.py`
- **Database Integration**: Uses existing SQLite + Redis persistence layer
- **Multi-platform**: Seamlessly works alongside Instagram and WhatsApp channels

## 🛠️ Configuration

### Voice Settings (`voice_config.py`)
```python
# Voice Model Configuration
VOICE_MODEL = "gemini-live-2.5-flash-preview"
VOICE_PERSONA = "Charon"  # Professional healthcare voice
VOICE_LANGUAGE = "en-IN"  # Indian English
VOICE_TEMPERATURE = 0.2   # Conservative for healthcare accuracy

# Voice Activity Detection (Optimized for Indian accents)
VAD_PREFIX_PADDING_MS = 500    # Account for speech patterns
VAD_SILENCE_DURATION_MS = 1200 # Deliberate pause detection
VAD_THRESHOLD = 0.5            # Diverse accent accommodation
```

### Supported Languages
- English (Indian)
- Hindi
- Bengali, Tamil, Telugu, Marathi
- Gujarati, Kannada, Malayalam, Punjabi

## 🎭 Voice Persona: Maya

**Maya** is Krishna Diagnostics' professional healthcare voice assistant:

- **Personality**: Warm, empathetic, professionally competent
- **Communication Style**: Clear, patient-focused, medically accurate
- **Language Skills**: Fluent in multiple Indian languages with healthcare terminology
- **Specialization**: Diagnostic test services, appointment booking, healthcare guidance

### Sample Interaction
```
Maya: "Hello, this is Maya from Krishna Diagnostics. I'm here to help you with 
       diagnostic test booking, test information, or report status. For your 
       convenience, I can speak in Hindi or English - which language would you prefer?"

Customer: "English please. I need to book a blood sugar test."

Maya: "Perfect! I can help you book a blood sugar test. To recommend the most 
       suitable test, could you please tell me your age and if you've experienced 
       any symptoms like increased thirst or frequent urination?"
```

## 🔧 Healthcare Tools Integration

### Available Voice Tools
1. **`check_test_availability`** - Medical test information and availability
2. **`validate_service_area`** - PIN code validation for home collection
3. **`book_diagnostic_tests`** - Complete test booking with order creation
4. **`process_payment`** - Payment processing (online/cash/card)
5. **`check_report_status`** - Report status and delivery
6. **`create_support_ticket_voice`** - Customer support ticket creation
7. **`emergency_escalation`** - Emergency situation handling

### Intelligent Emergency Protocols
- **LLM-Powered Assessment**: Gemini evaluates symptoms using medical knowledge
- **Context-Aware Responses**: Personalized emergency guidance based on specific situation
- **No Keyword Matching**: Uses AI understanding instead of hardcoded emergency patterns
- **Conservative Safety**: Always errs on the side of patient safety when uncertain
- **Professional Boundaries**: Clear scope - diagnostic services, not medical diagnosis
- **Comprehensive Documentation**: All emergency interactions logged with AI reasoning

## 📊 Monitoring & Analytics

### Health Checks
```bash
# Test voice agent connection
python services/voice/voice_setup.py test

# List active healthcare rooms
python services/voice/voice_setup.py list-rooms

# Cleanup expired rooms
python services/voice/voice_setup.py cleanup
```

### Key Metrics
- **Call Success Rate**: Target >99%
- **Response Time**: <2 seconds average
- **Language Detection**: >95% accuracy
- **Emergency Escalation**: 100% protocol compliance
- **Customer Satisfaction**: Voice quality and interaction effectiveness

## 🔐 Security & Compliance

### DPDP Act 2023 Compliance
- **Consent Management**: Explicit voice consent for call recording
- **Data Minimization**: Only collect necessary healthcare information
- **Retention Policy**: 90-day automatic data deletion
- **Access Controls**: Role-based access to voice recordings
- **Audit Logging**: Complete interaction history for compliance

### Healthcare Data Security
- **Encrypted Transmission**: End-to-end encryption for voice data
- **Secure Storage**: Healthcare data encrypted at rest
- **Access Logging**: All voice data access logged and monitored
- **Regular Audits**: Quarterly security and compliance reviews

## 🚀 Production Deployment

### Deployment Checklist
- [ ] LiveKit server configured with healthcare-grade security
- [ ] Google AI API keys configured with appropriate quotas
- [ ] Telephony integration setup (Exotel/Twilio)
- [ ] Call recording and compliance systems active
- [ ] Emergency escalation protocols tested
- [ ] Multi-language support validated
- [ ] Load balancing and failover configured
- [ ] Monitoring and alerting systems active

### Scalability
- **Concurrent Calls**: Supports 1000+ simultaneous healthcare consultations
- **Geographic Distribution**: Multi-region deployment for low latency
- **Auto-scaling**: Dynamic scaling based on call volume
- **Disaster Recovery**: Automatic failover to backup systems

## 🧪 Testing

### Voice Agent Testing
```bash
# Run comprehensive tests
python -m pytest services/voice/tests/

# Test specific functionality
python services/voice/voice_setup.py test --phone 9876543210 --room-type test

# Load testing
python services/voice/tests/load_test.py --concurrent-calls 100
```

### Test Coverage
- **Unit Tests**: Individual tool and function testing
- **Integration Tests**: End-to-end workflow validation
- **Voice Quality Tests**: Audio clarity and response accuracy
- **Load Tests**: Performance under high call volume
- **Compliance Tests**: DPDP Act and healthcare regulation compliance

## 📞 Integration with Telephony

### Supported Providers
- **Exotel**: Primary Indian telephony provider
- **Twilio**: International and backup provider
- **Plivo**: Alternative provider option
- **Custom SIP**: Enterprise SIP trunk integration

### Phone Number Integration
- **Toll-free Numbers**: 1800-XXX-XXXX for customer calls
- **Regional Numbers**: Local numbers for major cities
- **WhatsApp Integration**: Voice calls via WhatsApp Business
- **Call Routing**: Intelligent routing based on customer location

## 🔄 Workflow Integration

### Complete Healthcare Journey
1. **Voice Call Initiated** → LiveKit room creation
2. **Language Selection** → Switch to preferred language
3. **Service Request** → Tool selection and execution
4. **Data Collection** → Patient information gathering
5. **Order Creation** → Test booking with payment
6. **Confirmation** → Booking details confirmation
7. **Follow-up** → SMS confirmation and reminders

### Workflow Compliance
- ✅ **Node A-D**: Voice message handling and intent detection
- ✅ **Node E**: Intelligent voice routing with LLM decision making  
- ✅ **Node F-X**: Complete booking, payment, and confirmation flow
- ✅ **Prescription Flow**: Voice-guided image submission workflow
- ✅ **Emergency Protocols**: Immediate medical emergency escalation

## 📈 Future Enhancements

### Roadmap
- **AI-powered Health Insights**: Proactive health recommendations
- **Voice Biometrics**: Customer identification via voice patterns
- **Real-time Translation**: Live translation for family member calls
- **Integration with Wearables**: Voice-activated health data collection
- **Telemedicine Integration**: Direct doctor consultation via voice
- **Advanced Analytics**: Predictive health trend analysis

### Technology Evolution
- **Next-gen Models**: Integration with GPT-4 Turbo and beyond
- **Edge Computing**: Local voice processing for ultra-low latency
- **5G Optimization**: High-quality voice calls over 5G networks
- **IoT Integration**: Smart device integration for health monitoring

---

## 📞 Support & Maintenance

For technical support or questions about the Krishna Diagnostics Voice Agent:

- **Technical Issues**: Create issue in GitHub repository
- **Production Support**: Contact DevOps team
- **Healthcare Compliance**: Contact compliance team
- **Voice Quality Issues**: Contact voice engineering team

**Krishna Diagnostics Voice Agent** - Bringing healthcare services to your voice, in your language. 🎭🏥