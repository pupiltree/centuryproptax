"""
Legal Document Vector Store Indexer
Enhanced vector store specifically designed for Texas property tax legal documents
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import structlog
from pathlib import Path

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain.text_splitter import RecursiveCharacterTextSplitter

from services.data_acquisition.document_processor import ProcessedDocument

logger = structlog.get_logger()

class LegalDocumentVectorStore:
    """Enhanced vector store for Texas property tax legal documents"""

    def __init__(self, persist_directory: str = "./chroma_db_legal", use_google_embeddings: bool = True):
        self.logger = logger
        self.persist_directory = Path(persist_directory)
        self.collection_name = "texas_property_tax_legal"
        self.vectorstore: Optional[Chroma] = None
        self.retriever = None

        # Use Google embeddings optimized for legal content
        if use_google_embeddings:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                import os
                self.embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001",
                    google_api_key=os.getenv("GOOGLE_API_KEY")
                )
                self.logger.info("✅ Using Google embeddings for legal document understanding")
            except Exception as e:
                self.logger.warning(f"⚠️ Google embeddings failed, falling back to deterministic: {e}")
                self.embeddings = DeterministicFakeEmbedding(size=384)
        else:
            self.embeddings = DeterministicFakeEmbedding(size=384)
            self.logger.info("🧪 Using deterministic fake embeddings for testing")

        # Ensure persist directory exists
        self.persist_directory.mkdir(parents=True, exist_ok=True)

    async def index_processed_documents(self, processed_docs: List[ProcessedDocument]) -> int:
        """Index processed legal documents into the vector store"""
        self.logger.info(f"🏛️ Indexing {len(processed_docs)} legal documents")

        documents = []
        for processed_doc in processed_docs:
            # Create documents for each chunk
            doc_documents = await self._create_documents_from_processed(processed_doc)
            documents.extend(doc_documents)

        # Initialize vector store if not exists
        if self.vectorstore is None:
            await self._initialize_vectorstore()

        # Add documents to vector store
        if documents:
            await self._add_documents_to_store(documents)

        self.logger.info(f"✅ Successfully indexed {len(documents)} document chunks")
        return len(documents)

    async def _create_documents_from_processed(self, processed_doc: ProcessedDocument) -> List[Document]:
        """Create LangChain Document objects from processed document chunks"""
        documents = []

        base_metadata = {
            # Document identification
            'source_url': processed_doc.original_doc.url,
            'document_title': processed_doc.original_doc.title,
            'document_type': processed_doc.original_doc.document_type,
            'authority': processed_doc.original_doc.authority,
            'jurisdiction': processed_doc.original_doc.jurisdiction,
            'document_hash': processed_doc.original_doc.hash,

            # Legal metadata
            'effective_date': processed_doc.original_doc.effective_date.isoformat() if processed_doc.original_doc.effective_date else None,
            'section_number': processed_doc.original_doc.section_number,
            'citations': processed_doc.original_doc.citations,

            # Content metadata
            'quality_score': processed_doc.quality_score,
            'word_count': processed_doc.metadata.get('word_count', 0),
            'legal_concepts': processed_doc.metadata.get('legal_concepts', []),
            'property_types': processed_doc.metadata.get('property_types', []),
            'tax_concepts': processed_doc.metadata.get('tax_concepts', []),
            'deadlines': processed_doc.metadata.get('deadlines', []),
            'fee_amounts': processed_doc.metadata.get('fee_amounts', []),

            # Processing metadata
            'processed_at': processed_doc.metadata.get('processed_at'),
            'processing_notes': processed_doc.processing_notes
        }

        # Create a document for each chunk
        for i, chunk in enumerate(processed_doc.chunks):
            if not chunk.strip():
                continue

            # Enhanced content with legal context
            enhanced_content = self._enhance_chunk_content(chunk, processed_doc)

            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                'chunk_index': i,
                'total_chunks': len(processed_doc.chunks),
                'chunk_content_length': len(chunk)
            })

            doc = Document(
                page_content=enhanced_content,
                metadata=chunk_metadata
            )
            documents.append(doc)

        return documents

    def _enhance_chunk_content(self, chunk: str, processed_doc: ProcessedDocument) -> str:
        """Enhance chunk content with legal context for better embeddings"""
        # Add document context to help with semantic understanding
        context_parts = [
            f"Document: {processed_doc.original_doc.title}",
            f"Authority: {processed_doc.original_doc.authority}",
            f"Type: {processed_doc.original_doc.document_type}"
        ]

        if processed_doc.original_doc.section_number:
            context_parts.append(f"Section: {processed_doc.original_doc.section_number}")

        # Add legal concepts context
        legal_concepts = processed_doc.metadata.get('legal_concepts', [])
        if legal_concepts:
            context_parts.append(f"Legal concepts: {', '.join(legal_concepts[:5])}")

        # Add property types context
        property_types = processed_doc.metadata.get('property_types', [])
        if property_types:
            context_parts.append(f"Property types: {', '.join(property_types[:3])}")

        context = " | ".join(context_parts)

        # Enhanced content format for better semantic understanding
        enhanced_content = f"""Legal Document Context: {context}

