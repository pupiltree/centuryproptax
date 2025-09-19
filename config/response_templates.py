"""
Property Tax Response Templates - Comprehensive multilingual templates for Century Property Tax
Standardized conversation flows and response patterns for common property tax scenarios
"""

from typing import Dict, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PropertyTaxScenario(Enum):
    """Property tax conversation scenarios"""
    ASSESSMENT_INQUIRY = "assessment_inquiry"
    APPEAL_PROCESS = "appeal_process"
    EXEMPTION_QUALIFICATION = "exemption_qualification"
    PAYMENT_OPTIONS = "payment_options"
    DEADLINE_INQUIRY = "deadline_inquiry"
    DOCUMENTATION_REQUIRED = "documentation_required"
    GREETING = "greeting"
    BOOKING_CONFIRMATION = "booking_confirmation"
    ERROR_HANDLING = "error_handling"
    LEGAL_DISCLAIMER = "legal_disclaimer"

class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    HINDI = "hi"
    BENGALI = "bn"
    TAMIL = "ta"
    TELUGU = "te"
    MARATHI = "mr"
    GUJARATI = "gu"
    KANNADA = "kn"
    MALAYALAM = "ml"
    PUNJABI = "pa"

# Core response templates organized by scenario and language
PROPERTY_TAX_TEMPLATES = {
    PropertyTaxScenario.GREETING: {
        Language.ENGLISH: {
            "initial": "Hello! I'm here to help you with Century Property Tax services. Are you looking for assistance with property tax assessments, appeals, or exemptions?",
            "returning": "Welcome back! How can I assist you with your property tax needs today?",
            "with_name": "Hello {name}! I'm here to help you with Century Property Tax services. What property tax questions can I answer for you today?"
        },
        Language.HINDI: {
            "initial": "नमस्ते! मैं सेंचुरी प्रॉपर्टी टैक्स सेवाओं में आपकी सहायता के लिए यहां हूं। क्या आप संपत्ति कर मूल्यांकन, अपील, या छूट की सहायता चाहते हैं?",
            "returning": "वापस स्वागत है! आज मैं आपकी संपत्ति कर की जरूरतों में कैसे सहायता कर सकता हूं?",
            "with_name": "नमस्ते {name}! मैं सेंचुरी प्रॉपर्टी टैक्स सेवाओं में आपकी सहायता के लिए यहां हूं। आज मैं आपके संपत्ति कर के कौन से सवालों का जवाब दे सकता हूं?"
        },
        Language.BENGALI: {
            "initial": "নমস্কার! আমি সেঞ্চুরি প্রপার্টি ট্যাক্স সেবায় আপনাকে সাহায্য করতে এসেছি। আপনি কি সম্পত্তি কর মূল্যায়ন, আপিল, বা ছাড়ের সহায়তা চান?",
            "returning": "আবার স্বাগতম! আজ আপনার সম্পত্তি কর প্রয়োজনে আমি কীভাবে সাহায্য করতে পারি?",
            "with_name": "নমস্কার {name}! আমি সেঞ্চুরি প্রপার্টি ট্যাক্স সেবায় আপনাকে সাহায্য করতে এসেছি। আজ আপনার সম্পত্তি কর সম্পর্কে কোন প্রশ্নের উত্তর দিতে পারি?"
        }
    },

    PropertyTaxScenario.ASSESSMENT_INQUIRY: {
        Language.ENGLISH: {
            "high_assessment": "I understand your concern about a high property assessment. This is a common issue that affects many property owners in Texas. Let me help you understand your options for challenging this assessment.",
            "assessment_increase": "Property assessments can increase due to market value changes, improvements, or updated county valuations. I can help you review your assessment and determine if an appeal might be appropriate.",
            "first_time": "As a first-time property owner, property tax assessments can seem complex. Your property is assessed annually based on its market value as of January 1st. Let me explain how this affects your taxes.",
            "dispute_value": "If you believe your property value assessment is incorrect, you have the right to appeal through the Texas property tax system. The process typically involves informal review first, then formal ARB hearing if needed."
        },
        Language.HINDI: {
            "high_assessment": "मैं आपकी उच्च संपत्ति मूल्यांकन की चिंता समझ सकता हूं। यह एक आम समस्या है जो टेक्सास में कई संपत्ति मालिकों को प्रभावित करती है। मैं इस मूल्यांकन को चुनौती देने के आपके विकल्पों को समझने में मदद करूंगा।",
            "assessment_increase": "संपत्ति मूल्यांकन बाजार मूल्य परिवर्तन, सुधार, या अद्यतन काउंटी मूल्यांकन के कारण बढ़ सकते हैं। मैं आपके मूल्यांकन की समीक्षा करने और यह निर्धारित करने में मदद कर सकता हूं कि क्या अपील उपयुक्त हो सकती है।",
            "first_time": "पहली बार संपत्ति मालिक के रूप में, संपत्ति कर मूल्यांकन जटिल लग सकते हैं। आपकी संपत्ति का मूल्यांकन 1 जनवरी तक के बाजार मूल्य के आधार पर वार्षिक रूप से किया जाता है। मैं बताऊंगा कि यह आपके करों को कैसे प्रभावित करता है।",
            "dispute_value": "यदि आपको लगता है कि आपकी संपत्ति मूल्य मूल्यांकन गलत है, तो आपको टेक्सास संपत्ति कर प्रणाली के माध्यम से अपील करने का अधिकार है। प्रक्रिया में आमतौर पर पहले अनौपचारिक समीक्षा शामिल होती है, फिर यदि आवश्यक हो तो औपचारिक ARB सुनवाई।"
        },
        Language.BENGALI: {
            "high_assessment": "আমি আপনার উচ্চ সম্পত্তি মূল্যায়নের উদ্বেগ বুঝতে পারি। এটি একটি সাধারণ সমস্যা যা টেক্সাসের অনেক সম্পত্তির মালিকদের প্রভাবিত করে। আমি এই মূল্যায়নকে চ্যালেঞ্জ করার জন্য আপনার বিকল্পগুলি বুঝতে সাহায্য করব।",
            "assessment_increase": "বাজার মূল্য পরিবর্তন, উন্নতি, বা আপডেট কাউন্টি মূল্যায়নের কারণে সম্পত্তি মূল্যায়ন বাড়তে পারে। আমি আপনার মূল্যায়ন পর্যালোচনা করতে এবং আপিল উপযুক্ত হতে পারে কিনা তা নির্ধারণ করতে সাহায্য করতে পারি।",
            "first_time": "প্রথমবার সম্পত্তির মালিক হিসেবে, সম্পত্তি কর মূল্যায়ন জটিল মনে হতে পারে। আপনার সম্পত্তি 1 জানুয়ারির বাজার মূল্যের ভিত্তিতে বার্ষিক মূল্যায়ন করা হয়। আমি ব্যাখ্যা করব এটি আপনার করকে কীভাবে প্রভাবিত করে।",
            "dispute_value": "যদি আপনি মনে করেন যে আপনার সম্পত্তির মূল্য মূল্যায়ন ভুল, তাহলে টেক্সাস সম্পত্তি কর ব্যবস্থার মাধ্যমে আপিল করার আপনার অধিকার রয়েছে। প্রক্রিয়ায় সাধারণত প্রথমে অনানুষ্ঠানিক পর্যালোচনা জড়িত থাকে, তারপর প্রয়োজনে আনুষ্ঠানিক ARB শুনানি।"
        }
    },

    PropertyTaxScenario.APPEAL_PROCESS: {
        Language.ENGLISH: {
            "timeline": "Texas property tax appeals must be filed by May 15th (or 30 days after receiving your notice, whichever is later). The process includes: 1) Informal review with appraisal district, 2) Formal ARB hearing if needed, 3) Further appeals to district court if necessary.",
            "documents_needed": "For a successful appeal, you'll typically need: comparable property sales data, evidence of property condition issues, professional appraisal (if available), photos of property defects, and documentation of any factors that reduce your property value.",
            "success_factors": "Appeal success often depends on: providing clear comparable sales data, documenting property condition issues, presenting professional evidence, and showing the assessed value exceeds market value by a significant margin.",
            "informal_vs_formal": "Informal review is your first step - it's quicker and less formal. If unsuccessful, you can proceed to a formal ARB hearing where you present evidence to a panel. Most cases are resolved at the informal level."
        },
        Language.HINDI: {
            "timeline": "टेक्सास संपत्ति कर अपील 15 मई तक (या आपके नोटिस प्राप्त करने के 30 दिन बाद, जो भी बाद में हो) दाखिल करनी चाहिए। प्रक्रिया में शामिल है: 1) मूल्यांकन जिले के साथ अनौपचारिक समीक्षा, 2) यदि आवश्यक हो तो औपचारिक ARB सुनवाई, 3) यदि आवश्यक हो तो जिला न्यायालय में आगे की अपील।",
            "documents_needed": "सफल अपील के लिए, आपको आमतौर पर चाहिए: तुलनीय संपत्ति बिक्री डेटा, संपत्ति स्थिति के मुद्दों का सबूत, पेशेवर मूल्यांकन (यदि उपलब्ध हो), संपत्ति दोषों की तस्वीरें, और किसी भी कारक का दस्तावेजीकरण जो आपकी संपत्ति मूल्य कम करता है।",
            "success_factors": "अपील की सफलता अक्सर इस पर निर्भर करती है: स्पष्ट तुलनीय बिक्री डेटा प्रदान करना, संपत्ति स्थिति के मुद्दों का दस्तावेजीकरण, पेशेवर साक्ष्य प्रस्तुत करना, और दिखाना कि मूल्यांकित मूल्य बाजार मूल्य से काफी अधिक है।",
            "informal_vs_formal": "अनौपचारिक समीक्षा आपका पहला कदम है - यह तेज़ और कम औपचारिक है। यदि असफल हो, तो आप औपचारिक ARB सुनवाई में जा सकते हैं जहाँ आप पैनल के सामने साक्ष्य प्रस्तुत करते हैं। अधिकांश मामले अनौपचारिक स्तर पर हल हो जाते हैं।"
        },
        Language.BENGALI: {
            "timeline": "টেক্সাস সম্পত্তি কর আপিল 15 মে এর মধ্যে (বা আপনার নোটিস পাওয়ার 30 দিন পর, যেটি পরে হয়) জমা দিতে হবে। প্রক্রিয়ায় অন্তর্ভুক্ত: 1) মূল্যায়ন জেলার সাথে অনানুষ্ঠানিক পর্যালোচনা, 2) প্রয়োজনে আনুষ্ঠানিক ARB শুনানি, 3) প্রয়োজনে জেলা আদালতে আরও আপিল।",
            "documents_needed": "সফল আপিলের জন্য, আপনার সাধারণত প্রয়োজন: তুলনীয় সম্পত্তি বিক্রয় তথ্য, সম্পত্তি অবস্থার সমস্যার প্রমাণ, পেশাদার মূল্যায়ন (যদি উপলব্ধ থাকে), সম্পত্তির ত্রুটির ছবি, এবং আপনার সম্পত্তির মূল্য কমায় এমন কোনো কারণের ডকুমেন্টেশন।",
            "success_factors": "আপিলের সাফল্য প্রায়ই নির্ভর করে: স্পষ্ট তুলনীয় বিক্রয় তথ্য প্রদান, সম্পত্তি অবস্থার সমস্যা ডকুমেন্ট করা, পেশাদার প্রমাণ উপস্থাপনা, এবং দেখানো যে মূল্যায়িত মূল্য বাজার মূল্যের চেয়ে উল্লেখযোগ্যভাবে বেশি।",
            "informal_vs_formal": "অনানুষ্ঠানিক পর্যালোচনা আপনার প্রথম পদক্ষেপ - এটি দ্রুত এবং কম আনুষ্ঠানিক। যদি ব্যর্থ হয়, আপনি আনুষ্ঠানিক ARB শুনানিতে যেতে পারেন যেখানে আপনি একটি প্যানেলের কাছে প্রমাণ উপস্থাপন করেন। বেশিরভাগ ক্ষেত্রে অনানুষ্ঠানিক স্তরে সমাধান হয়।"
        }
    },

    PropertyTaxScenario.EXEMPTION_QUALIFICATION: {
        Language.ENGLISH: {
            "homestead": "The Texas Homestead Exemption provides a minimum $40,000 reduction in your home's assessed value for property tax purposes. You must apply by April 30th and the property must be your primary residence as of January 1st.",
            "senior": "Senior citizens (65 and older) qualify for additional exemptions and tax ceiling protection. Once you turn 65, your school taxes are frozen at that level. You must apply with your county appraisal district.",
            "disability": "Disabled persons may qualify for exemptions similar to senior citizens. You'll need documentation from a qualified physician. The application process includes medical verification and annual certification.",
            "veteran": "Veterans and their families may qualify for various exemptions depending on disability rating and service history. Benefits range from partial to complete property tax exemptions for qualifying veterans.",
            "application_process": "Exemption applications are typically due by April 30th. You'll need to provide documentation proving eligibility. Once approved, exemptions continue automatically unless your circumstances change."
        },
        Language.HINDI: {
            "homestead": "टेक्सास होमस्टेड एक्जम्प्शन संपत्ति कर उद्देश्यों के लिए आपके घर के मूल्यांकित मूल्य में न्यूनतम $40,000 की कमी प्रदान करता है। आपको 30 अप्रैल तक आवेदन करना होगा और 1 जनवरी तक संपत्ति आपका प्राथमिक निवास होना चाहिए।",
            "senior": "वरिष्ठ नागरिक (65 और अधिक उम्र) अतिरिक्त छूट और कर सीमा सुरक्षा के लिए योग्य हैं। एक बार जब आप 65 के हो जाते हैं, तो आपके स्कूल कर उस स्तर पर जमे रहते हैं। आपको अपने काउंटी मूल्यांकन जिले के साथ आवेदन करना होगा।",
            "disability": "विकलांग व्यक्ति वरिष्ठ नागरिकों के समान छूट के लिए योग्य हो सकते हैं। आपको एक योग्य चिकित्सक से दस्तावेज की आवश्यकता होगी। आवेदन प्रक्रिया में चिकित्सा सत्यापन और वार्षिक प्रमाणन शामिल है।",
            "veteran": "सेवानिवृत्त सैनिक और उनके परिवार विकलांगता रेटिंग और सेवा इतिहास के आधार पर विभिन्न छूट के लिए योग्य हो सकते हैं। लाभ योग्य सेवानिवृत्त सैनिकों के लिए आंशिक से पूर्ण संपत्ति कर छूट तक होते हैं।",
            "application_process": "छूट आवेदन आमतौर पर 30 अप्रैल तक देय होते हैं। आपको योग्यता साबित करने वाले दस्तावेज प्रदान करने होंगे। एक बार अनुमोदित होने पर, छूट तब तक स्वचालित रूप से जारी रहती है जब तक आपकी परिस्थितियां नहीं बदलतीं।"
        },
        Language.BENGALI: {
            "homestead": "টেক্সাস হোমস্টেড এক্সেম্পশন সম্পত্তি কর উদ্দেশ্যে আপনার বাড়ির মূল্যায়িত মূল্যে ন্যূনতম $40,000 হ্রাস প্রদান করে। আপনাকে 30 এপ্রিলের মধ্যে আবেদন করতে হবে এবং 1 জানুয়ারি পর্যন্ত সম্পত্তি আপনার প্রাথমিক বাসস্থান হতে হবে।",
            "senior": "প্রবীণ নাগরিকরা (65 এবং তার বেশি বয়সী) অতিরিক্ত ছাড় এবং কর সিলিং সুরক্ষার জন্য যোগ্য। একবার আপনি 65 বছর বয়সী হলে, আপনার স্কুল কর সেই স্তরে স্থির থাকে। আপনাকে আপনার কাউন্টি মূল্যায়ন জেলার সাথে আবেদন করতে হবে।",
            "disability": "প্রতিবন্ধী ব্যক্তিরা প্রবীণ নাগরিকদের অনুরূপ ছাড়ের জন্য যোগ্য হতে পারেন। আপনার একজন যোগ্য চিকিৎসকের কাছ থেকে ডকুমেন্টেশন প্রয়োজন হবে। আবেদন প্রক্রিয়ায় চিকিৎসা যাচাইকরণ এবং বার্ষিক সার্টিফিকেশন অন্তর্ভুক্ত।",
            "veteran": "প্রবীণ সৈনিক এবং তাদের পরিবার অক্ষমতা রেটিং এবং সেবা ইতিহাসের উপর ভিত্তি করে বিভিন্ন ছাড়ের জন্য যোগ্য হতে পারেন। সুবিধা যোগ্য প্রবীণদের জন্য আংশিক থেকে সম্পূর্ণ সম্পত্তি কর ছাড় পর্যন্ত।",
            "application_process": "ছাড়ের আবেদন সাধারণত 30 এপ্রিলের মধ্যে দিতে হয়। আপনাকে যোগ্যতা প্রমাণের ডকুমেন্টেশন প্রদান করতে হবে। একবার অনুমোদিত হলে, আপনার পরিস্থিতি পরিবর্তন না হওয়া পর্যন্ত ছাড় স্বয়ংক্রিয়ভাবে অব্যাহত থাকে।"
        }
    },

    PropertyTaxScenario.PAYMENT_OPTIONS: {
        Language.ENGLISH: {
            "installment_plans": "Texas offers installment payment plans for property taxes. You can split your annual tax bill into monthly payments, but you must apply before delinquency. Interest and fees may apply.",
            "online_payment": "Most Texas counties offer online payment options through their websites. You can pay by credit card, debit card, or electronic check. Convenience fees may apply for card payments.",
            "deadline_info": "Property taxes are typically due by January 31st. If you pay after the deadline, penalty and interest charges will be added to your bill. The longer you wait, the higher these charges become.",
            "partial_payments": "If you can't pay the full amount, contact your county tax office about partial payment arrangements. Some counties allow partial payments to reduce accumulating penalties and interest."
        },
        Language.HINDI: {
            "installment_plans": "टेक्सास संपत्ति करों के लिए किस्त भुगतान योजना प्रदान करता है। आप अपने वार्षिक कर बिल को मासिक भुगतान में विभाजित कर सकते हैं, लेकिन आपको अपराध से पहले आवेदन करना होगा। ब्याज और शुल्क लागू हो सकते हैं।",
            "online_payment": "अधिकांश टेक्सास काउंटियां अपनी वेबसाइटों के माध्यम से ऑनलाइन भुगतान विकल्प प्रदान करती हैं। आप क्रेडिट कार्ड, डेबिट कार्ड, या इलेक्ट्रॉनिक चेक द्वारा भुगतान कर सकते हैं। कार्ड भुगतान के लिए सुविधा शुल्क लागू हो सकते हैं।",
            "deadline_info": "संपत्ति कर आमतौर पर 31 जनवरी तक देय होते हैं। यदि आप समय सीमा के बाद भुगतान करते हैं, तो आपके बिल में जुर्माना और ब्याज शुल्क जोड़े जाएंगे। आप जितना अधिक इंतजार करेंगे, ये शुल्क उतने ही अधिक होंगे।",
            "partial_payments": "यदि आप पूरी राशि का भुगतान नहीं कर सकते, तो आंशिक भुगतान व्यवस्था के बारे में अपने काउंटी कर कार्यालय से संपर्क करें। कुछ काउंटियां संचित जुर्माना और ब्याज को कम करने के लिए आंशिक भुगतान की अनुमति देती हैं।"
        },
        Language.BENGALI: {
            "installment_plans": "টেক্সাস সম্পত্তি করের জন্য কিস্তি পেমেন্ট প্ল্যান অফার করে। আপনি আপনার বার্ষিক কর বিল মাসিক পেমেন্টে ভাগ করতে পারেন, কিন্তু আপনাকে অবহেলার আগে আবেদন করতে হবে। সুদ এবং ফি প্রযোজ্য হতে পারে।",
            "online_payment": "বেশিরভাগ টেক্সাস কাউন্টি তাদের ওয়েবসাইটের মাধ্যমে অনলাইন পেমেন্ট অপশন অফার করে। আপনি ক্রেডিট কার্ড, ডেবিট কার্ড, বা ইলেকট্রনিক চেক দিয়ে পেমেন্ট করতে পারেন। কার্ড পেমেন্টের জন্য সুবিধার ফি প্রযোজ্য হতে পারে।",
            "deadline_info": "সম্পত্তি কর সাধারণত 31 জানুয়ারির মধ্যে দিতে হয়। যদি আপনি সময়সীমার পরে পেমেন্ট করেন, তাহলে আপনার বিলে জরিমানা এবং সুদের চার্জ যোগ হবে। আপনি যত বেশি অপেক্ষা করবেন, এই চার্জগুলি তত বেশি হবে।",
            "partial_payments": "যদি আপনি পূর্ণ পরিমাণ পেমেন্ট করতে না পারেন, তাহলে আংশিক পেমেন্ট ব্যবস্থার বিষয়ে আপনার কাউন্টি ট্যাক্স অফিসের সাথে যোগাযোগ করুন। কিছু কাউন্টি জমা হওয়া জরিমানা এবং সুদ কমাতে আংশিক পেমেন্টের অনুমতি দেয়।"
        }
    },

    PropertyTaxScenario.LEGAL_DISCLAIMER: {
        Language.ENGLISH: {
            "general": "This information is provided for educational purposes only and does not constitute legal advice. For complex property tax matters, please consult with a licensed property tax consultant or attorney.",
            "assessment_guidance": "This professional assessment will help you understand your property tax situation, but for complex legal matters involving appeals or disputes, we may recommend consultation with a property tax attorney.",
            "appeal_disclaimer": "I can guide you through the general appeal process, but specific legal strategies should be discussed with a qualified property tax consultant or attorney.",
            "calculation_disclaimer": "These are estimates based on general Texas property tax procedures. Official calculations should be verified with your county appraisal district."
        },
        Language.HINDI: {
            "general": "यह जानकारी केवल शैक्षिक उद्देश्यों के लिए प्रदान की गई है और कानूनी सलाह नहीं है। जटिल संपत्ति कर मामलों के लिए, कृपया लाइसेंस प्राप्त संपत्ति कर सलाहकार या वकील से सलाह लें।",
            "assessment_guidance": "यह पेशेवर मूल्यांकन आपको अपनी संपत्ति कर स्थिति को समझने में मदद करेगा, लेकिन अपील या विवादों से जुड़े जटिल कानूनी मामलों के लिए, हम संपत्ति कर वकील से सलाह की सिफारिश कर सकते हैं।",
            "appeal_disclaimer": "मैं आपको सामान्य अपील प्रक्रिया के माध्यम से मार्गदर्शन कर सकता हूं, लेकिन विशिष्ट कानूनी रणनीतियों पर योग्य संपत्ति कर सलाहकार या वकील के साथ चर्चा करनी चाहिए।",
            "calculation_disclaimer": "ये सामान्य टेक्सास संपत्ति कर प्रक्रियाओं के आधार पर अनुमान हैं। आधिकारिक गणना आपके काउंटी मूल्यांकन जिले के साथ सत्यापित की जानी चाहिए।"
        },
        Language.BENGALI: {
            "general": "এই তথ্য শুধুমাত্র শিক্ষামূলক উদ্দেশ্যে প্রদান করা হয়েছে এবং এটি আইনি পরামর্শ নয়। জটিল সম্পত্তি কর বিষয়ের জন্য, অনুগ্রহ করে লাইসেন্সপ্রাপ্ত সম্পত্তি কর পরামর্শদাতা বা আইনজীবীর সাথে পরামর্শ করুন।",
            "assessment_guidance": "এই পেশাদার মূল্যায়ন আপনাকে আপনার সম্পত্তি কর পরিস্থিতি বুঝতে সাহায্য করবে, কিন্তু আপিল বা বিরোধের জড়িত জটিল আইনি বিষয়ের জন্য, আমরা সম্পত্তি কর আইনজীবীর সাথে পরামর্শের সুপারিশ করতে পারি।",
            "appeal_disclaimer": "আমি আপনাকে সাধারণ আপিল প্রক্রিয়ার মাধ্যমে গাইড করতে পারি, কিন্তু নির্দিষ্ট আইনি কৌশল যোগ্য সম্পত্তি কর পরামর্শদাতা বা আইনজীবীর সাথে আলোচনা করা উচিত।",
            "calculation_disclaimer": "এগুলি সাধারণ টেক্সাস সম্পত্তি কর পদ্ধতির উপর ভিত্তি করে অনুমান। অফিসিয়াল গণনা আপনার কাউন্টি মূল্যায়ন জেলার সাথে যাচাই করা উচিত।"
        }
    },

    PropertyTaxScenario.BOOKING_CONFIRMATION: {
        Language.ENGLISH: {
            "property_visit": "Perfect! I've booked your property tax assessment for {date} at {address}. Our specialist will visit your property to conduct a thorough evaluation. You'll receive a confirmation shortly with all the details.",
            "office_consultation": "Excellent! Your property tax consultation is scheduled for {date} at our office. Please bring your property documents and recent tax notices. You'll receive a confirmation with the office address and parking details.",
            "payment_online": "Your secure payment link has been sent to your phone. The assessment is confirmed once payment is completed. You'll receive booking details and specialist contact information.",
            "payment_cash": "Your property tax assessment is confirmed for cash payment during the visit. Our specialist will collect payment when they arrive. You'll receive all booking details shortly."
        },
        Language.HINDI: {
            "property_visit": "बहुत बढ़िया! मैंने {date} को {address} पर आपके संपत्ति कर मूल्यांकन को बुक कर दिया है। हमारे विशेषज्ञ एक संपूर्ण मूल्यांकन करने के लिए आपकी संपत्ति का दौरा करेंगे। आपको जल्द ही सभी विवरणों के साथ पुष्टि मिल जाएगी।",
            "office_consultation": "उत्कृष्ट! आपका संपत्ति कर परामर्श {date} को हमारे कार्यालय में निर्धारित है। कृपया अपने संपत्ति दस्तावेज और हाल के कर नोटिस लाएं। आपको कार्यालय का पता और पार्किंग विवरण के साथ पुष्टि मिलेगी।",
            "payment_online": "आपका सुरक्षित भुगतान लिंक आपके फोन पर भेजा गया है। भुगतान पूरा होने पर मूल्यांकन की पुष्टि हो जाती है। आपको बुकिंग विवरण और विशेषज्ञ संपर्क जानकारी मिलेगी।",
            "payment_cash": "आपके संपत्ति कर मूल्यांकन की दौरे के दौरान नकद भुगतान के लिए पुष्टि हो गई है। हमारे विशेषज्ञ पहुंचने पर भुगतान लेंगे। आपको जल्द ही सभी बुकिंग विवरण मिल जाएंगे।"
        },
        Language.BENGALI: {
            "property_visit": "দুর্দান্ত! আমি {date} তে {address}-এ আপনার সম্পত্তি কর মূল্যায়ন বুক করেছি। আমাদের বিশেষজ্ঞ একটি পুঙ্খানুপুঙ্খ মূল্যায়ন পরিচালনা করতে আপনার সম্পত্তি পরিদর্শন করবেন। আপনি শীঘ্রই সমস্ত বিবরণ সহ একটি নিশ্চিতকরণ পাবেন।",
            "office_consultation": "চমৎকার! আপনার সম্পত্তি কর পরামর্শ {date} তে আমাদের অফিসে নির্ধারিত হয়েছে। অনুগ্রহ করে আপনার সম্পত্তির ডকুমেন্ট এবং সাম্প্রতিক কর নোটিস নিয়ে আসুন। আপনি অফিসের ঠিকানা এবং পার্কিং বিবরণ সহ নিশ্চিতকরণ পাবেন।",
            "payment_online": "আপনার নিরাপদ পেমেন্ট লিংক আপনার ফোনে পাঠানো হয়েছে। পেমেন্ট সম্পূর্ণ হলে মূল্যায়ন নিশ্চিত হয়। আপনি বুকিং বিবরণ এবং বিশেষজ্ঞ যোগাযোগের তথ্য পাবেন।",
            "payment_cash": "আপনার সম্পত্তি কর মূল্যায়ন সফরের সময় নগদ পেমেন্টের জন্য নিশ্চিত হয়েছে। আমাদের বিশেষজ্ঞ পৌঁছলে পেমেন্ট নেবেন। আপনি শীঘ্রই সমস্ত বুকিং বিবরণ পাবেন।"
        }
    },

    PropertyTaxScenario.ERROR_HANDLING: {
        Language.ENGLISH: {
            "service_unavailable": "I apologize, but that service isn't available in your area at the moment. Let me connect you with a specialist who can help with alternative options.",
            "booking_failed": "I encountered an issue while processing your booking. Let me try again or connect you with our support team to ensure your assessment gets scheduled properly.",
            "payment_issue": "There seems to be an issue with the payment processing. Would you like to try a different payment method, or shall I arrange for cash payment during the visit?",
            "unclear_request": "I want to make sure I understand your property tax needs correctly. Could you tell me more about what specific help you're looking for today?"
        },
        Language.HINDI: {
            "service_unavailable": "मुझे खुशी है, लेकिन वह सेवा आपके क्षेत्र में इस समय उपलब्ध नहीं है। मैं आपको एक विशेषज्ञ से जोड़ता हूं जो वैकल्पिक विकल्पों में मदद कर सकता है।",
            "booking_failed": "आपकी बुकिंग को प्रोसेस करते समय मुझे एक समस्या आई है। मैं फिर से कोशिश करता हूं या आपको हमारी सहायता टीम से जोड़ता हूं ताकि आपका मूल्यांकन ठीक से निर्धारित हो सके।",
            "payment_issue": "भुगतान प्रसंस्करण में कोई समस्या लग रही है। क्या आप एक अलग भुगतान विधि आजमाना चाहेंगे, या मैं दौरे के दौरान नकद भुगतान की व्यवस्था करूं?",
            "unclear_request": "मैं यह सुनिश्चित करना चाहता हूं कि मैं आपकी संपत्ति कर की जरूरतों को सही तरीके से समझूं। क्या आप मुझे बता सकते हैं कि आज आप किस विशिष्ट सहायता की तलाश कर रहे हैं?"
        },
        Language.BENGALI: {
            "service_unavailable": "আমি দুঃখিত, কিন্তু সেই সেবাটি আপাতত আপনার এলাকায় উপলব্ধ নেই। আমি আপনাকে একজন বিশেষজ্ঞের সাথে সংযুক্ত করি যিনি বিকল্প অপশনে সাহায্য করতে পারেন।",
            "booking_failed": "আপনার বুকিং প্রক্রিয়া করার সময় আমি একটি সমস্যার সম্মুখীন হয়েছি। আমি আবার চেষ্টা করি বা আপনাকে আমাদের সাপোর্ট টিমের সাথে সংযুক্ত করি যাতে আপনার মূল্যায়ন সঠিকভাবে নির্ধারিত হয়।",
            "payment_issue": "পেমেন্ট প্রক্রিয়াকরণে কোনো সমস্যা আছে বলে মনে হচ্ছে। আপনি কি একটি ভিন্ন পেমেন্ট পদ্ধতি চেষ্টা করতে চান, নাকি আমি সফরের সময় নগদ পেমেন্টের ব্যবস্থা করব?",
            "unclear_request": "আমি নিশ্চিত করতে চাই যে আমি আপনার সম্পত্তি কর প্রয়োজন সঠিকভাবে বুঝতে পারছি। আপনি কি আমাকে আরও বলতে পারেন যে আজ আপনি কী নির্দিষ্ট সাহায্য খুঁজছেন?"
        }
    }
}

