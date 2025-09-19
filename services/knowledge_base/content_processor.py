"""
Content Processor for Texas Property Tax Law
Specialized processing pipeline for legal property tax content
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import structlog
import json
from pathlib import Path

from services.data_acquisition.document_processor import ProcessedDocument
from services.vector_store.citation_tracker import PropertyTaxCitationTracker, get_citation_tracker
from .legal_text_cleaner import LegalTextCleaner
from .taxonomy_builder import PropertyTaxTaxonomyBuilder

logger = structlog.get_logger()

@dataclass
class KnowledgeEntry:
    """Represents a processed knowledge base entry"""
    entry_id: str
    title: str
    content: str
    entry_type: str  # 'statute', 'procedure', 'exemption', 'form_guide', 'faq', 'deadline'
    topic_categories: List[str]
    subtopics: List[str]
    authority_level: float
    difficulty_level: str  # 'basic', 'intermediate', 'advanced'
    target_audience: List[str]  # 'taxpayer', 'professional', 'official'
    related_entries: List[str]
    citations: List[str]
    effective_date: Optional[datetime] = None
    last_updated: datetime = None
    quality_indicators: Dict[str, float] = None
    source_documents: List[str] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
        if self.quality_indicators is None:
            self.quality_indicators = {}
        if self.source_documents is None:
            self.source_documents = []

@dataclass
class KnowledgeGraph:
    """Represents relationships between knowledge entries"""
    entries: Dict[str, KnowledgeEntry]
    relationships: Dict[str, List[Tuple[str, str, float]]]  # entry_id -> [(related_id, relationship_type, strength)]
    topic_hierarchy: Dict[str, List[str]]
    authority_chains: List[List[str]]

class PropertyTaxContentProcessor:
    """Processes legal content into structured knowledge base entries"""

    def __init__(self, storage_dir: str = "./data/knowledge_base"):
        self.logger = logger
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Processing components
        self.text_cleaner = LegalTextCleaner()
        self.taxonomy_builder = PropertyTaxTaxonomyBuilder()
        self.citation_tracker: Optional[PropertyTaxCitationTracker] = None

        # Knowledge base
        self.knowledge_entries: Dict[str, KnowledgeEntry] = {}
        self.knowledge_graph: Optional[KnowledgeGraph] = None

        # Content templates and patterns
        self.content_templates = self._build_content_templates()
        self.quality_criteria = self._build_quality_criteria()

    async def initialize(self):
        """Initialize the content processor"""
        self.citation_tracker = get_citation_tracker()
        await self.citation_tracker.load_citations_from_storage()
        await self.taxonomy_builder.initialize()
        self.logger.info("✅ Property tax content processor initialized")

    async def process_documents_to_knowledge_base(self, processed_docs: List[ProcessedDocument]) -> List[KnowledgeEntry]:
        """Process documents into structured knowledge base entries"""
        if self.citation_tracker is None:
            await self.initialize()

        self.logger.info(f"🧠 Processing {len(processed_docs)} documents into knowledge base")

        all_entries = []

        for doc in processed_docs:
            try:
                entries = await self._process_single_document(doc)
                all_entries.extend(entries)
                self.logger.info(f"📝 Created {len(entries)} knowledge entries from {doc.original_doc.title}")

            except Exception as e:
                self.logger.error(f"❌ Failed to process document {doc.original_doc.title}: {e}")
                continue

        # Build knowledge graph
        await self._build_knowledge_graph(all_entries)

        self.logger.info(f"✅ Knowledge base processing complete: {len(all_entries)} total entries")
        return all_entries

    async def _process_single_document(self, doc: ProcessedDocument) -> List[KnowledgeEntry]:
        """Process a single document into knowledge entries"""
        entries = []

        # Determine processing strategy based on document type
        if doc.original_doc.document_type == "statute":
            entries = await self._process_statute_document(doc)
        elif doc.original_doc.document_type == "procedure":
            entries = await self._process_procedure_document(doc)
        elif doc.original_doc.document_type == "form":
            entries = await self._process_form_document(doc)
        elif doc.original_doc.document_type == "faq":
            entries = await self._process_faq_document(doc)
        else:
            entries = await self._process_general_document(doc)

        # Post-process all entries
        for entry in entries:
            await self._enhance_knowledge_entry(entry, doc)

        return entries

    async def _process_statute_document(self, doc: ProcessedDocument) -> List[KnowledgeEntry]:
        """Process statute documents into knowledge entries"""
        entries = []

        # Extract citations for this document
        citations = await self.citation_tracker.extract_citations_from_document(
            doc.original_doc.url,
            doc.original_doc.title,
            doc.cleaned_content,
            doc.original_doc.authority
        )

        # Process each chunk as a potential statute section
        for i, chunk in enumerate(doc.chunks):
            if len(chunk.strip()) < 100:  # Skip very short chunks
                continue

            # Clean the legal text
            cleaned_chunk = await self.text_cleaner.clean_legal_text(chunk)

            # Identify the statute structure
            statute_info = await self._analyze_statute_structure(cleaned_chunk)

            # Categorize by legal topic
            topics = await self.taxonomy_builder.categorize_content(cleaned_chunk)

            entry_id = f"{doc.original_doc.hash}_{i}"
            title = statute_info.get('title', f"Section {statute_info.get('section_number', i+1)}")

            entry = KnowledgeEntry(
                entry_id=entry_id,
                title=title,
                content=cleaned_chunk,
                entry_type="statute",
                topic_categories=topics['primary_categories'],
                subtopics=topics['subtopics'],
                authority_level=0.95,  # Statutes have high authority
                difficulty_level=self._assess_difficulty_level(cleaned_chunk),
                target_audience=["professional", "official"],
                related_entries=[],
                citations=[c.citation_id for c in citations if chunk in doc.cleaned_content],
                effective_date=doc.original_doc.effective_date,
                source_documents=[doc.original_doc.url]
            )

            entries.append(entry)

        return entries

    async def _process_procedure_document(self, doc: ProcessedDocument) -> List[KnowledgeEntry]:
        """Process procedural documents into step-by-step entries"""
        entries = []

        # Extract procedure steps
        procedure_steps = await self._extract_procedure_steps(doc.cleaned_content)

        for i, step in enumerate(procedure_steps):
            # Clean the step content
            cleaned_step = await self.text_cleaner.clean_procedural_text(step['content'])

            # Categorize the step
            topics = await self.taxonomy_builder.categorize_content(cleaned_step)

            entry_id = f"{doc.original_doc.hash}_step_{i}"

            entry = KnowledgeEntry(
                entry_id=entry_id,
                title=step['title'],
                content=cleaned_step,
                entry_type="procedure",
                topic_categories=topics['primary_categories'],
                subtopics=topics['subtopics'],
                authority_level=0.8,
                difficulty_level="basic",  # Procedures are usually basic
                target_audience=["taxpayer", "professional"],
                related_entries=[],
                citations=[],
                source_documents=[doc.original_doc.url]
            )

            entries.append(entry)

        return entries

    async def _process_form_document(self, doc: ProcessedDocument) -> List[KnowledgeEntry]:
        """Process form documents into guidance entries"""
        entries = []

        # Extract form guidance sections
        form_sections = await self._extract_form_sections(doc.cleaned_content)

        for section in form_sections:
            # Clean the form guidance
            cleaned_section = await self.text_cleaner.clean_form_text(section['content'])

            # Categorize the form content
            topics = await self.taxonomy_builder.categorize_content(cleaned_section)

            entry_id = f"{doc.original_doc.hash}_form_{section['section_id']}"

            entry = KnowledgeEntry(
                entry_id=entry_id,
                title=f"Form Guidance: {section['title']}",
                content=cleaned_section,
                entry_type="form_guide",
                topic_categories=topics['primary_categories'],
                subtopics=topics['subtopics'],
                authority_level=0.7,
                difficulty_level="basic",
                target_audience=["taxpayer"],
                related_entries=[],
                citations=[],
                source_documents=[doc.original_doc.url]
            )

            entries.append(entry)

        return entries

    async def _process_faq_document(self, doc: ProcessedDocument) -> List[KnowledgeEntry]:
        """Process FAQ documents into Q&A entries"""
        entries = []

        # Extract Q&A pairs
        qa_pairs = await self._extract_qa_pairs(doc.cleaned_content)

        for qa in qa_pairs:
            # Clean the Q&A content
            cleaned_content = await self.text_cleaner.clean_faq_text(f"Q: {qa['question']}\nA: {qa['answer']}")

            # Categorize the Q&A
            topics = await self.taxonomy_builder.categorize_content(cleaned_content)

            entry_id = f"{doc.original_doc.hash}_qa_{qa['question_id']}"

            entry = KnowledgeEntry(
                entry_id=entry_id,
                title=f"FAQ: {qa['question'][:100]}...",
                content=cleaned_content,
                entry_type="faq",
                topic_categories=topics['primary_categories'],
                subtopics=topics['subtopics'],
                authority_level=0.6,
                difficulty_level="basic",
                target_audience=["taxpayer"],
                related_entries=[],
                citations=[],
                source_documents=[doc.original_doc.url]
            )

            entries.append(entry)

        return entries

    async def _process_general_document(self, doc: ProcessedDocument) -> List[KnowledgeEntry]:
        """Process general documents into knowledge entries"""
        entries = []

        # Process each chunk as a general knowledge entry
        for i, chunk in enumerate(doc.chunks):
            if len(chunk.strip()) < 100:
                continue

            # Clean the content
            cleaned_chunk = await self.text_cleaner.clean_general_text(chunk)

            # Categorize the content
            topics = await self.taxonomy_builder.categorize_content(cleaned_chunk)

            # Generate title from content
            title = await self._generate_title_from_content(cleaned_chunk)

            entry_id = f"{doc.original_doc.hash}_general_{i}"

            entry = KnowledgeEntry(
                entry_id=entry_id,
                title=title,
                content=cleaned_chunk,
                entry_type="general",
                topic_categories=topics['primary_categories'],
                subtopics=topics['subtopics'],
                authority_level=0.5,
                difficulty_level=self._assess_difficulty_level(cleaned_chunk),
                target_audience=["taxpayer", "professional"],
                related_entries=[],
                citations=[],
                source_documents=[doc.original_doc.url]
            )

            entries.append(entry)

        return entries

    async def _analyze_statute_structure(self, content: str) -> Dict[str, Any]:
        """Analyze statute structure and extract metadata"""
        import re

        structure = {}

        # Extract section number
        section_match = re.search(r'(?:Section|§)\s*(\d+(?:\.\d+)*)', content, re.IGNORECASE)
        if section_match:
            structure['section_number'] = section_match.group(1)

        # Extract title (usually after section number)
        title_match = re.search(r'(?:Section|§)\s*\d+(?:\.\d+)*\.?\s*([^.]+)', content, re.IGNORECASE)
        if title_match:
            structure['title'] = title_match.group(1).strip()

        # Extract subsections
        subsections = re.findall(r'\([a-z]\)', content)
        structure['subsections'] = len(subsections)

        return structure

    async def _extract_procedure_steps(self, content: str) -> List[Dict[str, Any]]:
        """Extract procedure steps from content"""
        import re

        steps = []

        # Look for numbered steps
        step_pattern = r'(\d+)\.\s*([^.]+(?:\.[^.]*)*)'
        step_matches = re.finditer(step_pattern, content, re.MULTILINE | re.DOTALL)

        for i, match in enumerate(step_matches):
            step_number = match.group(1)
            step_content = match.group(2).strip()

            steps.append({
                'step_number': int(step_number),
                'title': f"Step {step_number}",
                'content': step_content,
                'section_id': f"step_{step_number}"
            })

        # If no numbered steps found, split by paragraphs
        if not steps:
            paragraphs = content.split('\n\n')
            for i, paragraph in enumerate(paragraphs):
                if len(paragraph.strip()) > 50:
                    steps.append({
                        'step_number': i + 1,
                        'title': f"Step {i + 1}",
                        'content': paragraph.strip(),
                        'section_id': f"para_{i}"
                    })

        return steps

    async def _extract_form_sections(self, content: str) -> List[Dict[str, Any]]:
        """Extract form sections from content"""
        sections = []

        # Split by common form section headers
        import re
        section_headers = [
            r'(?:Part|Section)\s+[A-Z]\s*[:-]',
            r'\d+\.\s*[A-Z][^.]+:',
            r'[A-Z][A-Z\s]+:(?=\s)'
        ]

        current_section = None
        section_content = []

        lines = content.split('\n')
        section_id = 0

        for line in lines:
            # Check if line is a section header
            is_header = any(re.match(pattern, line.strip()) for pattern in section_headers)

            if is_header:
                # Save previous section
                if current_section and section_content:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(section_content).strip(),
                        'section_id': section_id
                    })
                    section_id += 1

                # Start new section
                current_section = line.strip()
                section_content = []
            else:
                if line.strip():
                    section_content.append(line)

        # Add final section
        if current_section and section_content:
            sections.append({
                'title': current_section,
                'content': '\n'.join(section_content).strip(),
                'section_id': section_id
            })

        return sections

    async def _extract_qa_pairs(self, content: str) -> List[Dict[str, Any]]:
        """Extract Q&A pairs from FAQ content"""
        import re

        qa_pairs = []

        # Pattern for Q&A pairs
        qa_pattern = r'(?:Q(?:uestion)?[:\.]?\s*)(.*?)(?:A(?:nswer)?[:\.]?\s*)(.*?)(?=(?:Q(?:uestion)?[:\.])|$)'
        matches = re.finditer(qa_pattern, content, re.IGNORECASE | re.DOTALL)

        question_id = 0
        for match in matches:
            question = match.group(1).strip()
            answer = match.group(2).strip()

            if question and answer:
                qa_pairs.append({
                    'question': question,
                    'answer': answer,
                    'question_id': question_id
                })
                question_id += 1

        return qa_pairs

    async def _generate_title_from_content(self, content: str) -> str:
        """Generate a title from content"""
        # Take first sentence or first 100 characters
        sentences = content.split('.')
        if sentences and len(sentences[0]) < 100:
            return sentences[0].strip()
        else:
            return content[:97].strip() + "..."

    def _assess_difficulty_level(self, content: str) -> str:
        """Assess the difficulty level of content"""
        content_lower = content.lower()

        # Count technical legal terms
        technical_terms = [
            'subsection', 'notwithstanding', 'pursuant to', 'heretofore',
            'whereas', 'thereof', 'hereunder', 'aforementioned'
        ]

        technical_count = sum(1 for term in technical_terms if term in content_lower)

        # Assess sentence complexity
        sentences = content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0

        # Determine difficulty
        if technical_count >= 3 or avg_sentence_length > 25:
            return "advanced"
        elif technical_count >= 1 or avg_sentence_length > 15:
            return "intermediate"
        else:
            return "basic"

    async def _enhance_knowledge_entry(self, entry: KnowledgeEntry, doc: ProcessedDocument):
        """Enhance knowledge entry with additional metadata"""
        # Calculate quality indicators
        entry.quality_indicators = {
            'content_length_score': min(len(entry.content) / 1000, 1.0),
            'authority_score': entry.authority_level,
            'topic_relevance_score': len(entry.topic_categories) / 5.0,
            'citation_score': len(entry.citations) / 3.0 if entry.citations else 0.0
        }

        # Set target audience based on difficulty and type
        if entry.difficulty_level == "basic" and entry.entry_type in ["faq", "form_guide"]:
            entry.target_audience = ["taxpayer"]
        elif entry.difficulty_level == "advanced" or entry.entry_type == "statute":
            entry.target_audience = ["professional", "official"]
        else:
            entry.target_audience = ["taxpayer", "professional"]

    async def _build_knowledge_graph(self, entries: List[KnowledgeEntry]):
        """Build knowledge graph showing relationships between entries"""
        self.logger.info("🕸️ Building knowledge graph")

        # Store entries
        entry_dict = {entry.entry_id: entry for entry in entries}
        self.knowledge_entries.update(entry_dict)

        # Build relationships
        relationships = {}
        for entry in entries:
            relationships[entry.entry_id] = await self._find_related_entries(entry, entries)

        # Build topic hierarchy
        topic_hierarchy = await self.taxonomy_builder.build_topic_hierarchy([
            entry.topic_categories for entry in entries
        ])

        # Build authority chains
        authority_chains = await self._build_authority_chains(entries)

        self.knowledge_graph = KnowledgeGraph(
            entries=entry_dict,
            relationships=relationships,
            topic_hierarchy=topic_hierarchy,
            authority_chains=authority_chains
        )

        self.logger.info("✅ Knowledge graph built")

    async def _find_related_entries(self, entry: KnowledgeEntry, all_entries: List[KnowledgeEntry]) -> List[Tuple[str, str, float]]:
        """Find entries related to the given entry"""
        related = []

        for other_entry in all_entries:
            if other_entry.entry_id == entry.entry_id:
                continue

            # Calculate relationship strength
            strength = 0.0

            # Topic similarity
            common_topics = set(entry.topic_categories).intersection(set(other_entry.topic_categories))
            if common_topics:
                strength += len(common_topics) / max(len(entry.topic_categories), len(other_entry.topic_categories))

            # Citation relationships
            common_citations = set(entry.citations).intersection(set(other_entry.citations))
            if common_citations:
                strength += 0.3

            # Authority relationships
            if entry.entry_type == "statute" and other_entry.entry_type in ["procedure", "form_guide"]:
                strength += 0.2
            elif entry.entry_type == other_entry.entry_type:
                strength += 0.1

            # Only include if significant relationship
            if strength > 0.3:
                relationship_type = self._determine_relationship_type(entry, other_entry)
                related.append((other_entry.entry_id, relationship_type, strength))

        # Sort by strength and limit
        related.sort(key=lambda x: x[2], reverse=True)
        return related[:10]

    def _determine_relationship_type(self, entry1: KnowledgeEntry, entry2: KnowledgeEntry) -> str:
        """Determine the type of relationship between two entries"""
        if entry1.entry_type == "statute" and entry2.entry_type == "procedure":
            return "implements"
        elif entry1.entry_type == "procedure" and entry2.entry_type == "form_guide":
            return "uses_form"
        elif entry1.entry_type == entry2.entry_type:
            return "similar_topic"
        else:
            return "related"

    async def _build_authority_chains(self, entries: List[KnowledgeEntry]) -> List[List[str]]:
        """Build chains of authority from constitutional to procedural"""
        chains = []

        # Group by authority level
        by_authority = {}
        for entry in entries:
            level = entry.authority_level
            if level not in by_authority:
                by_authority[level] = []
            by_authority[level].append(entry.entry_id)

        # Build chains from highest to lowest authority
        authority_levels = sorted(by_authority.keys(), reverse=True)
        if len(authority_levels) > 1:
            chains.append([by_authority[level][0] for level in authority_levels if by_authority[level]])

        return chains

    def _build_content_templates(self) -> Dict[str, str]:
        """Build content templates for different entry types"""
        return {
            'statute': "Legal Statute: {title}\n\nSection {section}: {content}\n\nAuthority: {authority}",
            'procedure': "Procedure: {title}\n\nSteps:\n{content}\n\nRequired for: {topics}",
            'form_guide': "Form Guide: {title}\n\nInstructions:\n{content}\n\nRelated Forms: {related}",
            'faq': "Frequently Asked Question\n\nQ: {question}\nA: {answer}\n\nTopic: {topics}",
            'deadline': "Important Deadline: {title}\n\nDate: {date}\nDetails: {content}\n\nConsequences: {penalties}"
        }

    def _build_quality_criteria(self) -> Dict[str, Dict[str, float]]:
        """Build quality criteria for different content types"""
        return {
            'statute': {
                'min_content_length': 200,
                'citation_weight': 0.4,
                'authority_weight': 0.3,
                'topic_relevance_weight': 0.3
            },
            'procedure': {
                'min_content_length': 150,
                'citation_weight': 0.2,
                'authority_weight': 0.3,
                'topic_relevance_weight': 0.5
            },
            'form_guide': {
                'min_content_length': 100,
                'citation_weight': 0.1,
                'authority_weight': 0.2,
                'topic_relevance_weight': 0.7
            },
            'faq': {
                'min_content_length': 50,
                'citation_weight': 0.1,
                'authority_weight': 0.2,
                'topic_relevance_weight': 0.7
            }
        }

    async def save_knowledge_base(self):
        """Save knowledge base to storage"""
        self.logger.info("💾 Saving knowledge base")

        # Save knowledge entries
        entries_file = self.storage_dir / "knowledge_entries.json"
        entries_data = {
            entry_id: {
                'entry_id': entry.entry_id,
                'title': entry.title,
                'content': entry.content,
                'entry_type': entry.entry_type,
                'topic_categories': entry.topic_categories,
                'subtopics': entry.subtopics,
                'authority_level': entry.authority_level,
                'difficulty_level': entry.difficulty_level,
                'target_audience': entry.target_audience,
                'related_entries': entry.related_entries,
                'citations': entry.citations,
                'effective_date': entry.effective_date.isoformat() if entry.effective_date else None,
                'last_updated': entry.last_updated.isoformat() if entry.last_updated else None,
                'quality_indicators': entry.quality_indicators,
                'source_documents': entry.source_documents
            }
            for entry_id, entry in self.knowledge_entries.items()
        }

        with open(entries_file, 'w') as f:
            json.dump(entries_data, f, indent=2)

        # Save knowledge graph
        if self.knowledge_graph:
            graph_file = self.storage_dir / "knowledge_graph.json"
            graph_data = {
                'relationships': self.knowledge_graph.relationships,
                'topic_hierarchy': self.knowledge_graph.topic_hierarchy,
                'authority_chains': self.knowledge_graph.authority_chains
            }

            with open(graph_file, 'w') as f:
                json.dump(graph_data, f, indent=2)

        self.logger.info("✅ Knowledge base saved")

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        stats = {
            'total_entries': len(self.knowledge_entries),
            'entries_by_type': {},
            'entries_by_difficulty': {},
            'entries_by_audience': {},
            'avg_authority_level': 0.0,
            'total_topics': 0,
            'total_relationships': 0
        }

        if not self.knowledge_entries:
            return stats

        # Count by type
        for entry in self.knowledge_entries.values():
            entry_type = entry.entry_type
            stats['entries_by_type'][entry_type] = stats['entries_by_type'].get(entry_type, 0) + 1

            difficulty = entry.difficulty_level
            stats['entries_by_difficulty'][difficulty] = stats['entries_by_difficulty'].get(difficulty, 0) + 1

            for audience in entry.target_audience:
                stats['entries_by_audience'][audience] = stats['entries_by_audience'].get(audience, 0) + 1

        # Calculate averages
        stats['avg_authority_level'] = sum(e.authority_level for e in self.knowledge_entries.values()) / len(self.knowledge_entries)

        # Count topics and relationships
        all_topics = set()
        total_relationships = 0

        for entry in self.knowledge_entries.values():
            all_topics.update(entry.topic_categories)

        if self.knowledge_graph:
            total_relationships = sum(len(rels) for rels in self.knowledge_graph.relationships.values())

        stats['total_topics'] = len(all_topics)
        stats['total_relationships'] = total_relationships

        return stats

# Global instance
_content_processor = None

async def get_content_processor() -> PropertyTaxContentProcessor:
    """Get the global content processor instance"""
    global _content_processor
    if _content_processor is None:
        _content_processor = PropertyTaxContentProcessor()
        await _content_processor.initialize()
    return _content_processor

if __name__ == "__main__":
    # Test content processor
    async def test_processor():
        processor = PropertyTaxContentProcessor()
        await processor.initialize()

        # Get stats
        stats = processor.get_knowledge_base_stats()
        print(f"Knowledge base stats: {stats}")

    asyncio.run(test_processor())