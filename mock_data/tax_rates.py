"""
Tax Rates and Exemption Data for Texas Counties

Comprehensive tax rate information including county rates, school district rates,
municipal rates, and various exemption values for accurate savings calculations.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime


# Detailed tax rate structure for major Texas counties
COUNTY_TAX_RATES = {
    "harris": {
        "county_name": "Harris County",
        "county_rate": 0.004270,
        "school_districts": {
            "houston_isd": {
                "name": "Houston Independent School District",
                "rate": 0.012830,
                "homestead_cap": 0.10  # 10% cap on homestead increases
            },
            "cypress_fairbanks_isd": {
                "name": "Cypress-Fairbanks Independent School District",
                "rate": 0.013800,
                "homestead_cap": 0.10
            },
            "spring_isd": {
                "name": "Spring Independent School District",
                "rate": 0.014200,
                "homestead_cap": 0.10
            },
            "klein_isd": {
                "name": "Klein Independent School District",
                "rate": 0.013900,
                "homestead_cap": 0.10
            }
        },
        "cities": {
            "houston": {"rate": 0.005789, "homestead_exemption": 0},
            "pasadena": {"rate": 0.006200, "homestead_exemption": 0},
            "baytown": {"rate": 0.007100, "homestead_exemption": 0},
            "humble": {"rate": 0.005800, "homestead_exemption": 0},
            "tomball": {"rate": 0.004900, "homestead_exemption": 0}
        },
        "other_entities": {
            "hcfcd": {"name": "Harris County Flood Control District", "rate": 0.002680},
            "port_of_houston": {"name": "Port of Houston Authority", "rate": 0.000133},
            "houston_community_college": {"name": "Houston Community College", "rate": 0.003570}
        },
        "exemptions": {
            "homestead": 100000,
            "senior_citizen": 10000,
            "disability": 12000,
            "disabled_veteran": {
                "10_29_percent": 5000,
                "30_49_percent": 7500,
                "50_69_percent": 10000,
                "70_100_percent": 12000,
                "100_percent_unemployable": "full_exemption"
            },
            "surviving_spouse": 3000,
            "charitable": "full_exemption",
            "religious": "full_exemption"
        }
    },
    "dallas": {
        "county_name": "Dallas County",
        "county_rate": 0.002650,
        "school_districts": {
            "dallas_isd": {
                "name": "Dallas Independent School District",
                "rate": 0.013700,
                "homestead_cap": 0.10
            },
            "plano_isd": {
                "name": "Plano Independent School District",
                "rate": 0.011900,
                "homestead_cap": 0.10
            },
            "richardson_isd": {
                "name": "Richardson Independent School District",
                "rate": 0.013200,
                "homestead_cap": 0.10
            },
            "garland_isd": {
                "name": "Garland Independent School District",
                "rate": 0.013500,
                "homestead_cap": 0.10
            }
        },
        "cities": {
            "dallas": {"rate": 0.007950, "homestead_exemption": 0},
            "garland": {"rate": 0.007200, "homestead_exemption": 0},
            "irving": {"rate": 0.006800, "homestead_exemption": 0},
            "mesquite": {"rate": 0.007500, "homestead_exemption": 0},
            "richardson": {"rate": 0.006900, "homestead_exemption": 0}
        },
        "other_entities": {
            "dallas_county_community_college": {"name": "Dallas County Community College District", "rate": 0.002890},
            "dart": {"name": "Dallas Area Rapid Transit", "rate": 0.001000}
        },
        "exemptions": {
            "homestead": 100000,
            "senior_citizen": 10000,
            "disability": 12000,
            "disabled_veteran": {
                "10_29_percent": 5000,
                "30_49_percent": 7500,
                "50_69_percent": 10000,
                "70_100_percent": 12000,
                "100_percent_unemployable": "full_exemption"
            },
            "surviving_spouse": 3000
        }
    },
    "tarrant": {
        "county_name": "Tarrant County",
        "county_rate": 0.002360,
        "school_districts": {
            "fort_worth_isd": {
                "name": "Fort Worth Independent School District",
                "rate": 0.012900,
                "homestead_cap": 0.10
            },
            "arlington_isd": {
                "name": "Arlington Independent School District",
                "rate": 0.013100,
                "homestead_cap": 0.10
            },
            "heb_isd": {
                "name": "Hurst-Euless-Bedford Independent School District",
                "rate": 0.012500,
                "homestead_cap": 0.10
            }
        },
        "cities": {
            "fort_worth": {"rate": 0.007450, "homestead_exemption": 0},
            "arlington": {"rate": 0.006550, "homestead_exemption": 0},
            "grand_prairie": {"rate": 0.006900, "homestead_exemption": 0},
            "carrollton": {"rate": 0.005800, "homestead_exemption": 0}
        },
        "other_entities": {
            "tarrant_county_college": {"name": "Tarrant County College District", "rate": 0.001870},
            "trinity_metro": {"name": "Trinity Metro", "rate": 0.000315}
        },
        "exemptions": {
            "homestead": 100000,
            "senior_citizen": 10000,
            "disability": 12000,
            "disabled_veteran": {
                "10_29_percent": 5000,
                "30_49_percent": 7500,
                "50_69_percent": 10000,
                "70_100_percent": 12000,
                "100_percent_unemployable": "full_exemption"
            }
        }
    },
    "travis": {
        "county_name": "Travis County",
        "county_rate": 0.004080,
        "school_districts": {
            "austin_isd": {
                "name": "Austin Independent School District",
                "rate": 0.010700,
                "homestead_cap": 0.10
            },
            "round_rock_isd": {
                "name": "Round Rock Independent School District",
                "rate": 0.009900,
                "homestead_cap": 0.10
            },
            "pflugerville_isd": {
                "name": "Pflugerville Independent School District",
                "rate": 0.011200,
                "homestead_cap": 0.10
            }
        },
        "cities": {
            "austin": {"rate": 0.004369, "homestead_exemption": 0},
            "cedar_park": {"rate": 0.004200, "homestead_exemption": 0},
            "pflugerville": {"rate": 0.004800, "homestead_exemption": 0},
            "round_rock": {"rate": 0.003900, "homestead_exemption": 0}
        },
        "other_entities": {
            "austin_community_college": {"name": "Austin Community College District", "rate": 0.001040},
            "central_health": {"name": "Central Health", "rate": 0.007789}
        },
        "exemptions": {
            "homestead": 100000,
            "senior_citizen": 10000,
            "disability": 12000,
            "disabled_veteran": {
                "10_29_percent": 5000,
                "30_49_percent": 7500,
                "50_69_percent": 10000,
                "70_100_percent": 12000,
                "100_percent_unemployable": "full_exemption"
            }
        }
    },
    "bexar": {
        "county_name": "Bexar County",
        "county_rate": 0.003180,
        "school_districts": {
            "san_antonio_isd": {
                "name": "San Antonio Independent School District",
                "rate": 0.014630,
                "homestead_cap": 0.10
            },
            "northside_isd": {
                "name": "Northside Independent School District",
                "rate": 0.012800,
                "homestead_cap": 0.10
            },
            "northeast_isd": {
                "name": "Northeast Independent School District",
                "rate": 0.013100,
                "homestead_cap": 0.10
            }
        },
        "cities": {
            "san_antonio": {"rate": 0.005561, "homestead_exemption": 0},
            "universal_city": {"rate": 0.005200, "homestead_exemption": 0},
            "alamo_heights": {"rate": 0.004800, "homestead_exemption": 0}
        },
        "other_entities": {
            "alamo_community_college": {"name": "Alamo Community College District", "rate": 0.001320},
            "via_metropolitan_transit": {"name": "VIA Metropolitan Transit", "rate": 0.000625}
        },
        "exemptions": {
            "homestead": 100000,
            "senior_citizen": 10000,
            "disability": 12000,
            "disabled_veteran": {
                "10_29_percent": 5000,
                "30_49_percent": 7500,
                "50_69_percent": 10000,
                "70_100_percent": 12000,
                "100_percent_unemployable": "full_exemption"
            }
        }
    },
    "collin": {
        "county_name": "Collin County",
        "county_rate": 0.001870,
        "school_districts": {
            "plano_isd": {
                "name": "Plano Independent School District",
                "rate": 0.011900,
                "homestead_cap": 0.10
            },
            "frisco_isd": {
                "name": "Frisco Independent School District",
                "rate": 0.011000,
                "homestead_cap": 0.10
            },
            "mckinney_isd": {
                "name": "McKinney Independent School District",
                "rate": 0.012200,
                "homestead_cap": 0.10
            },
            "allen_isd": {
                "name": "Allen Independent School District",
                "rate": 0.011500,
                "homestead_cap": 0.10
            }
        },
        "cities": {
            "plano": {"rate": 0.004760, "homestead_exemption": 0},
            "frisco": {"rate": 0.004200, "homestead_exemption": 0},
            "mckinney": {"rate": 0.005200, "homestead_exemption": 0},
            "allen": {"rate": 0.004900, "homestead_exemption": 0},
            "richardson": {"rate": 0.006900, "homestead_exemption": 0}
        },
        "other_entities": {
            "collin_college": {"name": "Collin College", "rate": 0.001680}
        },
        "exemptions": {
            "homestead": 100000,
            "senior_citizen": 10000,
            "disability": 12000,
            "disabled_veteran": {
                "10_29_percent": 5000,
                "30_49_percent": 7500,
                "50_69_percent": 10000,
                "70_100_percent": 12000,
                "100_percent_unemployable": "full_exemption"
            }
        }
    }
}

# Appeal success rates by property type and county
APPEAL_SUCCESS_RATES = {
    "harris": {
        "residential": {"success_rate": 0.65, "avg_reduction": 0.12},
        "commercial": {"success_rate": 0.58, "avg_reduction": 0.15},
        "industrial": {"success_rate": 0.52, "avg_reduction": 0.18},
        "agricultural": {"success_rate": 0.45, "avg_reduction": 0.08}
    },
    "dallas": {
        "residential": {"success_rate": 0.62, "avg_reduction": 0.11},
        "commercial": {"success_rate": 0.55, "avg_reduction": 0.14},
        "industrial": {"success_rate": 0.48, "avg_reduction": 0.16},
        "agricultural": {"success_rate": 0.42, "avg_reduction": 0.07}
    },
    "tarrant": {
        "residential": {"success_rate": 0.60, "avg_reduction": 0.10},
        "commercial": {"success_rate": 0.53, "avg_reduction": 0.13},
        "industrial": {"success_rate": 0.46, "avg_reduction": 0.15},
        "agricultural": {"success_rate": 0.40, "avg_reduction": 0.06}
    },
    "travis": {
        "residential": {"success_rate": 0.58, "avg_reduction": 0.09},
        "commercial": {"success_rate": 0.51, "avg_reduction": 0.12},
        "industrial": {"success_rate": 0.44, "avg_reduction": 0.14},
        "agricultural": {"success_rate": 0.38, "avg_reduction": 0.05}
    },
    "bexar": {
        "residential": {"success_rate": 0.56, "avg_reduction": 0.08},
        "commercial": {"success_rate": 0.49, "avg_reduction": 0.11},
        "industrial": {"success_rate": 0.42, "avg_reduction": 0.13},
        "agricultural": {"success_rate": 0.36, "avg_reduction": 0.04}
    },
    "collin": {
        "residential": {"success_rate": 0.68, "avg_reduction": 0.13},
        "commercial": {"success_rate": 0.61, "avg_reduction": 0.16},
        "industrial": {"success_rate": 0.55, "avg_reduction": 0.19},
        "agricultural": {"success_rate": 0.48, "avg_reduction": 0.09}
    }
}

# Exemption qualification criteria
EXEMPTION_CRITERIA = {
    "homestead": {
        "name": "Homestead Exemption",
        "description": "Primary residence exemption available to all Texas homeowners",
        "value": 100000,  # Standard across most counties
        "requirements": [
            "Property must be primary residence",
            "Owner must occupy property as of January 1",
            "Must apply before April 30"
        ],
        "qualification_rate": 0.60  # 60% of residential properties qualify
    },
    "senior_citizen": {
        "name": "Senior Citizen Exemption",
        "description": "Additional exemption for homeowners 65 and older",
        "value": 10000,
        "requirements": [
            "Homeowner must be 65 or older as of January 1",
            "Must qualify for homestead exemption",
            "Provides tax ceiling at age 65 amount"
        ],
        "qualification_rate": 0.15
    },
    "disability": {
        "name": "Disability Exemption",
        "description": "Exemption for disabled homeowners",
        "value": 12000,
        "requirements": [
            "Must have qualifying disability",
            "Must qualify for homestead exemption",
            "Requires certification from authorized physician"
        ],
        "qualification_rate": 0.05
    },
    "disabled_veteran": {
        "name": "Disabled Veteran Exemption",
        "description": "Graduated exemption based on disability rating",
        "values": {
            "10_29_percent": 5000,
            "30_49_percent": 7500,
            "50_69_percent": 10000,
            "70_100_percent": 12000,
            "100_percent_unemployable": "full_exemption"
        },
        "requirements": [
            "Must be service-connected disabled veteran",
            "Disability rating from VA required",
            "100% unemployable rating qualifies for full exemption"
        ],
        "qualification_rate": 0.08
    },
    "surviving_spouse": {
        "name": "Surviving Spouse Exemption",
        "description": "Exemption for surviving spouse of disabled veteran",
        "value": 3000,
        "requirements": [
            "Spouse of disabled veteran who died from service-connected cause",
            "Must not have remarried",
            "Property must be homestead"
        ],
        "qualification_rate": 0.02
    },
    "agricultural": {
        "name": "Agricultural Use Exemption",
        "description": "Special use valuation for agricultural land",
        "description_detailed": "Property valued based on agricultural productivity rather than market value",
        "requirements": [
            "Land must be in agricultural use for 5 consecutive years",
            "Minimum acreage requirements (typically 5-10 acres)",
            "Must demonstrate agricultural activity and income"
        ],
        "typical_savings": 0.60,  # 60% reduction in assessed value
        "qualification_rate": 0.80  # 80% of agricultural properties qualify
    }
}

def calculate_total_tax_rate(county_code: str, city: str, school_district: str) -> Dict[str, Any]:
    """Calculate total tax rate for a specific jurisdiction"""
    county_data = COUNTY_TAX_RATES.get(county_code.lower())
    if not county_data:
        return {"error": "County not found"}

    total_rate = county_data["county_rate"]
    breakdown = {"county": county_data["county_rate"]}

    # Add school district rate
    if school_district and school_district in county_data["school_districts"]:
        sd_rate = county_data["school_districts"][school_district]["rate"]
        total_rate += sd_rate
        breakdown["school_district"] = sd_rate

    # Add city rate
    if city and city in county_data["cities"]:
        city_rate = county_data["cities"][city]["rate"]
        total_rate += city_rate
        breakdown["city"] = city_rate

    # Add other entities (typically apply to all properties in county)
    other_total = 0
    for entity, info in county_data.get("other_entities", {}).items():
        other_total += info["rate"]
        breakdown[entity] = info["rate"]

    total_rate += other_total

    return {
        "total_rate": round(total_rate, 6),
        "breakdown": breakdown,
        "effective_rate_per_100": round(total_rate * 100, 4)
    }

def calculate_exemption_value(exemptions_applied: Dict[str, Any], county_code: str) -> int:
    """Calculate total exemption value"""
    county_data = COUNTY_TAX_RATES.get(county_code.lower(), {})
    exemption_data = county_data.get("exemptions", {})

    total_exemption = 0

    if exemptions_applied.get("homestead"):
        total_exemption += exemption_data.get("homestead", 100000)

    if exemptions_applied.get("senior"):
        total_exemption += exemption_data.get("senior_citizen", 10000)

    if exemptions_applied.get("disability"):
        total_exemption += exemption_data.get("disability", 12000)

    if exemptions_applied.get("veteran"):
        # For simplicity, using 70-100% rating
        veteran_exemptions = exemption_data.get("disabled_veteran", {})
        total_exemption += veteran_exemptions.get("70_100_percent", 12000)

    return total_exemption

def estimate_appeal_outcome(
    current_value: int,
    property_type: str,
    county_code: str,
    evidence_strength: str = "moderate"
) -> Dict[str, Any]:
    """Estimate likely outcome of property tax appeal"""

    success_data = APPEAL_SUCCESS_RATES.get(county_code.lower(), {}).get(property_type.lower())
    if not success_data:
        return {"error": "No data available for this property type and county"}

    base_success_rate = success_data["success_rate"]
    base_reduction = success_data["avg_reduction"]

    # Adjust based on evidence strength
    strength_multipliers = {
        "weak": {"success": 0.7, "reduction": 0.6},
        "moderate": {"success": 1.0, "reduction": 1.0},
        "strong": {"success": 1.3, "reduction": 1.4},
        "very_strong": {"success": 1.5, "reduction": 1.6}
    }

    multiplier = strength_multipliers.get(evidence_strength, strength_multipliers["moderate"])

    adjusted_success_rate = min(0.95, base_success_rate * multiplier["success"])
    adjusted_reduction = min(0.30, base_reduction * multiplier["reduction"])

    potential_new_value = int(current_value * (1 - adjusted_reduction))
    potential_savings = current_value - potential_new_value

    return {
        "success_probability": round(adjusted_success_rate, 3),
        "estimated_reduction_percent": round(adjusted_reduction, 3),
        "current_assessed_value": current_value,
        "potential_new_value": potential_new_value,
        "potential_value_reduction": potential_savings,
        "evidence_strength": evidence_strength
    }

def get_county_tax_info(county_code: str) -> Optional[Dict[str, Any]]:
    """Get comprehensive tax information for a county"""
    return COUNTY_TAX_RATES.get(county_code.lower())

def get_exemption_info(exemption_type: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific exemption"""
    return EXEMPTION_CRITERIA.get(exemption_type.lower())

def get_available_exemptions() -> List[str]:
    """Get list of all available exemption types"""
    return list(EXEMPTION_CRITERIA.keys())