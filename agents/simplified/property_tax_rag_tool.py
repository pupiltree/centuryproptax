"""
Enhanced Property Tax RAG Tool
Comprehensive Texas property tax knowledge system with legal citations and semantic search
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
    Enhanced property tax guidance using comprehensive Texas property tax knowledge base.

    Handles all property tax scenarios:
    - Exemption guidance: "homestead exemption", "senior citizen exemption"
    - Appeal processes: "property tax protest", "ARB hearing"
    - Assessment questions: "property valuation", "appraisal process"
    - Legal requirements: "filing deadlines", "required documentation"
    - Procedural guidance: "how to apply", "step-by-step process"

    Args:
        customer_query: What the customer is asking for
        property_type: Property type for targeted recommendations
        location: Property location for county-specific guidance
        property_concerns: Comma-separated concerns if any
        assessment_history: Relevant assessment history

    Returns:
        Comprehensive property tax guidance with legal citations and authority
    """
    try:
        logger.info("🏛️ Processing property tax guidance request",
                   query=customer_query, property_type=property_type, location=location)

        from services.vector_store.semantic_search import create_property_tax_search, SearchRequest, SearchType, SearchScope
        from services.knowledge_base.content_processor import get_content_processor

        # Initialize the enhanced property tax search system
        search_engine = await create_property_tax_search()

        # Determine search scope based on query content
        search_scope = SearchScope.ALL
        query_lower = customer_query.lower()

        if any(term in query_lower for term in ['exemption', 'homestead', 'disability', 'senior', 'veteran']):
            search_scope = SearchScope.EXEMPTIONS
        elif any(term in query_lower for term in ['protest', 'appeal', 'challenge', 'hearing', 'arb']):
            search_scope = SearchScope.APPEALS
        elif any(term in query_lower for term in ['form', 'application', 'document']):
            search_scope = SearchScope.FORMS
        elif any(term in query_lower for term in ['procedure', 'process', 'step', 'how to']):
            search_scope = SearchScope.PROCEDURES
        elif any(term in query_lower for term in ['statute', 'law', 'code', 'legal']):
            search_scope = SearchScope.STATUTES

        # Build enhanced search request
        search_request = SearchRequest(
            query=customer_query,
            search_type=SearchType.LEGAL_REASONING,
            search_scope=search_scope,
            max_results=8,
            include_reasoning=True,
            filter_by_authority=None,
            priority_concepts=[property_type] if property_type else None
        )

        # Execute comprehensive search
        search_results = await search_engine.search(search_request)

        if not search_results:
            return {
                "success": False,
                "message": "I couldn't find relevant information in our Texas property tax knowledge base. Could you please provide more specific details about your property tax question?",
                "guidance": [],
                "legal_citations": []
            }

        # Format results for customer guidance
        formatted_guidance = []
        legal_citations = []
        authorities = set()

        for result in search_results[:5]:  # Top 5 results
            doc = result.document
            metadata = doc.metadata

            # Format guidance entry
            guidance_entry = {
                "title": metadata.get('document_title', 'Property Tax Guidance'),
                "content_summary": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                "authority": metadata.get('authority', 'Texas'),
                "document_type": metadata.get('document_type', 'general'),
                "relevance_score": result.score,
                "legal_concepts": metadata.get('legal_concepts', []),
                "property_types": metadata.get('property_types', []),
                "citations": metadata.get('citations', [])
            }

            formatted_guidance.append(guidance_entry)

            # Collect legal citations
            if metadata.get('citations'):
                legal_citations.extend(metadata['citations'])

            # Track authorities
            if metadata.get('authority'):
                authorities.add(metadata['authority'])

        # Remove duplicate citations
        legal_citations = list(set(legal_citations))

        # Generate comprehensive response message
        primary_authority = next(iter(authorities)) if authorities else "Texas"

        message_parts = [
            f"Based on your question about '{customer_query}', here's guidance from Texas property tax law:"
        ]

        if property_type:
            message_parts.append(f"For {property_type} properties:")

        if location:
            message_parts.append(f"In {location}:")

        # Add key guidance points
        if formatted_guidance:
            top_guidance = formatted_guidance[0]
            message_parts.append(f"\n{top_guidance['content_summary']}")

            if top_guidance.get('legal_concepts'):
                concepts = ', '.join(top_guidance['legal_concepts'][:3])
                message_parts.append(f"\nThis relates to: {concepts}")

        # Add legal citations if available
        if legal_citations:
            citations_text = ', '.join(legal_citations[:3])
            message_parts.append(f"\nLegal basis: {citations_text}")

        message = ' '.join(message_parts)

        return {
            "success": True,
            "message": message,
            "guidance": formatted_guidance,
            "legal_citations": legal_citations,
            "primary_authority": primary_authority,
            "search_scope": search_scope.value,
            "total_results_analyzed": len(search_results),
            "confidence_level": "high" if search_results and search_results[0].score > 0.7 else "medium"
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


# Create the enhanced property tax RAG tool
property_tax_rag_tool = StructuredTool.from_function(
    func=property_tax_assessment_recommendation_sync,
    coroutine=property_tax_assessment_recommendation_async,
    name="property_tax_assessment_recommendation",
    description="""Comprehensive Texas property tax guidance tool with legal citations and semantic search.

Provides expert guidance for all property tax scenarios:
- Exemptions: "homestead exemption", "senior citizen exemption", "veteran exemption"
- Appeals: "property tax protest", "ARB hearing", "challenge assessment"
- Legal requirements: "filing deadlines", "required documentation", "protest process"
- Procedures: "how to apply", "step-by-step guidance", "appeal timeline"
- Assessments: "property valuation", "appraisal process", "market value"

Features:
- Real Texas property tax law data from comptroller.texas.gov
- Legal citations with authority verification
- County-specific guidance when location provided
- Property type-specific recommendations
- Step-by-step procedural guidance

Returns comprehensive guidance with legal basis and authoritative sources."""
)