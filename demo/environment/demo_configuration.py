"""
Demo Environment Configuration Management
Centralized configuration for demo environment with reset capabilities and demo-specific settings
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import logging

from config.settings import get_settings

logger = logging.getLogger(__name__)

@dataclass
class DemoSettings:
    """Demo-specific configuration settings"""
    demo_mode: bool = True
    demo_database_name: str = "centuryproptax_demo"
    demo_redis_db: int = 15  # Use separate Redis DB for demo
    auto_reset_enabled: bool = True
    reset_interval_hours: int = 24
    demo_user_prefix: str = "demo_"
    mock_data_enabled: bool = True
    realistic_delays_enabled: bool = False  # For demo speed
    demo_analytics_enabled: bool = True
    demo_session_timeout_minutes: int = 120
    max_concurrent_demo_sessions: int = 10
    demo_environment_name: str = "Development Demo"

@dataclass
class DemoScenarioConfig:
    """Configuration for demo scenarios"""
    scenario_id: str
    enabled: bool
    difficulty_level: str  # "basic", "intermediate", "advanced"
    estimated_duration_minutes: int
    required_data_sets: List[str]
    demo_notes: str

@dataclass
class DemoPerformanceTargets:
    """Performance targets for demo environment"""
    max_response_time_ms: int = 200
    target_accuracy_percent: float = 95.0
    max_conversation_turns: int = 20
    target_resolution_rate_percent: float = 85.0

class DemoConfigurationManager:
    """Manages demo environment configuration and settings"""

    def __init__(self):
        self.base_settings = get_settings()
        self.demo_settings = self._load_demo_settings()
        self.scenario_configs = self._load_scenario_configs()
        self.performance_targets = DemoPerformanceTargets()
        self._config_file_path = Path("config/demo_config.json")

    def _load_demo_settings(self) -> DemoSettings:
        """Load demo settings from configuration file or environment"""
        demo_settings = DemoSettings()

        # Override with environment variables if set
        if os.getenv("DEMO_MODE"):
            demo_settings.demo_mode = os.getenv("DEMO_MODE").lower() == "true"
        if os.getenv("DEMO_DATABASE_NAME"):
            demo_settings.demo_database_name = os.getenv("DEMO_DATABASE_NAME")
        if os.getenv("DEMO_REDIS_DB"):
            demo_settings.demo_redis_db = int(os.getenv("DEMO_REDIS_DB"))
        if os.getenv("DEMO_AUTO_RESET"):
            demo_settings.auto_reset_enabled = os.getenv("DEMO_AUTO_RESET").lower() == "true"
        if os.getenv("DEMO_ENVIRONMENT_NAME"):
            demo_settings.demo_environment_name = os.getenv("DEMO_ENVIRONMENT_NAME")

        return demo_settings

    def _load_scenario_configs(self) -> Dict[str, DemoScenarioConfig]:
        """Load demo scenario configurations"""
        scenarios = {
            "basic_inquiry": DemoScenarioConfig(
                scenario_id="basic_inquiry",
                enabled=True,
                difficulty_level="basic",
                estimated_duration_minutes=5,
                required_data_sets=["property_records", "tax_rates", "payment_history"],
                demo_notes="Basic property information inquiries"
            ),
            "payment_processing": DemoScenarioConfig(
                scenario_id="payment_processing",
                enabled=True,
                difficulty_level="intermediate",
                estimated_duration_minutes=8,
                required_data_sets=["property_records", "payment_history", "payment_methods"],
                demo_notes="Payment options and processing workflows"
            ),
            "assessment_appeals": DemoScenarioConfig(
                scenario_id="assessment_appeals",
                enabled=True,
                difficulty_level="advanced",
                estimated_duration_minutes=12,
                required_data_sets=["property_records", "assessment_history", "appeal_procedures"],
                demo_notes="Assessment appeal process and guidance"
            ),
            "exemption_applications": DemoScenarioConfig(
                scenario_id="exemption_applications",
                enabled=True,
                difficulty_level="intermediate",
                estimated_duration_minutes=10,
                required_data_sets=["property_records", "exemption_rules", "application_forms"],
                demo_notes="Property tax exemption applications and eligibility"
            ),
            "multi_property": DemoScenarioConfig(
                scenario_id="multi_property",
                enabled=True,
                difficulty_level="advanced",
                estimated_duration_minutes=15,
                required_data_sets=["property_records", "portfolio_data", "consolidated_billing"],
                demo_notes="Multi-property portfolio management"
            ),
            "escalation_scenarios": DemoScenarioConfig(
                scenario_id="escalation_scenarios",
                enabled=True,
                difficulty_level="advanced",
                estimated_duration_minutes=10,
                required_data_sets=["property_records", "escalation_rules", "agent_handoff"],
                demo_notes="Complex cases requiring human agent escalation"
            ),
            "multilingual": DemoScenarioConfig(
                scenario_id="multilingual",
                enabled=True,
                difficulty_level="intermediate",
                estimated_duration_minutes=8,
                required_data_sets=["property_records", "spanish_templates", "translation_data"],
                demo_notes="Spanish language property tax assistance"
            )
        }
        return scenarios

    def get_demo_database_config(self) -> Dict[str, Any]:
        """Get demo-specific database configuration"""
        base_db_config = self.base_settings.database
        return {
            "database_name": self.demo_settings.demo_database_name,
            "host": base_db_config.get("host", "localhost"),
            "port": base_db_config.get("port", 5432),
            "username": base_db_config.get("username", "demo_user"),
            "password": base_db_config.get("password", "demo_pass"),
            "pool_size": 5,  # Smaller pool for demo
            "max_connections": 10,
            "isolation_level": "READ_COMMITTED"
        }

    def get_demo_redis_config(self) -> Dict[str, Any]:
        """Get demo-specific Redis configuration"""
        base_redis_config = self.base_settings.redis
        return {
            "host": base_redis_config.get("host", "localhost"),
            "port": base_redis_config.get("port", 6379),
            "db": self.demo_settings.demo_redis_db,
            "password": base_redis_config.get("password"),
            "socket_timeout": 5,
            "socket_connect_timeout": 5,
            "decode_responses": True
        }

    def get_demo_ai_config(self) -> Dict[str, Any]:
        """Get demo-specific AI configuration"""
        return {
            "model_name": "gemini-1.5-flash",  # Faster model for demos
            "temperature": 0.3,  # More consistent responses for demos
            "max_tokens": 500,  # Shorter responses for demo flow
            "response_timeout": 10,  # Quick timeout for demos
            "demo_mode": True,
            "context_window": 4000,  # Smaller context for speed
            "demo_personality": "helpful_professional_concise"
        }

    def get_enabled_scenarios(self) -> List[DemoScenarioConfig]:
        """Get list of enabled demo scenarios"""
        return [config for config in self.scenario_configs.values() if config.enabled]

    def get_scenario_config(self, scenario_id: str) -> Optional[DemoScenarioConfig]:
        """Get configuration for a specific scenario"""
        return self.scenario_configs.get(scenario_id)

    def enable_scenario(self, scenario_id: str) -> bool:
        """Enable a demo scenario"""
        if scenario_id in self.scenario_configs:
            self.scenario_configs[scenario_id].enabled = True
            self._save_scenario_configs()
            return True
        return False

    def disable_scenario(self, scenario_id: str) -> bool:
        """Disable a demo scenario"""
        if scenario_id in self.scenario_configs:
            self.scenario_configs[scenario_id].enabled = False
            self._save_scenario_configs()
            return True
        return False

    def get_demo_environment_info(self) -> Dict[str, Any]:
        """Get comprehensive demo environment information"""
        return {
            "environment_name": self.demo_settings.demo_environment_name,
            "demo_mode": self.demo_settings.demo_mode,
            "database_name": self.demo_settings.demo_database_name,
            "redis_db": self.demo_settings.demo_redis_db,
            "auto_reset_enabled": self.demo_settings.auto_reset_enabled,
            "reset_interval_hours": self.demo_settings.reset_interval_hours,
            "max_concurrent_sessions": self.demo_settings.max_concurrent_demo_sessions,
            "session_timeout_minutes": self.demo_settings.demo_session_timeout_minutes,
            "enabled_scenarios": len(self.get_enabled_scenarios()),
            "total_scenarios": len(self.scenario_configs),
            "performance_targets": asdict(self.performance_targets),
            "realistic_delays": self.demo_settings.realistic_delays_enabled,
            "analytics_enabled": self.demo_settings.demo_analytics_enabled
        }

    def validate_demo_environment(self) -> Dict[str, Any]:
        """Validate demo environment configuration and dependencies"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks": {
                "database_config": False,
                "redis_config": False,
                "ai_config": False,
                "scenario_configs": False,
                "required_data": False
            }
        }

        try:
            # Validate database configuration
            db_config = self.get_demo_database_config()
            if all(key in db_config for key in ["database_name", "host", "port"]):
                validation_results["checks"]["database_config"] = True
            else:
                validation_results["errors"].append("Incomplete database configuration")
                validation_results["valid"] = False

            # Validate Redis configuration
            redis_config = self.get_demo_redis_config()
            if all(key in redis_config for key in ["host", "port", "db"]):
                validation_results["checks"]["redis_config"] = True
            else:
                validation_results["errors"].append("Incomplete Redis configuration")
                validation_results["valid"] = False

            # Validate AI configuration
            ai_config = self.get_demo_ai_config()
            if "model_name" in ai_config and ai_config["model_name"]:
                validation_results["checks"]["ai_config"] = True
            else:
                validation_results["errors"].append("AI model not configured")
                validation_results["valid"] = False

            # Validate scenario configurations
            enabled_scenarios = self.get_enabled_scenarios()
            if len(enabled_scenarios) > 0:
                validation_results["checks"]["scenario_configs"] = True
            else:
                validation_results["warnings"].append("No demo scenarios enabled")

            # Check for required data dependencies
            required_data_sets = set()
            for scenario in enabled_scenarios:
                required_data_sets.update(scenario.required_data_sets)

            if len(required_data_sets) > 0:
                validation_results["checks"]["required_data"] = True
                validation_results["required_data_sets"] = list(required_data_sets)

        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Validation error: {str(e)}")
            logger.error(f"Demo environment validation error: {e}")

        return validation_results

    def _save_scenario_configs(self):
        """Save scenario configurations to file"""
        try:
            config_data = {
                "scenarios": {
                    scenario_id: asdict(config)
                    for scenario_id, config in self.scenario_configs.items()
                },
                "last_updated": datetime.now().isoformat()
            }

            self._config_file_path.parent.mkdir(exist_ok=True)
            with open(self._config_file_path, 'w') as f:
                json.dump(config_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save scenario configurations: {e}")

    def export_demo_config(self) -> Dict[str, Any]:
        """Export complete demo configuration for sharing or backup"""
        return {
            "demo_settings": asdict(self.demo_settings),
            "scenario_configs": {
                scenario_id: asdict(config)
                for scenario_id, config in self.scenario_configs.items()
            },
            "performance_targets": asdict(self.performance_targets),
            "exported_at": datetime.now().isoformat(),
            "version": "1.0"
        }

    def import_demo_config(self, config_data: Dict[str, Any]) -> bool:
        """Import demo configuration from exported data"""
        try:
            if "demo_settings" in config_data:
                self.demo_settings = DemoSettings(**config_data["demo_settings"])

            if "scenario_configs" in config_data:
                self.scenario_configs = {
                    scenario_id: DemoScenarioConfig(**config)
                    for scenario_id, config in config_data["scenario_configs"].items()
                }

            if "performance_targets" in config_data:
                self.performance_targets = DemoPerformanceTargets(**config_data["performance_targets"])

            self._save_scenario_configs()
            return True

        except Exception as e:
            logger.error(f"Failed to import demo configuration: {e}")
            return False

# Global demo configuration manager
demo_config = DemoConfigurationManager()