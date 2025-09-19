"""
Document Processing Tool for Texas Property Tax System

Processes tax statements, appraisal notices, appeal documents, and other
property tax related documents with OCR, data extraction, and validation.
"""

import asyncio
import base64
import hashlib
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal
import re

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from mock_data.document_templates import (
    DOCUMENT_TYPES,
    OCR_EXTRACTION_PATTERNS,
    DOCUMENT_TEMPLATES,
    generate_mock_ocr_response,
    generate_sample_document_data,
    validate_extracted_data,
    get_document_type_from_content,
    VALIDATION_PATTERNS
)

logger = structlog.get_logger()

class DocumentProcessingInput(BaseModel):
    """Input schema for document processing"""
    document_content: Optional[str] = Field(
        default=None,
        description="Base64 encoded document content or plain text"
    )
    document_url: Optional[str] = Field(
        default=None,
        description="URL to document file"
    )
    document_type: Optional[str] = Field(
        default=None,
        description="Expected document type (auto-detected if not provided)"
    )
    extract_fields: Optional[List[str]] = Field(
        default=None,
        description="Specific fields to extract (extracts all if not provided)"
    )
    validation_level: str = Field(
        default="standard",
        description="Validation level: minimal, standard, strict"
    )
    ocr_settings: Optional[Dict[str, Any]] = Field(
        default=None,
        description="OCR processing settings"
    )

class DocumentProcessingResponse(BaseModel):
    """Response schema for document processing"""
    success: bool = Field(description="Whether processing was successful")
    document_type: Optional[str] = Field(description="Detected or specified document type")
    extracted_data: Dict[str, Any] = Field(description="Extracted field data")
    validation_results: Dict[str, Any] = Field(description="Data validation results")
    processing_metadata: Dict[str, Any] = Field(description="Processing details and metrics")
    suggested_actions: List[Dict[str, str]] = Field(description="Recommended follow-up actions")

def simulate_ocr_processing(content: str, document_type: str) -> Dict[str, Any]:
    """Simulate OCR processing with realistic results"""

    # Simulate processing time based on document complexity
    processing_time = len(content) * 0.1 + 500  # Base time + content complexity

    # Generate sample data for the document
    county = "harris"  # Default for simulation
    sample_data = generate_sample_document_data(document_type, county)

    # Generate mock OCR response
    ocr_response = generate_mock_ocr_response(document_type, sample_data)

    # Add some real content extraction if plain text provided
    if content and not content.startswith("data:"):
        extracted_from_content = extract_from_plain_text(content, document_type)
        if extracted_from_content:
            # Merge content-based extraction with mock data
            for field, value in extracted_from_content.items():
                if value:
                    ocr_response["extracted_data"][field] = value
                    ocr_response["confidence_scores"][field] = 0.95

    ocr_response["processing_time_ms"] = int(processing_time)
    return ocr_response

def extract_from_plain_text(content: str, document_type: str) -> Dict[str, Any]:
    """Extract data from plain text using pattern matching"""

    extracted_data = {}
    patterns = OCR_EXTRACTION_PATTERNS.get(document_type, {}).get("patterns", {})

    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            try:
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    extracted_data[field] = match.group(1).strip()
                    break
            except re.error:
                continue

    return extracted_data

def clean_extracted_value(field_name: str, raw_value: str) -> Any:
    """Clean and normalize extracted values"""
    if not raw_value or raw_value == "EXTRACTION_FAILED":
        return None

    value = raw_value.strip()

    # Handle monetary values
    if field_name in ["assessed_value", "tax_amount", "land_value", "improvement_value", "requested_value"]:
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d.]', '', value)
        try:
            return int(float(cleaned)) if cleaned else None
        except ValueError:
            return None

    # Handle dates
    elif field_name in ["appeal_deadline", "due_date", "discount_date", "penalty_date", "hearing_date"]:
        # Normalize date format
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{1,2})-(\d{1,2})-(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, value)
            if match:
                try:
                    if len(match.group(1)) == 4:  # Year first
                        year, month, day = match.groups()
                    else:  # Month/day first
                        month, day, year = match.groups()

                    return f"{int(month):02d}/{int(day):02d}/{year}"
                except ValueError:
                    continue

        return value  # Return as-is if no pattern matches

    # Handle parcel IDs
    elif field_name == "parcel_id":
        # Clean up common OCR errors in parcel IDs
        cleaned = re.sub(r'[^\w\-]', '', value.upper())
        return cleaned

    # Handle phone numbers
    elif field_name == "phone":
        # Extract digits and format
        digits = re.sub(r'[^\d]', '', value)
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return value

    # Handle percentages
    elif "percent" in field_name or "rate" in field_name:
        # Extract numeric value
        numeric = re.sub(r'[^\d.\-]', '', value)
        try:
            return float(numeric)
        except ValueError:
            return value

    # Default: return cleaned string
    return value

