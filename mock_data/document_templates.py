"""
Document Templates and OCR Response Data for Property Tax Documents

Mock document processing data including tax statements, appraisal notices,
appeal forms, and OCR extraction patterns for testing document analysis.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
import random
import re


# Document type definitions
DOCUMENT_TYPES = {
    "appraisal_notice": {
        "name": "Property Appraisal Notice",
        "typical_pages": 2,
        "key_fields": [
            "property_address", "parcel_id", "owner_name", "assessed_value",
            "land_value", "improvement_value", "previous_value", "tax_year",
            "appeal_deadline", "appraisal_district"
        ],
        "common_variations": ["notice_of_appraised_value", "assessment_notice"],
        "issuing_authority": "County Appraisal District"
    },
    "tax_statement": {
        "name": "Property Tax Statement",
        "typical_pages": 1,
        "key_fields": [
            "property_address", "parcel_id", "owner_name", "assessed_value",
            "exemptions", "taxable_value", "tax_amount", "due_date",
            "discount_date", "penalty_date", "taxing_entities"
        ],
        "common_variations": ["tax_bill", "property_tax_bill"],
        "issuing_authority": "County Tax Assessor-Collector"
    },
    "protest_form": {
        "name": "Property Tax Protest Form",
        "typical_pages": 3,
        "key_fields": [
            "property_address", "parcel_id", "owner_name", "protest_reason",
            "requested_value", "current_value", "evidence_description",
            "hearing_preference", "contact_information"
        ],
        "common_variations": ["notice_of_protest", "arb_protest_form"],
        "issuing_authority": "County Appraisal District"
    },
    "exemption_application": {
        "name": "Exemption Application",
        "typical_pages": 2,
        "key_fields": [
            "property_address", "parcel_id", "owner_name", "exemption_type",
            "qualification_details", "supporting_documentation",
            "application_date", "effective_date"
        ],
        "common_variations": ["homestead_application", "senior_exemption_form"],
        "issuing_authority": "County Appraisal District"
    },
    "comparable_sales": {
        "name": "Comparable Sales Report",
        "typical_pages": 5,
        "key_fields": [
            "subject_property", "comparable_properties", "sale_dates",
            "sale_prices", "adjustments", "final_value_opinion",
            "property_characteristics", "market_analysis"
        ],
        "common_variations": ["market_analysis", "property_valuation"],
        "issuing_authority": "Appraiser or Property Owner"
    },
    "hearing_notice": {
        "name": "ARB Hearing Notice",
        "typical_pages": 1,
        "key_fields": [
            "property_address", "parcel_id", "hearing_date", "hearing_time",
            "hearing_location", "panel_type", "preparation_instructions",
            "contact_information"
        ],
        "common_variations": ["hearing_notification", "arb_schedule"],
        "issuing_authority": "Appraisal Review Board"
    }
}

# Sample OCR extraction patterns for different document types
OCR_EXTRACTION_PATTERNS = {
    "appraisal_notice": {
        "patterns": {
            "property_address": [
                r"Property Address[:\s]+(.+?)(?:\n|$)",
                r"Property Location[:\s]+(.+?)(?:\n|$)",
                r"PROPERTY[:\s]+(.+?)(?:\n|$)"
            ],
            "parcel_id": [
                r"Parcel[:\s#]+([A-Z0-9\-]+)",
                r"Account[:\s#]+([A-Z0-9\-]+)",
                r"Property ID[:\s#]+([A-Z0-9\-]+)"
            ],
            "assessed_value": [
                r"Market Value[:\s$]+([0-9,]+)",
                r"Appraised Value[:\s$]+([0-9,]+)",
                r"Total Value[:\s$]+([0-9,]+)"
            ],
            "land_value": [
                r"Land Value[:\s$]+([0-9,]+)",
                r"Land[:\s$]+([0-9,]+)"
            ],
            "improvement_value": [
                r"Improvement Value[:\s$]+([0-9,]+)",
                r"Building Value[:\s$]+([0-9,]+)",
                r"Improvements[:\s$]+([0-9,]+)"
            ],
            "tax_year": [
                r"Tax Year[:\s]+(20\d{2})",
                r"For Year[:\s]+(20\d{2})",
                r"(20\d{2})\s+Tax Year"
            ],
            "appeal_deadline": [
                r"Protest Deadline[:\s]+([0-9\/\-]+)",
                r"Appeal by[:\s]+([0-9\/\-]+)",
                r"Deadline[:\s]+([0-9\/\-]+)"
            ]
        },
        "common_ocr_errors": {
            "0": ["O", "o"],
            "1": ["l", "I"],
            "5": ["S", "s"],
            "8": ["B"],
            "$": ["S", "s"],
            ",": ["."]
        }
    },
    "tax_statement": {
        "patterns": {
            "tax_amount": [
                r"Total Tax[:\s$]+([0-9,\.]+)",
                r"Amount Due[:\s$]+([0-9,\.]+)",
                r"Tax Amount[:\s$]+([0-9,\.]+)"
            ],
            "due_date": [
                r"Due Date[:\s]+([0-9\/\-]+)",
                r"Payment Due[:\s]+([0-9\/\-]+)",
                r"Pay by[:\s]+([0-9\/\-]+)"
            ],
            "discount_date": [
                r"Discount Until[:\s]+([0-9\/\-]+)",
                r"3% Discount[:\s]+([0-9\/\-]+)",
                r"Early Pay[:\s]+([0-9\/\-]+)"
            ],
            "exemptions": [
                r"Homestead[:\s$]+([0-9,]+)",
                r"Exemptions[:\s$]+([0-9,]+)",
                r"Total Exemptions[:\s$]+([0-9,]+)"
            ]
        }
    },
    "protest_form": {
        "patterns": {
            "requested_value": [
                r"Requested Value[:\s$]+([0-9,]+)",
                r"Opinion of Value[:\s$]+([0-9,]+)",
                r"Proposed Value[:\s$]+([0-9,]+)"
            ],
            "protest_reason": [
                r"Reason for Protest[:\s]+(.+?)(?:\n|$)",
                r"Grounds[:\s]+(.+?)(?:\n|$)",
                r"Protest Basis[:\s]+(.+?)(?:\n|$)"
            ]
        }
    }
}

# Sample document templates with realistic data
DOCUMENT_TEMPLATES = {
    "harris_appraisal_notice": {
        "document_type": "appraisal_notice",
        "county": "Harris County",
        "template_content": """
