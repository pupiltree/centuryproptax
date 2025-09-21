"""
Legal Text Cleaner and Normalizer
Specialized text cleaning for legal property tax documents
"""

import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
import structlog
from datetime import datetime
from src.core.logging import get_logger

logger = get_logger("legal_text_cleaner")

@dataclass
class CleaningRule:
    """Represents a text cleaning rule"""
    name: str
    pattern: str
    replacement: str
    rule_type: str  # 'normalization', 'removal', 'formatting'
    applies_to: List[str]  # Document types this rule applies to
    priority: int  # Higher number = higher priority

@dataclass
class CleaningResult:
    """Result of text cleaning operation"""
    original_text: str
    cleaned_text: str
    applied_rules: List[str]
    cleaning_stats: Dict[str, int]
    quality_score: float

class LegalTextCleaner:
    """Specialized text cleaner for legal property tax documents"""

    def __init__(self):
        self.logger = logger

        # Cleaning rules organized by type
        self.cleaning_rules = self._build_cleaning_rules()

        # Legal terminology standardization
        self.terminology_mappings = self._build_terminology_mappings()

        # Citation standardization patterns
        self.citation_patterns = self._build_citation_patterns()

        # Legal formatting patterns
        self.formatting_patterns = self._build_formatting_patterns()

    def _build_cleaning_rules(self) -> List[CleaningRule]:
        """Build comprehensive cleaning rules for legal text"""
        return [
            # HTML and web artifacts removal
            CleaningRule(
                name="remove_html_tags",
                pattern=r'<[^>]+>',
                replacement='',
                rule_type="removal",
                applies_to=["all"],
                priority=100
            ),
            CleaningRule(
                name="remove_html_entities",
                pattern=r'&[a-zA-Z0-9#]+;',
                replacement=' ',
                rule_type="removal",
                applies_to=["all"],
                priority=99
            ),

            # Navigation and UI artifacts
            CleaningRule(
                name="remove_navigation",
                pattern=r'(?i)(?:skip to main content|breadcrumb|navigation|menu|footer)',
                replacement='',
                rule_type="removal",
                applies_to=["all"],
                priority=95
            ),
            CleaningRule(
                name="remove_social_media",
                pattern=r'(?i)(?:share on|follow us|like us|facebook|twitter|linkedin)',
                replacement='',
                rule_type="removal",
                applies_to=["all"],
                priority=94
            ),

            # Legal document specific cleaning
            CleaningRule(
                name="normalize_section_references",
                pattern=r'(?i)sec\.?\s*(\d+(?:\.\d+)*)',
                replacement=r'Section \1',
                rule_type="normalization",
                applies_to=["statute", "regulation"],
                priority=90
            ),
            CleaningRule(
                name="normalize_subsection_markers",
                pattern=r'\(([a-z])\)\s*',
                replacement=r'(\1) ',
                rule_type="formatting",
                applies_to=["statute", "regulation"],
                priority=89
            ),

            # Citation normalization
            CleaningRule(
                name="normalize_code_citations",
                pattern=r'(?i)(?:texas\s+)?prop(?:erty)?\.?\s+tax\s+code\s+(?:section|§|sec\.?)\s*(\d+(?:\.\d+)*)',
                replacement=r'Texas Property Tax Code Section \1',
                rule_type="normalization",
                applies_to=["all"],
                priority=88
            ),
            CleaningRule(
                name="normalize_constitution_citations",
                pattern=r'(?i)(?:texas\s+)?const(?:itution)?\.?\s+art(?:icle)?\.?\s*([IVXLC]+)(?:\s*[,§]\s*sec(?:tion)?\.?\s*(\d+))?',
                replacement=r'Texas Constitution Article \1\2',
                rule_type="normalization",
                applies_to=["all"],
                priority=87
            ),

            # Legal terminology standardization
            CleaningRule(
                name="standardize_exemption_terms",
                pattern=r'(?i)\b(?:residence|homestead|home)\s+exemption\b',
                replacement='homestead exemption',
                rule_type="normalization",
                applies_to=["all"],
                priority=85
            ),
            CleaningRule(
                name="standardize_appraisal_terms",
                pattern=r'(?i)\b(?:assessed|appraised)\s+value\b',
                replacement='appraised value',
                rule_type="normalization",
                applies_to=["all"],
                priority=84
            ),

            # Procedural text cleaning
            CleaningRule(
                name="clean_step_markers",
                pattern=r'(?i)step\s*(\d+)[:\.]?\s*',
                replacement=r'Step \1: ',
                rule_type="formatting",
                applies_to=["procedure", "form"],
                priority=80
            ),
            CleaningRule(
                name="normalize_deadlines",
                pattern=r'(?i)(?:due|deadline)\s+(?:date\s+)?(?:is\s+)?(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
                replacement=r'Deadline: \1',
                rule_type="formatting",
                applies_to=["procedure", "form", "deadline"],
                priority=79
            ),

            # Q&A formatting
            CleaningRule(
                name="format_questions",
                pattern=r'(?i)^q(?:uestion)?[:\.]?\s*',
                replacement='Q: ',
                rule_type="formatting",
                applies_to=["faq"],
                priority=75
            ),
            CleaningRule(
                name="format_answers",
                pattern=r'(?i)^a(?:nswer)?[:\.]?\s*',
                replacement='A: ',
                rule_type="formatting",
                applies_to=["faq"],
                priority=74
            ),

            # Whitespace and formatting cleanup
            CleaningRule(
                name="normalize_whitespace",
                pattern=r'\s+',
                replacement=' ',
                rule_type="formatting",
                applies_to=["all"],
                priority=50
            ),
            CleaningRule(
                name="clean_line_breaks",
                pattern=r'\n\s*\n\s*\n+',
                replacement='\n\n',
                rule_type="formatting",
                applies_to=["all"],
                priority=49
            ),
            CleaningRule(
                name="remove_trailing_spaces",
                pattern=r'[ \t]+$',
                replacement='',
                rule_type="formatting",
                applies_to=["all"],
                priority=48
            ),

            # Document metadata removal
            CleaningRule(
                name="remove_page_numbers",
                pattern=r'(?i)page\s+\d+\s+of\s+\d+',
                replacement='',
                rule_type="removal",
                applies_to=["all"],
                priority=40
            ),
            CleaningRule(
                name="remove_revision_dates",
                pattern=r'(?i)(?:revised|updated|effective)\s+\d{1,2}/\d{1,2}/\d{4}',
                replacement='',
                rule_type="removal",
                applies_to=["form", "procedure"],
                priority=39
            ),

            # Legal formatting preservation
            CleaningRule(
                name="preserve_section_structure",
                pattern=r'(\d+\.\d+(?:\.\d+)*)\s*([A-Z][^.]*)',
                replacement=r'\1 \2',
                rule_type="formatting",
                applies_to=["statute", "regulation"],
                priority=30
            ),

            # Final cleanup
            CleaningRule(
                name="remove_empty_lines",
                pattern=r'\n\s*\n',
                replacement='\n\n',
                rule_type="formatting",
                applies_to=["all"],
                priority=10
            )
        ]

    def _build_terminology_mappings(self) -> Dict[str, str]:
        """Build terminology standardization mappings"""
        return {
            # Exemption terminology
            'residence exemption': 'homestead exemption',
            'home exemption': 'homestead exemption',
            'disability exemption': 'disabled person exemption',
            'elderly exemption': 'senior citizen exemption',
            'over 65 exemption': 'senior citizen exemption',
            'ag exemption': 'agricultural exemption',
            'farm exemption': 'agricultural exemption',

            # Appraisal terminology
            'assessed value': 'appraised value',
            'market value': 'fair market value',
            'actual value': 'fair market value',
            'true value': 'fair market value',
            'CAD': 'County Appraisal District',
            'appraisal district': 'County Appraisal District',

            # Appeal terminology
            'tax protest': 'property tax protest',
            'assessment protest': 'property tax protest',
            'value protest': 'property tax protest',
            'ARB': 'Appraisal Review Board',
            'review board': 'Appraisal Review Board',
            'appeals board': 'Appraisal Review Board',

            # Property types
            'real estate': 'real property',
            'personal property': 'business personal property',
            'mobile home': 'manufactured housing',

            # Legal references
            'prop tax code': 'Property Tax Code',
            'tax code': 'Texas Tax Code',
            'govt code': 'Government Code',
            'local govt code': 'Local Government Code'
        }

    def _build_citation_patterns(self) -> Dict[str, str]:
        """Build citation standardization patterns"""
        return {
            'property_tax_code': r'(?i)(?:texas\s+)?prop(?:erty)?\.?\s+tax\s+code\s+(?:section|§|sec\.?)\s*(\d+(?:\.\d+)*)',
            'tax_code': r'(?i)(?:texas\s+)?tax\s+code\s+(?:section|§|sec\.?)\s*(\d+(?:\.\d+)*)',
            'government_code': r'(?i)(?:texas\s+)?gov(?:ernment)?\.?\s+code\s+(?:section|§|sec\.?)\s*(\d+(?:\.\d+)*)',
            'constitution': r'(?i)(?:texas\s+)?const(?:itution)?\.?\s+art(?:icle)?\.?\s*([IVXLC]+)(?:\s*[,§]\s*sec(?:tion)?\.?\s*(\d+))?',
            'section_only': r'(?i)(?:section|§|sec\.?)\s*(\d+(?:\.\d+)*)',
            'chapter': r'(?i)chapter\s+(\d+)',
            'rule': r'(?i)(?:comptroller\s+)?rule\s+(\d+(?:\.\d+)*)'
        }

    def _build_formatting_patterns(self) -> Dict[str, str]:
        """Build formatting patterns for different document types"""
        return {
            'statute_section': r'(\d+\.\d+(?:\.\d+)*)\.\s*([A-Z][^.]*\.)',
            'subsection': r'\(([a-z])\)\s*([^(]*?)(?=\([a-z]\)|$)',
            'numbered_list': r'(\d+)\.\s*([^.]*?)(?=\d+\.|$)',
            'lettered_list': r'\(([a-z])\)\s*([^(]*?)(?=\([a-z]\)|$)',
            'definition': r'(?i)"([^"]+)"\s+means\s+([^.]*\.)',
            'effective_date': r'(?i)effective\s+(\w+\s+\d{1,2},\s+\d{4})',
            'deadline': r'(?i)(?:due|deadline|before|by)\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})'
        }

    async def clean_legal_text(self, text: str, document_type: str = "general") -> str:
        """Clean legal text with document type specific rules"""
        if not text or not text.strip():
            return ""

        self.logger.info(f"🧹 Cleaning legal text ({document_type}): {len(text)} characters")

        result = await self._apply_cleaning_pipeline(text, document_type)

        self.logger.info(f"✅ Text cleaned: {len(result.cleaned_text)} characters ({len(result.applied_rules)} rules applied)")
        return result.cleaned_text

    async def clean_procedural_text(self, text: str) -> str:
        """Clean procedural text with specific formatting"""
        return await self.clean_legal_text(text, "procedure")

    async def clean_form_text(self, text: str) -> str:
        """Clean form text with specific formatting"""
        return await self.clean_legal_text(text, "form")

    async def clean_faq_text(self, text: str) -> str:
        """Clean FAQ text with Q&A formatting"""
        return await self.clean_legal_text(text, "faq")

    async def clean_general_text(self, text: str) -> str:
        """Clean general legal text"""
        return await self.clean_legal_text(text, "general")

    async def _apply_cleaning_pipeline(self, text: str, document_type: str) -> CleaningResult:
        """Apply the complete cleaning pipeline"""
        original_text = text
        current_text = text
        applied_rules = []
        cleaning_stats = {
            'character_count_reduction': 0,
            'patterns_replaced': 0,
            'normalizations_applied': 0,
            'formatting_fixes': 0
        }

        # Get applicable rules for this document type
        applicable_rules = [
            rule for rule in self.cleaning_rules
            if document_type in rule.applies_to or "all" in rule.applies_to
        ]

        # Sort by priority (highest first)
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)

        # Apply each rule
        for rule in applicable_rules:
            before_length = len(current_text)
            matches_before = len(re.findall(rule.pattern, current_text))

            # Apply the rule
            current_text = re.sub(rule.pattern, rule.replacement, current_text, flags=re.MULTILINE | re.IGNORECASE)

            after_length = len(current_text)
            matches_after = len(re.findall(rule.pattern, current_text))

            # Track if rule was applied
            if before_length != after_length or matches_before != matches_after:
                applied_rules.append(rule.name)

                # Update stats
                cleaning_stats['character_count_reduction'] += before_length - after_length
                cleaning_stats['patterns_replaced'] += matches_before - matches_after

                if rule.rule_type == "normalization":
                    cleaning_stats['normalizations_applied'] += 1
                elif rule.rule_type == "formatting":
                    cleaning_stats['formatting_fixes'] += 1

        # Apply terminology standardization
        current_text = await self._standardize_terminology(current_text)

        # Apply citation normalization
        current_text = await self._normalize_citations(current_text)

        # Apply document-specific formatting
        current_text = await self._apply_document_specific_formatting(current_text, document_type)

        # Final cleanup
        current_text = current_text.strip()

        # Calculate quality score
        quality_score = self._calculate_cleaning_quality_score(original_text, current_text, applied_rules)

        return CleaningResult(
            original_text=original_text,
            cleaned_text=current_text,
            applied_rules=applied_rules,
            cleaning_stats=cleaning_stats,
            quality_score=quality_score
        )

    async def _standardize_terminology(self, text: str) -> str:
        """Standardize legal terminology"""
        standardized_text = text

        for original_term, standard_term in self.terminology_mappings.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(original_term), re.IGNORECASE)
            standardized_text = pattern.sub(standard_term, standardized_text)

        return standardized_text

    async def _normalize_citations(self, text: str) -> str:
        """Normalize legal citations to standard format"""
        normalized_text = text

        # Normalize Property Tax Code citations
        pattern = self.citation_patterns['property_tax_code']
        normalized_text = re.sub(pattern, r'Texas Property Tax Code Section \1', normalized_text, flags=re.IGNORECASE)

        # Normalize Tax Code citations
        pattern = self.citation_patterns['tax_code']
        normalized_text = re.sub(pattern, r'Texas Tax Code Section \1', normalized_text, flags=re.IGNORECASE)

        # Normalize Government Code citations
        pattern = self.citation_patterns['government_code']
        normalized_text = re.sub(pattern, r'Texas Government Code Section \1', normalized_text, flags=re.IGNORECASE)

        # Normalize Constitution citations
        pattern = self.citation_patterns['constitution']
        normalized_text = re.sub(pattern, r'Texas Constitution Article \1 Section \2', normalized_text, flags=re.IGNORECASE)

        # Normalize section references
        pattern = self.citation_patterns['section_only']
        normalized_text = re.sub(pattern, r'Section \1', normalized_text, flags=re.IGNORECASE)

        return normalized_text

    async def _apply_document_specific_formatting(self, text: str, document_type: str) -> str:
        """Apply document type specific formatting"""
        formatted_text = text

        if document_type == "statute":
            formatted_text = await self._format_statute_text(formatted_text)
        elif document_type == "procedure":
            formatted_text = await self._format_procedure_text(formatted_text)
        elif document_type == "form":
            formatted_text = await self._format_form_text(formatted_text)
        elif document_type == "faq":
            formatted_text = await self._format_faq_text(formatted_text)

        return formatted_text

    async def _format_statute_text(self, text: str) -> str:
        """Format statute text with proper structure"""
        # Ensure section numbers are properly formatted
        text = re.sub(r'(\d+\.\d+(?:\.\d+)*)\s*([A-Z][^.]*)', r'\1. \2', text)

        # Format subsections
        text = re.sub(r'\(([a-z])\)\s*', r'(\1) ', text)

        # Ensure proper spacing after periods
        text = re.sub(r'\.([A-Z])', r'. \1', text)

        return text

    async def _format_procedure_text(self, text: str) -> str:
        """Format procedural text with clear steps"""
        # Ensure step numbers are formatted consistently
        text = re.sub(r'(?i)step\s*(\d+)[:\.]?\s*', r'Step \1: ', text)

        # Format numbered lists
        text = re.sub(r'^(\d+)\.\s*', r'\1. ', text, flags=re.MULTILINE)

        return text

    async def _format_form_text(self, text: str) -> str:
        """Format form text with clear sections"""
        # Format form section headers
        text = re.sub(r'(?i)^(part|section)\s+([a-z])[:\.]?\s*', r'\1 \2: ', text, flags=re.MULTILINE)

        return text

    async def _format_faq_text(self, text: str) -> str:
        """Format FAQ text with clear Q&A structure"""
        # Ensure Q&A formatting is consistent
        text = re.sub(r'(?i)^q(?:uestion)?[:\.]?\s*', 'Q: ', text, flags=re.MULTILINE)
        text = re.sub(r'(?i)^a(?:nswer)?[:\.]?\s*', 'A: ', text, flags=re.MULTILINE)

        return text

    def _calculate_cleaning_quality_score(self, original_text: str, cleaned_text: str, applied_rules: List[str]) -> float:
        """Calculate quality score for the cleaning operation"""
        score = 0.0

        # Base score for successful cleaning
        if cleaned_text:
            score += 0.3

        # Score based on character reduction (removing noise)
        if len(cleaned_text) < len(original_text):
            reduction_ratio = 1 - (len(cleaned_text) / len(original_text))
            score += min(reduction_ratio * 0.2, 0.2)  # Up to 0.2 for reasonable reduction

        # Score based on number of rules applied
        rules_score = min(len(applied_rules) / 20, 0.3)  # Up to 0.3 for comprehensive cleaning
        score += rules_score

        # Score based on text structure improvements
        structure_score = self._assess_text_structure_quality(cleaned_text)
        score += structure_score * 0.2

        return min(score, 1.0)

    def _assess_text_structure_quality(self, text: str) -> float:
        """Assess the structural quality of cleaned text"""
        quality_indicators = 0
        total_indicators = 7

        # Check for proper sentence structure
        sentences = re.split(r'[.!?]+', text)
        if sentences and len(sentences) > 1:
            quality_indicators += 1

        # Check for proper section formatting
        if re.search(r'Section\s+\d+', text):
            quality_indicators += 1

        # Check for proper citation formatting
        if re.search(r'Texas\s+(?:Property\s+Tax\s+)?Code\s+Section', text):
            quality_indicators += 1

        # Check for consistent spacing
        if not re.search(r'\s{2,}', text):  # No excessive whitespace
            quality_indicators += 1

        # Check for proper capitalization
        if re.search(r'[A-Z][a-z]', text):  # Has proper capitalization
            quality_indicators += 1

        # Check for legal terminology
        legal_terms = ['exemption', 'appraisal', 'assessment', 'protest', 'appeal', 'property tax']
        if any(term in text.lower() for term in legal_terms):
            quality_indicators += 1

        # Check for structured content
        if re.search(r'\([a-z]\)', text) or re.search(r'\d+\.', text):  # Has lists or subsections
            quality_indicators += 1

        return quality_indicators / total_indicators

    async def get_cleaning_suggestions(self, text: str, document_type: str = "general") -> List[Dict[str, Any]]:
        """Get suggestions for improving text quality"""
        suggestions = []

        # Check for common issues
        if len(text) < 50:
            suggestions.append({
                'type': 'length',
                'severity': 'warning',
                'message': 'Text is very short and may lack sufficient detail'
            })

        # Check for HTML artifacts
        if re.search(r'<[^>]+>', text):
            suggestions.append({
                'type': 'formatting',
                'severity': 'error',
                'message': 'Text contains HTML tags that should be removed'
            })

        # Check for inconsistent citations
        citation_formats = len(set(re.findall(r'(?:Section|§|Sec\.?)\s*\d+', text, re.IGNORECASE)))
        if citation_formats > 1:
            suggestions.append({
                'type': 'citation',
                'severity': 'warning',
                'message': 'Citations use inconsistent formatting'
            })

        # Check for missing legal context
        if document_type in ['statute', 'regulation'] and not re.search(r'(?:Section|Chapter|Code)', text, re.IGNORECASE):
            suggestions.append({
                'type': 'legal_structure',
                'severity': 'warning',
                'message': 'Legal document may be missing structural elements'
            })

        return suggestions

if __name__ == "__main__":
    # Test legal text cleaner
    async def test_cleaner():
        cleaner = LegalTextCleaner()

        # Test statute cleaning
        statute_text = """
        <p>Sec. 11.13. RESIDENCE HOMESTEAD EXEMPTION.  (a) A person is entitled to an
        exemption from taxation of $25,000 of the appraised value of the person's residence homestead.
        (b)  In addition to the exemption provided by Subsection (a), a person is entitled to an
        exemption from taxation by a school district of $25,000 of the appraised value.
        """

        cleaned = await cleaner.clean_legal_text(statute_text, "statute")
        print("Original:")
        print(statute_text)
        print("\nCleaned:")
        print(cleaned)

        # Test suggestions
        suggestions = await cleaner.get_cleaning_suggestions(statute_text, "statute")
        print("\nSuggestions:")
        for suggestion in suggestions:
            print(f"- {suggestion['type']}: {suggestion['message']}")

    asyncio.run(test_cleaner())