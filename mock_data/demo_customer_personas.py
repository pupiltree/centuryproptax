"""
Demo Customer Personas for Property Tax AI Assistant
Realistic customer profiles representing diverse use cases and demographics for demo scenarios
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import random

class PersonaType(Enum):
    """Types of customer personas"""
    FIRST_TIME_HOMEOWNER = "first_time_homeowner"
    EXPERIENCED_MULTI_PROPERTY = "experienced_multi_property"
    SENIOR_CITIZEN = "senior_citizen"
    COMMERCIAL_BUSINESS_OWNER = "commercial_business_owner"
    AGRICULTURAL_PROPERTY_OWNER = "agricultural_property_owner"
    PROPERTY_IN_DISPUTE = "property_in_dispute"

class TechComfortLevel(Enum):
    """Technology comfort levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class CommunicationStyle(Enum):
    """Communication preferences"""
    FORMAL = "formal"
    CASUAL = "casual"
    DIRECT = "direct"
    DETAILED = "detailed"

@dataclass
class CustomerPersona:
    """Comprehensive customer persona for demo scenarios"""
    persona_id: str
    persona_type: PersonaType
    name: str
    age: int
    occupation: str
    tech_comfort: TechComfortLevel
    communication_style: CommunicationStyle
    primary_language: str
    properties_owned: List[Dict[str, Any]]
    typical_concerns: List[str]
    background_story: str
    demo_conversation_starters: List[str]
    expected_interaction_patterns: List[str]
    escalation_triggers: List[str]
    special_considerations: List[str]

