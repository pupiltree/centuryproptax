"""TDLR public records handling per Texas Government Code Chapter 552."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re

from config.compliance_settings import (
    TDLRComplianceSettings,
    DataClassification,
    compliance_settings
)


class PublicRecordStatus(Enum):
    """Status of public record requests."""
    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    DENIED = "denied"
    COMPLETED = "completed"
    APPEALED = "appealed"


class ExemptionType(Enum):
    """Types of public records exemptions under Texas Government Code."""
    CONFIDENTIAL_INFORMATION = "confidential_information"
    PERSONNEL_RECORDS = "personnel_records"
    LITIGATION_RECORDS = "litigation_records"
    SECURITY_INFORMATION = "security_information"
    TRADE_SECRETS = "trade_secrets"
    PRIVACY_PROTECTION = "privacy_protection"
    LAW_ENFORCEMENT = "law_enforcement"
    INTERNAL_COMMUNICATIONS = "internal_communications"


@dataclass
class PublicRecordRequest:
    """Public record request under Texas Government Code Chapter 552."""
    request_id: str
    requester_name: str
    requester_contact: str
    request_date: datetime
    description: str
    specific_records: List[str]
    status: PublicRecordStatus
    response_deadline: datetime
    estimated_cost: Optional[float]
    records_identified: List[str]
    exemptions_applied: List[ExemptionType]
    redactions_required: bool
    final_response_date: Optional[datetime]
    appeal_deadline: Optional[datetime]
    metadata: Dict[str, Any]


@dataclass
class RecordClassification:
    """Classification of records for public access."""
    record_id: str
    record_type: str
    classification: DataClassification
    is_public_record: bool
    exemptions: List[ExemptionType]
    redaction_required: bool
    access_restrictions: List[str]
    retention_requirements: str


@dataclass
class RedactionRule:
    """Rules for redacting sensitive information from public records."""
    rule_id: str
    name: str
    description: str
    pattern: str
    replacement: str
    exemption_basis: ExemptionType
    applies_to_record_types: List[str]
    mandatory: bool


class PublicRecordsHandler:
    """TDLR public records handling system per Texas Government Code Chapter 552."""

    def __init__(self):
        self.settings = compliance_settings
        self.logger = logging.getLogger(__name__)
        self.public_record_requests: Dict[str, PublicRecordRequest] = {}
        self.record_classifications: Dict[str, RecordClassification] = {}
        self.redaction_rules: List[RedactionRule] = []
        self._initialize_default_redaction_rules()

    def _initialize_default_redaction_rules(self):
        """Initialize default redaction rules for public records."""
        default_rules = [
            RedactionRule(
                rule_id="SSN_REDACTION",
                name="Social Security Number Redaction",
                description="Redact SSN from public records",
                pattern=r"\b\d{3}-?\d{2}-?\d{4}\b",
                replacement="XXX-XX-XXXX",
                exemption_basis=ExemptionType.PRIVACY_PROTECTION,
                applies_to_record_types=["all"],
                mandatory=True
            ),
            RedactionRule(
                rule_id="BANK_ACCOUNT_REDACTION",
                name="Bank Account Number Redaction",
                description="Redact bank account numbers from public records",
                pattern=r"\b\d{8,17}\b",
                replacement="XXXXXXXXXX",
                exemption_basis=ExemptionType.PRIVACY_PROTECTION,
                applies_to_record_types=["payment_records", "financial_documents"],
                mandatory=True
            ),
            RedactionRule(
                rule_id="PHONE_REDACTION",
                name="Phone Number Redaction",
                description="Redact personal phone numbers from public records",
                pattern=r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
                replacement="XXX-XXX-XXXX",
                exemption_basis=ExemptionType.PRIVACY_PROTECTION,
                applies_to_record_types=["customer_communications", "correspondence"],
                mandatory=False
            ),
            RedactionRule(
                rule_id="EMAIL_REDACTION",
                name="Email Address Redaction",
                description="Redact personal email addresses from public records",
                pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                replacement="[REDACTED EMAIL]",
                exemption_basis=ExemptionType.PRIVACY_PROTECTION,
                applies_to_record_types=["customer_communications", "correspondence"],
                mandatory=False
            ),
            RedactionRule(
                rule_id="INTERNAL_MEMO_REDACTION",
                name="Internal Communications Redaction",
                description="Redact internal deliberative communications",
                pattern=r"(INTERNAL|CONFIDENTIAL|DRAFT).*?(?=\n\n|\Z)",
                replacement="[REDACTED - INTERNAL COMMUNICATION]",
                exemption_basis=ExemptionType.INTERNAL_COMMUNICATIONS,
                applies_to_record_types=["memos", "internal_documents"],
                mandatory=True
            )
        ]

        self.redaction_rules.extend(default_rules)

    def submit_public_record_request(self, requester_name: str, requester_contact: str,
                                   description: str, specific_records: List[str]) -> str:
        """Submit a new public record request."""
        request_id = f"PRR-{datetime.now().strftime('%Y%m%d')}-{len(self.public_record_requests) + 1:04d}"
        request_date = datetime.now()
        response_deadline = request_date + timedelta(days=10)  # Texas Gov Code 552.221

        request = PublicRecordRequest(
            request_id=request_id,
            requester_name=requester_name,
            requester_contact=requester_contact,
            request_date=request_date,
            description=description,
            specific_records=specific_records,
            status=PublicRecordStatus.RECEIVED,
            response_deadline=response_deadline,
            estimated_cost=None,
            records_identified=[],
            exemptions_applied=[],
            redactions_required=False,
            final_response_date=None,
            appeal_deadline=None,
            metadata={}
        )

        self.public_record_requests[request_id] = request
        self.logger.info(f"Public record request submitted: {request_id}")

        # Automatically start review process
        self._initiate_request_review(request_id)

        return request_id

    def _initiate_request_review(self, request_id: str):
        """Initiate review process for public record request."""
        if request_id not in self.public_record_requests:
            return

        request = self.public_record_requests[request_id]
        request.status = PublicRecordStatus.UNDER_REVIEW

        # Identify potentially responsive records
        identified_records = self._identify_responsive_records(request.description, request.specific_records)
        request.records_identified = identified_records

        # Classify records and determine exemptions
        exemptions_needed = []
        redactions_needed = False

        for record_id in identified_records:
            classification = self._classify_record_for_public_access(record_id)
            if classification.exemptions:
                exemptions_needed.extend(classification.exemptions)
            if classification.redaction_required:
                redactions_needed = True

        request.exemptions_applied = list(set(exemptions_needed))
        request.redactions_required = redactions_needed

        # Estimate cost if substantial time required
        estimated_hours = len(identified_records) * 0.5  # 30 minutes per record
        if estimated_hours > 1:
            request.estimated_cost = estimated_hours * 25.00  # $25/hour per Texas Gov Code

        self.logger.info(f"Request {request_id} under review: {len(identified_records)} records identified")

    def _identify_responsive_records(self, description: str, specific_records: List[str]) -> List[str]:
        """Identify records responsive to the public record request."""
        responsive_records = []

        # Search based on specific record IDs if provided
        responsive_records.extend(specific_records)

        # Search based on description keywords
        keywords = self._extract_keywords_from_description(description)
        for keyword in keywords:
            # Implementation would search actual record database
            # For demo purposes, simulate finding records
            if keyword.lower() in ["property", "tax", "assessment"]:
                responsive_records.extend([f"PROP_{keyword}_{i}" for i in range(1, 4)])
            elif keyword.lower() in ["payment", "receipt"]:
                responsive_records.extend([f"PAY_{keyword}_{i}" for i in range(1, 3)])

        return list(set(responsive_records))

    def _extract_keywords_from_description(self, description: str) -> List[str]:
        """Extract keywords from request description."""
        # Simple keyword extraction
        common_words = {"the", "and", "or", "of", "to", "from", "in", "on", "at", "by", "for"}
        words = re.findall(r'\b\w+\b', description.lower())
        keywords = [word for word in words if len(word) > 3 and word not in common_words]
        return keywords

    def _classify_record_for_public_access(self, record_id: str) -> RecordClassification:
        """Classify a record for public access determination."""
        # Simulate record classification - in practice, this would query actual records
        if record_id.startswith("PROP_"):
            return RecordClassification(
                record_id=record_id,
                record_type="property_assessment",
                classification=DataClassification.PUBLIC,
                is_public_record=True,
                exemptions=[],
                redaction_required=False,
                access_restrictions=[],
                retention_requirements="7 years"
            )
        elif record_id.startswith("PAY_"):
            return RecordClassification(
                record_id=record_id,
                record_type="payment_record",
                classification=DataClassification.CONFIDENTIAL,
                is_public_record=True,
                exemptions=[ExemptionType.PRIVACY_PROTECTION],
                redaction_required=True,
                access_restrictions=["personal_financial_information"],
                retention_requirements="7 years"
            )
        else:
            return RecordClassification(
                record_id=record_id,
                record_type="general_document",
                classification=DataClassification.CONFIDENTIAL,
                is_public_record=False,
                exemptions=[ExemptionType.CONFIDENTIAL_INFORMATION],
                redaction_required=False,
                access_restrictions=["not_public_record"],
                retention_requirements="varies"
            )

    def process_public_record_request(self, request_id: str, approved_records: List[str],
                                    denied_records: List[str], exemption_justifications: Dict[str, str]) -> Dict[str, Any]:
        """Process and respond to public record request."""
        if request_id not in self.public_record_requests:
            raise ValueError(f"Request {request_id} not found")

        request = self.public_record_requests[request_id]

        # Determine final status
        if approved_records and not denied_records:
            request.status = PublicRecordStatus.APPROVED
        elif approved_records and denied_records:
            request.status = PublicRecordStatus.PARTIALLY_APPROVED
        else:
            request.status = PublicRecordStatus.DENIED

        # Apply redactions to approved records
        redacted_records = {}
        for record_id in approved_records:
            redacted_content = self._apply_redactions(record_id)
            redacted_records[record_id] = redacted_content

        # Set appeal deadline (180 days per Texas Gov Code 552.321)
        request.appeal_deadline = datetime.now() + timedelta(days=180)
        request.final_response_date = datetime.now()

        response = {
            "request_id": request_id,
            "status": request.status.value,
            "response_date": request.final_response_date.isoformat(),
            "approved_records": approved_records,
            "denied_records": denied_records,
            "exemption_justifications": exemption_justifications,
            "redacted_records": redacted_records,
            "appeal_deadline": request.appeal_deadline.isoformat(),
            "total_cost": request.estimated_cost or 0.0
        }

        self.logger.info(f"Public record request {request_id} processed: {request.status.value}")
        return response

    def _apply_redactions(self, record_id: str) -> Dict[str, Any]:
        """Apply redactions to record based on exemptions."""
        # Simulate getting record content
        simulated_content = f"""
        Property Assessment Record {record_id}
        Owner: John Doe
        SSN: 123-45-6789
        Phone: 555-123-4567
        Email: john.doe@email.com
        Property Value: $250,000
        Tax Amount: $3,125.00
        Payment Method: Bank Account 1234567890
        INTERNAL NOTE: Reviewed by assessor - potential adjustment needed
        """

        classification = self._classify_record_for_public_access(record_id)
        redacted_content = simulated_content

        # Apply redaction rules
        for rule in self.redaction_rules:
            if (rule.applies_to_record_types == ["all"] or
                classification.record_type in rule.applies_to_record_types):
                if rule.mandatory or rule.exemption_basis in classification.exemptions:
                    redacted_content = re.sub(rule.pattern, rule.replacement, redacted_content, flags=re.IGNORECASE | re.MULTILINE)

        return {
            "original_length": len(simulated_content),
            "redacted_content": redacted_content,
            "redactions_applied": [rule.name for rule in self.redaction_rules
                                 if (rule.applies_to_record_types == ["all"] or
                                     classification.record_type in rule.applies_to_record_types)],
            "exemption_basis": [exemption.value for exemption in classification.exemptions]
        }

    def handle_request_appeal(self, request_id: str, appeal_basis: str, appellant_contact: str) -> str:
        """Handle appeal of public record request decision."""
        if request_id not in self.public_record_requests:
            raise ValueError(f"Request {request_id} not found")

        request = self.public_record_requests[request_id]

        if request.appeal_deadline and datetime.now() > request.appeal_deadline:
            raise ValueError("Appeal deadline has passed")

        request.status = PublicRecordStatus.APPEALED
        appeal_id = f"APPEAL-{request_id}-{datetime.now().strftime('%Y%m%d')}"

        self.logger.info(f"Appeal submitted for request {request_id}: {appeal_id}")
        return appeal_id

    def generate_public_records_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive public records compliance report."""
        period_requests = [
            req for req in self.public_record_requests.values()
            if start_date <= req.request_date <= end_date
        ]

        status_counts = {}
        total_cost = 0
        total_records_released = 0
        exemptions_used = {}

        for request in period_requests:
            status = request.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            if request.estimated_cost:
                total_cost += request.estimated_cost

            total_records_released += len(request.records_identified)

            for exemption in request.exemptions_applied:
                exemption_name = exemption.value
                exemptions_used[exemption_name] = exemptions_used.get(exemption_name, 0) + 1

        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_requests": len(period_requests),
                "requests_by_status": status_counts,
                "total_cost_collected": total_cost,
                "total_records_released": total_records_released,
                "average_response_time_days": self._calculate_average_response_time(period_requests)
            },
            "exemptions_usage": exemptions_used,
            "compliance_metrics": {
                "on_time_responses": len([r for r in period_requests
                                        if r.final_response_date and r.final_response_date <= r.response_deadline]),
                "overdue_responses": len([r for r in period_requests
                                        if not r.final_response_date and datetime.now() > r.response_deadline]),
                "appeals_filed": len([r for r in period_requests if r.status == PublicRecordStatus.APPEALED])
            }
        }

    def _calculate_average_response_time(self, requests: List[PublicRecordRequest]) -> float:
        """Calculate average response time for completed requests."""
        completed_requests = [r for r in requests if r.final_response_date]
        if not completed_requests:
            return 0.0

        total_days = sum((r.final_response_date - r.request_date).days for r in completed_requests)
        return total_days / len(completed_requests)

    def validate_compliance_with_texas_gov_code_552(self) -> Dict[str, Any]:
        """Validate compliance with Texas Government Code Chapter 552."""
        validation_results = {
            "response_time_compliance": True,
            "cost_estimation_compliance": True,
            "exemption_documentation": True,
            "appeal_process_compliance": True,
            "redaction_compliance": True,
            "issues_found": []
        }

        current_time = datetime.now()

        # Check response time compliance (10 business days)
        overdue_requests = [
            req for req in self.public_record_requests.values()
            if not req.final_response_date and current_time > req.response_deadline
        ]

        if overdue_requests:
            validation_results["response_time_compliance"] = False
            validation_results["issues_found"].append(f"{len(overdue_requests)} overdue responses")

        # Check cost estimation compliance
        requests_needing_estimates = [
            req for req in self.public_record_requests.values()
            if len(req.records_identified) > 5 and not req.estimated_cost
        ]

        if requests_needing_estimates:
            validation_results["cost_estimation_compliance"] = False
            validation_results["issues_found"].append(f"{len(requests_needing_estimates)} requests missing cost estimates")

        # Check exemption documentation
        requests_with_undocumented_exemptions = [
            req for req in self.public_record_requests.values()
            if req.exemptions_applied and not any(req.metadata.get("exemption_justifications", {}).values())
        ]

        if requests_with_undocumented_exemptions:
            validation_results["exemption_documentation"] = False
            validation_results["issues_found"].append("Exemptions applied without proper documentation")

        return validation_results


# Example usage and testing
if __name__ == "__main__":
    handler = PublicRecordsHandler()

    print("Testing public records handling...")

    # Submit a test request
    request_id = handler.submit_public_record_request(
        requester_name="Jane Smith",
        requester_contact="jane.smith@email.com",
        description="Property tax assessment records for 123 Main Street",
        specific_records=["PROP_123_MAIN"]
    )

    print(f"Submitted request: {request_id}")

    # Process the request
    response = handler.process_public_record_request(
        request_id=request_id,
        approved_records=["PROP_123_MAIN"],
        denied_records=[],
        exemption_justifications={}
    )

    print(f"Request processed: {response['status']}")
    print(f"Records provided: {len(response['approved_records'])}")

    # Generate compliance report
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    report = handler.generate_public_records_report(start_date, end_date)

    print(f"\nPublic Records Report:")
    print(f"  Total requests: {report['summary']['total_requests']}")
    print(f"  Average response time: {report['summary']['average_response_time_days']:.1f} days")

    # Validate compliance
    compliance = handler.validate_compliance_with_texas_gov_code_552()
    print(f"\nCompliance Status:")
    print(f"  Response time compliance: {compliance['response_time_compliance']}")
    print(f"  Issues found: {len(compliance['issues_found'])}")