def enrich_extracted_data(extracted_data: Dict[str, Any], document_type: str) -> Dict[str, Any]:
    """Enrich extracted data with calculated fields and insights"""

    enriched_data = extracted_data.copy()

    # Calculate assessment increase if we have both values
    current_value = extracted_data.get("assessed_value") or extracted_data.get("total_value")
    previous_value = extracted_data.get("previous_value")

    if current_value and previous_value and isinstance(current_value, (int, float)) and isinstance(previous_value, (int, float)):
        increase_amount = current_value - previous_value
        increase_percent = (increase_amount / previous_value) * 100 if previous_value > 0 else 0

        enriched_data["assessment_increase_amount"] = increase_amount
        enriched_data["assessment_increase_percent"] = round(increase_percent, 2)

        # Categorize increase
        if increase_percent < 5:
            enriched_data["increase_category"] = "minimal"
        elif increase_percent < 10:
            enriched_data["increase_category"] = "moderate"
        elif increase_percent < 20:
            enriched_data["increase_category"] = "significant"
        else:
            enriched_data["increase_category"] = "substantial"

    # Calculate taxable value if we have assessed value and exemptions
    assessed_value = enriched_data.get("assessed_value")
    exemptions = enriched_data.get("exemptions") or enriched_data.get("homestead_exemption", 0)

    if assessed_value and isinstance(assessed_value, (int, float)):
        if isinstance(exemptions, (int, float)):
            enriched_data["estimated_taxable_value"] = max(0, assessed_value - exemptions)

    # Add document insights
    if document_type == "appraisal_notice":
        appeal_deadline = enriched_data.get("appeal_deadline")
        if appeal_deadline:
            enriched_data["days_to_appeal"] = calculate_days_until_date(appeal_deadline)

    elif document_type == "tax_statement":
        due_date = enriched_data.get("due_date")
        discount_date = enriched_data.get("discount_date")

        if due_date:
            enriched_data["days_to_payment"] = calculate_days_until_date(due_date)

        if discount_date:
            enriched_data["days_to_discount"] = calculate_days_until_date(discount_date)

        # Calculate potential discount savings
        tax_amount = enriched_data.get("tax_amount")
        if tax_amount and isinstance(tax_amount, (int, float)):
            enriched_data["discount_savings"] = int(tax_amount * 0.03)

    # Add data quality indicators
    non_null_fields = sum(1 for v in enriched_data.values() if v is not None and v != "")
    total_possible_fields = len(DOCUMENT_TYPES.get(document_type, {}).get("key_fields", []))

    enriched_data["data_completeness"] = non_null_fields / total_possible_fields if total_possible_fields > 0 else 0

    return enriched_data

def calculate_days_until_date(date_string: str) -> Optional[int]:
    """Calculate days until a given date"""
    try:
        # Parse various date formats
        date_patterns = [
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%Y-%m-%d",
            "%d/%m/%Y"
        ]

        target_date = None
        for pattern in date_patterns:
            try:
                target_date = datetime.strptime(date_string, pattern).date()
                break
            except ValueError:
                continue

        if target_date:
            today = date.today()
            return (target_date - today).days

    except Exception:
        pass

    return None