def get_template(scenario: PropertyTaxScenario, language: Language, template_type: str = "initial") -> str:
    """
    Get a response template for a specific scenario and language.

    Args:
        scenario: The property tax scenario
        language: The target language
        template_type: The specific template type (e.g., 'initial', 'with_name', etc.)

    Returns:
        The formatted template string
    """
    try:
        scenario_templates = PROPERTY_TAX_TEMPLATES.get(scenario, {})
        language_templates = scenario_templates.get(language, {})

        if isinstance(language_templates, dict):
            template = language_templates.get(template_type, language_templates.get("initial", ""))
        else:
            template = language_templates

        if not template:
            # Fallback to English if template not found
            english_templates = scenario_templates.get(Language.ENGLISH, {})
            if isinstance(english_templates, dict):
                template = english_templates.get(template_type, english_templates.get("initial", ""))
            else:
                template = english_templates

        return template or "I'm here to help you with your property tax needs."

    except Exception as e:
        logger.error(f"Error getting template: {e}")
        return "I'm here to help you with your property tax needs."

def detect_language_from_message(message: str) -> Language:
    """
    Detect language from message content.

    Args:
        message: The user message

    Returns:
        Detected language
    """
    # Simple language detection based on character patterns
    if any(ord(char) >= 0x900 and ord(char) <= 0x97F for char in message):  # Devanagari
        return Language.HINDI
    elif any(ord(char) >= 0x980 and ord(char) <= 0x9FF for char in message):  # Bengali
        return Language.BENGALI
    elif any(ord(char) >= 0xB80 and ord(char) <= 0xBFF for char in message):  # Tamil
        return Language.TAMIL
    elif any(ord(char) >= 0xC00 and ord(char) <= 0xC7F for char in message):  # Telugu
        return Language.TELUGU
    elif any(ord(char) >= 0x900 and ord(char) <= 0x97F for char in message):  # Marathi (Devanagari)
        return Language.MARATHI
    elif any(ord(char) >= 0xA80 and ord(char) <= 0xAFF for char in message):  # Gujarati
        return Language.GUJARATI
    elif any(ord(char) >= 0xC80 and ord(char) <= 0xCFF for char in message):  # Kannada
        return Language.KANNADA
    elif any(ord(char) >= 0xD00 and ord(char) <= 0xD7F for char in message):  # Malayalam
        return Language.MALAYALAM
    elif any(ord(char) >= 0xA00 and ord(char) <= 0xA7F for char in message):  # Punjabi
        return Language.PUNJABI
    else:
        return Language.ENGLISH

