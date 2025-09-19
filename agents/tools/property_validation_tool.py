"""
Property Validation Tool for Texas Property Tax System

Validates property addresses and parcel IDs, returns comprehensive
property details including assessment history and characteristics.
"""

import asyncio
import re
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from datetime import datetime

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from mock_data.property_records import (
    find_property_by_address,
    find_property_by_parcel_id,
    search_properties_by_criteria,
    TEXAS_COUNTIES,
    PROPERTY_TYPES
)

logger = structlog.get_logger()

class PropertyValidationInput(BaseModel):
    """Input schema for property validation"""
    search_query: str = Field(description="Property address, parcel ID, or search criteria")
    search_type: Optional[str] = Field(
        default="auto",
        description="Type of search: 'address', 'parcel_id', 'criteria', or 'auto' for automatic detection"
    )
    county: Optional[str] = Field(default=None, description="County name for filtering results")
    property_type: Optional[str] = Field(default=None, description="Property type filter")

class PropertyValidationResponse(BaseModel):
    """Response schema for property validation"""
    success: bool = Field(description="Whether validation was successful")
    property_found: bool = Field(description="Whether property was located")
    property_data: Optional[Dict[str, Any]] = Field(description="Complete property information")
    validation_details: Dict[str, Any] = Field(description="Validation process details")
    suggestions: List[str] = Field(description="Suggestions for failed searches")

def detect_search_type(query: str) -> str:
    """Automatically detect the type of search query"""
    query = query.strip().upper()

    # Parcel ID patterns (County-Type-District-Block-Lot)
    parcel_patterns = [
        r'^[A-Z]{3,}-[A-Z0-9]{1,3}-\d{3}-\d{4}-\d{3}$',  # Standard format
        r'^[A-Z]{3,}\d{10,}$',  # Condensed format
        r'^\d{4}-\d{4}-\d{4}$',  # Alternative format
    ]

    for pattern in parcel_patterns:
        if re.match(pattern, query):
            return "parcel_id"

    # Address patterns
    if re.search(r'\d+.*\b(ST|STREET|AVE|AVENUE|DR|DRIVE|LN|LANE|RD|ROAD|BLVD|BOULEVARD)\b', query):
        return "address"

    # If it contains numbers but doesn't match parcel format, likely address
    if re.search(r'\d+', query):
        return "address"

    # Otherwise, treat as criteria search
    return "criteria"

def normalize_address(address: str) -> str:
    """Normalize address for better matching"""
    address = address.lower().strip()

    # Common abbreviations
    replacements = {
        ' street': ' st',
        ' avenue': ' ave',
        ' drive': ' dr',
        ' lane': ' ln',
        ' road': ' rd',
        ' boulevard': ' blvd',
        ' court': ' ct',
        ' place': ' pl',
        ' trail': ' trl',
        'north ': 'n ',
        'south ': 's ',
        'east ': 'e ',
        'west ': 'w ',
    }

    for full, abbrev in replacements.items():
        address = address.replace(full, abbrev)

    return address