HARRIS COUNTY APPRAISAL DISTRICT
NOTICE OF APPRAISED VALUE
Tax Year: 2024

Property Owner: {owner_name}
Property Address: {property_address}
Parcel ID: {parcel_id}

CURRENT APPRAISAL:
Land Value: ${land_value:,}
Improvement Value: ${improvement_value:,}
TOTAL MARKET VALUE: ${total_value:,}

PRIOR YEAR COMPARISON:
2023 Market Value: ${previous_value:,}
2024 Market Value: ${total_value:,}
Change: ${value_change:,} ({change_percent:+.1f}%)

IMPORTANT DEADLINES:
Protest Deadline: {protest_deadline}
(Must file protest within 30 days of receipt or by May 15, whichever is later)

If you disagree with this appraisal, you have the right to protest.
Contact HCAD at (713) 957-5800 or visit www.hcad.org

Harris County Appraisal District
13013 Northwest Freeway
Houston, TX 77040
        """,
        "variable_fields": [
            "owner_name", "property_address", "parcel_id", "land_value",
            "improvement_value", "total_value", "previous_value",
            "value_change", "change_percent", "protest_deadline"
        ]
    },
    "dallas_tax_statement": {
        "document_type": "tax_statement",
        "county": "Dallas County",
        "template_content": """
DALLAS COUNTY TAX OFFICE
2024 PROPERTY TAX STATEMENT

Account Number: {parcel_id}
Property Address: {property_address}
Owner: {owner_name}

ASSESSMENT INFORMATION:
Market Value: ${assessed_value:,}
Homestead Exemption: ${homestead_exemption:,}
Other Exemptions: ${other_exemptions:,}
Taxable Value: ${taxable_value:,}

TAX CALCULATION:
County Tax: ${county_tax:.2f}
School District: ${school_tax:.2f}
City Tax: ${city_tax:.2f}
Other: ${other_tax:.2f}
TOTAL TAX: ${total_tax:.2f}

PAYMENT INFORMATION:
Discount Date (3%): {discount_date}
Due Date (No Penalty): {due_date}
Penalty Starts: {penalty_date}

Pay online at: www.dallascounty.org/tax
Questions: (214) 653-7811
        """,
        "variable_fields": [
            "parcel_id", "property_address", "owner_name", "assessed_value",
            "homestead_exemption", "other_exemptions", "taxable_value",
            "county_tax", "school_tax", "city_tax", "other_tax", "total_tax",
            "discount_date", "due_date", "penalty_date"
        ]
    },
    "travis_protest_form": {
        "document_type": "protest_form",
        "county": "Travis County",
        "template_content": """
TRAVIS CENTRAL APPRAISAL DISTRICT
NOTICE OF PROTEST

Property Owner: {owner_name}
Property Address: {property_address}
Account Number: {parcel_id}

CURRENT APPRAISAL: ${current_value:,}
PROTESTED VALUE: ${requested_value:,}

