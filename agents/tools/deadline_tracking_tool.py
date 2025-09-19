"""
Deadline Tracking Tool for Texas Property Tax System

Tracks tax payment deadlines, appeal deadlines, and exemption deadlines
by county with automated notifications and reminders.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date, timedelta
from decimal import Decimal

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from mock_data.tax_calendars import (
    get_county_calendar,
    get_current_deadlines,
    calculate_payment_amount,
    get_notification_preferences,
    COUNTY_TAX_CALENDARS,
    BUSINESS_PROPERTY_DEADLINES,
    SPECIAL_CIRCUMSTANCES
)

logger = structlog.get_logger()

class DeadlineTrackingInput(BaseModel):
    """Input schema for deadline tracking"""
    county_code: str = Field(description="County code for deadline tracking")
    tracking_type: str = Field(
        default="all",
        description="Type of deadlines to track: all, payment, appeal, exemption, assessment"
    )
    property_type: Optional[str] = Field(
        default=None,
        description="Property type for specific deadline filtering"
    )
    current_date: Optional[str] = Field(
        default=None,
        description="Current date for deadline calculation (YYYY-MM-DD format)"
    )
    notification_preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Notification preferences for reminders"
    )
    custom_reminders: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Custom reminder settings"
    )

class DeadlineTrackingResponse(BaseModel):
    """Response schema for deadline tracking"""
    success: bool = Field(description="Whether tracking request was successful")
    county_info: Dict[str, Any] = Field(description="County information and contact details")
    upcoming_deadlines: List[Dict[str, Any]] = Field(description="List of upcoming deadlines")
    overdue_deadlines: List[Dict[str, Any]] = Field(description="List of overdue deadlines")
    notifications_scheduled: List[Dict[str, Any]] = Field(description="Scheduled notifications")
    quick_actions: List[Dict[str, str]] = Field(description="Quick action recommendations")

def parse_date_safely(date_string: str) -> Optional[date]:
    """Safely parse date string"""
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

def calculate_urgency_score(days_until: int, deadline_category: str) -> int:
    """Calculate urgency score (1-10) based on days until deadline and category"""
    # Base urgency based on days
    if days_until < 0:  # Overdue
        base_urgency = 10
    elif days_until <= 3:
        base_urgency = 9
    elif days_until <= 7:
        base_urgency = 8
    elif days_until <= 14:
        base_urgency = 6
    elif days_until <= 30:
        base_urgency = 4
    else:
        base_urgency = 2

    # Adjust based on deadline category importance
    category_modifiers = {
        "appeal": 1.2,      # Appeals have strict deadlines
        "exemption": 1.1,   # Exemptions save money long-term
        "payment": 1.0,     # Standard importance
        "assessment": 0.8,  # Informational mostly
        "other": 0.9
    }

    modifier = category_modifiers.get(deadline_category, 1.0)
    urgency_score = min(10, int(base_urgency * modifier))

    return urgency_score

def generate_quick_actions(deadlines: List[Dict[str, Any]], county_info: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate quick action recommendations based on upcoming deadlines"""
    actions = []

    # Sort deadlines by urgency
    urgent_deadlines = [d for d in deadlines if d.get("urgency") == "high" or d.get("days_until_deadline", 999) <= 7]

    for deadline in urgent_deadlines[:3]:  # Top 3 most urgent
        deadline_name = deadline.get("deadline_name", "").lower()

        if "homestead" in deadline_name:
            actions.append({
                "action": "File Homestead Exemption",
                "priority": "high",
                "description": "Apply for homestead exemption to save on taxes",
                "contact": county_info.get("contact", {}).get("phone", ""),
                "deadline": deadline.get("deadline_date", "")
            })

        elif "protest" in deadline_name:
            actions.append({
                "action": "File Property Tax Protest",
                "priority": "high",
                "description": "Challenge your property assessment",
                "contact": county_info.get("contact", {}).get("website", ""),
                "deadline": deadline.get("deadline_date", "")
            })

        elif "discount" in deadline_name:
            actions.append({
                "action": "Pay Early for Discount",
                "priority": "medium",
                "description": "Pay taxes before discount deadline to save 3%",
                "contact": county_info.get("payment_options", {}).get("online", ""),
                "deadline": deadline.get("deadline_date", "")
            })

        elif "payment" in deadline_name or "penalty" in deadline_name:
            actions.append({
                "action": "Pay Property Taxes",
                "priority": "high",
                "description": "Pay taxes to avoid penalties and interest",
                "contact": county_info.get("payment_options", {}).get("online", ""),
                "deadline": deadline.get("deadline_date", "")
            })

    return actions

