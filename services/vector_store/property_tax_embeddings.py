"""
Property Tax Optimized Embeddings
Specialized embedding strategies for Texas property tax legal documents
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
import structlog
import numpy as np
from dataclasses import dataclass
import json
from pathlib import Path

# Embedding imports
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    GOOGLE_EMBEDDINGS_AVAILABLE = True
except ImportError:
    GOOGLE_EMBEDDINGS_AVAILABLE = False

from langchain_core.embeddings import DeterministicFakeEmbedding, Embeddings

logger = structlog.get_logger()

@dataclass
class PropertyTaxTermMapping:
    """Mapping of property tax terms to semantic concepts"""
    canonical_term: str
    variations: List[str]
    concept_category: str
    importance_weight: float

class PropertyTaxEmbeddings:
    """Enhanced embeddings specifically optimized for property tax legal content"""

    def __init__(self, base_embeddings: Optional[Embeddings] = None, use_google: bool = True):
        self.logger = logger

        # Initialize base embeddings
        if base_embeddings:
            self.base_embeddings = base_embeddings
        elif use_google and GOOGLE_EMBEDDINGS_AVAILABLE:
            try:
                import os
                self.base_embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001",
                    google_api_key=os.getenv("GOOGLE_API_KEY")
                )
                self.logger.info("✅ Using Google embeddings as base for property tax optimization")
            except Exception as e:
                self.logger.warning(f"⚠️ Google embeddings failed, using deterministic: {e}")
                self.base_embeddings = DeterministicFakeEmbedding(size=384)
        else:
            self.base_embeddings = DeterministicFakeEmbedding(size=384)

        # Property tax terminology mappings
        self.term_mappings = self._load_property_tax_terminology()

        # Legal concept weights
        self.concept_weights = self._load_concept_weights()

    def _load_property_tax_terminology(self) -> List[PropertyTaxTermMapping]:
        """Load property tax terminology mappings"""
        return [
            # Exemption-related terms
            PropertyTaxTermMapping(
                canonical_term="homestead exemption",
                variations=["homestead", "residence exemption", "primary residence", "homestead deduction"],
                concept_category="exemption",
                importance_weight=1.0
            ),
            PropertyTaxTermMapping(
                canonical_term="disability exemption",
                variations=["disabled person exemption", "disability", "handicapped exemption"],
                concept_category="exemption",
                importance_weight=0.9
            ),
            PropertyTaxTermMapping(
                canonical_term="senior exemption",
                variations=["elderly exemption", "over 65", "senior citizen", "age exemption"],
                concept_category="exemption",
                importance_weight=0.9
            ),
            PropertyTaxTermMapping(
                canonical_term="veteran exemption",
                variations=["disabled veteran", "military exemption", "veteran disability"],
                concept_category="exemption",
                importance_weight=0.8
            ),
            PropertyTaxTermMapping(
                canonical_term="agricultural exemption",
                variations=["ag exemption", "farm exemption", "agricultural use", "ag use"],
                concept_category="exemption",
                importance_weight=0.8
            ),

            # Appraisal and Assessment terms
            PropertyTaxTermMapping(
                canonical_term="property appraisal",
                variations=["property assessment", "property valuation", "appraised value", "assessed value"],
                concept_category="appraisal",
                importance_weight=1.0
            ),
            PropertyTaxTermMapping(
                canonical_term="market value",
                variations=["fair market value", "actual value", "true value", "market price"],
                concept_category="appraisal",
                importance_weight=0.9
            ),
            PropertyTaxTermMapping(
                canonical_term="appraisal district",
                variations=["CAD", "county appraisal district", "appraisal authority"],
                concept_category="authority",
                importance_weight=0.8
            ),

            # Appeal and Protest terms
            PropertyTaxTermMapping(
                canonical_term="property tax protest",
                variations=["tax protest", "assessment protest", "value protest", "appraisal protest"],
                concept_category="appeal",
                importance_weight=1.0
            ),
            PropertyTaxTermMapping(
                canonical_term="appraisal review board",
                variations=["ARB", "review board", "appeals board", "hearing board"],
                concept_category="appeal",
                importance_weight=0.9
            ),
            PropertyTaxTermMapping(
                canonical_term="informal hearing",
                variations=["informal review", "informal meeting", "preliminary hearing"],
                concept_category="appeal",
                importance_weight=0.7
            ),
            PropertyTaxTermMapping(
                canonical_term="formal hearing",
                variations=["formal protest", "ARB hearing", "board hearing"],
                concept_category="appeal",
                importance_weight=0.8
            ),

            # Tax Collection terms
            PropertyTaxTermMapping(
                canonical_term="property tax",
                variations=["real estate tax", "property taxes", "tax bill", "tax assessment"],
                concept_category="taxation",
                importance_weight=1.0
            ),
            PropertyTaxTermMapping(
                canonical_term="tax rate",
                variations=["millage rate", "tax levy", "property tax rate", "mill rate"],
                concept_category="taxation",
                importance_weight=0.8
            ),
            PropertyTaxTermMapping(
                canonical_term="delinquent tax",
                variations=["overdue tax", "unpaid tax", "late tax", "tax delinquency"],
                concept_category="collection",
                importance_weight=0.7
            ),
            PropertyTaxTermMapping(
                canonical_term="tax lien",
                variations=["property lien", "tax claim", "lien certificate"],
                concept_category="collection",
                importance_weight=0.6
            ),

            # Property Types
            PropertyTaxTermMapping(
                canonical_term="residential property",
                variations=["residential", "home", "house", "dwelling", "residence"],
                concept_category="property_type",
                importance_weight=0.8
            ),
            PropertyTaxTermMapping(
                canonical_term="commercial property",
                variations=["commercial", "business property", "commercial real estate"],
                concept_category="property_type",
                importance_weight=0.7
            ),
            PropertyTaxTermMapping(
                canonical_term="industrial property",
                variations=["industrial", "manufacturing property", "factory"],
                concept_category="property_type",
                importance_weight=0.6
            ),
            PropertyTaxTermMapping(
                canonical_term="agricultural land",
                variations=["farm land", "agricultural property", "ranch", "farming"],
                concept_category="property_type",
                importance_weight=0.7
            ),

            # Legal and Procedural terms
            PropertyTaxTermMapping(
                canonical_term="rendition",
                variations=["property rendition", "business personal property rendition"],
                concept_category="procedure",
                importance_weight=0.6
            ),
            PropertyTaxTermMapping(
                canonical_term="property tax code",
                variations=["tax code", "Texas Property Tax Code", "property tax law"],
                concept_category="legal",
                importance_weight=0.9
            ),
            PropertyTaxTermMapping(
                canonical_term="notice of appraised value",
                variations=["appraisal notice", "NOV", "notice of value"],
                concept_category="procedure",
                importance_weight=0.7
            )
        ]

    def _load_concept_weights(self) -> Dict[str, float]:
        """Load concept category weights for embedding optimization"""
        return {
            "exemption": 1.0,      # Highest priority - common user need
            "appraisal": 0.95,     # Very important
            "appeal": 0.9,         # Important process
            "taxation": 0.85,      # Core concept
            "procedure": 0.8,      # Important for guidance
            "authority": 0.75,     # Needed for context
            "legal": 0.7,          # Background information
            "collection": 0.65,    # Less common queries
            "property_type": 0.6   # Contextual information
        }

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate optimized embeddings for property tax documents"""
        self.logger.info(f"🧮 Generating optimized embeddings for {len(texts)} documents")

        # Preprocess texts with property tax optimization
        optimized_texts = [self._optimize_text_for_property_tax(text) for text in texts]

        # Get base embeddings
        base_embeddings = await self._get_base_embeddings(optimized_texts)

        # Apply property tax specific enhancements
        enhanced_embeddings = []
        for i, (text, base_embedding) in enumerate(zip(optimized_texts, base_embeddings)):
            enhanced_embedding = await self._enhance_embedding_for_property_tax(
                text, base_embedding
            )
            enhanced_embeddings.append(enhanced_embedding)

        self.logger.info("✅ Property tax optimized embeddings generated")
        return enhanced_embeddings

    async def embed_query(self, query: str) -> List[float]:
        """Generate optimized embedding for a property tax query"""
        # Optimize query text
        optimized_query = self._optimize_text_for_property_tax(query)

        # Get base embedding
        base_embeddings = await self._get_base_embeddings([optimized_query])

        # Enhance for property tax context
        enhanced_embedding = await self._enhance_embedding_for_property_tax(
            optimized_query, base_embeddings[0]
        )

        return enhanced_embedding

    def _optimize_text_for_property_tax(self, text: str) -> str:
        """Optimize text content for property tax semantic understanding"""
        optimized_text = text

        # Normalize property tax terminology
        for mapping in self.term_mappings:
            # Replace variations with canonical terms for better semantic consistency
            for variation in mapping.variations:
                # Case-insensitive replacement but preserve original case pattern
                import re
                pattern = re.compile(re.escape(variation), re.IGNORECASE)
                optimized_text = pattern.sub(mapping.canonical_term, optimized_text)

        # Add property tax context markers
        if not any(marker in optimized_text.lower() for marker in [
            'property tax', 'texas', 'comptroller', 'appraisal', 'exemption'
        ]):
            optimized_text = f"Texas property tax context: {optimized_text}"

        return optimized_text

    async def _get_base_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get base embeddings from the underlying model"""
        try:
            if hasattr(self.base_embeddings, 'aembed_documents'):
                return await self.base_embeddings.aembed_documents(texts)
            else:
                # Fallback to synchronous method
                return self.base_embeddings.embed_documents(texts)
        except Exception as e:
            self.logger.error(f"❌ Failed to get base embeddings: {e}")
            # Return dummy embeddings as fallback
            return [[0.0] * 384 for _ in texts]

    async def _enhance_embedding_for_property_tax(self, text: str, base_embedding: List[float]) -> List[float]:
        """Enhance base embedding with property tax specific signals"""
        enhanced = base_embedding.copy()

        # Calculate property tax relevance scores
        relevance_scores = self._calculate_property_tax_relevance(text)

        # Apply concept-based weighting
        concept_boost = self._calculate_concept_boost(text)

        # Apply enhancement (simple approach - in practice this could be more sophisticated)
        if relevance_scores['total_score'] > 0.5:
            # Boost embeddings for highly relevant property tax content
            boost_factor = 1.0 + (concept_boost * 0.1)  # Up to 10% boost
            enhanced = [val * boost_factor for val in enhanced]

        return enhanced

    def _calculate_property_tax_relevance(self, text: str) -> Dict[str, float]:
        """Calculate how relevant the text is to property tax concepts"""
        text_lower = text.lower()
        scores = {}
        total_score = 0.0

        for mapping in self.term_mappings:
            # Check for canonical term and variations
            term_score = 0.0

            if mapping.canonical_term.lower() in text_lower:
                term_score = mapping.importance_weight

            for variation in mapping.variations:
                if variation.lower() in text_lower:
                    term_score = max(term_score, mapping.importance_weight * 0.8)

            scores[mapping.canonical_term] = term_score
            total_score += term_score

        # Normalize total score
        max_possible_score = sum(m.importance_weight for m in self.term_mappings)
        normalized_score = min(total_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0

        return {
            'individual_scores': scores,
            'total_score': normalized_score
        }

    def _calculate_concept_boost(self, text: str) -> float:
        """Calculate concept-based boost factor"""
        text_lower = text.lower()
        concept_scores = {}

        # Calculate scores for each concept category
        for category, weight in self.concept_weights.items():
            category_terms = [m for m in self.term_mappings if m.concept_category == category]
            category_score = 0.0

            for mapping in category_terms:
                if any(term.lower() in text_lower
                      for term in [mapping.canonical_term] + mapping.variations):
                    category_score += mapping.importance_weight

            if category_terms:
                category_score /= len(category_terms)  # Normalize by number of terms

            concept_scores[category] = category_score * weight

        # Calculate weighted average
        total_weight = sum(self.concept_weights.values())
        boost_score = sum(concept_scores.values()) / total_weight if total_weight > 0 else 0.0

        return boost_score

    async def find_similar_property_tax_terms(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find the most similar property tax terms to a query"""
        query_lower = query.lower()
        similarities = []

        for mapping in self.term_mappings:
            # Calculate similarity to canonical term
            canonical_sim = self._calculate_term_similarity(query_lower, mapping.canonical_term.lower())

            # Calculate similarity to variations
            variation_sims = [
                self._calculate_term_similarity(query_lower, var.lower())
                for var in mapping.variations
            ]

            # Take best similarity
            best_sim = max([canonical_sim] + variation_sims)

            # Weight by importance
            weighted_sim = best_sim * mapping.importance_weight

            similarities.append((mapping.canonical_term, weighted_sim))

        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _calculate_term_similarity(self, term1: str, term2: str) -> float:
        """Calculate similarity between two terms (simple implementation)"""
        # Simple word overlap similarity
        words1 = set(term1.split())
        words2 = set(term2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    async def get_property_tax_context_vector(self) -> List[float]:
        """Get a context vector representing general property tax domain"""
        # Create a representative text for property tax domain
        context_text = """
        Texas property tax law exemptions appraisal assessment homestead disability
        senior veteran agricultural protest appeal review board hearing market value
        tax rate collection delinquent lien residential commercial industrial
        comptroller county appraisal district rendition notice procedure code
        """

        context_embedding = await self.embed_query(context_text)
        return context_embedding

# Global instance
_property_tax_embeddings = None

def get_property_tax_embeddings(use_google: bool = True) -> PropertyTaxEmbeddings:
    """Get the global property tax embeddings instance"""
    global _property_tax_embeddings
    if _property_tax_embeddings is None:
        _property_tax_embeddings = PropertyTaxEmbeddings(use_google=use_google)
    return _property_tax_embeddings

if __name__ == "__main__":
    # Test property tax embeddings
    async def test_embeddings():
        embeddings = PropertyTaxEmbeddings()

        # Test term similarity
        similar_terms = await embeddings.find_similar_property_tax_terms("homestead", top_k=3)
        print(f"Similar terms to 'homestead': {similar_terms}")

        # Test text optimization
        original_text = "I need help with my home exemption"
        optimized = embeddings._optimize_text_for_property_tax(original_text)
        print(f"Original: {original_text}")
        print(f"Optimized: {optimized}")

        # Test relevance calculation
        relevance = embeddings._calculate_property_tax_relevance("homestead exemption for disabled veteran")
        print(f"Relevance scores: {relevance}")

    asyncio.run(test_embeddings())