Content:
{chunk}

Legal Domain: Texas Property Tax Law
Jurisdiction: {processed_doc.original_doc.jurisdiction}
Document Classification: {processed_doc.original_doc.document_type}"""

        return enhanced_content

    async def _initialize_vectorstore(self):
        """Initialize the Chroma vector store"""
        try:
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=str(self.persist_directory)
            )

            # Create retriever with legal-specific configuration
            self.retriever = self.vectorstore.as_retriever(
                search_type="mmr",  # Maximal Marginal Relevance for diversity
                search_kwargs={
                    "k": 10,  # Return top 10 results
                    "fetch_k": 20,  # Fetch 20 candidates for MMR
                    "lambda_mult": 0.7  # Balance relevance vs diversity
                }
            )

            self.logger.info("✅ Legal document vector store initialized")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize vector store: {e}")
            raise

    async def _add_documents_to_store(self, documents: List[Document]):
        """Add documents to the vector store"""
        try:
            # Add documents in batches to avoid memory issues
            batch_size = 50
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                self.vectorstore.add_documents(batch)

                self.logger.info(f"📝 Added batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")

            # Persist the vector store
            self.vectorstore.persist()

        except Exception as e:
            self.logger.error(f"❌ Failed to add documents to vector store: {e}")
            raise

    async def search_legal_documents(self, query: str, document_type: Optional[str] = None,
                                   authority: Optional[str] = None, k: int = 5) -> List[Document]:
        """Search legal documents with optional filters"""
        if self.vectorstore is None:
            await self._initialize_vectorstore()

        try:
            # Enhanced query with legal context
            enhanced_query = self._enhance_search_query(query, document_type, authority)

            # Perform similarity search
            results = self.vectorstore.similarity_search(
                enhanced_query,
                k=k,
                filter=self._build_search_filter(document_type, authority)
            )

            self.logger.info(f"🔍 Legal search returned {len(results)} results for: {query}")
            return results

        except Exception as e:
            self.logger.error(f"❌ Legal document search failed: {e}")
            return []

    def _enhance_search_query(self, query: str, document_type: Optional[str] = None,
                            authority: Optional[str] = None) -> str:
        """Enhance search query with legal context"""
        enhanced_parts = [query]

        if document_type:
            enhanced_parts.append(f"document type: {document_type}")

        if authority:
            enhanced_parts.append(f"authority: {authority}")

        # Add property tax context
        enhanced_parts.append("Texas property tax law")

        return " ".join(enhanced_parts)

    def _build_search_filter(self, document_type: Optional[str] = None,
                           authority: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Build metadata filter for search"""
        filters = {}

        if document_type:
            filters['document_type'] = document_type

        if authority:
            filters['authority'] = authority

        return filters if filters else None

    async def search_with_legal_reasoning(self, query: str, k: int = 10) -> Dict[str, Any]:
        """Advanced search with LLM reasoning for legal queries"""
        try:
            # Get relevant documents
            documents = await self.search_legal_documents(query, k=k)

            if not documents:
                return {
                    'success': False,
                    'message': 'No relevant legal documents found',
                    'documents': []
                }

            # Organize documents by type and authority
            organized_docs = self._organize_documents_by_type(documents)

            # Use LLM to reason about the legal context
            legal_analysis = await self._analyze_legal_context(query, documents)

            return {
                'success': True,
                'query': query,
                'documents': documents,
                'organized_by_type': organized_docs,
                'legal_analysis': legal_analysis,
                'total_results': len(documents)
            }

        except Exception as e:
            self.logger.error(f"❌ Legal reasoning search failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'documents': []
            }

    def _organize_documents_by_type(self, documents: List[Document]) -> Dict[str, List[Document]]:
        """Organize documents by type for better presentation"""
        organized = {}

        for doc in documents:
            doc_type = doc.metadata.get('document_type', 'unknown')
            if doc_type not in organized:
                organized[doc_type] = []
            organized[doc_type].append(doc)

        return organized

    async def _analyze_legal_context(self, query: str, documents: List[Document]) -> Dict[str, Any]:
        """Analyze legal context using LLM (placeholder for now)"""
        # This would integrate with an LLM service for legal reasoning
        # For now, return basic analysis

        document_types = [doc.metadata.get('document_type') for doc in documents]
        authorities = [doc.metadata.get('authority') for doc in documents]

        return {
            'query_type': self._classify_legal_query(query),
            'relevant_authorities': list(set(authorities)),
            'document_types_found': list(set(document_types)),
            'confidence_score': 0.8,  # Would be calculated by LLM
            'legal_reasoning': f"Found {len(documents)} relevant documents for property tax query: {query}"
        }

    def _classify_legal_query(self, query: str) -> str:
        """Classify the type of legal query"""
        query_lower = query.lower()

        if any(term in query_lower for term in ['exemption', 'homestead', 'disability', 'veteran']):
            return 'exemption_inquiry'
        elif any(term in query_lower for term in ['protest', 'appeal', 'challenge', 'dispute']):
            return 'appeal_process'
        elif any(term in query_lower for term in ['appraisal', 'assessment', 'value', 'valuation']):
            return 'appraisal_inquiry'
        elif any(term in query_lower for term in ['deadline', 'due date', 'when', 'timeline']):
            return 'deadline_inquiry'
        elif any(term in query_lower for term in ['fee', 'cost', 'payment', 'amount']):
            return 'fee_inquiry'
        elif any(term in query_lower for term in ['form', 'application', 'document']):
            return 'form_request'
        else:
            return 'general_inquiry'

    async def get_vector_store_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        if self.vectorstore is None:
            return {'status': 'not_initialized'}

        try:
            # Get collection info
            collection = self.vectorstore._collection
            count = collection.count()

            # Get some sample metadata to understand content distribution
            sample_docs = self.vectorstore.similarity_search("property tax", k=10)

            # Analyze document distribution
            doc_types = {}
            authorities = {}
            quality_scores = []

            for doc in sample_docs:
                doc_type = doc.metadata.get('document_type', 'unknown')
                authority = doc.metadata.get('authority', 'unknown')
                quality = doc.metadata.get('quality_score', 0)

                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                authorities[authority] = authorities.get(authority, 0) + 1
                quality_scores.append(quality)

            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

            return {
                'status': 'active',
                'total_documents': count,
                'collection_name': self.collection_name,
                'sample_document_types': doc_types,
                'sample_authorities': authorities,
                'average_quality_score': round(avg_quality, 2),
                'persist_directory': str(self.persist_directory)
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get vector store stats: {e}")
            return {'status': 'error', 'error': str(e)}

# Global instance
_legal_vector_store = None

async def get_legal_vector_store(use_google_embeddings: bool = True) -> LegalDocumentVectorStore:
    """Get the global legal document vector store instance"""
    global _legal_vector_store
    if _legal_vector_store is None:
        _legal_vector_store = LegalDocumentVectorStore(use_google_embeddings=use_google_embeddings)
    return _legal_vector_store

if __name__ == "__main__":
    # Test the legal document indexer
    async def test_legal_indexer():
        indexer = LegalDocumentVectorStore()

        # Get stats
        stats = await indexer.get_vector_store_stats()
        print(f"Vector store stats: {stats}")

        # Test search
        results = await indexer.search_legal_documents("property tax exemption", k=3)
        print(f"Search results: {len(results)} documents found")

    asyncio.run(test_legal_indexer())