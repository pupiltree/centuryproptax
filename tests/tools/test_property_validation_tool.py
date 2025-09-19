"""
Unit Tests for Property Validation Tool

Comprehensive tests for property validation functionality including
address validation, parcel ID lookup, and error handling.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime

from agents.tools.property_validation_tool import (
    property_validation_tool,
    detect_search_type,
    normalize_address,
    format_property_response,
    validate_multiple_properties,
    get_supported_counties,
    get_property_type_info
)

class TestPropertyValidationTool:
    """Test class for property validation tool"""

    @pytest.mark.asyncio
    async def test_property_validation_success_address(self):
        """Test successful property validation by address"""
        result = await property_validation_tool(
            search_query="123 Main St, Houston, TX",
            search_type="address"
        )

        assert result["success"] is True
        if result["property_found"]:
            assert "property_data" in result
            assert "formatted_address" in result["property_data"]
            assert "parcel_id" in result["property_data"]
            assert "current_assessed_value" in result["property_data"]

        assert "validation_details" in result
        assert "suggestions" in result

        print(f"✅ Address validation test: Property found = {result['property_found']}")
        if result["property_found"]:
            print(f"   Address: {result['property_data']['formatted_address']}")
            print(f"   Value: ${result['property_data']['current_assessed_value']:,}")

    @pytest.mark.asyncio
    async def test_property_validation_success_parcel_id(self):
        """Test successful property validation by parcel ID"""
        # Use a format that might exist in our mock data
        result = await property_validation_tool(
            search_query="HAR-R1-123-4567-890",
            search_type="parcel_id"
        )

        assert result["success"] is True
        assert "validation_details" in result
        assert result["validation_details"]["search_type_detected"] == "parcel_id"

        print(f"✅ Parcel ID validation test: Property found = {result['property_found']}")
        if result["property_found"]:
            print(f"   Parcel: {result['property_data']['parcel_id']}")

    @pytest.mark.asyncio
    async def test_property_validation_auto_detect(self):
        """Test automatic search type detection"""
        # Test address detection
        address_result = await property_validation_tool(
            search_query="456 Oak Street, Dallas, TX",
            search_type="auto"
        )

        assert address_result["success"] is True
        assert address_result["validation_details"]["search_type_detected"] == "address"

        # Test parcel ID detection
        parcel_result = await property_validation_tool(
            search_query="DAL-R2-456-7890-123",
            search_type="auto"
        )

        assert parcel_result["success"] is True
        assert parcel_result["validation_details"]["search_type_detected"] == "parcel_id"

        print("✅ Auto-detection test passed")
        print(f"   Address query detected as: {address_result['validation_details']['search_type_detected']}")
        print(f"   Parcel query detected as: {parcel_result['validation_details']['search_type_detected']}")

    @pytest.mark.asyncio
    async def test_property_validation_not_found(self):
        """Test property validation when property is not found"""
        result = await property_validation_tool(
            search_query="999999 Nonexistent Street, Nowhere, TX",
            search_type="address"
        )

        assert result["success"] is True
        assert result["property_found"] is False
        assert len(result["suggestions"]) > 0

        print("✅ Property not found test passed")
        print(f"   Suggestions provided: {len(result['suggestions'])}")

    @pytest.mark.asyncio
    async def test_property_validation_criteria_search(self):
        """Test criteria-based property search"""
        result = await property_validation_tool(
            search_query="commercial property",
            search_type="criteria",
            county="harris",
            property_type="commercial"
        )

        assert result["success"] is True
        print(f"✅ Criteria search test: Property found = {result['property_found']}")

    @pytest.mark.asyncio
    async def test_property_validation_error_handling(self):
        """Test error handling with invalid inputs"""
        result = await property_validation_tool(
            search_query="",  # Empty query
            search_type="address"
        )

        assert result["success"] is True  # Tool handles gracefully
        assert result["property_found"] is False

        print("✅ Error handling test passed")

    def test_detect_search_type(self):
        """Test search type detection function"""
        # Test address detection
        assert detect_search_type("123 Main Street") == "address"
        assert detect_search_type("456 Oak Ave, Dallas") == "address"

        # Test parcel ID detection
        assert detect_search_type("HAR-R1-123-4567-890") == "parcel_id"
        assert detect_search_type("DAL123456789") == "parcel_id"

        # Test criteria detection
        assert detect_search_type("commercial property") == "criteria"
        assert detect_search_type("residential") == "criteria"

        print("✅ Search type detection tests passed")

    def test_normalize_address(self):
        """Test address normalization function"""
        # Test basic normalization
        normalized = normalize_address("123 Main Street, Houston, TX")
        assert "main st" in normalized.lower()

        # Test abbreviation replacement
        normalized = normalize_address("456 Oak Avenue")
        assert "ave" in normalized

        # Test direction normalization
        normalized = normalize_address("North Main Street")
        assert "n main" in normalized

        print("✅ Address normalization tests passed")

    def test_format_property_response(self):
        """Test property response formatting"""
        # Create sample property data
        sample_property = {
            "parcel_id": "TEST-R1-123-4567-890",
            "address": {
                "street_number": "123",
                "street_name": "Main St",
                "city": "Houston",
                "state": "TX",
                "zip_code": "77001"
            },
            "property_type": "residential",
            "county": "Harris County",
            "county_code": "harris",
            "assessed_value": 300000,
            "exemptions": {"homestead": True},
            "owner": {"owner_occupied": True},
            "characteristics": {"square_feet": 2000},
            "assessment_history": [
                {"tax_year": 2022, "assessed_value": 250000},
                {"tax_year": 2023, "assessed_value": 275000},
                {"tax_year": 2024, "assessed_value": 300000}
            ],
            "last_updated": datetime.now().isoformat(),
            "status": "active"
        }

        formatted = format_property_response(sample_property)

        assert "formatted_address" in formatted
        assert "123 Main St, Houston, TX 77001" in formatted["formatted_address"]
        assert formatted["current_assessed_value"] == 300000
        assert "annual_tax_estimated" in formatted
        assert len(formatted["assessment_history"]) <= 3  # Last 3 years

        print("✅ Property response formatting test passed")

    @pytest.mark.asyncio
    async def test_validate_multiple_properties(self):
        """Test bulk property validation"""
        properties = [
            "123 Main St, Houston, TX",
            "HAR-R1-123-4567-890",
            "456 Oak Ave, Dallas, TX"
        ]

        results = await validate_multiple_properties(properties)

        assert len(results) == len(properties)
        for result in results:
            assert "success" in result
            assert "property_found" in result

        print(f"✅ Bulk validation test: Processed {len(results)} properties")

    def test_get_supported_counties(self):
        """Test getting supported counties list"""
        counties = get_supported_counties()

        assert len(counties) > 0
        assert all("county_code" in county for county in counties)
        assert all("county_name" in county for county in counties)
        assert all("tax_rate" in county for county in counties)

        print(f"✅ Supported counties test: {len(counties)} counties available")
        for county in counties[:3]:  # Show first 3
            print(f"   {county['county_name']}: {county['tax_rate']} rate")

    def test_get_property_type_info(self):
        """Test getting property type information"""
        property_types = get_property_type_info()

        assert len(property_types) > 0
        assert all("property_type" in pt for pt in property_types)
        assert all("description" in pt for pt in property_types)
        assert all("typical_value_range" in pt for pt in property_types)

        print(f"✅ Property type info test: {len(property_types)} types available")
        for pt in property_types[:2]:  # Show first 2
            print(f"   {pt['property_type']}: {pt['description']}")

class TestPropertyValidationIntegration:
    """Integration tests for property validation"""

    @pytest.mark.asyncio
    async def test_end_to_end_property_lookup(self):
        """Test complete property lookup workflow"""
        # Step 1: Search for property
        search_result = await property_validation_tool(
            search_query="123 Main Street, Houston, TX",
            search_type="auto"
        )

        print("🔍 End-to-end test started")
        print(f"   Search successful: {search_result['success']}")
        print(f"   Property found: {search_result['property_found']}")

        if search_result["property_found"]:
            property_data = search_result["property_data"]

            # Step 2: Verify all required fields are present
            required_fields = [
                "parcel_id", "formatted_address", "current_assessed_value",
                "property_type", "county"
            ]

            for field in required_fields:
                assert field in property_data, f"Missing required field: {field}"
                print(f"   ✓ {field}: {property_data[field]}")

            # Step 3: Verify data types and ranges
            assert isinstance(property_data["current_assessed_value"], int)
            assert property_data["current_assessed_value"] > 0
            assert property_data["county"] in ["Harris County", "Dallas County", "Travis County", "Tarrant County", "Bexar County", "Collin County"]

            print(f"   ✓ Assessment value: ${property_data['current_assessed_value']:,}")
            print(f"   ✓ Annual tax estimate: ${property_data['annual_tax_estimated']:,}")

        print("✅ End-to-end test completed successfully")

    @pytest.mark.asyncio
    async def test_performance_multiple_searches(self):
        """Test performance with multiple concurrent searches"""
        import time

        search_queries = [
            "123 Main St, Houston, TX",
            "456 Oak Ave, Dallas, TX",
            "789 Pine Rd, Austin, TX",
            "321 Elm St, Fort Worth, TX",
            "654 Cedar Ln, San Antonio, TX"
        ]

        start_time = time.time()

        # Run searches concurrently
        tasks = [
            property_validation_tool(query, "auto")
            for query in search_queries
        ]

        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        assert len(results) == len(search_queries)
        for result in results:
            assert result["success"] is True

        print(f"✅ Performance test: {len(search_queries)} searches in {total_time:.2f} seconds")
        print(f"   Average time per search: {total_time/len(search_queries):.3f} seconds")

if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v", "-s"])