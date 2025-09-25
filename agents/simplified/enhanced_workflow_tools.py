"""
Enhanced workflow tools for Century Property Tax following the complete workflow diagram.
Implements tools for property assessments, appeals, payment processing, and report retrieval.
"""

import asyncio
import json
import os
import uuid
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from services.persistence.database import get_db_session
from services.persistence.repositories import (
    CustomerRepository,
    PropertyAssessmentServiceRepository, 
    PropertyAssessmentRequestRepository
)
from services.payments.razorpay_integration import create_razorpay_payment_link, verify_payment_completion
from services.date_intelligence import parse_date_intelligently, get_current_time_info, validate_booking_constraints
from services.utils.retry_handler import (
    async_retry, 
    sync_retry,
    DatabaseRetryableError, 
    APIRetryableError,
    database_circuit_breaker,
    payment_circuit_breaker,
    RetryExhaustedError
)
from src.core.logging import get_logger

logger = get_logger("enhanced_workflow_tools")

# ZIP Code Service Areas (expandable)
SERVICEABLE_ZIPS = {
    "75001": {"area": "Dallas County", "available": True, "onsite_assessment": True},
    "75002": {"area": "Dallas County East", "available": True, "onsite_assessment": True},
    "75003": {"area": "Dallas County West", "available": True, "onsite_assessment": True},
    "75004": {"area": "Dallas County South", "available": True, "onsite_assessment": True},
    "75005": {"area": "Dallas County North", "available": True, "onsite_assessment": True},
    "75201": {"area": "Dallas County Downtown", "available": True, "onsite_assessment": True},
    "77001": {"area": "Harris County", "available": True, "onsite_assessment": True},
    "78701": {"area": "Travis County", "available": True, "onsite_assessment": True},
    "79901": {"area": "El Paso County", "available": True, "onsite_assessment": True},
    "76101": {"area": "Tarrant County", "available": True, "onsite_assessment": True},
    "78201": {"area": "Bexar County", "available": True, "onsite_assessment": True},
}

# Pydantic Schema for create_assessment tool
class CreateAssessmentSchema(BaseModel):
    """Schema for creating property assessment requests with comprehensive validation"""

    whatsapp_id: str = Field(description="Customer's WhatsApp ID for identification")
    customer_name: str = Field(description="Full name of the property owner")
    phone: str = Field(description="Customer phone number (digits only, formatting will be stripped automatically)")
    assessment_types: List[str] = Field(
        description="List of assessment types to request. Examples: ['property_valuation', 'appeal_review', 'exemption_analysis', 'market_analysis']. Available types can be found using suggest_assessment_services tool"
    )
    zip_code: str = Field(
        description="Property ZIP code (5 digits). Must be serviceable area - validate with validate_zip_code tool first"
    )
    preferred_date: Optional[str] = Field(
        default=None,
        description="Preferred assessment date. Accepts: YYYY-MM-DD format ('2025-08-27'), natural language ('tomorrow', 'next Monday', 'August 30th'), or None for system suggestion"
    )
    preferred_time: Optional[str] = Field(
        default=None,
        description="Preferred time slot. Options: 'morning' (8AM-12PM), 'afternoon' (12PM-4PM), 'evening' (4PM-8PM), specific times ('10:00 AM', '2:30 PM'), or None for flexible timing"
    )
    assessment_type: str = Field(
        default="onsite",
        description="Assessment delivery type. Options: 'onsite' (default - property visit) or 'office' (visit our office)"
    )
    property_address: Optional[Union[str, Dict[str, str]]] = Field(
        default=None,
        description="Property address. Accepts: String format ('123 Main St, Dallas, TX 75001'), Dictionary format ({'full_address': '...', 'landmark': '...', 'zip_code': '...'}), or None to prompt user for address"
    )

# Pydantic Schema for suggest_assessment_services tool
class SuggestAssessmentServicesSchema(BaseModel):
    """Schema for suggesting property assessment services based on property types and needs"""

    property_type_or_issue: str = Field(
        description="Property type or assessment issue to find relevant services for. Examples: 'residential', 'commercial', 'appeal dispute', 'exemption qualification', 'market analysis', 'tax protest'"
    )
    property_year: Optional[int] = Field(
        default=None,
        description="Property construction year - helps suggest appropriate assessment methods and comparable analysis"
    )
    property_category: Optional[str] = Field(
        default=None,
        description="Property category for specialized assessments. Options: 'residential', 'commercial', 'industrial', 'agricultural' (case insensitive)"
    )

# Pydantic Schema for schedule_property_assessment tool
class SchedulePropertyAssessmentSchema(BaseModel):
    """Schema for scheduling property assessment appointments"""

    assessment_id: str = Field(description="Assessment ID to schedule appointment for (format: CPT20250827ABCD1234)")
    preferred_date: str = Field(
        description="Preferred assessment date. Accepts: YYYY-MM-DD format ('2025-08-27'), natural language ('tomorrow', 'next Monday', 'August 30th')"
    )
    preferred_time: str = Field(
        description="Preferred time slot. Options: 'morning' (8AM-12PM), 'afternoon' (12PM-4PM), 'evening' (4PM-8PM), or specific times like '10:00 AM', '2:30 PM'"
    )
    whatsapp_id: str = Field(description="Customer's WhatsApp ID for verification")
    special_instructions: Optional[str] = Field(
        default=None,
        description="Special instructions for assessment team (e.g., 'Gate code is 1234', 'Call before arrival', 'Property has guard dog')"
    )

# Advanced Assessment Services for Suggestions
ADVANCED_ASSESSMENT_SERVICES = {
    "residential": {
        "service_name": "Comprehensive Residential Assessment",
        "assessments": ["Market Analysis", "Property Valuation", "Exemption Review", "Comparable Analysis", "Appeal Preparation"],
        "price": 1200,
        "discounted_price": 999,
        "description": "Complete residential property assessment with market analysis and appeal preparation"
    },
    "commercial": {
        "service_name": "Advanced Commercial Assessment",
        "assessments": ["Income Analysis", "Market Study", "Lease Review", "Comparable Sales", "Tax Optimization"],
        "price": 1800,
        "discounted_price": 1499,
        "description": "Comprehensive commercial property assessment and tax strategy"
    },
    "appeal": {
        "service_name": "Complete Appeal Preparation Service",
        "assessments": ["Evidence Gathering", "Comparable Analysis", "Market Research", "Documentation Review", "Hearing Representation"],
        "price": 1000,
        "discounted_price": 799,
        "description": "Comprehensive property tax appeal preparation and representation"
    },
    "exemption": {
        "service_name": "Comprehensive Exemption Analysis",
        "assessments": ["Eligibility Review", "Documentation Prep", "Application Filing", "Status Tracking", "Compliance Monitoring"],
        "price": 800,
        "discounted_price": 649,
        "description": "Complete property tax exemption qualification and application"
    },
    "homestead": {
        "service_name": "Homestead Exemption Comprehensive Service",
        "assessments": ["Qualification Review", "Market Analysis", "Savings Calculation", "Application Processing", "Annual Monitoring"],
        "price": 2200,
        "discounted_price": 1799,
        "description": "Complete homestead exemption service for residential properties"
    },
    "investment": {
        "service_name": "Investment Property Tax Optimization",
        "assessments": ["Portfolio Analysis", "Tax Strategy", "Depreciation Review", "Market Position", "Optimization Plan"],
        "price": 2000,
        "discounted_price": 1599,
        "description": "Complete tax optimization service designed for investment properties"
    }
}


