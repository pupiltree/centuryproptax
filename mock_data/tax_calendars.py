"""
Tax Calendar Data for Texas Counties

Comprehensive tax payment and appeal deadline information for major Texas counties,
including seasonal variations and special circumstances.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import calendar


# Tax calendar template for Texas counties
TAX_CALENDAR_TEMPLATE = {
    "tax_year": 2024,
    "key_dates": {
        "assessment_notice": "2024-04-01",  # Assessment notices typically sent
        "homestead_deadline": "2024-04-30",  # Homestead exemption deadline
        "protest_deadline": "2024-05-15",   # Standard protest deadline (or 30 days after notice)
        "protest_deadline_extended": "2024-06-15",  # If notice sent after April 1
        "arb_hearings_begin": "2024-06-01",  # ARB hearings typically begin
        "arb_hearings_end": "2024-09-30",   # ARB hearings must conclude by
        "values_certified": "2024-07-25",   # Certified values to taxing units
        "tax_bills_sent": "2024-10-01",     # Tax bills typically mailed
        "discount_deadline": "2024-11-30",  # 3% discount if paid early
        "no_penalty_deadline": "2024-01-31",  # Pay without penalty
        "penalty_begins": "2024-02-01",     # Penalties and interest begin
        "delinquent_date": "2024-07-01"     # Delinquent date (6 months after Jan 31)
    },
    "payment_schedule": {
        "discount_period": {
            "start_date": "2024-10-01",
            "end_date": "2024-11-30",
            "discount_percent": 0.03,
            "description": "3% discount for early payment"
        },
        "no_penalty_period": {
            "start_date": "2024-10-01",
            "end_date": "2024-01-31",
            "description": "No penalty or interest"
        },
        "penalty_structure": [
            {"month": "February", "penalty_percent": 0.06, "interest_percent": 0.01},
            {"month": "March", "penalty_percent": 0.07, "interest_percent": 0.01},
            {"month": "April", "penalty_percent": 0.08, "interest_percent": 0.01},
            {"month": "May", "penalty_percent": 0.09, "interest_percent": 0.01},
            {"month": "June", "penalty_percent": 0.10, "interest_percent": 0.01},
            {"month": "July+", "penalty_percent": 0.12, "interest_percent": 0.01}
        ]
    },
    "special_deadlines": {
        "senior_freeze": "2024-04-30",  # Senior citizen tax ceiling
        "disability_exemption": "2024-04-30",
        "veteran_exemption": "2024-04-30",
        "agricultural_exemption": "2024-04-30",
        "business_personal_property": "2024-04-15",
        "rendition_deadline": "2024-04-15"  # Business property rendition
    }
}

# County-specific variations
COUNTY_TAX_CALENDARS = {
    "harris": {
        "county_name": "Harris County",
        "appraisal_district": "Harris County Appraisal District (HCAD)",
        "contact": {
            "phone": "(713) 957-5800",
            "website": "https://hcad.org",
            "address": "13013 Northwest Freeway, Houston, TX 77040"
        },
        "tax_year": 2024,
        "key_dates": {
            "assessment_notice": "2024-04-15",  # HCAD sends notices mid-April
            "homestead_deadline": "2024-04-30",
            "protest_deadline": "2024-05-15",   # Or 30 days after notice
            "protest_deadline_extended": "2024-06-15",
            "arb_hearings_begin": "2024-06-01",
            "arb_hearings_end": "2024-09-30",
            "values_certified": "2024-07-25",
            "tax_bills_sent": "2024-10-01",
            "discount_deadline": "2024-11-30",
            "no_penalty_deadline": "2024-01-31",
            "penalty_begins": "2024-02-01",
            "delinquent_date": "2024-07-01"
        },
        "special_provisions": {
            "disaster_extensions": True,  # May extend deadlines for natural disasters
            "online_protest": True,       # Supports online protest filing
            "informal_review": True       # Offers informal review before ARB
        },
        "payment_options": {
            "online": "https://actweb.acttax.com/act_webdev/harris/index.jsp",
            "phone": "(713) 274-8000",
            "mail": True,
            "in_person": True,
            "installment_plans": True
        }
    },
    "dallas": {
        "county_name": "Dallas County",
        "appraisal_district": "Dallas Central Appraisal District (DCAD)",
        "contact": {
            "phone": "(214) 631-0910",
            "website": "https://dallascad.org",
            "address": "2949 North Stemmons Freeway, Dallas, TX 75247"
        },
        "tax_year": 2024,
        "key_dates": {
            "assessment_notice": "2024-04-01",
            "homestead_deadline": "2024-04-30",
            "protest_deadline": "2024-05-15",
            "protest_deadline_extended": "2024-06-15",
            "arb_hearings_begin": "2024-06-01",
            "arb_hearings_end": "2024-09-30",
            "values_certified": "2024-07-25",
            "tax_bills_sent": "2024-10-01",
            "discount_deadline": "2024-11-30",
            "no_penalty_deadline": "2024-01-31",
            "penalty_begins": "2024-02-01",
            "delinquent_date": "2024-07-01"
        },
        "special_provisions": {
            "disaster_extensions": True,
            "online_protest": True,
            "informal_review": True,
            "evening_hearings": True  # DCAD offers evening ARB hearings
        },
        "payment_options": {
            "online": "https://www.dallascounty.org/government/tax-office/",
            "phone": "(214) 653-7811",
            "mail": True,
            "in_person": True,
            "installment_plans": True
        }
    },
    "tarrant": {
        "county_name": "Tarrant County",
        "appraisal_district": "Tarrant Appraisal District (TAD)",
        "contact": {
            "phone": "(817) 284-5400",
            "website": "https://www.tad.org",
            "address": "2500 Handley Ederville Road, Fort Worth, TX 76118"
        },
        "tax_year": 2024,
        "key_dates": {
            "assessment_notice": "2024-04-05",
            "homestead_deadline": "2024-04-30",
            "protest_deadline": "2024-05-15",
            "protest_deadline_extended": "2024-06-15",
            "arb_hearings_begin": "2024-06-01",
            "arb_hearings_end": "2024-09-30",
            "values_certified": "2024-07-25",
            "tax_bills_sent": "2024-10-01",
            "discount_deadline": "2024-11-30",
            "no_penalty_deadline": "2024-01-31",
            "penalty_begins": "2024-02-01",
            "delinquent_date": "2024-07-01"
        },
        "special_provisions": {
            "disaster_extensions": True,
            "online_protest": True,
            "informal_review": True,
            "saturday_hearings": True  # TAD offers Saturday hearings
        },
        "payment_options": {
            "online": "https://www.tarrantcounty.com/en/tax-assessor-collector.html",
            "phone": "(817) 884-1100",
            "mail": True,
            "in_person": True,
            "installment_plans": True
        }
    },
    "travis": {
        "county_name": "Travis County",
        "appraisal_district": "Travis Central Appraisal District (TCAD)",
        "contact": {
            "phone": "(512) 834-9317",
            "website": "https://traviscad.org",
            "address": "8314 Cross Park Drive, Austin, TX 78754"
        },
        "tax_year": 2024,
        "key_dates": {
            "assessment_notice": "2024-04-10",
            "homestead_deadline": "2024-04-30",
            "protest_deadline": "2024-05-15",
            "protest_deadline_extended": "2024-06-15",
            "arb_hearings_begin": "2024-06-01",
            "arb_hearings_end": "2024-09-30",
            "values_certified": "2024-07-25",
            "tax_bills_sent": "2024-10-01",
            "discount_deadline": "2024-11-30",
            "no_penalty_deadline": "2024-01-31",
            "penalty_begins": "2024-02-01",
            "delinquent_date": "2024-07-01"
        },
        "special_provisions": {
            "disaster_extensions": True,
            "online_protest": True,
            "informal_review": True,
            "mobile_hearings": True  # TCAD offers mobile hearings for accessibility
        },
        "payment_options": {
            "online": "https://tax-office.traviscountytx.gov/",
            "phone": "(512) 854-9473",
            "mail": True,
            "in_person": True,
            "installment_plans": True
        }
    },
    "bexar": {
        "county_name": "Bexar County",
        "appraisal_district": "Bexar Appraisal District (BCAD)",
        "contact": {
            "phone": "(210) 242-2405",
            "website": "https://www.bcad.org",
            "address": "411 N. Frio St., San Antonio, TX 78207"
        },
        "tax_year": 2024,
        "key_dates": {
            "assessment_notice": "2024-04-08",
            "homestead_deadline": "2024-04-30",
            "protest_deadline": "2024-05-15",
            "protest_deadline_extended": "2024-06-15",
            "arb_hearings_begin": "2024-06-01",
            "arb_hearings_end": "2024-09-30",
            "values_certified": "2024-07-25",
            "tax_bills_sent": "2024-10-01",
            "discount_deadline": "2024-11-30",
            "no_penalty_deadline": "2024-01-31",
            "penalty_begins": "2024-02-01",
            "delinquent_date": "2024-07-01"
        },
        "special_provisions": {
            "disaster_extensions": True,
            "online_protest": True,
            "informal_review": True,
            "bilingual_services": True  # BCAD offers bilingual services
        },
        "payment_options": {
            "online": "https://www.bexar.org/1847/Tax-Assessor-Collector",
            "phone": "(210) 335-2251",
            "mail": True,
            "in_person": True,
            "installment_plans": True
        }
    },
    "collin": {
        "county_name": "Collin County",
        "appraisal_district": "Collin Central Appraisal District (CCAD)",
        "contact": {
            "phone": "(972) 562-8121",
            "website": "https://www.collincad.org",
            "address": "250 Eldorado Parkway, McKinney, TX 75069"
        },
        "tax_year": 2024,
        "key_dates": {
            "assessment_notice": "2024-04-12",
            "homestead_deadline": "2024-04-30",
            "protest_deadline": "2024-05-15",
            "protest_deadline_extended": "2024-06-15",
            "arb_hearings_begin": "2024-06-01",
            "arb_hearings_end": "2024-09-30",
            "values_certified": "2024-07-25",
            "tax_bills_sent": "2024-10-01",
            "discount_deadline": "2024-11-30",
            "no_penalty_deadline": "2024-01-31",
            "penalty_begins": "2024-02-01",
            "delinquent_date": "2024-07-01"
        },
        "special_provisions": {
            "disaster_extensions": True,
            "online_protest": True,
            "informal_review": True,
            "expedited_hearings": True  # CCAD offers expedited hearings for simple cases
        },
        "payment_options": {
            "online": "https://www.collincountytx.gov/tax_assessor/",
            "phone": "(972) 548-4650",
            "mail": True,
            "in_person": True,
            "installment_plans": True
        }
    }
}

# Business property specific deadlines
BUSINESS_PROPERTY_DEADLINES = {
    "rendition_deadline": "2024-04-15",  # Business personal property rendition
    "rendition_extension": "2024-05-15",  # With penalty
    "efile_deadline": "2024-04-15",      # Electronic filing
    "franchise_tax": "2024-05-15",       # Related franchise tax deadline
    "sales_tax": {
        "monthly": "20th of following month",
        "quarterly": "20th of month following quarter",
        "annual": "2024-01-20"
    }
}

# Special circumstances and extensions
SPECIAL_CIRCUMSTANCES = {
    "disaster_declarations": {
        "description": "Natural disaster deadline extensions",
        "typical_extension": "30-60 days",
        "recent_examples": [
            {"event": "Hurricane Harvey", "year": 2017, "extension_days": 60},
            {"event": "Winter Storm Uri", "year": 2021, "extension_days": 30},
            {"event": "Hurricane Beryl", "year": 2024, "extension_days": 30}
        ]
    },
    "covid19_impacts": {
        "description": "COVID-19 related extensions (mostly ended)",
        "status": "No longer applicable for 2024",
        "historical_note": "Extensive extensions were provided in 2020-2021"
    },
    "military_deployment": {
        "description": "Active military deployment extensions",
        "extension": "180 days after return from deployment",
        "requirements": ["Must be deployed outside Texas", "Must provide military orders"]
    },
    "elderly_disabled": {
        "description": "Special provisions for elderly and disabled taxpayers",
        "provisions": [
            "Extended time for hearings",
            "Special assistance available",
            "Home visit options in some counties"
        ]
    }
}

# Notification and reminder schedule
NOTIFICATION_SCHEDULE = {
    "advance_warnings": {
        "90_days": "Notice of upcoming assessment notice",
        "60_days": "Reminder about exemption deadlines",
        "30_days": "Final exemption deadline warning",
        "15_days": "Protest deadline approaching",
        "7_days": "Final protest deadline warning",
        "3_days": "Last chance to file protest"
    },
    "payment_reminders": {
        "discount_available": "2024-10-15",  # Two weeks after bills sent
        "discount_ending": "2024-11-25",     # 5 days before discount deadline
        "payment_due": "2024-01-25",         # 6 days before penalty
        "penalty_starting": "2024-02-01",    # Day penalties begin
        "delinquent_warning": "2024-06-15"   # 15 days before delinquent
    }
}

def get_county_calendar(county_code: str) -> Optional[Dict[str, Any]]:
    """Get tax calendar for specific county"""
    return COUNTY_TAX_CALENDARS.get(county_code.lower())

def get_current_deadlines(county_code: str, current_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """Get upcoming deadlines for a county"""
    if current_date is None:
        current_date = date.today()

    county_calendar = get_county_calendar(county_code)
    if not county_calendar:
        return []

    upcoming_deadlines = []
    key_dates = county_calendar["key_dates"]

    for deadline_name, deadline_date_str in key_dates.items():
        deadline_date = datetime.strptime(deadline_date_str, "%Y-%m-%d").date()

        # Only include future deadlines or deadlines within last 30 days
        days_difference = (deadline_date - current_date).days

        if -30 <= days_difference <= 365:  # Past 30 days to future 365 days
            urgency = "low"
            if days_difference <= 7:
                urgency = "high"
            elif days_difference <= 30:
                urgency = "medium"

            upcoming_deadlines.append({
                "deadline_name": deadline_name.replace("_", " ").title(),
                "deadline_date": deadline_date_str,
                "days_until_deadline": days_difference,
                "urgency": urgency,
                "category": categorize_deadline(deadline_name),
                "description": get_deadline_description(deadline_name)
            })

    # Sort by deadline date
    upcoming_deadlines.sort(key=lambda x: x["days_until_deadline"])

    return upcoming_deadlines

def categorize_deadline(deadline_name: str) -> str:
    """Categorize deadline type"""
    if "protest" in deadline_name or "arb" in deadline_name:
        return "appeal"
    elif "payment" in deadline_name or "discount" in deadline_name or "penalty" in deadline_name or "delinquent" in deadline_name:
        return "payment"
    elif "exemption" in deadline_name or "homestead" in deadline_name:
        return "exemption"
    elif "assessment" in deadline_name or "notice" in deadline_name:
        return "assessment"
    else:
        return "other"

def get_deadline_description(deadline_name: str) -> str:
    """Get human-readable description of deadline"""
    descriptions = {
        "assessment_notice": "Property assessment notices are typically mailed",
        "homestead_deadline": "Last day to file for homestead exemption",
        "protest_deadline": "Last day to file property tax protest (if notice received by April 1)",
        "protest_deadline_extended": "Extended protest deadline (if notice received after April 1)",
        "arb_hearings_begin": "Appraisal Review Board hearings begin",
        "arb_hearings_end": "All ARB hearings must conclude by this date",
        "values_certified": "Certified appraisal roll delivered to taxing units",
        "tax_bills_sent": "Property tax bills are mailed",
        "discount_deadline": "Last day to pay taxes with 3% discount",
        "no_penalty_deadline": "Last day to pay taxes without penalty",
        "penalty_begins": "Penalties and interest begin accruing",
        "delinquent_date": "Taxes become delinquent"
    }
    return descriptions.get(deadline_name, "Important tax-related deadline")

def calculate_payment_amount(
    tax_amount: int,
    payment_date: date,
    county_code: str
) -> Dict[str, Any]:
    """Calculate payment amount with discounts or penalties"""
    county_calendar = get_county_calendar(county_code)
    if not county_calendar:
        return {"error": "County not found"}

    # Parse key dates
    discount_deadline = datetime.strptime(
        county_calendar["key_dates"]["discount_deadline"], "%Y-%m-%d"
    ).date()
    no_penalty_deadline = datetime.strptime(
        county_calendar["key_dates"]["no_penalty_deadline"], "%Y-%m-%d"
    ).date()
    penalty_begins = datetime.strptime(
        county_calendar["key_dates"]["penalty_begins"], "%Y-%m-%d"
    ).date()

    base_amount = tax_amount
    discount = 0
    penalty = 0
    interest = 0

    # Calculate discount (if applicable)
    if payment_date <= discount_deadline:
        discount = int(tax_amount * 0.03)  # 3% discount
        total_amount = tax_amount - discount
        status = "discount_period"

    # No penalty period
    elif payment_date <= no_penalty_deadline:
        total_amount = tax_amount
        status = "no_penalty"

    # Penalty period
    else:
        # Calculate penalty based on month
        months_late = (payment_date.year - penalty_begins.year) * 12 + (payment_date.month - penalty_begins.month)

        if months_late == 0:  # February
            penalty_rate = 0.06
        elif months_late == 1:  # March
            penalty_rate = 0.07
        elif months_late == 2:  # April
            penalty_rate = 0.08
        elif months_late == 3:  # May
            penalty_rate = 0.09
        elif months_late == 4:  # June
            penalty_rate = 0.10
        else:  # July and beyond
            penalty_rate = 0.12

        penalty = int(tax_amount * penalty_rate)
        interest = int(tax_amount * 0.01 * max(1, months_late))  # 1% per month interest
        total_amount = tax_amount + penalty + interest
        status = "penalty_period"

    return {
        "base_tax_amount": base_amount,
        "discount": discount,
        "penalty": penalty,
        "interest": interest,
        "total_amount": total_amount,
        "payment_status": status,
        "payment_date": payment_date.isoformat(),
        "savings_vs_late": discount if discount > 0 else -(penalty + interest)
    }

def get_notification_preferences() -> Dict[str, Any]:
    """Get available notification preferences"""
    return {
        "methods": ["email", "sms", "phone_call", "mail"],
        "frequencies": ["immediate", "daily", "weekly", "monthly"],
        "advance_notice": [1, 3, 7, 14, 30, 60, 90],  # days in advance
        "categories": ["exemptions", "appeals", "payments", "assessments", "all"]
    }