REASON FOR PROTEST:
{protest_reason}

EVIDENCE ATTACHED:
{evidence_list}

HEARING PREFERENCE:
[ ] Informal Review
[ ] Formal ARB Hearing
[ ] Agent Representation

Contact Information:
Phone: {phone}
Email: {email}

Signature: _________________ Date: {submission_date}

Submit to: Travis CAD, 8314 Cross Park Drive, Austin, TX 78754
Deadline: {protest_deadline}
        """,
        "variable_fields": [
            "owner_name", "property_address", "parcel_id", "current_value",
            "requested_value", "protest_reason", "evidence_list",
            "phone", "email", "submission_date", "protest_deadline"
        ]
    }
}

# Mock OCR responses for testing
def generate_mock_ocr_response(document_type: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate mock OCR response with realistic errors and confidence scores"""

    patterns = OCR_EXTRACTION_PATTERNS.get(document_type, {}).get("patterns", {})
    ocr_errors = OCR_EXTRACTION_PATTERNS.get(document_type, {}).get("common_ocr_errors", {})

    extracted_data = {}
    confidence_scores = {}

    for field, field_patterns in patterns.items():
        # Simulate successful extraction with some variance
        if field in template_data:
            value = str(template_data[field])

            # Apply OCR errors randomly
            if random.random() < 0.15:  # 15% chance of OCR error
                for original, replacements in ocr_errors.items():
                    if original in value:
                        replacement = random.choice(replacements)
                        value = value.replace(original, replacement, 1)

            extracted_data[field] = value
            confidence_scores[field] = random.uniform(0.75, 0.98)
        else:
            # Field not found or extraction failed
            if random.random() < 0.20:  # 20% chance of missing field
                extracted_data[field] = None
                confidence_scores[field] = 0.0
            else:
                extracted_data[field] = "EXTRACTION_FAILED"
                confidence_scores[field] = random.uniform(0.30, 0.60)

    return {
        "extracted_data": extracted_data,
        "confidence_scores": confidence_scores,
        "overall_confidence": sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0,
        "processing_time_ms": random.randint(500, 2000),
        "pages_processed": random.randint(1, 3),
        "document_type_detected": document_type,
        "document_quality": random.choice(["excellent", "good", "fair", "poor"])
    }

def generate_sample_document_data(document_type: str, county: str) -> Dict[str, Any]:
    """Generate sample data for document templates"""

    # Base property data
    property_value = random.randint(200000, 800000)
    land_value = int(property_value * random.uniform(0.20, 0.35))
    improvement_value = property_value - land_value
    previous_value = int(property_value * random.uniform(0.85, 0.95))

    # Address generation
    street_number = random.randint(100, 9999)
    street_names = ["Oak", "Pine", "Main", "Elm", "Cedar", "Maple", "Live Oak", "Bluebonnet"]
    street_types = ["St", "Ave", "Dr", "Ln", "Rd", "Blvd", "Way", "Ct"]
    cities = {
        "harris": ["Houston", "Pasadena", "Baytown"],
        "dallas": ["Dallas", "Garland", "Irving"],
        "travis": ["Austin", "Cedar Park", "Pflugerville"]
    }

    address = f"{street_number} {random.choice(street_names)} {random.choice(street_types)}"
    city = random.choice(cities.get(county.lower(), ["Unknown City"]))
    zip_code = random.randint(70000, 79999)

    # Generate parcel ID
    parcel_id = f"{county.upper()[:3]}-R1-{random.randint(100, 999)}-{random.randint(1000, 9999)}-{random.randint(100, 999)}"

    # Tax calculations
    tax_rates = {
        "harris": 0.0255,
        "dallas": 0.0238,
        "travis": 0.0267
    }
    tax_rate = tax_rates.get(county.lower(), 0.025)

    homestead_exemption = 100000 if random.random() < 0.6 else 0
    other_exemptions = random.choice([0, 10000, 12000]) if random.random() < 0.2 else 0
    taxable_value = max(0, property_value - homestead_exemption - other_exemptions)
    total_tax = taxable_value * tax_rate

    # Dates
    current_year = datetime.now().year
    protest_deadline = f"05/15/{current_year}"
    discount_date = f"11/30/{current_year}"
    due_date = f"01/31/{current_year + 1}"
    penalty_date = f"02/01/{current_year + 1}"

    return {
        "owner_name": f"Property Owner {random.randint(1000, 9999)}",
        "property_address": f"{address}, {city}, TX {zip_code}",
        "parcel_id": parcel_id,
        "total_value": property_value,
        "assessed_value": property_value,
        "land_value": land_value,
        "improvement_value": improvement_value,
        "previous_value": previous_value,
        "value_change": property_value - previous_value,
        "change_percent": ((property_value - previous_value) / previous_value) * 100,
        "homestead_exemption": homestead_exemption,
        "other_exemptions": other_exemptions,
        "taxable_value": taxable_value,
        "county_tax": total_tax * 0.15,
        "school_tax": total_tax * 0.55,
        "city_tax": total_tax * 0.25,
        "other_tax": total_tax * 0.05,
        "total_tax": total_tax,
        "protest_deadline": protest_deadline,
        "discount_date": discount_date,
        "due_date": due_date,
        "penalty_date": penalty_date,
        "current_value": property_value,
        "requested_value": int(property_value * random.uniform(0.80, 0.95)),
        "protest_reason": random.choice([
            "Property overvalued compared to similar properties",
            "Assessment increase exceeds market trends",
            "Property condition not accurately reflected",
            "Comparable sales do not support valuation",
            "Functional obsolescence not considered"
        ]),
        "evidence_list": "Comparable sales data, property photos, repair estimates",
        "phone": f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
        "email": f"owner{random.randint(100, 999)}@email.com",
        "submission_date": datetime.now().strftime("%m/%d/%Y")
    }

