"""
Prescription Image Analysis Tools for Healthcare Assistant
Integrates with enhanced_workflow_tools.py for prescription-based booking
"""

import asyncio
import json
import base64
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
# Remove BaseToolException import as it doesn't exist in current LangChain
import structlog

# Import the prescription parser
from services.image_analysis.prescription_parser import (
    get_prescription_parser, 
    PrescriptionData,
    analyze_prescription_image
)

logger = structlog.get_logger()


async def analyze_prescription_image_tool_async(
    image_data_b64: str,
    image_format: str = "jpeg",
    customer_id: str = None
) -> Dict[str, Any]:
    """
    Analyze prescription image and extract medical test information.
    
    Args:
        image_data_b64: Base64 encoded image data
        image_format: Image format (jpeg, png, webp)
        customer_id: Customer identifier for tracking
        
    Returns:
        Structured prescription data with extracted information
    """
    try:
        logger.info("🔍 Starting prescription image analysis", 
                   customer_id=customer_id, image_format=image_format)
        
        # Decode base64 image data
        try:
            image_bytes = base64.b64decode(image_data_b64)
            logger.info("✅ Successfully decoded image", decoded_size=len(image_bytes))
        except Exception as e:
            logger.error("❌ Base64 decode failed", error=str(e))
            return {
                "success": False,
                "error": "invalid_image_data",
                "message": "Could not decode the image. Please make sure the image is properly uploaded.",
                "user_friendly_error": "Image format not supported. Please try uploading a clearer image."
            }
        
        # Analyze prescription image using Gemini-2.5-Pro
        prescription_data = await analyze_prescription_image(image_bytes, image_format)
        
        # Validate the extracted data
        parser = get_prescription_parser()
        validation_result = parser.validate_prescription_data(prescription_data)
        
        # Determine response based on extraction quality
        if prescription_data.confidence_score >= 0.7 and validation_result["is_valid"]:
            # High confidence, complete extraction
            return {
                "success": True,
                "extraction_quality": "excellent",
                "prescription_data": {
                    "patient_name": prescription_data.patient_name,
                    "age": prescription_data.age,
                    "gender": prescription_data.gender,
                    "prescribed_tests": prescription_data.prescribed_tests,
                    "doctor_name": prescription_data.doctor_name,
                    "hospital_clinic": prescription_data.hospital_clinic,
                    "prescription_date": prescription_data.prescription_date,
                    "additional_instructions": prescription_data.additional_instructions
                },
                "confidence_score": prescription_data.confidence_score,
                "missing_fields": validation_result["missing_critical"],
                "message": f"I found {len(prescription_data.prescribed_tests)} tests in your prescription. Let me help you book these tests.",
                "next_action": "confirm_booking" if validation_result["is_valid"] else "collect_missing_info"
            }
            
        elif prescription_data.confidence_score >= 0.4 and prescription_data.prescribed_tests:
            # Medium confidence, partial extraction
            return {
                "success": True,
                "extraction_quality": "partial",
                "prescription_data": {
                    "patient_name": prescription_data.patient_name,
                    "age": prescription_data.age,
                    "gender": prescription_data.gender,
                    "prescribed_tests": prescription_data.prescribed_tests,
                    "doctor_name": prescription_data.doctor_name,
                    "hospital_clinic": prescription_data.hospital_clinic,
                    "prescription_date": prescription_data.prescription_date,
                    "additional_instructions": prescription_data.additional_instructions
                },
                "confidence_score": prescription_data.confidence_score,
                "missing_fields": validation_result["missing_critical"],
                "message": f"I could identify {len(prescription_data.prescribed_tests)} tests from your prescription, but I need some additional information to complete the booking.",
                "next_action": "collect_missing_info"
            }
        
        elif prescription_data.prescribed_tests:
            # Low confidence but some tests found
            return {
                "success": True,
                "extraction_quality": "low",
                "prescription_data": {
                    "prescribed_tests": prescription_data.prescribed_tests,
                    "patient_name": prescription_data.patient_name,
                    "age": prescription_data.age,
                    "gender": prescription_data.gender
                },
                "confidence_score": prescription_data.confidence_score,
                "missing_fields": validation_result["missing_critical"],
                "message": f"I found some tests ({', '.join(prescription_data.prescribed_tests[:3])}) in your prescription, but the image quality makes it difficult to read all details. Could you help me confirm the information?",
                "next_action": "manual_verification"
            }
        
        else:
            # No usable information found
            return {
                "success": False,
                "extraction_quality": "failed",
                "error": "no_tests_found",
                "confidence_score": prescription_data.confidence_score,
                "message": "I couldn't identify any diagnostic tests in this prescription. This might be because the image is unclear, or it contains only medications. Could you either upload a clearer image or tell me which tests you'd like to book?",
                "user_friendly_error": "Unable to read prescription clearly",
                "next_action": "manual_input"
            }
        
    except Exception as e:
        logger.error("❌ Prescription image analysis failed", error=str(e), customer_id=customer_id)
        return {
            "success": False,
            "error": "analysis_failed",
            "message": "I'm having trouble analyzing your prescription image right now. Could you please tell me which tests you'd like to book, or try uploading the image again?",
            "user_friendly_error": "Technical issue with image analysis",
            "retry_suggested": True
        }


