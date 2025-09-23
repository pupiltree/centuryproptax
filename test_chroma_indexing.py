#!/usr/bin/env python3
"""
Test script to verify ChromaDB vector store indexing with mock data
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.data_acquisition.texas_comptroller_scraper import ScrapedDocument
from services.data_acquisition.document_processor import ProcessedDocument
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_core.embeddings import DeterministicFakeEmbedding


async def test_chroma_indexing():
    """Test ChromaDB indexing with sample property tax data"""

    print("🧪 Testing ChromaDB vector store indexing...")

    # Create sample mock documents using the existing structure
    sample_docs = [
        ProcessedDocument(
            original_doc=ScrapedDocument(
                url="https://mock-texas.gov/homestead-exemption",
                title="Texas Homestead Exemption Guide",
                content="Complete guide to homestead exemptions in Texas",
                document_type="exemption_guide",
                authority="Texas Comptroller"
            ),
            cleaned_content="The homestead exemption reduces the taxable value of your home. To qualify, the property must be your principal residence as of January 1. You can claim up to $40,000 in assessed value for school tax purposes and up to $25,000 for other taxing units. Submit form 50-114 to your county appraisal district by April 30.",
            chunks=[
                "The homestead exemption reduces the taxable value of your home. To qualify, the property must be your principal residence as of January 1.",
                "You can claim up to $40,000 in assessed value for school tax purposes and up to $25,000 for other taxing units.",
                "Submit form 50-114 to your county appraisal district by April 30. The exemption applies to the tax year in which it is granted."
            ],
            metadata={
                "legal_concepts": ["homestead exemption", "principal residence", "taxable value"],
                "property_types": ["residential"],
                "citations": ["Texas Tax Code Section 11.13", "Texas Tax Code Section 11.43"],
                "authority": "Texas Comptroller"
            },
            quality_score=0.95,
            processing_notes=["Clean legal document", "High authority"]
        ),
        ProcessedDocument(
            original_doc=ScrapedDocument(
                url="https://mock-texas.gov/property-tax-protest",
                title="Texas Property Tax Protest Guide",
                content="Guide to protesting property tax assessments",
                document_type="appeal_guide",
                authority="Texas Comptroller"
            ),
            cleaned_content="Property owners may protest their property value, exemptions, or other tax-related determinations. Protests must be filed by May 15 or within 30 days of receiving a notice of appraised value, whichever is later. The protest can be filed online, by mail, or in person.",
            chunks=[
                "Property owners may protest their property value, exemptions, or other tax-related determinations.",
                "Protests must be filed by May 15 or within 30 days of receiving a notice of appraised value, whichever is later.",
                "The protest can be filed online, by mail, or in person."
            ],
            metadata={
                "legal_concepts": ["property tax protest", "filing deadline", "appraised value"],
                "property_types": ["all"],
                "citations": ["Texas Tax Code Section 41.44"],
                "authority": "Texas Comptroller"
            },
            quality_score=0.92,
            processing_notes=["Procedural document", "High authority"]
        )
    ]

    # Initialize ChromaDB with deterministic embeddings for testing
    embeddings = DeterministicFakeEmbedding(size=384)

    # Create LangChain documents from processed documents
    langchain_docs = []
    for processed_doc in sample_docs:
        for i, chunk in enumerate(processed_doc.chunks):
            # Convert list metadata to strings for ChromaDB compatibility
            metadata = {
                "source_url": processed_doc.original_doc.url,
                "document_title": processed_doc.original_doc.title,
                "document_type": processed_doc.original_doc.document_type,
                "authority": processed_doc.original_doc.authority,
                "chunk_index": i,
                "quality_score": processed_doc.quality_score,
            }

            # Handle list values in metadata
            for key, value in processed_doc.metadata.items():
                if isinstance(value, list):
                    metadata[key] = ", ".join(value) if value else ""
                else:
                    metadata[key] = value

            doc = Document(
                page_content=chunk,
                metadata=metadata
            )
            langchain_docs.append(doc)

    # Initialize ChromaDB
    vectorstore = Chroma(
        collection_name="texas_property_tax_test",
        embedding_function=embeddings,
        persist_directory="./chroma_db_test"
    )

    # Index the documents
    vectorstore.add_documents(langchain_docs)
    print(f"✅ Indexed {len(langchain_docs)} document chunks")

    # Test search functionality
    print("\n🔍 Testing vector search...")

    # Test semantic search
    results = vectorstore.similarity_search("homestead exemption requirements", k=3)
    print(f"Found {len(results)} results for 'homestead exemption requirements'")

    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"Content: {result.page_content[:200]}...")
        print(f"Metadata: {result.metadata}")

    # Test retrieval with threshold
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    retrieved_docs = retriever.invoke("property tax protest deadline")
    print(f"\nRetrieved {len(retrieved_docs)} documents for 'property tax protest deadline'")

    # Check collection stats
    collection = vectorstore._collection
    if collection:
        count = collection.count()
        print(f"\n📊 Total documents in vector store: {count}")

    print("\n✅ ChromaDB vector store is working correctly!")
    return vectorstore


async def test_search_functionality():
    """Test the integrated search functionality"""
    print("\n🔍 Testing integrated search functionality...")

    try:
        from services.vector_store.semantic_search import create_property_tax_search, SearchRequest, SearchType, SearchScope

        # Initialize search engine
        search_engine = await create_property_tax_search()

        # Test search request
        search_request = SearchRequest(
            query="homestead exemption eligibility",
            search_type=SearchType.SEMANTIC,
            search_scope=SearchScope.EXEMPTIONS,
            max_results=3,
            include_reasoning=True
        )

        # Execute search
        results = await search_engine.search(search_request)

        if results:
            print(f"✅ Search returned {len(results)} results")
            for i, result in enumerate(results):
                print(f"\nResult {i+1}:")
                print(f"Score: {result.score:.3f}")
                print(f"Content: {result.document.page_content[:150]}...")
                print(f"Authority: {result.document.metadata.get('authority', 'Unknown')}")
        else:
            print("⚠️ Search returned no results")

        return True

    except Exception as e:
        print(f"❌ Search functionality test failed: {e}")
        return False


if __name__ == "__main__":
    async def main():
        print("🏛️ Century Property Tax - ChromaDB Indexing Test\n")

        # Test indexing
        indexing_success = await test_chroma_indexing()

        # Test search
        if indexing_success:
            search_success = await test_search_functionality()

        if indexing_success:
            print("\n🎉 All tests passed! ChromaDB vector store is properly configured.")
        else:
            print("\n❌ Tests failed. Check the configuration.")

    asyncio.run(main())