def schedule_notifications(
    deadlines: List[Dict[str, Any]],
    preferences: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Schedule notifications based on deadlines and preferences"""
    notifications = []

    # Default notification schedule if not specified
    default_advances = [30, 14, 7, 3, 1]  # days before deadline
    advance_days = preferences.get("advance_notice", default_advances)
    notification_method = preferences.get("method", "email")

    for deadline in deadlines:
        deadline_date = parse_date_safely(deadline.get("deadline_date", ""))
        if not deadline_date:
            continue

        current_date = date.today()
        days_until = (deadline_date - current_date).days

        # Only schedule notifications for future deadlines
        if days_until > 0:
            for advance in advance_days:
                notification_date = deadline_date - timedelta(days=advance)

                # Only schedule if notification date is in the future
                if notification_date >= current_date:
                    notifications.append({
                        "notification_date": notification_date.isoformat(),
                        "deadline_name": deadline.get("deadline_name", ""),
                        "deadline_date": deadline.get("deadline_date", ""),
                        "days_in_advance": advance,
                        "method": notification_method,
                        "urgency": deadline.get("urgency", "medium"),
                        "message_template": generate_notification_message(deadline, advance)
                    })

    # Sort notifications by date
    notifications.sort(key=lambda x: x["notification_date"])

    return notifications

def generate_notification_message(deadline: Dict[str, Any], days_advance: int) -> str:
    """Generate notification message template"""
    deadline_name = deadline.get("deadline_name", "Deadline")
    deadline_date = deadline.get("deadline_date", "")

    if days_advance == 1:
        urgency = "URGENT: "
    elif days_advance <= 3:
        urgency = "IMPORTANT: "
    else:
        urgency = "REMINDER: "

    message = f"{urgency}{deadline_name} is "

    if days_advance == 0:
        message += "TODAY"
    elif days_advance == 1:
        message += "TOMORROW"
    else:
        message += f"in {days_advance} days"

    message += f" ({deadline_date}). "

    # Add action-specific guidance
    deadline_lower = deadline_name.lower()
    if "homestead" in deadline_lower:
        message += "File your homestead exemption application to reduce your property taxes."
    elif "protest" in deadline_lower:
        message += "File your property tax protest to challenge your assessment."
    elif "discount" in deadline_lower:
        message += "Pay your property taxes early to receive a 3% discount."
    elif "payment" in deadline_lower or "penalty" in deadline_lower:
        message += "Pay your property taxes to avoid penalties and interest."
    else:
        message += "Take action to meet this important deadline."

    return message

@tool("deadline_tracking_tool", return_direct=False)
async def deadline_tracking_tool(
    county_code: str,
    tracking_type: str = "all",
    property_type: Optional[str] = None,
    current_date: Optional[str] = None,
    notification_preferences: Optional[Dict[str, Any]] = None,
    custom_reminders: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Track property tax deadlines and schedule notifications for Texas counties.

    Monitors payment deadlines, appeal deadlines, exemption deadlines, and assessment dates
    with customizable notification preferences and automated reminders.

    Args:
        county_code: County code (harris, dallas, tarrant, travis, bexar, collin)
        tracking_type: Type of deadlines (all, payment, appeal, exemption, assessment)
        property_type: Property type for specific filtering
        current_date: Current date for calculations (defaults to today)
        notification_preferences: Notification settings (method, advance_notice, etc.)
        custom_reminders: Custom reminder configurations

    Returns:
        Comprehensive deadline tracking with scheduled notifications and quick actions
    """
    try:
        logger.info("⏰ Processing deadline tracking request",
                   county=county_code, tracking_type=tracking_type)

        # Get county information
        county_info = get_county_calendar(county_code)
        if not county_info:
            return {
                "success": False,
                "error": f"County '{county_code}' not supported",
                "suggestions": [f"Supported counties: {', '.join(COUNTY_TAX_CALENDARS.keys())}"]
            }

        # Parse current date
        if current_date:
            current_date_obj = parse_date_safely(current_date)
            if not current_date_obj:
                return {
                    "success": False,
                    "error": "Invalid date format. Use YYYY-MM-DD format.",
                    "suggestions": ["Example: 2024-03-15"]
                }
        else:
            current_date_obj = date.today()

        # Get deadlines
        all_deadlines = get_current_deadlines(county_code, current_date_obj)

        # Filter deadlines by tracking type
        if tracking_type != "all":
            filtered_deadlines = [
                d for d in all_deadlines
                if d.get("category", "").lower() == tracking_type.lower()
            ]
        else:
            filtered_deadlines = all_deadlines

        # Separate upcoming and overdue deadlines
        upcoming_deadlines = []
        overdue_deadlines = []

        for deadline in filtered_deadlines:
            days_until = deadline.get("days_until_deadline", 0)

            # Calculate urgency score
            deadline["urgency_score"] = calculate_urgency_score(
                days_until,
                deadline.get("category", "other")
            )

            # Add payment calculation if it's a payment deadline
            if deadline.get("category") == "payment" and "tax_amount" in deadline:
                payment_info = calculate_payment_amount(
                    deadline["tax_amount"],
                    current_date_obj,
                    county_code
                )
                deadline["payment_info"] = payment_info

            if days_until < 0:
                overdue_deadlines.append(deadline)
            else:
                upcoming_deadlines.append(deadline)

        # Sort deadlines by urgency score (highest first)
        upcoming_deadlines.sort(key=lambda x: x.get("urgency_score", 0), reverse=True)
        overdue_deadlines.sort(key=lambda x: abs(x.get("days_until_deadline", 0)), reverse=True)

        # Set default notification preferences
        default_prefs = {
            "method": "email",
            "advance_notice": [30, 14, 7, 3, 1],
            "categories": ["all"]
        }
        notification_prefs = {**default_prefs, **(notification_preferences or {})}

        # Schedule notifications
        notifications_scheduled = schedule_notifications(upcoming_deadlines, notification_prefs)

        # Add custom reminders if provided
        if custom_reminders:
            for reminder in custom_reminders:
                notifications_scheduled.append({
                    "notification_date": reminder.get("date", ""),
                    "deadline_name": reminder.get("title", "Custom Reminder"),
                    "deadline_date": reminder.get("target_date", ""),
                    "days_in_advance": 0,
                    "method": reminder.get("method", notification_prefs["method"]),
                    "urgency": reminder.get("urgency", "medium"),
                    "message_template": reminder.get("message", "Custom reminder"),
                    "custom": True
                })

        # Generate quick actions
        quick_actions = generate_quick_actions(upcoming_deadlines, county_info)

        # Add business property deadlines if applicable
        if property_type == "commercial" or property_type == "industrial":
            business_deadlines = []
            for deadline_name, deadline_date in BUSINESS_PROPERTY_DEADLINES.items():
                if isinstance(deadline_date, str) and deadline_date.startswith("2024"):
                    deadline_date_obj = parse_date_safely(deadline_date)
                    if deadline_date_obj:
                        days_until = (deadline_date_obj - current_date_obj).days
                        if -30 <= days_until <= 365:
                            business_deadlines.append({
                                "deadline_name": deadline_name.replace("_", " ").title(),
                                "deadline_date": deadline_date,
                                "days_until_deadline": days_until,
                                "urgency": "high" if days_until <= 7 else "medium",
                                "category": "business",
                                "description": f"Business property {deadline_name.replace('_', ' ')}"
                            })

            upcoming_deadlines.extend(business_deadlines)

        return {
            "success": True,
            "county_info": {
                "county_name": county_info["county_name"],
                "appraisal_district": county_info["appraisal_district"],
                "contact": county_info["contact"],
                "payment_options": county_info.get("payment_options", {}),
                "special_provisions": county_info.get("special_provisions", {})
            },
            "upcoming_deadlines": upcoming_deadlines,
            "overdue_deadlines": overdue_deadlines,
            "notifications_scheduled": notifications_scheduled,
            "quick_actions": quick_actions,
            "tracking_summary": {
                "total_deadlines": len(filtered_deadlines),
                "upcoming_count": len(upcoming_deadlines),
                "overdue_count": len(overdue_deadlines),
                "high_urgency_count": len([d for d in upcoming_deadlines if d.get("urgency") == "high"]),
                "notifications_count": len(notifications_scheduled),
                "tracking_type": tracking_type,
                "current_date": current_date_obj.isoformat()
            },
            "special_circumstances": {
                "disaster_extensions_available": county_info.get("special_provisions", {}).get("disaster_extensions", False),
                "online_services_available": county_info.get("special_provisions", {}).get("online_protest", False),
                "special_assistance": list(county_info.get("special_provisions", {}).keys())
            }
        }

    except Exception as e:
        logger.error("❌ Deadline tracking failed",
                    error=str(e), county=county_code)

        return {
            "success": False,
            "error": f"Deadline tracking failed: {str(e)}",
            "suggestions": [
                "Verify county code is valid (harris, dallas, tarrant, travis, bexar, collin)",
                "Check date format is YYYY-MM-DD",
                "Ensure tracking_type is valid (all, payment, appeal, exemption, assessment)",
                "Contact support if the problem persists"
            ]
        }

# Additional utility functions

async def get_county_comparison(counties: List[str], deadline_type: str = "all") -> Dict[str, Any]:
    """Compare deadlines across multiple counties"""
    comparison = {}

    for county in counties:
        county_deadlines = await deadline_tracking_tool(
            county_code=county,
            tracking_type=deadline_type
        )

        if county_deadlines.get("success"):
            comparison[county] = {
                "county_name": county_deadlines["county_info"]["county_name"],
                "upcoming_count": county_deadlines["tracking_summary"]["upcoming_count"],
                "high_urgency_count": county_deadlines["tracking_summary"]["high_urgency_count"],
                "contact_phone": county_deadlines["county_info"]["contact"].get("phone", ""),
                "online_services": county_deadlines["county_info"]["contact"].get("website", "")
            }

    return comparison

def calculate_penalty_savings(
    tax_amount: int,
    current_date: date,
    target_payment_date: date,
    county_code: str
) -> Dict[str, Any]:
    """Calculate potential penalty savings by paying early"""
    current_payment = calculate_payment_amount(tax_amount, current_date, county_code)
    target_payment = calculate_payment_amount(tax_amount, target_payment_date, county_code)

    savings = current_payment.get("total_amount", 0) - target_payment.get("total_amount", 0)

    return {
        "current_payment_amount": current_payment.get("total_amount", 0),
        "target_payment_amount": target_payment.get("total_amount", 0),
        "potential_savings": savings,
        "days_difference": (target_payment_date - current_date).days,
        "recommendation": "Pay early to save money" if savings > 0 else "No savings available"
    }

def get_deadline_calendar_view(county_code: str, year: int = 2024) -> Dict[str, List[Dict[str, Any]]]:
    """Get calendar view of all deadlines by month"""
    county_info = get_county_calendar(county_code)
    if not county_info:
        return {}

    calendar_view = {}
    key_dates = county_info["key_dates"]

    for deadline_name, deadline_date_str in key_dates.items():
        try:
            deadline_date = datetime.strptime(deadline_date_str, "%Y-%m-%d").date()
            month_name = deadline_date.strftime("%B %Y")

            if month_name not in calendar_view:
                calendar_view[month_name] = []

            calendar_view[month_name].append({
                "date": deadline_date.strftime("%Y-%m-%d"),
                "day": deadline_date.day,
                "deadline_name": deadline_name.replace("_", " ").title(),
                "category": categorize_deadline(deadline_name),
                "description": get_deadline_description(deadline_name)
            })

        except ValueError:
            continue

    # Sort deadlines within each month
    for month in calendar_view:
        calendar_view[month].sort(key=lambda x: x["day"])

    return calendar_view