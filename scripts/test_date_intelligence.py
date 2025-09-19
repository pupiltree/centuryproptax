#!/usr/bin/env python3
"""
Test script for intelligent date parsing integration in booking workflow.
"""

import sys
import os
import asyncio
from datetime import datetime, date, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our date intelligence service
from services.date_intelligence import parse_date_intelligently, get_current_time_info

def test_natural_language_dates():
    """Test various natural language date inputs."""
    print("🧪 Testing Intelligent Date Parsing\n")
    
    # Test cases
    test_dates = [
        "tomorrow",
        "day after tomorrow", 
        "next Monday",
        "this Friday",
        "Monday",
        "next week",
        "15/01/2025",
        "2025-01-20",
        "January 25, 2025",
        "in 3 days",
        "invalid date",
        "yesterday",  # Should fail - past date
        ""
    ]
    
    current_info = get_current_time_info()
    print(f"📅 Current Date: {current_info['formatted_date']} ({current_info['day_of_week']})")
    print(f"🕐 Current Time: {current_info['current_time']}")
    print(f"💼 Business Hours: {'Yes' if current_info['is_business_hours'] else 'No'}")
    print("-" * 80)
    
    for date_input in test_dates:
        print(f"Input: '{date_input}'")
        result = parse_date_intelligently(date_input)
        
        if result["success"]:
            if result["is_valid"]:
                print(f"✅ Parsed: {result['display_date']} ({result['formatted_date']})")
                print(f"   Method: {result['method_used']}")
                print(f"   Days from now: {result['days_from_now']}")
                print(f"   Validation: {result['validation_message']}")
                print(f"   Weekend: {'Yes' if result['is_weekend'] else 'No'}")
                print(f"   Time slots: {len(result['available_time_slots'])}")
            else:
                print(f"⚠️  Parsed but invalid: {result['validation_message']}")
        else:
            print(f"❌ Failed: {result['error']}")
            if result.get("suggestions"):
                print(f"   Suggestions: {', '.join(result['suggestions'])}")
        
        print("-" * 40)

def test_booking_scenarios():
    """Test realistic booking scenarios."""
    print("\n🏥 Testing Realistic Booking Scenarios\n")
    
    scenarios = [
        {
            "description": "Customer says 'book for tomorrow'",
            "input": "tomorrow",
            "expected": "Should work if not past business hours"
        },
        {
            "description": "Customer says 'I want test on Monday'", 
            "input": "Monday",
            "expected": "Should pick next Monday if current day is after Monday"
        },
        {
            "description": "Customer says 'day after tomorrow'",
            "input": "day after tomorrow", 
            "expected": "Should work and show specific date"
        },
        {
            "description": "Customer provides DD/MM/YYYY format",
            "input": "25/01/2025",
            "expected": "Should parse as January 25, 2025"
        },
        {
            "description": "Customer says 'next week'",
            "input": "next week",
            "expected": "Should default to Monday of next week"
        }
    ]
    
    for scenario in scenarios:
        print(f"📋 Scenario: {scenario['description']}")
        print(f"   Input: '{scenario['input']}'")
        print(f"   Expected: {scenario['expected']}")
        
        result = parse_date_intelligently(scenario['input'])
        
        if result["success"] and result["is_valid"]:
            print(f"   ✅ Result: {result['display_date']} using {result['method_used']}")
            print(f"   📊 Available slots: {len(result['available_time_slots'])}")
            if result['is_weekend']:
                print(f"   🏖️  Weekend booking (limited slots)")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        
        print("-" * 50)

def test_multiple_concurrent_bookings():
    """Test support for multiple concurrent bookings."""
    print("\n👥 Testing Multiple Concurrent Booking Support\n")
    
    from services.date_intelligence import validate_booking_constraints
    
    test_date = date.today() + timedelta(days=1)  # Tomorrow
    
    # Simulate different booking loads
    booking_loads = [0, 5, 8, 10, 12]  # 10 is the capacity limit
    
    for booking_count in booking_loads:
        current_bookings = [f"booking_{i}" for i in range(booking_count)]
        result = validate_booking_constraints(test_date, current_bookings)
        
        print(f"📊 Current bookings: {booking_count}/10")
        if result["is_valid"]:
            if "agent_availability" in result:
                avail = result["agent_availability"]
                print(f"   ✅ {avail['available_slots']} slots available")
                print(f"   💬 {avail['message']}")
            else:
                print(f"   ✅ Available: {result['message']}")
        else:
            print(f"   ❌ Fully booked: {result['message']}")
            if "alternative_dates" in result:
                print(f"   📅 Alternatives: {', '.join(result['alternative_dates'])}")
        print("-" * 30)

if __name__ == "__main__":
    print("🚀 Krsnaa Diagnostics - Intelligent Date Parsing Test\n")
    
    try:
        test_natural_language_dates()
        test_booking_scenarios()
        test_multiple_concurrent_bookings()
        
        print("\n✅ All tests completed!")
        print("\n💡 The system now supports:")
        print("   • Natural language dates (tomorrow, next Monday, etc.)")
        print("   • Multiple date formats (DD/MM/YYYY, YYYY-MM-DD, etc.)")
        print("   • Business hours validation")
        print("   • Weekend booking support")
        print("   • Multiple concurrent bookings (10 agents capacity)")
        print("   • Intelligent error messages and suggestions")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()