def format_property_response(property_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format property data for consistent response"""
    if not property_data:
        return {}

    # Format address for display
    addr = property_data["address"]
    formatted_address = f"{addr['street_number']} {addr['street_name']}"
    if "suite" in addr:
        formatted_address += f", {addr['suite']}"
    formatted_address += f", {addr['city']}, {addr['state']} {addr['zip_code']}"

    # Calculate current tax burden
    current_value = property_data["assessed_value"]
    county_info = TEXAS_COUNTIES.get(property_data["county_code"], {})
    tax_rate = county_info.get("tax_rate", 0.025)

    # Apply exemptions
    exemptions = property_data.get("exemptions", {})
    exemption_value = 0

    if exemptions.get("homestead"):
        exemption_value += county_info.get("homestead_exemption", 100000)
    if exemptions.get("senior"):
        exemption_value += county_info.get("senior_exemption", 10000)
    if exemptions.get("disability"):
        exemption_value += county_info.get("disability_exemption", 12000)

    taxable_value = max(0, current_value - exemption_value)
    annual_tax = int(taxable_value * tax_rate)

    return {
        "parcel_id": property_data["parcel_id"],
        "formatted_address": formatted_address,
        "property_type": property_data["property_type"],
        "county": property_data["county"],
        "current_assessed_value": current_value,
        "taxable_value": taxable_value,
        "annual_tax_estimated": annual_tax,
        "exemptions_applied": exemptions,
        "owner_occupied": property_data["owner"]["owner_occupied"],
        "characteristics": property_data["characteristics"],
        "assessment_history": property_data["assessment_history"][-3:],  # Last 3 years
        "last_updated": property_data["last_updated"],
        "status": property_data["status"]
    }

@tool("property_validation_tool", return_direct=False)
async def property_validation_tool(
    search_query: str,
    search_type: str = "auto",
    county: Optional[str] = None,
    property_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate property addresses and parcel IDs for Texas properties.

    Supports multiple search methods:
    - Address lookup: "123 Main St, Houston, TX"
    - Parcel ID lookup: "HAR-R1-123-4567-890"
    - Criteria search: "commercial property in Dallas"

    Args:
        search_query: Property address, parcel ID, or search criteria
        search_type: Type of search ('address', 'parcel_id', 'criteria', 'auto')
        county: Optional county filter
        property_type: Optional property type filter

    Returns:
        Comprehensive property validation results with details and suggestions
    """
    try:
        logger.info("🏠 Processing property validation request",
                   query=search_query, search_type=search_type)

        # Auto-detect search type if needed
        if search_type == "auto":
            search_type = detect_search_type(search_query)

        property_data = None
        validation_details = {
            "search_type_detected": search_type,
            "original_query": search_query,
            "normalization_applied": False
        }

        # Execute search based on type
        if search_type == "parcel_id":
            # Clean up parcel ID
            clean_parcel = search_query.strip().upper()
            property_data = find_property_by_parcel_id(clean_parcel)
            validation_details["cleaned_parcel_id"] = clean_parcel

        elif search_type == "address":
            # Normalize and search address
            normalized_address = normalize_address(search_query)
            validation_details["normalized_address"] = normalized_address
            validation_details["normalization_applied"] = normalized_address != search_query.lower()

            property_data = find_property_by_address(normalized_address)

            # If not found, try original address
            if not property_data and validation_details["normalization_applied"]:
                property_data = find_property_by_address(search_query)

        elif search_type == "criteria":
            # Parse criteria search
            results = search_properties_by_criteria(
                county=county,
                property_type=property_type
            )

            # Filter by search query keywords
            query_words = search_query.lower().split()
            if results and query_words:
                filtered_results = []
                for prop in results:
                    # Check if query words match property details
                    searchable_text = f"{prop['address']['city']} {prop['property_type']} {prop['county']}".lower()
                    if any(word in searchable_text for word in query_words):
                        filtered_results.append(prop)

                if filtered_results:
                    property_data = filtered_results[0]  # Return first match
                    validation_details["total_matches"] = len(filtered_results)

        # Generate response
        if property_data:
            formatted_data = format_property_response(property_data)

            return {
                "success": True,
                "property_found": True,
                "property_data": formatted_data,
                "validation_details": validation_details,
                "suggestions": []
            }

        else:
            # Generate helpful suggestions
            suggestions = []

            if search_type == "address":
                suggestions.extend([
                    "Try using a more complete address (include street number, name, city)",
                    "Check spelling of street name and city",
                    "Use common abbreviations (St, Ave, Dr, Ln, Rd, Blvd)",
                    "Include Texas (TX) in the address"
                ])

            elif search_type == "parcel_id":
                suggestions.extend([
                    "Verify the parcel ID format (should be like HAR-R1-123-4567-890)",
                    "Check if all numbers and letters are correct",
                    "Try searching by address instead"
                ])

            else:  # criteria
                suggestions.extend([
                    "Try being more specific with location (include city or county)",
                    "Use standard property types: residential, commercial, industrial, agricultural",
                    f"Available counties: {', '.join(TEXAS_COUNTIES.keys())}",
                    "Try searching by specific address or parcel ID"
                ])

            return {
                "success": True,
                "property_found": False,
                "property_data": None,
                "validation_details": validation_details,
                "suggestions": suggestions
            }

    except Exception as e:
        logger.error("❌ Property validation failed",
                    error=str(e), query=search_query)

        return {
            "success": False,
            "property_found": False,
            "property_data": None,
            "validation_details": {"error": str(e)},
            "suggestions": [
                "Please try again with a valid Texas property address or parcel ID",
                "Ensure the property is located in a supported Texas county",
                "Contact support if the problem persists"
            ]
        }

# Additional utility functions for the tool

async def validate_multiple_properties(
    property_identifiers: List[str]
) -> List[Dict[str, Any]]:
    """Validate multiple properties in batch"""
    results = []

    for identifier in property_identifiers:
        result = await property_validation_tool(identifier)
        results.append(result)

    return results

def get_supported_counties() -> List[Dict[str, Any]]:
    """Get list of supported Texas counties with details"""
    return [
        {
            "county_code": code,
            "county_name": info["name"],
            "tax_rate": info["tax_rate"],
            "homestead_exemption": info["homestead_exemption"],
            "cities": info["cities"]
        }
        for code, info in TEXAS_COUNTIES.items()
    ]

def get_property_type_info() -> List[Dict[str, Any]]:
    """Get property type information"""
    return [
        {
            "property_type": prop_type,
            "codes": info["codes"],
            "description": info["description"],
            "typical_value_range": info["typical_value_range"]
        }
        for prop_type, info in PROPERTY_TYPES.items()
    ]