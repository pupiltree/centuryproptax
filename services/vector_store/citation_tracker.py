"""
Citation Tracker for Legal References
Tracks and manages legal citations, cross-references, and authority relationships
"""

import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import structlog
import re
import json
from pathlib import Path
from collections import defaultdict

logger = structlog.get_logger()

@dataclass
class LegalCitation:
    """Represents a legal citation with metadata"""
    citation_id: str
    citation_text: str
    citation_type: str  # 'statute', 'code', 'regulation', 'case', 'administrative'
    source_document_url: str
    source_document_title: str
    section_number: Optional[str] = None
    subsection: Optional[str] = None
    title_number: Optional[str] = None
    chapter_number: Optional[str] = None
    authority: str = "Texas"
    effective_date: Optional[datetime] = None
    status: str = "active"  # 'active', 'superseded', 'repealed', 'pending'
    cross_references: List[str] = field(default_factory=list)
    cited_by: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)

@dataclass
class CitationRelationship:
    """Represents a relationship between citations"""
    from_citation_id: str
    to_citation_id: str
    relationship_type: str  # 'amends', 'supersedes', 'references', 'implements', 'authorizes'
    strength: float  # 0.0 to 1.0 indicating relationship strength
    context: Optional[str] = None

@dataclass
class CitationNetwork:
    """Network of related citations"""
    primary_citation_id: str
    related_citations: List[str]
    network_type: str  # 'hierarchy', 'topic_cluster', 'amendment_chain'
    authority_level: float  # 0.0 to 1.0, higher = more authoritative