# Document validation patterns
VALIDATION_PATTERNS = {
    "required_fields": {
        "appraisal_notice": ["property_address", "parcel_id", "assessed_value", "appeal_deadline"],
        "tax_statement": ["property_address", "parcel_id", "tax_amount", "due_date"],
        "protest_form": ["property_address", "parcel_id", "current_value", "requested_value"],
        "exemption_application": ["property_address", "parcel_id", "exemption_type"],
        "comparable_sales": ["subject_property", "comparable_properties", "sale_prices"],
        "hearing_notice": ["property_address", "hearing_date", "hearing_time"]
    },
    "field_formats": {
        "parcel_id": r"^[A-Z]{2,4}-[A-Z0-9]{1,3}-\d{3}-\d{4}-\d{3}$",
        "assessed_value": r"^\$?[\d,]+$",
        "tax_amount": r"^\$?[\d,]+\.?\d{0,2}$",
        "date": r"^\d{1,2}\/\d{1,2}\/\d{4}$",
        "phone": r"^\(\d{3}\)\s?\d{3}-\d{4}$",
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    },
    "value_ranges": {
        "assessed_value": (10000, 10000000),
        "tax_amount": (100, 100000),
        "requested_value": (10000, 10000000)
    }
}

def validate_extracted_data(document_type: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate extracted document data"""

    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "confidence_score": 1.0
    }

    required_fields = VALIDATION_PATTERNS["required_fields"].get(document_type, [])
    field_formats = VALIDATION_PATTERNS["field_formats"]
    value_ranges = VALIDATION_PATTERNS["value_ranges"]

    # Check required fields
    for field in required_fields:
        if field not in extracted_data or not extracted_data[field]:
            validation_result["errors"].append(f"Missing required field: {field}")
            validation_result["is_valid"] = False

    # Check field formats
    for field, value in extracted_data.items():
        if value and field in field_formats:
            pattern = field_formats[field]
            if not re.match(pattern, str(value)):
                validation_result["warnings"].append(f"Invalid format for {field}: {value}")
                validation_result["confidence_score"] *= 0.9

    # Check value ranges
    for field, value in extracted_data.items():
        if field in value_ranges and value:
            try:
                numeric_value = float(str(value).replace("$", "").replace(",", ""))
                min_val, max_val = value_ranges[field]
                if not (min_val <= numeric_value <= max_val):
                    validation_result["warnings"].append(
                        f"Value for {field} outside expected range: {value}"
                    )
                    validation_result["confidence_score"] *= 0.8
            except (ValueError, TypeError):
                validation_result["errors"].append(f"Invalid numeric value for {field}: {value}")
                validation_result["is_valid"] = False

    return validation_result

def get_document_type_from_content(content: str) -> Optional[str]:
    """Detect document type from content"""

    content_lower = content.lower()

    type_indicators = {
        "appraisal_notice": ["appraisal", "notice of appraised value", "market value", "protest deadline"],
        "tax_statement": ["tax statement", "tax bill", "amount due", "discount date"],
        "protest_form": ["protest", "notice of protest", "arb", "requested value"],
        "exemption_application": ["exemption", "homestead", "application", "qualification"],
        "comparable_sales": ["comparable", "sales", "market analysis", "valuation"],
        "hearing_notice": ["hearing", "arb hearing", "panel", "hearing date"]
    }

    scores = {}
    for doc_type, indicators in type_indicators.items():
        score = sum(1 for indicator in indicators if indicator in content_lower)
        if score > 0:
            scores[doc_type] = score

    if scores:
        return max(scores, key=scores.get)

    return None