def analyze_prescription_image_tool_sync(
    image_data_b64: str,
    image_format: str = "jpeg",
    customer_id: str = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper for prescription image analysis.
    
    Args:
        image_data_b64: Base64 encoded image data
        image_format: Image format (jpeg, png, webp)
        customer_id: Customer identifier for tracking
        
    Returns:
        Structured prescription data with extracted information
    """
    import asyncio
    import threading
    
    # Get or create event loop in a thread-safe way
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # If we're in an async context, run in a thread to avoid blocking
        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(
                    analyze_prescription_image_tool_async(image_data_b64, image_format, customer_id)
                )
            finally:
                new_loop.close()
        
        # Run in a separate thread to avoid event loop conflicts
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
            
    except RuntimeError:
        # No event loop running, safe to create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                analyze_prescription_image_tool_async(image_data_b64, image_format, customer_id)
            )
        finally:
            loop.close()


# Create the tool using StructuredTool.from_function with both sync and async implementations
from langchain_core.tools import StructuredTool

analyze_prescription_image_tool = StructuredTool.from_function(
    func=analyze_prescription_image_tool_sync,
    coroutine=analyze_prescription_image_tool_async,
    name="analyze_prescription_image_tool",
    description="Analyze prescription image and extract medical test information using Gemini-2.5-Pro vision model. Returns structured data with patient info, prescribed tests, doctor details, and confidence score."
)


@tool
def confirm_prescription_booking(
    prescription_data: Dict[str, Any],
    customer_confirmation: str,
    additional_info: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Process user confirmation for prescription-based booking.
    
    Args:
        prescription_data: Extracted prescription information
        customer_confirmation: User's confirmation response
        additional_info: Any additional information provided by user
        
    Returns:
        Booking confirmation status and next steps
    """
    try:
        logger.info("📋 Processing prescription booking confirmation")
        
        confirmation_lower = customer_confirmation.lower()
        
        # Check for positive confirmation
        if any(word in confirmation_lower for word in ['yes', 'confirm', 'book', 'proceed', 'correct']):
            # Prepare data for order creation
            booking_data = {
                "confirmed": True,
                "prescription_based": True,
                "patient_name": prescription_data.get("patient_name"),
                "age": prescription_data.get("age"),
                "gender": prescription_data.get("gender"),
                "tests": prescription_data.get("prescribed_tests", []),
                "doctor_name": prescription_data.get("doctor_name"),
                "prescription_date": prescription_data.get("prescription_date")
            }
            
            # Merge additional info if provided
            if additional_info:
                booking_data.update(additional_info)
            
            return {
                "success": True,
                "confirmed": True,
                "booking_data": booking_data,
                "message": "Perfect! I'll help you book these tests. I'll need your phone number, PIN code, preferred date, payment method, and service preference (home collection or test center visit).",
                "next_action": "collect_booking_details"
            }
        
        elif any(word in confirmation_lower for word in ['no', 'wrong', 'incorrect', 'different']):
            return {
                "success": True,
                "confirmed": False,
                "message": "I understand the extracted information wasn't correct. Could you please tell me which tests you'd like to book and any other details I got wrong?",
                "next_action": "manual_correction"
            }
        
        else:
            # Unclear response, ask for clarification
            return {
                "success": True,
                "needs_clarification": True,
                "message": "I want to make sure I have the right information. Are the tests and details I found correct, or would you like to make any changes?",
                "next_action": "request_clear_confirmation"
            }
            
    except Exception as e:
        logger.error("Error processing prescription booking confirmation", error=str(e))
        return {
            "success": False,
            "error": "confirmation_processing_failed",
            "message": "Let me help you book these tests step by step. Which tests would you like to book?",
            "fallback_to_manual": True
        }


# REMOVED: format_prescription_summary tool - LLM now handles formatting intelligently
# The LLM can naturally format prescription data based on the raw prescription_data dict
# This eliminates 56 lines of redundant formatting code


# Helper function to integrate with existing workflow
def create_prescription_workflow_tools():
    """Create prescription-specific tools for the healthcare assistant workflow."""
    return [
        analyze_prescription_image_tool,
        confirm_prescription_booking
        # REMOVED: format_prescription_summary - LLM handles formatting naturally
    ]