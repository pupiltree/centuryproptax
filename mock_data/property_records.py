"""
Mock Property Records for Texas Counties

Comprehensive property database with realistic Texas property data
including addresses, parcel IDs, assessments, and characteristics.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random


# Texas Counties and their characteristics
TEXAS_COUNTIES = {
    "harris": {
        "name": "Harris County",
        "tax_rate": 0.0255,
        "homestead_exemption": 100000,
        "senior_exemption": 10000,
        "disability_exemption": 12000,
        "cities": ["Houston", "Pasadena", "Baytown", "Humble", "Tomball"]
    },
    "dallas": {
        "name": "Dallas County",
        "tax_rate": 0.0238,
        "homestead_exemption": 100000,
        "senior_exemption": 10000,
        "disability_exemption": 12000,
        "cities": ["Dallas", "Garland", "Irving", "Mesquite", "Richardson"]
    },
    "tarrant": {
        "name": "Tarrant County",
        "tax_rate": 0.0241,
        "homestead_exemption": 100000,
        "senior_exemption": 10000,
        "disability_exemption": 12000,
        "cities": ["Fort Worth", "Arlington", "Plano", "Grand Prairie", "Carrollton"]
    },
    "travis": {
        "name": "Travis County",
        "tax_rate": 0.0267,
        "homestead_exemption": 100000,
        "senior_exemption": 10000,
        "disability_exemption": 12000,
        "cities": ["Austin", "Cedar Park", "Pflugerville", "Round Rock", "Lakeway"]
    },
    "bexar": {
        "name": "Bexar County",
        "tax_rate": 0.0249,
        "homestead_exemption": 100000,
        "senior_exemption": 10000,
        "disability_exemption": 12000,
        "cities": ["San Antonio", "Universal City", "Alamo Heights", "Converse", "Leon Valley"]
    },
    "collin": {
        "name": "Collin County",
        "tax_rate": 0.0226,
        "homestead_exemption": 100000,
        "senior_exemption": 10000,
        "disability_exemption": 12000,
        "cities": ["Plano", "Frisco", "McKinney", "Allen", "Richardson"]
    }
}

# Property types and their characteristics
PROPERTY_TYPES = {
    "residential": {
        "codes": ["R1", "R2", "R3", "RES"],
        "description": "Residential Property",
        "typical_value_range": (75000, 800000),
        "land_ratio": 0.25  # Land value as % of total
    },
    "commercial": {
        "codes": ["C1", "C2", "C3", "COM"],
        "description": "Commercial Property",
        "typical_value_range": (200000, 2000000),
        "land_ratio": 0.40
    },
    "industrial": {
        "codes": ["I1", "I2", "IND"],
        "description": "Industrial Property",
        "typical_value_range": (150000, 1500000),
        "land_ratio": 0.35
    },
    "agricultural": {
        "codes": ["AG", "AGR", "A1"],
        "description": "Agricultural Property",
        "typical_value_range": (50000, 500000),
        "land_ratio": 0.80
    },
    "vacant": {
        "codes": ["VAC", "V1", "VL"],
        "description": "Vacant Land",
        "typical_value_range": (10000, 200000),
        "land_ratio": 1.0
    }
}

def generate_parcel_id(county_code: str, property_type: str) -> str:
    """Generate realistic Texas parcel ID"""
    type_prefix = PROPERTY_TYPES[property_type]["codes"][0]
    district = random.randint(100, 999)
    block = random.randint(1000, 9999)
    lot = random.randint(100, 999)
    return f"{county_code.upper()}-{type_prefix}-{district}-{block}-{lot}"

def generate_address(city: str, property_type: str) -> Dict[str, str]:
    """Generate realistic Texas addresses"""

    # Street types common in Texas
    street_types = ["St", "Ave", "Dr", "Ln", "Rd", "Blvd", "Way", "Ct", "Pl", "Trl"]

    # Texas-specific street names
    street_names = [
        "Main", "Oak", "Pine", "Elm", "Cedar", "Maple", "Pecan", "Live Oak",
        "Bluebonnet", "Mockingbird", "Cardinal", "Meadowbrook", "Spring Creek",
        "Ranch", "Prairie", "Heritage", "Legacy", "Liberty", "Independence",
        "Republic", "Lone Star", "Alamo", "San Jacinto", "Buffalo Bayou"
    ]

    # Different number patterns for property types
    if property_type == "commercial":
        number = random.randint(100, 9999)
        if random.random() < 0.3:  # Some commercial have suite numbers
            suite = random.randint(100, 999)
            return {
                "street_number": str(number),
                "street_name": f"{random.choice(street_names)} {random.choice(street_types)}",
                "suite": f"Suite {suite}",
                "city": city,
                "state": "TX",
                "zip_code": f"{random.randint(70000, 79999)}"
            }

    number = random.randint(100, 9999)
    return {
        "street_number": str(number),
        "street_name": f"{random.choice(street_names)} {random.choice(street_types)}",
        "city": city,
        "state": "TX",
        "zip_code": f"{random.randint(70000, 79999)}"
    }

def generate_assessment_history(current_value: int, years: int = 5) -> List[Dict[str, Any]]:
    """Generate realistic assessment history with Texas market trends"""
    history = []
    base_year = datetime.now().year - years

    # Start with a lower value and trend upward (Texas property appreciation)
    initial_value = int(current_value * random.uniform(0.6, 0.8))

    for year in range(years + 1):
        # Texas has seen steady appreciation with some volatility
        if year == 0:
            value = initial_value
        else:
            # Annual appreciation between 2-8% with some years higher
            appreciation = random.uniform(0.02, 0.08)
            if random.random() < 0.2:  # 20% chance of higher appreciation
                appreciation = random.uniform(0.08, 0.15)
            value = int(history[-1]["assessed_value"] * (1 + appreciation))

        # Land value typically appreciates faster than improvements
        land_ratio = PROPERTY_TYPES.get("residential", {}).get("land_ratio", 0.25)
        land_value = int(value * land_ratio)
        improvement_value = value - land_value

        history.append({
            "tax_year": base_year + year,
            "assessed_value": value,
            "land_value": land_value,
            "improvement_value": improvement_value,
            "assessment_date": f"{base_year + year}-01-01",
            "market_value": int(value * random.uniform(0.95, 1.05)),  # Assessed vs market variation
            "protested": random.random() < 0.15,  # 15% chance of protest
            "protest_outcome": None
        })

        # Add protest outcomes for protested assessments
        if history[-1]["protested"]:
            outcomes = ["reduced", "upheld", "settled"]
            outcome = random.choice(outcomes)
            history[-1]["protest_outcome"] = outcome

            if outcome == "reduced":
                reduction = random.uniform(0.05, 0.20)  # 5-20% reduction
                history[-1]["final_value"] = int(value * (1 - reduction))
            elif outcome == "settled":
                reduction = random.uniform(0.02, 0.10)  # 2-10% reduction in settlement
                history[-1]["final_value"] = int(value * (1 - reduction))
            else:
                history[-1]["final_value"] = value
        else:
            history[-1]["final_value"] = value

    return history

def generate_property_characteristics(property_type: str, assessed_value: int) -> Dict[str, Any]:
    """Generate realistic property characteristics based on type and value"""

    if property_type == "residential":
        # Higher value homes tend to be larger and newer
        value_factor = min(assessed_value / 200000, 4.0)  # Cap the factor

        return {
            "square_feet": int(random.uniform(1200, 1800) * value_factor),
            "bedrooms": random.randint(2, 5),
            "bathrooms": round(random.uniform(1.5, 3.5), 1),
            "year_built": random.randint(1960, 2023),
            "garage_spaces": random.randint(0, 3),
            "pool": random.random() < (0.3 if assessed_value > 300000 else 0.1),
            "lot_size": random.uniform(0.15, 1.2),  # acres
            "stories": random.randint(1, 2),
            "exterior": random.choice(["Brick", "Siding", "Stucco", "Stone", "Mixed"]),
            "roof": random.choice(["Composition", "Tile", "Metal"])
        }

    elif property_type == "commercial":
        return {
            "square_feet": random.randint(2000, 50000),
            "building_class": random.choice(["A", "B", "C"]),
            "year_built": random.randint(1970, 2023),
            "parking_spaces": random.randint(10, 200),
            "units": random.randint(1, 20),
            "lot_size": random.uniform(0.5, 5.0),  # acres
            "zoning": random.choice(["C1", "C2", "C3"]),
            "use_type": random.choice(["Retail", "Office", "Warehouse", "Mixed Use"])
        }

    elif property_type == "industrial":
        return {
            "square_feet": random.randint(5000, 100000),
            "year_built": random.randint(1960, 2023),
            "dock_doors": random.randint(0, 20),
            "ceiling_height": random.randint(12, 32),
            "lot_size": random.uniform(1.0, 20.0),  # acres
            "rail_access": random.random() < 0.3,
            "zoning": random.choice(["I1", "I2", "M1"]),
            "use_type": random.choice(["Manufacturing", "Warehouse", "Distribution"])
        }

    elif property_type == "agricultural":
        return {
            "total_acres": random.uniform(10, 500),
            "agricultural_use": random.choice(["Livestock", "Crops", "Mixed", "Pasture"]),
            "year_built": random.randint(1950, 2020) if random.random() < 0.7 else None,
            "agricultural_exemption": random.random() < 0.8,
            "water_rights": random.random() < 0.4,
            "mineral_rights": random.random() < 0.2,
            "fencing": random.choice(["Full", "Partial", "None"]),
            "water_source": random.choice(["Well", "Creek", "Pond", "Municipal"])
        }

    else:  # vacant
        return {
            "lot_size": random.uniform(0.1, 5.0),  # acres
            "zoning": random.choice(["R1", "R2", "C1", "I1"]),
            "utilities": random.choice(["All", "Partial", "None"]),
            "access": random.choice(["Paved", "Gravel", "Dirt"]),
            "topography": random.choice(["Level", "Sloped", "Mixed"]),
            "flood_zone": random.random() < 0.1  # 10% in flood zone
        }

# Generate 150+ realistic property records
PROPERTY_RECORDS = []

def generate_property_records() -> List[Dict[str, Any]]:
    """Generate comprehensive property database"""
    records = []

    for county_code, county_info in TEXAS_COUNTIES.items():
        # Generate 25-30 properties per county
        properties_per_county = random.randint(25, 30)

        for _ in range(properties_per_county):
            # Select property type (weighted toward residential)
            property_type = random.choices(
                list(PROPERTY_TYPES.keys()),
                weights=[60, 20, 10, 8, 2],  # Favor residential
                k=1
            )[0]

            # Generate property value within type range
            value_range = PROPERTY_TYPES[property_type]["typical_value_range"]
            assessed_value = random.randint(value_range[0], value_range[1])

            # Select city
            city = random.choice(county_info["cities"])

            # Generate address
            address = generate_address(city, property_type)

            # Create property record
            record = {
                "parcel_id": generate_parcel_id(county_code, property_type),
                "property_type": property_type,
                "property_type_code": random.choice(PROPERTY_TYPES[property_type]["codes"]),
                "address": address,
                "county": county_info["name"],
                "county_code": county_code,
                "assessed_value": assessed_value,
                "assessment_history": generate_assessment_history(assessed_value),
                "characteristics": generate_property_characteristics(property_type, assessed_value),
                "owner": {
                    "name": f"Owner {random.randint(1000, 9999)}",  # Anonymized
                    "mailing_same_as_property": random.random() < 0.7,
                    "owner_occupied": random.random() < 0.6 if property_type == "residential" else False
                },
                "exemptions": {
                    "homestead": random.random() < 0.6 if property_type == "residential" else False,
                    "senior": random.random() < 0.15 if property_type == "residential" else False,
                    "disability": random.random() < 0.05 if property_type == "residential" else False,
                    "veteran": random.random() < 0.08 if property_type == "residential" else False,
                    "agricultural": property_type == "agricultural" and random.random() < 0.8
                },
                "status": random.choice(["active", "active", "active", "pending_sale"]),  # Mostly active
                "last_updated": datetime.now().isoformat(),
                "data_source": "county_appraisal_district"
            }

            records.append(record)

    return records

# Generate the records when module is imported
PROPERTY_RECORDS = generate_property_records()

def find_property_by_address(address: str) -> Optional[Dict[str, Any]]:
    """Find property by address string"""
    address_lower = address.lower()

    for record in PROPERTY_RECORDS:
        prop_address = record["address"]
        full_address = f"{prop_address['street_number']} {prop_address['street_name']}, {prop_address['city']}, {prop_address['state']} {prop_address['zip_code']}"

        if address_lower in full_address.lower():
            return record

    return None

def find_property_by_parcel_id(parcel_id: str) -> Optional[Dict[str, Any]]:
    """Find property by parcel ID"""
    for record in PROPERTY_RECORDS:
        if record["parcel_id"] == parcel_id.upper():
            return record

    return None

def search_properties_by_criteria(
    county: Optional[str] = None,
    property_type: Optional[str] = None,
    value_min: Optional[int] = None,
    value_max: Optional[int] = None,
    city: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search properties by various criteria"""
    results = []

    for record in PROPERTY_RECORDS:
        # County filter
        if county and county.lower() not in record["county"].lower():
            continue

        # Property type filter
        if property_type and property_type.lower() != record["property_type"].lower():
            continue

        # Value range filter
        if value_min and record["assessed_value"] < value_min:
            continue
        if value_max and record["assessed_value"] > value_max:
            continue

        # City filter
        if city and city.lower() != record["address"]["city"].lower():
            continue

        results.append(record)

    return results

def get_property_statistics() -> Dict[str, Any]:
    """Get statistics about the property database"""
    total_properties = len(PROPERTY_RECORDS)

    by_type = {}
    by_county = {}
    value_sum = 0

    for record in PROPERTY_RECORDS:
        # Count by type
        prop_type = record["property_type"]
        by_type[prop_type] = by_type.get(prop_type, 0) + 1

        # Count by county
        county = record["county"]
        by_county[county] = by_county.get(county, 0) + 1

        # Sum values
        value_sum += record["assessed_value"]

    return {
        "total_properties": total_properties,
        "by_property_type": by_type,
        "by_county": by_county,
        "average_assessed_value": value_sum // total_properties if total_properties > 0 else 0,
        "counties_covered": list(TEXAS_COUNTIES.keys()),
        "property_types_available": list(PROPERTY_TYPES.keys())
    }