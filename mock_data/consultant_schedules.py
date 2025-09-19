"""
Consultant Schedules and Availability Data for Property Tax Consultations

Mock scheduling data including consultant profiles, availability patterns,
appointment types, and time zone handling for Texas regions.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, time, timedelta
import random
from dataclasses import dataclass


# Consultant profiles
CONSULTANT_PROFILES = {
    "consultant_001": {
        "name": "Sarah Johnson",
        "title": "Senior Property Tax Consultant",
        "specialties": ["residential_appeals", "commercial_properties", "exemptions"],
        "certifications": ["Texas Certified Appraiser", "Property Tax Professional"],
        "experience_years": 12,
        "success_rate": 0.78,
        "counties_served": ["harris", "dallas", "tarrant"],
        "languages": ["english", "spanish"],
        "contact": {
            "email": "sarah.johnson@centuryproptax.com",
            "phone": "(713) 555-0101",
            "extension": "101"
        },
        "availability": {
            "timezone": "America/Chicago",
            "working_hours": {
                "monday": {"start": "08:00", "end": "17:00"},
                "tuesday": {"start": "08:00", "end": "17:00"},
                "wednesday": {"start": "08:00", "end": "17:00"},
                "thursday": {"start": "08:00", "end": "17:00"},
                "friday": {"start": "08:00", "end": "16:00"},
                "saturday": {"start": "09:00", "end": "13:00"},
                "sunday": {"start": None, "end": None}
            },
            "lunch_break": {"start": "12:00", "end": "13:00"},
            "appointment_duration": {
                "initial_consultation": 60,
                "follow_up": 30,
                "document_review": 45,
                "hearing_prep": 90
            }
        },
        "preferences": {
            "max_appointments_per_day": 8,
            "buffer_time_minutes": 15,
            "prefers_in_person": True,
            "video_call_capable": True,
            "travel_radius_miles": 25
        }
    },
    "consultant_002": {
        "name": "Michael Chen",
        "title": "Commercial Property Tax Specialist",
        "specialties": ["commercial_appeals", "industrial_properties", "business_personal_property"],
        "certifications": ["Texas Certified Appraiser", "MAI Designation"],
        "experience_years": 15,
        "success_rate": 0.82,
        "counties_served": ["harris", "travis", "bexar"],
        "languages": ["english", "mandarin"],
        "contact": {
            "email": "michael.chen@centuryproptax.com",
            "phone": "(713) 555-0102",
            "extension": "102"
        },
        "availability": {
            "timezone": "America/Chicago",
            "working_hours": {
                "monday": {"start": "09:00", "end": "18:00"},
                "tuesday": {"start": "09:00", "end": "18:00"},
                "wednesday": {"start": "09:00", "end": "18:00"},
                "thursday": {"start": "09:00", "end": "18:00"},
                "friday": {"start": "09:00", "end": "17:00"},
                "saturday": {"start": None, "end": None},
                "sunday": {"start": None, "end": None}
            },
            "lunch_break": {"start": "12:30", "end": "13:30"},
            "appointment_duration": {
                "initial_consultation": 90,
                "follow_up": 45,
                "document_review": 60,
                "hearing_prep": 120
            }
        },
        "preferences": {
            "max_appointments_per_day": 6,
            "buffer_time_minutes": 30,
            "prefers_in_person": True,
            "video_call_capable": True,
            "travel_radius_miles": 50
        }
    },
    "consultant_003": {
        "name": "Lisa Rodriguez",
        "title": "Property Tax Consultant",
        "specialties": ["residential_appeals", "exemptions", "agricultural_properties"],
        "certifications": ["Property Tax Professional", "Agricultural Appraiser"],
        "experience_years": 8,
        "success_rate": 0.75,
        "counties_served": ["dallas", "collin", "tarrant"],
        "languages": ["english", "spanish"],
        "contact": {
            "email": "lisa.rodriguez@centuryproptax.com",
            "phone": "(214) 555-0103",
            "extension": "103"
        },
        "availability": {
            "timezone": "America/Chicago",
            "working_hours": {
                "monday": {"start": "08:30", "end": "17:30"},
                "tuesday": {"start": "08:30", "end": "17:30"},
                "wednesday": {"start": "08:30", "end": "17:30"},
                "thursday": {"start": "08:30", "end": "17:30"},
                "friday": {"start": "08:30", "end": "16:30"},
                "saturday": {"start": "10:00", "end": "14:00"},
                "sunday": {"start": None, "end": None}
            },
            "lunch_break": {"start": "12:00", "end": "13:00"},
            "appointment_duration": {
                "initial_consultation": 60,
                "follow_up": 30,
                "document_review": 45,
                "hearing_prep": 75
            }
        },
        "preferences": {
            "max_appointments_per_day": 9,
            "buffer_time_minutes": 10,
            "prefers_in_person": False,
            "video_call_capable": True,
            "travel_radius_miles": 30
        }
    },
    "consultant_004": {
        "name": "David Thompson",
        "title": "Senior Tax Strategist",
        "specialties": ["complex_appeals", "high_value_properties", "legal_representation"],
        "certifications": ["Texas Attorney", "Property Tax Professional", "ASA Designation"],
        "experience_years": 20,
        "success_rate": 0.85,
        "counties_served": ["harris", "dallas", "travis", "tarrant", "bexar", "collin"],
        "languages": ["english"],
        "contact": {
            "email": "david.thompson@centuryproptax.com",
            "phone": "(713) 555-0104",
            "extension": "104"
        },
        "availability": {
            "timezone": "America/Chicago",
            "working_hours": {
                "monday": {"start": "07:30", "end": "18:30"},
                "tuesday": {"start": "07:30", "end": "18:30"},
                "wednesday": {"start": "07:30", "end": "18:30"},
                "thursday": {"start": "07:30", "end": "18:30"},
                "friday": {"start": "07:30", "end": "17:30"},
                "saturday": {"start": "08:00", "end": "12:00"},
                "sunday": {"start": None, "end": None}
            },
            "lunch_break": {"start": "12:00", "end": "13:00"},
            "appointment_duration": {
                "initial_consultation": 90,
                "follow_up": 60,
                "document_review": 75,
                "hearing_prep": 150
            }
        },
        "preferences": {
            "max_appointments_per_day": 5,
            "buffer_time_minutes": 30,
            "prefers_in_person": True,
            "video_call_capable": True,
            "travel_radius_miles": 100
        }
    }
}

# Appointment types and configurations
APPOINTMENT_TYPES = {
    "initial_consultation": {
        "name": "Initial Property Tax Consultation",
        "description": "Comprehensive review of property assessment and appeal potential",
        "duration_minutes": 60,
        "price": 0,  # Free initial consultation
        "preparation_required": [
            "Property tax statement",
            "Appraisal notice",
            "Recent comparable sales (if available)",
            "Property photos",
            "Recent repair/improvement receipts"
        ],
        "deliverables": [
            "Assessment analysis",
            "Appeal recommendation",
            "Timeline and next steps",
            "Fee estimate"
        ],
        "can_be_virtual": True,
        "requires_documents": True
    },
    "follow_up": {
        "name": "Follow-up Consultation",
        "description": "Status update and strategy refinement for ongoing appeals",
        "duration_minutes": 30,
        "price": 150,
        "preparation_required": [
            "Previous consultation notes",
            "Any new documentation",
            "County responses (if any)"
        ],
        "deliverables": [
            "Status update",
            "Adjusted strategy",
            "Next action items"
        ],
        "can_be_virtual": True,
        "requires_documents": False
    },
    "document_review": {
        "name": "Document Review Session",
        "description": "Detailed review of property tax documents and evidence",
        "duration_minutes": 45,
        "price": 200,
        "preparation_required": [
            "All property tax documents",
            "Evidence materials",
            "Comparable sales data"
        ],
        "deliverables": [
            "Document analysis",
            "Evidence assessment",
            "Recommendations for additional materials"
        ],
        "can_be_virtual": True,
        "requires_documents": True
    },
    "hearing_prep": {
        "name": "ARB Hearing Preparation",
        "description": "Preparation for Appraisal Review Board hearing",
        "duration_minutes": 90,
        "price": 350,
        "preparation_required": [
            "Complete case file",
            "Evidence package",
            "Hearing notice",
            "Witness information (if applicable)"
        ],
        "deliverables": [
            "Hearing strategy",
            "Presentation materials",
            "Practice session",
            "Day-of-hearing checklist"
        ],
        "can_be_virtual": False,
        "requires_documents": True
    },
    "emergency_consultation": {
        "name": "Emergency Consultation",
        "description": "Urgent consultation for approaching deadlines",
        "duration_minutes": 45,
        "price": 300,
        "preparation_required": [
            "Immediate deadline documentation",
            "Property tax statement",
            "Appraisal notice"
        ],
        "deliverables": [
            "Immediate action plan",
            "Deadline compliance strategy",
            "Emergency filing assistance"
        ],
        "can_be_virtual": True,
        "requires_documents": True,
        "priority_booking": True
    }
}

# Location options
OFFICE_LOCATIONS = {
    "houston_main": {
        "name": "Houston Main Office",
        "address": "1234 Main Street, Suite 500, Houston, TX 77002",
        "phone": "(713) 555-0100",
        "parking": "Validated parking available",
        "public_transit": "Metro Rail accessible",
        "counties_served": ["harris"],
        "amenities": ["conference_rooms", "document_scanning", "refreshments"],
        "accessibility": "ADA compliant"
    },
    "dallas_office": {
        "name": "Dallas Office",
        "address": "5678 Commerce Street, Suite 300, Dallas, TX 75201",
        "phone": "(214) 555-0200",
        "parking": "Free parking garage",
        "public_transit": "DART accessible",
        "counties_served": ["dallas", "collin"],
        "amenities": ["conference_rooms", "document_scanning"],
        "accessibility": "ADA compliant"
    },
    "austin_office": {
        "name": "Austin Office",
        "address": "9012 Congress Avenue, Suite 200, Austin, TX 78701",
        "phone": "(512) 555-0300",
        "parking": "Street parking and nearby lots",
        "public_transit": "CapMetro accessible",
        "counties_served": ["travis"],
        "amenities": ["conference_rooms", "refreshments"],
        "accessibility": "ADA compliant"
    },
    "client_location": {
        "name": "Client Location",
        "description": "Meeting at client's home or business",
        "requirements": "Suitable for consultation and document review",
        "additional_fee": 50,  # Travel fee
        "max_distance_miles": 50
    },
    "virtual_meeting": {
        "name": "Virtual Meeting",
        "description": "Video conference consultation",
        "platform": "Zoom, Teams, or client preference",
        "requirements": "Stable internet connection, camera, microphone",
        "document_sharing": "Secure document portal provided"
    }
}

# Time zone handling for Texas
TEXAS_TIMEZONES = {
    "central": {
        "timezone": "America/Chicago",
        "counties": ["harris", "dallas", "tarrant", "travis", "bexar", "collin"],
        "dst_aware": True
    },
    "mountain": {
        "timezone": "America/Denver",
        "counties": ["el_paso"],  # West Texas
        "dst_aware": True
    }
}

def generate_consultant_schedule(
    consultant_id: str,
    start_date: date,
    days: int = 30
) -> Dict[str, Any]:
    """Generate realistic consultant schedule with appointments and availability"""

    consultant = CONSULTANT_PROFILES.get(consultant_id)
    if not consultant:
        return {"error": "Consultant not found"}

    schedule = {}
    current_date = start_date

    for day in range(days):
        day_name = current_date.strftime("%A").lower()
        working_hours = consultant["availability"]["working_hours"].get(day_name)

        if working_hours and working_hours["start"]:
            # Generate daily schedule
            start_time = datetime.strptime(working_hours["start"], "%H:%M").time()
            end_time = datetime.strptime(working_hours["end"], "%H:%M").time()
            lunch_start = datetime.strptime(consultant["availability"]["lunch_break"]["start"], "%H:%M").time()
            lunch_end = datetime.strptime(consultant["availability"]["lunch_break"]["end"], "%H:%M").time()

            # Generate random appointments (60% booking rate)
            appointments = []
            blocked_times = []

            # Add lunch break
            blocked_times.append({
                "start_time": lunch_start.strftime("%H:%M"),
                "end_time": lunch_end.strftime("%H:%M"),
                "type": "lunch_break"
            })

            # Generate some random appointments
            if random.random() < 0.6:  # 60% chance of having appointments
                num_appointments = random.randint(1, min(4, consultant["preferences"]["max_appointments_per_day"]))

                for _ in range(num_appointments):
                    # Random appointment type
                    apt_type = random.choice(list(APPOINTMENT_TYPES.keys()))
                    duration = APPOINTMENT_TYPES[apt_type]["duration_minutes"]

                    # Find available time slot
                    attempts = 0
                    while attempts < 10:  # Prevent infinite loop
                        # Random start time during working hours
                        work_start_minutes = start_time.hour * 60 + start_time.minute
                        work_end_minutes = end_time.hour * 60 + end_time.minute - duration

                        if work_end_minutes > work_start_minutes:
                            random_minutes = random.randint(work_start_minutes, work_end_minutes)
                            apt_start = time(random_minutes // 60, random_minutes % 60)
                            apt_end = time((random_minutes + duration) // 60, (random_minutes + duration) % 60)

                            # Check for conflicts
                            conflicts = False
                            for blocked in blocked_times:
                                blocked_start = datetime.strptime(blocked["start_time"], "%H:%M").time()
                                blocked_end = datetime.strptime(blocked["end_time"], "%H:%M").time()

                                if (apt_start < blocked_end and apt_end > blocked_start):
                                    conflicts = True
                                    break

                            if not conflicts:
                                appointments.append({
                                    "start_time": apt_start.strftime("%H:%M"),
                                    "end_time": apt_end.strftime("%H:%M"),
                                    "appointment_type": apt_type,
                                    "duration_minutes": duration,
                                    "status": "booked",
                                    "client_id": f"client_{random.randint(1000, 9999)}",
                                    "location": random.choice(["houston_main", "virtual_meeting", "client_location"])
                                })

                                blocked_times.append({
                                    "start_time": apt_start.strftime("%H:%M"),
                                    "end_time": apt_end.strftime("%H:%M"),
                                    "type": "appointment"
                                })
                                break

                        attempts += 1

            schedule[current_date.isoformat()] = {
                "date": current_date.isoformat(),
                "day_of_week": day_name.title(),
                "working_hours": working_hours,
                "appointments": appointments,
                "blocked_times": blocked_times,
                "available": len(appointments) < consultant["preferences"]["max_appointments_per_day"]
            }
        else:
            # Non-working day
            schedule[current_date.isoformat()] = {
                "date": current_date.isoformat(),
                "day_of_week": day_name.title(),
                "working_hours": None,
                "appointments": [],
                "blocked_times": [],
                "available": False
            }

        current_date += timedelta(days=1)

    return {
        "consultant_id": consultant_id,
        "consultant_name": consultant["name"],
        "schedule_period": {
            "start_date": start_date.isoformat(),
            "end_date": (start_date + timedelta(days=days-1)).isoformat(),
            "total_days": days
        },
        "schedule": schedule
    }

def find_available_time_slots(
    consultant_id: str,
    appointment_type: str,
    preferred_date: Optional[date] = None,
    days_ahead: int = 14
) -> List[Dict[str, Any]]:
    """Find available time slots for a specific appointment type"""

    consultant = CONSULTANT_PROFILES.get(consultant_id)
    if not consultant:
        return []

    appointment_info = APPOINTMENT_TYPES.get(appointment_type)
    if not appointment_info:
        return []

    start_date = preferred_date or date.today() + timedelta(days=1)  # Tomorrow or preferred date
    duration = appointment_info["duration_minutes"]
    buffer_time = consultant["preferences"]["buffer_time_minutes"]

    available_slots = []

    for day_offset in range(days_ahead):
        check_date = start_date + timedelta(days=day_offset)
        day_name = check_date.strftime("%A").lower()

        working_hours = consultant["availability"]["working_hours"].get(day_name)
        if not working_hours or not working_hours["start"]:
            continue

        # Get existing schedule (simplified - in reality would query database)
        schedule = generate_consultant_schedule(consultant_id, check_date, 1)
        day_schedule = schedule["schedule"].get(check_date.isoformat(), {})

        if not day_schedule.get("available"):
            continue

        # Find free slots
        start_time = datetime.strptime(working_hours["start"], "%H:%M").time()
        end_time = datetime.strptime(working_hours["end"], "%H:%M").time()

        # Convert to minutes for easier calculation
        work_start_minutes = start_time.hour * 60 + start_time.minute
        work_end_minutes = end_time.hour * 60 + end_time.minute

        # Get blocked times
        blocked_periods = []
        for blocked in day_schedule.get("blocked_times", []):
            blocked_start = datetime.strptime(blocked["start_time"], "%H:%M")
            blocked_end = datetime.strptime(blocked["end_time"], "%H:%M")
            blocked_periods.append((
                blocked_start.hour * 60 + blocked_start.minute,
                blocked_end.hour * 60 + blocked_end.minute
            ))

        # Find available slots
        current_time = work_start_minutes
        while current_time + duration + buffer_time <= work_end_minutes:
            slot_end = current_time + duration

            # Check for conflicts
            conflicts = False
            for blocked_start, blocked_end in blocked_periods:
                if current_time < blocked_end and slot_end > blocked_start:
                    conflicts = True
                    current_time = blocked_end + buffer_time
                    break

            if not conflicts:
                slot_start_time = time(current_time // 60, current_time % 60)
                slot_end_time = time(slot_end // 60, slot_end % 60)

                available_slots.append({
                    "date": check_date.isoformat(),
                    "start_time": slot_start_time.strftime("%H:%M"),
                    "end_time": slot_end_time.strftime("%H:%M"),
                    "duration_minutes": duration,
                    "consultant_id": consultant_id,
                    "consultant_name": consultant["name"],
                    "appointment_type": appointment_type,
                    "can_be_virtual": appointment_info["can_be_virtual"],
                    "price": appointment_info["price"]
                })

                current_time += duration + buffer_time
            else:
                # Move to next possible slot if no conflict found
                if current_time == work_start_minutes:
                    current_time += 30  # Move by 30 minutes if stuck

    return available_slots

def get_consultant_recommendations(
    property_type: str,
    county: str,
    case_complexity: str = "medium",
    preferred_language: str = "english"
) -> List[Dict[str, Any]]:
    """Get consultant recommendations based on case requirements"""

    recommendations = []

    for consultant_id, consultant in CONSULTANT_PROFILES.items():
        score = 0
        reasons = []

        # County coverage
        if county.lower() in consultant["counties_served"]:
            score += 30
            reasons.append(f"Serves {county.title()} County")

        # Specialties match
        property_specialties = {
            "residential": ["residential_appeals", "exemptions"],
            "commercial": ["commercial_appeals", "business_personal_property"],
            "industrial": ["commercial_appeals", "industrial_properties"],
            "agricultural": ["agricultural_properties", "exemptions"]
        }

        matching_specialties = set(consultant["specialties"]) & set(property_specialties.get(property_type, []))
        if matching_specialties:
            score += 25 * len(matching_specialties)
            reasons.append(f"Specializes in {', '.join(matching_specialties)}")

        # Experience level
        if case_complexity == "high" and consultant["experience_years"] >= 15:
            score += 20
            reasons.append("Extensive experience for complex cases")
        elif case_complexity == "medium" and consultant["experience_years"] >= 8:
            score += 15
            reasons.append("Good experience level")
        elif case_complexity == "low":
            score += 10
            reasons.append("Suitable experience level")

        # Success rate
        if consultant["success_rate"] >= 0.8:
            score += 15
            reasons.append("High success rate")
        elif consultant["success_rate"] >= 0.7:
            score += 10
            reasons.append("Good success rate")

        # Language preference
        if preferred_language.lower() in consultant["languages"]:
            score += 10
            reasons.append(f"Speaks {preferred_language.title()}")

        if score > 0:
            recommendations.append({
                "consultant_id": consultant_id,
                "consultant_name": consultant["name"],
                "title": consultant["title"],
                "recommendation_score": score,
                "reasons": reasons,
                "experience_years": consultant["experience_years"],
                "success_rate": consultant["success_rate"],
                "specialties": consultant["specialties"],
                "contact": consultant["contact"]
            })

    # Sort by recommendation score
    recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)

    return recommendations

def calculate_optimal_meeting_times(
    multiple_participants: List[str],
    appointment_type: str,
    preferred_dates: List[date]
) -> List[Dict[str, Any]]:
    """Find optimal meeting times when multiple consultants are needed"""

    common_slots = []

    for preferred_date in preferred_dates:
        # Find slots for each participant
        participant_slots = {}

        for participant in multiple_participants:
            slots = find_available_time_slots(participant, appointment_type, preferred_date, 1)
            participant_slots[participant] = slots

        # Find overlapping time slots
        if len(participant_slots) >= 2:
            # Get the participant with the fewest slots as base
            base_participant = min(participant_slots.keys(),
                                 key=lambda x: len(participant_slots[x]))
            base_slots = participant_slots[base_participant]

            for base_slot in base_slots:
                slot_works_for_all = True

                for other_participant in participant_slots:
                    if other_participant == base_participant:
                        continue

                    # Check if any slot overlaps
                    overlapping_slot = None
                    for other_slot in participant_slots[other_participant]:
                        if (other_slot["date"] == base_slot["date"] and
                            other_slot["start_time"] == base_slot["start_time"]):
                            overlapping_slot = other_slot
                            break

                    if not overlapping_slot:
                        slot_works_for_all = False
                        break

                if slot_works_for_all:
                    common_slots.append({
                        "date": base_slot["date"],
                        "start_time": base_slot["start_time"],
                        "end_time": base_slot["end_time"],
                        "participants": multiple_participants,
                        "appointment_type": appointment_type,
                        "total_price": APPOINTMENT_TYPES[appointment_type]["price"]
                    })

    return common_slots