class PropertyTaxCitationTracker:
    """Tracks and manages legal citations in property tax documents"""

    def __init__(self, storage_dir: str = "./data/citations"):
        self.logger = logger
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory citation index
        self.citations: Dict[str, LegalCitation] = {}
        self.relationships: List[CitationRelationship] = []
        self.citation_networks: List[CitationNetwork] = []

        # Citation patterns for Texas property tax law
        self.citation_patterns = self._build_citation_patterns()

        # Authority hierarchy
        self.authority_hierarchy = self._build_authority_hierarchy()

    def _build_citation_patterns(self) -> Dict[str, str]:
        """Build regex patterns for different citation types"""
        return {
            'texas_property_tax_code': r'(?:Texas\s+)?Prop(?:erty)?\.?\s+Tax\s+Code\s+(?:Section|§|Sec\.?)\s*(\d+(?:\.\d+)*)',
            'texas_tax_code': r'(?:Texas\s+)?Tax\s+Code\s+(?:Section|§|Sec\.?)\s*(\d+(?:\.\d+)*)',
            'texas_government_code': r'(?:Texas\s+)?Gov(?:ernment)?\.?\s+Code\s+(?:Section|§|Sec\.?)\s*(\d+(?:\.\d+)*)',
            'texas_local_government_code': r'(?:Texas\s+)?Local\s+Gov(?:ernment)?\.?\s+Code\s+(?:Section|§|Sec\.?)\s*(\d+(?:\.\d+)*)',
            'texas_constitution': r'(?:Texas\s+)?Const(?:itution)?\.?\s+[Aa]rt(?:icle)?\.?\s*([IVXLC]+)(?:\s*[,§]\s*[Ss]ec(?:tion)?\.?\s*(\d+))?',
            'administrative_code': r'(?:Texas\s+)?Admin(?:istrative)?\.?\s+Code\s+(?:Title\s*)?(\d+)\s*(?:Part\s*)?(\d+)?\s*(?:Chapter\s*)?(\d+)?',
            'comptroller_rule': r'(?:Comptroller\s+)?Rule\s+(\d+(?:\.\d+)*)',
            'section_reference': r'(?:Section|§|Sec\.?)\s*(\d+(?:\.\d+)*)',
            'chapter_reference': r'Chapter\s+(\d+)',
            'title_reference': r'Title\s+(\d+)',
        }

    def _build_authority_hierarchy(self) -> Dict[str, float]:
        """Build authority hierarchy with scores"""
        return {
            'texas_constitution': 1.0,
            'texas_property_tax_code': 0.95,
            'texas_tax_code': 0.9,
            'texas_government_code': 0.85,
            'texas_local_government_code': 0.8,
            'administrative_code': 0.75,
            'comptroller_rule': 0.7,
            'county_ordinance': 0.6,
            'appraisal_district_policy': 0.5,
            'general_reference': 0.3
        }

    async def extract_citations_from_document(self, document_url: str, document_title: str,
                                            content: str, authority: str = "Texas") -> List[LegalCitation]:
        """Extract legal citations from document content"""
        self.logger.info(f"📋 Extracting citations from: {document_title}")

        citations = []
        citation_id_counter = 0

        for pattern_name, pattern in self.citation_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)

            for match in matches:
                citation_id_counter += 1
                citation_id = f"{document_url}#{citation_id_counter}"

                # Extract citation details
                citation_text = match.group(0)
                section_number = match.group(1) if match.groups() else None

                # Determine citation type and extract additional details
                citation_type, title_num, chapter_num, subsection = self._parse_citation_details(
                    pattern_name, match, citation_text
                )

                # Extract surrounding context for topics
                context_start = max(0, match.start() - 100)
                context_end = min(len(content), match.end() + 100)
                context = content[context_start:context_end]
                topics = self._extract_topics_from_context(context)

                citation = LegalCitation(
                    citation_id=citation_id,
                    citation_text=citation_text,
                    citation_type=citation_type,
                    source_document_url=document_url,
                    source_document_title=document_title,
                    section_number=section_number,
                    subsection=subsection,
                    title_number=title_num,
                    chapter_number=chapter_num,
                    authority=authority,
                    topics=topics
                )

                citations.append(citation)
                self.citations[citation_id] = citation

        self.logger.info(f"✅ Extracted {len(citations)} citations from document")
        return citations

    def _parse_citation_details(self, pattern_name: str, match, citation_text: str) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
        """Parse detailed citation information"""
        citation_type = "general"
        title_number = None
        chapter_number = None
        subsection = None

        if pattern_name == "texas_property_tax_code":
            citation_type = "statute"
        elif pattern_name == "texas_tax_code":
            citation_type = "statute"
        elif pattern_name == "texas_constitution":
            citation_type = "constitutional"
            title_number = match.group(1) if len(match.groups()) >= 1 else None
            subsection = match.group(2) if len(match.groups()) >= 2 else None
        elif pattern_name == "administrative_code":
            citation_type = "regulation"
            title_number = match.group(1) if len(match.groups()) >= 1 else None
            chapter_number = match.group(3) if len(match.groups()) >= 3 else None
        elif pattern_name == "comptroller_rule":
            citation_type = "administrative"

        return citation_type, title_number, chapter_number, subsection

    def _extract_topics_from_context(self, context: str) -> List[str]:
        """Extract property tax topics from citation context"""
        topics = []
        context_lower = context.lower()

        topic_keywords = {
            'exemption': ['exemption', 'exempt', 'homestead', 'disability', 'senior', 'veteran', 'agricultural'],
            'appraisal': ['appraisal', 'assessment', 'value', 'valuation', 'market value'],
            'protest': ['protest', 'appeal', 'challenge', 'hearing', 'review board'],
            'collection': ['collection', 'payment', 'delinquent', 'penalty', 'interest'],
            'taxation': ['tax', 'taxation', 'levy', 'rate', 'millage'],
            'procedure': ['procedure', 'process', 'deadline', 'filing', 'application'],
            'authority': ['district', 'comptroller', 'county', 'appraisal district'],
            'property_types': ['residential', 'commercial', 'industrial', 'agricultural', 'personal property']
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                topics.append(topic)

        return topics

    async def build_citation_relationships(self) -> List[CitationRelationship]:
        """Build relationships between citations"""
        self.logger.info("🔗 Building citation relationships")

        relationships = []

        # Build relationships based on hierarchical references
        relationships.extend(await self._build_hierarchical_relationships())

        # Build topical relationships
        relationships.extend(await self._build_topical_relationships())

        # Build amendment/supersession relationships
        relationships.extend(await self._build_amendment_relationships())

        # Store relationships
        self.relationships = relationships

        self.logger.info(f"✅ Built {len(relationships)} citation relationships")
        return relationships

    async def _build_hierarchical_relationships(self) -> List[CitationRelationship]:
        """Build hierarchical relationships between citations"""
        relationships = []

        # Group citations by type and authority
        statute_citations = [c for c in self.citations.values() if c.citation_type == "statute"]
        regulation_citations = [c for c in self.citations.values() if c.citation_type == "regulation"]

        # Regulations implement statutes
        for reg_citation in regulation_citations:
            for stat_citation in statute_citations:
                # Simple heuristic: if topics overlap, there might be an implementation relationship
                topic_overlap = set(reg_citation.topics).intersection(set(stat_citation.topics))
                if topic_overlap:
                    strength = len(topic_overlap) / max(len(reg_citation.topics), len(stat_citation.topics))

                    relationship = CitationRelationship(
                        from_citation_id=reg_citation.citation_id,
                        to_citation_id=stat_citation.citation_id,
                        relationship_type="implements",
                        strength=strength,
                        context=f"Topics: {', '.join(topic_overlap)}"
                    )
                    relationships.append(relationship)

        return relationships

    async def _build_topical_relationships(self) -> List[CitationRelationship]:
        """Build relationships based on topical similarity"""
        relationships = []

        # Group citations by topics
        topic_groups = defaultdict(list)
        for citation in self.citations.values():
            for topic in citation.topics:
                topic_groups[topic].append(citation)

        # Create relationships within topic groups
        for topic, citations in topic_groups.items():
            if len(citations) > 1:
                for i, citation1 in enumerate(citations):
                    for citation2 in citations[i+1:]:
                        # Calculate relationship strength based on authority levels
                        auth1_score = self.authority_hierarchy.get(citation1.citation_type, 0.3)
                        auth2_score = self.authority_hierarchy.get(citation2.citation_type, 0.3)
                        strength = (auth1_score + auth2_score) / 2

                        relationship = CitationRelationship(
                            from_citation_id=citation1.citation_id,
                            to_citation_id=citation2.citation_id,
                            relationship_type="topic_related",
                            strength=strength,
                            context=f"Common topic: {topic}"
                        )
                        relationships.append(relationship)

        return relationships

    async def _build_amendment_relationships(self) -> List[CitationRelationship]:
        """Build amendment and supersession relationships"""
        relationships = []

        # Look for amendment language in citation contexts
        amendment_patterns = [
            r'(?:amend|amending|amended by|supersede|superseded by|replace|replaced by)',
            r'(?:as amended|as modified|as updated)',
            r'(?:repeal|repealed by|void|invalid)'
        ]

        for citation in self.citations.values():
            # Check source document content for amendment language
            # This would require access to the full document content
            # For now, we'll create placeholder relationships based on section numbers

            if citation.section_number:
                # Look for other citations with similar section numbers (potential amendments)
                similar_citations = [
                    c for c in self.citations.values()
                    if c.citation_id != citation.citation_id
                    and c.section_number == citation.section_number
                    and c.citation_type == citation.citation_type
                ]

                for similar_citation in similar_citations:
                    relationship = CitationRelationship(
                        from_citation_id=citation.citation_id,
                        to_citation_id=similar_citation.citation_id,
                        relationship_type="references",
                        strength=0.8,
                        context="Same section number"
                    )
                    relationships.append(relationship)

        return relationships

    async def build_citation_networks(self) -> List[CitationNetwork]:
        """Build networks of related citations"""
        self.logger.info("🕸️ Building citation networks")

        networks = []

        # Build topic-based networks
        networks.extend(await self._build_topic_networks())

        # Build authority-based networks
        networks.extend(await self._build_authority_networks())

        # Build hierarchical networks
        networks.extend(await self._build_hierarchical_networks())

        self.citation_networks = networks

        self.logger.info(f"✅ Built {len(networks)} citation networks")
        return networks

    async def _build_topic_networks(self) -> List[CitationNetwork]:
        """Build networks based on topics"""
        networks = []

        # Group citations by topics
        topic_groups = defaultdict(list)
        for citation in self.citations.values():
            for topic in citation.topics:
                topic_groups[topic].append(citation.citation_id)

        # Create networks for topics with multiple citations
        for topic, citation_ids in topic_groups.items():
            if len(citation_ids) >= 3:  # Only create networks with 3+ citations
                # Find the most authoritative citation as primary
                primary_citation_id = max(
                    citation_ids,
                    key=lambda cid: self.authority_hierarchy.get(
                        self.citations[cid].citation_type, 0.3
                    )
                )

                authority_level = self.authority_hierarchy.get(
                    self.citations[primary_citation_id].citation_type, 0.3
                )

                network = CitationNetwork(
                    primary_citation_id=primary_citation_id,
                    related_citations=citation_ids,
                    network_type="topic_cluster",
                    authority_level=authority_level
                )
                networks.append(network)

        return networks

    async def _build_authority_networks(self) -> List[CitationNetwork]:
        """Build networks based on authority hierarchy"""
        networks = []

        # Group by citation type (authority level)
        authority_groups = defaultdict(list)
        for citation in self.citations.values():
            authority_groups[citation.citation_type].append(citation.citation_id)

        # Create networks for each authority type with multiple citations
        for authority_type, citation_ids in authority_groups.items():
            if len(citation_ids) >= 2:
                authority_level = self.authority_hierarchy.get(authority_type, 0.3)

                # Primary citation is the first one (could be improved)
                primary_citation_id = citation_ids[0]

                network = CitationNetwork(
                    primary_citation_id=primary_citation_id,
                    related_citations=citation_ids,
                    network_type="authority_cluster",
                    authority_level=authority_level
                )
                networks.append(network)

        return networks

    async def _build_hierarchical_networks(self) -> List[CitationNetwork]:
        """Build hierarchical citation networks"""
        networks = []

        # Find constitutional and statutory foundations
        constitutional_citations = [
            c for c in self.citations.values()
            if c.citation_type == "constitutional"
        ]

        for const_citation in constitutional_citations:
            # Find all related citations
            related_citations = [const_citation.citation_id]

            # Add implementing statutes
            for relationship in self.relationships:
                if (relationship.to_citation_id == const_citation.citation_id and
                    relationship.relationship_type == "implements"):
                    related_citations.append(relationship.from_citation_id)

            if len(related_citations) > 1:
                network = CitationNetwork(
                    primary_citation_id=const_citation.citation_id,
                    related_citations=related_citations,
                    network_type="hierarchy",
                    authority_level=1.0
                )
                networks.append(network)

        return networks

    async def find_citations_by_topic(self, topic: str) -> List[LegalCitation]:
        """Find citations related to a specific topic"""
        matching_citations = [
            citation for citation in self.citations.values()
            if topic.lower() in [t.lower() for t in citation.topics]
        ]

        # Sort by authority level
        matching_citations.sort(
            key=lambda c: self.authority_hierarchy.get(c.citation_type, 0.3),
            reverse=True
        )

        return matching_citations

    async def get_citation_authority_score(self, citation_id: str) -> float:
        """Get authority score for a citation"""
        if citation_id not in self.citations:
            return 0.0

        citation = self.citations[citation_id]
        base_score = self.authority_hierarchy.get(citation.citation_type, 0.3)

        # Boost score based on how many times it's cited by others
        cited_by_count = len(citation.cited_by)
        citation_boost = min(cited_by_count * 0.05, 0.2)

        return min(base_score + citation_boost, 1.0)

    async def get_related_citations(self, citation_id: str, max_results: int = 10) -> List[Tuple[LegalCitation, float]]:
        """Get citations related to a given citation"""
        if citation_id not in self.citations:
            return []

        related = []

        # Find direct relationships
        for relationship in self.relationships:
            related_id = None
            if relationship.from_citation_id == citation_id:
                related_id = relationship.to_citation_id
            elif relationship.to_citation_id == citation_id:
                related_id = relationship.from_citation_id

            if related_id and related_id in self.citations:
                related.append((self.citations[related_id], relationship.strength))

        # Sort by relationship strength
        related.sort(key=lambda x: x[1], reverse=True)

        return related[:max_results]

    async def save_citations_to_storage(self):
        """Save citations and relationships to persistent storage"""
        self.logger.info("💾 Saving citations to storage")

        # Save citations
        citations_file = self.storage_dir / "citations.json"
        citations_data = {
            cid: {
                'citation_id': c.citation_id,
                'citation_text': c.citation_text,
                'citation_type': c.citation_type,
                'source_document_url': c.source_document_url,
                'source_document_title': c.source_document_title,
                'section_number': c.section_number,
                'subsection': c.subsection,
                'title_number': c.title_number,
                'chapter_number': c.chapter_number,
                'authority': c.authority,
                'effective_date': c.effective_date.isoformat() if c.effective_date else None,
                'status': c.status,
                'cross_references': c.cross_references,
                'cited_by': c.cited_by,
                'topics': c.topics
            }
            for cid, c in self.citations.items()
        }

        with open(citations_file, 'w') as f:
            json.dump(citations_data, f, indent=2)

        # Save relationships
        relationships_file = self.storage_dir / "relationships.json"
        relationships_data = [
            {
                'from_citation_id': r.from_citation_id,
                'to_citation_id': r.to_citation_id,
                'relationship_type': r.relationship_type,
                'strength': r.strength,
                'context': r.context
            }
            for r in self.relationships
        ]

        with open(relationships_file, 'w') as f:
            json.dump(relationships_data, f, indent=2)

        # Save networks
        networks_file = self.storage_dir / "networks.json"
        networks_data = [
            {
                'primary_citation_id': n.primary_citation_id,
                'related_citations': n.related_citations,
                'network_type': n.network_type,
                'authority_level': n.authority_level
            }
            for n in self.citation_networks
        ]

        with open(networks_file, 'w') as f:
            json.dump(networks_data, f, indent=2)

        self.logger.info("✅ Citations saved to storage")

    async def load_citations_from_storage(self):
        """Load citations and relationships from persistent storage"""
        self.logger.info("📂 Loading citations from storage")

        try:
            # Load citations
            citations_file = self.storage_dir / "citations.json"
            if citations_file.exists():
                with open(citations_file, 'r') as f:
                    citations_data = json.load(f)

                for cid, data in citations_data.items():
                    citation = LegalCitation(
                        citation_id=data['citation_id'],
                        citation_text=data['citation_text'],
                        citation_type=data['citation_type'],
                        source_document_url=data['source_document_url'],
                        source_document_title=data['source_document_title'],
                        section_number=data.get('section_number'),
                        subsection=data.get('subsection'),
                        title_number=data.get('title_number'),
                        chapter_number=data.get('chapter_number'),
                        authority=data.get('authority', 'Texas'),
                        effective_date=datetime.fromisoformat(data['effective_date']) if data.get('effective_date') else None,
                        status=data.get('status', 'active'),
                        cross_references=data.get('cross_references', []),
                        cited_by=data.get('cited_by', []),
                        topics=data.get('topics', [])
                    )
                    self.citations[cid] = citation

            # Load relationships
            relationships_file = self.storage_dir / "relationships.json"
            if relationships_file.exists():
                with open(relationships_file, 'r') as f:
                    relationships_data = json.load(f)

                self.relationships = [
                    CitationRelationship(
                        from_citation_id=data['from_citation_id'],
                        to_citation_id=data['to_citation_id'],
                        relationship_type=data['relationship_type'],
                        strength=data['strength'],
                        context=data.get('context')
                    )
                    for data in relationships_data
                ]

            # Load networks
            networks_file = self.storage_dir / "networks.json"
            if networks_file.exists():
                with open(networks_file, 'r') as f:
                    networks_data = json.load(f)

                self.citation_networks = [
                    CitationNetwork(
                        primary_citation_id=data['primary_citation_id'],
                        related_citations=data['related_citations'],
                        network_type=data['network_type'],
                        authority_level=data['authority_level']
                    )
                    for data in networks_data
                ]

            self.logger.info(f"✅ Loaded {len(self.citations)} citations, {len(self.relationships)} relationships, {len(self.citation_networks)} networks")

        except Exception as e:
            self.logger.error(f"❌ Failed to load citations from storage: {e}")

    def get_citation_stats(self) -> Dict[str, Any]:
        """Get statistics about the citation database"""
        stats = {
            'total_citations': len(self.citations),
            'total_relationships': len(self.relationships),
            'total_networks': len(self.citation_networks),
            'citations_by_type': defaultdict(int),
            'citations_by_authority': defaultdict(int),
            'citations_by_topic': defaultdict(int)
        }

        for citation in self.citations.values():
            stats['citations_by_type'][citation.citation_type] += 1
            stats['citations_by_authority'][citation.authority] += 1
            for topic in citation.topics:
                stats['citations_by_topic'][topic] += 1

        # Convert defaultdicts to regular dicts
        stats['citations_by_type'] = dict(stats['citations_by_type'])
        stats['citations_by_authority'] = dict(stats['citations_by_authority'])
        stats['citations_by_topic'] = dict(stats['citations_by_topic'])

        return stats

# Global instance
_citation_tracker = None

def get_citation_tracker() -> PropertyTaxCitationTracker:
    """Get the global citation tracker instance"""
    global _citation_tracker
    if _citation_tracker is None:
        _citation_tracker = PropertyTaxCitationTracker()
    return _citation_tracker

if __name__ == "__main__":
    # Test citation tracker
    async def test_citation_tracker():
        tracker = PropertyTaxCitationTracker()

        # Test citation extraction
        sample_content = """
        Section 11.13 of the Texas Property Tax Code provides for homestead exemptions.
        This is implemented by Comptroller Rule 9.4301. See also Tax Code Section 1.07
        and Article VIII, Section 1 of the Texas Constitution.
        """

        citations = await tracker.extract_citations_from_document(
            "https://example.com/test",
            "Test Document",
            sample_content
        )

        print(f"Extracted {len(citations)} citations:")
        for citation in citations:
            print(f"  {citation.citation_text} ({citation.citation_type})")
            print(f"    Topics: {citation.topics}")

        # Build relationships
        relationships = await tracker.build_citation_relationships()
        print(f"Built {len(relationships)} relationships")

        # Build networks
        networks = await tracker.build_citation_networks()
        print(f"Built {len(networks)} networks")

        # Get stats
        stats = tracker.get_citation_stats()
        print(f"Citation stats: {stats}")

    asyncio.run(test_citation_tracker())