class DemoCustomerPersonas:
    """Demo customer persona manager with realistic profiles"""

    def __init__(self):
        self.personas = self._create_personas()

    def _create_personas(self) -> Dict[str, CustomerPersona]:
        """Create comprehensive customer personas for demo scenarios"""
        personas = {}

        # First-Time Homeowner Personas
        personas.update(self._create_first_time_homeowner_personas())

        # Experienced Multi-Property Owner Personas
        personas.update(self._create_multi_property_personas())

        # Senior Citizen Personas
        personas.update(self._create_senior_citizen_personas())

        # Commercial Business Owner Personas
        personas.update(self._create_commercial_personas())

        # Agricultural Property Owner Personas
        personas.update(self._create_agricultural_personas())

        # Property in Dispute Personas
        personas.update(self._create_dispute_personas())

        return personas

    def _create_first_time_homeowner_personas(self) -> Dict[str, CustomerPersona]:
        """Create first-time homeowner personas"""
        personas = {}

        # Young Professional - Tech Savvy
        personas["sarah_first_time"] = CustomerPersona(
            persona_id="sarah_first_time",
            persona_type=PersonaType.FIRST_TIME_HOMEOWNER,
            name="Sarah Chen",
            age=28,
            occupation="Software Engineer",
            tech_comfort=TechComfortLevel.HIGH,
            communication_style=CommunicationStyle.DIRECT,
            primary_language="English",
            properties_owned=[
                {
                    "address": "123 Starter Home Lane, Austin",
                    "county": "Travis",
                    "property_type": "residential",
                    "assessed_value": 285000,
                    "purchase_date": "2024-03-15",
                    "purchase_price": 290000,
                    "homestead_exemption": False,  # Needs to apply
                    "monthly_payment": 2100
                }
            ],
            typical_concerns=[
                "Understanding property tax process",
                "Homestead exemption application",
                "Why assessment differs from purchase price",
                "When taxes are due",
                "Online payment options"
            ],
            background_story="Sarah is a software engineer who just bought her first home in Austin. She's tech-savvy but completely new to property taxes. She wants clear, efficient information and prefers digital interactions.",
            demo_conversation_starters=[
                "I just bought my first house and got a tax bill. Can you explain what this means?",
                "My realtor mentioned something about a homestead exemption. Do I need that?",
                "Can I pay my property taxes online like everything else?",
                "Why is my assessed value different from what I paid for the house?"
            ],
            expected_interaction_patterns=[
                "Asks direct, specific questions",
                "Prefers step-by-step instructions",
                "Wants to understand the 'why' behind processes",
                "Comfortable with digital processes",
                "Appreciates efficiency and clarity"
            ],
            escalation_triggers=[
                "Complex legal questions about property rights",
                "Disputes requiring legal interpretation",
                "Issues with mortgage company escrow"
            ],
            special_considerations=[
                "First-time experience - needs extra context",
                "Tech-savvy - can handle complex online processes",
                "Time-conscious - values efficiency",
                "Detail-oriented - wants comprehensive understanding"
            ]
        )

        # Young Family - Moderate Tech Comfort
        personas["mike_young_family"] = CustomerPersona(
            persona_id="mike_young_family",
            persona_type=PersonaType.FIRST_TIME_HOMEOWNER,
            name="Mike and Jessica Rodriguez",
            age=32,
            occupation="Teacher (Mike), Nurse (Jessica)",
            tech_comfort=TechComfortLevel.MEDIUM,
            communication_style=CommunicationStyle.CASUAL,
            primary_language="English/Spanish",
            properties_owned=[
                {
                    "address": "456 Family Circle, San Antonio",
                    "county": "Bexar",
                    "property_type": "residential",
                    "assessed_value": 195000,
                    "purchase_date": "2023-08-20",
                    "purchase_price": 185000,
                    "homestead_exemption": True,
                    "monthly_payment": 1650
                }
            ],
            typical_concerns=[
                "Managing tight budget with property taxes",
                "Payment plan options",
                "Understanding exemptions",
                "Impact of tax increases on family budget",
                "Spanish language support needs"
            ],
            background_story="Mike and Jessica are a young family with two small children. They're both public service employees on tight budgets and need affordable payment options. They occasionally prefer Spanish for complex explanations.",
            demo_conversation_starters=[
                "Our property taxes went up and it's straining our budget. What options do we have?",
                "Can we pay our taxes in installments? We can't afford the full amount at once.",
                "¿Pueden explicarme las opciones de pago en español?",
                "We're both teachers - are there any special programs for public service workers?"
            ],
            expected_interaction_patterns=[
                "Budget-conscious decision making",
                "Asks about payment flexibility",
                "May switch between English and Spanish",
                "Values personal, empathetic service",
                "Concerned about family financial stability"
            ],
            escalation_triggers=[
                "Complex financial hardship situations",
                "Need for Spanish-speaking human agent",
                "Legal advice about property protection"
            ],
            special_considerations=[
                "Budget constraints - emphasize affordable options",
                "Bilingual needs - offer Spanish support",
                "Family priorities - understand time constraints",
                "Public service background - may qualify for special programs"
            ]
        )

        return personas

    def _create_multi_property_personas(self) -> Dict[str, CustomerPersona]:
        """Create experienced multi-property owner personas"""
        personas = {}

        # Real Estate Investor
        personas["david_investor"] = CustomerPersona(
            persona_id="david_investor",
            persona_type=PersonaType.EXPERIENCED_MULTI_PROPERTY,
            name="David Park",
            age=45,
            occupation="Real Estate Investor",
            tech_comfort=TechComfortLevel.HIGH,
            communication_style=CommunicationStyle.DIRECT,
            primary_language="English",
            properties_owned=[
                {
                    "address": "789 Investment Ave, Dallas",
                    "county": "Dallas",
                    "property_type": "residential_rental",
                    "assessed_value": 245000,
                    "purchase_date": "2019-05-12",
                    "rental_income": 2200
                },
                {
                    "address": "321 Duplex Drive, Dallas",
                    "county": "Dallas",
                    "property_type": "duplex",
                    "assessed_value": 285000,
                    "purchase_date": "2020-11-08",
                    "rental_income": 2800
                },
                {
                    "address": "555 Commercial St, Plano",
                    "county": "Collin",
                    "property_type": "small_commercial",
                    "assessed_value": 425000,
                    "purchase_date": "2021-03-22",
                    "rental_income": 4500
                }
            ],
            typical_concerns=[
                "Portfolio-level tax management",
                "Bulk payment processing",
                "Investment property tax implications",
                "Appeal strategies for multiple properties",
                "Tax planning and projections"
            ],
            background_story="David is an experienced real estate investor with a growing portfolio. He needs efficient, business-focused solutions and values time-saving tools for managing multiple properties.",
            demo_conversation_starters=[
                "I have several investment properties. Can I manage all their taxes in one place?",
                "What's the most efficient way to pay taxes on multiple properties?",
                "I think my commercial property assessment is too high. How do I appeal it?",
                "Can you show me the tax implications of my entire portfolio?"
            ],
            expected_interaction_patterns=[
                "Business-focused questions",
                "Seeks efficiency and time savings",
                "Comfortable with complex financial concepts",
                "Values comprehensive reporting",
                "Interested in tax optimization strategies"
            ],
            escalation_triggers=[
                "Complex commercial property appeals",
                "Tax planning requiring professional advice",
                "Legal issues affecting multiple properties"
            ],
            special_considerations=[
                "Business context - efficiency is priority",
                "Multiple properties - needs consolidated views",
                "Investment focus - interested in ROI implications",
                "Experienced - can handle complex processes"
            ]
        )

        return personas

    def _create_senior_citizen_personas(self) -> Dict[str, CustomerPersona]:
        """Create senior citizen personas"""
        personas = {}

        # Retired Professional
        personas["mary_retired"] = CustomerPersona(
            persona_id="mary_retired",
            persona_type=PersonaType.SENIOR_CITIZEN,
            name="Mary Thompson",
            age=72,
            occupation="Retired Teacher",
            tech_comfort=TechComfortLevel.LOW,
            communication_style=CommunicationStyle.DETAILED,
            primary_language="English",
            properties_owned=[
                {
                    "address": "888 Retirement Lane, Houston",
                    "county": "Harris",
                    "property_type": "residential",
                    "assessed_value": 285000,
                    "purchase_date": "1985-06-15",
                    "purchase_price": 85000,
                    "homestead_exemption": True,
                    "senior_exemption": True,
                    "fixed_income": True
                }
            ],
            typical_concerns=[
                "Senior exemptions and discounts",
                "Fixed income payment challenges",
                "Tax deferral programs",
                "Foreclosure protections for seniors",
                "Traditional payment methods"
            ],
            background_story="Mary is a retired teacher living on a fixed income. She's lived in her home for nearly 40 years and sometimes struggles with technology. She needs patient, clear explanations and traditional service options.",
            demo_conversation_starters=[
                "I'm 72 and on a fixed income. Are there special programs for seniors like me?",
                "My property taxes keep going up but my income doesn't. What can I do?",
                "I prefer to pay by check or in person. Is that still possible?",
                "Can you explain the senior exemption? I'm not sure if I have it."
            ],
            expected_interaction_patterns=[
                "Prefers detailed explanations",
                "May need concepts repeated or clarified",
                "Appreciates patient, respectful service",
                "Prefers traditional interaction methods",
                "Concerned about financial security"
            ],
            escalation_triggers=[
                "Complex technology requirements",
                "Financial hardship situations",
                "Need for in-person assistance"
            ],
            special_considerations=[
                "Senior-specific programs and protections",
                "Lower tech comfort - offer alternatives",
                "Fixed income - emphasize affordable options",
                "May need extra time and patience"
            ]
        )

        return personas

    def _create_commercial_personas(self) -> Dict[str, CustomerPersona]:
        """Create commercial business owner personas"""
        personas = {}

        # Small Business Owner
        personas["robert_business"] = CustomerPersona(
            persona_id="robert_business",
            persona_type=PersonaType.COMMERCIAL_BUSINESS_OWNER,
            name="Robert Chen",
            age=38,
            occupation="Restaurant Owner",
            tech_comfort=TechComfortLevel.MEDIUM,
            communication_style=CommunicationStyle.DIRECT,
            primary_language="English",
            properties_owned=[
                {
                    "address": "123 Restaurant Row, Austin",
                    "county": "Travis",
                    "property_type": "commercial",
                    "assessed_value": 650000,
                    "purchase_date": "2020-01-15",
                    "business_type": "restaurant",
                    "employees": 15
                }
            ],
            typical_concerns=[
                "Commercial property tax rates",
                "Business impact of tax increases",
                "Available business incentives",
                "Tax planning for business expenses",
                "Dispute resolution for commercial assessments"
            ],
            background_story="Robert owns a successful restaurant and understands the business impact of property taxes. He needs clear information about commercial tax implications and available incentives.",
            demo_conversation_starters=[
                "My restaurant's property taxes are a big expense. Are there any business incentives available?",
                "How do commercial property tax rates compare to residential?",
                "My assessment seems high for a restaurant. How do I dispute it?",
                "Can property taxes be deducted as a business expense?"
            ],
            expected_interaction_patterns=[
                "Business-focused perspective",
                "Interested in cost management",
                "Values quick, actionable information",
                "Asks about business implications",
                "May need to discuss with accountant"
            ],
            escalation_triggers=[
                "Complex commercial assessment disputes",
                "Business tax planning questions",
                "Legal issues affecting business operations"
            ],
            special_considerations=[
                "Business impact focus",
                "May need accounting-friendly documentation",
                "Time-sensitive - busy schedule",
                "Interested in cost optimization"
            ]
        )

        return personas

    def _create_agricultural_personas(self) -> Dict[str, CustomerPersona]:
        """Create agricultural property owner personas"""
        personas = {}

        # Farmer/Rancher
        personas["john_farmer"] = CustomerPersona(
            persona_id="john_farmer",
            persona_type=PersonaType.AGRICULTURAL_PROPERTY_OWNER,
            name="John Williams",
            age=55,
            occupation="Cattle Rancher",
            tech_comfort=TechComfortLevel.LOW,
            communication_style=CommunicationStyle.FORMAL,
            primary_language="English",
            properties_owned=[
                {
                    "address": "Rural Route 1, Farm to Market 2325",
                    "county": "Williamson",
                    "property_type": "agricultural",
                    "assessed_value": 450000,
                    "acres": 125,
                    "agricultural_exemption": True,
                    "use_type": "cattle_grazing",
                    "purchase_date": "1995-03-10"
                }
            ],
            typical_concerns=[
                "Agricultural exemption maintenance",
                "Land use changes affecting taxes",
                "Drought impact on assessments",
                "Family farm succession planning",
                "Traditional payment and communication methods"
            ],
            background_story="John is a third-generation cattle rancher who values traditional business practices. He understands agriculture but needs help navigating property tax regulations and exemptions.",
            demo_conversation_starters=[
                "I've had my agricultural exemption for years. How do I make sure I keep it?",
                "What happens to my farm taxes if I have to change how I use the land?",
                "The drought hurt my cattle operation. Does that affect my property taxes?",
                "I want to pass the farm to my son. How do taxes work with that?"
            ],
            expected_interaction_patterns=[
                "Values traditional, respectful communication",
                "Focuses on long-term family considerations",
                "Asks practical, land-use focused questions",
                "May need agricultural regulations explained",
                "Prefers phone or in-person communication"
            ],
            escalation_triggers=[
                "Complex agricultural exemption issues",
                "Succession planning questions",
                "Land use regulation conflicts"
            ],
            special_considerations=[
                "Agricultural exemption expertise required",
                "Generational/family perspective important",
                "Traditional communication preferences",
                "Practical, land-focused approach"
            ]
        )

        return personas

    def _create_dispute_personas(self) -> Dict[str, CustomerPersona]:
        """Create property in dispute personas"""
        personas = {}

        # Property in Appeal Process
        personas["lisa_dispute"] = CustomerPersona(
            persona_id="lisa_dispute",
            persona_type=PersonaType.PROPERTY_IN_DISPUTE,
            name="Lisa Anderson",
            age=42,
            occupation="Marketing Manager",
            tech_comfort=TechComfortLevel.HIGH,
            communication_style=CommunicationStyle.DETAILED,
            primary_language="English",
            properties_owned=[
                {
                    "address": "456 Disputed Value St, Plano",
                    "county": "Collin",
                    "property_type": "residential",
                    "assessed_value": 485000,
                    "market_value_estimate": 425000,
                    "purchase_date": "2021-05-20",
                    "purchase_price": 430000,
                    "appeal_status": "in_progress",
                    "appeal_filed_date": "2024-04-15"
                }
            ],
            typical_concerns=[
                "Appeal process status and timeline",
                "Evidence requirements for appeals",
                "Understanding appraisal methodologies",
                "Appeal hearing preparation",
                "Rights during appeal process"
            ],
            background_story="Lisa is actively appealing her property assessment, believing it's overvalued. She's detail-oriented and wants to understand every aspect of the appeal process.",
            demo_conversation_starters=[
                "I filed an appeal three weeks ago. How can I check the status?",
                "What evidence do I need to prove my house is overvalued?",
                "My informal conference is next week. What should I expect?",
                "Can you explain how the appraiser came up with my assessment?"
            ],
            expected_interaction_patterns=[
                "Seeks detailed process information",
                "Asks for status updates and timelines",
                "Wants to understand technical aspects",
                "Prepared and organized approach",
                "May express frustration with process"
            ],
            escalation_triggers=[
                "Complex appeal strategy questions",
                "Formal hearing preparation needs",
                "Legal questions about appeal rights"
            ],
            special_considerations=[
                "Currently in appeal process - needs status info",
                "Detail-oriented - provide comprehensive information",
                "May be stressed about outcome",
                "Wants to understand technical details"
            ]
        )

        return personas

    def get_persona_by_id(self, persona_id: str) -> Optional[CustomerPersona]:
        """Get a specific persona by ID"""
        return self.personas.get(persona_id)

    def get_personas_by_type(self, persona_type: PersonaType) -> List[CustomerPersona]:
        """Get all personas of a specific type"""
        return [persona for persona in self.personas.values() if persona.persona_type == persona_type]

    def get_personas_by_tech_comfort(self, tech_comfort: TechComfortLevel) -> List[CustomerPersona]:
        """Get personas by technology comfort level"""
        return [persona for persona in self.personas.values() if persona.tech_comfort == tech_comfort]

    def get_random_persona(self) -> CustomerPersona:
        """Get a random persona for spontaneous demos"""
        return random.choice(list(self.personas.values()))

    def get_all_personas(self) -> List[CustomerPersona]:
        """Get all available customer personas"""
        return list(self.personas.values())

    def get_persona_conversation_starter(self, persona_id: str) -> Optional[str]:
        """Get a random conversation starter for a specific persona"""
        persona = self.get_persona_by_id(persona_id)
        if persona and persona.demo_conversation_starters:
            return random.choice(persona.demo_conversation_starters)
        return None

    def get_personas_summary(self) -> Dict[str, Any]:
        """Get summary of all personas for demo planning"""
        return {
            "total_personas": len(self.personas),
            "by_type": {
                persona_type.value: len(self.get_personas_by_type(persona_type))
                for persona_type in PersonaType
            },
            "by_tech_comfort": {
                tech_level.value: len(self.get_personas_by_tech_comfort(tech_level))
                for tech_level in TechComfortLevel
            },
            "persona_names": [persona.name for persona in self.personas.values()],
            "available_languages": list(set(persona.primary_language for persona in self.personas.values()))
        }

# Global demo personas manager
demo_personas = DemoCustomerPersonas()