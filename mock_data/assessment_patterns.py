"""
Assessment Patterns and Lead Qualification Data for Texas Counties

Historical assessment data, appeal success patterns, and customer
qualification criteria for property tax services.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import random
from decimal import Decimal


# Assessment increase patterns by county and property type
ASSESSMENT_INCREASE_PATTERNS = {
    "harris": {
        "residential": {
            "avg_annual_increase": 0.065,
            "std_deviation": 0.025,
            "typical_range": (0.02, 0.12),
            "high_increase_threshold": 0.15,
            "protest_likelihood_by_increase": {
                "0-5%": 0.05,
                "5-10%": 0.15,
                "10-15%": 0.35,
                "15-20%": 0.55,
                "20%+": 0.75
            }
        },
        "commercial": {
            "avg_annual_increase": 0.055,
            "std_deviation": 0.030,
            "typical_range": (0.01, 0.10),
            "high_increase_threshold": 0.12,
            "protest_likelihood_by_increase": {
                "0-5%": 0.08,
                "5-10%": 0.20,
                "10-15%": 0.40,
                "15-20%": 0.60,
                "20%+": 0.80
            }
        },
        "industrial": {
            "avg_annual_increase": 0.045,
            "std_deviation": 0.035,
            "typical_range": (0.00, 0.09),
            "high_increase_threshold": 0.10,
            "protest_likelihood_by_increase": {
                "0-5%": 0.10,
                "5-10%": 0.25,
                "10-15%": 0.45,
                "15-20%": 0.65,
                "20%+": 0.85
            }
        }
    },
    "dallas": {
        "residential": {
            "avg_annual_increase": 0.058,
            "std_deviation": 0.022,
            "typical_range": (0.02, 0.10),
            "high_increase_threshold": 0.13,
            "protest_likelihood_by_increase": {
                "0-5%": 0.04,
                "5-10%": 0.12,
                "10-15%": 0.32,
                "15-20%": 0.52,
                "20%+": 0.72
            }
        },
        "commercial": {
            "avg_annual_increase": 0.048,
            "std_deviation": 0.028,
            "typical_range": (0.01, 0.08),
            "high_increase_threshold": 0.10,
            "protest_likelihood_by_increase": {
                "0-5%": 0.07,
                "5-10%": 0.18,
                "10-15%": 0.38,
                "15-20%": 0.58,
                "20%+": 0.78
            }
        },
        "industrial": {
            "avg_annual_increase": 0.042,
            "std_deviation": 0.032,
            "typical_range": (0.00, 0.08),
            "high_increase_threshold": 0.09,
            "protest_likelihood_by_increase": {
                "0-5%": 0.09,
                "5-10%": 0.22,
                "10-15%": 0.42,
                "15-20%": 0.62,
                "20%+": 0.82
            }
        }
    },
    "travis": {
        "residential": {
            "avg_annual_increase": 0.078,
            "std_deviation": 0.030,
            "typical_range": (0.03, 0.15),
            "high_increase_threshold": 0.18,
            "protest_likelihood_by_increase": {
                "0-5%": 0.03,
                "5-10%": 0.10,
                "10-15%": 0.28,
                "15-20%": 0.48,
                "20%+": 0.68
            }
        },
        "commercial": {
            "avg_annual_increase": 0.068,
            "std_deviation": 0.035,
            "typical_range": (0.02, 0.12),
            "high_increase_threshold": 0.15,
            "protest_likelihood_by_increase": {
                "0-5%": 0.06,
                "5-10%": 0.16,
                "10-15%": 0.36,
                "15-20%": 0.56,
                "20%+": 0.76
            }
        }
    },
    "tarrant": {
        "residential": {
            "avg_annual_increase": 0.052,
            "std_deviation": 0.020,
            "typical_range": (0.02, 0.09),
            "high_increase_threshold": 0.12,
            "protest_likelihood_by_increase": {
                "0-5%": 0.05,
                "5-10%": 0.14,
                "10-15%": 0.34,
                "15-20%": 0.54,
                "20%+": 0.74
            }
        }
    },
    "bexar": {
        "residential": {
            "avg_annual_increase": 0.045,
            "std_deviation": 0.018,
            "typical_range": (0.02, 0.08),
            "high_increase_threshold": 0.10,
            "protest_likelihood_by_increase": {
                "0-5%": 0.06,
                "5-10%": 0.16,
                "10-15%": 0.36,
                "15-20%": 0.56,
                "20%+": 0.76
            }
        }
    },
    "collin": {
        "residential": {
            "avg_annual_increase": 0.072,
            "std_deviation": 0.028,
            "typical_range": (0.03, 0.12),
            "high_increase_threshold": 0.15,
            "protest_likelihood_by_increase": {
                "0-5%": 0.04,
                "5-10%": 0.11,
                "10-15%": 0.31,
                "15-20%": 0.51,
                "20%+": 0.71
            }
        }
    }
}

# Appeal success rates and patterns
APPEAL_SUCCESS_PATTERNS = {
    "harris": {
        "residential": {
            "overall_success_rate": 0.65,
            "avg_reduction": 0.12,
            "success_by_value_range": {
                "under_200k": {"success_rate": 0.58, "avg_reduction": 0.08},
                "200k_400k": {"success_rate": 0.68, "avg_reduction": 0.12},
                "400k_600k": {"success_rate": 0.70, "avg_reduction": 0.14},
                "600k_1m": {"success_rate": 0.72, "avg_reduction": 0.16},
                "over_1m": {"success_rate": 0.65, "avg_reduction": 0.18}
            },
            "success_by_increase": {
                "under_10%": {"success_rate": 0.45, "avg_reduction": 0.06},
                "10_20%": {"success_rate": 0.65, "avg_reduction": 0.12},
                "20_30%": {"success_rate": 0.75, "avg_reduction": 0.18},
                "over_30%": {"success_rate": 0.85, "avg_reduction": 0.25}
            },
            "evidence_strength_impact": {
                "weak": 0.7,      # Multiplier for success rate
                "moderate": 1.0,
                "strong": 1.3,
                "very_strong": 1.6
            }
        },
        "commercial": {
            "overall_success_rate": 0.58,
            "avg_reduction": 0.15,
            "success_by_value_range": {
                "under_500k": {"success_rate": 0.52, "avg_reduction": 0.10},
                "500k_1m": {"success_rate": 0.58, "avg_reduction": 0.15},
                "1m_5m": {"success_rate": 0.62, "avg_reduction": 0.18},
                "over_5m": {"success_rate": 0.55, "avg_reduction": 0.20}
            }
        }
    },
    "dallas": {
        "residential": {
            "overall_success_rate": 0.62,
            "avg_reduction": 0.11,
            "success_by_value_range": {
                "under_200k": {"success_rate": 0.55, "avg_reduction": 0.07},
                "200k_400k": {"success_rate": 0.65, "avg_reduction": 0.11},
                "400k_600k": {"success_rate": 0.67, "avg_reduction": 0.13},
                "600k_1m": {"success_rate": 0.69, "avg_reduction": 0.15},
                "over_1m": {"success_rate": 0.62, "avg_reduction": 0.17}
            }
        }
    },
    "travis": {
        "residential": {
            "overall_success_rate": 0.58,
            "avg_reduction": 0.09,
            "success_by_value_range": {
                "under_300k": {"success_rate": 0.52, "avg_reduction": 0.06},
                "300k_500k": {"success_rate": 0.60, "avg_reduction": 0.09},
                "500k_800k": {"success_rate": 0.62, "avg_reduction": 0.11},
                "over_800k": {"success_rate": 0.58, "avg_reduction": 0.13}
            }
        }
    }
}

# Customer qualification criteria and scoring
QUALIFICATION_CRITERIA = {
    "property_value_score": {
        "under_100k": 2,      # Lower value properties = lower score
        "100k_300k": 4,
        "300k_500k": 6,
        "500k_750k": 8,
        "750k_1m": 9,
        "over_1m": 10
    },
    "assessment_increase_score": {
        "under_5%": 2,        # Lower increases = lower score
        "5_10%": 4,
        "10_15%": 6,
        "15_20%": 8,
        "20_25%": 9,
        "over_25%": 10
    },
    "property_type_score": {
        "residential": 7,     # Standard scoring
        "commercial": 9,      # Higher value, more complex
        "industrial": 8,
        "agricultural": 5,    # Lower margins typically
        "vacant": 4
    },
    "county_score": {
        "harris": 8,          # High volume, good success rates
        "dallas": 7,
        "travis": 6,          # Austin market - competitive
        "tarrant": 7,
        "bexar": 6,
        "collin": 8           # High value properties
    },
    "appeal_history_score": {
        "never_appealed": 8,  # First-time appeal often successful
        "successful_appeal": 5,  # Previous success might make it harder
        "unsuccessful_appeal": 3,  # Previous failure is concerning
        "multiple_appeals": 2   # Frequent appeals may indicate difficult case
    }
}

# Lead quality indicators
LEAD_QUALITY_INDICATORS = {
    "very_high": {
        "score_range": (85, 100),
        "characteristics": [
            "Property value over $500K",
            "Assessment increase over 20%",
            "Commercial or high-value residential",
            "Never appealed before",
            "High-success county"
        ],
        "estimated_savings": (5000, 25000),
        "success_probability": 0.75,
        "priority": "immediate_contact"
    },
    "high": {
        "score_range": (70, 84),
        "characteristics": [
            "Property value $300K-$500K",
            "Assessment increase 15-20%",
            "Residential in good county",
            "Limited appeal history"
        ],
        "estimated_savings": (2000, 8000),
        "success_probability": 0.65,
        "priority": "contact_within_24h"
    },
    "medium": {
        "score_range": (50, 69),
        "characteristics": [
            "Property value $200K-$300K",
            "Assessment increase 10-15%",
            "Standard property type",
            "Some appeal history"
        ],
        "estimated_savings": (1000, 3000),
        "success_probability": 0.55,
        "priority": "contact_within_week"
    },
    "low": {
        "score_range": (30, 49),
        "characteristics": [
            "Property value under $200K",
            "Assessment increase under 10%",
            "Lower-value property types",
            "Multiple previous appeals"
        ],
        "estimated_savings": (500, 1500),
        "success_probability": 0.35,
        "priority": "contact_when_available"
    },
    "very_low": {
        "score_range": (0, 29),
        "characteristics": [
            "Very low property value",
            "Minimal assessment increase",
            "Difficult property type or location",
            "Poor appeal history"
        ],
        "estimated_savings": (0, 500),
        "success_probability": 0.20,
        "priority": "do_not_pursue"
    }
}

# Market segment analysis
MARKET_SEGMENTS = {
    "luxury_residential": {
        "value_range": (750000, 5000000),
        "typical_counties": ["harris", "dallas", "travis", "collin"],
        "appeal_characteristics": {
            "success_rate": 0.68,
            "avg_reduction": 0.16,
            "typical_savings": (8000, 40000)
        },
        "customer_profile": {
            "income_range": "high",
            "price_sensitivity": "medium",
            "decision_speed": "fast",
            "preferred_contact": "phone"
        }
    },
    "mid_market_residential": {
        "value_range": (200000, 750000),
        "typical_counties": ["harris", "dallas", "tarrant", "bexar"],
        "appeal_characteristics": {
            "success_rate": 0.62,
            "avg_reduction": 0.12,
            "typical_savings": (2000, 12000)
        },
        "customer_profile": {
            "income_range": "medium",
            "price_sensitivity": "high",
            "decision_speed": "moderate",
            "preferred_contact": "email"
        }
    },
    "commercial_small": {
        "value_range": (200000, 1000000),
        "typical_counties": ["harris", "dallas", "travis"],
        "appeal_characteristics": {
            "success_rate": 0.58,
            "avg_reduction": 0.14,
            "typical_savings": (3000, 15000)
        },
        "customer_profile": {
            "income_range": "business",
            "price_sensitivity": "medium",
            "decision_speed": "slow",
            "preferred_contact": "email"
        }
    },
    "commercial_large": {
        "value_range": (1000000, 20000000),
        "typical_counties": ["harris", "dallas"],
        "appeal_characteristics": {
            "success_rate": 0.55,
            "avg_reduction": 0.18,
            "typical_savings": (15000, 100000)
        },
        "customer_profile": {
            "income_range": "business",
            "price_sensitivity": "low",
            "decision_speed": "very_slow",
            "preferred_contact": "in_person"
        }
    }
}

def calculate_assessment_increase_percentage(current_value: int, previous_value: int) -> float:
    """Calculate assessment increase percentage"""
    if previous_value <= 0:
        return 0.0
    return ((current_value - previous_value) / previous_value) * 100

def get_increase_category(increase_percentage: float) -> str:
    """Categorize assessment increase percentage"""
    if increase_percentage < 5:
        return "under_5%"
    elif increase_percentage < 10:
        return "5_10%"
    elif increase_percentage < 15:
        return "10_15%"
    elif increase_percentage < 20:
        return "15_20%"
    elif increase_percentage < 25:
        return "20_25%"
    else:
        return "over_25%"

def get_value_range_category(property_value: int, property_type: str = "residential") -> str:
    """Categorize property value for scoring"""
    if property_type == "residential":
        if property_value < 100000:
            return "under_100k"
        elif property_value < 300000:
            return "100k_300k"
        elif property_value < 500000:
            return "300k_500k"
        elif property_value < 750000:
            return "500k_750k"
        elif property_value < 1000000:
            return "750k_1m"
        else:
            return "over_1m"

    elif property_type in ["commercial", "industrial"]:
        if property_value < 500000:
            return "under_500k"
        elif property_value < 1000000:
            return "500k_1m"
        elif property_value < 5000000:
            return "1m_5m"
        else:
            return "over_5m"

    else:  # agricultural, vacant
        if property_value < 100000:
            return "under_100k"
        elif property_value < 300000:
            return "100k_300k"
        else:
            return "over_300k"

def estimate_appeal_success_probability(
    county_code: str,
    property_type: str,
    property_value: int,
    assessment_increase: float,
    evidence_strength: str = "moderate"
) -> Dict[str, Any]:
    """Estimate probability of successful appeal"""

    county_data = APPEAL_SUCCESS_PATTERNS.get(county_code.lower(), {})
    property_data = county_data.get(property_type.lower(), {})

    if not property_data:
        # Use default estimates if no specific data
        return {
            "success_probability": 0.50,
            "estimated_reduction": 0.10,
            "confidence": "low",
            "note": "Limited data available for this property type and county"
        }

    # Base success rate
    base_success_rate = property_data["overall_success_rate"]
    base_reduction = property_data["avg_reduction"]

    # Adjust for property value
    value_category = get_value_range_category(property_value, property_type)
    value_data = property_data.get("success_by_value_range", {}).get(value_category, {})

    if value_data:
        value_success_rate = value_data.get("success_rate", base_success_rate)
        value_reduction = value_data.get("avg_reduction", base_reduction)
    else:
        value_success_rate = base_success_rate
        value_reduction = base_reduction

    # Adjust for assessment increase
    increase_category = get_increase_category(assessment_increase)
    increase_data = property_data.get("success_by_increase", {}).get(increase_category, {})

    if increase_data:
        increase_success_rate = increase_data.get("success_rate", value_success_rate)
        increase_reduction = increase_data.get("avg_reduction", value_reduction)
    else:
        # Estimate based on increase level
        if assessment_increase >= 20:
            increase_success_rate = value_success_rate * 1.2
            increase_reduction = value_reduction * 1.3
        elif assessment_increase >= 10:
            increase_success_rate = value_success_rate * 1.1
            increase_reduction = value_reduction * 1.1
        else:
            increase_success_rate = value_success_rate * 0.8
            increase_reduction = value_reduction * 0.8

    # Adjust for evidence strength
    evidence_multiplier = property_data.get("evidence_strength_impact", {}).get(
        evidence_strength, 1.0
    )

    final_success_rate = min(0.95, increase_success_rate * evidence_multiplier)
    final_reduction = min(0.30, increase_reduction * evidence_multiplier)

    return {
        "success_probability": round(final_success_rate, 3),
        "estimated_reduction": round(final_reduction, 3),
        "confidence": "high" if county_data and property_data else "medium",
        "value_category": value_category,
        "increase_category": increase_category,
        "evidence_strength": evidence_strength
    }

def calculate_estimated_savings(
    property_value: int,
    tax_rate: float,
    estimated_reduction: float,
    success_probability: float
) -> Dict[str, Any]:
    """Calculate estimated tax savings from appeal"""

    # Calculate potential value reduction
    potential_value_reduction = int(property_value * estimated_reduction)

    # Calculate annual tax savings
    annual_tax_savings = int(potential_value_reduction * tax_rate)

    # Calculate expected value (accounting for success probability)
    expected_annual_savings = int(annual_tax_savings * success_probability)

    # Multi-year savings (assuming 5-year impact)
    five_year_savings = expected_annual_savings * 5

    return {
        "potential_value_reduction": potential_value_reduction,
        "annual_tax_savings": annual_tax_savings,
        "expected_annual_savings": expected_annual_savings,
        "five_year_expected_savings": five_year_savings,
        "success_probability": success_probability,
        "estimated_reduction_percent": estimated_reduction
    }

def determine_market_segment(property_value: int, property_type: str) -> Optional[str]:
    """Determine market segment for a property"""
    for segment_name, segment_data in MARKET_SEGMENTS.items():
        value_range = segment_data["value_range"]
        if (value_range[0] <= property_value <= value_range[1] and
            property_type.lower() in segment_name.lower()):
            return segment_name

    return None

def get_historical_trends(county_code: str, property_type: str, years: int = 5) -> Dict[str, Any]:
    """Get historical assessment trends for analysis"""
    pattern_data = ASSESSMENT_INCREASE_PATTERNS.get(county_code.lower(), {}).get(property_type.lower(), {})

    if not pattern_data:
        return {"error": "No historical data available"}

    avg_increase = pattern_data["avg_annual_increase"]
    std_dev = pattern_data["std_deviation"]

    # Generate historical trend simulation
    historical_increases = []
    base_year = datetime.now().year - years

    for year in range(years):
        # Simulate annual increase with some randomness
        annual_increase = max(0, random.normalvariate(avg_increase, std_dev))
        historical_increases.append({
            "year": base_year + year,
            "increase_percentage": round(annual_increase * 100, 2),
            "market_conditions": "normal"  # Could be enhanced with real market data
        })

    return {
        "county": county_code,
        "property_type": property_type,
        "average_annual_increase": round(avg_increase * 100, 2),
        "typical_range": [round(x * 100, 2) for x in pattern_data["typical_range"]],
        "high_increase_threshold": round(pattern_data["high_increase_threshold"] * 100, 2),
        "historical_years": historical_increases,
        "protest_likelihood": pattern_data.get("protest_likelihood_by_increase", {})
    }