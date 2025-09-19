"""
Exemption Application Scenarios for Demo Environment
Realistic conversation flows for property tax exemption applications and eligibility
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import random
from datetime import datetime, timedelta

from agents.core.conversation_flows import ConversationStage, PropertyTaxConcern
from mock_data.property_records import get_sample_properties

class ExemptionType(Enum):
    """Types of property tax exemptions"""
    HOMESTEAD = "homestead"
    SENIOR = "senior"
    DISABILITY = "disability"
    VETERAN = "veteran"
    AGRICULTURAL = "agricultural"
    FREEPORT = "freeport"
    HISTORIC = "historic"
    SOLAR = "solar"

class ApplicationStage(Enum):
    """Stages of exemption application process"""
    ELIGIBILITY_CHECK = "eligibility_check"
    APPLICATION_PROCESS = "application_process"
    DOCUMENTATION = "documentation"
    STATUS_CHECK = "status_check"
    RENEWAL = "renewal"
    APPEAL = "appeal"

@dataclass
class ExemptionApplicationScenario:
    """Exemption application scenario with realistic conversation flow"""
    scenario_id: str
    exemption_type: ExemptionType
    application_stage: ApplicationStage
    customer_persona: str
    property_address: str
    county: str
    exemption_value: float
    conversation_flow: List[Dict[str, str]]
    expected_response_elements: List[str]
    demo_notes: str
    eligibility_requirements: List[str]
    required_documents: List[str]

class ExemptionApplicationDemoScenarios:
    """Demo scenarios for property tax exemption applications"""

    def __init__(self):
        self.properties = get_sample_properties()
        self.scenarios = self._generate_scenarios()

    def _generate_scenarios(self) -> List[ExemptionApplicationScenario]:
        """Generate realistic exemption application scenarios"""
        scenarios = []

        # Homestead Exemption Scenarios
        scenarios.extend(self._create_homestead_scenarios())

        # Senior Exemption Scenarios
        scenarios.extend(self._create_senior_scenarios())

        # Disability Exemption Scenarios
        scenarios.extend(self._create_disability_scenarios())

        # Veteran Exemption Scenarios
        scenarios.extend(self._create_veteran_scenarios())

        # Agricultural Exemption Scenarios
        scenarios.extend(self._create_agricultural_scenarios())

        # Solar Exemption Scenarios
        scenarios.extend(self._create_solar_scenarios())

        return scenarios

    def _create_homestead_scenarios(self) -> List[ExemptionApplicationScenario]:
        """Create homestead exemption application scenarios"""
        scenarios = []

        # Scenario 1: New homeowner applying for homestead exemption
        scenarios.append(ExemptionApplicationScenario(
            scenario_id="exemption_001",
            exemption_type=ExemptionType.HOMESTEAD,
            application_stage=ApplicationStage.ELIGIBILITY_CHECK,
            customer_persona="new_homeowner",
            property_address="123 New Home Drive, Austin",
            county="Travis",
            exemption_value=100000.00,
            conversation_flow=[
                {
                    "user": "I just bought my first house and heard about a homestead exemption. Do I qualify and how much will it save me?",
                    "ai": "Congratulations on your new home! Yes, you likely qualify for the homestead exemption in Travis County. If this is your primary residence as of January 1st, you can receive a $100,000 exemption, which will save you approximately $2,700 annually in property taxes based on current rates.",
                    "demo_action": "homestead_eligibility_calculation"
                },
                {
                    "user": "What do I need to prove it's my primary residence?",
                    "ai": "You'll need to provide documentation showing this is where you live on January 1st. Acceptable documents include: driver's license with this address, voter registration, utility bills, or bank statements. The key is proving you live here as your main home, not as a rental or second property.",
                    "demo_action": "residency_documentation_requirements"
                },
                {
                    "user": "When do I need to apply? Is there a deadline?",
                    "ai": "The deadline to apply is April 30th for the current tax year. Since you just moved in, you should apply as soon as possible. The good news is that if approved, the exemption will apply to this year's taxes. You can apply online, by mail, or in person at the Travis County Appraisal District.",
                    "demo_action": "application_deadline_info"
                },
                {
                    "user": "Can you help me start the application process?",
                    "ai": "Absolutely! I can guide you through the online application. You'll need your property account number, driver's license, and one utility bill. The application takes about 10 minutes to complete. Would you like me to walk you through it step by step or provide you with the direct link?",
                    "demo_action": "application_assistance_offer"
                }
            ],
            expected_response_elements=[
                "eligibility_confirmation",
                "exemption_amount",
                "annual_savings_calculation",
                "residency_requirements",
                "application_deadline",
                "application_process_assistance"
            ],
            eligibility_requirements=[
                "Property must be primary residence",
                "Must own property as of January 1st",
                "Must be individual owner (not corporation)",
                "Must file application by April 30th"
            ],
            required_documents=[
                "Property deed or closing documents",
                "Driver's license with property address",
                "Utility bill or bank statement",
                "Completed application form"
            ],
            demo_notes="Shows basic homestead exemption eligibility and application process"
        ))

        # Scenario 2: Homeowner checking exemption status
        scenarios.append(ExemptionApplicationScenario(
            scenario_id="exemption_002",
            exemption_type=ExemptionType.HOMESTEAD,
            application_stage=ApplicationStage.STATUS_CHECK,
            customer_persona="existing_homeowner",
            property_address="456 Established Street, Dallas",
            county="Dallas",
            exemption_value=100000.00,
            conversation_flow=[
                {
                    "user": "I applied for a homestead exemption a few weeks ago. How can I check if it was approved?",
                    "ai": "I can help you check your exemption status. For your property at 456 Established Street in Dallas, let me look up your application. I see that your homestead exemption application was approved on March 15th and is active for this tax year. Your taxable value has been reduced by $100,000.",
                    "demo_action": "exemption_status_lookup"
                },
                {
                    "user": "Great! Will this automatically continue next year or do I need to reapply?",
                    "ai": "Good news - the homestead exemption automatically renews each year as long as you continue to use the property as your primary residence. You don't need to reapply. However, you must notify the appraisal district if you sell the property or it's no longer your primary residence.",
                    "demo_action": "renewal_process_explanation"
                },
                {
                    "user": "What if I want to rent out part of my house? Does that affect my exemption?",
                    "ai": "Renting out part of your house (like a room or garage apartment) typically doesn't affect your homestead exemption as long as you still live in the house as your primary residence. However, if you convert it to a full rental property and move out, you would lose the exemption. The key is that you must continue living there.",
                    "demo_action": "partial_rental_impact_explanation"
                }
            ],
            expected_response_elements=[
                "exemption_status_confirmation",
                "approval_date",
                "automatic_renewal_info",
                "notification_requirements",
                "partial_rental_guidance"
            ],
            eligibility_requirements=[
                "Continued primary residence use",
                "Notification of status changes",
                "Compliance with residence requirements"
            ],
            required_documents=[
                "No additional documents for renewal",
                "Change notification if applicable"
            ],
            demo_notes="Demonstrates exemption status checking and renewal information"
        ))

        return scenarios

    def _create_senior_scenarios(self) -> List[ExemptionApplicationScenario]:
        """Create senior citizen exemption scenarios"""
        scenarios = []

        # Scenario 3: Senior citizen applying for additional exemptions
        scenarios.append(ExemptionApplicationScenario(
            scenario_id="exemption_003",
            exemption_type=ExemptionType.SENIOR,
            application_stage=ApplicationStage.ELIGIBILITY_CHECK,
            customer_persona="senior_citizen",
            property_address="789 Senior Circle, Houston",
            county="Harris",
            exemption_value=160000.00,  # $100k homestead + $60k senior
            conversation_flow=[
                {
                    "user": "I just turned 65 last month. Are there additional property tax exemptions available for seniors?",
                    "ai": "Congratulations on your 65th birthday! Yes, in Harris County, you're now eligible for an additional senior exemption. On top of your existing $100,000 homestead exemption, you can receive an additional $60,000 senior exemption, totaling $160,000 in exemptions.",
                    "demo_action": "senior_exemption_eligibility"
                },
                {
                    "user": "How much will this save me in taxes?",
                    "ai": "The additional $60,000 senior exemption will save you approximately $1,650 per year based on Harris County's current tax rates. Combined with your homestead exemption, your total annual savings is about $4,400 compared to having no exemptions.",
                    "demo_action": "senior_savings_calculation"
                },
                {
                    "user": "What do I need to apply? I already have the homestead exemption.",
                    "ai": "Since you already have the homestead exemption, you just need to apply for the additional senior exemption. You'll need proof of age (driver's license or birth certificate) and to confirm this is still your primary residence. The application can be done online or by mail, and there's no fee.",
                    "demo_action": "senior_application_requirements"
                },
                {
                    "user": "Are there any other senior benefits I should know about?",
                    "ai": "Yes! As a senior in Texas, you also have special protections: you cannot lose your home for unpaid property taxes if you're 65 or older, you may qualify for tax deferrals if you meet income requirements, and you have additional appeal rights. Would you like information about any of these programs?",
                    "demo_action": "additional_senior_benefits"
                }
            ],
            expected_response_elements=[
                "senior_exemption_amount",
                "combined_exemption_total",
                "annual_savings_calculation",
                "age_verification_requirements",
                "additional_senior_protections"
            ],
            eligibility_requirements=[
                "Must be 65 years or older on January 1st",
                "Must have homestead exemption",
                "Property must be primary residence"
            ],
            required_documents=[
                "Driver's license or birth certificate",
                "Proof of age showing 65+",
                "Confirmation of primary residence"
            ],
            demo_notes="Shows senior citizen exemption benefits and protections"
        ))

        return scenarios

    def _create_disability_scenarios(self) -> List[ExemptionApplicationScenario]:
        """Create disability exemption scenarios"""
        scenarios = []

        # Scenario 4: Disabled veteran applying for exemptions
        scenarios.append(ExemptionApplicationScenario(
            scenario_id="exemption_004",
            exemption_type=ExemptionType.DISABILITY,
            application_stage=ApplicationStage.APPLICATION_PROCESS,
            customer_persona="disabled_veteran",
            property_address="321 Veterans Way, Fort Worth",
            county="Tarrant",
            exemption_value=160000.00,  # $100k homestead + $60k disability
            conversation_flow=[
                {
                    "user": "I'm a disabled veteran with a 70% disability rating. What property tax exemptions am I eligible for?",
                    "ai": "Thank you for your service. As a disabled veteran with a 70% rating in Tarrant County, you're eligible for significant exemptions: the standard $100,000 homestead exemption plus an additional $60,000 disability exemption, totaling $160,000 in tax relief.",
                    "demo_action": "veteran_disability_exemption_overview"
                },
                {
                    "user": "What documentation do I need to prove my disability rating?",
                    "ai": "You'll need your VA disability rating letter showing your current percentage rating. This official letter from the Department of Veterans Affairs is the primary document required. If you don't have a recent copy, you can request one from the VA or download it from the VA website.",
                    "demo_action": "disability_documentation_requirements"
                },
                {
                    "user": "My disability rating recently increased to 80%. Can I get more exemption?",
                    "ai": "Yes, congratulations on the updated rating. With an 80% disability rating, you may be eligible for additional exemption amounts. In Texas, veterans with ratings of 70% or higher receive the $60,000 exemption, but some counties offer additional benefits for higher ratings. Let me check Tarrant County's specific benefits for 80% ratings.",
                    "demo_action": "increased_rating_benefits_check"
                },
                {
                    "user": "How do I update my exemption with the new rating?",
                    "ai": "You'll need to file an updated application with your new VA rating letter. This can typically be done by submitting the new documentation to the Tarrant County Appraisal District. The updated exemption will apply to the current tax year if filed before the deadline. Would you like me to help you start this update process?",
                    "demo_action": "exemption_update_process"
                }
            ],
            expected_response_elements=[
                "veteran_disability_recognition",
                "exemption_amount_breakdown",
                "VA_documentation_requirements",
                "rating_increase_benefits",
                "update_process_guidance"
            ],
            eligibility_requirements=[
                "Must be honorably discharged veteran",
                "Must have VA disability rating",
                "Property must be primary residence",
                "Must have homestead exemption"
            ],
            required_documents=[
                "VA disability rating letter",
                "DD-214 (discharge papers)",
                "Property ownership documentation",
                "Homestead exemption application"
            ],
            demo_notes="Demonstrates veteran disability exemption process and rating updates"
        ))

        return scenarios

    def _create_veteran_scenarios(self) -> List[ExemptionApplicationScenario]:
        """Create veteran exemption scenarios"""
        scenarios = []

        # Scenario 5: Veteran's surviving spouse exemption
        scenarios.append(ExemptionApplicationScenario(
            scenario_id="exemption_005",
            exemption_type=ExemptionType.VETERAN,
            application_stage=ApplicationStage.ELIGIBILITY_CHECK,
            customer_persona="veteran_spouse",
            property_address="555 Memorial Drive, San Antonio",
            county="Bexar",
            exemption_value=160000.00,
            conversation_flow=[
                {
                    "user": "My husband was a disabled veteran who passed away last year. Do I still qualify for his veteran exemptions?",
                    "ai": "I'm sorry for your loss. Yes, as the surviving spouse of a disabled veteran, you may continue to receive the veteran exemptions as long as you don't remarry and continue to live in the home as your primary residence. The exemptions can continue for your lifetime under these conditions.",
                    "demo_action": "surviving_spouse_exemption_explanation"
                },
                {
                    "user": "What documentation do I need to continue receiving the exemption?",
                    "ai": "You'll need to provide: your husband's death certificate, your marriage certificate, proof that you haven't remarried, and confirmation that this remains your primary residence. The appraisal district may also need a copy of his original VA disability rating letter if not already on file.",
                    "demo_action": "surviving_spouse_documentation"
                },
                {
                    "user": "What happens if I eventually want to sell the house and move?",
                    "ai": "If you sell the house, the exemptions end with the sale since they're tied to this specific property and your residence here. However, if you purchase another home in Texas and it becomes your primary residence, you can apply for a homestead exemption at the new property, though the veteran disability exemption was specific to your late husband.",
                    "demo_action": "relocation_impact_explanation"
                }
            ],
            expected_response_elements=[
                "surviving_spouse_eligibility",
                "continuation_requirements",
                "required_documentation",
                "remarriage_impact",
                "relocation_consequences"
            ],
            eligibility_requirements=[
                "Must be surviving spouse of qualified veteran",
                "Must not have remarried",
                "Property must remain primary residence",
                "Must maintain exemption requirements"
            ],
            required_documents=[
                "Death certificate",
                "Marriage certificate",
                "Affidavit of non-remarriage",
                "Veteran's disability documentation"
            ],
            demo_notes="Shows surviving spouse exemption continuation and requirements"
        ))

        return scenarios

    def _create_agricultural_scenarios(self) -> List[ExemptionApplicationScenario]:
        """Create agricultural exemption scenarios"""
        scenarios = []

        # Scenario 6: Agricultural land use exemption
        scenarios.append(ExemptionApplicationScenario(
            scenario_id="exemption_006",
            exemption_type=ExemptionType.AGRICULTURAL,
            application_stage=ApplicationStage.APPLICATION_PROCESS,
            customer_persona="agricultural_property_owner",
            property_address="Rural Route 1, County Road 250",
            county="Williamson",
            exemption_value=350000.00,  # Significant agricultural value reduction
            conversation_flow=[
                {
                    "user": "I have 50 acres that I use for cattle grazing. How do I apply for agricultural exemption?",
                    "ai": "Agricultural exemption can provide significant tax savings for qualified agricultural use. For 50 acres of cattle grazing in Williamson County, you'll need to demonstrate active agricultural use, meet minimum acreage requirements, and show agricultural income or production. The exemption typically reduces taxable value from market value to agricultural use value.",
                    "demo_action": "agricultural_exemption_overview"
                },
                {
                    "user": "What qualifies as 'active agricultural use' for cattle?",
                    "ai": "For cattle operations, active use means: maintaining an appropriate number of cattle for the acreage (typically 1 head per 5-7 acres in this region), demonstrating continuous grazing activity, maintaining fences and water sources, and showing intent to produce income or agricultural products. You'll need to document your cattle count and management practices.",
                    "demo_action": "cattle_agricultural_requirements"
                },
                {
                    "user": "What documentation do I need to provide?",
                    "ai": "You'll need: completed agricultural exemption application, documentation of cattle numbers and grazing activities, evidence of agricultural income (tax returns, sales receipts), photos showing agricultural use, and possibly a statement from a county extension agent. The application deadline is typically April 30th for the current tax year.",
                    "demo_action": "agricultural_documentation_requirements"
                },
                {
                    "user": "How much could this save me in taxes?",
                    "ai": "Agricultural exemption can provide substantial savings. If your 50 acres has a market value of $400,000 but agricultural use value of $50,000, you'd save approximately $9,450 annually based on current tax rates. The exact savings depend on the difference between market and agricultural use values as determined by the appraisal district.",
                    "demo_action": "agricultural_savings_calculation"
                }
            ],
            expected_response_elements=[
                "agricultural_use_requirements",
                "cattle_operation_standards",
                "documentation_checklist",
                "application_deadline",
                "substantial_savings_potential"
            ],
            eligibility_requirements=[
                "Minimum acreage requirements (typically 10+ acres)",
                "Active agricultural use for 5+ years",
                "Intent to produce agricultural products",
                "Compliance with agricultural practices"
            ],
            required_documents=[
                "Agricultural exemption application",
                "Proof of agricultural income",
                "Cattle count documentation",
                "Property management records"
            ],
            demo_notes="Demonstrates agricultural exemption for cattle operations with significant savings"
        ))

        return scenarios

    def _create_solar_scenarios(self) -> List[ExemptionApplicationScenario]:
        """Create solar energy exemption scenarios"""
        scenarios = []

        # Scenario 7: Solar panel exemption application
        scenarios.append(ExemptionApplicationScenario(
            scenario_id="exemption_007",
            exemption_type=ExemptionType.SOLAR,
            application_stage=ApplicationStage.APPLICATION_PROCESS,
            customer_persona="environmentally_conscious_homeowner",
            property_address="888 Green Energy Lane, Austin",
            county="Travis",
            exemption_value=25000.00,  # Solar installation value exemption
            conversation_flow=[
                {
                    "user": "I just installed solar panels on my house. Are there property tax exemptions for solar energy systems?",
                    "ai": "Yes! Texas offers a solar energy system exemption that removes the added value of your solar installation from your property taxes. This means the solar panels won't increase your taxable property value, even though they add value to your home. This exemption helps offset the cost of going solar.",
                    "demo_action": "solar_exemption_explanation"
                },
                {
                    "user": "How much could this save me? My solar system cost $35,000.",
                    "ai": "If your $35,000 solar system adds $25,000 to your home's assessed value, the exemption would save you approximately $675 annually in Travis County based on current tax rates. Over 20 years, that's about $13,500 in tax savings, which significantly improves your solar investment return.",
                    "demo_action": "solar_savings_calculation"
                },
                {
                    "user": "What do I need to apply for this exemption?",
                    "ai": "You'll need: proof of solar system installation (contractor invoices, permits), documentation showing the system's value and specifications, photos of the installed system, and the completed solar exemption application. The system must be primarily for on-site energy use, not commercial energy production.",
                    "demo_action": "solar_application_requirements"
                },
                {
                    "user": "Does this exemption last forever or does it expire?",
                    "ai": "The solar exemption continues as long as the solar energy system remains installed and functional on your property. If you remove the system or it becomes non-functional, you should notify the appraisal district. The exemption transfers with the property if you sell your home with the solar system intact.",
                    "demo_action": "solar_exemption_duration"
                }
            ],
            expected_response_elements=[
                "solar_exemption_benefits",
                "added_value_exemption",
                "annual_savings_calculation",
                "installation_documentation_requirements",
                "exemption_permanency"
            ],
            eligibility_requirements=[
                "Solar system must be primarily for on-site use",
                "System must be permanently installed",
                "Must be used for energy production",
                "Installation must be documented"
            ],
            required_documents=[
                "Solar installation invoices",
                "Building permits for solar installation",
                "System specifications and photos",
                "Solar exemption application"
            ],
            demo_notes="Shows solar energy exemption benefits and environmental incentives"
        ))

        return scenarios

    def get_scenario_by_id(self, scenario_id: str) -> Optional[ExemptionApplicationScenario]:
        """Get a specific scenario by ID"""
        for scenario in self.scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        return None

    def get_scenarios_by_exemption_type(self, exemption_type: ExemptionType) -> List[ExemptionApplicationScenario]:
        """Get all scenarios for a specific exemption type"""
        return [s for s in self.scenarios if s.exemption_type == exemption_type]

    def get_scenarios_by_stage(self, stage: ApplicationStage) -> List[ExemptionApplicationScenario]:
        """Get scenarios by application stage"""
        return [s for s in self.scenarios if s.application_stage == stage]

    def get_scenarios_by_persona(self, persona: str) -> List[ExemptionApplicationScenario]:
        """Get scenarios for a specific customer persona"""
        return [s for s in self.scenarios if s.customer_persona == persona]

    def get_random_scenario(self) -> ExemptionApplicationScenario:
        """Get a random scenario for spontaneous demos"""
        return random.choice(self.scenarios)

    def get_all_scenarios(self) -> List[ExemptionApplicationScenario]:
        """Get all exemption application scenarios"""
        return self.scenarios

# Demo scenario manager
demo_exemption_scenarios = ExemptionApplicationDemoScenarios()