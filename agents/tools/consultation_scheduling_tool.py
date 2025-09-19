"""
Consultation Scheduling Tool for Property Tax Services

Manages appointment scheduling for property tax consultations with consultants,
handles availability checking, time zone conversions, and appointment coordination.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date, time, timedelta
import pytz
from decimal import Decimal

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from mock_data.consultant_schedules import (
    CONSULTANT_PROFILES,
    APPOINTMENT_TYPES,
    OFFICE_LOCATIONS,
    TEXAS_TIMEZONES,
    generate_consultant_schedule,
    find_available_time_slots,
    get_consultant_recommendations,
    calculate_optimal_meeting_times
)
from agents.tools.property_validation_tool import property_validation_tool

logger = structlog.get_logger()

class ConsultationSchedulingInput(BaseModel):
    """Input schema for consultation scheduling"""
    appointment_type: str = Field(description="Type of consultation appointment")
    property_address: Optional[str] = Field(default=None, description="Property address for context")
    county: Optional[str] = Field(default=None, description="Property county")
    property_type: Optional[str] = Field(default="residential", description="Property type")
    preferred_consultant: Optional[str] = Field(default=None, description="Preferred consultant ID")
    preferred_dates: Optional[List[str]] = Field(default=None, description="Preferred dates (YYYY-MM-DD format)")
    preferred_times: Optional[List[str]] = Field(default=None, description="Preferred times (HH:MM format)")
    meeting_type: str = Field(default="in_person", description="Meeting type: in_person, virtual, client_location")
    location_preference: Optional[str] = Field(default=None, description="Preferred office location")
    case_complexity: str = Field(default="medium", description="Case complexity: low, medium, high")
    urgency_level: str = Field(default="normal", description="Urgency: normal, high, emergency")
    client_info: Optional[Dict[str, Any]] = Field(default=None, description="Client contact information")
    special_requirements: Optional[List[str]] = Field(default=None, description="Special requirements or accommodations")

class ConsultationSchedulingResponse(BaseModel):
    """Response schema for consultation scheduling"""
    success: bool = Field(description="Whether scheduling was successful")
    appointment_details: Optional[Dict[str, Any]] = Field(description="Scheduled appointment information")
    available_slots: List[Dict[str, Any]] = Field(description="Available time slots")
    consultant_recommendations: List[Dict[str, Any]] = Field(description="Recommended consultants")
    scheduling_options: Dict[str, Any] = Field(description="Available scheduling options")
    next_steps: List[Dict[str, str]] = Field(description="Required next steps for confirmation")

def validate_appointment_inputs(
    appointment_type: str,
    preferred_dates: Optional[List[str]] = None,
    meeting_type: str = "in_person"
) -> Dict[str, Any]:
    """Validate scheduling inputs"""

    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }

    # Validate appointment type
    if appointment_type not in APPOINTMENT_TYPES:
        validation_result["errors"].append(
            f"Invalid appointment type: {appointment_type}. "
            f"Available types: {', '.join(APPOINTMENT_TYPES.keys())}"
        )
        validation_result["is_valid"] = False

    # Validate meeting type compatibility
    appointment_info = APPOINTMENT_TYPES.get(appointment_type, {})
    if meeting_type == "virtual" and not appointment_info.get("can_be_virtual", True):
        validation_result["errors"].append(
            f"Appointment type '{appointment_type}' cannot be conducted virtually"
        )
        validation_result["is_valid"] = False

    # Validate dates
    if preferred_dates:
        for date_str in preferred_dates:
            try:
                preferred_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if preferred_date < date.today():
                    validation_result["warnings"].append(
                        f"Date {date_str} is in the past"
                    )
                elif preferred_date < date.today() + timedelta(days=1):
                    validation_result["warnings"].append(
                        f"Date {date_str} is very soon - limited availability"
                    )
            except ValueError:
                validation_result["errors"].append(
                    f"Invalid date format: {date_str}. Use YYYY-MM-DD format"
                )
                validation_result["is_valid"] = False

    return validation_result

def find_best_consultant_match(
    property_type: str,
    county: str,
    case_complexity: str,
    appointment_type: str,
    preferred_consultant: Optional[str] = None
) -> Optional[str]:
    """Find the best consultant match for the requirements"""

    if preferred_consultant and preferred_consultant in CONSULTANT_PROFILES:
        consultant = CONSULTANT_PROFILES[preferred_consultant]
        # Verify consultant serves the county
        if county.lower() in consultant["counties_served"]:
            return preferred_consultant
        else:
            logger.warning("Preferred consultant doesn't serve county",
                         consultant=preferred_consultant, county=county)

    # Get recommendations and return the top match
    recommendations = get_consultant_recommendations(
        property_type, county, case_complexity
    )

    if recommendations:
        return recommendations[0]["consultant_id"]

    return None

def calculate_appointment_pricing(
    appointment_type: str,
    meeting_type: str,
    location: Optional[str] = None,
    urgency_level: str = "normal"
) -> Dict[str, Any]:
    """Calculate total appointment pricing including additional fees"""

    base_price = APPOINTMENT_TYPES[appointment_type]["price"]
    additional_fees = []
    total_price = base_price

    # Travel fee for client location meetings
    if meeting_type == "client_location":
        travel_fee = OFFICE_LOCATIONS["client_location"]["additional_fee"]
        additional_fees.append({
            "type": "travel_fee",
            "amount": travel_fee,
            "description": "Travel to client location"
        })
        total_price += travel_fee

    # Emergency scheduling fee
    if urgency_level == "emergency":
        emergency_fee = max(100, base_price * 0.5)  # 50% surcharge or $100 minimum
        additional_fees.append({
            "type": "emergency_fee",
            "amount": emergency_fee,
            "description": "Emergency scheduling surcharge"
        })
        total_price += emergency_fee

    # Weekend fee (if applicable)
    # Note: This would be calculated based on actual appointment date in real implementation

    return {
        "base_price": base_price,
        "additional_fees": additional_fees,
        "total_price": total_price,
        "currency": "USD"
    }

def generate_appointment_confirmation_details(
    appointment_slot: Dict[str, Any],
    consultant_id: str,
    meeting_type: str,
    location: Optional[str] = None,
    client_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate comprehensive appointment confirmation details"""

    consultant = CONSULTANT_PROFILES[consultant_id]
    appointment_info = APPOINTMENT_TYPES[appointment_slot["appointment_type"]]

    # Determine meeting location details
    location_details = {}
    if meeting_type == "in_person":
        if location and location in OFFICE_LOCATIONS:
            location_details = OFFICE_LOCATIONS[location]
        else:
            # Default to main office serving the consultant's primary county
            primary_county = consultant["counties_served"][0]
            if primary_county == "harris":
                location_details = OFFICE_LOCATIONS["houston_main"]
            elif primary_county == "dallas":
                location_details = OFFICE_LOCATIONS["dallas_office"]
            elif primary_county == "travis":
                location_details = OFFICE_LOCATIONS["austin_office"]

    elif meeting_type == "virtual":
        location_details = OFFICE_LOCATIONS["virtual_meeting"]

    elif meeting_type == "client_location":
        location_details = OFFICE_LOCATIONS["client_location"]

    # Generate confirmation details
    confirmation = {
        "appointment_id": f"APT-{datetime.now().strftime('%Y%m%d')}-{consultant_id[-3:]}-{hash(str(appointment_slot)) % 1000:03d}",
        "appointment_date": appointment_slot["date"],
        "start_time": appointment_slot["start_time"],
        "end_time": appointment_slot["end_time"],
        "duration_minutes": appointment_slot["duration_minutes"],
        "appointment_type": appointment_slot["appointment_type"],
        "appointment_description": appointment_info["description"],
        "consultant": {
            "id": consultant_id,
            "name": consultant["name"],
            "title": consultant["title"],
            "contact": consultant["contact"],
            "specialties": consultant["specialties"]
        },
        "meeting_details": {
            "type": meeting_type,
            "location": location_details
        },
        "preparation_required": appointment_info["preparation_required"],
        "deliverables": appointment_info["deliverables"],
        "pricing": calculate_appointment_pricing(
            appointment_slot["appointment_type"],
            meeting_type
        ),
        "client_info": client_info or {},
        "timezone": consultant["availability"]["timezone"],
        "status": "pending_confirmation"
    }

    return confirmation

