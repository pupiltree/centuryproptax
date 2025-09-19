"""
Advanced Semantic Search for Property Tax Legal Documents
Multi-modal search with legal reasoning and context awareness
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import structlog
import json
from enum import Enum

from langchain_core.documents import Document

from .legal_document_indexer import LegalDocumentVectorStore, get_legal_vector_store
from .property_tax_embeddings import PropertyTaxEmbeddings, get_property_tax_embeddings

logger = structlog.get_logger()

class SearchType(Enum):
    """Types of search strategies"""
    SEMANTIC = "semantic"           # Pure semantic similarity
    KEYWORD = "keyword"            # Keyword-based search
    HYBRID = "hybrid"              # Combination of semantic and keyword
    LEGAL_REASONING = "legal_reasoning"  # LLM-powered legal analysis

class SearchScope(Enum):
    """Scope of search within legal documents"""
    ALL = "all"                    # All document types
    STATUTES = "statutes"          # Legal statutes only
    PROCEDURES = "procedures"      # Procedural documents
    FORMS = "forms"               # Forms and applications
    EXEMPTIONS = "exemptions"     # Exemption-related content
    APPEALS = "appeals"           # Appeal and protest content

@dataclass
class SearchResult:
    """Enhanced search result with legal context"""
    document: Document
    score: float
    search_type: SearchType
    legal_context: Dict[str, Any]
    relevance_explanation: str
    citation_references: List[str]

@dataclass
class SearchRequest:
    """Comprehensive search request specification"""
    query: str
    search_type: SearchType = SearchType.HYBRID
    search_scope: SearchScope = SearchScope.ALL
    max_results: int = 10
    min_score_threshold: float = 0.3
    include_reasoning: bool = True
    filter_by_authority: Optional[str] = None
    filter_by_date_range: Optional[Tuple[datetime, datetime]] = None
    priority_concepts: Optional[List[str]] = None

class PropertyTaxSemanticSearch:
    """Advanced semantic search engine for property tax legal documents"""

    def __init__(self):
        self.logger = logger
        self.vector_store: Optional[LegalDocumentVectorStore] = None
        self.embeddings: Optional[PropertyTaxEmbeddings] = None

        # Legal concept hierarchies for enhanced search
        self.concept_hierarchies = self._build_concept_hierarchies()

        # Search result rankers
        self.result_rankers = {
            SearchType.SEMANTIC: self._rank_semantic_results,
            SearchType.KEYWORD: self._rank_keyword_results,
            SearchType.HYBRID: self._rank_hybrid_results,
            SearchType.LEGAL_REASONING: self._rank_legal_reasoning_results
        }

    async def initialize(self):
        """Initialize search components"""
        self.vector_store = await get_legal_vector_store()
        self.embeddings = get_property_tax_embeddings()
        self.logger.info("✅ Property tax semantic search initialized")

    async def search(self, request: SearchRequest) -> List[SearchResult]:
        """Execute comprehensive search based on request parameters"""
        if self.vector_store is None or self.embeddings is None:
            await self.initialize()

        self.logger.info(f"🔍 Executing {request.search_type.value} search: {request.query}")

        try:
            # Execute search based on type
            raw_results = await self._execute_search_by_type(request)

            # Apply filters
            filtered_results = await self._apply_filters(raw_results, request)

            # Rank and score results
            ranked_results = await self._rank_and_score_results(filtered_results, request)

            # Add legal context and reasoning
            enhanced_results = await self._enhance_results_with_legal_context(ranked_results, request)

            # Apply final filtering and limits
            final_results = self._apply_final_filtering(enhanced_results, request)

            self.logger.info(f"✅ Search completed: {len(final_results)} results returned")
            return final_results

        except Exception as e:
            self.logger.error(f"❌ Search failed: {e}")
            return []

    async def _execute_search_by_type(self, request: SearchRequest) -> List[Document]:
        """Execute search based on search type"""
        if request.search_type == SearchType.SEMANTIC:
            return await self._semantic_search(request)
        elif request.search_type == SearchType.KEYWORD:
            return await self._keyword_search(request)
        elif request.search_type == SearchType.HYBRID:
            return await self._hybrid_search(request)
        elif request.search_type == SearchType.LEGAL_REASONING:
            return await self._legal_reasoning_search(request)
        else:
            raise ValueError(f"Unsupported search type: {request.search_type}")

    async def _semantic_search(self, request: SearchRequest) -> List[Document]:
        """Pure semantic similarity search"""
        # Enhance query with property tax context
        enhanced_query = await self._enhance_query_for_semantic_search(request.query, request)

        # Get semantic results
        results = await self.vector_store.search_legal_documents(
            enhanced_query,
            document_type=self._scope_to_document_type(request.search_scope),
            authority=request.filter_by_authority,
            k=request.max_results * 2  # Get more for filtering
        )

        return results

    async def _keyword_search(self, request: SearchRequest) -> List[Document]:
        """Keyword-based search with property tax term expansion"""
        # Expand query with property tax terminology
        expanded_query = await self._expand_query_with_property_tax_terms(request.query)

        # Use keyword search (simulated with enhanced semantic search)
        results = await self.vector_store.search_legal_documents(
            expanded_query,
            document_type=self._scope_to_document_type(request.search_scope),
            authority=request.filter_by_authority,
            k=request.max_results * 2
        )

        return results

    async def _hybrid_search(self, request: SearchRequest) -> List[Document]:
        """Hybrid semantic + keyword search"""
        # Get semantic results
        semantic_results = await self._semantic_search(request)

        # Get keyword results
        keyword_results = await self._keyword_search(request)

        # Merge and deduplicate results
        all_results = semantic_results + keyword_results
        seen_urls = set()
        deduplicated = []

        for doc in all_results:
            url = doc.metadata.get('source_url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduplicated.append(doc)

        return deduplicated

    async def _legal_reasoning_search(self, request: SearchRequest) -> List[Document]:
        """LLM-powered legal reasoning search"""
        # Start with hybrid search
        base_results = await self._hybrid_search(request)

        # Apply legal reasoning analysis (placeholder for LLM integration)
        reasoning_enhanced = await self._apply_legal_reasoning_analysis(base_results, request)

        return reasoning_enhanced

    async def _enhance_query_for_semantic_search(self, query: str, request: SearchRequest) -> str:
        """Enhance query with semantic context"""
        enhanced_parts = [query]

        # Add scope context
        if request.search_scope != SearchScope.ALL:
            scope_context = {
                SearchScope.STATUTES: "legal statute code section",
                SearchScope.PROCEDURES: "procedure process steps how to",
                SearchScope.FORMS: "form application document",
                SearchScope.EXEMPTIONS: "exemption homestead disability senior veteran",
                SearchScope.APPEALS: "protest appeal hearing review board"
            }
            enhanced_parts.append(scope_context.get(request.search_scope, ""))

        # Add priority concepts
        if request.priority_concepts:
            enhanced_parts.extend(request.priority_concepts)

        # Add Texas property tax context
        enhanced_parts.append("Texas property tax law")

        return " ".join(enhanced_parts)

    async def _expand_query_with_property_tax_terms(self, query: str) -> str:
        """Expand query with related property tax terminology"""
        # Find similar terms
        similar_terms = await self.embeddings.find_similar_property_tax_terms(query, top_k=3)

        expanded_parts = [query]
        for term, score in similar_terms:
            if score > 0.5:  # Only include highly similar terms
                expanded_parts.append(term)

        return " ".join(expanded_parts)

    def _scope_to_document_type(self, scope: SearchScope) -> Optional[str]:
        """Convert search scope to document type filter"""
        scope_mapping = {
            SearchScope.STATUTES: "statute",
            SearchScope.PROCEDURES: "procedure",
            SearchScope.FORMS: "form",
            SearchScope.EXEMPTIONS: None,  # Cross-cutting concept
            SearchScope.APPEALS: None,     # Cross-cutting concept
            SearchScope.ALL: None
        }
        return scope_mapping.get(scope)

    async def _apply_filters(self, results: List[Document], request: SearchRequest) -> List[Document]:
        """Apply request filters to search results"""
        filtered = results

        # Filter by date range
        if request.filter_by_date_range:
            start_date, end_date = request.filter_by_date_range
            filtered = [
                doc for doc in filtered
                if self._is_document_in_date_range(doc, start_date, end_date)
            ]

        # Filter by scope-specific content
        if request.search_scope in [SearchScope.EXEMPTIONS, SearchScope.APPEALS]:
            filtered = [
                doc for doc in filtered
                if self._document_matches_scope(doc, request.search_scope)
            ]

        return filtered

    def _is_document_in_date_range(self, doc: Document, start_date: datetime, end_date: datetime) -> bool:
        """Check if document falls within date range"""
        effective_date_str = doc.metadata.get('effective_date')
        if not effective_date_str:
            return True  # Include documents without dates

        try:
            effective_date = datetime.fromisoformat(effective_date_str)
            return start_date <= effective_date <= end_date
        except:
            return True  # Include documents with invalid dates

    def _document_matches_scope(self, doc: Document, scope: SearchScope) -> bool:
        """Check if document matches specific scope criteria"""
        content = doc.page_content.lower()
        metadata = doc.metadata

        if scope == SearchScope.EXEMPTIONS:
            exemption_terms = ['exemption', 'homestead', 'disability', 'senior', 'veteran', 'agricultural']
            return any(term in content for term in exemption_terms)

        elif scope == SearchScope.APPEALS:
            appeal_terms = ['protest', 'appeal', 'hearing', 'review board', 'ARB', 'challenge']
            return any(term in content for term in appeal_terms)

        return True

    async def _rank_and_score_results(self, results: List[Document], request: SearchRequest) -> List[Tuple[Document, float]]:
        """Rank and score results based on search type"""
        ranker = self.result_rankers.get(request.search_type, self._rank_hybrid_results)
        return await ranker(results, request)

    async def _rank_semantic_results(self, results: List[Document], request: SearchRequest) -> List[Tuple[Document, float]]:
        """Rank results for semantic search"""
        scored_results = []

        for doc in results:
            # Calculate semantic relevance score
            score = await self._calculate_semantic_relevance_score(doc, request)
            scored_results.append((doc, score))

        # Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results

    async def _rank_keyword_results(self, results: List[Document], request: SearchRequest) -> List[Tuple[Document, float]]:
        """Rank results for keyword search"""
        scored_results = []

        for doc in results:
            # Calculate keyword relevance score
            score = self._calculate_keyword_relevance_score(doc, request)
            scored_results.append((doc, score))

        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results

    async def _rank_hybrid_results(self, results: List[Document], request: SearchRequest) -> List[Tuple[Document, float]]:
        """Rank results for hybrid search"""
        scored_results = []

        for doc in results:
            # Combine semantic and keyword scores
            semantic_score = await self._calculate_semantic_relevance_score(doc, request)
            keyword_score = self._calculate_keyword_relevance_score(doc, request)

            # Weighted combination
            hybrid_score = (semantic_score * 0.7) + (keyword_score * 0.3)
            scored_results.append((doc, hybrid_score))

        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results

    async def _rank_legal_reasoning_results(self, results: List[Document], request: SearchRequest) -> List[Tuple[Document, float]]:
        """Rank results with legal reasoning"""
        # Start with hybrid ranking
        hybrid_results = await self._rank_hybrid_results(results, request)

        # Apply legal reasoning boost
        legal_enhanced = []
        for doc, score in hybrid_results:
            legal_boost = self._calculate_legal_reasoning_boost(doc, request)
            enhanced_score = score * (1.0 + legal_boost)
            legal_enhanced.append((doc, enhanced_score))

        legal_enhanced.sort(key=lambda x: x[1], reverse=True)
        return legal_enhanced

    async def _calculate_semantic_relevance_score(self, doc: Document, request: SearchRequest) -> float:
        """Calculate semantic relevance score"""
        # Use embeddings to calculate semantic similarity
        content = doc.page_content
        relevance = self.embeddings._calculate_property_tax_relevance(content)

        # Base score from property tax relevance
        base_score = relevance['total_score']

        # Boost for quality
        quality_score = doc.metadata.get('quality_score', 0.5)
        quality_boost = quality_score * 0.2

        # Boost for authority
        authority_boost = 0.0
        authority = doc.metadata.get('authority', '').lower()
        if 'texas comptroller' in authority:
            authority_boost = 0.3
        elif 'county' in authority:
            authority_boost = 0.2

        return min(base_score + quality_boost + authority_boost, 1.0)

    def _calculate_keyword_relevance_score(self, doc: Document, request: SearchRequest) -> float:
        """Calculate keyword relevance score"""
        content = doc.page_content.lower()
        query_terms = request.query.lower().split()

        # Count term matches
        term_matches = sum(1 for term in query_terms if term in content)
        term_score = term_matches / len(query_terms) if query_terms else 0

        # Boost for exact phrase matches
        phrase_boost = 0.0
        if request.query.lower() in content:
            phrase_boost = 0.3

        # Boost for title matches
        title_boost = 0.0
        title = doc.metadata.get('document_title', '').lower()
        if any(term in title for term in query_terms):
            title_boost = 0.2

        return min(term_score + phrase_boost + title_boost, 1.0)

    def _calculate_legal_reasoning_boost(self, doc: Document, request: SearchRequest) -> float:
        """Calculate legal reasoning boost factor"""
        # Boost based on document type relevance
        doc_type = doc.metadata.get('document_type', '')
        type_boost = {
            'statute': 0.3,
            'regulation': 0.25,
            'procedure': 0.2,
            'form': 0.15,
            'faq': 0.1
        }.get(doc_type, 0.0)

        # Boost based on citations
        citations = doc.metadata.get('citations', [])
        citation_boost = min(len(citations) * 0.05, 0.2)

        # Boost based on legal concepts
        legal_concepts = doc.metadata.get('legal_concepts', [])
        concept_boost = min(len(legal_concepts) * 0.03, 0.15)

        return type_boost + citation_boost + concept_boost

    async def _apply_legal_reasoning_analysis(self, results: List[Document], request: SearchRequest) -> List[Document]:
        """Apply legal reasoning analysis to filter and enhance results"""
        # This would integrate with an LLM for legal analysis
        # For now, return results as-is
        return results

    async def _enhance_results_with_legal_context(self, ranked_results: List[Tuple[Document, float]],
                                                request: SearchRequest) -> List[SearchResult]:
        """Enhance results with legal context and explanations"""
        enhanced_results = []

        for doc, score in ranked_results:
            # Generate legal context
            legal_context = self._generate_legal_context(doc, request)

            # Generate relevance explanation
            relevance_explanation = self._generate_relevance_explanation(doc, request, score)

            # Extract citation references
            citation_references = self._extract_citation_references(doc)

            search_result = SearchResult(
                document=doc,
                score=score,
                search_type=request.search_type,
                legal_context=legal_context,
                relevance_explanation=relevance_explanation,
                citation_references=citation_references
            )

            enhanced_results.append(search_result)

        return enhanced_results

    def _generate_legal_context(self, doc: Document, request: SearchRequest) -> Dict[str, Any]:
        """Generate legal context for a document"""
        return {
            'document_type': doc.metadata.get('document_type', 'unknown'),
            'authority': doc.metadata.get('authority', 'unknown'),
            'jurisdiction': doc.metadata.get('jurisdiction', 'unknown'),
            'effective_date': doc.metadata.get('effective_date'),
            'section_number': doc.metadata.get('section_number'),
            'legal_concepts': doc.metadata.get('legal_concepts', []),
            'property_types': doc.metadata.get('property_types', []),
            'tax_concepts': doc.metadata.get('tax_concepts', [])
        }

    def _generate_relevance_explanation(self, doc: Document, request: SearchRequest, score: float) -> str:
        """Generate explanation for why document is relevant"""
        explanations = []

        # Score-based explanation
        if score > 0.8:
            explanations.append("Highly relevant to your query")
        elif score > 0.6:
            explanations.append("Moderately relevant to your query")
        else:
            explanations.append("Somewhat relevant to your query")

        # Authority-based explanation
        authority = doc.metadata.get('authority', '')
        if 'texas comptroller' in authority.lower():
            explanations.append("from the authoritative Texas Comptroller")
        elif 'county' in authority.lower():
            explanations.append("from county appraisal district")

        # Content-based explanation
        legal_concepts = doc.metadata.get('legal_concepts', [])
        if legal_concepts:
            explanations.append(f"covers {', '.join(legal_concepts[:2])}")

        return "; ".join(explanations)

    def _extract_citation_references(self, doc: Document) -> List[str]:
        """Extract citation references from document"""
        return doc.metadata.get('citations', [])

    def _apply_final_filtering(self, results: List[SearchResult], request: SearchRequest) -> List[SearchResult]:
        """Apply final filtering and limits"""
        # Filter by minimum score threshold
        filtered = [r for r in results if r.score >= request.min_score_threshold]

        # Limit results
        final_results = filtered[:request.max_results]

        return final_results

    def _build_concept_hierarchies(self) -> Dict[str, List[str]]:
        """Build legal concept hierarchies for enhanced search"""
        return {
            'exemptions': [
                'homestead exemption', 'disability exemption', 'senior exemption',
                'veteran exemption', 'agricultural exemption', 'charitable exemption'
            ],
            'appraisal': [
                'property appraisal', 'market value', 'assessed value',
                'appraisal district', 'appraisal review', 'property valuation'
            ],
            'appeals': [
                'property tax protest', 'appraisal review board', 'informal hearing',
                'formal hearing', 'appeal process', 'tax court'
            ],
            'collection': [
                'property tax bill', 'tax payment', 'delinquent tax',
                'tax lien', 'payment plan', 'tax sale'
            ]
        }

# Factory function
async def create_property_tax_search() -> PropertyTaxSemanticSearch:
    """Create and initialize property tax semantic search"""
    search_engine = PropertyTaxSemanticSearch()
    await search_engine.initialize()
    return search_engine

if __name__ == "__main__":
    # Test semantic search
    async def test_semantic_search():
        search_engine = await create_property_tax_search()

        # Test search request
        request = SearchRequest(
            query="homestead exemption for disabled veterans",
            search_type=SearchType.HYBRID,
            search_scope=SearchScope.EXEMPTIONS,
            max_results=5,
            include_reasoning=True
        )

        results = await search_engine.search(request)

        print(f"Search results: {len(results)} found")
        for result in results[:3]:
            print(f"Score: {result.score:.2f}")
            print(f"Title: {result.document.metadata.get('document_title', 'Unknown')}")
            print(f"Explanation: {result.relevance_explanation}")
            print("---")

    asyncio.run(test_semantic_search())