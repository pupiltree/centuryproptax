"""
Intelligent Date Parsing Service for Krsnaa Diagnostics
Handles natural language dates, business hours, and booking constraints.
"""

import re
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, Tuple, List
import structlog

logger = structlog.get_logger()

class DateIntelligenceService:
    """Service for parsing natural language dates and managing booking constraints."""
    
    def __init__(self):
        self.logger = logger.bind(component="date_intelligence")
        
        # Business configuration
        self.business_hours = {
            "weekdays": {"start": "06:00", "end": "21:00"},  # 6 AM to 9 PM
            "weekends": {"start": "08:00", "end": "18:00"}   # 8 AM to 6 PM
        }
        
        # Time slot mappings
        self.time_slots = {
            "early_morning": {"start": "06:00", "end": "09:00", "display": "Early Morning (6-9 AM)"},
            "morning": {"start": "09:00", "end": "12:00", "display": "Morning (9 AM-12 PM)"},
            "afternoon": {"start": "12:00", "end": "17:00", "display": "Afternoon (12-5 PM)"},
            "evening": {"start": "17:00", "end": "21:00", "display": "Evening (5-9 PM)"}
        }
        
        # Day name mappings
        self.day_names = {
            "monday": 0, "mon": 0,
            "tuesday": 1, "tue": 1, "tues": 1,
            "wednesday": 2, "wed": 2,
            "thursday": 3, "thu": 3, "thurs": 3,
            "friday": 4, "fri": 4,
            "saturday": 5, "sat": 5,
            "sunday": 6, "sun": 6
        }
        
    def get_current_time_info(self) -> Dict[str, Any]:
        """Get current date/time information for context."""
        now = datetime.now()
        today = now.date()
        
        return {
            "current_datetime": now,
            "current_date": today,
            "current_time": now.strftime("%H:%M"),
            "day_of_week": now.strftime("%A"),
            "formatted_date": today.strftime("%B %d, %Y"),
            "is_business_hours": self._is_business_hours(now),
            "next_business_day": self._get_next_business_day(today)
        }
    
    def parse_date_intelligently(self, date_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Parse natural language date input into structured date information.
        
        Args:
            date_input: User's date input (e.g., "tomorrow", "next Monday", "2025-01-15")
            context: Optional context (current booking info, user preferences)
            
        Returns:
            Parsed date information with validation
        """
        try:
            if not date_input or not date_input.strip():
                return self._create_error_response("No date provided")
            
            date_input = date_input.strip().lower()
            current_info = self.get_current_time_info()
            
            self.logger.info(f"Parsing date input: '{date_input}' at {current_info['current_datetime']}")
            
            # Try different parsing methods
            parsed_date = None
            method_used = None
            
            # Method 1: Relative dates (today, tomorrow, etc.)
            if not parsed_date:
                parsed_date, method_used = self._parse_relative_dates(date_input, current_info)
            
            # Method 2: Named days (Monday, Tuesday, etc.)
            if not parsed_date:
                parsed_date, method_used = self._parse_named_days(date_input, current_info)
            
            # Method 3: Specific date patterns (DD/MM, DD-MM, etc.)
            if not parsed_date:
                parsed_date, method_used = self._parse_specific_dates(date_input, current_info)
            
            # Method 4: Relative weeks (next week, this week, etc.)
            if not parsed_date:
                parsed_date, method_used = self._parse_relative_weeks(date_input, current_info)
            
            if not parsed_date:
                return self._create_error_response(f"Could not understand date '{date_input}'. Try 'tomorrow', 'Monday', or 'DD/MM/YYYY'")
            
            # Validate the parsed date
            validation = self._validate_booking_date(parsed_date, current_info)
            
            return {
                "success": True,
                "parsed_date": parsed_date,
                "formatted_date": parsed_date.strftime("%Y-%m-%d"),
                "display_date": parsed_date.strftime("%A, %B %d, %Y"),
                "method_used": method_used,
                "is_valid": validation["is_valid"],
                "validation_message": validation["message"],
                "days_from_now": (parsed_date - current_info["current_date"]).days,
                "is_weekend": parsed_date.weekday() >= 5,
                "business_day": self._is_business_day(parsed_date),
                "available_time_slots": self._get_available_time_slots(parsed_date),
                "current_info": current_info
            }
            
        except Exception as e:
            self.logger.error(f"Date parsing error: {e}")
            return self._create_error_response(f"Date parsing failed: {str(e)}")
    
    def _parse_relative_dates(self, date_input: str, current_info: Dict) -> Tuple[Optional[date], Optional[str]]:
        """Parse relative dates like 'today', 'tomorrow', 'day after tomorrow'."""
        today = current_info["current_date"]
        
        # Order matters - longer patterns first to avoid partial matching
        patterns = [
            (r'\bday after tomorrow\b', (today + timedelta(days=2), "day_after_tomorrow")),
            (r'\bin (\d+) days?\b', lambda m: (today + timedelta(days=int(m.group(1))), f"in_{m.group(1)}_days")),
            (r'\bafter (\d+) days?\b', lambda m: (today + timedelta(days=int(m.group(1))), f"after_{m.group(1)}_days")),
            (r'\btomorrow\b', (today + timedelta(days=1), "tomorrow")),
            (r'\btoday\b', (today, "today")),
            (r'\bnext day\b', (today + timedelta(days=1), "next_day")),
        ]
        
        for pattern, result in patterns:
            match = re.search(pattern, date_input)
            if match:
                if callable(result):
                    return result(match)
                else:
                    return result
        
        return None, None
    
    def _parse_named_days(self, date_input: str, current_info: Dict) -> Tuple[Optional[date], Optional[str]]:
        """Parse named days like 'Monday', 'next Tuesday', 'this Friday'."""
        today = current_info["current_date"]
        current_weekday = today.weekday()
        
        # Look for day names
        for day_name, target_weekday in self.day_names.items():
            if day_name in date_input:
                # Determine which occurrence of the day
                if "next" in date_input:
                    # Next occurrence (always next week)
                    days_ahead = target_weekday - current_weekday + 7
                    target_date = today + timedelta(days=days_ahead)
                    return target_date, f"next_{day_name}"
                
                elif "this" in date_input:
                    # This week's occurrence
                    if target_weekday > current_weekday:
                        # Later this week
                        days_ahead = target_weekday - current_weekday
                        target_date = today + timedelta(days=days_ahead)
                        return target_date, f"this_{day_name}"
                    else:
                        # Already passed, assume next week
                        days_ahead = target_weekday - current_weekday + 7
                        target_date = today + timedelta(days=days_ahead)
                        return target_date, f"next_{day_name}"
                
                else:
                    # Just "Monday" - assume next occurrence
                    if target_weekday > current_weekday:
                        # Later this week
                        days_ahead = target_weekday - current_weekday
                        target_date = today + timedelta(days=days_ahead)
                        return target_date, f"coming_{day_name}"
                    else:
                        # Next week
                        days_ahead = target_weekday - current_weekday + 7
                        target_date = today + timedelta(days=days_ahead)
                        return target_date, f"next_{day_name}"
        
        return None, None
    
    def _parse_specific_dates(self, date_input: str, current_info: Dict) -> Tuple[Optional[date], Optional[str]]:
        """Parse specific date formats like DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD."""
        current_year = current_info["current_date"].year
        
        # Pattern 1: DD/MM/YYYY or DD/MM
        match = re.search(r'\b(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{4}))?\b', date_input)
        if match:
            day, month, year = match.groups()
            year = int(year) if year else current_year
            
            try:
                target_date = date(year, int(month), int(day))
                return target_date, f"specific_date_dmy"
            except ValueError:
                pass
        
        # Pattern 2: YYYY-MM-DD (ISO format)
        match = re.search(r'\b(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})\b', date_input)
        if match:
            year, month, day = match.groups()
            try:
                target_date = date(int(year), int(month), int(day))
                return target_date, f"specific_date_ymd"
            except ValueError:
                pass
        
        # Pattern 3: Month Day, Year (e.g., "January 15, 2025")
        month_names = {
            "january": 1, "jan": 1, "february": 2, "feb": 2,
            "march": 3, "mar": 3, "april": 4, "apr": 4,
            "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
            "august": 8, "aug": 8, "september": 9, "sep": 9,
            "october": 10, "oct": 10, "november": 11, "nov": 11,
            "december": 12, "dec": 12
        }
        
        for month_name, month_num in month_names.items():
            pattern = rf'\b{month_name}\.?\s+(\d{{1,2}})(?:,?\s+(\d{{4}}))?\b'
            match = re.search(pattern, date_input)
            if match:
                day, year = match.groups()
                year = int(year) if year else current_year
                try:
                    target_date = date(year, month_num, int(day))
                    return target_date, f"specific_date_month_name"
                except ValueError:
                    pass
        
        return None, None
    
    def _parse_relative_weeks(self, date_input: str, current_info: Dict) -> Tuple[Optional[date], Optional[str]]:
        """Parse relative week references like 'next week', 'this week'."""
        today = current_info["current_date"]
        
        if "next week" in date_input:
            # Default to Monday of next week
            days_until_monday = 7 - today.weekday()
            target_date = today + timedelta(days=days_until_monday)
            return target_date, "next_week_monday"
        
        elif "this week" in date_input:
            # Default to tomorrow if still this week, else Monday
            tomorrow = today + timedelta(days=1)
            if tomorrow.weekday() < 6:  # Still this week
                return tomorrow, "this_week_tomorrow"
            else:
                # Weekend, suggest Monday
                days_until_monday = 7 - today.weekday()
                target_date = today + timedelta(days=days_until_monday)
                return target_date, "next_week_monday"
        
        return None, None
    
    def _validate_booking_date(self, target_date: date, current_info: Dict) -> Dict[str, Any]:
        """Validate if a date is suitable for booking."""
        today = current_info["current_date"]
        days_diff = (target_date - today).days
        
        # Check if date is in the past
        if target_date < today:
            return {
                "is_valid": False,
                "message": f"Cannot book for past dates. Please choose a future date."
            }
        
        # Check if date is today and past business hours
        if target_date == today:
            current_time = current_info["current_datetime"].time()
            if not current_info["is_business_hours"]:
                return {
                    "is_valid": False,
                    "message": "Too late to book for today. Please choose tomorrow or later."
                }
        
        # Check if date is too far in the future (90 days limit)
        if days_diff > 90:
            return {
                "is_valid": False,
                "message": "Cannot book more than 90 days in advance. Please choose an earlier date."
            }
        
        # Check if it's a business day (weekday)
        if target_date.weekday() >= 5:  # Weekend
            next_monday = target_date + timedelta(days=7-target_date.weekday())
            return {
                "is_valid": True,
                "message": f"Weekend booking available with limited slots. Consider {next_monday.strftime('%A, %B %d')} for more options.",
                "warning": "Limited weekend availability"
            }
        
        return {
            "is_valid": True,
            "message": f"✅ {target_date.strftime('%A, %B %d')} is available for booking."
        }
    
    def _get_available_time_slots(self, target_date: date) -> List[Dict[str, Any]]:
        """Get available time slots for a given date."""
        is_weekend = target_date.weekday() >= 5
        
        if is_weekend:
            # Weekend slots (reduced)
            return [
                {"slot": "morning", "time": "9:00-12:00", "available": True, "popular": True},
                {"slot": "afternoon", "time": "12:00-15:00", "available": True, "popular": False}
            ]
        else:
            # Weekday slots (full)
            return [
                {"slot": "early_morning", "time": "6:00-9:00", "available": True, "popular": False},
                {"slot": "morning", "time": "9:00-12:00", "available": True, "popular": True},
                {"slot": "afternoon", "time": "12:00-17:00", "available": True, "popular": True},
                {"slot": "evening", "time": "17:00-21:00", "available": True, "popular": False}
            ]
    
    def _is_business_hours(self, dt: datetime) -> bool:
        """Check if datetime is within business hours."""
        time_str = dt.strftime("%H:%M")
        is_weekend = dt.weekday() >= 5
        
        if is_weekend:
            start_time = self.business_hours["weekends"]["start"]
            end_time = self.business_hours["weekends"]["end"]
        else:
            start_time = self.business_hours["weekdays"]["start"]
            end_time = self.business_hours["weekdays"]["end"]
        
        return start_time <= time_str <= end_time
    
    def _is_business_day(self, target_date: date) -> bool:
        """Check if date is a business day."""
        return target_date.weekday() < 5
    
    def _get_next_business_day(self, from_date: date) -> date:
        """Get the next business day from a given date."""
        next_day = from_date + timedelta(days=1)
        while next_day.weekday() >= 5:  # Skip weekends
            next_day += timedelta(days=1)
        return next_day
    
    def _create_error_response(self, message: str) -> Dict[str, Any]:
        """Create standardized error response."""
        current_info = self.get_current_time_info()
        tomorrow = current_info["current_date"] + timedelta(days=1)
        
        return {
            "success": False,
            "error": message,
            "suggestions": [
                f"Try 'tomorrow' ({tomorrow.strftime('%A, %B %d')})",
                "Try 'Monday', 'Tuesday', etc.",
                "Try 'DD/MM/YYYY' format",
                "Try 'next week'"
            ],
            "current_info": current_info
        }


# Global service instance
date_intelligence = DateIntelligenceService()


# Convenience functions for tools
def parse_date_intelligently(date_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Parse date input intelligently with business logic."""
    return date_intelligence.parse_date_intelligently(date_input, context)


def get_current_time_info() -> Dict[str, Any]:
    """Get current time information for booking context."""
    return date_intelligence.get_current_time_info()


def validate_booking_constraints(target_date: date, current_bookings: Optional[List] = None) -> Dict[str, Any]:
    """Validate booking constraints including agent availability."""
    current_info = get_current_time_info()
    validation = date_intelligence._validate_booking_date(target_date, current_info)
    
    # Add agent availability check
    # Since business has multiple agents, multiple bookings are allowed on same day
    agent_capacity = 10  # Assume 10 concurrent bookings per day across all agents
    current_booking_count = len(current_bookings) if current_bookings else 0
    
    if current_booking_count >= agent_capacity:
        validation.update({
            "is_valid": False,
            "message": f"Date is fully booked ({current_booking_count}/{agent_capacity} slots filled). Please choose another date.",
            "alternative_dates": [
                (target_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                (target_date + timedelta(days=2)).strftime("%Y-%m-%d")
            ]
        })
    else:
        available_slots = agent_capacity - current_booking_count
        validation.update({
            "agent_availability": {
                "available_slots": available_slots,
                "total_capacity": agent_capacity,
                "multiple_bookings_allowed": True,
                "message": f"✅ {available_slots} booking slots available for this date"
            }
        })
    
    return validation