@tool("consultation_scheduling_tool", return_direct=False)
async def consultation_scheduling_tool(
    appointment_type: str,
    property_address: Optional[str] = None,
    county: Optional[str] = None,
    property_type: str = "residential",
    preferred_consultant: Optional[str] = None,
    preferred_dates: Optional[List[str]] = None,
    preferred_times: Optional[List[str]] = None,
    meeting_type: str = "in_person",
    location_preference: Optional[str] = None,
    case_complexity: str = "medium",
    urgency_level: str = "normal",
    client_info: Optional[Dict[str, Any]] = None,
    special_requirements: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Schedule property tax consultation appointments with qualified consultants.

    Handles availability checking, consultant matching, and appointment coordination
    for various types of property tax consultations including initial consultations,
    follow-ups, document reviews, and hearing preparation.

    Args:
        appointment_type: Type of consultation (initial_consultation, follow_up, document_review, hearing_prep, emergency_consultation)
        property_address: Property address for context and validation
        county: Property county for consultant matching
        property_type: Property type (residential, commercial, industrial, agricultural)
        preferred_consultant: Specific consultant ID if preferred
        preferred_dates: List of preferred dates in YYYY-MM-DD format
        preferred_times: List of preferred times in HH:MM format
        meeting_type: Type of meeting (in_person, virtual, client_location)
        location_preference: Preferred office location
        case_complexity: Complexity level (low, medium, high)
        urgency_level: Urgency (normal, high, emergency)
        client_info: Client contact and preference information
        special_requirements: Special accommodations needed

    Returns:
        Comprehensive scheduling results with available slots and recommendations
    """
    try:
        logger.info("📅 Processing consultation scheduling request",
                   appointment_type=appointment_type, county=county,
                   meeting_type=meeting_type, urgency=urgency_level)

        # Validate inputs
        validation_result = validate_appointment_inputs(
            appointment_type, preferred_dates, meeting_type
        )

        if not validation_result["is_valid"]:
            return {
                "success": False,
                "errors": validation_result["errors"],
                "suggestions": [
                    f"Available appointment types: {', '.join(APPOINTMENT_TYPES.keys())}",
                    "Use YYYY-MM-DD format for dates",
                    "Check meeting type compatibility with appointment type"
                ]
            }

        # Validate property if address provided
        property_context = {}
        if property_address and not county:
            # Try to validate property to get county information
            property_validation = await property_validation_tool(property_address)
            if property_validation.get("success") and property_validation.get("property_found"):
                property_data = property_validation["property_data"]
                county = property_data.get("county", "").lower().replace(" county", "")
                property_context = {
                    "validated": True,
                    "county": property_data.get("county"),
                    "parcel_id": property_data.get("parcel_id"),
                    "property_type": property_data.get("property_type"),
                    "assessed_value": property_data.get("current_assessed_value")
                }

        # Ensure we have county information
        if not county:
            county = "harris"  # Default to Harris County
            property_context["county_defaulted"] = True

        # Find best consultant match
        best_consultant = find_best_consultant_match(
            property_type, county, case_complexity, appointment_type, preferred_consultant
        )

        if not best_consultant:
            return {
                "success": False,
                "error": "No suitable consultant found for requirements",
                "suggestions": [
                    f"No consultants available for {county} county",
                    "Try expanding to nearby counties",
                    "Consider virtual consultation options",
                    "Contact support for manual scheduling"
                ]
            }

        # Determine search dates
        search_dates = []
        if preferred_dates:
            for date_str in preferred_dates:
                try:
                    search_dates.append(datetime.strptime(date_str, "%Y-%m-%d").date())
                except ValueError:
                    continue
        else:
            # Default to next 14 days
            start_date = date.today() + timedelta(days=1)
            search_dates = [start_date + timedelta(days=i) for i in range(14)]

        # Find available slots
        available_slots = []
        for search_date in search_dates[:7]:  # Limit to first 7 dates
            slots = find_available_time_slots(
                best_consultant, appointment_type, search_date, 1
            )
            available_slots.extend(slots)

        # Filter by preferred times if specified
        if preferred_times and available_slots:
            filtered_slots = []
            for slot in available_slots:
                slot_time = datetime.strptime(slot["start_time"], "%H:%M").time()
                for pref_time_str in preferred_times:
                    try:
                        pref_time = datetime.strptime(pref_time_str, "%H:%M").time()
                        # Allow 1-hour window around preferred time
                        time_diff = abs((datetime.combine(date.today(), slot_time) -
                                       datetime.combine(date.today(), pref_time)).total_seconds())
                        if time_diff <= 3600:  # Within 1 hour
                            filtered_slots.append(slot)
                            break
                    except ValueError:
                        continue
            available_slots = filtered_slots

        # Sort slots by date and time
        available_slots.sort(key=lambda x: (x["date"], x["start_time"]))

        # Get consultant recommendations
        consultant_recommendations = get_consultant_recommendations(
            property_type, county, case_complexity
        )

        # Prepare scheduling options
        scheduling_options = {
            "appointment_types": list(APPOINTMENT_TYPES.keys()),
            "meeting_types": ["in_person", "virtual", "client_location"],
            "available_locations": list(OFFICE_LOCATIONS.keys()),
            "urgency_levels": ["normal", "high", "emergency"],
            "case_complexity_levels": ["low", "medium", "high"]
        }

        # Handle emergency scheduling
        next_steps = []
        if urgency_level == "emergency":
            next_steps.append({
                "step": "emergency_contact",
                "description": "Contact consultant directly for emergency scheduling",
                "contact": CONSULTANT_PROFILES[best_consultant]["contact"]["phone"],
                "priority": "immediate"
            })

        # Generate appointment if we have available slots
        appointment_details = None
        if available_slots:
            # Select best slot (first available, considering urgency)
            selected_slot = available_slots[0]

            if urgency_level == "emergency" and len(available_slots) > 1:
                # For emergency, try to find earliest slot
                selected_slot = min(available_slots, key=lambda x: (x["date"], x["start_time"]))

            appointment_details = generate_appointment_confirmation_details(
                selected_slot,
                best_consultant,
                meeting_type,
                location_preference,
                client_info
            )

            next_steps.extend([
                {
                    "step": "confirm_appointment",
                    "description": "Confirm appointment details and provide required documents",
                    "priority": "high"
                },
                {
                    "step": "payment_processing",
                    "description": f"Process payment of ${appointment_details['pricing']['total_price']}",
                    "priority": "medium"
                },
                {
                    "step": "document_preparation",
                    "description": "Prepare required documents for consultation",
                    "priority": "medium"
                }
            ])

        return {
            "success": True,
            "appointment_details": appointment_details,
            "available_slots": available_slots[:10],  # Limit to 10 slots
            "consultant_recommendations": consultant_recommendations[:5],  # Top 5
            "scheduling_options": scheduling_options,
            "next_steps": next_steps,
            "property_context": property_context,
            "validation_warnings": validation_result.get("warnings", []),
            "scheduling_metadata": {
                "search_dates_count": len(search_dates),
                "available_slots_count": len(available_slots),
                "primary_consultant": best_consultant,
                "meeting_type": meeting_type,
                "urgency_level": urgency_level,
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error("❌ Consultation scheduling failed",
                    error=str(e), appointment_type=appointment_type)

        return {
            "success": False,
            "error": f"Scheduling failed: {str(e)}",
            "suggestions": [
                "Verify appointment type is valid",
                "Check date format (YYYY-MM-DD)",
                "Ensure county is supported",
                "Try with different meeting type preferences",
                "Contact support for manual scheduling assistance"
            ]
        }

# Additional utility functions

async def reschedule_appointment(
    appointment_id: str,
    new_date: str,
    new_time: Optional[str] = None
) -> Dict[str, Any]:
    """Reschedule an existing appointment"""
    # In real implementation, would look up existing appointment
    # For mock, simulate rescheduling process

    return {
        "success": True,
        "appointment_id": appointment_id,
        "original_date": "2024-03-15",
        "new_date": new_date,
        "new_time": new_time or "09:00",
        "reschedule_fee": 0,  # No fee for mock
        "confirmation_required": True
    }

async def cancel_appointment(
    appointment_id: str,
    cancellation_reason: Optional[str] = None
) -> Dict[str, Any]:
    """Cancel an existing appointment"""
    # Calculate cancellation policy
    cancellation_fee = 0
    # Normally would check timing of cancellation vs appointment date

    return {
        "success": True,
        "appointment_id": appointment_id,
        "cancellation_fee": cancellation_fee,
        "refund_amount": 0,  # Would calculate based on original payment
        "cancellation_reason": cancellation_reason,
        "confirmation_sent": True
    }

def get_consultant_availability_summary(
    consultant_id: str,
    days_ahead: int = 30
) -> Dict[str, Any]:
    """Get availability summary for a consultant"""
    if consultant_id not in CONSULTANT_PROFILES:
        return {"error": "Consultant not found"}

    consultant = CONSULTANT_PROFILES[consultant_id]
    start_date = date.today()

    # Generate schedule
    schedule = generate_consultant_schedule(consultant_id, start_date, days_ahead)

    # Calculate availability metrics
    total_days = 0
    available_days = 0
    total_appointments = 0

    for day_data in schedule["schedule"].values():
        if day_data["working_hours"]:
            total_days += 1
            if day_data["available"]:
                available_days += 1
            total_appointments += len(day_data["appointments"])

    availability_percentage = (available_days / total_days * 100) if total_days > 0 else 0

    return {
        "consultant_id": consultant_id,
        "consultant_name": consultant["name"],
        "period": f"{start_date} to {start_date + timedelta(days=days_ahead-1)}",
        "total_working_days": total_days,
        "available_days": available_days,
        "availability_percentage": round(availability_percentage, 1),
        "total_appointments": total_appointments,
        "average_appointments_per_day": round(total_appointments / max(1, total_days), 1)
    }

def find_group_consultation_times(
    participants: List[str],
    appointment_type: str,
    preferred_dates: List[date]
) -> List[Dict[str, Any]]:
    """Find available times for group consultations with multiple consultants"""

    return calculate_optimal_meeting_times(participants, appointment_type, preferred_dates)

def get_appointment_preparation_checklist(appointment_type: str) -> Dict[str, Any]:
    """Get preparation checklist for specific appointment type"""

    appointment_info = APPOINTMENT_TYPES.get(appointment_type)
    if not appointment_info:
        return {"error": "Invalid appointment type"}

    return {
        "appointment_type": appointment_type,
        "preparation_required": appointment_info["preparation_required"],
        "expected_deliverables": appointment_info["deliverables"],
        "duration": appointment_info["duration_minutes"],
        "can_be_virtual": appointment_info["can_be_virtual"],
        "advance_preparation_time": "24-48 hours recommended"
    }