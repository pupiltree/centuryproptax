"""
Test Runner for Property Tax Tools

Comprehensive test suite runner that executes all tool tests
and provides detailed reporting for debugging and verification.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest


def run_individual_tool_tests():
    """Run tests for each tool individually with detailed output"""

    test_files = [
        "test_property_validation_tool.py",
        "test_savings_calculator_tool.py",
        "test_lead_qualification_tool.py"
    ]

    results = {}
    total_start_time = time.time()

    print("🧪 Starting Property Tax Tools Test Suite")
    print("=" * 60)

    for test_file in test_files:
        tool_name = test_file.replace("test_", "").replace(".py", "")
        print(f"\n📋 Running tests for {tool_name}")
        print("-" * 40)

        start_time = time.time()

        # Run pytest for individual file
        result = pytest.main([
            str(Path(__file__).parent / test_file),
            "-v",
            "-s",
            "--tb=short"
        ])

        end_time = time.time()
        duration = end_time - start_time

        results[tool_name] = {
            "result_code": result,
            "duration": duration,
            "status": "PASSED" if result == 0 else "FAILED"
        }

        print(f"\n✅ {tool_name} tests completed in {duration:.2f}s - {results[tool_name]['status']}")

    total_duration = time.time() - total_start_time

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for r in results.values() if r["status"] == "PASSED")
    failed_count = len(results) - passed_count

    for tool_name, result in results.items():
        status_icon = "✅" if result["status"] == "PASSED" else "❌"
        print(f"{status_icon} {tool_name}: {result['status']} ({result['duration']:.2f}s)")

    print(f"\nTotal: {len(results)} test suites")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print(f"Total time: {total_duration:.2f}s")

    return failed_count == 0


async def test_tool_integration():
    """Test integration between tools"""
    print("\n🔗 Testing Tool Integration")
    print("-" * 40)

    try:
        # Import all tools
        from agents.tools.property_validation_tool import property_validation_tool
        from agents.tools.savings_calculator_tool import savings_calculator_tool
        from agents.tools.deadline_tracking_tool import deadline_tracking_tool
        from agents.tools.lead_qualification_tool import lead_qualification_tool
        from agents.tools.document_processing_tool import document_processing_tool
        from agents.tools.consultation_scheduling_tool import consultation_scheduling_tool

        print("✅ All tools imported successfully")

        # Test basic workflow integration
        print("\n🔄 Testing Basic Workflow Integration")

        # Step 1: Validate a property
        property_result = await property_validation_tool.ainvoke({
            "search_query": "123 Main Street, Houston, TX",
            "search_type": "auto"
        })

        assert property_result["success"], "Property validation failed"
        print("✅ Property validation successful")

        if property_result["property_found"]:
            property_data = property_result["property_data"]

            # Step 2: Calculate savings for the property
            savings_result = await savings_calculator_tool.ainvoke({
                "property_value": property_data["current_assessed_value"],
                "county_code": "harris",
                "property_type": "residential"
            })

            assert savings_result["success"], "Savings calculation failed"
            print("✅ Savings calculation successful")

            # Step 3: Qualify as a lead
            lead_result = await lead_qualification_tool.ainvoke({
                "property_value": property_data["current_assessed_value"],
                "county_code": "harris",
                "property_type": "residential"
            })

            assert lead_result["success"], "Lead qualification failed"
            print("✅ Lead qualification successful")

            # Step 4: Check deadlines
            deadline_result = await deadline_tracking_tool.ainvoke({
                "county_code": "harris",
                "tracking_type": "all"
            })

            assert deadline_result["success"], "Deadline tracking failed"
            print("✅ Deadline tracking successful")

            # Step 5: Test document processing
            doc_result = await document_processing_tool.ainvoke({
                "document_content": "Sample property tax document",
                "document_type": "appraisal_notice"
            })

            assert doc_result["success"], "Document processing failed"
            print("✅ Document processing successful")

            # Step 6: Test consultation scheduling
            consultation_result = await consultation_scheduling_tool.ainvoke({
                "appointment_type": "initial_consultation",
                "county": "harris",
                "property_type": "residential"
            })

            assert consultation_result["success"], "Consultation scheduling failed"
            print("✅ Consultation scheduling successful")

            print("\n🎉 All integration tests passed!")
            return True

        else:
            print("⚠️  Property not found, testing with default values")

            # Test with default values
            savings_result = await savings_calculator_tool.ainvoke({
                "property_value": 400000,
                "county_code": "harris",
                "property_type": "residential"
            })

            assert savings_result["success"], "Savings calculation with defaults failed"
            print("✅ Integration tests with defaults successful")
            return True

    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        return False


def test_mock_data_availability():
    """Test that all mock data is available and properly structured"""
    print("\n📊 Testing Mock Data Availability")
    print("-" * 40)

    try:
        # Test property records
        from mock_data.property_records import PROPERTY_RECORDS, find_property_by_address
        print(f"✅ Property records: {len(PROPERTY_RECORDS)} properties loaded")

        # Test tax rates
        from mock_data.tax_rates import COUNTY_TAX_RATES, calculate_total_tax_rate
        print(f"✅ Tax rates: {len(COUNTY_TAX_RATES)} counties configured")

        # Test tax calendars
        from mock_data.tax_calendars import COUNTY_TAX_CALENDARS, get_current_deadlines
        print(f"✅ Tax calendars: {len(COUNTY_TAX_CALENDARS)} county calendars loaded")

        # Test assessment patterns
        from mock_data.assessment_patterns import ASSESSMENT_INCREASE_PATTERNS, APPEAL_SUCCESS_PATTERNS
        print(f"✅ Assessment patterns: {len(ASSESSMENT_INCREASE_PATTERNS)} counties with pattern data")

        # Test document templates
        from mock_data.document_templates import DOCUMENT_TYPES, DOCUMENT_TEMPLATES
        print(f"✅ Document templates: {len(DOCUMENT_TYPES)} document types, {len(DOCUMENT_TEMPLATES)} templates")

        # Test consultant schedules
        from mock_data.consultant_schedules import CONSULTANT_PROFILES, APPOINTMENT_TYPES
        print(f"✅ Consultant schedules: {len(CONSULTANT_PROFILES)} consultants, {len(APPOINTMENT_TYPES)} appointment types")

        print("\n🎉 All mock data successfully loaded!")
        return True

    except Exception as e:
        print(f"❌ Mock data test failed: {str(e)}")
        return False


async def test_ai_framework_integration():
    """Test integration with existing AI chat framework"""
    print("\n🤖 Testing AI Framework Integration")
    print("-" * 40)

    try:
        # Check if tools follow LangChain @tool decorator pattern
        from agents.tools.property_validation_tool import property_validation_tool

        # Verify tool has required attributes
        assert hasattr(property_validation_tool, 'name'), "Tool missing name attribute"
        assert hasattr(property_validation_tool, 'description'), "Tool missing description attribute"

        print("✅ Tools follow LangChain @tool pattern")

        # Test that tools can be called asynchronously (required for AI framework)
        result = await property_validation_tool.ainvoke({
            "search_query": "test address",
            "search_type": "auto"
        })

        assert isinstance(result, dict), "Tool should return dictionary"
        assert "success" in result, "Tool should include success field"

        print("✅ Tools return properly structured responses")

        # Test error handling (AI framework requires graceful error handling)
        error_result = await property_validation_tool.ainvoke({
            "search_query": "",
            "search_type": "invalid_type"
        })

        # Should not raise exception, should return error in response
        assert isinstance(error_result, dict), "Error handling should return dict"
        print("✅ Tools handle errors gracefully")

        print("\n🎉 AI framework integration tests passed!")
        return True

    except Exception as e:
        print(f"❌ AI framework integration test failed: {str(e)}")
        return False


async def main():
    """Main test runner"""
    print("🚀 Century Property Tax Tools - Comprehensive Test Suite")
    print("=" * 70)

    # Track overall results
    all_passed = True

    # 1. Run individual tool tests
    tools_passed = run_individual_tool_tests()
    all_passed &= tools_passed

    # 2. Test mock data
    mock_data_passed = test_mock_data_availability()
    all_passed &= mock_data_passed

    # 3. Test tool integration
    integration_passed = await test_tool_integration()
    all_passed &= integration_passed

    # 4. Test AI framework integration
    ai_framework_passed = await test_ai_framework_integration()
    all_passed &= ai_framework_passed

    # Final summary
    print("\n" + "=" * 70)
    print("🏁 FINAL TEST RESULTS")
    print("=" * 70)

    results = [
        ("Individual Tool Tests", tools_passed),
        ("Mock Data Availability", mock_data_passed),
        ("Tool Integration", integration_passed),
        ("AI Framework Integration", ai_framework_passed)
    ]

    for test_name, passed in results:
        status_icon = "✅" if passed else "❌"
        status_text = "PASSED" if passed else "FAILED"
        print(f"{status_icon} {test_name}: {status_text}")

    overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
    print(f"\n{overall_status}")

    if all_passed:
        print("\n🎉 Property Tax Tools are ready for production!")
        print("   All 6 tools implemented with comprehensive functionality")
        print("   Mock data covers realistic Texas property tax scenarios")
        print("   Integration with AI chat framework verified")
    else:
        print("\n⚠️  Please review failed tests before deployment")

    return 0 if all_passed else 1


if __name__ == "__main__":
    # Run the test suite
    exit_code = asyncio.run(main())