"""
Property Tax Taxonomy Builder
Builds hierarchical taxonomy and categorizes content for Texas property tax law
"""

import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import structlog
import json
from pathlib import Path
from collections import defaultdict, Counter
import re

logger = structlog.get_logger()

@dataclass
class TaxonomyNode:
    """Represents a node in the property tax taxonomy"""
    node_id: str
    name: str
    description: str
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    content_count: int = 0
    authority_level: float = 0.0
    complexity_level: str = "basic"  # basic, intermediate, advanced

@dataclass
class ContentCategory:
    """Represents content categorization result"""
    primary_categories: List[str]
    secondary_categories: List[str]
    subtopics: List[str]
    confidence_scores: Dict[str, float]
    detected_keywords: List[str]
    classification_reasoning: str

class PropertyTaxTaxonomyBuilder:
    """Builds and manages taxonomy for Texas property tax content"""

    def __init__(self, storage_dir: str = "./data/taxonomy"):
        self.logger = logger
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Taxonomy structure
        self.taxonomy_nodes: Dict[str, TaxonomyNode] = {}
        self.root_categories: List[str] = []

        # Content classification components
        self.keyword_patterns = {}
        self.classification_rules = {}
        self.topic_hierarchies = {}

    async def initialize(self):
        """Initialize the taxonomy builder"""
        await self._build_base_taxonomy()
        await self._load_classification_patterns()
        self.logger.info("✅ Property tax taxonomy builder initialized")

    async def _build_base_taxonomy(self):
        """Build the base taxonomy structure for Texas property tax law"""
        # Root level categories
        root_categories = [
            "property_taxation",
            "exemptions",
            "appraisal_and_assessment",
            "appeals_and_protests",
            "collection_and_enforcement",
            "legal_framework",
            "procedures_and_deadlines",
            "property_types",
            "authorities_and_jurisdictions"
        ]

        self.root_categories = root_categories

        # Build detailed taxonomy tree
        await self._build_property_taxation_taxonomy()
        await self._build_exemptions_taxonomy()
        await self._build_appraisal_taxonomy()
        await self._build_appeals_taxonomy()
        await self._build_collection_taxonomy()
        await self._build_legal_framework_taxonomy()
        await self._build_procedures_taxonomy()
        await self._build_property_types_taxonomy()
        await self._build_authorities_taxonomy()

        self.logger.info(f"✅ Built taxonomy with {len(self.taxonomy_nodes)} nodes")

    async def _build_property_taxation_taxonomy(self):
        """Build property taxation category taxonomy"""
        # Main category
        self._add_taxonomy_node(
            "property_taxation",
            "Property Taxation",
            "General property taxation concepts and principles",
            keywords=["property tax", "taxation", "tax", "levy", "millage"],
            complexity_level="basic"
        )

        # Subcategories
        subcategories = [
            ("tax_rates", "Tax Rates", "Property tax rates and millage calculations",
             ["tax rate", "millage", "levy", "mill rate"], "intermediate"),
            ("tax_bills", "Tax Bills and Notices", "Property tax bills and billing notices",
             ["tax bill", "notice", "billing", "statement"], "basic"),
            ("payment_methods", "Payment Methods", "Ways to pay property taxes",
             ["payment", "pay", "installment", "online payment"], "basic"),
            ("calculations", "Tax Calculations", "How property taxes are calculated",
             ["calculation", "formula", "compute", "determine"], "intermediate")
        ]

        for node_id, name, desc, keywords, complexity in subcategories:
            self._add_taxonomy_node(node_id, name, desc, parent_id="property_taxation",
                                  keywords=keywords, complexity_level=complexity)

    async def _build_exemptions_taxonomy(self):
        """Build exemptions category taxonomy"""
        self._add_taxonomy_node(
            "exemptions",
            "Property Tax Exemptions",
            "Various types of property tax exemptions available",
            keywords=["exemption", "exempt", "reduction", "deduction"],
            complexity_level="intermediate"
        )

        exemption_types = [
            ("homestead_exemption", "Homestead Exemptions", "Residence homestead exemptions",
             ["homestead", "residence", "home", "primary residence"], "basic"),
            ("senior_exemptions", "Senior Citizen Exemptions", "Exemptions for seniors 65 and older",
             ["senior", "elderly", "65", "over 65", "age"], "basic"),
            ("disability_exemptions", "Disability Exemptions", "Exemptions for disabled persons",
             ["disability", "disabled", "handicapped"], "basic"),
            ("veteran_exemptions", "Veteran Exemptions", "Exemptions for veterans",
             ["veteran", "military", "disabled veteran"], "basic"),
            ("agricultural_exemptions", "Agricultural Exemptions", "Agricultural use exemptions",
             ["agricultural", "farm", "ranch", "ag use", "1-d-1"], "intermediate"),
            ("charitable_exemptions", "Charitable Exemptions", "Exemptions for charitable organizations",
             ["charitable", "nonprofit", "religious", "church"], "intermediate"),
            ("freeport_exemptions", "Freeport Exemptions", "Freeport goods exemptions",
             ["freeport", "inventory", "goods in transit"], "advanced")
        ]

        for node_id, name, desc, keywords, complexity in exemption_types:
            self._add_taxonomy_node(node_id, name, desc, parent_id="exemptions",
                                  keywords=keywords, complexity_level=complexity)

        # Homestead exemption subcategories
        homestead_subcategories = [
            ("general_homestead", "General Homestead", "$25,000 general homestead exemption"),
            ("school_homestead", "School District Homestead", "Additional $25,000 school exemption"),
            ("senior_school_freeze", "Senior School Tax Freeze", "School tax freeze for seniors"),
            ("disability_improvements", "Disability Improvements", "Exemption for disability improvements")
        ]

        for node_id, name, desc in homestead_subcategories:
            self._add_taxonomy_node(node_id, name, desc, parent_id="homestead_exemption")

    async def _build_appraisal_taxonomy(self):
        """Build appraisal and assessment taxonomy"""
        self._add_taxonomy_node(
            "appraisal_and_assessment",
            "Appraisal and Assessment",
            "Property appraisal, assessment, and valuation processes",
            keywords=["appraisal", "assessment", "value", "valuation"],
            complexity_level="intermediate"
        )

        appraisal_subcategories = [
            ("market_value", "Market Value", "Fair market value determination",
             ["market value", "fair market value", "fmv"], "intermediate"),
            ("appraisal_methods", "Appraisal Methods", "Methods used to appraise property",
             ["cost approach", "sales comparison", "income approach"], "advanced"),
            ("appraisal_districts", "Appraisal Districts", "County appraisal districts",
             ["CAD", "appraisal district", "county appraisal"], "basic"),
            ("appraisal_notices", "Appraisal Notices", "Notices of appraised value",
             ["notice", "NOV", "appraisal notice"], "basic"),
            ("rendition", "Rendition", "Business personal property rendition",
             ["rendition", "business personal property", "BPP"], "intermediate")
        ]

        for node_id, name, desc, keywords, complexity in appraisal_subcategories:
            self._add_taxonomy_node(node_id, name, desc, parent_id="appraisal_and_assessment",
                                  keywords=keywords, complexity_level=complexity)

    async def _build_appeals_taxonomy(self):
        """Build appeals and protests taxonomy"""
        self._add_taxonomy_node(
            "appeals_and_protests",
            "Appeals and Protests",
            "Property tax protest and appeal processes",
            keywords=["protest", "appeal", "challenge", "dispute"],
            complexity_level="intermediate"
        )

        appeals_subcategories = [
            ("protest_process", "Protest Process", "How to protest property valuations",
             ["protest", "challenge", "dispute"], "intermediate"),
            ("informal_review", "Informal Review", "Informal review process",
             ["informal", "informal review", "preliminary"], "basic"),
            ("arb_hearing", "ARB Hearing", "Appraisal Review Board hearing process",
             ["ARB", "hearing", "formal hearing", "review board"], "intermediate"),
            ("evidence", "Evidence and Documentation", "Evidence needed for protests",
             ["evidence", "documentation", "proof", "comparable sales"], "intermediate"),
            ("deadlines", "Protest Deadlines", "Important deadlines for protests",
             ["deadline", "due date", "filing deadline"], "basic"),
            ("representation", "Representation", "Using agents or attorneys",
             ["agent", "attorney", "representative"], "intermediate")
        ]

        for node_id, name, desc, keywords, complexity in appeals_subcategories:
            self._add_taxonomy_node(node_id, name, desc, parent_id="appeals_and_protests",
                                  keywords=keywords, complexity_level=complexity)

    async def _build_collection_taxonomy(self):
        """Build collection and enforcement taxonomy"""
        self._add_taxonomy_node(
            "collection_and_enforcement",
            "Collection and Enforcement",
            "Tax collection, delinquency, and enforcement",
            keywords=["collection", "delinquent", "penalty", "interest"],
            complexity_level="intermediate"
        )

        collection_subcategories = [
            ("delinquency", "Delinquent Taxes", "Delinquent tax consequences",
             ["delinquent", "overdue", "late", "unpaid"], "basic"),
            ("penalties_interest", "Penalties and Interest", "Penalties and interest on delinquent taxes",
             ["penalty", "interest", "charges"], "basic"),
            ("payment_plans", "Payment Plans", "Installment payment agreements",
             ["payment plan", "installment", "agreement"], "basic"),
            ("tax_liens", "Tax Liens", "Property tax liens",
             ["lien", "tax lien", "lien certificate"], "intermediate"),
            ("tax_sales", "Tax Sales", "Tax foreclosure sales",
             ["tax sale", "foreclosure", "sheriff sale"], "advanced")
        ]

        for node_id, name, desc, keywords, complexity in collection_subcategories:
            self._add_taxonomy_node(node_id, name, desc, parent_id="collection_and_enforcement",
                                  keywords=keywords, complexity_level=complexity)

    async def _build_legal_framework_taxonomy(self):
        """Build legal framework taxonomy"""
        self._add_taxonomy_node(
            "legal_framework",
            "Legal Framework",
            "Legal foundation and statutes governing property taxation",
            keywords=["law", "statute", "code", "constitution"],
            complexity_level="advanced"
        )

        legal_subcategories = [
            ("constitution", "Texas Constitution", "Constitutional provisions",
             ["constitution", "article VIII"], "advanced"),
            ("property_tax_code", "Property Tax Code", "Texas Property Tax Code",
             ["property tax code", "tax code"], "advanced"),
            ("government_code", "Government Code", "Relevant Government Code sections",
             ["government code"], "advanced"),
            ("local_government_code", "Local Government Code", "Local government provisions",
             ["local government code"], "advanced"),
            ("comptroller_rules", "Comptroller Rules", "Texas Comptroller rules and regulations",
             ["comptroller rule", "regulation"], "advanced")
        ]

        for node_id, name, desc, keywords, complexity in legal_subcategories:
            self._add_taxonomy_node(node_id, name, desc, parent_id="legal_framework",
                                  keywords=keywords, complexity_level=complexity)

    async def _build_procedures_taxonomy(self):
        """Build procedures and deadlines taxonomy"""
        self._add_taxonomy_node(
            "procedures_and_deadlines",
            "Procedures and Deadlines",
            "Important procedures and deadlines",
            keywords=["procedure", "deadline", "process", "steps"],
            complexity_level="basic"
        )

        procedure_subcategories = [
            ("application_procedures", "Application Procedures", "How to apply for exemptions",
             ["application", "apply", "file", "submit"], "basic"),
            ("filing_deadlines", "Filing Deadlines", "Important filing deadlines",
             ["deadline", "due", "file by", "before"], "basic"),
            ("hearing_procedures", "Hearing Procedures", "Procedures for hearings",
             ["hearing", "procedure", "process"], "intermediate"),
            ("appeal_procedures", "Appeal Procedures", "How to appeal decisions",
             ["appeal", "challenge", "contest"], "intermediate")
        ]

        for node_id, name, desc, keywords, complexity in procedure_subcategories:
            self._add_taxonomy_node(node_id, name, desc, parent_id="procedures_and_deadlines",
                                  keywords=keywords, complexity_level=complexity)

    async def _build_property_types_taxonomy(self):
        """Build property types taxonomy"""
        self._add_taxonomy_node(
            "property_types",
            "Property Types",
            "Different types of property subject to taxation",
            keywords=["property", "real estate", "personal property"],
            complexity_level="basic"
        )

        property_type_subcategories = [
            ("residential", "Residential Property", "Homes and residential properties",
             ["residential", "home", "house", "dwelling"], "basic"),
            ("commercial", "Commercial Property", "Commercial and business properties",
             ["commercial", "business", "office", "retail"], "basic"),
            ("industrial", "Industrial Property", "Industrial and manufacturing properties",
             ["industrial", "manufacturing", "factory", "warehouse"], "intermediate"),
            ("agricultural", "Agricultural Property", "Agricultural and rural properties",
             ["agricultural", "farm", "ranch", "rural"], "intermediate"),
            ("personal_property", "Personal Property", "Business personal property",
             ["personal property", "business personal property", "equipment"], "intermediate"),
            ("mineral_rights", "Mineral Rights", "Oil, gas, and mineral interests",
             ["mineral", "oil", "gas", "mineral rights"], "advanced")
        ]

        for node_id, name, desc, keywords, complexity in property_type_subcategories:
            self._add_taxonomy_node(node_id, name, desc, parent_id="property_types",
                                  keywords=keywords, complexity_level=complexity)

    async def _build_authorities_taxonomy(self):
        """Build authorities and jurisdictions taxonomy"""
        self._add_taxonomy_node(
            "authorities_and_jurisdictions",
            "Authorities and Jurisdictions",
            "Government entities involved in property taxation",
            keywords=["authority", "jurisdiction", "government", "entity"],
            complexity_level="basic"
        )

        authority_subcategories = [
            ("comptroller", "Texas Comptroller", "Texas Comptroller of Public Accounts",
             ["comptroller", "texas comptroller"], "basic"),
            ("appraisal_districts", "Appraisal Districts", "County appraisal districts",
             ["appraisal district", "CAD"], "basic"),
            ("taxing_units", "Taxing Units", "Cities, counties, school districts, etc.",
             ["taxing unit", "city", "county", "school district"], "basic"),
            ("arb", "Appraisal Review Board", "Appraisal Review Boards",
             ["ARB", "appraisal review board", "review board"], "intermediate"),
            ("tax_assessor", "Tax Assessor-Collector", "County tax assessor-collectors",
             ["tax assessor", "collector"], "basic")
        ]

        for node_id, name, desc, keywords, complexity in authority_subcategories:
            self._add_taxonomy_node(node_id, name, desc, parent_id="authorities_and_jurisdictions",
                                  keywords=keywords, complexity_level=complexity)

    def _add_taxonomy_node(self, node_id: str, name: str, description: str,
                          parent_id: Optional[str] = None, keywords: List[str] = None,
                          synonyms: List[str] = None, complexity_level: str = "basic"):
        """Add a node to the taxonomy"""
        if keywords is None:
            keywords = []
        if synonyms is None:
            synonyms = []

        node = TaxonomyNode(
            node_id=node_id,
            name=name,
            description=description,
            parent_id=parent_id,
            keywords=keywords,
            synonyms=synonyms,
            complexity_level=complexity_level
        )

        self.taxonomy_nodes[node_id] = node

        # Add to parent's children
        if parent_id and parent_id in self.taxonomy_nodes:
            self.taxonomy_nodes[parent_id].children.append(node_id)

    async def _load_classification_patterns(self):
        """Load patterns for content classification"""
        # Keyword patterns for each category
        self.keyword_patterns = {
            "exemptions": [
                r'\b(?:exemption|exempt|homestead|disability|senior|veteran|agricultural)\b',
                r'\b(?:65|over 65|disabled|military)\b',
                r'\b(?:charitable|nonprofit|religious)\b'
            ],
            "appraisal_and_assessment": [
                r'\b(?:appraisal|assessment|value|valuation|market value)\b',
                r'\b(?:CAD|appraisal district|appraised value)\b',
                r'\b(?:notice|NOV|rendition)\b'
            ],
            "appeals_and_protests": [
                r'\b(?:protest|appeal|challenge|dispute|hearing)\b',
                r'\b(?:ARB|review board|informal|formal)\b',
                r'\b(?:evidence|comparable|deadline)\b'
            ],
            "collection_and_enforcement": [
                r'\b(?:delinquent|penalty|interest|payment)\b',
                r'\b(?:lien|foreclosure|tax sale)\b',
                r'\b(?:installment|agreement)\b'
            ],
            "legal_framework": [
                r'\b(?:code|statute|law|constitution|section)\b',
                r'\b(?:property tax code|government code)\b',
                r'\b(?:comptroller rule|regulation)\b'
            ],
            "procedures_and_deadlines": [
                r'\b(?:procedure|deadline|process|step|file|apply)\b',
                r'\b(?:due|before|after|within|must)\b',
                r'\b(?:application|form|submit)\b'
            ]
        }

        # Classification rules based on content analysis
        self.classification_rules = {
            "high_confidence_threshold": 0.7,
            "medium_confidence_threshold": 0.4,
            "keyword_weight": 0.4,
            "context_weight": 0.3,
            "structure_weight": 0.3
        }

    async def categorize_content(self, content: str) -> ContentCategory:
        """Categorize content into taxonomy categories"""
        if not content or not content.strip():
            return ContentCategory(
                primary_categories=[],
                secondary_categories=[],
                subtopics=[],
                confidence_scores={},
                detected_keywords=[],
                classification_reasoning="Empty content"
            )

        content_lower = content.lower()

        # Calculate scores for each category
        category_scores = {}
        detected_keywords = []

        for category, patterns in self.keyword_patterns.items():
            score = 0.0
            category_keywords = []

            # Score based on keyword matches
            for pattern in patterns:
                matches = re.findall(pattern, content_lower)
                if matches:
                    score += len(matches) * 0.1  # Each match adds 0.1
                    category_keywords.extend(matches)

            # Normalize score based on content length
            word_count = len(content_lower.split())
            if word_count > 0:
                score = min(score / (word_count / 100), 1.0)

            category_scores[category] = score
            if category_keywords:
                detected_keywords.extend(category_keywords)

        # Determine primary and secondary categories
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)

        primary_categories = []
        secondary_categories = []

        for category, score in sorted_categories:
            if score >= self.classification_rules["high_confidence_threshold"]:
                primary_categories.append(category)
            elif score >= self.classification_rules["medium_confidence_threshold"]:
                secondary_categories.append(category)

        # If no high confidence categories, take the top scoring one if it's above minimum
        if not primary_categories and sorted_categories and sorted_categories[0][1] > 0.2:
            primary_categories.append(sorted_categories[0][0])

        # Identify subtopics within primary categories
        subtopics = await self._identify_subtopics(content, primary_categories)

        # Generate classification reasoning
        reasoning = self._generate_classification_reasoning(
            content, primary_categories, secondary_categories, category_scores
        )

        return ContentCategory(
            primary_categories=primary_categories,
            secondary_categories=secondary_categories,
            subtopics=subtopics,
            confidence_scores=category_scores,
            detected_keywords=list(set(detected_keywords)),
            classification_reasoning=reasoning
        )

    async def _identify_subtopics(self, content: str, primary_categories: List[str]) -> List[str]:
        """Identify subtopics within primary categories"""
        subtopics = []
        content_lower = content.lower()

        for category in primary_categories:
            if category in self.taxonomy_nodes:
                category_node = self.taxonomy_nodes[category]

                # Check children nodes for matches
                for child_id in category_node.children:
                    if child_id in self.taxonomy_nodes:
                        child_node = self.taxonomy_nodes[child_id]

                        # Check if child keywords appear in content
                        child_keywords = child_node.keywords + child_node.synonyms
                        for keyword in child_keywords:
                            if keyword.lower() in content_lower:
                                subtopics.append(child_id)
                                break

        return list(set(subtopics))  # Remove duplicates

    def _generate_classification_reasoning(self, content: str, primary_categories: List[str],
                                         secondary_categories: List[str], scores: Dict[str, float]) -> str:
        """Generate reasoning for classification decision"""
        reasoning_parts = []

        if primary_categories:
            top_category = primary_categories[0]
            top_score = scores.get(top_category, 0)
            reasoning_parts.append(f"Primary category '{top_category}' (confidence: {top_score:.2f})")

        if secondary_categories:
            reasoning_parts.append(f"Secondary categories: {', '.join(secondary_categories)}")

        if not primary_categories and not secondary_categories:
            reasoning_parts.append("No strong categorical match found")

        # Add content length context
        word_count = len(content.split())
        reasoning_parts.append(f"Content length: {word_count} words")

        return "; ".join(reasoning_parts)

    async def build_topic_hierarchy(self, category_lists: List[List[str]]) -> Dict[str, List[str]]:
        """Build topic hierarchy from categorized content"""
        topic_hierarchy = {}

        # Count category co-occurrences
        co_occurrence = defaultdict(lambda: defaultdict(int))

        for categories in category_lists:
            for i, cat1 in enumerate(categories):
                for cat2 in categories[i+1:]:
                    co_occurrence[cat1][cat2] += 1
                    co_occurrence[cat2][cat1] += 1

        # Build hierarchy based on co-occurrence and taxonomy structure
        for category in self.root_categories:
            if category in self.taxonomy_nodes:
                related_topics = []

                # Add direct children
                category_node = self.taxonomy_nodes[category]
                related_topics.extend(category_node.children)

                # Add frequently co-occurring categories
                if category in co_occurrence:
                    frequent_cooccur = sorted(
                        co_occurrence[category].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]  # Top 5 co-occurring topics

                    related_topics.extend([topic for topic, count in frequent_cooccur if count > 2])

                topic_hierarchy[category] = list(set(related_topics))

        return topic_hierarchy

    async def get_category_suggestions(self, content: str) -> List[Dict[str, Any]]:
        """Get category suggestions for content"""
        categorization = await self.categorize_content(content)

        suggestions = []

        # Suggest primary categories if confidence is low
        if not categorization.primary_categories:
            suggestions.append({
                'type': 'category',
                'message': 'Consider adding more specific property tax terminology to improve categorization',
                'severity': 'info'
            })

        # Suggest subtopics if available
        if categorization.primary_categories and not categorization.subtopics:
            for category in categorization.primary_categories:
                if category in self.taxonomy_nodes:
                    children = self.taxonomy_nodes[category].children
                    if children:
                        suggestions.append({
                            'type': 'subtopic',
                            'message': f'Consider adding subtopic details for {category}',
                            'suggestions': children[:3],
                            'severity': 'info'
                        })

        return suggestions

    async def save_taxonomy(self):
        """Save taxonomy to storage"""
        self.logger.info("💾 Saving taxonomy")

        # Save taxonomy nodes
        taxonomy_file = self.storage_dir / "taxonomy_nodes.json"
        nodes_data = {
            node_id: {
                'node_id': node.node_id,
                'name': node.name,
                'description': node.description,
                'parent_id': node.parent_id,
                'children': node.children,
                'keywords': node.keywords,
                'synonyms': node.synonyms,
                'content_count': node.content_count,
                'authority_level': node.authority_level,
                'complexity_level': node.complexity_level
            }
            for node_id, node in self.taxonomy_nodes.items()
        }

        with open(taxonomy_file, 'w') as f:
            json.dump(nodes_data, f, indent=2)

        # Save classification patterns
        patterns_file = self.storage_dir / "classification_patterns.json"
        patterns_data = {
            'keyword_patterns': self.keyword_patterns,
            'classification_rules': self.classification_rules,
            'root_categories': self.root_categories
        }

        with open(patterns_file, 'w') as f:
            json.dump(patterns_data, f, indent=2)

        self.logger.info("✅ Taxonomy saved")

    async def load_taxonomy(self):
        """Load taxonomy from storage"""
        try:
            # Load taxonomy nodes
            taxonomy_file = self.storage_dir / "taxonomy_nodes.json"
            if taxonomy_file.exists():
                with open(taxonomy_file, 'r') as f:
                    nodes_data = json.load(f)

                for node_id, data in nodes_data.items():
                    node = TaxonomyNode(
                        node_id=data['node_id'],
                        name=data['name'],
                        description=data['description'],
                        parent_id=data.get('parent_id'),
                        children=data.get('children', []),
                        keywords=data.get('keywords', []),
                        synonyms=data.get('synonyms', []),
                        content_count=data.get('content_count', 0),
                        authority_level=data.get('authority_level', 0.0),
                        complexity_level=data.get('complexity_level', 'basic')
                    )
                    self.taxonomy_nodes[node_id] = node

            # Load classification patterns
            patterns_file = self.storage_dir / "classification_patterns.json"
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    patterns_data = json.load(f)

                self.keyword_patterns = patterns_data.get('keyword_patterns', {})
                self.classification_rules = patterns_data.get('classification_rules', {})
                self.root_categories = patterns_data.get('root_categories', [])

            self.logger.info(f"✅ Loaded taxonomy with {len(self.taxonomy_nodes)} nodes")

        except Exception as e:
            self.logger.error(f"❌ Failed to load taxonomy: {e}")
            # Fall back to building base taxonomy
            await self._build_base_taxonomy()

    def get_taxonomy_stats(self) -> Dict[str, Any]:
        """Get taxonomy statistics"""
        stats = {
            'total_nodes': len(self.taxonomy_nodes),
            'root_categories': len(self.root_categories),
            'nodes_by_complexity': defaultdict(int),
            'average_children_per_node': 0,
            'max_depth': 0
        }

        total_children = 0
        for node in self.taxonomy_nodes.values():
            stats['nodes_by_complexity'][node.complexity_level] += 1
            total_children += len(node.children)

        if self.taxonomy_nodes:
            stats['average_children_per_node'] = total_children / len(self.taxonomy_nodes)

        # Calculate max depth
        stats['max_depth'] = self._calculate_max_depth()

        # Convert defaultdict to regular dict
        stats['nodes_by_complexity'] = dict(stats['nodes_by_complexity'])

        return stats

    def _calculate_max_depth(self) -> int:
        """Calculate maximum depth of taxonomy tree"""
        def get_depth(node_id: str, current_depth: int = 0) -> int:
            if node_id not in self.taxonomy_nodes:
                return current_depth

            node = self.taxonomy_nodes[node_id]
            if not node.children:
                return current_depth

            max_child_depth = 0
            for child_id in node.children:
                child_depth = get_depth(child_id, current_depth + 1)
                max_child_depth = max(max_child_depth, child_depth)

            return max_child_depth

        max_depth = 0
        for root_category in self.root_categories:
            depth = get_depth(root_category)
            max_depth = max(max_depth, depth)

        return max_depth

if __name__ == "__main__":
    # Test taxonomy builder
    async def test_taxonomy():
        builder = PropertyTaxTaxonomyBuilder()
        await builder.initialize()

        # Test content categorization
        test_content = """
        A person is entitled to an exemption from taxation of the appraised value
        of the person's residence homestead. To qualify for the homestead exemption,
        the person must occupy the property as their primary residence.
        """

        categorization = await builder.categorize_content(test_content)

        print(f"Primary categories: {categorization.primary_categories}")
        print(f"Secondary categories: {categorization.secondary_categories}")
        print(f"Subtopics: {categorization.subtopics}")
        print(f"Confidence scores: {categorization.confidence_scores}")
        print(f"Reasoning: {categorization.classification_reasoning}")

        # Get taxonomy stats
        stats = builder.get_taxonomy_stats()
        print(f"Taxonomy stats: {stats}")

    asyncio.run(test_taxonomy())