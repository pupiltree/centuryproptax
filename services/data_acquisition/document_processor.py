"""
Document Processor for Property Tax Content
Handles PDF extraction, HTML cleaning, and document normalization
"""

import asyncio
import aiofiles
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import structlog
import re
from datetime import datetime
import hashlib
import mimetypes

# PDF processing
try:
    import PyPDF2
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# HTML processing
from bs4 import BeautifulSoup
import html

from .texas_comptroller_scraper import ScrapedDocument

logger = structlog.get_logger()

@dataclass
class ProcessedDocument:
    """Represents a processed document ready for vector storage"""
    original_doc: ScrapedDocument
    cleaned_content: str
    chunks: List[str]
    metadata: Dict[str, Any]
    quality_score: float
    processing_notes: List[str]

class DocumentProcessor:
    """Processes various document formats for the property tax knowledge base"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def process_document(self, document: ScrapedDocument) -> ProcessedDocument:
        """Process a single document through the full pipeline"""
        logger.info(f"📄 Processing document: {document.title}")

        try:
            # Step 1: Clean and normalize content
            cleaned_content = await self.clean_content(document.content, document.document_type)

            # Step 2: Extract and enhance metadata
            metadata = await self.extract_metadata(document, cleaned_content)

            # Step 3: Chunk the content appropriately
            chunks = await self.chunk_content(cleaned_content, document.document_type)

            # Step 4: Calculate quality score
            quality_score = await self.calculate_quality_score(document, cleaned_content, chunks)

            # Step 5: Generate processing notes
            processing_notes = await self.generate_processing_notes(document, cleaned_content, chunks)

            processed_doc = ProcessedDocument(
                original_doc=document,
                cleaned_content=cleaned_content,
                chunks=chunks,
                metadata=metadata,
                quality_score=quality_score,
                processing_notes=processing_notes
            )

            logger.info(f"✅ Document processed: {len(chunks)} chunks, quality score: {quality_score:.2f}")
            return processed_doc

        except Exception as e:
            logger.error(f"❌ Error processing document {document.title}: {e}")
            raise

    async def process_documents_batch(self, documents: List[ScrapedDocument]) -> List[ProcessedDocument]:
        """Process multiple documents in parallel"""
        logger.info(f"🔄 Processing batch of {len(documents)} documents")

        semaphore = asyncio.Semaphore(5)  # Limit concurrent processing

        async def process_with_semaphore(doc):
            async with semaphore:
                return await self.process_document(doc)

        tasks = [process_with_semaphore(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_docs = []
        for result in results:
            if isinstance(result, ProcessedDocument):
                processed_docs.append(result)
            elif isinstance(result, Exception):
                logger.error(f"❌ Error in batch processing: {result}")

        logger.info(f"✅ Batch processing complete: {len(processed_docs)}/{len(documents)} successful")
        return processed_docs

    async def clean_content(self, content: str, document_type: str) -> str:
        """Clean and normalize document content"""
        if not content:
            return ""

        # HTML decode
        content = html.unescape(content)

        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)

        # Clean common artifacts
        content = self._remove_common_artifacts(content)

        # Document type specific cleaning
        if document_type == 'statute':
            content = self._clean_legal_text(content)
        elif document_type == 'form':
            content = self._clean_form_text(content)
        elif document_type == 'faq':
            content = self._clean_faq_text(content)

        # Final cleanup
        content = content.strip()

        return content

    def _remove_common_artifacts(self, content: str) -> str:
        """Remove common web artifacts and noise"""
        # Remove navigation artifacts
        artifacts = [
            r'Skip to main content',
            r'JavaScript must be enabled',
            r'This site uses cookies',
            r'For accessibility help',
            r'Print this page',
            r'Share this page',
            r'Last updated:?\s*\d{1,2}/\d{1,2}/\d{4}',
            r'Copyright \d{4}',
            r'All rights reserved',
            r'Privacy Policy',
            r'Terms of Use'
        ]

        for artifact in artifacts:
            content = re.sub(artifact, '', content, flags=re.IGNORECASE)

        return content

    def _clean_legal_text(self, content: str) -> str:
        """Clean legal/statute text"""
        # Normalize section references
        content = re.sub(r'Sec\.?\s+(\d+)', r'Section \1', content)
        content = re.sub(r'§\s*(\d+)', r'Section \1', content)

        # Clean up legal formatting
        content = re.sub(r'\([a-z]\)\s*', '\n', content)  # Subsection markers
        content = re.sub(r'\(\d+\)\s*', '\n', content)   # Numbered subsections

        return content

    def _clean_form_text(self, content: str) -> str:
        """Clean form-related text"""
        # Remove form field artifacts
        content = re.sub(r'Required field', '', content, flags=re.IGNORECASE)
        content = re.sub(r'Please enter', '', content, flags=re.IGNORECASE)
        content = re.sub(r'Click here to', '', content, flags=re.IGNORECASE)

        return content

    def _clean_faq_text(self, content: str) -> str:
        """Clean FAQ text"""
        # Normalize Q&A format
        content = re.sub(r'Question:\s*', 'Q: ', content, flags=re.IGNORECASE)
        content = re.sub(r'Answer:\s*', 'A: ', content, flags=re.IGNORECASE)
        content = re.sub(r'Q\d+[:\.]?\s*', 'Q: ', content)

        return content

    async def extract_metadata(self, document: ScrapedDocument, cleaned_content: str) -> Dict[str, Any]:
        """Extract enhanced metadata from document"""
        metadata = {
            # Original metadata
            'url': document.url,
            'title': document.title,
            'document_type': document.document_type,
            'authority': document.authority,
            'jurisdiction': document.jurisdiction,
            'effective_date': document.effective_date.isoformat() if document.effective_date else None,
            'section_number': document.section_number,
            'citations': document.citations,
            'hash': document.hash,

            # Enhanced metadata
            'content_length': len(cleaned_content),
            'word_count': len(cleaned_content.split()),
            'processed_at': datetime.now().isoformat(),

            # Legal-specific metadata
            'legal_concepts': await self._extract_legal_concepts(cleaned_content),
            'property_types': await self._extract_property_types(cleaned_content),
            'tax_concepts': await self._extract_tax_concepts(cleaned_content),
            'deadlines': await self._extract_deadlines(cleaned_content),
            'fee_amounts': await self._extract_fee_amounts(cleaned_content)
        }

        return metadata

    async def _extract_legal_concepts(self, content: str) -> List[str]:
        """Extract legal concepts from content"""
        concepts = []

        # Legal concept patterns
        legal_patterns = [
            r'exemption',
            r'appraisal',
            r'assessment',
            r'protest',
            r'appeal',
            r'hearing',
            r'rendition',
            r'homestead',
            r'valuation',
            r'tax rate',
            r'levy',
            r'collection',
            r'delinquent',
            r'penalty',
            r'interest'
        ]

        content_lower = content.lower()
        for pattern in legal_patterns:
            if re.search(pattern, content_lower):
                concepts.append(pattern)

        return concepts

    async def _extract_property_types(self, content: str) -> List[str]:
        """Extract property types mentioned in content"""
        property_types = []

        patterns = [
            r'residential',
            r'commercial',
            r'industrial',
            r'agricultural',
            r'vacant land',
            r'mobile home',
            r'manufactured home',
            r'condominium',
            r'cooperative',
            r'farm',
            r'ranch',
            r'timber land',
            r'mineral rights'
        ]

        content_lower = content.lower()
        for pattern in patterns:
            if re.search(pattern, content_lower):
                property_types.append(pattern)

        return property_types

    async def _extract_tax_concepts(self, content: str) -> List[str]:
        """Extract tax-specific concepts"""
        tax_concepts = []

        patterns = [
            r'tax rate',
            r'millage',
            r'tax year',
            r'tax roll',
            r'tax bill',
            r'tax certificate',
            r'tax sale',
            r'tax lien',
            r'delinquent tax',
            r'penalty and interest',
            r'installment plan',
            r'payment agreement'
        ]

        content_lower = content.lower()
        for pattern in patterns:
            if re.search(pattern, content_lower):
                tax_concepts.append(pattern)

        return tax_concepts

    async def _extract_deadlines(self, content: str) -> List[str]:
        """Extract important deadlines from content"""
        deadlines = []

        # Look for deadline patterns
        deadline_patterns = [
            r'(?:deadline|due|before|by)\s+(\w+\s+\d{1,2},?\s+\d{4})',
            r'(\w+\s+\d{1,2}(?:st|nd|rd|th)?)(?:\s+deadline|\s+due)',
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}',
            r'(\d{1,2}/\d{1,2}/\d{4})'
        ]

        for pattern in deadline_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            deadlines.extend(matches)

        return list(set(deadlines))  # Remove duplicates

    async def _extract_fee_amounts(self, content: str) -> List[str]:
        """Extract fee amounts from content"""
        fees = []

        # Look for fee patterns
        fee_patterns = [
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
            r'\$\d+(?:\.\d{2})?',
            r'\d+(?:,\d{3})*\s*dollars?',
            r'fee\s+of\s+\$?(\d+(?:\.\d{2})?)'
        ]

        for pattern in fee_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            fees.extend(matches)

        return list(set(fees))  # Remove duplicates

    async def chunk_content(self, content: str, document_type: str) -> List[str]:
        """Chunk content appropriately for vector storage"""
        if not content:
            return []

        # Document type specific chunking strategies
        if document_type == 'statute':
            return await self._chunk_legal_text(content)
        elif document_type == 'faq':
            return await self._chunk_faq_text(content)
        elif document_type == 'form':
            return await self._chunk_form_text(content)
        else:
            return await self._chunk_generic_text(content)

    async def _chunk_legal_text(self, content: str) -> List[str]:
        """Chunk legal text by sections and subsections"""
        chunks = []

        # Split by sections first
        section_pattern = r'(?:Section|§)\s*\d+(?:\.\d+)*'
        sections = re.split(section_pattern, content)

        for i, section in enumerate(sections):
            if not section.strip():
                continue

            # Add section header back
            if i > 0:
                matches = re.findall(section_pattern, content)
                if i - 1 < len(matches):
                    section = f"{matches[i-1]}\n{section}"

            # Further chunk if section is too long
            if len(section) > self.chunk_size:
                sub_chunks = await self._chunk_generic_text(section)
                chunks.extend(sub_chunks)
            else:
                chunks.append(section.strip())

        return chunks

    async def _chunk_faq_text(self, content: str) -> List[str]:
        """Chunk FAQ text by Q&A pairs"""
        chunks = []

        # Split by Q&A pairs
        qa_pattern = r'(?:Q:|Question:)'
        qa_sections = re.split(qa_pattern, content, flags=re.IGNORECASE)

        for i, section in enumerate(qa_sections):
            if not section.strip():
                continue

            # Add Q: back
            if i > 0:
                section = f"Q: {section}"

            section = section.strip()
            if section:
                chunks.append(section)

        return chunks

    async def _chunk_form_text(self, content: str) -> List[str]:
        """Chunk form text by logical sections"""
        # Keep form content together more than other types
        chunks = []

        # Split by major sections or use smaller chunks
        if len(content) <= self.chunk_size * 1.5:  # Keep smaller forms together
            chunks.append(content)
        else:
            chunks = await self._chunk_generic_text(content)

        return chunks

    async def _chunk_generic_text(self, content: str) -> List[str]:
        """Generic text chunking with overlap"""
        chunks = []

        # Split by paragraphs first
        paragraphs = content.split('\n\n')

        current_chunk = ""
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph

        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Handle very long paragraphs that exceed chunk size
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > self.chunk_size * 1.5:
                # Split long chunks by sentences
                sentences = re.split(r'[.!?]+', chunk)
                sub_chunk = ""
                for sentence in sentences:
                    if len(sub_chunk) + len(sentence) > self.chunk_size and sub_chunk:
                        final_chunks.append(sub_chunk.strip())
                        sub_chunk = sentence
                    else:
                        if sub_chunk:
                            sub_chunk += ". " + sentence
                        else:
                            sub_chunk = sentence
                if sub_chunk.strip():
                    final_chunks.append(sub_chunk.strip())
            else:
                final_chunks.append(chunk)

        return final_chunks

    async def calculate_quality_score(self, document: ScrapedDocument, cleaned_content: str, chunks: List[str]) -> float:
        """Calculate quality score for the processed document"""
        score = 0.0
        max_score = 10.0

        # Content length score (0-2 points)
        content_length = len(cleaned_content)
        if content_length > 500:
            score += 2.0
        elif content_length > 200:
            score += 1.0

        # Structure score (0-2 points)
        if document.section_number:
            score += 1.0
        if document.citations:
            score += 1.0

        # Authority score (0-2 points)
        if 'texas comptroller' in document.authority.lower():
            score += 2.0
        elif 'county' in document.authority.lower():
            score += 1.5

        # Content quality score (0-2 points)
        if re.search(r'section\s+\d+', cleaned_content, re.IGNORECASE):
            score += 1.0
        if any(concept in cleaned_content.lower() for concept in ['exemption', 'appraisal', 'protest', 'appeal']):
            score += 1.0

        # Chunking quality (0-2 points)
        if chunks and len(chunks) > 0:
            avg_chunk_size = sum(len(chunk) for chunk in chunks) / len(chunks)
            if 300 <= avg_chunk_size <= 1200:  # Good chunk size range
                score += 2.0
            elif 100 <= avg_chunk_size <= 300 or 1200 <= avg_chunk_size <= 2000:
                score += 1.0

        return min(score, max_score) / max_score  # Normalize to 0-1

    async def generate_processing_notes(self, document: ScrapedDocument, cleaned_content: str, chunks: List[str]) -> List[str]:
        """Generate notes about the processing"""
        notes = []

        # Content reduction note
        original_length = len(document.content)
        cleaned_length = len(cleaned_content)
        if cleaned_length < original_length * 0.8:
            reduction_pct = ((original_length - cleaned_length) / original_length) * 100
            notes.append(f"Content reduced by {reduction_pct:.1f}% during cleaning")

        # Chunking note
        notes.append(f"Split into {len(chunks)} chunks")

        # Document type note
        notes.append(f"Processed as {document.document_type} document")

        # Authority note
        notes.append(f"Source: {document.authority}")

        return notes

async def process_scraped_documents(documents: List[ScrapedDocument]) -> List[ProcessedDocument]:
    """Main function to process scraped documents"""
    logger.info(f"🔄 Starting document processing for {len(documents)} documents")

    processor = DocumentProcessor()
    processed_docs = await processor.process_documents_batch(documents)

    # Filter by quality score
    high_quality_docs = [doc for doc in processed_docs if doc.quality_score >= 0.3]

    logger.info(f"✅ Document processing complete: {len(high_quality_docs)}/{len(processed_docs)} high-quality documents")

    return high_quality_docs

if __name__ == "__main__":
    # Test document processing
    async def test_processor():
        # Create a sample document
        sample_doc = ScrapedDocument(
            url="https://example.com/test",
            title="Test Property Tax Document",
            content="Section 11.01. Exemption Requirements. A person is entitled to an exemption from taxation of the property if the person is disabled or is 65 or older.",
            document_type="statute",
            authority="Texas Comptroller",
            jurisdiction="Texas"
        )

        processor = DocumentProcessor()
        processed = await processor.process_document(sample_doc)

        print(f"Original content length: {len(sample_doc.content)}")
        print(f"Cleaned content length: {len(processed.cleaned_content)}")
        print(f"Number of chunks: {len(processed.chunks)}")
        print(f"Quality score: {processed.quality_score:.2f}")
        print(f"Processing notes: {processed.processing_notes}")

    asyncio.run(test_processor())