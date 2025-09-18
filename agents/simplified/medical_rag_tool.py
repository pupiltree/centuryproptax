"""
Unified Medical RAG Tool
Replaces complex agentic RAG v2 with simple, powerful Google embeddings + LLM reasoning
"""

import asyncio
from typing import Dict, Any, List, Optional
from langchain_core.tools import StructuredTool
import structlog

logger = structlog.get_logger()


async def medical_test_recommendation_async(
    customer_query: str,
    age: Optional[int] = None,
    gender: Optional[str] = None,
    symptoms: Optional[str] = None,
    medical_history: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unified medical test recommendation using Google embeddings + LLM reasoning.
    
    Handles all scenarios:
    - Direct test names: "I want HbA1c test"
    - Symptom-based: "I have fatigue and frequent urination" 
    - General health: "diabetes screening", "blood sugar check"
    - Age/demographic specific recommendations
    
    Args:
        customer_query: What the customer is asking for
        age: Patient age for appropriate recommendations
        gender: Patient gender for targeted recommendations  
        symptoms: Comma-separated symptoms if any
        medical_history: Relevant medical history
        
    Returns:
        Comprehensive medical recommendations with reasoning
    """
    try:
        logger.info("🩺 Processing medical test recommendation request", 
                   query=customer_query, age=age, gender=gender)
        
        from services.vector_store.test_indexer import get_test_vector_store
        
        # Get the enhanced vector store with Google embeddings
        vector_store = await get_test_vector_store(use_google_embeddings=True)
        
        # Parse symptoms if provided as string
        symptoms_list = []
        if symptoms:
            symptoms_list = [s.strip() for s in symptoms.split(',') if s.strip()]
        
        # Use the advanced search with LLM reasoning
        result = await vector_store.search_and_reason_tests(
            customer_query=customer_query,
            age=age,
            gender=gender,
            symptoms=symptoms_list if symptoms_list else None,
            k=10  # Get top 10 for LLM analysis
        )
        
        if not result.get('success'):
            return {
                "success": False,
                "message": "I couldn't find any relevant tests in our catalog. Could you please provide more specific information?",
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
                        "test_name": rec.get('test_name', 'Unknown Test'),
                        "test_code": rec.get('test_code', ''),
                        "medical_rationale": rec.get('medical_rationale', 'Recommended based on your query'),
                        "priority": rec.get('priority', 'medium'),
                        "price": rec.get('price', 0)
                    }
                else:
                    # Fallback to vector result format
                    formatted_rec = {
                        "test_name": rec.get('test_name', 'Unknown Test'),
                        "test_code": rec.get('test_code', ''),
                        "medical_rationale": f"Recommended for {customer_query.lower()}",
                        "priority": "medium",
                        "price": rec.get('price', 0)
                    }
                
                formatted_recommendations.append(formatted_rec)
            
            # Create user-friendly message
            test_names = [rec["test_name"] for rec in formatted_recommendations]
            
            if len(test_names) == 1:
                test_summary = test_names[0]
            elif len(test_names) == 2:
                test_summary = f"{test_names[0]} and {test_names[1]}"
            else:
                test_summary = f"{', '.join(test_names[:-1])}, and {test_names[-1]}"
            
            message = f"Based on your request '{customer_query}'"
            if age:
                message += f" and your age ({age})"
            if symptoms_list:
                message += f" and symptoms ({', '.join(symptoms_list)})"
            message += f", I recommend: {test_summary}."
            
            # Add LLM reasoning if available
            if llm_analysis.get('reasoning'):
                message += f"\n\nMedical insight: {llm_analysis['reasoning']}"
            
            return {
                "success": True,
                "message": message,
                "recommendations": formatted_recommendations,
                "medical_reasoning": llm_analysis.get('reasoning', ''),
                "additional_notes": llm_analysis.get('additional_notes', ''),
                "total_options_analyzed": result.get('vector_results_count', 0)
            }
        
        else:
            return {
                "success": False,
                "message": f"I couldn't find specific test recommendations for '{customer_query}'. Could you provide more details about what you're looking for?",
                "recommendations": []
            }
            
    except Exception as e:
        logger.error("❌ Medical test recommendation failed", error=str(e), query=customer_query)
        return {
            "success": False,
            "message": "I'm having trouble processing your request right now. Could you please try asking about specific tests or symptoms?",
            "error": str(e)
        }


def medical_test_recommendation_sync(
    customer_query: str,
    age: Optional[int] = None,
    gender: Optional[str] = None,
    symptoms: Optional[str] = None,
    medical_history: Optional[str] = None
) -> Dict[str, Any]:
    """Synchronous wrapper for the medical test recommendation."""
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
                    medical_test_recommendation_async(
                        customer_query, age, gender, symptoms, medical_history
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
                medical_test_recommendation_async(
                    customer_query, age, gender, symptoms, medical_history
                )
            )
        finally:
            loop.close()


# Create the unified medical RAG tool
medical_rag_tool = StructuredTool.from_function(
    func=medical_test_recommendation_sync,
    coroutine=medical_test_recommendation_async,
    name="medical_test_recommendation",
    description="""Unified medical test recommendation tool using Google embeddings and LLM reasoning.
    
Handles all medical test queries:
- Direct test requests: "I want diabetes test", "HbA1c test"
- Symptom-based: "I have fatigue and thirst", "frequent urination"  
- General screening: "blood sugar check", "diabetes screening"
- Age/gender specific recommendations

Returns intelligent medical recommendations with clinical reasoning."""
)