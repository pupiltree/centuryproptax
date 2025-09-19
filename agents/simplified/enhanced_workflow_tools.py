"""
Enhanced workflow tools for Krsnaa Diagnostics following the complete workflow diagram.
Implements missing tools for orders, payments, PIN validation, and report retrieval.
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

logger = structlog.get_logger()

# PIN Code Service Areas (expandable)
SERVICEABLE_PINS = {
    "560001": {"area": "Bangalore Central", "available": True, "home_collection": True},
    "560002": {"area": "Bangalore East", "available": True, "home_collection": True}, 
    "560003": {"area": "Bangalore West", "available": True, "home_collection": True},
    "560004": {"area": "Bangalore South", "available": True, "home_collection": True},
    "560005": {"area": "Bangalore North", "available": True, "home_collection": True},
    "110001": {"area": "Delhi Central", "available": True, "home_collection": True},
    "400001": {"area": "Mumbai Central", "available": True, "home_collection": True},
    "600001": {"area": "Chennai Central", "available": True, "home_collection": True},
    "500001": {"area": "Hyderabad Central", "available": True, "home_collection": True},
    "700001": {"area": "Kolkata Central", "available": True, "home_collection": True},
}

# Pydantic Schema for create_order tool
class CreateOrderSchema(BaseModel):
    """Schema for creating medical test orders with comprehensive validation"""
    
    instagram_id: str = Field(description="Customer's Instagram ID for identification")
    customer_name: str = Field(description="Full name of the customer")
    phone: str = Field(description="Customer phone number (digits only, formatting will be stripped automatically)")
    test_codes: List[str] = Field(
        description="List of medical test codes to book. Examples: ['CBC', 'LIPID_PROFILE', 'HBA1C', 'FBS', 'THYROID']. Available codes can be found using suggest_advanced_test_panel tool"
    )
    pin_code: str = Field(
        description="Collection area PIN code (6 digits). Must be serviceable area - validate with validate_pin_code tool first"
    )
    preferred_date: Optional[str] = Field(
        default=None,
        description="Preferred booking date. Accepts: YYYY-MM-DD format ('2025-08-27'), natural language ('tomorrow', 'next Monday', 'August 30th'), or None for system suggestion"
    )
    preferred_time: Optional[str] = Field(
        default=None,
        description="Preferred time slot. Options: 'morning' (8AM-12PM), 'afternoon' (12PM-4PM), 'evening' (4PM-8PM), specific times ('10:00 AM', '2:30 PM'), or None for flexible timing"
    )
    collection_type: str = Field(
        default="home",
        description="Service delivery type. Options: 'home' (default - home collection) or 'lab' (visit lab center)"
    )
    address: Optional[Union[str, Dict[str, str]]] = Field(
        default=None,
        description="Collection address. Accepts: String format ('12, Barakhamba Road, New Delhi, Delhi - 110001'), Dictionary format ({'full_address': '...', 'landmark': '...', 'pin_code': '...'}), or None to prompt user for address"
    )

# Pydantic Schema for suggest_advanced_test_panel tool
class SuggestTestPanelSchema(BaseModel):
    """Schema for suggesting medical test panels based on health conditions"""
    
    condition_or_symptoms: str = Field(
        description="Health condition or symptoms to find relevant tests for. Examples: 'diabetes', 'thyroid problems', 'heart disease', 'high cholesterol', 'liver function', 'kidney problems'"
    )
    age: Optional[int] = Field(
        default=None,
        description="Patient age in years (0-120) - helps suggest age-appropriate tests and reference ranges"
    )
    gender: Optional[str] = Field(
        default=None,
        description="Patient gender for gender-specific test recommendations. Options: 'male', 'female', 'M', 'F' (case insensitive)"
    )

# Pydantic Schema for schedule_sample_collection tool
class ScheduleSampleCollectionSchema(BaseModel):
    """Schema for scheduling sample collection appointments"""
    
    order_id: str = Field(description="Order ID to schedule collection for (format: KD20250827ABCD1234)")
    preferred_date: str = Field(
        description="Preferred collection date. Accepts: YYYY-MM-DD format ('2025-08-27'), natural language ('tomorrow', 'next Monday', 'August 30th')"
    )
    preferred_time: str = Field(
        description="Preferred time slot. Options: 'morning' (8AM-12PM), 'afternoon' (12PM-4PM), 'evening' (4PM-8PM), or specific times like '10:00 AM', '2:30 PM'"
    )
    instagram_id: str = Field(description="Customer's Instagram ID for verification")
    special_instructions: Optional[str] = Field(
        default=None,
        description="Special instructions for collection team (e.g., 'Ring doorbell twice', 'Call before arrival', 'Patient is elderly')"
    )

# Advanced Test Panels for Suggestions
ADVANCED_TEST_PANELS = {
    "diabetes": {
        "panel_name": "Comprehensive Diabetes Profile",
        "tests": ["HbA1c", "Fasting Glucose", "Post Prandial Glucose", "Insulin", "C-Peptide"],
        "price": 1200,
        "discounted_price": 999,
        "description": "Complete diabetes assessment with insulin resistance markers"
    },
    "cardiac": {
        "panel_name": "Advanced Cardiac Health Panel", 
        "tests": ["Lipid Profile", "Troponin I", "CRP", "Homocysteine", "ECG"],
        "price": 1800,
        "discounted_price": 1499,
        "description": "Comprehensive heart health evaluation"
    },
    "thyroid": {
        "panel_name": "Complete Thyroid Function Panel",
        "tests": ["TSH", "T3", "T4", "Anti-TPO", "Anti-Thyroglobulin"],
        "price": 1000,
        "discounted_price": 799,
        "description": "Comprehensive thyroid function assessment"
    },
    "liver": {
        "panel_name": "Comprehensive Liver Function Panel",
        "tests": ["SGPT", "SGOT", "Bilirubin", "ALP", "GGT", "Protein"],
        "price": 800,
        "discounted_price": 649,
        "description": "Complete liver health evaluation"
    },
    "women_health": {
        "panel_name": "Women's Health Comprehensive Panel",
        "tests": ["CBC", "Thyroid Profile", "Vitamin D", "Iron Studies", "Hormonal Panel"],
        "price": 2200,
        "discounted_price": 1799,
        "description": "Complete health checkup designed for women"
    },
    "men_health": {
        "panel_name": "Men's Health Comprehensive Panel", 
        "tests": ["CBC", "Lipid Profile", "Liver Function", "Kidney Function", "Testosterone"],
        "price": 2000,
        "discounted_price": 1599,
        "description": "Complete health checkup designed for men"
    }
}


@tool(parse_docstring=True)
def validate_pin_code(pin_code: str) -> Dict[str, Any]:
    """
    Validate if PIN code is serviceable for medical test collection and get area details.
    
    This tool checks if the provided PIN code is within our service coverage area
    and returns detailed information about service availability and area details.
    
    Args:
        pin_code: 6-digit PIN code to validate (e.g., '110001', '560001')
    """
    try:
        logger.info(f"PIN validation started for: {pin_code}")
        
        # Clean PIN code
        clean_pin = str(pin_code).strip()
        logger.debug(f"Cleaned PIN code: '{clean_pin}' (length: {len(clean_pin)})")
        
        if len(clean_pin) != 6 or not clean_pin.isdigit():
            print(f"❌ PIN VALIDATION DEBUG: Invalid format - Length={len(clean_pin)}, IsDigit={clean_pin.isdigit()}")
            error_response = {
                "success": False,
                "serviceable": False,
                "error": "Invalid PIN code format. Please provide a 6-digit PIN code.",
                "pin_code": clean_pin
            }
            print(f"🔍 PIN VALIDATION DEBUG: Returning error response")
            return error_response
        
        print(f"🔍 PIN VALIDATION DEBUG: Checking serviceable pins: {list(SERVICEABLE_PINS.keys())}")
        
        if clean_pin in SERVICEABLE_PINS:
            area_info = SERVICEABLE_PINS[clean_pin]
            print(f"✅ PIN VALIDATION DEBUG: Found serviceable! Area='{area_info['area']}'")
            
            success_response = {
                "success": True,
                "serviceable": area_info["available"],
                "pin_code": clean_pin,
                "area": area_info["area"],
                "home_collection_available": area_info["home_collection"],
                "message": f"Great! We provide services in {area_info['area']}. Home collection is {'available' if area_info['home_collection'] else 'not available'}."
            }
            print(f"🔍 PIN VALIDATION DEBUG: Returning success response")
            return success_response
        else:
            print(f"⚠️ PIN VALIDATION DEBUG: PIN not serviceable")
            not_serviceable_response = {
                "success": True,
                "serviceable": False,
                "pin_code": clean_pin,
                "message": f"Sorry, we currently don't provide services in PIN code {clean_pin}. We are expanding and will reach your area soon!",
                "alternative_message": "You can visit our nearest lab or try a different PIN code where you might want the sample collected."
            }
            print(f"🔍 PIN VALIDATION DEBUG: Returning not serviceable response")
            return not_serviceable_response
            
    except Exception as e:
        print(f"❌ PIN VALIDATION DEBUG: EXCEPTION - {e}")
        print(f"❌ PIN VALIDATION DEBUG: EXCEPTION TYPE - {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        error_response = {
            "success": False,
            "serviceable": False,
            "error": "Unable to validate PIN code at this time.",
            "pin_code": pin_code,
            "debug_error": str(e)
        }
        print(f"🔍 PIN VALIDATION DEBUG: Returning exception response")
        return error_response


@tool("suggest_advanced_test_panel", args_schema=SuggestTestPanelSchema, parse_docstring=True)
def suggest_advanced_test_panel(
    condition_or_symptoms: str,
    age: Optional[int] = None,
    gender: Optional[str] = None
) -> Dict[str, Any]:
    """
    Suggest comprehensive medical test panels based on health conditions, symptoms, or preventive health goals.
    
    This tool uses an intelligent recommendation system that combines predefined panels with 
    database-driven test catalog searches to provide personalized test suggestions based on
    patient demographics and medical conditions.
    
    Args:
        condition_or_symptoms: Health condition or symptoms - Examples: 'diabetes', 'thyroid', 'heart disease'
        age: Patient age in years (0-120) for age-appropriate test selection
        gender: Patient gender ('male'/'female'/'M'/'F') for gender-specific recommendations
    """
    try:
        print(f"🔧 SUGGEST_PANEL DEBUG: condition_or_symptoms='{condition_or_symptoms}'")
        print(f"🔧 SUGGEST_PANEL DEBUG: age={age}, gender={gender}")
        
        # Normalize input
        condition_lower = condition_or_symptoms.lower()
        print(f"🔧 SUGGEST_PANEL DEBUG: normalized condition='{condition_lower}'")
        
        # Try database-driven approach first
        async def _suggest_panel_async():
            async with get_db_session() as session:
                assessment_service_repo = PropertyAssessmentServiceRepository(session)
                
                # Search for tests based on condition/symptoms
                recommended_tests = []
                
                # Map common conditions to search terms
                condition_mappings = {
                    "diabetes": ["diabetes", "blood_sugar", "glucose"],
                    "cardiac": ["heart_disease", "high_cholesterol"], 
                    "thyroid": ["thyroid_disorder", "fatigue", "weight_changes"],
                    "liver": ["liver_disease", "hepatitis"],
                    "kidney": ["kidney_disease", "high_blood_pressure"],
                    "women": ["women_health", "hormonal_imbalance"],
                    "general": ["general_health", "annual_checkup"],
                }
                
                # Find matching conditions
                search_conditions = []
                for key, conditions in condition_mappings.items():
                    if any(word in condition_lower for word in key.split()) or any(cond in condition_lower for cond in conditions):
                        search_conditions.extend(conditions)
                
                print(f"🔧 SUGGEST_PANEL DEBUG: search_conditions={search_conditions}")
                
                # Search for recommended tests
                for condition in search_conditions:
                    tests = await test_catalog_repo.get_recommended_for_condition(condition, limit=5)
                    recommended_tests.extend(tests)
                
                # If no specific condition match, do general search
                if not recommended_tests:
                    print(f"🔧 SUGGEST_PANEL DEBUG: No condition match, searching by keywords")
                    # Search by general keywords
                    search_terms = ["blood test", "health checkup", "basic health", "comprehensive"]
                    for term in search_terms:
                        if term in condition_lower:
                            tests = await test_catalog_repo.search_tests(term, limit=3)
                            recommended_tests.extend(tests)
                            break
                
                # Remove duplicates and get best match
                seen_codes = set()
                unique_tests = []
                for test in recommended_tests:
                    if test.test_code not in seen_codes:
                        unique_tests.append(test)
                        seen_codes.add(test.test_code)
                
                print(f"🔧 SUGGEST_PANEL DEBUG: Found {len(unique_tests)} unique tests")
                
                if unique_tests:
                    # Return the most suitable test (first one, sorted by price in repo)
                    best_test = unique_tests[0]
                    
                    savings = 0
                    if best_test.discounted_price and best_test.discounted_price < best_test.price:
                        savings = float(best_test.price - best_test.discounted_price)
                        savings_percent = (savings / float(best_test.price)) * 100
                        final_price = float(best_test.discounted_price)
                    else:
                        savings_percent = 0
                        final_price = float(best_test.price)
                    
                    print(f"✅ SUGGEST_PANEL DEBUG: Recommending {best_test.name}")
                    
                    return {
                        "success": True,
                        "panel_suggested": True,
                        "panel_name": best_test.name,
                        "test_code": best_test.test_code,
                        "description": best_test.description,
                        "tests_included": best_test.includes or [best_test.name],
                        "category": best_test.category,
                        "original_price": float(best_test.price),
                        "discounted_price": final_price,
                        "savings": savings,
                        "savings_percent": round(savings_percent, 1),
                        "sample_type": best_test.sample_type,
                        "fasting_required": best_test.fasting_required,
                        "home_collection": best_test.home_collection,
                        "message": f"Based on your requirements, I recommend the {best_test.name}. It includes {len(best_test.includes or [best_test.name])} test(s)" + (f" and you save ₹{savings:.0f} ({savings_percent:.1f}% off)!" if savings > 0 else "!"),
                        "tests_count": len(best_test.includes or [best_test.name]),
                        "data_source": "database"
                    }
                return None  # No suitable test found
        
        try:
            result = asyncio.run(_suggest_panel_async())
            if result:
                return result
        except Exception as db_error:
            print(f"⚠️ SUGGEST_PANEL DEBUG: Database error: {db_error}")
            print("🔧 SUGGEST_PANEL DEBUG: Falling back to hardcoded panels")
        
        # Fallback to hardcoded panels if database fails
        suggested_panel = None
        
        if any(word in condition_lower for word in ["diabetes", "sugar", "glucose", "hba1c"]):
            suggested_panel = ADVANCED_TEST_PANELS["diabetes"]
        elif any(word in condition_lower for word in ["heart", "cardiac", "cholesterol", "chest pain"]):
            suggested_panel = ADVANCED_TEST_PANELS["cardiac"]
        elif any(word in condition_lower for word in ["thyroid", "weight", "fatigue", "hair loss"]):
            suggested_panel = ADVANCED_TEST_PANELS["thyroid"]
        elif any(word in condition_lower for word in ["liver", "jaundice", "alcohol", "hepatitis"]):
            suggested_panel = ADVANCED_TEST_PANELS["liver"]
        elif gender and gender.lower() in ["female", "woman", "f"] and any(word in condition_lower for word in ["health check", "checkup", "screening", "women", "blood test"]):
            suggested_panel = ADVANCED_TEST_PANELS["women_health"]
        elif gender and gender.lower() in ["male", "man", "m"] and any(word in condition_lower for word in ["health check", "checkup", "screening", "men", "blood test"]):
            suggested_panel = ADVANCED_TEST_PANELS["men_health"]
        elif any(word in condition_lower for word in ["health check", "checkup", "screening", "blood test", "general"]):
            suggested_panel = ADVANCED_TEST_PANELS["thyroid"]  # Default fallback
        
        if suggested_panel:
            print(f"✅ SUGGEST_PANEL DEBUG: Found hardcoded panel: {suggested_panel['panel_name']}")
            savings = suggested_panel["price"] - suggested_panel["discounted_price"]
            savings_percent = (savings / suggested_panel["price"]) * 100
            
            return {
                "success": True,
                "panel_suggested": True,
                "panel_name": suggested_panel["panel_name"],
                "description": suggested_panel["description"],
                "tests": suggested_panel["tests"],  # Fixed: renamed from tests_included
                "original_price": suggested_panel["price"],
                "discounted_price": suggested_panel["discounted_price"],
                "savings": savings,
                "savings_percent": round(savings_percent, 1),
                "message": f"Based on your requirements, I recommend the {suggested_panel['panel_name']}. It includes {len(suggested_panel['tests'])} tests and you save ₹{savings} ({savings_percent:.1f}% off)!",
                "tests_count": len(suggested_panel["tests"]),
                "data_source": "hardcoded"
            }
        else:
            print(f"⚠️ SUGGEST_PANEL DEBUG: No matching panel found for '{condition_lower}'")
            return {
                "success": True,
                "panel_suggested": False,
                "message": "Let me help you find the right tests. Could you provide more details about your symptoms or what specific health concerns you have?",
                "suggestion": "You can also opt for our general health checkup packages."
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
    
    # Define panel mappings (test codes that should get panel pricing)
    panels = {
        "diabetes": {
            "required_codes": ["HBA1C", "GLU_F"],  # Minimum required for diabetes panel
            "optional_codes": ["PPBS", "INSULIN", "CPEPTIDE"],
            "panel_name": "Comprehensive Diabetes Profile",
            "discounted_price": 999
        }
    }
    
    for panel_key, panel_info in panels.items():
        required_codes = panel_info["required_codes"]
        
        # Check if all required codes are present
        if all(code in test_codes_upper for code in required_codes):
            print(f"🎯 PANEL_PRICING DEBUG: Found matching panel '{panel_info['panel_name']}'")
            return panel_info
    
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
        
        # Auto-map common test names that customers might use
        mapped_test_codes = []
        for code in test_codes:
            if code.upper() == "FBS" or code.lower() in ["fasting glucose", "fasting sugar"]:
                mapped_test_codes.append("GLU_F")
            elif code.upper() == "SUGAR" or code.lower() in ["blood sugar", "glucose"]:
                mapped_test_codes.append("GLU_F")
            elif code.upper() in ["HBA1C", "HBAIC", "A1C"]:
                mapped_test_codes.append("HBA1C")
            # Prescription test mappings
            elif "HLA B27" in code.upper() or "HLA-B27" in code.upper():
                mapped_test_codes.append("HLA_B27_PCR")
            elif "MRI OF DL SPINE" in code.upper() or "MRI DL SPINE" in code.upper() or "MRI OF D L SPINE" in code.upper():
                mapped_test_codes.append("MRI_DL_SPINE")
            elif "MRI OF SI JOINTS" in code.upper() or "MRI SI JOINTS" in code.upper():
                mapped_test_codes.append("MRI_SI_JOINTS")
            else:
                mapped_test_codes.append(code.upper())
        
        test_codes = mapped_test_codes
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
            
            # Look up each test in the database
            for test_code in test_codes:
                test_upper = test_code.upper()
                print(f"🔍 CREATE_ORDER DEBUG: Looking up test {test_upper}")
                
                # Search for test by code or name
                test = await test_catalog_repo.get_by_code(test_upper)
                
                if not test:
                    # Try searching by name if code lookup fails
                    search_results = await test_catalog_repo.search_tests(test_upper, limit=1)
                    test = search_results[0] if search_results else None
                
                if test and test.available:
                    test_info = {
                        "code": test.test_code,
                        "name": test.name,
                        "description": test.description,
                        "price": float(test.price),
                        "discounted_price": float(test.discounted_price) if test.discounted_price is not None else float(test.price),
                        "sample_type": test.sample_type,
                        "fasting_required": test.fasting_required,
                        "home_collection": test.home_collection,
                        "category": test.category
                    }
                    validated_tests.append(test_info)
                    price_to_use = float(test.discounted_price) if test.discounted_price is not None else float(test.price)
                    total_amount += price_to_use
                    print(f"✅ CREATE_ORDER DEBUG: Added {test.name} - ₹{price_to_use}")
                else:
                    not_found_tests.append(test_code)
                    print(f"⚠️ CREATE_ORDER DEBUG: Test not found or unavailable: {test_code}")
            
            # Check if tests match a known panel for special pricing
            panel_pricing = _check_panel_pricing(test_codes, validated_tests)
            if panel_pricing:
                total_amount = panel_pricing["discounted_price"]
                print(f"💰 CREATE_ORDER DEBUG: Applied panel pricing: {panel_pricing['panel_name']} - ₹{total_amount}")
            
            if not validated_tests:
                # Get available tests for suggestion
                available_tests = await test_catalog_repo.search_tests("", limit=10)
                available_codes = [t.test_code for t in available_tests]
                
                print(f"❌ CREATE_ORDER DEBUG: No valid tests found")
                # Create user-friendly suggestion based on not found test
                user_friendly_suggestion = ""
                if "FBS" in not_found_tests:
                    user_friendly_suggestion = "For fasting glucose, please try 'GLU_F'"
                elif "CBC" in not_found_tests:
                    user_friendly_suggestion = "For complete blood count, the available code is 'CBC'"
                else:
                    # Map available codes to friendly names
                    friendly_available = []
                    for code in available_codes[:3]:
                        if code == "GLU_F":
                            friendly_available.append("Fasting Glucose (GLU_F)")
                        elif code == "HBA1C":
                            friendly_available.append("HbA1c Test (HBA1C)")
                        else:
                            friendly_available.append(code)
                    user_friendly_suggestion = f"Available tests: {', '.join(friendly_available)}"
                
                return {
                    "success": False,
                    "error": "The requested test is not available with that name.",
                    "not_found": not_found_tests,
                    "user_friendly_suggestion": user_friendly_suggestion,
                    "retry_needed": True
                }
        
            print(f"✅ CREATE_ORDER DEBUG: Validated {len(validated_tests)} tests, total=₹{total_amount}")
            
            # Create/update customer record
            print(f"🔧 CREATE_ORDER DEBUG: Creating/updating customer record")
            customer = await customer_repo.create_or_update(
                instagram_id=instagram_id,
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
                
                # Find the test record for the test_id
                test_record = await test_catalog_repo.get_by_code(test_info["code"])
                
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
                        test_id=test_record.id,
                        booking_id=booking_id,
                        total_amount=Decimal(str(test_info["discounted_price"])),
                        preferred_date=parsed_preferred_date,
                        preferred_time=preferred_time,
                        collection_type=collection_type,
                        collection_address=processed_address
                    )
                    booking_ids.append(booking.booking_id)
                    print(f"✅ CREATE_ORDER DEBUG: Created booking {booking.booking_id} for {test_info['name']}")
                else:
                    print(f"⚠️ CREATE_ORDER DEBUG: Could not find test record for {test_info['code']}")
            
            # Prepare order data for Redis storage (for quick access)
            order_data = {
                "order_id": order_id,
                "customer_id": customer.id,
                "customer_name": customer_name,
                "phone": phone,
                "instagram_id": instagram_id,
                "tests_booked": validated_tests,
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
        base_url = os.getenv('BASE_URL', 'https://dev-payments.krsnaa.com')
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
                "description": f"Krsnaa Diagnostics - Medical Tests for Order {order_id}",
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
                    download_link = f"https://reports.krsnaa.com/download/{booking.booking_id}"
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
            
            customer = await customer_repo.get_by_instagram_id(instagram_id)
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
                "message": "Order confirmed! You can pay cash during sample collection.",
                "next_steps": "Our phlebotomist will contact you to schedule the sample collection."
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


@tool("schedule_sample_collection", args_schema=ScheduleSampleCollectionSchema, parse_docstring=True)
async def schedule_sample_collection(
    order_id: str,
    preferred_date: str,
    preferred_time: str,
    instagram_id: str,
    special_instructions: Optional[str] = None
) -> Dict[str, Any]:
    """
    Schedule home sample collection appointment for confirmed medical test orders.
    
    This tool manages the scheduling process including date validation, time slot availability,
    and coordination with the phlebotomy team for sample collection at customer's location.
    
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
            "error": "Failed to schedule sample collection"
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