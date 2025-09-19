"""
Natural language date parser for healthcare booking system
"""

from datetime import datetime, timedelta
import re
from typing import Optional

def parse_natural_date(date_input: str) -> Optional[str]:
    """
    Parse natural language date input and return YYYY-MM-DD format.
    
    Supports formats like:
    - "today", "tomorrow", "day after tomorrow"
    - "next Monday", "this Friday"  
    - "September 7", "Sep 7th", "7 Sep"
    - "2025-09-07", "09/07/2025", "07-09-2025"
    - "in 2 days", "after 3 days"
    
    Args:
        date_input: Natural language date string
        
    Returns:
        Date in YYYY-MM-DD format or None if parsing fails
    """
    if not date_input or not isinstance(date_input, str):
        return None
        
    date_input = date_input.lower().strip()
    today = datetime.now()
    
    # Handle relative dates
    if date_input in ["today"]:
        return today.strftime("%Y-%m-%d")
    elif date_input in ["tomorrow"]:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_input in ["day after tomorrow", "day after"]:
        return (today + timedelta(days=2)).strftime("%Y-%m-%d")
    
    # Handle "in X days" / "after X days"
    days_pattern = re.search(r'(?:in|after)\s+(\d+)\s+days?', date_input)
    if days_pattern:
        days = int(days_pattern.group(1))
        return (today + timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Handle weekdays ("next Monday", "this Friday")
    weekdays = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6,
        'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
    }
    
    for day_name, day_num in weekdays.items():
        if day_name in date_input:
            current_weekday = today.weekday()
            if "next" in date_input:
                days_ahead = (day_num - current_weekday + 7) % 7
                if days_ahead == 0:  # If today is the same weekday, go to next week
                    days_ahead = 7
            else:  # "this" or no prefix
                days_ahead = (day_num - current_weekday) % 7
                if days_ahead == 0 and "this" not in date_input:
                    days_ahead = 7  # Default to next week if no prefix
            
            target_date = today + timedelta(days=days_ahead)
            return target_date.strftime("%Y-%m-%d")
    
    # Handle month names with dates
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8,
        'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    # Pattern: "September 7", "Sep 7th", "7 September"
    for month_name, month_num in months.items():
        if month_name in date_input:
            # Extract day number
            day_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?', date_input)
            if day_match:
                day = int(day_match.group(1))
                year = today.year
                
                # If the date has passed this year, assume next year
                try:
                    target_date = datetime(year, month_num, day)
                    if target_date < today:
                        target_date = datetime(year + 1, month_num, day)
                    return target_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue
    
    # Handle standard formats
    standard_patterns = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY or DD/MM/YYYY  
        r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
    ]
    
    for pattern in standard_patterns:
        match = re.search(pattern, date_input)
        if match:
            try:
                if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD
                    year, month, day = map(int, match.groups())
                else:  # Assume DD/MM/YYYY or DD-MM-YYYY for others
                    day, month, year = map(int, match.groups())
                
                target_date = datetime(year, month, day)
                return target_date.strftime("%Y-%m-%d")
            except ValueError:
                continue
    
    # If all parsing fails, return None
    return None


def format_date_user_friendly(date_str: str) -> str:
    """
    Convert YYYY-MM-DD date to user-friendly format.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        User-friendly date format like "September 7, 2025"
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%B %d, %Y")
    except ValueError:
        return date_str


# Test the parser with common inputs
if __name__ == "__main__":
    test_inputs = [
        "today", "tomorrow", "next Friday", "September 7", 
        "2025-09-07", "in 3 days", "next Monday"
    ]
    
    print("Testing natural date parser:")
    for test_input in test_inputs:
        result = parse_natural_date(test_input)
        friendly = format_date_user_friendly(result) if result else "Could not parse"
        print(f"'{test_input}' → {result} ({friendly})")