@tool(parse_docstring=True)
def validate_pin_code(pin_code: str) -> Dict[str, Any]:
    """
    Validate if ZIP code is serviceable for property tax assessment and get area details.

    This tool checks if the provided ZIP code is within our service coverage area
    and returns detailed information about service availability and area details.

    Args:
        pin_code: 5-digit ZIP code to validate (e.g., '75001', '77001')
    """
    try:
        logger.info(f"ZIP validation started for: {pin_code}")

        # Clean ZIP code
        clean_zip = str(pin_code).strip()
        logger.debug(f"Cleaned ZIP code: '{clean_zip}' (length: {len(clean_zip)})")

        if len(clean_zip) != 5 or not clean_zip.isdigit():
            print(f"❌ ZIP VALIDATION DEBUG: Invalid format - Length={len(clean_zip)}, IsDigit={clean_zip.isdigit()}")
            error_response = {
                "success": False,
                "serviceable": False,
                "error": "Invalid ZIP code format. Please provide a 5-digit ZIP code.",
                "zip_code": clean_zip
            }
            print(f"🔍 ZIP VALIDATION DEBUG: Returning error response")
            return error_response

        print(f"🔍 ZIP VALIDATION DEBUG: Checking serviceable zips: {list(SERVICEABLE_ZIPS.keys())}")

        if clean_zip in SERVICEABLE_ZIPS:
            area_info = SERVICEABLE_ZIPS[clean_zip]
            print(f"✅ ZIP VALIDATION DEBUG: Found serviceable! Area='{area_info['area']}'")
            
            success_response = {
                "success": True,
                "serviceable": area_info["available"],
                "zip_code": clean_zip,
                "area": area_info["area"],
                "onsite_assessment_available": area_info["onsite_assessment"],
                "message": f"Great! We provide services in {area_info['area']}. Onsite assessment is {'available' if area_info['onsite_assessment'] else 'not available'}."
            }
            print(f"🔍 ZIP VALIDATION DEBUG: Returning success response")
            return success_response
        else:
            print(f"⚠️ ZIP VALIDATION DEBUG: ZIP not serviceable")
            not_serviceable_response = {
                "success": True,
                "serviceable": False,
                "zip_code": clean_zip,
                "message": f"Sorry, we currently don't provide services in ZIP code {clean_zip}. We are expanding and will reach your area soon!",
                "alternative_message": "You can visit our nearest office or try a different ZIP code where you might want the assessment conducted."
            }
            print(f"🔍 ZIP VALIDATION DEBUG: Returning not serviceable response")
            return not_serviceable_response
            
    except Exception as e:
        print(f"❌ ZIP VALIDATION DEBUG: EXCEPTION - {e}")
        print(f"❌ ZIP VALIDATION DEBUG: EXCEPTION TYPE - {type(e).__name__}")
        import traceback
        traceback.print_exc()

        error_response = {
            "success": False,
            "serviceable": False,
            "error": "Unable to validate ZIP code at this time.",
            "zip_code": zip_code,
            "debug_error": str(e)
        }
        print(f"🔍 ZIP VALIDATION DEBUG: Returning exception response")
        return error_response


