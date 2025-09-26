"""
Property Document Analysis Tools for Property Tax Assistant
Integrates with form_context_tool for Microsoft Forms registration flow
"""

import asyncio
import json
import base64
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
import structlog

# Image analysis services removed - property document analysis capabilities disabled

logger = structlog.get_logger()


async def analyze_property_document_tool_async(
    image_data_b64: str,
    image_format: str = "jpeg",
    customer_id: str = None
) -> Dict[str, Any]:
    """
    Property document image analysis is not available in this system.
    Image analysis services have been removed.

    Args:
        image_data_b64: Base64 encoded image data
        image_format: Image format (jpeg, png, webp)
        customer_id: Customer identifier for tracking

    Returns:
        Error response indicating feature is not available
    """
    logger.info("❌ Property document image analysis not available", customer_id=customer_id)

    return {
        "success": False,
        "error": "feature_not_available",
        "message": "Image analysis for property documents is not currently available. Please provide property details through text instead.",
        "user_friendly_error": "Image analysis feature is not available. Please describe your property tax query in text.",
        "next_action": "manual_input"
    }


def analyze_property_document_tool_sync(
    image_data_b64: str,
    image_format: str = "jpeg",
    customer_id: str = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper for property document analysis.
    Returns error indicating feature is not available.

    Args:
        image_data_b64: Base64 encoded image data
        image_format: Image format (jpeg, png, webp)
        customer_id: Customer identifier for tracking

    Returns:
        Error response indicating feature is not available
    """
    import asyncio

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
                    analyze_property_document_tool_async(image_data_b64, image_format, customer_id)
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
                analyze_property_document_tool_async(image_data_b64, image_format, customer_id)
            )
        finally:
            loop.close()


# Create the tool using StructuredTool.from_function with both sync and async implementations
from langchain_core.tools import StructuredTool

analyze_property_document_tool = StructuredTool.from_function(
    func=analyze_property_document_tool_sync,
    coroutine=analyze_property_document_tool_async,
    name="analyze_property_document_tool",
    description="Property document image analysis is not available. This tool returns an error message indicating the feature has been removed."
)


@tool
def confirm_property_assessment_booking(
    property_data: Dict[str, Any],
    customer_confirmation: str,
    additional_info: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Process user confirmation for property assessment booking.
    Note: Since image analysis is disabled, this primarily handles manual property data.

    Args:
        property_data: Property information provided by user
        customer_confirmation: User's confirmation response
        additional_info: Any additional information provided by user

    Returns:
        Booking confirmation status and next steps
    """
    try:
        logger.info("📋 Processing property assessment booking confirmation")

        confirmation_lower = customer_confirmation.lower()

        # Check for positive confirmation
        if any(word in confirmation_lower for word in ['yes', 'confirm', 'book', 'proceed', 'correct']):
            # Prepare data for property assessment booking
            booking_data = {
                "confirmed": True,
                "property_based": True,
                "property_address": property_data.get("property_address"),
                "property_type": property_data.get("property_type"),
                "assessment_year": property_data.get("assessment_year"),
                "owner_name": property_data.get("owner_name"),
                "contact_details": property_data.get("contact_details")
            }

            # Merge additional info if provided
            if additional_info:
                booking_data.update(additional_info)

            return {
                "success": True,
                "confirmed": True,
                "booking_data": booking_data,
                "message": "Perfect! I'll help you with your property tax assessment. I'll need to confirm some details about your property and contact information.",
                "next_action": "collect_property_details"
            }

        elif any(word in confirmation_lower for word in ['no', 'wrong', 'incorrect', 'different']):
            return {
                "success": True,
                "confirmed": False,
                "message": "I understand the information wasn't correct. Could you please provide the correct property details?",
                "next_action": "manual_correction"
            }

        else:
            # Unclear response, ask for clarification
            return {
                "success": True,
                "needs_clarification": True,
                "message": "I want to make sure I have the right property information. Are the details I have correct, or would you like to make any changes?",
                "next_action": "request_clear_confirmation"
            }

    except Exception as e:
        logger.error("Error processing property assessment confirmation", error=str(e))
        return {
            "success": False,
            "error": "confirmation_processing_failed",
            "message": "Let me help you with your property tax inquiry step by step. Could you provide your property details?",
            "fallback_to_manual": True
        }


# Property tax document analysis tools for Century Property Tax
# Tools for processing property tax documents, assessments, and related paperwork


# Helper function to integrate with existing workflow
def create_property_document_workflow_tools():
    """Create property document tools for the property tax assistant workflow."""
    return [
        analyze_property_document_tool,
        confirm_property_assessment_booking
        # Note: Image analysis functionality has been removed - tools now handle text-based property data only
    ]