def generate_action_suggestions(
    document_type: str,
    extracted_data: Dict[str, Any],
    validation_results: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Generate suggested actions based on processed document"""

    suggestions = []

    # Document type specific suggestions
    if document_type == "appraisal_notice":
        days_to_appeal = extracted_data.get("days_to_appeal", 0)

        if days_to_appeal and days_to_appeal > 0:
            if days_to_appeal <= 7:
                suggestions.append({
                    "action": "File Property Tax Protest Immediately",
                    "priority": "urgent",
                    "description": f"Appeal deadline is in {days_to_appeal} days. File protest now.",
                    "deadline": extracted_data.get("appeal_deadline", "")
                })
            elif days_to_appeal <= 30:
                suggestions.append({
                    "action": "Prepare Property Tax Protest",
                    "priority": "high",
                    "description": f"Appeal deadline is in {days_to_appeal} days. Gather evidence and file protest.",
                    "deadline": extracted_data.get("appeal_deadline", "")
                })

        increase_percent = extracted_data.get("assessment_increase_percent", 0)
        if increase_percent > 10:
            suggestions.append({
                "action": "Review Assessment Increase",
                "priority": "medium",
                "description": f"Assessment increased by {increase_percent:.1f}%. Consider protest if market doesn't support increase.",
                "deadline": ""
            })

    elif document_type == "tax_statement":
        days_to_discount = extracted_data.get("days_to_discount", 0)
        days_to_payment = extracted_data.get("days_to_payment", 0)

        if days_to_discount and days_to_discount > 0:
            discount_savings = extracted_data.get("discount_savings", 0)
            suggestions.append({
                "action": "Pay Early for Discount",
                "priority": "medium",
                "description": f"Pay by discount date to save ${discount_savings:,} (3% discount).",
                "deadline": extracted_data.get("discount_date", "")
            })

        if days_to_payment and days_to_payment <= 15:
            suggestions.append({
                "action": "Schedule Tax Payment",
                "priority": "high",
                "description": f"Payment due in {days_to_payment} days to avoid penalties.",
                "deadline": extracted_data.get("due_date", "")
            })

    elif document_type == "protest_form":
        current_value = extracted_data.get("current_value")
        requested_value = extracted_data.get("requested_value")

        if current_value and requested_value:
            potential_savings = (current_value - requested_value) * 0.025  # Estimate 2.5% tax rate
            suggestions.append({
                "action": "Submit Protest Form",
                "priority": "high",
                "description": f"Potential annual savings: ${potential_savings:,.0f} if protest succeeds.",
                "deadline": extracted_data.get("protest_deadline", "")
            })

    # Validation-based suggestions
    if not validation_results.get("is_valid", True):
        suggestions.append({
            "action": "Verify Document Data",
            "priority": "medium",
            "description": "Some extracted data appears invalid. Please review and correct.",
            "deadline": ""
        })

    if validation_results.get("confidence_score", 1.0) < 0.8:
        suggestions.append({
            "action": "Manual Review Required",
            "priority": "medium",
            "description": "Low confidence in data extraction. Manual review recommended.",
            "deadline": ""
        })

    return suggestions

@tool("document_processing_tool", return_direct=False)
async def document_processing_tool(
    document_content: Optional[str] = None,
    document_url: Optional[str] = None,
    document_type: Optional[str] = None,
    extract_fields: Optional[List[str]] = None,
    validation_level: str = "standard",
    ocr_settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process property tax documents with OCR, data extraction, and validation.

    Handles tax statements, appraisal notices, appeal forms, exemption applications,
    and other property tax related documents. Extracts key information and validates data.

    Args:
        document_content: Base64 encoded document content or plain text
        document_url: URL to document file (alternative to content)
        document_type: Expected document type (auto-detected if not provided)
        extract_fields: Specific fields to extract (all fields if not provided)
        validation_level: Validation strictness (minimal, standard, strict)
        ocr_settings: OCR processing configuration

    Returns:
        Comprehensive document processing results with extracted data and validation
    """
    try:
        logger.info("📄 Processing property tax document",
                   has_content=bool(document_content),
                   has_url=bool(document_url),
                   expected_type=document_type)

        # Validate inputs
        if not document_content and not document_url:
            return {
                "success": False,
                "error": "Either document_content or document_url must be provided",
                "suggestions": [
                    "Provide base64 encoded document content",
                    "Provide URL to document file",
                    "Include plain text content for text-based extraction"
                ]
            }

        # Process document content
        if document_url:
            # In real implementation, would fetch from URL
            # For mock, generate sample content
            document_content = "Sample document content from URL"

        # Detect document type if not provided
        detected_type = document_type
        if not detected_type and document_content:
            detected_type = get_document_type_from_content(document_content)

        if not detected_type:
            detected_type = "unknown"

        # Validate document type
        if detected_type not in DOCUMENT_TYPES and detected_type != "unknown":
            return {
                "success": False,
                "error": f"Unsupported document type: {detected_type}",
                "suggestions": [
                    f"Supported types: {', '.join(DOCUMENT_TYPES.keys())}",
                    "Use 'unknown' for auto-detection",
                    "Check document content format"
                ]
            }

        # Simulate OCR processing
        start_time = datetime.now()
        ocr_results = simulate_ocr_processing(document_content or "", detected_type)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Extract and clean data
        raw_extracted_data = ocr_results.get("extracted_data", {})
        cleaned_data = {}

        # Filter fields if specific extraction requested
        fields_to_process = extract_fields or raw_extracted_data.keys()

        for field in fields_to_process:
            if field in raw_extracted_data:
                cleaned_value = clean_extracted_value(field, raw_extracted_data[field])
                if cleaned_value is not None:
                    cleaned_data[field] = cleaned_value

        # Enrich extracted data
        enriched_data = enrich_extracted_data(cleaned_data, detected_type)

        # Validate extracted data
        validation_results = validate_extracted_data(detected_type, enriched_data)

        # Adjust validation based on level
        if validation_level == "minimal":
            # Only check for critical errors
            validation_results["warnings"] = []
        elif validation_level == "strict":
            # Promote warnings to errors
            validation_results["errors"].extend(validation_results["warnings"])
            validation_results["is_valid"] = len(validation_results["errors"]) == 0

        # Generate action suggestions
        suggested_actions = generate_action_suggestions(
            detected_type,
            enriched_data,
            validation_results
        )

        # Compile processing metadata
        processing_metadata = {
            "document_type_detected": detected_type,
            "document_type_confidence": 0.9 if detected_type != "unknown" else 0.5,
            "ocr_confidence": ocr_results.get("overall_confidence", 0.0),
            "processing_time_ms": int(processing_time),
            "pages_processed": ocr_results.get("pages_processed", 1),
            "fields_extracted": len(enriched_data),
            "validation_level": validation_level,
            "data_completeness": enriched_data.get("data_completeness", 0.0),
            "extraction_method": "ocr_simulation",
            "timestamp": datetime.now().isoformat()
        }

        return {
            "success": True,
            "document_type": detected_type,
            "extracted_data": enriched_data,
            "validation_results": validation_results,
            "processing_metadata": processing_metadata,
            "suggested_actions": suggested_actions,
            "confidence_scores": ocr_results.get("confidence_scores", {}),
            "raw_ocr_data": raw_extracted_data if validation_level == "strict" else {}
        }

    except Exception as e:
        logger.error("❌ Document processing failed",
                    error=str(e), document_type=document_type)

        return {
            "success": False,
            "error": f"Document processing failed: {str(e)}",
            "suggestions": [
                "Check document format and content",
                "Verify document type is supported",
                "Ensure document is readable and not corrupted",
                "Try with different validation level",
                "Contact support if the problem persists"
            ]
        }

# Additional utility functions

async def process_multiple_documents(
    documents: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Process multiple documents in batch"""
    results = []

    for doc in documents:
        result = await document_processing_tool(**doc)
        results.append(result)

    return results

def compare_document_values(
    current_document: Dict[str, Any],
    previous_document: Dict[str, Any]
) -> Dict[str, Any]:
    """Compare values between two documents (e.g., current vs previous year)"""

    comparison = {
        "changes_detected": [],
        "value_changes": {},
        "significant_changes": []
    }

    current_data = current_document.get("extracted_data", {})
    previous_data = previous_document.get("extracted_data", {})

    # Compare common fields
    common_fields = set(current_data.keys()) & set(previous_data.keys())

    for field in common_fields:
        current_value = current_data[field]
        previous_value = previous_data[field]

        if current_value != previous_value:
            comparison["changes_detected"].append(field)

            # Calculate numeric changes for monetary fields
            if field in ["assessed_value", "tax_amount", "land_value", "improvement_value"]:
                try:
                    curr_num = float(str(current_value).replace("$", "").replace(",", ""))
                    prev_num = float(str(previous_value).replace("$", "").replace(",", ""))

                    change_amount = curr_num - prev_num
                    change_percent = (change_amount / prev_num) * 100 if prev_num > 0 else 0

                    comparison["value_changes"][field] = {
                        "previous": prev_num,
                        "current": curr_num,
                        "change_amount": change_amount,
                        "change_percent": change_percent
                    }

                    # Flag significant changes
                    if abs(change_percent) > 10:
                        comparison["significant_changes"].append({
                            "field": field,
                            "change_percent": change_percent,
                            "significance": "high" if abs(change_percent) > 20 else "medium"
                        })

                except (ValueError, TypeError):
                    pass

    return comparison

def extract_property_summary(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract property summary for quick reference"""

    summary = {
        "property_address": extracted_data.get("property_address"),
        "parcel_id": extracted_data.get("parcel_id"),
        "current_value": extracted_data.get("assessed_value") or extracted_data.get("total_value"),
        "tax_amount": extracted_data.get("tax_amount"),
        "key_dates": {},
        "exemptions": extracted_data.get("exemptions") or extracted_data.get("homestead_exemption"),
        "assessment_change": {
            "amount": extracted_data.get("assessment_increase_amount"),
            "percent": extracted_data.get("assessment_increase_percent"),
            "category": extracted_data.get("increase_category")
        }
    }

    # Collect important dates
    date_fields = ["appeal_deadline", "due_date", "discount_date", "hearing_date", "penalty_date"]
    for field in date_fields:
        if field in extracted_data and extracted_data[field]:
            summary["key_dates"][field] = extracted_data[field]

    return summary

def get_document_type_info(document_type: str) -> Optional[Dict[str, Any]]:
    """Get information about a document type"""
    return DOCUMENT_TYPES.get(document_type)

def get_supported_document_types() -> List[str]:
    """Get list of supported document types"""
    return list(DOCUMENT_TYPES.keys())