def format_response_with_context(template: str, context: Dict[str, Any]) -> str:
    """
    Format a response template with context variables.

    Args:
        template: The template string
        context: Context variables for formatting

    Returns:
        Formatted response string
    """
    try:
        return template.format(**context)
    except KeyError as e:
        logger.warning(f"Missing context variable: {e}")
        return template
    except Exception as e:
        logger.error(f"Error formatting template: {e}")
        return template

def get_scenario_from_message(message: str) -> PropertyTaxScenario:
    """
    Determine the most likely scenario from a user message.

    Args:
        message: The user message

    Returns:
        The most likely scenario
    """
    message_lower = message.lower()

    # Assessment-related keywords
    if any(word in message_lower for word in ['assessment', 'value', 'appraisal', 'valuation', 'too high', 'increased']):
        return PropertyTaxScenario.ASSESSMENT_INQUIRY

    # Appeal-related keywords
    if any(word in message_lower for word in ['appeal', 'dispute', 'challenge', 'disagree', 'arb', 'hearing']):
        return PropertyTaxScenario.APPEAL_PROCESS

    # Exemption-related keywords
    if any(word in message_lower for word in ['exemption', 'homestead', 'senior', 'disability', 'veteran', 'reduce']):
        return PropertyTaxScenario.EXEMPTION_QUALIFICATION

    # Payment-related keywords
    if any(word in message_lower for word in ['payment', 'pay', 'installment', 'deadline', 'late', 'penalty']):
        return PropertyTaxScenario.PAYMENT_OPTIONS

    # Deadline-related keywords
    if any(word in message_lower for word in ['deadline', 'due', 'when', 'timeline', 'date']):
        return PropertyTaxScenario.DEADLINE_INQUIRY

    # Documentation-related keywords
    if any(word in message_lower for word in ['document', 'paperwork', 'form', 'evidence', 'proof']):
        return PropertyTaxScenario.DOCUMENTATION_REQUIRED

    # Greeting patterns
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'namaste', 'namaskar']):
        return PropertyTaxScenario.GREETING

    # Default to assessment inquiry for property tax questions
    return PropertyTaxScenario.ASSESSMENT_INQUIRY

# Quick access functions for common scenarios
def get_greeting_template(language: Language, name: str = None) -> str:
    """Get a greeting template in the specified language."""
    template_type = "with_name" if name else "initial"
    template = get_template(PropertyTaxScenario.GREETING, language, template_type)
    if name and "{name}" in template:
        return template.format(name=name)
    return template

def get_legal_disclaimer(language: Language, disclaimer_type: str = "general") -> str:
    """Get a legal disclaimer in the specified language."""
    return get_template(PropertyTaxScenario.LEGAL_DISCLAIMER, language, disclaimer_type)

def get_error_message(language: Language, error_type: str = "unclear_request") -> str:
    """Get an error handling message in the specified language."""
    return get_template(PropertyTaxScenario.ERROR_HANDLING, language, error_type)

# Export key functions and classes
__all__ = [
    'PropertyTaxScenario',
    'Language',
    'get_template',
    'detect_language_from_message',
    'format_response_with_context',
    'get_scenario_from_message',
    'get_greeting_template',
    'get_legal_disclaimer',
    'get_error_message',
    'PROPERTY_TAX_TEMPLATES'
]