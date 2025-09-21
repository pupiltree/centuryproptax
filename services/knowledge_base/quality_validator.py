"""
Quality Validator for Legal Content
Validates accuracy, completeness, and quality of property tax legal content
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import structlog
import re
from enum import Enum
import json

from .content_processor import KnowledgeEntry
from services.vector_store.citation_tracker import PropertyTaxCitationTracker, get_citation_tracker
from src.core.logging import get_logger

logger = get_logger("quality_validator")

class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"    # Legal accuracy issues, missing required info
    WARNING = "warning"      # Quality issues, unclear content
    INFO = "info"           # Suggestions for improvement
    PASS = "pass"           # No issues found

@dataclass
class ValidationRule:
    """Represents a content validation rule"""
    rule_id: str
    name: str
    description: str
    severity: ValidationSeverity
    applies_to: List[str]  # Content types this rule applies to
    validation_function: str  # Name of validation method
    weight: float = 1.0  # Importance weight

@dataclass
class ValidationIssue:
    """Represents a validation issue found in content"""
    rule_id: str
    severity: ValidationSeverity
    message: str
    location: Optional[str] = None  # Where in content the issue was found
    suggestion: Optional[str] = None  # How to fix the issue
    confidence: float = 1.0  # Confidence in the issue detection

@dataclass
class ValidationResult:
    """Result of content validation"""
    entry_id: str
    overall_score: float  # 0.0 to 1.0
    validation_issues: List[ValidationIssue]
    quality_metrics: Dict[str, float]
    validation_timestamp: datetime
    recommendations: List[str]

class PropertyTaxQualityValidator:
    """Validates quality and accuracy of property tax legal content"""

    def __init__(self):
        self.logger = logger
        self.citation_tracker: Optional[PropertyTaxCitationTracker] = None

        # Validation rules
        self.validation_rules = self._build_validation_rules()

        # Quality thresholds
        self.quality_thresholds = self._build_quality_thresholds()

        # Legal accuracy patterns
        self.accuracy_patterns = self._build_accuracy_patterns()

    async def initialize(self):
        """Initialize the quality validator"""
        self.citation_tracker = get_citation_tracker()
        self.logger.info("✅ Property tax quality validator initialized")

    def _build_validation_rules(self) -> List[ValidationRule]:
        """Build comprehensive validation rules"""
        return [
            # Legal Accuracy Rules
            ValidationRule(
                rule_id="valid_citations",
                name="Valid Legal Citations",
                description="Ensure all legal citations are properly formatted and valid",
                severity=ValidationSeverity.CRITICAL,
                applies_to=["statute", "regulation", "procedure"],
                validation_function="validate_citations",
                weight=2.0
            ),
            ValidationRule(
                rule_id="authority_verification",
                name="Authority Verification",
                description="Verify content comes from authoritative sources",
                severity=ValidationSeverity.CRITICAL,
                applies_to=["all"],
                validation_function="validate_authority",
                weight=1.8
            ),
            ValidationRule(
                rule_id="legal_consistency",
                name="Legal Consistency",
                description="Check for consistency with established legal principles",
                severity=ValidationSeverity.WARNING,
                applies_to=["statute", "regulation"],
                validation_function="validate_legal_consistency",
                weight=1.5
            ),

            # Content Completeness Rules
            ValidationRule(
                rule_id="content_length",
                name="Adequate Content Length",
                description="Ensure content has sufficient detail",
                severity=ValidationSeverity.WARNING,
                applies_to=["all"],
                validation_function="validate_content_length",
                weight=1.0
            ),
            ValidationRule(
                rule_id="required_elements",
                name="Required Elements Present",
                description="Check for required elements based on content type",
                severity=ValidationSeverity.WARNING,
                applies_to=["procedure", "form_guide", "exemption"],
                validation_function="validate_required_elements",
                weight=1.3
            ),
            ValidationRule(
                rule_id="definition_clarity",
                name="Definition Clarity",
                description="Ensure legal terms are properly defined or explained",
                severity=ValidationSeverity.INFO,
                applies_to=["statute", "procedure"],
                validation_function="validate_definitions",
                weight=1.0
            ),

            # Accuracy and Currency Rules
            ValidationRule(
                rule_id="date_currency",
                name="Content Currency",
                description="Check if content is current and up-to-date",
                severity=ValidationSeverity.WARNING,
                applies_to=["all"],
                validation_function="validate_currency",
                weight=1.2
            ),
            ValidationRule(
                rule_id="factual_accuracy",
                name="Factual Accuracy",
                description="Validate factual claims and numbers",
                severity=ValidationSeverity.CRITICAL,
                applies_to=["all"],
                validation_function="validate_factual_accuracy",
                weight=1.7
            ),

            # Clarity and Readability Rules
            ValidationRule(
                rule_id="readability",
                name="Content Readability",
                description="Assess readability for target audience",
                severity=ValidationSeverity.INFO,
                applies_to=["faq", "form_guide", "procedure"],
                validation_function="validate_readability",
                weight=0.8
            ),
            ValidationRule(
                rule_id="terminology_consistency",
                name="Terminology Consistency",
                description="Check for consistent use of legal terminology",
                severity=ValidationSeverity.WARNING,
                applies_to=["all"],
                validation_function="validate_terminology",
                weight=1.1
            ),

            # Structure and Format Rules
            ValidationRule(
                rule_id="proper_structure",
                name="Proper Content Structure",
                description="Validate content follows proper structural patterns",
                severity=ValidationSeverity.WARNING,
                applies_to=["all"],
                validation_function="validate_structure",
                weight=1.0
            ),
            ValidationRule(
                rule_id="cross_references",
                name="Valid Cross References",
                description="Ensure cross-references are valid and helpful",
                severity=ValidationSeverity.INFO,
                applies_to=["statute", "procedure"],
                validation_function="validate_cross_references",
                weight=0.9
            )
        ]

    def _build_quality_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Build quality thresholds for different content types"""
        return {
            "statute": {
                "min_length": 200,
                "min_citations": 1,
                "min_authority_level": 0.8,
                "target_score": 0.85
            },
            "regulation": {
                "min_length": 150,
                "min_citations": 1,
                "min_authority_level": 0.7,
                "target_score": 0.8
            },
            "procedure": {
                "min_length": 100,
                "min_citations": 0,
                "min_authority_level": 0.6,
                "target_score": 0.75
            },
            "form_guide": {
                "min_length": 80,
                "min_citations": 0,
                "min_authority_level": 0.5,
                "target_score": 0.7
            },
            "faq": {
                "min_length": 50,
                "min_citations": 0,
                "min_authority_level": 0.4,
                "target_score": 0.65
            },
            "general": {
                "min_length": 100,
                "min_citations": 0,
                "min_authority_level": 0.5,
                "target_score": 0.7
            }
        }

    def _build_accuracy_patterns(self) -> Dict[str, List[str]]:
        """Build patterns for accuracy validation"""
        return {
            "valid_dollar_amounts": [
                r'\$[\d,]+(?:\.\d{2})?',  # Standard dollar format
                r'\$\d+(?:,\d{3})*(?:\.\d{2})?'  # With commas
            ],
            "valid_percentages": [
                r'\d+(?:\.\d+)?%',
                r'\d+(?:\.\d+)?\s*percent'
            ],
            "valid_dates": [
                r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
                r'\d{1,2}/\d{1,2}/\d{4}',
                r'\d{4}-\d{2}-\d{2}'
            ],
            "texas_specific_terms": [
                r'Texas Property Tax Code',
                r'Texas Constitution',
                r'Comptroller of Public Accounts',
                r'County Appraisal District',
                r'Appraisal Review Board'
            ],
            "warning_terms": [
                r'(?i)\b(?:may|might|could|possibly|potentially)\b',  # Uncertain language
                r'(?i)\b(?:should|must|shall|required)\b'  # Strong directives
            ]
        }

    async def validate_knowledge_entry(self, entry: KnowledgeEntry) -> ValidationResult:
        """Validate a single knowledge entry"""
        self.logger.info(f"🔍 Validating knowledge entry: {entry.title}")

        validation_issues = []
        quality_metrics = {}

        # Get applicable rules for this entry type
        applicable_rules = [
            rule for rule in self.validation_rules
            if entry.entry_type in rule.applies_to or "all" in rule.applies_to
        ]

        # Run each validation rule
        for rule in applicable_rules:
            try:
                issues = await self._run_validation_rule(rule, entry)
                validation_issues.extend(issues)
            except Exception as e:
                self.logger.error(f"❌ Validation rule {rule.rule_id} failed: {e}")
                validation_issues.append(ValidationIssue(
                    rule_id=rule.rule_id,
                    severity=ValidationSeverity.WARNING,
                    message=f"Validation rule failed: {str(e)}",
                    confidence=0.5
                ))

        # Calculate quality metrics
        quality_metrics = await self._calculate_quality_metrics(entry, validation_issues)

        # Calculate overall score
        overall_score = await self._calculate_overall_score(entry, validation_issues, quality_metrics)

        # Generate recommendations
        recommendations = await self._generate_recommendations(entry, validation_issues, quality_metrics)

        return ValidationResult(
            entry_id=entry.entry_id,
            overall_score=overall_score,
            validation_issues=validation_issues,
            quality_metrics=quality_metrics,
            validation_timestamp=datetime.now(),
            recommendations=recommendations
        )

    async def _run_validation_rule(self, rule: ValidationRule, entry: KnowledgeEntry) -> List[ValidationIssue]:
        """Run a specific validation rule"""
        method_name = rule.validation_function
        if hasattr(self, method_name):
            validation_method = getattr(self, method_name)
            return await validation_method(rule, entry)
        else:
            self.logger.warning(f"⚠️ Validation method {method_name} not found")
            return []

    async def validate_citations(self, rule: ValidationRule, entry: KnowledgeEntry) -> List[ValidationIssue]:
        """Validate legal citations in content"""
        issues = []

        # Check for citation format consistency
        citation_patterns = [
            r'(?:Section|§|Sec\.?)\s*\d+(?:\.\d+)*',
            r'Texas\s+(?:Property\s+Tax\s+)?Code\s+Section\s+\d+(?:\.\d+)*',
            r'Texas\s+Constitution\s+Article\s+[IVXLC]+(?:\s+Section\s+\d+)?'
        ]

        content = entry.content.lower()
        found_citations = []

        for pattern in citation_patterns:
            matches = re.findall(pattern, entry.content, re.IGNORECASE)
            found_citations.extend(matches)

        # Check if statute/regulation entries have citations
        if entry.entry_type in ["statute", "regulation"] and not found_citations:
            issues.append(ValidationIssue(
                rule_id=rule.rule_id,
                severity=rule.severity,
                message="Legal document should contain proper citations",
                suggestion="Add appropriate legal citations to support the content",
                confidence=0.9
            ))

        # Check citation format consistency
        if len(found_citations) > 1:
            # Check for mixed formats
            section_formats = set()
            for citation in found_citations:
                if 'section' in citation.lower():
                    section_formats.add('section')
                elif '§' in citation:
                    section_formats.add('symbol')
                elif 'sec.' in citation.lower():
                    section_formats.add('abbreviation')

            if len(section_formats) > 1:
                issues.append(ValidationIssue(
                    rule_id=rule.rule_id,
                    severity=ValidationSeverity.WARNING,
                    message="Inconsistent citation formatting found",
                    suggestion="Use consistent citation format throughout the document",
                    confidence=0.8
                ))

        return issues

    async def validate_authority(self, rule: ValidationRule, entry: KnowledgeEntry) -> List[ValidationIssue]:
        """Validate content authority and source credibility"""
        issues = []

        # Check authority level against thresholds
        thresholds = self.quality_thresholds.get(entry.entry_type, {})
        min_authority = thresholds.get("min_authority_level", 0.5)

        if entry.authority_level < min_authority:
            issues.append(ValidationIssue(
                rule_id=rule.rule_id,
                severity=rule.severity,
                message=f"Authority level ({entry.authority_level:.2f}) below threshold ({min_authority:.2f})",
                suggestion="Verify content comes from authoritative sources",
                confidence=0.9
            ))

        # Check for authoritative source indicators
        authoritative_indicators = [
            "texas comptroller",
            "property tax code",
            "texas constitution",
            "county appraisal district",
            "appraisal review board"
        ]

        content_lower = entry.content.lower()
        found_indicators = [ind for ind in authoritative_indicators if ind in content_lower]

        if entry.entry_type in ["statute", "regulation"] and not found_indicators:
            issues.append(ValidationIssue(
                rule_id=rule.rule_id,
                severity=ValidationSeverity.WARNING,
                message="Legal content lacks authoritative source indicators",
                suggestion="Reference authoritative sources like Texas Property Tax Code",
                confidence=0.7
            ))

        return issues

    async def validate_legal_consistency(self, rule: ValidationRule, entry: KnowledgeEntry) -> List[ValidationIssue]:
        """Validate consistency with legal principles"""
        issues = []

        # Check for contradictory statements
        contradictory_patterns = [
            (r'\bmust\b.*\bmay\b', "Content contains both mandatory and optional language"),
            (r'\brequired\b.*\boptional\b', "Content mixes required and optional elements"),
            (r'\ballowed\b.*\bprohibited\b', "Content contains contradictory permissions")
        ]

        for pattern, message in contradictory_patterns:
            if re.search(pattern, entry.content, re.IGNORECASE):
                issues.append(ValidationIssue(
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    message=message,
                    suggestion="Review content for consistency in legal requirements",
                    confidence=0.7
                ))

        return issues

    async def validate_content_length(self, rule: ValidationRule, entry: KnowledgeEntry) -> List[ValidationIssue]:
        """Validate content has adequate length"""
        issues = []

        thresholds = self.quality_thresholds.get(entry.entry_type, {})
        min_length = thresholds.get("min_length", 100)

        if len(entry.content) < min_length:
            issues.append(ValidationIssue(
                rule_id=rule.rule_id,
                severity=rule.severity,
                message=f"Content length ({len(entry.content)}) below minimum ({min_length})",
                suggestion="Add more detail to provide comprehensive information",
                confidence=0.9
            ))

        return issues

    async def validate_required_elements(self, rule: ValidationRule, entry: KnowledgeEntry) -> List[ValidationIssue]:
        """Validate required elements are present"""
        issues = []

        required_elements = {
            "procedure": ["step", "deadline", "requirement"],
            "form_guide": ["instruction", "field", "submit"],
            "exemption": ["qualification", "application", "deadline"]
        }

        if entry.entry_type in required_elements:
            required = required_elements[entry.entry_type]
            content_lower = entry.content.lower()

            missing_elements = [elem for elem in required if elem not in content_lower]

            if missing_elements:
                issues.append(ValidationIssue(
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    message=f"Missing required elements: {', '.join(missing_elements)}",
                    suggestion=f"Include information about {', '.join(missing_elements)}",
                    confidence=0.8
                ))

        return issues

    async def validate_definitions(self, rule: ValidationRule, entry: KnowledgeEntry) -> List[ValidationIssue]:
        """Validate legal terms are properly defined"""
        issues = []

        # Common legal terms that should be defined
        legal_terms = [
            "appraised value", "market value", "homestead exemption",
            "appraisal district", "protest", "rendition"
        ]

        content_lower = entry.content.lower()
        undefined_terms = []

        for term in legal_terms:
            if term in content_lower:
                # Check if term is defined (look for "means", "is defined as", etc.)
                definition_patterns = [
                    rf'{re.escape(term)}\s+means',
                    rf'{re.escape(term)}\s+is\s+defined\s+as',
                    rf'{re.escape(term)}\s*:\s*[A-Z]'
                ]

                if not any(re.search(pattern, entry.content, re.IGNORECASE) for pattern in definition_patterns):
                    undefined_terms.append(term)

        if undefined_terms:
            issues.append(ValidationIssue(
                rule_id=rule.rule_id,
                severity=rule.severity,
                message=f"Legal terms may need definition: {', '.join(undefined_terms[:3])}",
                suggestion="Consider defining technical legal terms for clarity",
                confidence=0.6
            ))

        return issues

    async def validate_currency(self, rule: ValidationRule, entry: KnowledgeEntry) -> List[ValidationIssue]:
        """Validate content currency and date information"""
        issues = []

        # Check for old dates that might indicate outdated content
        current_year = datetime.now().year
        date_pattern = r'(\d{4})'
        years_found = re.findall(date_pattern, entry.content)

        old_years = [year for year in years_found if int(year) < current_year - 5]

        if old_years and entry.entry_type in ["statute", "regulation", "procedure"]:
            issues.append(ValidationIssue(
                rule_id=rule.rule_id,
                severity=rule.severity,
                message=f"Content references old years: {', '.join(set(old_years))}",
                suggestion="Verify content is current and update if necessary",
                confidence=0.7
            ))

        return issues

    async def validate_factual_accuracy(self, rule: ValidationRule, entry: KnowledgeEntry) -> List[ValidationIssue]:
        """Validate factual accuracy of claims and numbers"""
        issues = []

        # Check for common factual elements
        dollar_amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', entry.content)
        percentages = re.findall(r'\d+(?:\.\d+)?%', entry.content)

        # Basic sanity checks for property tax amounts
        for amount_str in dollar_amounts:
            amount = float(amount_str.replace('$', '').replace(',', ''))
            if amount > 1000000:  # Very high exemption amounts might be errors
                issues.append(ValidationIssue(
                    rule_id=rule.rule_id,
                    severity=ValidationSeverity.WARNING,
                    message=f"Unusually high dollar amount found: {amount_str}",
                    suggestion="Verify the accuracy of large dollar amounts",
                    confidence=0.6
                ))

        return issues

    async def validate_readability(self, rule: ValidationRule, entry: KnowledgeEntry) -> List[ValidationIssue]:
        """Validate content readability for target audience"""
        issues = []

        # Basic readability metrics
        sentences = re.split(r'[.!?]+', entry.content)
        words = entry.content.split()

        if sentences and words:
            avg_sentence_length = len(words) / len(sentences)

            # Check for overly complex sentences
            if avg_sentence_length > 25 and entry.entry_type in ["faq", "form_guide"]:
                issues.append(ValidationIssue(
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    message=f"Average sentence length ({avg_sentence_length:.1f}) may be too complex",
                    suggestion="Consider breaking long sentences into shorter ones",
                    confidence=0.7
                ))

        return issues

    async def validate_terminology(self, rule: ValidationRule, entry: KnowledgeEntry) -> List[ValidationIssue]:
        """Validate consistent use of terminology"""
        issues = []

        # Check for terminology consistency
        terminology_variants = {
            "homestead exemption": ["residence exemption", "home exemption"],
            "appraisal district": ["CAD", "county appraisal"],
            "property tax": ["real estate tax", "ad valorem tax"]
        }

        content_lower = entry.content.lower()

        for standard_term, variants in terminology_variants.items():
            uses_standard = standard_term in content_lower
            uses_variants = any(variant in content_lower for variant in variants)

            if uses_variants and not uses_standard:
                issues.append(ValidationIssue(
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    message=f"Consider using standard term '{standard_term}' instead of variants",
                    suggestion=f"Use '{standard_term}' consistently throughout content",
                    confidence=0.6
                ))

        return issues

    async def validate_structure(self, rule: ValidationRule, entry: KnowledgeEntry) -> List[ValidationIssue]:
        """Validate proper content structure"""
        issues = []

        # Check for appropriate structure based on content type
        if entry.entry_type == "procedure":
            # Should have numbered steps or clear sequence
            if not re.search(r'(?:step|first|second|then|next|\d+\.)', entry.content, re.IGNORECASE):
                issues.append(ValidationIssue(
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    message="Procedural content lacks clear step structure",
                    suggestion="Organize content with clear numbered steps or sequence",
                    confidence=0.8
                ))

        elif entry.entry_type == "faq":
            # Should have question and answer format
            if not re.search(r'(?:Q:|question:|A:|answer:)', entry.content, re.IGNORECASE):
                issues.append(ValidationIssue(
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    message="FAQ content lacks clear Q&A structure",
                    suggestion="Format as clear questions and answers",
                    confidence=0.8
                ))

        return issues

    async def validate_cross_references(self, rule: ValidationRule, entry: KnowledgeEntry) -> List[ValidationIssue]:
        """Validate cross-references are valid"""
        issues = []

        # Check for "see also" or similar references
        cross_ref_patterns = [
            r'see\s+(?:also\s+)?(?:section|chapter|part)\s+[\d.]+',
            r'refer\s+to\s+(?:section|chapter|part)\s+[\d.]+',
            r'as\s+defined\s+in\s+(?:section|chapter|part)\s+[\d.]+']

        found_refs = []
        for pattern in cross_ref_patterns:
            matches = re.findall(pattern, entry.content, re.IGNORECASE)
            found_refs.extend(matches)

        # For now, just check if cross-references exist (actual validation would require content database)
        if found_refs:
            # This is actually good - note as positive finding
            pass

        return issues

    async def _calculate_quality_metrics(self, entry: KnowledgeEntry, issues: List[ValidationIssue]) -> Dict[str, float]:
        """Calculate quality metrics for the entry"""
        metrics = {}

        # Issue severity distribution
        critical_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.CRITICAL)
        warning_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.WARNING)
        info_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.INFO)

        metrics['critical_issues'] = critical_count
        metrics['warning_issues'] = warning_count
        metrics['info_issues'] = info_count
        metrics['total_issues'] = len(issues)

        # Content metrics
        metrics['content_length'] = len(entry.content)
        metrics['word_count'] = len(entry.content.split())
        metrics['citation_count'] = len(entry.citations)
        metrics['authority_level'] = entry.authority_level

        # Readability metrics
        sentences = re.split(r'[.!?]+', entry.content)
        if sentences:
            metrics['sentence_count'] = len(sentences)
            metrics['avg_sentence_length'] = metrics['word_count'] / len(sentences)
        else:
            metrics['sentence_count'] = 0
            metrics['avg_sentence_length'] = 0

        # Legal terminology density
        legal_terms = ['exemption', 'appraisal', 'assessment', 'protest', 'appeal', 'property tax']
        term_count = sum(1 for term in legal_terms if term in entry.content.lower())
        metrics['legal_term_density'] = term_count / max(metrics['word_count'] / 100, 1)

        return metrics

    async def _calculate_overall_score(self, entry: KnowledgeEntry, issues: List[ValidationIssue],
                                     metrics: Dict[str, float]) -> float:
        """Calculate overall quality score"""
        base_score = 1.0

        # Subtract points for issues
        for issue in issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                base_score -= 0.2 * issue.confidence
            elif issue.severity == ValidationSeverity.WARNING:
                base_score -= 0.1 * issue.confidence
            elif issue.severity == ValidationSeverity.INFO:
                base_score -= 0.05 * issue.confidence

        # Apply content type specific adjustments
        thresholds = self.quality_thresholds.get(entry.entry_type, {})

        # Length bonus/penalty
        min_length = thresholds.get("min_length", 100)
        if metrics['content_length'] >= min_length:
            base_score += 0.05  # Small bonus for adequate length
        else:
            base_score -= 0.1  # Penalty for insufficient length

        # Authority level adjustment
        min_authority = thresholds.get("min_authority_level", 0.5)
        if entry.authority_level >= min_authority:
            base_score += 0.05  # Bonus for good authority
        else:
            base_score -= 0.1  # Penalty for low authority

        # Citation bonus for legal documents
        if entry.entry_type in ["statute", "regulation"] and metrics['citation_count'] > 0:
            base_score += 0.05

        return max(0.0, min(1.0, base_score))

    async def _generate_recommendations(self, entry: KnowledgeEntry, issues: List[ValidationIssue],
                                      metrics: Dict[str, float]) -> List[str]:
        """Generate recommendations for improvement"""
        recommendations = []

        # High-priority recommendations based on critical issues
        critical_issues = [issue for issue in issues if issue.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            recommendations.append("Address critical legal accuracy issues immediately")

        # Content length recommendations
        thresholds = self.quality_thresholds.get(entry.entry_type, {})
        min_length = thresholds.get("min_length", 100)
        if metrics['content_length'] < min_length:
            recommendations.append(f"Expand content to at least {min_length} characters for better coverage")

        # Citation recommendations
        if entry.entry_type in ["statute", "regulation"] and metrics['citation_count'] == 0:
            recommendations.append("Add legal citations to support the content")

        # Readability recommendations
        if metrics.get('avg_sentence_length', 0) > 25:
            recommendations.append("Break up long sentences for better readability")

        # Authority recommendations
        if entry.authority_level < 0.7:
            recommendations.append("Verify content comes from authoritative sources")

        # Structure recommendations based on content type
        if entry.entry_type == "procedure" and not re.search(r'\d+\.|\bstep\b', entry.content, re.IGNORECASE):
            recommendations.append("Organize procedural content with numbered steps")

        # Limit to top 5 recommendations
        return recommendations[:5]

    async def validate_knowledge_batch(self, entries: List[KnowledgeEntry]) -> List[ValidationResult]:
        """Validate a batch of knowledge entries"""
        self.logger.info(f"🔍 Validating batch of {len(entries)} knowledge entries")

        results = []
        for entry in entries:
            try:
                result = await self.validate_knowledge_entry(entry)
                results.append(result)
            except Exception as e:
                self.logger.error(f"❌ Failed to validate entry {entry.entry_id}: {e}")
                # Create a failure result
                results.append(ValidationResult(
                    entry_id=entry.entry_id,
                    overall_score=0.0,
                    validation_issues=[ValidationIssue(
                        rule_id="validation_error",
                        severity=ValidationSeverity.CRITICAL,
                        message=f"Validation failed: {str(e)}",
                        confidence=1.0
                    )],
                    quality_metrics={},
                    validation_timestamp=datetime.now(),
                    recommendations=["Fix validation errors before re-validating"]
                ))

        self.logger.info(f"✅ Batch validation complete: {len(results)} results")
        return results

    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Get summary statistics for validation results"""
        if not results:
            return {}

        scores = [result.overall_score for result in results]
        total_issues = sum(len(result.validation_issues) for result in results)

        # Count issues by severity
        severity_counts = {
            ValidationSeverity.CRITICAL.value: 0,
            ValidationSeverity.WARNING.value: 0,
            ValidationSeverity.INFO.value: 0
        }

        for result in results:
            for issue in result.validation_issues:
                severity_counts[issue.severity.value] += 1

        return {
            'total_entries': len(results),
            'average_score': sum(scores) / len(scores) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'total_issues': total_issues,
            'issues_by_severity': severity_counts,
            'entries_needing_attention': sum(1 for score in scores if score < 0.7),
            'high_quality_entries': sum(1 for score in scores if score >= 0.8)
        }

# Global instance
_quality_validator = None

async def get_quality_validator() -> PropertyTaxQualityValidator:
    """Get the global quality validator instance"""
    global _quality_validator
    if _quality_validator is None:
        _quality_validator = PropertyTaxQualityValidator()
        await _quality_validator.initialize()
    return _quality_validator

if __name__ == "__main__":
    # Test quality validator
    async def test_validator():
        validator = PropertyTaxQualityValidator()
        await validator.initialize()

        # Create a test knowledge entry
        from .content_processor import KnowledgeEntry

        test_entry = KnowledgeEntry(
            entry_id="test_001",
            title="Homestead Exemption Basics",
            content="""A person is entitled to an exemption from taxation of $25,000 of the
                       appraised value of the person's residence homestead. The homestead exemption
                       reduces the taxable value of your home.""",
            entry_type="exemption",
            topic_categories=["exemptions"],
            subtopics=["homestead_exemption"],
            authority_level=0.8,
            difficulty_level="basic",
            target_audience=["taxpayer"],
            related_entries=[],
            citations=[]
        )

        # Validate the entry
        result = await validator.validate_knowledge_entry(test_entry)

        print(f"Overall Score: {result.overall_score:.2f}")
        print(f"Issues Found: {len(result.validation_issues)}")
        for issue in result.validation_issues:
            print(f"  - {issue.severity.value}: {issue.message}")
        print(f"Recommendations: {result.recommendations}")

    asyncio.run(test_validator())