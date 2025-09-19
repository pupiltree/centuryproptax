"""
Demo Scenarios Module
Centralized access to all demo scenarios for property tax AI assistant demonstrations
"""

from typing import Dict, List, Any, Optional, Union
import random
from enum import Enum

# Import all scenario types
from .basic_inquiry_scenarios import demo_basic_scenarios, BasicInquiryScenario
from .payment_processing_scenarios import demo_payment_scenarios, PaymentProcessingScenario
from .assessment_appeal_scenarios import demo_appeal_scenarios, AssessmentAppealScenario
from .exemption_application_scenarios import demo_exemption_scenarios, ExemptionApplicationScenario
from .multi_property_scenarios import demo_multi_property_scenarios, MultiPropertyScenario
from .escalation_scenarios import demo_escalation_scenarios, EscalationScenario

class ScenarioCategory(Enum):
    """Categories of demo scenarios"""
    BASIC_INQUIRY = "basic_inquiry"
    PAYMENT_PROCESSING = "payment_processing"
    ASSESSMENT_APPEALS = "assessment_appeals"
    EXEMPTION_APPLICATIONS = "exemption_applications"
    MULTI_PROPERTY = "multi_property"
    ESCALATION = "escalation"

class DemoScenarioManager:
    """Centralized manager for all demo scenarios"""

    def __init__(self):
        self.scenario_managers = {
            ScenarioCategory.BASIC_INQUIRY: demo_basic_scenarios,
            ScenarioCategory.PAYMENT_PROCESSING: demo_payment_scenarios,
            ScenarioCategory.ASSESSMENT_APPEALS: demo_appeal_scenarios,
            ScenarioCategory.EXEMPTION_APPLICATIONS: demo_exemption_scenarios,
            ScenarioCategory.MULTI_PROPERTY: demo_multi_property_scenarios,
            ScenarioCategory.ESCALATION: demo_escalation_scenarios
        }

    def get_all_scenarios(self) -> Dict[str, List]:
        """Get all scenarios organized by category"""
        all_scenarios = {}
        for category, manager in self.scenario_managers.items():
            all_scenarios[category.value] = manager.get_all_scenarios()
        return all_scenarios

    def get_scenario_by_id(self, scenario_id: str) -> Optional[Union[BasicInquiryScenario, PaymentProcessingScenario, AssessmentAppealScenario, ExemptionApplicationScenario, MultiPropertyScenario, EscalationScenario]]:
        """Get a specific scenario by ID across all categories"""
        for manager in self.scenario_managers.values():
            scenario = manager.get_scenario_by_id(scenario_id)
            if scenario:
                return scenario
        return None

    def get_scenarios_by_category(self, category: ScenarioCategory) -> List:
        """Get all scenarios for a specific category"""
        manager = self.scenario_managers.get(category)
        return manager.get_all_scenarios() if manager else []

    def get_scenarios_by_persona(self, persona: str) -> List:
        """Get all scenarios for a specific customer persona across categories"""
        scenarios = []
        for manager in self.scenario_managers.values():
            if hasattr(manager, 'get_scenarios_by_persona'):
                scenarios.extend(manager.get_scenarios_by_persona(persona))
        return scenarios

    def get_random_scenario(self, category: Optional[ScenarioCategory] = None) -> Optional[Union[BasicInquiryScenario, PaymentProcessingScenario, AssessmentAppealScenario, ExemptionApplicationScenario, MultiPropertyScenario, EscalationScenario]]:
        """Get a random scenario, optionally from a specific category"""
        if category:
            manager = self.scenario_managers.get(category)
            return manager.get_random_scenario() if manager else None
        else:
            # Get random scenario from any category
            manager = random.choice(list(self.scenario_managers.values()))
            return manager.get_random_scenario()

    def get_scenario_categories(self) -> List[Dict[str, Any]]:
        """Get list of available scenario categories with metadata"""
        categories = []
        for category, manager in self.scenario_managers.items():
            scenarios = manager.get_all_scenarios()
            categories.append({
                "id": category.value,
                "name": category.value.replace("_", " ").title(),
                "scenario_count": len(scenarios),
                "description": self._get_category_description(category)
            })
        return categories

    def _get_category_description(self, category: ScenarioCategory) -> str:
        """Get description for a scenario category"""
        descriptions = {
            ScenarioCategory.BASIC_INQUIRY: "Basic property tax information requests and general inquiries",
            ScenarioCategory.PAYMENT_PROCESSING: "Payment options, online payments, installment plans, and payment issues",
            ScenarioCategory.ASSESSMENT_APPEALS: "Property assessment disputes, appeal processes, and evidence gathering",
            ScenarioCategory.EXEMPTION_APPLICATIONS: "Homestead, senior, veteran, agricultural, and other tax exemptions",
            ScenarioCategory.MULTI_PROPERTY: "Portfolio management for investors and multi-property owners",
            ScenarioCategory.ESCALATION: "Complex cases requiring human agent intervention and specialized assistance"
        }
        return descriptions.get(category, "Demo scenarios for property tax assistance")

    def get_scenarios_by_difficulty(self, difficulty: str) -> List:
        """Get scenarios by difficulty level across all categories"""
        scenarios = []
        for manager in self.scenario_managers.values():
            all_scenarios = manager.get_all_scenarios()
            for scenario in all_scenarios:
                # Different scenario types may have different difficulty attributes
                scenario_difficulty = None
                if hasattr(scenario, 'legal_complexity'):
                    scenario_difficulty = scenario.legal_complexity
                elif hasattr(scenario, 'complexity'):
                    scenario_difficulty = scenario.complexity.value if hasattr(scenario.complexity, 'value') else str(scenario.complexity)
                elif hasattr(scenario, 'difficulty_level'):
                    scenario_difficulty = scenario.difficulty_level

                if scenario_difficulty and difficulty.lower() in scenario_difficulty.lower():
                    scenarios.append(scenario)
        return scenarios

    def get_demo_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of all demo scenarios"""
        total_scenarios = 0
        category_summaries = {}

        for category, manager in self.scenario_managers.items():
            scenarios = manager.get_all_scenarios()
            total_scenarios += len(scenarios)

            category_summaries[category.value] = {
                "count": len(scenarios),
                "scenarios": [
                    {
                        "id": scenario.scenario_id,
                        "description": getattr(scenario, 'demo_notes', 'Demo scenario'),
                        "persona": getattr(scenario, 'customer_persona', 'Unknown')
                    }
                    for scenario in scenarios[:3]  # First 3 scenarios as preview
                ]
            }

        return {
            "total_scenarios": total_scenarios,
            "total_categories": len(self.scenario_managers),
            "categories": category_summaries,
            "available_personas": self._get_all_personas(),
            "demo_ready": total_scenarios > 0
        }

    def _get_all_personas(self) -> List[str]:
        """Get list of all unique customer personas across scenarios"""
        personas = set()
        for manager in self.scenario_managers.values():
            scenarios = manager.get_all_scenarios()
            for scenario in scenarios:
                if hasattr(scenario, 'customer_persona'):
                    personas.add(scenario.customer_persona)
        return sorted(list(personas))

    def validate_scenarios(self) -> Dict[str, Any]:
        """Validate all scenarios for demo readiness"""
        validation_results = {
            "valid": True,
            "total_scenarios": 0,
            "issues": [],
            "warnings": [],
            "category_status": {}
        }

        for category, manager in self.scenario_managers.items():
            scenarios = manager.get_all_scenarios()
            category_issues = []

            validation_results["total_scenarios"] += len(scenarios)

            if len(scenarios) == 0:
                category_issues.append("No scenarios available")
                validation_results["valid"] = False

            # Validate scenario structure
            for scenario in scenarios:
                if not hasattr(scenario, 'scenario_id') or not scenario.scenario_id:
                    category_issues.append(f"Scenario missing ID")
                    validation_results["valid"] = False

                if not hasattr(scenario, 'conversation_flow') or not scenario.conversation_flow:
                    category_issues.append(f"Scenario {getattr(scenario, 'scenario_id', 'unknown')} missing conversation flow")
                    validation_results["valid"] = False

            validation_results["category_status"][category.value] = {
                "scenario_count": len(scenarios),
                "issues": category_issues,
                "valid": len(category_issues) == 0
            }

            validation_results["issues"].extend(category_issues)

        return validation_results

    def get_scenario_for_demo(self, preferences: Dict[str, Any]) -> Optional[Union[BasicInquiryScenario, PaymentProcessingScenario, AssessmentAppealScenario, ExemptionApplicationScenario, MultiPropertyScenario, EscalationScenario]]:
        """Get a scenario based on demo preferences"""
        category = preferences.get('category')
        persona = preferences.get('persona')
        difficulty = preferences.get('difficulty')

        # Filter by category first
        if category:
            try:
                category_enum = ScenarioCategory(category)
                scenarios = self.get_scenarios_by_category(category_enum)
            except ValueError:
                scenarios = []
                for manager in self.scenario_managers.values():
                    scenarios.extend(manager.get_all_scenarios())
        else:
            scenarios = []
            for manager in self.scenario_managers.values():
                scenarios.extend(manager.get_all_scenarios())

        # Filter by persona if specified
        if persona:
            scenarios = [s for s in scenarios if getattr(s, 'customer_persona', '') == persona]

        # Filter by difficulty if specified
        if difficulty:
            filtered_scenarios = []
            for scenario in scenarios:
                scenario_difficulty = None
                if hasattr(scenario, 'legal_complexity'):
                    scenario_difficulty = scenario.legal_complexity
                elif hasattr(scenario, 'complexity'):
                    scenario_difficulty = scenario.complexity.value if hasattr(scenario.complexity, 'value') else str(scenario.complexity)
                elif hasattr(scenario, 'difficulty_level'):
                    scenario_difficulty = scenario.difficulty_level

                if scenario_difficulty and difficulty.lower() in scenario_difficulty.lower():
                    filtered_scenarios.append(scenario)
            scenarios = filtered_scenarios

        # Return random scenario from filtered results
        return random.choice(scenarios) if scenarios else None

# Global demo scenario manager
demo_scenario_manager = DemoScenarioManager()

# Convenience functions for easy access
def get_all_demo_scenarios():
    """Get all demo scenarios organized by category"""
    return demo_scenario_manager.get_all_scenarios()

def get_demo_scenario(scenario_id: str):
    """Get a specific demo scenario by ID"""
    return demo_scenario_manager.get_scenario_by_id(scenario_id)

def get_random_demo_scenario(category: str = None):
    """Get a random demo scenario"""
    if category:
        try:
            category_enum = ScenarioCategory(category)
            return demo_scenario_manager.get_random_scenario(category_enum)
        except ValueError:
            return demo_scenario_manager.get_random_scenario()
    return demo_scenario_manager.get_random_scenario()

def get_demo_categories():
    """Get available demo scenario categories"""
    return demo_scenario_manager.get_scenario_categories()

def validate_demo_scenarios():
    """Validate all demo scenarios"""
    return demo_scenario_manager.validate_scenarios()

def get_demo_summary():
    """Get comprehensive demo summary"""
    return demo_scenario_manager.get_demo_summary()