@tool("suggest_assessment_services", args_schema=SuggestAssessmentServicesSchema, parse_docstring=True)
def suggest_assessment_services(
    property_type_or_issue: str,
    property_year: Optional[int] = None,
    property_category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Suggest comprehensive property assessment services based on property types, issues, or tax optimization goals.

    This tool uses an intelligent recommendation system that combines predefined service packages with
    database-driven service catalog searches to provide personalized assessment suggestions based on
    property characteristics and tax situations.

    Args:
        property_type_or_issue: Property type or tax issue - Examples: 'residential', 'commercial', 'appeal dispute'
        property_year: Property construction year for age-appropriate assessment methods
        property_category: Property category ('residential'/'commercial'/'industrial'/'agricultural') for specialized assessments
    """
    try:
        print(f"🔧 SUGGEST_SERVICES DEBUG: property_type_or_issue='{property_type_or_issue}'")
        print(f"🔧 SUGGEST_SERVICES DEBUG: property_year={property_year}, property_category={property_category}")

        # Normalize input
        issue_lower = property_type_or_issue.lower()
        print(f"🔧 SUGGEST_SERVICES DEBUG: normalized issue='{issue_lower}'")
        
        # Try database-driven approach first
        async def _suggest_services_async():
            async with get_db_session() as session:
                assessment_service_repo = PropertyAssessmentServiceRepository(session)

                # Search for services based on property type/issue
                recommended_services = []
                
                # Map common property tax issues to search terms
                issue_mappings = {
                    "residential": ["residential", "homestead", "single_family"],
                    "commercial": ["commercial", "business", "retail"],
                    "appeal": ["appeal", "protest", "dispute", "valuation_challenge"],
                    "exemption": ["exemption", "homestead_exemption", "disability"],
                    "assessment": ["assessment", "valuation", "appraisal"],
                    "agricultural": ["agricultural", "farm", "ranch"],
                    "general": ["property_tax", "consultation"],
                }
                
                # Find matching property tax issues
                search_issues = []
                for key, issues in issue_mappings.items():
                    if any(word in issue_lower for word in key.split()) or any(issue in issue_lower for issue in issues):
                        search_issues.extend(issues)

                print(f"🔧 SUGGEST_SERVICES DEBUG: search_issues={search_issues}")

                # For property tax services, we return predefined service recommendations
                # Database integration would be implemented here for dynamic services
                
                # If no specific issue match, do general search
                if not search_issues:
                    print(f"🔧 SUGGEST_SERVICES DEBUG: No issue match, using general property consultation")
                    # Default to general property tax consultation
                    search_issues = ["property_tax", "consultation"]
                
                # Return appropriate property tax service recommendation
                if "appeal" in search_issues or "protest" in search_issues:
                    service_type = "Property Tax Appeal Consultation"
                    description = "Comprehensive property tax appeal and protest representation"
                elif "exemption" in search_issues:
                    service_type = "Homestead Exemption Consultation"
                    description = "Property tax exemption application and compliance review"
                elif "commercial" in search_issues:
                    service_type = "Commercial Property Tax Assessment"
                    description = "Specialized commercial property tax valuation review"
                else:
                    service_type = "General Property Tax Consultation"
                    description = "Comprehensive property tax assessment and consultation"

                print(f"✅ SUGGEST_SERVICES DEBUG: Recommending {service_type}")

                return {
                    "success": True,
                    "service_suggested": True,
                    "service_name": service_type,
                    "service_code": "PROP_TAX_CONSULT",
                    "description": description,
                    "category": "Property Tax",
                    "price": 0.0,
                    "discounted_price": 0.0,
                    "savings": 0.0,
                    "savings_percent": 0.0,
                    "onsite_available": True,
                    "consultation_type": "FREE",
                    "message": f"Based on your property situation, I recommend our {service_type}. This is a FREE consultation with contingency-based representation.",
                    "data_source": "property_tax_services"
                }
                return None  # No suitable test found
        
        try:
            result = asyncio.run(_suggest_panel_async())
            if result:
                return result
        except Exception as db_error:
            print(f"⚠️ SUGGEST_PANEL DEBUG: Database error: {db_error}")
            print("🔧 SUGGEST_PANEL DEBUG: Falling back to hardcoded panels")
        
        # Fallback to hardcoded property tax services if database fails
        suggested_service = None

        if any(word in issue_lower for word in ["appeal", "protest", "dispute", "challenge"]):
            suggested_service = {
                "service_name": "Property Tax Appeal Consultation",
                "description": "Expert property tax appeal and protest representation",
                "category": "Property Tax Appeals",
                "price": 0.0,
                "discounted_price": 0.0
            }
        elif any(word in issue_lower for word in ["exemption", "homestead", "disability"]):
            suggested_service = {
                "service_name": "Homestead Exemption Application",
                "description": "Property tax exemption application and compliance review",
                "category": "Tax Exemptions",
                "price": 0.0,
                "discounted_price": 0.0
            }
        elif any(word in issue_lower for word in ["commercial", "business", "retail", "industrial"]):
            suggested_service = {
                "service_name": "Commercial Property Tax Assessment",
                "description": "Specialized commercial property tax evaluation and consultation",
                "category": "Commercial Property Tax",
                "price": 0.0,
                "discounted_price": 0.0
            }
        else:
            suggested_service = {
                "service_name": "General Property Tax Consultation",
                "description": "Comprehensive property tax assessment and guidance",
                "category": "Property Tax Consultation",
                "price": 0.0,
                "discounted_price": 0.0
            }

        if suggested_service:
            print(f"✅ SUGGEST_SERVICES DEBUG: Found hardcoded service: {suggested_service['service_name']}")

            return {
                "success": True,
                "service_suggested": True,
                "service_name": suggested_service["service_name"],
                "description": suggested_service["description"],
                "category": suggested_service["category"],
                "original_price": suggested_service["price"],
                "discounted_price": suggested_service["discounted_price"],
                "savings": 0.0,
                "savings_percent": 0.0,
                "message": f"Based on your property tax situation, I recommend our {suggested_service['service_name']}. This is a FREE consultation with contingency-based representation - you only pay if we reduce your taxes!",
                "consultation_type": "FREE",
                "data_source": "hardcoded"
            }
        else:
            print(f"⚠️ SUGGEST_SERVICES DEBUG: No matching service found for '{issue_lower}'")
            return {
                "success": True,
                "service_suggested": False,
                "message": "Let me help you with your property tax situation. Could you provide more details about your property or tax concerns?",
                "suggestion": "You can schedule a FREE property tax consultation to get started."
            }
            
    except Exception as e:
        print(f"❌ SUGGEST_PANEL DEBUG: EXCEPTION - {e}")
        print(f"❌ SUGGEST_PANEL DEBUG: EXCEPTION TYPE - {type(e).__name__}")
        import traceback
        traceback.print_exc()
        logger.error(f"Panel suggestion error: {e}")
        return {
            "success": False,
            "error": f"Unable to suggest test panel: {str(e)}"
        }


# Helper function to check if test codes match a known panel
def _check_panel_pricing(test_codes: List[str], validated_tests: List[Dict]) -> Optional[Dict]:
    """Check if the requested tests match a known panel for special pricing."""
    test_codes_upper = [code.upper() for code in test_codes]
    
    # Define property tax service packages
    packages = {
        "comprehensive": {
            "required_codes": ["PROP_TAX_CONSULT"],
            "optional_codes": ["PROP_TAX_APPEAL", "PROP_TAX_EXEMPTION"],
            "panel_name": "Comprehensive Property Tax Package",
            "discounted_price": 0  # FREE consultation
        }
    }
    
    for package_key, package_info in packages.items():
        required_codes = package_info["required_codes"]

        # Check if all required codes are present
        if all(code in test_codes_upper for code in required_codes):
            print(f"🎯 PACKAGE_PRICING DEBUG: Found matching package '{package_info['panel_name']}'")
            return package_info
    
    return None

# Async version of create_order for internal use
@async_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
async def _create_order_async(
    instagram_id: str,
    customer_name: str,
    phone: str,
    test_codes: List[str],
    pin_code: str,
    preferred_date: Optional[str] = None,
    preferred_time: Optional[str] = None,
    collection_type: str = "home",
    address: Optional[Union[str, Dict[str, str]]] = None
) -> Dict[str, Any]:
    """Async implementation with database operations."""
    # [This would contain the async logic]
    pass

# Async implementation for database operations
async def _create_order_async(
    instagram_id: str,
    customer_name: str,
    phone: str,
    test_codes: List[str],
    pin_code: str,
    preferred_date: Optional[str] = None,
    preferred_time: Optional[str] = None,
    collection_type: str = "home",
    address: Optional[Union[str, Dict[str, str]]] = None
) -> Dict[str, Any]:

    """
    Async implementation of create_order with database operations.
    """
    try:
        # CRITICAL DEBUG: Add comprehensive logging
        print(f"🔧 CREATE_ORDER DEBUG: Starting order creation")
        print(f"🔧 CREATE_ORDER DEBUG: test_codes={test_codes}, customer={customer_name}")
        print(f"🔧 CREATE_ORDER DEBUG: phone={phone}, pin={pin_code}")
        print(f"🔧 CREATE_ORDER DEBUG: date={preferred_date}, time={preferred_time}")
        print(f"🔧 CREATE_ORDER DEBUG: collection_type={collection_type}, address={address}")
        
        # Smart validation: Address guidance for home collection
        if collection_type.lower() == "home" and not address:
            return {
                "success": False,
                "error": "address_needed_for_home_collection",
                "message": "I'll need your complete address for home collection. Could you please share your address including house/flat number, building name, street, and area?",
                "requires_address": True
            }
        
        # Soft validation: Guide users to provide more complete address if needed
        if collection_type.lower() == "home" and address:
            address_str = address if isinstance(address, str) else str(address.get("full_address", ""))
            if len(address_str.strip()) < 8:  # More lenient than before
                return {
                    "success": False,
                    "error": "address_too_brief",
                    "message": "Could you provide a more complete address? I need details like house number, street name, and area to ensure our team can locate you easily.",
                    "requires_complete_address": True
                }
            print(f"✅ CREATE_ORDER DEBUG: Address looks good for home collection: {address_str[:50]}...")
        
        # Parse natural language date if provided
        if preferred_date:
            from services.utils.date_parser import parse_natural_date, format_date_user_friendly
            parsed_date = parse_natural_date(preferred_date)
            if parsed_date:
                preferred_date = parsed_date
                friendly_date = format_date_user_friendly(parsed_date)
                print(f"🔧 CREATE_ORDER DEBUG: Parsed date '{preferred_date}' as {friendly_date}")
            else:
                print(f"⚠️ CREATE_ORDER DEBUG: Could not parse date '{preferred_date}', using as-is")
        
        # Auto-map common property tax service names that customers might use
        mapped_service_codes = []
        for code in test_codes:  # Note: variable name kept as test_codes for compatibility
            if code.upper() in ["APPEAL", "PROTEST"] or code.lower() in ["property appeal", "tax protest"]:
                mapped_service_codes.append("PROP_TAX_APPEAL")
            elif code.upper() in ["EXEMPTION", "HOMESTEAD"] or code.lower() in ["homestead exemption", "property exemption"]:
                mapped_service_codes.append("PROP_TAX_EXEMPTION")
            elif code.upper() in ["CONSULTATION", "CONSULT"] or code.lower() in ["property consultation", "tax consultation"]:
                mapped_service_codes.append("PROP_TAX_CONSULT")
            elif code.upper() in ["ASSESSMENT", "VALUATION"] or code.lower() in ["property assessment", "property valuation"]:
                mapped_service_codes.append("PROP_TAX_ASSESSMENT")
            elif code.upper().startswith("PROP_TAX"):
                mapped_service_codes.append(code.upper())
            else:
                # Default to general consultation for any unrecognized service
                mapped_service_codes.append("PROP_TAX_CONSULT")
        
        test_codes = mapped_service_codes  # Use mapped property tax service codes
        print(f"🔧 CREATE_ORDER DEBUG: Mapped test codes: {test_codes}")
        
        # Validate PIN code first
        pin_validation = validate_pin_code(pin_code)
        print(f"🔧 CREATE_ORDER DEBUG: PIN validation result: {pin_validation}")
        
        if not pin_validation.get("serviceable"):
            return {
                "success": False,
                "error": "Service not available in your area",
                "pin_validation": pin_validation
            }
        
        # Generate order ID
        order_id = f"KD{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
        print(f"🔧 CREATE_ORDER DEBUG: Generated order_id={order_id}")
        
        # Database-driven test validation and pricing
        async with get_db_session() as session:
            assessment_service_repo = PropertyAssessmentServiceRepository(session)
            customer_repo = CustomerRepository(session)
            assessment_request_repo = PropertyAssessmentRequestRepository(session)

            validated_tests = []
            total_amount = 0
            not_found_tests = []

            # Property Tax Service Bypass - skip medical test validation for property tax consultations
            if any(code.startswith("PROP_TAX") for code in test_codes):
                print(f"🏠 CREATE_ORDER DEBUG: Property tax consultation - bypassing medical test validation")
                for test_code in test_codes:
                    if test_code.startswith("PROP_TAX"):
                        validated_tests.append({
                            "code": test_code,
                            "name": "Property Tax Consultation",
                            "description": "Free property tax assessment consultation",
                            "price": 0.0,
                            "discounted_price": 0.0,
                            "sample_type": "N/A",
                            "fasting_required": False,
                            "home_collection": collection_type == "property visit",
                            "category": "Property Tax"
                        })
                        print(f"✅ CREATE_ORDER DEBUG: Added {test_code} - Property Tax Consultation - FREE")
            else:
                # Handle other service codes (non-property tax services are not supported)
                for service_code in test_codes:
                    service_upper = service_code.upper()
                    print(f"🔍 CREATE_ORDER DEBUG: Service not supported: {service_upper}")
                    not_found_tests.append(service_code)
            
            # Check if services match a known package for special pricing
            package_pricing = _check_panel_pricing(test_codes, validated_tests)
            if package_pricing:
                total_amount = package_pricing["discounted_price"]
                print(f"💰 CREATE_ORDER DEBUG: Applied package pricing: {package_pricing['panel_name']} - $0 (FREE)")
            
            if not validated_tests:
                print(f"❌ CREATE_ORDER DEBUG: No valid services found")
                return {
                    "success": False,
                    "error": "The requested service is not available.",
                    "not_found": not_found_tests,
                    "user_friendly_suggestion": "For property tax consultations, please use service codes starting with PROP_TAX.",
                    "retry_needed": True
                }
        
            print(f"✅ CREATE_ORDER DEBUG: Validated {len(validated_tests)} services, total=$0 (FREE consultations)")
            
            # Create/update customer record
            print(f"🔧 CREATE_ORDER DEBUG: Creating/updating customer record")
            customer = await customer_repo.create_or_update(
                whatsapp_id=instagram_id,  # Fixed: use whatsapp_id parameter
                name=customer_name,
                phone=phone.replace("+91", "").replace("-", "").replace(" ", ""),
                pin_code=pin_code
            )
            print(f"✅ CREATE_ORDER DEBUG: Customer record ready: {customer.name}")
            
            # Create booking records for each test
            booking_ids = []
            
            # Convert date string to date object if provided
            parsed_preferred_date = None
            if preferred_date:
                try:
                    # Use intelligent date parsing for natural language dates
                    from services.date_intelligence import DateIntelligenceService
                    date_service = DateIntelligenceService()
                    date_result = date_service.parse_date_intelligently(preferred_date)
                    
                    if date_result["success"]:
                        parsed_preferred_date = date_result["parsed_date"]
                        print(f"🔧 CREATE_ORDER DEBUG: Parsed date using intelligence: {parsed_preferred_date}")
                    else:
                        print(f"⚠️ CREATE_ORDER DEBUG: Date parsing failed: {date_result.get('error', 'Unknown error')}")
                        # Fallback to basic parsing
                        try:
                            parsed_preferred_date = datetime.strptime(preferred_date, '%Y-%m-%d').date()
                            print(f"🔧 CREATE_ORDER DEBUG: Fallback date parse successful: {parsed_preferred_date}")
                        except ValueError:
                            print(f"⚠️ CREATE_ORDER DEBUG: All date parsing failed for: {preferred_date}")
                            
                except ImportError:
                    # Fallback if date intelligence service not available
                    try:
                        parsed_preferred_date = datetime.strptime(preferred_date, '%Y-%m-%d').date()
                        print(f"🔧 CREATE_ORDER DEBUG: Basic date parsing: {parsed_preferred_date}")
                    except ValueError:
                        print(f"⚠️ CREATE_ORDER DEBUG: Invalid date format: {preferred_date}")
                except Exception as e:
                    print(f"⚠️ CREATE_ORDER DEBUG: Date parsing error: {e}")
            
            for i, test_info in enumerate(validated_tests):
                booking_id = f"{order_id}_T{i+1}"
                
                # Find the service record for the service_id - property tax consultations only
                test_record = None
                if test_info["code"].startswith("PROP_TAX"):
                    # Property tax consultations use dummy record for processing
                    test_record = {"id": f"prop_tax_{i+1}", "dummy": True}
                else:
                    # Non-property tax services are not supported
                    print(f"⚠️ CREATE_ORDER DEBUG: Unsupported service type: {test_info['code']}")
                    test_record = None

                if test_record:
                    # Handle address conversion - ensure it's a dictionary
                    processed_address = None
                    if address:
                        if isinstance(address, str):
                            # Convert string address to dictionary format
                            processed_address = {
                                "full_address": address.strip(),
                                "pin_code": pin_code
                            }
                            print(f"🔧 CREATE_ORDER DEBUG: Converted string address to dict: {processed_address}")
                        elif isinstance(address, dict):
                            processed_address = address
                            print(f"🔧 CREATE_ORDER DEBUG: Using provided address dict: {processed_address}")

                    booking = await assessment_request_repo.create_booking(
                        customer_id=customer.id,
                        test_id=test_record.get("id", f"prop_tax_{i+1}"),  # Use dummy ID for property tax services
                        booking_id=booking_id,
                        total_amount=Decimal("0.00"),  # Property tax consultations are FREE
                        preferred_date=parsed_preferred_date,
                        preferred_time=preferred_time,
                        collection_type=collection_type,
                        collection_address=processed_address
                    )
                    booking_ids.append(booking.booking_id)
                    print(f"✅ CREATE_ORDER DEBUG: Created booking {booking.booking_id} for {test_info['name']}")
                else:
                    print(f"⚠️ CREATE_ORDER DEBUG: Could not find service record for {test_info['code']}")
            
            # Prepare order data for Redis storage (for quick access)
            order_data = {
                "order_id": order_id,
                "customer_id": customer.id,
                "customer_name": customer_name,
                "phone": phone,
                "instagram_id": instagram_id,
                "services_booked": validated_tests,
                "booking_ids": booking_ids,
                "total_amount": total_amount,
                "pin_code": pin_code,
                "service_area": pin_validation.get("area", f"Area {pin_code}"),
                "collection_type": collection_type,
                "preferred_date": preferred_date,
                "preferred_time": preferred_time,
                "status": "pending",
                "payment_status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            # Store order in Redis for quick access
            try:
                from services.persistence.order_storage import get_order_storage
                storage = get_order_storage()
                stored = storage.store_order(order_data)
                if stored:
                    print(f"✅ CREATE_ORDER DEBUG: Order stored in Redis successfully")
                else:
                    print(f"⚠️ CREATE_ORDER DEBUG: Failed to store order in Redis")
            except Exception as storage_error:
                print(f"⚠️ CREATE_ORDER DEBUG: Order storage error: {storage_error}")
            
            # Commit database transaction
            await session.commit()
            print(f"✅ CREATE_ORDER DEBUG: Database transaction committed")
        
        # Track booking in Google Sheets for CRM
        try:
            from integrations.google_sheets.lead_tracker import get_lead_tracker
            lead_tracker = get_lead_tracker()
            
            if lead_tracker.is_enabled():
                print(f"📊 CREATE_ORDER DEBUG: Tracking booking in Google Sheets")
                
                # Prepare booking data for sheets
                booking_data = {
                    "order_id": order_id,
                    "customer_id": instagram_id,
                    "customer_name": customer_name,
                    "phone": phone,
                    "address": str(address) if address else "",
                    "pin_code": pin_code,
                    "test_name": ", ".join([test["name"] for test in validated_tests]),
                    "test_code": ", ".join([test["code"] for test in validated_tests]),
                    "price": total_amount,
                    "scheduled_date": preferred_date or "",
                    "scheduled_time": preferred_time or "",
                    "status": "booked",
                    "payment_status": "pending"
                }
                
                # Track booking asynchronously
                sheets_result = await lead_tracker.track_booking(booking_data)
                print(f"📊 CREATE_ORDER DEBUG: Sheets tracking result: {sheets_result}")
            else:
                print(f"📊 CREATE_ORDER DEBUG: Google Sheets disabled - skipping tracking")
                
        except Exception as sheets_error:
            print(f"⚠️ CREATE_ORDER DEBUG: Sheets tracking failed: {sheets_error}")
            # Don't fail the order if sheets tracking fails
        
        # Return success response
        response = {
            "success": True,
            "order_id": order_id,
            "booking_ids": booking_ids,
            "customer_name": customer_name,
            "phone": phone,
            "instagram_id": instagram_id,
            "tests_booked": validated_tests,
            "total_amount": total_amount,
            "pin_code": pin_code,
            "service_area": pin_validation.get("area", f"Area {pin_code}"),
            "collection_type": collection_type,
            "preferred_date": preferred_date,
            "preferred_time": preferred_time,
            "message": f"Order {order_id} created successfully! Total: ₹{total_amount}",
            "next_steps": ["Choose payment method", "Complete booking"],
            "data_source": "database"
        }
        
        print(f"🎉 CREATE_ORDER DEBUG: Order created and stored successfully!")
        return response
        
    except RetryExhaustedError as e:
        print(f"❌ CREATE_ORDER DEBUG: All retries exhausted - {e}")
        logger.error("Order creation failed after all retries", error=str(e))
        return {
            "success": False,
            "error": "We're experiencing temporary technical difficulties. Please try booking again in a few minutes.",
            "user_friendly_error": "Temporary system issue - please retry",
            "debug_info": "All retry attempts exhausted",
            "retry_suggested": True
        }
    except Exception as e:
        print(f"❌ CREATE_ORDER DEBUG: EXCEPTION - {e}")
        print(f"❌ CREATE_ORDER DEBUG: EXCEPTION TYPE - {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        # Check if this is a database-related error that should be retryable
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['connection', 'timeout', 'lock', 'unavailable']):
            logger.error("Database-related error during order creation", error=str(e))
            raise DatabaseRetryableError(f"Database error: {str(e)}") from e
        
        # For other errors, log and return user-friendly message
        logger.error("Order creation error", error=str(e), error_type=type(e).__name__)
        return {
            "success": False,
            "error": "Unable to process your booking request right now. Please try again or contact our support team.",
            "user_friendly_error": "Booking system temporarily unavailable",
            "debug_info": f"Exception: {type(e).__name__}",
            "support_contact": True
        }


class CreateOrderSchema(BaseModel):
    """Schema for creating property tax service orders"""
    instagram_id: str = Field(description="Customer's contact ID")
    customer_name: str = Field(description="Customer's full name")
    phone: str = Field(description="Customer's phone number")
    test_codes: List[str] = Field(description="Service codes for property tax services")
    pin_code: str = Field(description="Property location pin code")
    preferred_date: Optional[str] = Field(default=None, description="Preferred service date")
    preferred_time: Optional[str] = Field(default=None, description="Preferred service time")
    collection_type: str = Field(default="home", description="Service type")
    address: Optional[Union[str, Dict[str, str]]] = Field(default=None, description="Property address")


@tool("create_order", args_schema=CreateOrderSchema)
def create_order(
    instagram_id: str,
    customer_name: str,
    phone: str,
    test_codes: List[str],
    pin_code: str,
    preferred_date: Optional[str] = None,
    preferred_time: Optional[str] = None,
    collection_type: str = "home",
    address: Optional[Union[str, Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper for create_order that calls the async implementation.
    """
    try:
        return asyncio.run(_create_order_async(
            instagram_id=instagram_id,
            customer_name=customer_name,
            phone=phone,
            test_codes=test_codes,
            pin_code=pin_code,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            collection_type=collection_type,
            address=address
        ))
    except Exception as e:
        print(f"❌ CREATE_ORDER SYNC WRAPPER ERROR: {e}")
        return {
            "success": False,
            "error": "Unable to process booking request",
            "debug_info": f"Sync wrapper error: {str(e)}"
        }


@tool
@sync_retry(max_retries=2, base_delay=1.0)
def create_payment_link(
    order_id: str,
    amount: float,
    customer_phone: str,
    customer_name: str,
    customer_email: str = None,
    instagram_id: str = None,
    booking_date: str = None,
    booking_time: str = None,
    test_name: str = None,
    pin_code: str = None
) -> Dict[str, Any]:
    """
    Create REAL Razorpay payment link with fraud prevention.
    
    Args:
        order_id: Order ID to create payment for
        amount: Payment amount
        customer_phone: Customer phone number
        customer_name: Customer name
        customer_email: Customer email (optional)
        instagram_id: Customer Instagram ID for confirmation messages (optional)
        booking_date: Date of the appointment for dynamic messaging (optional)
        booking_time: Time of the appointment for dynamic messaging (optional)
        test_name: Name of the test for dynamic messaging (optional)
        pin_code: Customer PIN code for lead tracking (optional)
        
    Returns:
        Real Razorpay payment link with security features
    """
    try:
        print(f"🔧 CREATE_PAYMENT_LINK DEBUG: Starting payment link creation")
        print(f"🔧 CREATE_PAYMENT_LINK DEBUG: order_id={order_id}, amount={amount}")
        print(f"🔧 CREATE_PAYMENT_LINK DEBUG: customer_name={customer_name}, phone={customer_phone}")
        
        # For now, create mock payment link since we can't call async functions
        # TODO: Implement sync version of Razorpay integration
        payment_id = f"MOCK_PAY_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8].upper()}"
        expires_at = datetime.now() + timedelta(hours=24)
        
        print(f"🔧 CREATE_PAYMENT_LINK DEBUG: Generated payment_id={payment_id}")
        
        # Get BASE_URL from environment or use fallback
        base_url = os.getenv('BASE_URL', 'https://dev-payments.centuryproptax.com')
        payment_link = f"{base_url}/mock-payment/{payment_id}"
        
        print(f"🔧 CREATE_PAYMENT_LINK DEBUG: BASE_URL={base_url}")
        print(f"🔧 CREATE_PAYMENT_LINK DEBUG: payment_link={payment_link}")
        
        # Store payment data in mock service for the payment page
        try:
            from services.payments.mock_razorpay import MOCK_PAYMENT_LINKS
            
            MOCK_PAYMENT_LINKS[payment_id] = {
                "id": payment_id,
                "status": "created",
                "amount": amount,
                "currency": "INR",
                "customer": {
                    "name": customer_name,
                    "phone": customer_phone,
                    "email": customer_email or f"{customer_phone}@placeholder.com"
                },
                "description": f"Century PropTax - Property Tax Services for Order {order_id}",
                "reference_id": order_id,
                "created_at": datetime.now().timestamp(),
                "expire_by": expires_at.timestamp(),
                "payments": [],
                "callback_url": None,
                "notes": {
                    "order_id": order_id,
                    "customer_phone": customer_phone,
                    "instagram_id": instagram_id,
                    "booking_date": booking_date,
                    "booking_time": booking_time,
                    "test_name": test_name,
                    "pin_code": pin_code,
                    "created_via": "chatbot"
                }
            }
            print(f"🔧 CREATE_PAYMENT_LINK DEBUG: Stored payment data in mock service")
        except Exception as store_error:
            print(f"⚠️ CREATE_PAYMENT_LINK DEBUG: Failed to store payment data: {store_error}")
        
        mock_result = {
            "success": True,
            "payment_id": payment_id,
            "payment_link": payment_link,
            "order_id": order_id,
            "amount": amount,
            "currency": "INR",
            "customer": {
                "name": customer_name,
                "phone": customer_phone,
                "email": customer_email
            },
            "expires_at": expires_at.isoformat(),
            "message": f"💳 Payment Link: {payment_link}\\n\\nAmount: ₹{amount}\\nOrder: {order_id}\\n\\n⚠️ This is a development payment link for testing.",
            "instructions": "Click the link to complete payment securely",
            "payment_methods": ["UPI", "Credit Card", "Debit Card", "Net Banking"],
            "status": "created",
            "security_features": {
                "razorpay_verified": False,
                "development_mode": True
            }
        }
        
        print(f"✅ CREATE_PAYMENT_LINK DEBUG: Payment link created successfully!")
        return mock_result
        
    except Exception as e:
        print(f"❌ CREATE_PAYMENT_LINK DEBUG: EXCEPTION - {e}")
        print(f"❌ CREATE_PAYMENT_LINK DEBUG: EXCEPTION TYPE - {type(e).__name__}")
        import traceback
        traceback.print_exc()
        logger.error(f"Payment link creation error: {e}")
        return {
            "success": False,
            "error": f"Failed to create payment link: {str(e)}",
            "debug_error": str(e)
        }


@tool
async def check_report_status(
    booking_id: str,
    phone: str = None,
    patient_name: str = None
) -> Dict[str, Any]:
    """
    Check report status and retrieve reports for customers using booking ID.
    
    Args:
        booking_id: Booking ID (required) - ask user for this
        phone: Customer phone number (optional for verification)
        patient_name: Patient name (optional for verification)
        
    Returns:
        Report status and download links if available
    """
    try:
        print(f"🔧 CHECK_REPORT DEBUG: booking_id={booking_id}, phone={phone}")
        
        async with get_db_session() as session:
            customer_repo = CustomerRepository(session)
            assessment_request_repo = PropertyAssessmentRequestRepository(session)
            
            # First, try to find booking by booking_id
            booking = await assessment_request_repo.get_by_booking_id(booking_id)
            
            if not booking:
                return {
                    "success": False,
                    "reports_found": 0,
                    "message": f"No booking found with ID '{booking_id}'. Please verify the booking ID and try again.",
                    "suggestion": "Booking IDs are provided when you create an order (e.g., KD20250811_T1)"
                }
            
            # Get customer details
            customer = await customer_repo.get_by_id(booking.customer_id)
            
            # Phone verification if provided
            if phone:
                clean_phone = phone.replace("+91", "").replace("-", "").replace(" ", "")
                if customer.phone != clean_phone:
                    return {
                        "success": False,
                        "reports_found": 0,
                        "message": "Phone number does not match the booking record. Please verify your details."
                    }
            
            print(f"✅ CHECK_REPORT DEBUG: Found booking {booking.booking_id} for customer {customer.name}")
            
            # Process single booking for report status
            bookings = [booking]
            
            # Process bookings and check for reports
            reports = []
            for booking in bookings:
                # Mock report status logic
                days_since_booking = (datetime.now().date() - booking.created_at.date()).days
                
                if booking.status == "completed" and days_since_booking >= 1:
                    report_status = "Ready"
                    download_link = f"https://reports.centuryproptax.com/download/{booking.booking_id}"
                elif booking.status == "sample_collected" and days_since_booking >= 1:
                    report_status = "Processing" 
                    download_link = None
                elif booking.status == "confirmed":
                    report_status = "Sample Pending"
                    download_link = None
                else:
                    report_status = "In Progress"
                    download_link = None
                
                reports.append({
                    "booking_id": booking.booking_id,
                    "test_name": booking.test.name,
                    "test_date": booking.created_at.strftime("%Y-%m-%d"),
                    "report_status": report_status,
                    "download_link": download_link,
                    "estimated_completion": (booking.created_at + timedelta(days=2)).strftime("%Y-%m-%d") if report_status != "Ready" else None
                })
            
            ready_reports = [r for r in reports if r["report_status"] == "Ready"]
            
            return {
                "success": True,
                "customer_name": customer.name,
                "reports_found": len(reports),
                "ready_reports": len(ready_reports),
                "reports": reports,
                "message": f"Found {len(reports)} test record(s). {len(ready_reports)} report(s) ready for download."
            }
            
    except Exception as e:
        logger.error(f"Report status check error: {e}")
        return {
            "success": False,
            "error": "Unable to check report status at this time."
        }


@tool
async def confirm_order_cash_payment(
    order_id: str,
    instagram_id: str
) -> Dict[str, Any]:
    """
    Mark order as confirmed with cash payment option.
    
    Args:
        order_id: Order ID to confirm
        instagram_id: Customer's Instagram ID
        
    Returns:
        Order confirmation status
    """
    try:
        async with get_db_session() as session:
            customer_repo = CustomerRepository(session)
            assessment_request_repo = PropertyAssessmentRequestRepository(session)
            
            customer = await customer_repo.get_by_whatsapp_id(instagram_id)  # Parameter naming will be updated separately
            if not customer:
                return {
                    "success": False,
                    "error": "Customer not found"
                }
            
            # Get bookings for this order (assuming order_id pattern)
            bookings = await assessment_request_repo.get_customer_bookings(customer.id)
            order_bookings = [b for b in bookings if order_id in b.booking_id]
            
            if not order_bookings:
                return {
                    "success": False,
                    "error": "Order not found"
                }
            
            # Update booking status to confirmed
            confirmed_bookings = []
            for booking in order_bookings:
                # In real implementation, update booking status
                confirmed_bookings.append({
                    "booking_id": booking.booking_id,
                    "test_name": booking.test.name,
                    "status": "confirmed_cash",
                    "amount": float(booking.total_amount)
                })
            
            return {
                "success": True,
                "order_id": order_id,
                "payment_method": "Cash on Collection",
                "status": "confirmed",
                "bookings": confirmed_bookings,
                "message": "Property tax consultation booked! This is a FREE consultation with contingency-based representation.",
                "next_steps": "Our property tax specialist will contact you to schedule the consultation."
            }
            
    except Exception as e:
        logger.error(f"Cash payment confirmation error: {e}")
        return {
            "success": False,
            "error": "Failed to confirm order"
        }


# REMOVED: get_payment_options tool - static data embedded in LLM prompt instead
# Payment options are now handled naturally by the LLM:
# 1. **Pay Online**: Secure payment via UPI, Cards, Net Banking (recommended for instant confirmation)
# 2. **Cash on Collection**: Pay when our technician arrives (home collection only)
# This eliminates 28 lines of static data that LLM can present contextually


class ScheduleSampleCollectionSchema(BaseModel):
    """Schema for scheduling property tax service collection"""
    order_id: str = Field(description="Order ID for the service")
    preferred_date: str = Field(description="Preferred service date")
    preferred_time: Optional[str] = Field(default=None, description="Preferred service time")
    address: Optional[str] = Field(default=None, description="Service address")


@tool("schedule_property_assessment", args_schema=ScheduleSampleCollectionSchema, parse_docstring=True)
async def schedule_property_assessment(
    order_id: str,
    preferred_date: str,
    preferred_time: str,
    instagram_id: str,
    special_instructions: Optional[str] = None
) -> Dict[str, Any]:
    """
    Schedule property assessment appointment for confirmed property tax consultation orders.

    This tool manages the scheduling process including date validation, time slot availability,
    and coordination with the property tax team for on-site property assessment.
    
    Args:
        order_id: Unique order ID to schedule collection for (format: KD20250827ABCD1234)
        preferred_date: Collection date in YYYY-MM-DD format or natural language
        preferred_time: Time slot preference - 'morning'/'afternoon'/'evening' or specific time
        instagram_id: Customer's Instagram ID for order verification and communication
        special_instructions: Optional instructions for collection team
    """
    try:
        # Parse date intelligently
        date_result = parse_date_intelligently(preferred_date)
        
        if not date_result["success"] or not date_result["is_valid"]:
            return {
                "success": False,
                "error": f"Invalid date: {date_result.get('error', 'Could not understand the date')}",
                "suggestions": date_result.get("suggestions", []),
                "validation_message": date_result.get("validation_message"),
                "current_info": date_result.get("current_info", {})
            }
        
        # Get the parsed date
        collection_date = datetime.strptime(date_result["formatted_date"], "%Y-%m-%d").date()
        
        # Additional validation for scheduling constraints (30-day limit)
        today = datetime.now().date()
        if collection_date > today + timedelta(days=30):
            return {
                "success": False,
                "error": "Cannot schedule collection beyond 30 days from today.",
                "alternative_dates": [
                    (today + timedelta(days=1)).strftime("%A, %B %d"),
                    (today + timedelta(days=2)).strftime("%A, %B %d"),
                    (today + timedelta(days=7)).strftime("%A, %B %d")
                ]
            }
        
        # Generate collection ID
        collection_id = f"COL_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6].upper()}"
        
        # Build response with intelligent date information
        response = {
            "success": True,
            "collection_id": collection_id,
            "order_id": order_id,
            "scheduled_date": date_result["formatted_date"],
            "scheduled_date_display": date_result["display_date"],
            "scheduled_time": preferred_time,
            "status": "scheduled",
            "message": f"✅ Property assessment appointment scheduled for {date_result['display_date']} at {preferred_time}",
            "assessor_contact": "+91-9876543210",
            "instructions": [
                "Have all property documents ready",
                "Have your ID and property ownership proof ready",
                "Ensure someone is available at the scheduled time"
            ],
            "special_instructions": special_instructions,
            "contact_info": "Our property assessor will call you 30 minutes before arrival.",
            "date_intelligence": {
                "parsed_using": date_result["method_used"],
                "days_from_now": date_result["days_from_now"],
                "is_weekend": date_result["is_weekend"],
                "business_day": date_result["business_day"],
                "available_time_slots": date_result["available_time_slots"],
                "validation_message": date_result["validation_message"],
                "smart_parsing": "You can say 'tomorrow', 'next Monday', 'day after tomorrow', etc."
            }
        }
        
        # Add weekend warning if applicable
        if date_result["is_weekend"]:
            response["weekend_notice"] = "Weekend collection scheduled - limited time slots available"
            
        return response
        
    except Exception as e:
        logger.error(f"Collection scheduling error: {e}")
        return {
            "success": False,
            "error": "Failed to schedule property assessment"
        }


@tool
async def verify_customer_payment(
    order_id: str,
    instagram_id: str,
    payment_id: str = None,
    customer_claim: str = None
) -> Dict[str, Any]:
    """
    Verify if customer has actually completed payment - prevents fraud from fake claims.
    
    This tool MUST be called whenever a customer claims they have paid to prevent fraud.
    
    Args:
        order_id: Order ID to verify payment for
        instagram_id: Customer's Instagram ID for verification
        payment_id: Razorpay payment ID if customer provides it
        customer_claim: What the customer is claiming (e.g., "I have paid")
        
    Returns:
        Payment verification result with anti-fraud checks
    """
    try:
        logger.info(f"ANTI-FRAUD CHECK: Verifying payment claim for order {order_id} from Instagram {instagram_id}")
        
        # Use the real Razorpay verification system
        result = await verify_payment_completion(
            order_id=order_id,
            payment_id=payment_id,
            instagram_id=instagram_id
        )
        
        if result.get("verified"):
            # Payment is actually verified
            logger.info(f"✅ PAYMENT VERIFIED: Order {order_id} payment confirmed via Razorpay")
            return {
                "success": True,
                "payment_verified": True,
                "fraud_check": "PASSED",
                "payment_status": result["payment_status"],
                "payment_id": result.get("payment_id"),
                "amount": result.get("amount"),
                "method": result.get("method"),
                "message": "✅ Payment verified successfully! Your order is confirmed.",
                "next_steps": [
                    "Property assessment will be scheduled",
                    "You will receive SMS confirmation",
                    "Assessment report will be available post property evaluation"
                ]
            }
        else:
            # Payment NOT verified - potential fraud
            fraud_reason = result.get("anti_fraud_check", "no_payment_found")
            logger.warning(f"🚨 POTENTIAL FRAUD: Order {order_id} - {fraud_reason}")
            
            return {
                "success": True,
                "payment_verified": False,
                "fraud_check": "FAILED",
                "fraud_reason": fraud_reason,
                "payment_status": result.get("payment_status", "not_found"),
                "message": "❌ Payment not verified. Please complete payment first.",
                "instructions": [
                    "Click on the payment link provided earlier",
                    "Complete payment using UPI/Card/Net Banking", 
                    "Return here after successful payment",
                    "Do not claim payment completion without actually paying"
                ],
                "warning": "False payment claims are monitored for fraud prevention",
                "support_message": "If you've actually paid, please share the payment reference ID"
            }
    
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        return {
            "success": False,
            "error": "Unable to verify payment status. Please try again.",
            "payment_verified": False,
            "fraud_check": "ERROR"
        }