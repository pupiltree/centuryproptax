"""
Unified Property Tax RAG Tool
Replaces complex agentic RAG v2 with simple, powerful Google embeddings + LLM reasoning
"""

import asyncio
from typing import Dict, Any, List, Optional
from langchain_core.tools import StructuredTool
import structlog

logger = structlog.get_logger()


async def property_tax_assessment_recommendation_async(
    customer_query: str,
    property_type: Optional[str] = None,
    location: Optional[str] = None,
    property_concerns: Optional[str] = None,
    assessment_history: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unified property tax assessment recommendation using Google embeddings + LLM reasoning.

    Handles all scenarios:
    - Direct assessment names: "I want property valuation assessment"
    - Concern-based: "I think my property tax is too high"
    - General property tax: "tax appeal process", "property value review"
    - Property type/location specific recommendations

    Args:
        customer_query: What the customer is asking for
        property_type: Property type for appropriate recommendations
        location: Property location for targeted recommendations
        property_concerns: Comma-separated concerns if any
        assessment_history: Relevant assessment history

    Returns:
        Comprehensive property tax recommendations with reasoning
    """
    try:
        logger.info("🏢 Processing property tax assessment recommendation request",
                   query=customer_query, property_type=property_type, location=location)

        from services.vector_store.assessment_indexer import get_assessment_vector_store

        # Get the enhanced vector store with Google embeddings
        vector_store = await get_assessment_vector_store(use_google_embeddings=True)

        # Parse property concerns if provided as string
        concerns_list = []
        if property_concerns:
            concerns_list = [s.strip() for s in property_concerns.split(',') if s.strip()]

        # Use the advanced search with LLM reasoning
        result = await vector_store.search_and_reason_assessments(
            customer_query=customer_query,
            property_type=property_type,
            location=location,
            concerns=concerns_list if concerns_list else None,
            k=10  # Get top 10 for LLM analysis
        )
        
        if not result.get('success'):
            return {
                "success": False,
                "message": "I couldn't find any relevant assessments in our catalog. Could you please provide more specific information?",
                "recommendations": []
            }
        
        # Extract LLM analysis
        llm_analysis = result.get('llm_analysis', {})
        recommendations = llm_analysis.get('top_recommendations', [])
        
        # Format user-friendly response
        if recommendations:
            formatted_recommendations = []
            
            for rec in recommendations[:5]:  # Top 5 recommendations
                if isinstance(rec, dict):
                    # LLM-formatted recommendation
                    formatted_rec = {
                        "assessment_name": rec.get('assessment_name', 'Unknown Assessment'),
                        "assessment_code": rec.get('assessment_code', ''),
                        "property_tax_rationale": rec.get('property_tax_rationale', 'Recommended based on your query'),
                        "priority": rec.get('priority', 'medium'),
                        "price": rec.get('price', 0)
                    }
                else:
                    # Fallback to vector result format
                    formatted_rec = {
                        "assessment_name": rec.get('assessment_name', 'Unknown Assessment'),
                        "assessment_code": rec.get('assessment_code', ''),
                        "property_tax_rationale": f"Recommended for {customer_query.lower()}",
                        "priority": "medium",
                        "price": rec.get('price', 0)
                    }
                
                formatted_recommendations.append(formatted_rec)
            
            # Create user-friendly message
            assessment_names = [rec["assessment_name"] for rec in formatted_recommendations]

            if len(assessment_names) == 1:
                assessment_summary = assessment_names[0]
            elif len(assessment_names) == 2:
                assessment_summary = f"{assessment_names[0]} and {assessment_names[1]}"
            else:
                assessment_summary = f"{', '.join(assessment_names[:-1])}, and {assessment_names[-1]}"

            message = f"Based on your request '{customer_query}'"
            if property_type:
                message += f" and your property type ({property_type})"
            if concerns_list:
                message += f" and concerns ({', '.join(concerns_list)})"
            message += f", I recommend: {assessment_summary}."

            # Add LLM reasoning if available
            if llm_analysis.get('reasoning'):
                message += f"\n\nProperty tax insight: {llm_analysis['reasoning']}"
            
            return {
                "success": True,
                "message": message,
                "recommendations": formatted_recommendations,
                "property_tax_reasoning": llm_analysis.get('reasoning', ''),
                "additional_notes": llm_analysis.get('additional_notes', ''),
                "total_options_analyzed": result.get('vector_results_count', 0)
            }
        
        else:
            return {
                "success": False,
                "message": f"I couldn't find specific assessment recommendations for '{customer_query}'. Could you provide more details about what you're looking for?",
                "recommendations": []
            }

    except Exception as e:
        logger.error("❌ Property tax assessment recommendation failed", error=str(e), query=customer_query)
        return {
            "success": False,
            "message": "I'm having trouble processing your request right now. Could you please try asking about specific assessments or property concerns?",
            "error": str(e)
        }


def property_tax_assessment_recommendation_sync(
    customer_query: str,
    property_type: Optional[str] = None,
    location: Optional[str] = None,
    property_concerns: Optional[str] = None,
    assessment_history: Optional[str] = None
) -> Dict[str, Any]:
    """Synchronous wrapper for the property tax assessment recommendation."""
    import threading
    import concurrent.futures
    
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
                    property_tax_assessment_recommendation_async(
                        customer_query, property_type, location, property_concerns, assessment_history
                    )
                )
            finally:
                new_loop.close()
        
        # Run in a separate thread to avoid event loop conflicts
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
            
    except RuntimeError:
        # No event loop running, safe to create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                property_tax_assessment_recommendation_async(
                    customer_query, property_type, location, property_concerns, assessment_history
                )
            )
        finally:
            loop.close()


# Create the unified property tax RAG tool
property_tax_rag_tool = StructuredTool.from_function(
    func=property_tax_assessment_recommendation_sync,
    coroutine=property_tax_assessment_recommendation_async,
    name="property_tax_assessment_recommendation",
    description="""Unified property tax assessment recommendation tool using Google embeddings and LLM reasoning.

Handles all property tax assessment queries:
- Direct assessment requests: "I want property valuation", "tax appeal assessment"
- Concern-based: "My property tax is too high", "assessment seems unfair"
- General property tax: "property value review", "tax calculation analysis"
- Property type/location specific recommendations

Returns intelligent property tax recommendations with professional reasoning."""
)