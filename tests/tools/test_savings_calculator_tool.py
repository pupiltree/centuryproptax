"""
Unit Tests for Savings Calculator Tool

Comprehensive tests for tax savings calculation functionality including
exemption optimization, appeal scenarios, and multi-year projections.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime

from agents.tools.savings_calculator_tool import (
    savings_calculator_tool,
    calculate_multi_year_projections,
    compare_county_rates
)

class TestSavingsCalculatorTool:
    """Test class for savings calculator tool"""

    @pytest.mark.asyncio
    async def test_savings_calculation_basic_residential(self):
        """Test basic savings calculation for residential property"""
        result = await savings_calculator_tool(
            property_value=400000,
            county_code="harris",
            city="houston",
            property_type="residential",
            current_exemptions={"homestead": True},
            calculation_type="comprehensive"
        )

        assert result["success"] is True
        assert "current_scenario" in result
        assert "optimized_scenario" in result
        assert "savings_summary" in result

        current = result["current_scenario"]
        assert current["assessed_value"] == 400000
        assert current["annual_tax"] > 0

        savings = result["savings_summary"]
        assert "annual_savings" in savings
        assert "five_year_savings" in savings
        assert "savings_percentage" in savings

        print("✅ Basic residential calculation test passed")
        print(f"   Property value: ${current['assessed_value']:,}")
        print(f"   Current annual tax: ${current['annual_tax']:,}")
        print(f"   Potential annual savings: ${savings['annual_savings']:,}")
        print(f"   Savings percentage: {savings['savings_percentage']:.1f}%")

    @pytest.mark.asyncio
    async def test_savings_calculation_exemption_optimization(self):
        """Test exemption optimization scenarios"""
        # Test without exemptions
        result_no_exemptions = await savings_calculator_tool(
            property_value=500000,
            county_code="dallas",
            property_type="residential",
            current_exemptions={},
            potential_exemptions={"homestead": True, "senior": True},
            calculation_type="exemption_only"
        )

        assert result_no_exemptions["success"] is True

        # Test with existing exemptions
        result_with_exemptions = await savings_calculator_tool(
            property_value=500000,
            county_code="dallas",
            property_type="residential",
            current_exemptions={"homestead": True},
            potential_exemptions={"senior": True, "disability": True},
            calculation_type="exemption_only"
        )

        assert result_with_exemptions["success"] is True

        # Verify exemption optimization provides recommendations
        if result_no_exemptions["exemption_opportunities"]:
            assert len(result_no_exemptions["exemption_opportunities"]) > 0
            homestead_opportunity = next(
                (opp for opp in result_no_exemptions["exemption_opportunities"]
                 if opp["exemption_type"] == "homestead"), None
            )
            assert homestead_opportunity is not None

        print("✅ Exemption optimization test passed")
        print(f"   Exemption opportunities found: {len(result_no_exemptions.get('exemption_opportunities', []))}")

    @pytest.mark.asyncio
    async def test_savings_calculation_appeal_scenarios(self):
        """Test appeal scenario calculations"""
        result = await savings_calculator_tool(
            property_value=600000,
            county_code="travis",
            property_type="residential",
            appeal_scenario={
                "evidence_strength": "strong",
                "target_reduction": 0.15
            },
            calculation_type="appeal_only"
        )

        assert result["success"] is True
        assert "appeal_scenarios" in result
        assert len(result["appeal_scenarios"]) > 0

        # Check appeal scenario details
        for scenario in result["appeal_scenarios"]:
            assert "scenario_name" in scenario
            assert "success_probability" in scenario
            assert "potential_reduction_percent" in scenario
            assert scenario["success_probability"] >= 0
            assert scenario["success_probability"] <= 1

        print("✅ Appeal scenarios test passed")
        print(f"   Appeal scenarios generated: {len(result['appeal_scenarios'])}")
        for scenario in result["appeal_scenarios"][:2]:
            print(f"   {scenario['scenario_name']}: {scenario['success_probability']:.1%} success rate")

    @pytest.mark.asyncio
    async def test_savings_calculation_commercial_property(self):
        """Test savings calculation for commercial property"""
        result = await savings_calculator_tool(
            property_value=2000000,
            county_code="harris",
            property_type="commercial",
            calculation_type="comprehensive"
        )

        assert result["success"] is True

        current = result["current_scenario"]
        assert current["assessed_value"] == 2000000

        # Commercial properties should have different tax characteristics
        assert "rate_breakdown" in current
        assert current["annual_tax"] > 0

        print("✅ Commercial property calculation test passed")
        print(f"   Commercial property value: ${current['assessed_value']:,}")
        print(f"   Annual tax: ${current['annual_tax']:,}")

    @pytest.mark.asyncio
    async def test_savings_calculation_invalid_inputs(self):
        """Test error handling with invalid inputs"""
        # Test invalid property value
        result_invalid_value = await savings_calculator_tool(
            property_value=0,
            county_code="harris"
        )

        assert result_invalid_value["success"] is False
        assert "error" in result_invalid_value

        # Test invalid county
        result_invalid_county = await savings_calculator_tool(
            property_value=300000,
            county_code="invalid_county"
        )

        assert result_invalid_county["success"] is False
        assert "error" in result_invalid_county

        print("✅ Invalid inputs test passed")

    @pytest.mark.asyncio
    async def test_savings_calculation_comprehensive_analysis(self):
        """Test comprehensive savings analysis with all options"""
        result = await savings_calculator_tool(
            property_value=750000,
            county_code="collin",
            city="plano",
            school_district="plano_isd",
            property_type="residential",
            current_exemptions={"homestead": True},
            potential_exemptions={"senior": True},
            appeal_scenario={"evidence_strength": "moderate"},
            calculation_type="comprehensive"
        )

        assert result["success"] is True

        # Verify all components are present
        assert "current_scenario" in result
        assert "optimized_scenario" in result
        assert "savings_summary" in result
        assert "recommendations" in result
        assert "scenarios_compared" in result
        assert "calculation_details" in result

        # Verify rate breakdown includes school district
        current = result["current_scenario"]
        if "rate_breakdown" in current:
            # Should include various tax entities
            assert len(current["rate_breakdown"]) > 1

        savings = result["savings_summary"]
        assert "optimization_steps" in savings

        print("✅ Comprehensive analysis test passed")
        print(f"   Total potential savings: ${savings['annual_savings']:,}")
        print(f"   Optimization steps: {len(savings.get('optimization_steps', []))}")

    def test_compare_county_rates(self):
        """Test county tax rate comparison"""
        counties = ["harris", "dallas", "travis"]
        property_value = 400000

        comparison = compare_county_rates(property_value, counties)

        assert len(comparison) == len(counties)
        for county in counties:
            assert county in comparison
            county_data = comparison[county]
            assert "county_name" in county_data
            assert "total_rate" in county_data
            assert "annual_tax" in county_data
            assert "effective_rate" in county_data

        print("✅ County comparison test passed")
        for county, data in comparison.items():
            print(f"   {data['county_name']}: ${data['annual_tax']:,} annual tax ({data['effective_rate']:.3f}%)")

    @pytest.mark.asyncio
    async def test_multi_year_projections(self):
        """Test multi-year savings projections"""
        # First get a base calculation
        base_calculation = await savings_calculator_tool(
            property_value=500000,
            county_code="harris",
            property_type="residential",
            calculation_type="comprehensive"
        )

        assert base_calculation["success"] is True

        # Generate projections
        projections = await calculate_multi_year_projections(
            base_calculation,
            years=5,
            annual_appreciation=0.05
        )

        assert len(projections) == 5
        for i, projection in enumerate(projections):
            assert projection["year"] == i + 1
            assert projection["projected_value"] > 500000  # Should increase with appreciation
            assert "projected_savings" in projection

        print("✅ Multi-year projections test passed")
        for projection in projections[:3]:
            print(f"   Year {projection['year']}: ${projection['projected_value']:,} value, ${projection['projected_savings']:,} savings")

class TestSavingsCalculatorIntegration:
    """Integration tests for savings calculator"""

    @pytest.mark.asyncio
    async def test_end_to_end_savings_analysis(self):
        """Test complete savings analysis workflow"""
        print("🔍 End-to-end savings analysis started")

        # Scenario: Homeowner with recent assessment increase
        result = await savings_calculator_tool(
            property_value=550000,  # Current assessment
            county_code="harris",
            city="houston",
            school_district="houston_isd",
            property_type="residential",
            current_exemptions={"homestead": True},
            potential_exemptions={"senior": False, "disability": False},
            appeal_scenario={"evidence_strength": "strong"},
            calculation_type="comprehensive"
        )

        assert result["success"] is True

        # Analyze results
        current = result["current_scenario"]
        optimized = result["optimized_scenario"]
        savings = result["savings_summary"]

        print(f"   Current situation:")
        print(f"     Assessed value: ${current['assessed_value']:,}")
        print(f"     Taxable value: ${current['taxable_value']:,}")
        print(f"     Annual tax: ${current['annual_tax']:,}")

        print(f"   Optimized situation:")
        print(f"     Taxable value: ${optimized['taxable_value']:,}")
        print(f"     Annual tax: ${optimized['annual_tax']:,}")

        print(f"   Savings potential:")
        print(f"     Annual savings: ${savings['annual_savings']:,}")
        print(f"     5-year savings: ${savings['five_year_savings']:,}")
        print(f"     Savings percentage: {savings['savings_percentage']:.1f}%")

        # Verify recommendations are actionable
        recommendations = result["recommendations"]
        assert len(recommendations) > 0

        print(f"   Recommendations: {len(recommendations)}")
        for rec in recommendations[:2]:
            print(f"     - {rec['title']} (${rec.get('estimated_annual_savings', 0):,} potential)")

        print("✅ End-to-end analysis completed successfully")

    @pytest.mark.asyncio
    async def test_multiple_property_types_comparison(self):
        """Test savings calculations across different property types"""
        property_types = ["residential", "commercial", "industrial"]
        base_value = 500000

        results = {}
        for prop_type in property_types:
            result = await savings_calculator_tool(
                property_value=base_value,
                county_code="dallas",
                property_type=prop_type,
                calculation_type="comprehensive"
            )

            if result["success"]:
                results[prop_type] = result

        assert len(results) >= 2  # At least residential and commercial should work

        print("✅ Property type comparison test passed")
        for prop_type, result in results.items():
            current = result["current_scenario"]
            savings = result["savings_summary"]
            print(f"   {prop_type.title()}: ${current['annual_tax']:,} tax, ${savings['annual_savings']:,} potential savings")

    @pytest.mark.asyncio
    async def test_performance_bulk_calculations(self):
        """Test performance with multiple simultaneous calculations"""
        import time

        # Create test scenarios
        scenarios = [
            {"property_value": 300000, "county_code": "harris", "property_type": "residential"},
            {"property_value": 500000, "county_code": "dallas", "property_type": "residential"},
            {"property_value": 1000000, "county_code": "travis", "property_type": "commercial"},
            {"property_value": 750000, "county_code": "tarrant", "property_type": "residential"},
            {"property_value": 1500000, "county_code": "bexar", "property_type": "commercial"}
        ]

        start_time = time.time()

        # Run calculations concurrently
        tasks = [
            savings_calculator_tool(**scenario)
            for scenario in scenarios
        ]

        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Verify all calculations succeeded
        successful_results = [r for r in results if r.get("success")]
        assert len(successful_results) >= len(scenarios) * 0.8  # At least 80% success rate

        print(f"✅ Performance test: {len(scenarios)} calculations in {total_time:.2f} seconds")
        print(f"   Success rate: {len(successful_results)}/{len(scenarios)} ({len(successful_results)/len(scenarios)*100:.1f}%)")
        print(f"   Average time per calculation: {total_time/len(scenarios):.3f} seconds")

if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v", "-s"])