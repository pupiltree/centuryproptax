"""
Python Integration Example for Century Property Tax API

This example demonstrates how to integrate with the Century Property Tax API
using Python and the requests library.
"""

import requests
import json
from typing import Dict, Any

class CenturyPropertyTaxAPI:
    """Century Property Tax API client."""

    def __init__(self, base_url: str = "https://api.centuryproptax.com"):
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def search_assessments(self, booking_id: str = None, phone: str = None,
                          status: str = None) -> Dict[str, Any]:
        """Search for assessment reports."""
        params = {}
        if booking_id:
            params['booking_id'] = booking_id
        if phone:
            params['phone'] = phone
        if status:
            params['status'] = status

        response = self.session.get(
            f"{self.base_url}/api/assessment-reports/search",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def update_assessment_status(self, booking_id: str, status: str,
                               report_url: str = None, notes: str = None) -> Dict[str, Any]:
        """Update assessment report status."""
        data = {
            "booking_id": booking_id,
            "status": status
        }
        if report_url:
            data["report_url"] = report_url
        if notes:
            data["notes"] = notes

        response = self.session.post(
            f"{self.base_url}/api/assessment-reports/update",
            json=data
        )
        response.raise_for_status()
        return response.json()

# Example usage
if __name__ == "__main__":
    api = CenturyPropertyTaxAPI()

    # Check API health
    health = api.health_check()
    print(f"API Status: {health.get('status')}")

    # Search for assessments
    assessments = api.search_assessments(status="pending")
    print(f"Found {len(assessments.get('bookings', []))} pending assessments")

    # Update assessment status (example)
    # result = api.update_assessment_status(
    #     booking_id="CPT20250811_A1",
    #     status="ready",
    #     report_url="https://reports.example.com/report.pdf",
    #     notes="Assessment complete"
    # )
    # print(f"Update result: {result.get('message')}")
