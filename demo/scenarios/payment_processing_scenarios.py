"""
Payment Processing Scenarios for Demo Environment
Realistic conversation flows for property tax payment-related inquiries
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import random
from datetime import datetime, timedelta

from agents.core.conversation_flows import ConversationStage, PropertyTaxConcern
from mock_data.property_records import get_sample_properties
from mock_data.tax_rates import get_tax_rates_by_county

class PaymentScenarioType(Enum):
    """Types of payment processing scenarios"""
    ONLINE_PAYMENT = "online_payment"
    INSTALLMENT_SETUP = "installment_setup"
    LATE_PAYMENT = "late_payment"
    PAYMENT_HISTORY = "payment_history"
    REFUND_REQUEST = "refund_request"
    PAYMENT_PLAN = "payment_plan"
    HARDSHIP_ASSISTANCE = "hardship_assistance"
    OVERPAYMENT = "overpayment"

@dataclass
class PaymentProcessingScenario:
    """Payment processing scenario with realistic conversation flow"""
    scenario_id: str
    scenario_type: PaymentScenarioType
    customer_persona: str
    property_address: str
    county: str
    payment_amount: float
    conversation_flow: List[Dict[str, str]]
    expected_response_elements: List[str]
    demo_notes: str
    technical_demo_features: List[str]

class PaymentProcessingDemoScenarios:
    """Demo scenarios for payment processing workflows"""

    def __init__(self):
        self.properties = get_sample_properties()
        self.scenarios = self._generate_scenarios()

    def _generate_scenarios(self) -> List[PaymentProcessingScenario]:
        """Generate realistic payment processing scenarios"""
        scenarios = []

        # Online Payment Scenarios
        scenarios.extend(self._create_online_payment_scenarios())

        # Installment Setup Scenarios
        scenarios.extend(self._create_installment_scenarios())

        # Late Payment Scenarios
        scenarios.extend(self._create_late_payment_scenarios())

        # Payment History Scenarios
        scenarios.extend(self._create_payment_history_scenarios())

        # Hardship Assistance Scenarios
        scenarios.extend(self._create_hardship_scenarios())

        # Refund and Overpayment Scenarios
        scenarios.extend(self._create_refund_scenarios())

        return scenarios

    def _create_online_payment_scenarios(self) -> List[PaymentProcessingScenario]:
        """Create online payment processing scenarios"""
        scenarios = []

        # Scenario 1: First-time online payment
        scenarios.append(PaymentProcessingScenario(
            scenario_id="payment_001",
            scenario_type=PaymentScenarioType.ONLINE_PAYMENT,
            customer_persona="tech_comfortable_homeowner",
            property_address="123 Digital Ave, Austin",
            county="Travis",
            payment_amount=4250.75,
            conversation_flow=[
                {
                    "user": "I'd like to pay my property taxes online for 123 Digital Ave in Austin. How do I do this?",
                    "ai": "I can help you pay your property taxes online. For your property at 123 Digital Ave in Austin, your current tax bill is $4,250.75. I can guide you through the online payment process or create a secure payment link for you. Which would you prefer?",
                    "demo_action": "payment_amount_lookup"
                },
                {
                    "user": "Create a payment link for me please.",
                    "ai": "I'll create a secure payment link for you. You can pay by bank transfer (ACH) for a $2.95 convenience fee, or by credit/debit card for a 2.35% convenience fee (about $99.89). The payment link will be valid for 48 hours and you'll receive a confirmation email immediately after payment.",
                    "demo_action": "payment_link_creation"
                },
                {
                    "user": "I'll use bank transfer. Is this secure?",
                    "ai": "Yes, absolutely secure. We use bank-grade encryption and tokenization. Your banking information is never stored on our servers. You'll be redirected to a secure portal where you can enter your account details. You'll receive confirmation via email and text when the payment is processed, typically within 1-2 business days.",
                    "demo_action": "security_assurance"
                },
                {
                    "user": "Perfect. Can I set up automatic payments for next year?",
                    "ai": "Great idea! Once this payment is complete, I can help you set up automatic payments for next year. You can choose to pay the full amount in October or split it into quarterly installments. The automatic payment will be scheduled based on when your tax bill becomes available, typically in late September.",
                    "demo_action": "auto_payment_setup_offer"
                }
            ],
            expected_response_elements=[
                "current_tax_amount",
                "payment_link_generation",
                "fee_structure_explanation",
                "security_confirmation",
                "automatic_payment_option"
            ],
            technical_demo_features=[
                "Real-time tax amount lookup",
                "Secure payment link generation",
                "Multiple payment method support",
                "Automatic payment enrollment"
            ],
            demo_notes="Demonstrates full online payment workflow with security features"
        ))

        # Scenario 2: Business owner bulk payment
        scenarios.append(PaymentProcessingScenario(
            scenario_id="payment_002",
            scenario_type=PaymentScenarioType.ONLINE_PAYMENT,
            customer_persona="commercial_property_manager",
            property_address="Multiple Commercial Properties",
            county="Harris",
            payment_amount=15750.30,
            conversation_flow=[
                {
                    "user": "I manage several commercial properties in Harris County and need to pay all the property taxes at once. Can I do this online?",
                    "ai": "Yes, I can help you with bulk payments for multiple properties. I see you have 4 commercial properties in Harris County with a total tax amount of $15,750.30. I can create a single payment for all properties or separate payments for each. Which would you prefer?",
                    "demo_action": "bulk_payment_lookup"
                },
                {
                    "user": "Single payment for all would be easier. Can I get a breakdown?",
                    "ai": "Absolutely. Here's your breakdown: Property A (555 Commerce St): $4,125.50, Property B (777 Industrial Blvd): $5,890.20, Property C (999 Business Park): $3,234.60, Property D (111 Corporate Dr): $2,500.00. Total: $15,750.30. I'll create a consolidated payment link with detailed receipts for each property.",
                    "demo_action": "payment_breakdown_display"
                },
                {
                    "user": "Perfect. I need receipts for tax purposes. Will I get separate receipts?",
                    "ai": "Yes, you'll receive both a consolidated receipt for the total payment and individual receipts for each property showing the specific amounts paid. All receipts will include your business information and are formatted for tax filing purposes. You'll also receive a detailed statement you can provide to your accountant.",
                    "demo_action": "receipt_confirmation"
                }
            ],
            expected_response_elements=[
                "multi_property_identification",
                "consolidated_payment_option",
                "detailed_breakdown",
                "business_receipt_formatting"
            ],
            technical_demo_features=[
                "Multi-property payment aggregation",
                "Business-grade receipt generation",
                "Accountant-ready documentation",
                "Portfolio payment management"
            ],
            demo_notes="Shows commercial property management and bulk payment capabilities"
        ))

        return scenarios

    def _create_installment_scenarios(self) -> List[PaymentProcessingScenario]:
        """Create installment payment setup scenarios"""
        scenarios = []

        # Scenario 3: Senior citizen setting up installments
        scenarios.append(PaymentProcessingScenario(
            scenario_id="payment_003",
            scenario_type=PaymentScenarioType.INSTALLMENT_SETUP,
            customer_persona="senior_citizen_fixed_income",
            property_address="456 Retirement Ln, Dallas",
            county="Dallas",
            payment_amount=3200.00,
            conversation_flow=[
                {
                    "user": "I'm 72 years old and on a fixed income. Can I pay my property taxes in smaller amounts throughout the year?",
                    "ai": "Absolutely! Dallas County offers installment plans that are perfect for your situation. Your annual tax bill of $3,200 can be split into four quarterly payments of $800 each, plus a one-time $25 application fee. As a senior, you also have additional protections against foreclosure.",
                    "demo_action": "senior_installment_calculation"
                },
                {
                    "user": "When would the payments be due?",
                    "ai": "Your payments would be due quarterly: October 1st ($800), December 1st ($800), February 1st ($800), and April 1st ($800). There's no interest charged if you pay on time. I can set up automatic payments from your bank account to make sure you never miss a payment.",
                    "demo_action": "installment_schedule_display"
                },
                {
                    "user": "What happens if I miss a payment due to illness or emergency?",
                    "ai": "As a senior citizen, you have special protections. If you miss a payment due to illness or emergency, you can contact the tax office to discuss your situation. They often work with seniors to modify payment plans. Additionally, Texas law provides strong protections for homeowners over 65 - you cannot lose your home for unpaid taxes if you're working with the county on a payment arrangement.",
                    "demo_action": "senior_protection_explanation"
                }
            ],
            expected_response_elements=[
                "installment_eligibility_confirmation",
                "quarterly_payment_breakdown",
                "senior_citizen_protections",
                "emergency_payment_options"
            ],
            technical_demo_features=[
                "Age-based payment plan calculation",
                "Senior protection validation",
                "Automatic payment setup",
                "Emergency modification procedures"
            ],
            demo_notes="Highlights senior-specific payment assistance and protections"
        ))

        return scenarios

    def _create_late_payment_scenarios(self) -> List[PaymentProcessingScenario]:
        """Create late payment handling scenarios"""
        scenarios = []

        # Scenario 4: Property owner with late payment
        scenarios.append(PaymentProcessingScenario(
            scenario_id="payment_004",
            scenario_type=PaymentScenarioType.LATE_PAYMENT,
            customer_persona="busy_professional",
            property_address="789 Busy Street, Plano",
            county="Collin",
            payment_amount=5680.45,
            conversation_flow=[
                {
                    "user": "I forgot to pay my property taxes and they're now overdue. What do I owe and what are my options?",
                    "ai": "I understand - life gets busy! Your property at 789 Busy Street in Plano had taxes of $5,680.45 that were due January 31st. With penalty and interest charges through today, your total amount due is $6,248.90. This includes a 6% penalty plus 1% interest per month.",
                    "demo_action": "late_payment_calculation"
                },
                {
                    "user": "Can I still pay online? And will this affect my credit?",
                    "ai": "Yes, you can still pay online right now. The penalty and interest stop accruing once you pay. Property tax delinquency typically doesn't affect your credit score initially, but if it remains unpaid for an extended period, it could eventually lead to a tax lien. The good news is that paying now prevents any further complications.",
                    "demo_action": "payment_options_and_credit_impact"
                },
                {
                    "user": "I can pay now. Can you process this immediately?",
                    "ai": "Absolutely! I'll create an immediate payment link for $6,248.90. Once processed, you'll receive confirmation that your taxes are current. I'll also set up a reminder system for next year so this doesn't happen again. Would you like me to add automatic payment or calendar reminders?",
                    "demo_action": "immediate_payment_processing"
                }
            ],
            expected_response_elements=[
                "penalty_interest_calculation",
                "total_amount_due",
                "credit_impact_explanation",
                "immediate_payment_option",
                "future_reminder_setup"
            ],
            technical_demo_features=[
                "Real-time penalty calculation",
                "Immediate payment processing",
                "Credit impact assessment",
                "Automatic reminder enrollment"
            ],
            demo_notes="Shows late payment handling and prevention features"
        ))

        return scenarios

    def _create_payment_history_scenarios(self) -> List[PaymentProcessingScenario]:
        """Create payment history inquiry scenarios"""
        scenarios = []

        # Scenario 5: Property owner checking payment history
        scenarios.append(PaymentProcessingScenario(
            scenario_id="payment_005",
            scenario_type=PaymentScenarioType.PAYMENT_HISTORY,
            customer_persona="detail_oriented_homeowner",
            property_address="321 Record Street, Austin",
            county="Travis",
            payment_amount=0.00,  # Historical inquiry
            conversation_flow=[
                {
                    "user": "Can you show me my payment history for 321 Record Street in Austin? I need it for my tax records.",
                    "ai": "I can provide your complete payment history. For 321 Record Street in Austin, here are your last three years: 2023: $4,156.78 (paid 12/15/2023), 2022: $3,892.45 (paid 11/30/2022), 2021: $3,654.23 (paid 1/28/2022). I can generate a detailed statement for tax purposes if needed.",
                    "demo_action": "payment_history_display"
                },
                {
                    "user": "Yes, I need a formal statement for my accountant. Can you include the property details too?",
                    "ai": "Absolutely! I'll generate a comprehensive tax statement including: property details (address, account number, legal description), payment history with dates and amounts, assessment values by year, and exemption information. This will be formatted for professional tax preparation. Would you like this emailed or available for download?",
                    "demo_action": "comprehensive_statement_generation"
                },
                {
                    "user": "Email it please. Also, can you show me how my taxes have changed over time?",
                    "ai": "I'll email the statement to your registered address. Looking at your tax trends: 2021 ($3,654), 2022 ($3,892 - 6.5% increase), 2023 ($4,157 - 6.8% increase). This is slightly above the county average of 5.2% annually, likely due to rising property values in your area. Your effective tax rate has remained steady at about 2.7%.",
                    "demo_action": "tax_trend_analysis"
                }
            ],
            expected_response_elements=[
                "multi_year_payment_history",
                "professional_statement_generation",
                "tax_trend_analysis",
                "email_delivery_confirmation"
            ],
            technical_demo_features=[
                "Historical data retrieval",
                "Professional document generation",
                "Trend analysis and visualization",
                "Secure document delivery"
            ],
            demo_notes="Demonstrates historical data access and professional reporting"
        ))

        return scenarios

    def _create_hardship_scenarios(self) -> List[PaymentProcessingScenario]:
        """Create hardship assistance scenarios"""
        scenarios = []

        # Scenario 6: Family facing financial hardship
        scenarios.append(PaymentProcessingScenario(
            scenario_id="payment_006",
            scenario_type=PaymentScenarioType.HARDSHIP_ASSISTANCE,
            customer_persona="family_financial_hardship",
            property_address="555 Struggle Street, Houston",
            county="Harris",
            payment_amount=4500.00,
            conversation_flow=[
                {
                    "user": "I lost my job and can't afford to pay my property taxes. I'm worried about losing my house. What options do I have?",
                    "ai": "I understand this is a very stressful situation, and I want to help you explore all available options. Harris County offers several hardship assistance programs. You may qualify for a payment deferral, reduced payment plan, or in some cases, temporary tax relief. Let me check what programs you might be eligible for.",
                    "demo_action": "hardship_program_lookup"
                },
                {
                    "user": "What is a payment deferral? How does that work?",
                    "ai": "A payment deferral allows you to postpone your property tax payments without risk of foreclosure if you meet certain criteria, such as unemployment or significant income reduction. The deferred taxes accrue interest at 5% annually, but you keep your home. The taxes become due when your financial situation improves or when the property is sold.",
                    "demo_action": "deferral_program_explanation"
                },
                {
                    "user": "How do I apply for this? What documents do I need?",
                    "ai": "To apply for deferral, you'll need: proof of financial hardship (unemployment documentation, income statements), homestead exemption confirmation, and a completed hardship affidavit. I can help you start the application process and connect you with a county assistance counselor who can guide you through the entire process. Would you like me to schedule a call with a counselor?",
                    "demo_action": "application_assistance_offer"
                }
            ],
            expected_response_elements=[
                "hardship_program_options",
                "eligibility_requirements",
                "application_process",
                "counselor_connection_offer",
                "foreclosure_protection_info"
            ],
            technical_demo_features=[
                "Hardship program database lookup",
                "Eligibility pre-screening",
                "Document requirement checklist",
                "Counselor appointment scheduling"
            ],
            demo_notes="Shows compassionate hardship assistance and human escalation"
        ))

        return scenarios

    def _create_refund_scenarios(self) -> List[PaymentProcessingScenario]:
        """Create refund and overpayment scenarios"""
        scenarios = []

        # Scenario 7: Overpayment refund request
        scenarios.append(PaymentProcessingScenario(
            scenario_id="payment_007",
            scenario_type=PaymentScenarioType.OVERPAYMENT,
            customer_persona="meticulous_property_owner",
            property_address="888 Precise Ave, Fort Worth",
            county="Tarrant",
            payment_amount=-245.67,  # Negative indicates refund
            conversation_flow=[
                {
                    "user": "I think I overpaid my property taxes. My bank account shows I paid $4,500 but my tax bill was only $4,254.33. Can I get a refund?",
                    "ai": "Let me check your payment records for 888 Precise Ave in Fort Worth. I can confirm you overpaid by $245.67. You paid $4,500.00 on January 15th, but your actual tax amount was $4,254.33. You're definitely entitled to a refund of the overpayment plus statutory interest.",
                    "demo_action": "overpayment_verification"
                },
                {
                    "user": "How long does the refund process take and will I get interest?",
                    "ai": "Tarrant County typically processes refunds within 30-45 days of filing the request. You'll receive interest on the overpayment at the statutory rate from the date of overpayment. Based on your payment date of January 15th, you'll receive approximately $3.85 in interest, making your total refund $249.52.",
                    "demo_action": "refund_timeline_and_interest"
                },
                {
                    "user": "Can you help me file the refund request now?",
                    "ai": "Absolutely! I can initiate the refund request for you right now. I'll need to verify some information and then submit your refund application electronically. You'll receive a confirmation email with your refund request number, and you can track the status online. The refund will be mailed to your property address unless you prefer direct deposit.",
                    "demo_action": "refund_request_initiation"
                }
            ],
            expected_response_elements=[
                "overpayment_amount_confirmation",
                "statutory_interest_calculation",
                "refund_timeline",
                "electronic_filing_option",
                "tracking_information"
            ],
            technical_demo_features=[
                "Overpayment detection and calculation",
                "Interest computation",
                "Electronic refund filing",
                "Status tracking system"
            ],
            demo_notes="Demonstrates overpayment detection and refund processing"
        ))

        return scenarios

    def get_scenario_by_id(self, scenario_id: str) -> Optional[PaymentProcessingScenario]:
        """Get a specific scenario by ID"""
        for scenario in self.scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        return None

    def get_scenarios_by_type(self, scenario_type: PaymentScenarioType) -> List[PaymentProcessingScenario]:
        """Get all scenarios of a specific type"""
        return [s for s in self.scenarios if s.scenario_type == scenario_type]

    def get_scenarios_by_persona(self, persona: str) -> List[PaymentProcessingScenario]:
        """Get all scenarios for a specific customer persona"""
        return [s for s in self.scenarios if s.customer_persona == persona]

    def get_random_scenario(self) -> PaymentProcessingScenario:
        """Get a random scenario for spontaneous demos"""
        return random.choice(self.scenarios)

    def get_all_scenarios(self) -> List[PaymentProcessingScenario]:
        """Get all payment processing scenarios"""
        return self.scenarios

# Demo scenario manager
demo_payment_scenarios = PaymentProcessingDemoScenarios()