"""
Test Catalog Vector Store Indexer
Creates and manages vector embeddings for seeded test data following LangGraph Agentic RAG patterns.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from pathlib import Path

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_core.embeddings import DeterministicFakeEmbedding
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path

from services.persistence.database import get_db_session
from services.persistence.repositories import TestCatalogRepository

logger = structlog.get_logger()

class TestCatalogVectorStore:
    """Vector store for test catalog data following LangGraph Agentic RAG patterns with ChromaDB persistence."""
    
    def __init__(self, persist_directory: str = "./chroma_db", use_google_embeddings: bool = True):
        # Initialize logger first
        self.logger = logger
        self.persist_directory = Path(persist_directory)
        self.collection_name = "krishna_test_catalog"
        self.vectorstore: Optional[Chroma] = None
        self.retriever = None
        
        # Use Google embeddings for better semantic understanding, fallback to fake for testing
        if use_google_embeddings:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                import os
                self.embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001",
                    google_api_key=os.getenv("GOOGLE_API_KEY")
                )
                self.logger.info("✅ Using Google embeddings for semantic understanding")
            except Exception as e:
                self.logger.warning(f"⚠️ Google embeddings failed, falling back to deterministic: {e}")
                self.embeddings = DeterministicFakeEmbedding(size=384)
        else:
            # Use deterministic fake embeddings for development/testing
            self.embeddings = DeterministicFakeEmbedding(size=384)
            self.logger.info("🧪 Using deterministic fake embeddings for testing")
        
        # Ensure persist directory exists
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
    async def create_test_documents(self) -> List[Document]:
        """Create LangChain Document objects from seeded test data with rich metadata."""
        
        self.logger.info("📚 Loading seeded test data for vector indexing")
        
        async with get_db_session() as session:
            test_repo = TestCatalogRepository(session)
            # Get all available tests using search with empty query
            all_tests = await test_repo.search_tests(query="", available_only=True, limit=1000)
            
            documents = []
            
            for test in all_tests:
                # Create rich content for each test following RAG best practices
                test_name = test.name or "Unknown Test"
                description = test.description or "No description available"
                sample_type = test.sample_type or "Not specified"
                category = test.category or "General"
                
                # Create comprehensive medical content - let Google embeddings handle semantic understanding
                conditions_text = test.conditions_recommended_for or ""
                
                # Pure semantic content for Google embeddings - no keyword-based matching
                content = f"""Test Name: {test_name}
Description: {description}
Category: {category}
Sample Type: {sample_type}
Price: ₹{test.price}
Discounted Price: ₹{test.discounted_price or test.price}
Fasting Required: {'Yes' if test.fasting_required else 'No'}
Home Collection Available: {'Yes' if test.home_collection else 'No'}

Medical Information:
This test is used to assess {category.lower()} health conditions.
{description}

Recommended For: {conditions_text}

