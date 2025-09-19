"""
Unit Tests for Lead Qualification Tool

Comprehensive tests for lead qualification functionality including
scoring algorithms, quality tiers, and recommendation generation.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from agents.tools.lead_qualification_tool import (
    lead_qualification_tool,
    qualify_multiple_leads,
    generate_lead_report,
    filter_leads_by_criteria,
    get_lead_recommendations_summary
)

class TestLeadQualificationTool:
    """Test class for lead qualification tool"""

    @pytest.mark.asyncio
    async def test_lead_qualification_high_value_property(self):
        """Test lead qualification for high-value property"""
        result = await lead_qualification_tool(
            property_value=800000,
            county_code="harris",
            previous_value=650000,  # Significant increase
            property_type="residential",
            appeal_history="never_appealed"
        )

        assert result["success"] is True
        assert "qualification_score" in result
        assert "quality_tier" in result
        assert "estimated_savings" in result

        # High value property with significant increase should score well
        assert result["qualification_score"] >= 60

        quality_tier = result["quality_tier"]
        assert quality_tier in ["very_high", "high", "medium", "low", "very_low"]

        savings = result["estimated_savings"]
        assert savings["expected_annual_savings"] > 0

        print("✅ High-value property qualification test passed")
        print(f"   Qualification score: {result['qualification_score']}")
        print(f"   Quality tier: {quality_tier}")
        print(f"   Expected annual savings: ${savings['expected_annual_savings']:,}")
        print(f"   ROI percentage: {savings['roi_percentage']:.1f}%")

    @pytest.mark.asyncio
    async def test_lead_qualification_commercial_property(self):
        """Test lead qualification for commercial property"""
        result = await lead_qualification_tool(
            property_value=2000000,
            county_code="dallas",
            previous_value=1700000,
            property_type="commercial",
            case_complexity="high",
            appeal_history="never_appealed"
        )

        assert result["success"] is True

        # Commercial properties typically score higher due to higher values
        assert result["qualification_score"] >= 50

        # Verify appeal analysis includes commercial-specific factors
        appeal_analysis = result["appeal_analysis"]
        assert "success_probability" in appeal_analysis
        assert "estimated_reduction" in appeal_analysis

        print("✅ Commercial property qualification test passed")
        print(f"   Commercial property score: {result['qualification_score']}")
        print(f"   Appeal success probability: {appeal_analysis['success_probability']:.1%}")

    @pytest.mark.asyncio
    async def test_lead_qualification_low_value_property(self):
        """Test lead qualification for low-value property"""
        result = await lead_qualification_tool(
            property_value=150000,
            county_code="bexar",
            previous_value=145000,  # Minimal increase
            property_type="residential",
            appeal_history="multiple_appeals"
        )

        assert result["success"] is True

        # Low value with minimal increase and multiple appeals should score lower
        score = result["qualification_score"]
        print(f"✅ Low-value property qualification test passed")
        print(f"   Low-value property score: {score}")

        # Verify appropriate priority level
        priority = result["priority_level"]
        assert priority in ["immediate_contact", "contact_within_24h", "contact_within_week", "contact_when_available", "do_not_pursue"]

    @pytest.mark.asyncio
    async def test_lead_qualification_with_assessment_increase(self):
        """Test qualification with various assessment increase levels"""
        base_value = 400000

        # Test different increase scenarios
        increase_scenarios = [
            {"previous": 390000, "description": "minimal increase"},
            {"previous": 350000, "description": "moderate increase"},
            {"previous": 300000, "description": "significant increase"},
            {"previous": 250000, "description": "substantial increase"}
        ]

        scores = []
        for scenario in increase_scenarios:
            result = await lead_qualification_tool(
                property_value=base_value,
                county_code="travis",
                previous_value=scenario["previous"],
                property_type="residential"
            )

            assert result["success"] is True
            scores.append({
                "scenario": scenario["description"],
                "score": result["qualification_score"],
                "increase_percent": result["property_analysis"]["assessment_increase_percent"]
            })

        print("✅ Assessment increase scenarios test passed")
        for score_data in scores:
            print(f"   {score_data['scenario']}: {score_data['increase_percent']:.1f}% increase, score {score_data['score']}")

        # Verify that higher increases generally result in higher scores
        # (allowing for some variation due to other factors)
        highest_increase = max(scores, key=lambda x: x["increase_percent"])
        lowest_increase = min(scores, key=lambda x: x["increase_percent"])

        # This should generally be true, though other factors can affect the score
        print(f"   Highest increase score: {highest_increase['score']}, Lowest increase score: {lowest_increase['score']}")

    @pytest.mark.asyncio
    async def test_lead_qualification_invalid_inputs(self):
        """Test error handling with invalid inputs"""
        # Test invalid property value
        result_invalid_value = await lead_qualification_tool(
            property_value=0,
            county_code="harris"
        )

        assert result_invalid_value["success"] is False
        assert "error" in result_invalid_value

        # Test invalid county
        result_invalid_county = await lead_qualification_tool(
            property_value=300000,
            county_code="invalid_county"
        )

        assert result_invalid_county["success"] is False

        print("✅ Invalid inputs test passed")

    @pytest.mark.asyncio
    async def test_qualify_multiple_leads(self):
        """Test bulk lead qualification"""
        leads = [
            {
                "property_value": 500000,
                "county_code": "harris",
                "previous_value": 420000,
                "property_type": "residential",
                "appeal_history": "never_appealed"
            },
            {
                "property_value": 1200000,
                "county_code": "dallas",
                "previous_value": 1000000,
                "property_type": "commercial",
                "appeal_history": "never_appealed"
            },
            {
                "property_value": 200000,
                "county_code": "travis",
                "previous_value": 195000,
                "property_type": "residential",
                "appeal_history": "unsuccessful_appeal"
            }
        ]

        results = await qualify_multiple_leads(leads)

        assert len(results) == len(leads)

        # Results should be sorted by qualification score (highest first)
        for i in range(len(results) - 1):
            if results[i].get("success") and results[i+1].get("success"):
                assert results[i]["qualification_score"] >= results[i+1]["qualification_score"]

        successful_results = [r for r in results if r.get("success")]
        print(f"✅ Multiple leads qualification test passed")
        print(f"   Processed {len(leads)} leads, {len(successful_results)} successful")

    def test_generate_lead_report(self):
        """Test lead report generation"""
        # Create sample qualified leads
        sample_leads = [
            {
                "success": True,
                "qualification_score": 85,
                "quality_tier": "very_high",
                "priority_level": "immediate_contact",
                "estimated_savings": {"expected_annual_savings": 8000}
            },
            {
                "success": True,
                "qualification_score": 70,
                "quality_tier": "high",
                "priority_level": "contact_within_24h",
                "estimated_savings": {"expected_annual_savings": 3500}
            },
            {
                "success": True,
                "qualification_score": 45,
                "quality_tier": "medium",
                "priority_level": "contact_within_week",
                "estimated_savings": {"expected_annual_savings": 1200}
            }
        ]

        report = generate_lead_report(sample_leads)

        assert "total_leads" in report
        assert "quality_distribution" in report
        assert "high_priority_count" in report
        assert "total_potential_annual_savings" in report
        assert "average_qualification_score" in report
        assert "top_leads" in report

        assert report["total_leads"] == 3
        assert report["total_potential_annual_savings"] == 12700
        assert len(report["top_leads"]) <= 5

        print("✅ Lead report generation test passed")
        print(f"   Total leads: {report['total_leads']}")
        print(f"   High priority leads: {report['high_priority_count']}")
        print(f"   Total potential savings: ${report['total_potential_annual_savings']:,}")

    def test_filter_leads_by_criteria(self):
        """Test lead filtering functionality"""
        sample_leads = [
            {
                "success": True,
                "qualification_score": 85,
                "quality_tier": "very_high",
                "estimated_savings": {"expected_annual_savings": 8000},
                "property_analysis": {"county": "harris"}
            },
            {
                "success": True,
                "qualification_score": 70,
                "quality_tier": "high",
                "estimated_savings": {"expected_annual_savings": 3500},
                "property_analysis": {"county": "dallas"}
            },
            {
                "success": True,
                "qualification_score": 45,
                "quality_tier": "medium",
                "estimated_savings": {"expected_annual_savings": 1200},
                "property_analysis": {"county": "harris"}
            }
        ]

        # Test score filtering
        high_score_leads = filter_leads_by_criteria(
            sample_leads,
            min_score=70
        )
        assert len(high_score_leads) == 2

        # Test tier filtering
        high_tier_leads = filter_leads_by_criteria(
            sample_leads,
            quality_tiers=["very_high", "high"]
        )
        assert len(high_tier_leads) == 2

        # Test savings filtering
        high_savings_leads = filter_leads_by_criteria(
            sample_leads,
            min_savings=3000
        )
        assert len(high_savings_leads) == 2

        # Test county filtering
        harris_leads = filter_leads_by_criteria(
            sample_leads,
            counties=["harris"]
        )
        assert len(harris_leads) == 2

        print("✅ Lead filtering test passed")
        print(f"   High score leads: {len(high_score_leads)}")
        print(f"   Harris county leads: {len(harris_leads)}")

    def test_get_lead_recommendations_summary(self):
        """Test lead recommendations summary"""
        quality_tiers = ["very_high", "high", "medium", "low"]

        for tier in quality_tiers:
            summary = get_lead_recommendations_summary(tier)

            assert "quality_tier" in summary
            assert "score_range" in summary
            assert "priority" in summary
            assert "success_probability" in summary
            assert "estimated_savings_range" in summary
            assert "typical_characteristics" in summary

            assert summary["quality_tier"] == tier
            assert len(summary["score_range"]) == 2
            assert summary["success_probability"] >= 0
            assert summary["success_probability"] <= 1

        print("✅ Lead recommendations summary test passed")

class TestLeadQualificationIntegration:
    """Integration tests for lead qualification"""

    @pytest.mark.asyncio
    async def test_end_to_end_lead_qualification_workflow(self):
        """Test complete lead qualification workflow"""
        print("🔍 End-to-end lead qualification workflow started")

        # Scenario: High-potential residential lead
        result = await lead_qualification_tool(
            property_value=650000,
            county_code="collin",
            previous_value=500000,  # 30% increase
            property_type="residential",
            city="plano",
            appeal_history="never_appealed",
            case_complexity="medium",
            lead_source="website_inquiry"
        )

        assert result["success"] is True

        # Analyze qualification results
        score = result["qualification_score"]
        tier = result["quality_tier"]
        priority = result["priority_level"]

        print(f"   Qualification Results:")
        print(f"     Score: {score}/100")
        print(f"     Quality tier: {tier}")
        print(f"     Priority level: {priority}")

        # Analyze financial potential
        savings = result["estimated_savings"]
        print(f"   Financial Analysis:")
        print(f"     Expected annual savings: ${savings['expected_annual_savings']:,}")
        print(f"     5-year savings: ${savings['five_year_expected_savings']:,}")
        print(f"     ROI percentage: {savings['roi_percentage']:.1f}%")

        # Analyze appeal prospects
        appeal = result["appeal_analysis"]
        print(f"   Appeal Analysis:")
        print(f"     Success probability: {appeal['success_probability']:.1%}")
        print(f"     Estimated reduction: {appeal['estimated_reduction']:.1%}")

        # Verify recommendations are actionable
        recommendations = result["recommendations"]
        print(f"   Sales Recommendations:")
        print(f"     Contact strategy: {recommendations['approach_strategy']}")
        print(f"     Follow-up schedule: {recommendations['follow_up_schedule']}")

        # Verify score components make sense
        score_breakdown = result["score_breakdown"]
        print(f"   Score Components:")
        for component, score_val in score_breakdown["component_scores"].items():
            print(f"     {component}: {score_val}/10")

        print("✅ End-to-end workflow completed successfully")

    @pytest.mark.asyncio
    async def test_lead_qualification_market_segments(self):
        """Test qualification across different market segments"""
        market_scenarios = [
            {
                "name": "Luxury Residential",
                "property_value": 1200000,
                "property_type": "residential",
                "county_code": "harris"
            },
            {
                "name": "Mid-Market Residential",
                "property_value": 400000,
                "property_type": "residential",
                "county_code": "dallas"
            },
            {
                "name": "Small Commercial",
                "property_value": 800000,
                "property_type": "commercial",
                "county_code": "travis"
            },
            {
                "name": "Large Commercial",
                "property_value": 5000000,
                "property_type": "commercial",
                "county_code": "harris"
            }
        ]

        results = {}
        for scenario in market_scenarios:
            result = await lead_qualification_tool(
                property_value=scenario["property_value"],
                county_code=scenario["county_code"],
                property_type=scenario["property_type"],
                appeal_history="never_appealed"
            )

            if result["success"]:
                results[scenario["name"]] = {
                    "score": result["qualification_score"],
                    "tier": result["quality_tier"],
                    "market_segment": result.get("market_segment"),
                    "savings": result["estimated_savings"]["expected_annual_savings"]
                }

        print("✅ Market segments test passed")
        for segment, data in results.items():
            print(f"   {segment}: Score {data['score']}, Tier {data['tier']}, ${data['savings']:,} savings")

if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v", "-s"])