Clinical Context: This {sample_type.lower()} test called {test_name} is used to {description.lower()}. It belongs to the {category.lower()} category and helps in diagnosis, monitoring, and screening of relevant health conditions.
Sample collection: {sample_type}
{'Requires fasting' if test.fasting_required else 'No fasting required'}
"""

                # Simple metadata - trust Google embeddings for semantic matching
                metadata = {
                    "test_code": test.test_code,
                    "test_name": test_name,
                    "category": category,
                    "sample_type": sample_type,
                    "price": float(test.price),
                    "discounted_price": float(test.discounted_price) if test.discounted_price else float(test.price),
                    "fasting_required": test.fasting_required,
                    "home_collection": test.home_collection,
                    "available": test.available,
                    "type": "medical_test",
                    "indexed_at": datetime.now().isoformat()
                }
                
                doc = Document(
                    page_content=content,
                    metadata=metadata
                )
                documents.append(doc)
            
            self.logger.info(f"📋 Created {len(documents)} test documents for vector indexing")
            return documents
    
    def _generate_test_synonyms(self, test_name: str, test_code: str) -> List[str]:
        """Generate comprehensive medical synonyms and abbreviations for better matching."""
        synonyms = [test_name.lower(), test_code.lower()] if test_name and test_code else []
        
        # Enhanced medical test synonyms with more comprehensive mapping
        synonym_map = {
            "hba1c": ["hemoglobin a1c", "glycated hemoglobin", "a1c test", "diabetes test", "hb a1c"],
            "cbc": ["complete blood count", "full blood count", "blood count", "hemogram", "cbc test"],
            "glu_f": ["fasting glucose", "fasting blood sugar", "fbs", "blood sugar fasting", "glucose fasting"],
            "ppbs": ["post prandial blood sugar", "after meal glucose", "post meal sugar", "pp glucose"],
            "hla_b27": ["hla b27", "hla-b27", "hlab27", "ankylosing spondylitis test", "hla b 27", "hla b27 pcr", "hla b27 by pcr method"],
            "mri_dl_spine": ["mri dl spine", "mri d l spine", "mri dorsolumbar spine", "mri of dl spine", "mri of d l spine", "mri dorsal lumbar spine", "dl spine mri"],
            "mri_si_joints": ["mri si joints", "mri of si joints", "si joint mri", "sacroiliac joint mri", "si joints imaging"],
            "mri": ["magnetic resonance imaging", "mri scan", "mri imaging"],
            "tsh": ["thyroid stimulating hormone", "thyroid test", "tsh test"],
            "cpeptide": ["c peptide", "c-peptide", "cpeptide test", "connecting peptide"],
            "insulin": ["insulin test", "insulin level", "serum insulin"],
            "lipid": ["cholesterol test", "lipid profile", "cardiac risk assessment"]
        }
        
        # Add specific synonyms with partial matching
        test_lower = test_name.lower() if test_name else ""
        code_lower = test_code.lower() if test_code else ""
        
        for key, values in synonym_map.items():
            if (key in code_lower or key in test_lower or 
                any(synonym in test_lower for synonym in values[:2])):  # Check first 2 synonyms
                synonyms.extend(values)
        
        # Add word variations and common abbreviations
        if test_name:
            words = test_name.lower().split()
            for word in words:
                if len(word) > 3:  # Only meaningful words
                    synonyms.append(word)
        
        return list(set(synonyms))  # Remove duplicates
    
    def _extract_medical_keywords(self, test_name: str, description: str) -> List[str]:
        """Extract medical keywords for better search."""
        test_name = test_name or ""
        description = description or ""
        text = f"{test_name} {description}".lower()
        
        medical_keywords = []
        
        # Common medical terms
        medical_terms = [
            "diabetes", "blood sugar", "glucose", "insulin",
            "thyroid", "hormone", "tsh", "t3", "t4",
            "cholesterol", "lipid", "cardiac", "heart",
            "hemoglobin", "anemia", "iron", "blood",
            "kidney", "liver", "function", "enzyme",
            "infection", "inflammation", "immunity",
            "vitamin", "mineral", "deficiency",
            "cancer", "tumor", "marker", "screening"
        ]
        
        for term in medical_terms:
            if term in text:
                medical_keywords.append(term)
        
        return medical_keywords
    
    def _generate_medical_synonyms(self, test_name: str, description: str, category: str) -> List[str]:
        """Generate medical synonyms for better semantic matching."""
        test_name_lower = test_name.lower()
        synonyms = []
        
        # Medical synonym mappings
        medical_synonyms = {
            "glucose": ["blood sugar", "sugar level", "glycemia"],
            "diabetes": ["diabetic", "dm", "blood sugar disorder"],
            "thyroid": ["tsh", "t3", "t4", "thyroid function"],
            "cholesterol": ["lipid", "lipid profile", "cholesterol panel"],
            "hemoglobin": ["hb", "hemoglobin level", "blood count"],
            "insulin": ["insulin level", "insulin test", "hormone test"],
            "liver": ["hepatic", "liver function", "lft"],
            "kidney": ["renal", "kidney function", "rft"],
            "cardiac": ["heart", "cardio", "cardiac function"],
            "hba1c": ["glycated hemoglobin", "glycohemoglobin", "diabetes control"],
            "c-peptide": ["cpeptide", "c peptide", "insulin production"]
        }
        
        # Find synonyms based on test name
        for key, values in medical_synonyms.items():
            if key in test_name_lower:
                synonyms.extend(values)
        
        # Add category-specific synonyms
        if category.lower() == "diabetes":
            synonyms.extend(["blood sugar", "glucose", "diabetic test", "sugar level"])
        elif category.lower() == "thyroid":
            synonyms.extend(["thyroid function", "hormone test", "endocrine"])
        elif category.lower() == "cardiac":
            synonyms.extend(["heart test", "cardiovascular", "cardiac function"])
        
        return list(set(synonyms))
    
    def _extract_medical_conditions(self, conditions_text) -> List[str]:
        """Extract medical conditions from conditions_recommended_for field."""
        if not conditions_text:
            return []
        
        # Handle both string and list inputs
        if isinstance(conditions_text, list):
            return [str(item) for item in conditions_text if item]
        
        if not str(conditions_text).strip():
            return []
        
        # Parse JSON-like conditions or simple text
        conditions_str = str(conditions_text)
        try:
            import json
            if conditions_str.startswith('[') or conditions_str.startswith('{'):
                # Try to parse JSON
                conditions_data = json.loads(conditions_str)
                if isinstance(conditions_data, list):
                    return conditions_data
                elif isinstance(conditions_data, dict):
                    return list(conditions_data.values())
        except:
            pass
        
        # For simple text, just return as is - let Google embeddings handle semantic matching
        return [conditions_str.strip()] if conditions_str.strip() else []
    
    def _map_test_to_conditions(self, test_code: str, category: str) -> List[str]:
        """Map tests to medical conditions they help diagnose."""
        condition_map = {
            "hba1c": ["diabetes", "prediabetes", "blood sugar control"],
            "glu_f": ["diabetes", "hypoglycemia", "metabolic disorders"],
            "tsh": ["hypothyroidism", "hyperthyroidism", "thyroid disorders"],
            "cbc": ["anemia", "infection", "blood disorders", "immune system"],
            "lipid": ["heart disease", "cholesterol", "cardiovascular risk"],
            "hla_b27": ["ankylosing spondylitis", "autoimmune", "joint pain"],
            "liver": ["hepatitis", "liver disease", "jaundice"],
            "kidney": ["kidney disease", "urinary tract", "renal function"]
        }
        
        conditions = [category.lower()]
        
        for key, values in condition_map.items():
            if key in test_code.lower():
                conditions.extend(values)
        
        return list(set(conditions))
    
    async def build_vector_store(self, chunk_size: int = 500, chunk_overlap: int = 50, force_rebuild: bool = False):
        """Build persistent ChromaDB vector store following LangGraph Agentic RAG patterns."""
        
        self.logger.info("🔧 Building persistent ChromaDB vector store for test catalog")
        
        # Check if ChromaDB collection already exists and has data
        try:
            existing_vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=str(self.persist_directory)
            )
            
            # Check if collection has data
            if not force_rebuild and len(existing_vectorstore.get()["ids"]) > 0:
                self.logger.info(f"📋 Found existing ChromaDB collection with {len(existing_vectorstore.get()['ids'])} documents")
                self.vectorstore = existing_vectorstore
                self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
                self.logger.info("✅ Loaded existing ChromaDB vector store")
                return self.vectorstore
                
        except Exception as e:
            self.logger.info(f"📝 Creating new ChromaDB collection: {e}")
        
        # Create documents from seeded test data
        documents = await self.create_test_documents()
        
        # Split documents for better retrieval (following LangGraph patterns)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        doc_splits = text_splitter.split_documents(documents)
        
        self.logger.info(f"📄 Split {len(documents)} documents into {len(doc_splits)} chunks")
        
        # Create persistent ChromaDB vector store
        self.vectorstore = Chroma.from_documents(
            documents=doc_splits,
            embedding=self.embeddings,
            collection_name=self.collection_name,
            persist_directory=str(self.persist_directory)
        )
        
        # Create retriever for agentic RAG
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 5}  # Return top 5 most relevant tests
        )
        
        self.logger.info(f"💾 ChromaDB collection persisted to: {self.persist_directory}")
        self.logger.info("✅ Persistent ChromaDB vector store built successfully")
        return self.vectorstore
    
    async def search_tests(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Search for tests using vector similarity."""
        
        if not self.retriever:
            await self.build_vector_store()
        
        # Retrieve relevant documents
        docs = self.retriever.invoke(query)
        
        results = []
        for doc in docs[:k]:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "test_code": doc.metadata.get("test_code"),
                "test_name": doc.metadata.get("test_name"),
                "price": doc.metadata.get("price"),
                "category": doc.metadata.get("category")
            })
        
        return results
    
    async def search_and_reason_tests(
        self, 
        customer_query: str, 
        symptoms: Optional[List[str]] = None,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        k: int = 10
    ) -> Dict[str, Any]:
        """
        Advanced test search with LLM medical reasoning.
        
        1. Vector search returns top-10 similar tests
        2. LLM analyzes based on symptoms, age, gender 
        3. Returns intelligently ranked recommendations
        """
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Step 1: Get top-10 vector similarity results
        vector_results = await self.search_tests(customer_query, k=k)
        
        if not vector_results:
            return {
                "success": False,
                "message": "No relevant tests found in our catalog.",
                "recommendations": []
            }
        
        # Step 2: Prepare context for LLM reasoning
        patient_context = []
        if age:
            patient_context.append(f"Age: {age} years")
        if gender:
            patient_context.append(f"Gender: {gender}")
        if symptoms:
            patient_context.append(f"Symptoms: {', '.join(symptoms)}")
        
        patient_info = " | ".join(patient_context) if patient_context else "No specific patient information provided"
        
        # Format test options for LLM
        test_options = []
        for i, test in enumerate(vector_results, 1):
            test_options.append(
                f"{i}. {test['test_name']} ({test.get('category', 'General')})\n"
                f"   Price: ₹{test.get('price', 0)}\n"
                f"   Sample: {test.get('sample_type', 'Not specified')}\n"
                f"   Fasting: {'Required' if test.get('fasting_required') else 'Not required'}"
            )
        
        # Step 3: LLM medical reasoning
        try:
            import os
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=0.1,  # Low temperature for consistent medical recommendations
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        except Exception as e:
            # Fallback for credential issues - return vector results with basic analysis
            self.logger.warning(f"LLM unavailable, using vector-only results: {e}")
            return {
                "success": True,
                "customer_query": customer_query,
                "patient_info": patient_info,
                "vector_results_count": len(vector_results),
                "llm_analysis": {
                    "reasoning": f"Based on vector search for '{customer_query}', these tests are most relevant.",
                    "top_recommendations": [
                        {
                            "test_name": test['test_name'],
                            "test_code": test.get('test_code', ''),
                            "medical_rationale": f"Recommended based on semantic similarity to '{customer_query}'",
                            "priority": "medium",
                            "price": test.get('price', 0)
                        } for test in vector_results[:5]
                    ],
                    "additional_notes": "LLM analysis unavailable - using vector search results only"
                },
                "all_vector_results": vector_results,
                "llm_fallback": True
            }
        
        reasoning_prompt = f"""You are a medical assistant helping recommend diagnostic tests based on vector search results.

CUSTOMER QUERY: "{customer_query}"
PATIENT INFO: {patient_info}

TOP 10 VECTOR SEARCH RESULTS:
{chr(10).join(test_options)}

TASK: Analyze these test options and provide intelligent medical recommendations.

ANALYSIS CRITERIA:
1. Relevance to customer query
2. Appropriateness for patient age/gender
3. Diagnostic value for mentioned symptoms
4. Cost-effectiveness 
5. Medical best practices

RESPONSE FORMAT (JSON):
{{
    "reasoning": "Brief medical explanation of your analysis",
    "top_recommendations": [
        {{
            "rank": 1,
            "test_name": "Test Name",
            "test_code": "TEST_CODE",
            "medical_rationale": "Why this test is recommended",
            "priority": "high/medium/low",
            "price": 000
        }}
    ],
    "additional_notes": "Any additional medical guidance"
}}

Recommend 3-5 most appropriate tests. Focus on medical accuracy and patient safety.
"""
        
        try:
            response = await llm.ainvoke(reasoning_prompt)
            
            # Parse LLM response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                llm_analysis = json.loads(json_match.group())
            else:
                # Fallback if JSON parsing fails
                llm_analysis = {
                    "reasoning": "Vector search completed successfully",
                    "top_recommendations": vector_results[:3],
                    "additional_notes": "Standard test recommendations based on search query"
                }
            
            return {
                "success": True,
                "customer_query": customer_query,
                "patient_info": patient_info,
                "vector_results_count": len(vector_results),
                "llm_analysis": llm_analysis,
                "all_vector_results": vector_results  # For debugging/transparency
            }
            
        except Exception as e:
            self.logger.error(f"LLM reasoning failed: {e}")
            # Fallback to vector results only
            return {
                "success": True,
                "customer_query": customer_query,
                "patient_info": patient_info,
                "vector_results_count": len(vector_results),
                "llm_analysis": {
                    "reasoning": "LLM analysis unavailable, providing vector search results",
                    "top_recommendations": vector_results[:5],
                    "additional_notes": "Please consult with healthcare provider for personalized recommendations"
                },
                "all_vector_results": vector_results,
                "llm_error": str(e)
            }
    
    def get_retriever(self):
        """Get the retriever for agentic RAG system."""
        return self.retriever
    
    def clear_collection(self):
        """Clear the ChromaDB collection and force rebuild."""
        try:
            if self.vectorstore:
                # Delete the collection
                self.vectorstore.delete_collection()
                self.logger.info(f"🗑️ Cleared ChromaDB collection: {self.collection_name}")
            
            # Reset vectorstore
            self.vectorstore = None
            self.retriever = None
            
        except Exception as e:
            self.logger.error(f"Failed to clear collection: {e}")
    
    async def refresh_from_database(self):
        """Force refresh vector store from database (clears existing data)."""
        self.logger.info("🔄 Refreshing vector store from database")
        self.clear_collection()
        await self.build_vector_store(force_rebuild=True)
        self.logger.info("✅ Vector store refreshed from database")
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the ChromaDB collection."""
        if not self.vectorstore:
            return {"status": "not_initialized", "document_count": 0}
        
        try:
            collection_data = self.vectorstore.get()
            return {
                "status": "initialized",
                "collection_name": self.collection_name,
                "persist_directory": str(self.persist_directory),
                "document_count": len(collection_data["ids"]),
                "embedding_function": type(self.embeddings).__name__
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Global instance for reuse
_vector_store_instance = None

async def get_test_vector_store(use_google_embeddings: bool = True) -> TestCatalogVectorStore:
    """Get singleton instance of test catalog vector store."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = TestCatalogVectorStore(use_google_embeddings=use_google_embeddings)
        await _vector_store_instance.build_vector_store()
    return _vector_store_instance

async def initialize_test_vector_store():
    """Initialize the test catalog vector store on startup."""
    logger.info("🚀 Initializing test catalog vector store")
    vector_store = await get_test_vector_store()
    logger.info("✅ Test catalog vector store initialized")
    return vector_store

if __name__ == "__main__":
    # Test the vector store
    async def test_vector_store():
        print("Testing Test Catalog Vector Store")
        
        vector_store = await get_test_vector_store()
        
        # Test searches
        queries = [
            "diabetes blood sugar test",
            "HbA1c hemoglobin",
            "thyroid function",
            "complete blood count",
            "heart disease cholesterol"
        ]
        
        for query in queries:
            print(f"\n🔍 Query: '{query}'")
            results = await vector_store.search_tests(query, k=3)
            for result in results:
                print(f"  ✅ {result['test_name']} ({result['test_code']}) - ₹{result['price']}")
    
    asyncio.run(test_vector_store())