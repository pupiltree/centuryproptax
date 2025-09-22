#!/usr/bin/env python3
"""
OpenAPI Documentation Generator for Century Property Tax API.

This script automatically extracts the OpenAPI schema from the FastAPI application
and generates comprehensive documentation including:
- OpenAPI JSON schema
- Markdown documentation
- Integration examples
- Developer guides

Usage:
    python docs/scripts/generate_openapi_docs.py
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def extract_openapi_schema() -> Dict[str, Any]:
    """Extract OpenAPI schema from the FastAPI application."""
    try:
        from src.main import app

        # Generate OpenAPI schema
        openapi_schema = app.openapi()

        return openapi_schema
    except Exception as e:
        print(f"Error extracting OpenAPI schema: {e}")
        return {}

def save_openapi_json(schema: Dict[str, Any], output_path: Path) -> None:
    """Save OpenAPI schema as JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        print(f"✅ OpenAPI schema saved to: {output_path}")
    except Exception as e:
        print(f"❌ Error saving OpenAPI JSON: {e}")

def generate_markdown_docs(schema: Dict[str, Any], output_dir: Path) -> None:
    """Generate markdown documentation from OpenAPI schema."""
    try:
        # Create API reference markdown
        api_ref_content = generate_api_reference_md(schema)
        api_ref_path = output_dir / "api-reference.md"

        with open(api_ref_path, 'w', encoding='utf-8') as f:
            f.write(api_ref_content)
        print(f"✅ API reference saved to: {api_ref_path}")

        # Create endpoint summary
        endpoint_summary = generate_endpoint_summary_md(schema)
        summary_path = output_dir / "endpoints-summary.md"

        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(endpoint_summary)
        print(f"✅ Endpoint summary saved to: {summary_path}")

    except Exception as e:
        print(f"❌ Error generating markdown docs: {e}")

def generate_api_reference_md(schema: Dict[str, Any]) -> str:
    """Generate comprehensive API reference markdown."""
    info = schema.get('info', {})
    paths = schema.get('paths', {})
    components = schema.get('components', {})

    content = f"""# {info.get('title', 'API')} Reference

{info.get('description', '')}

**Version:** {info.get('version', '1.0.0')}

## Overview

This API provides comprehensive functionality for Century Property Tax's intelligent assistant system.

## Base URLs

"""

    # Add servers information
    servers = schema.get('servers', [])
    for server in servers:
        content += f"- **{server.get('description', 'Server')}**: `{server.get('url', '')}`\n"

    content += "\n## Authentication\n\n"
    content += "This API uses webhook verification tokens for WhatsApp integration and signature verification for security.\n\n"

    # Add endpoints documentation
    content += "## Endpoints\n\n"

    for path, methods in paths.items():
        content += f"### {path}\n\n"

        for method, details in methods.items():
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                content += f"#### {method.upper()} {path}\n\n"
                content += f"**Summary:** {details.get('summary', 'No summary available')}\n\n"

                description = details.get('description', '')
                if description:
                    content += f"{description}\n\n"

                # Parameters
                parameters = details.get('parameters', [])
                if parameters:
                    content += "**Parameters:**\n\n"
                    for param in parameters:
                        param_name = param.get('name', '')
                        param_type = param.get('schema', {}).get('type', 'string')
                        param_desc = param.get('description', '')
                        param_required = '(required)' if param.get('required', False) else '(optional)'
                        content += f"- `{param_name}` {param_required}: {param_type} - {param_desc}\n"
                    content += "\n"

                # Responses
                responses = details.get('responses', {})
                if responses:
                    content += "**Responses:**\n\n"
                    for status_code, response_info in responses.items():
                        description = response_info.get('description', '')
                        content += f"- `{status_code}`: {description}\n"
                    content += "\n"

                content += "---\n\n"

    # Add schemas documentation
    schemas = components.get('schemas', {})
    if schemas:
        content += "## Data Models\n\n"
        for schema_name, schema_details in schemas.items():
            content += f"### {schema_name}\n\n"
            schema_description = schema_details.get('description', '')
            if schema_description:
                content += f"{schema_description}\n\n"

            properties = schema_details.get('properties', {})
            if properties:
                content += "**Properties:**\n\n"
                for prop_name, prop_details in properties.items():
                    prop_type = prop_details.get('type', 'unknown')
                    prop_desc = prop_details.get('description', '')
                    content += f"- `{prop_name}`: {prop_type} - {prop_desc}\n"
                content += "\n"

    return content

def generate_endpoint_summary_md(schema: Dict[str, Any]) -> str:
    """Generate endpoint summary table."""
    paths = schema.get('paths', {})

    content = """# API Endpoints Summary

| Method | Endpoint | Summary | Tags |
|--------|----------|---------|------|
"""

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                summary = details.get('summary', 'No summary')
                tags = ', '.join(details.get('tags', []))
                content += f"| {method.upper()} | `{path}` | {summary} | {tags} |\n"

    content += "\n## Tags Description\n\n"
    content += "- **WhatsApp Webhooks**: Core webhook endpoints for WhatsApp message processing\n"
    content += "- **Assessment Report Management**: Administrative endpoints for report status management\n"
    content += "- **Health & Monitoring**: System health and performance monitoring endpoints\n"

    return content

def generate_integration_examples() -> None:
    """Generate integration examples using mock data."""
    examples_dir = Path("docs/examples")
    examples_dir.mkdir(exist_ok=True)

    # Python integration example
    python_example = '''"""
Python Integration Example for Century Property Tax API

This example demonstrates how to integrate with the Century Property Tax API
using Python and the requests library.
"""

import requests
import json
from typing import Dict, Any

class CenturyPropertyTaxAPI:
    """Century Property Tax API client."""

    def __init__(self, base_url: str = "https://api.centuryproptax.com"):
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def search_assessments(self, booking_id: str = None, phone: str = None,
                          status: str = None) -> Dict[str, Any]:
        """Search for assessment reports."""
        params = {}
        if booking_id:
            params['booking_id'] = booking_id
        if phone:
            params['phone'] = phone
        if status:
            params['status'] = status

        response = self.session.get(
            f"{self.base_url}/api/assessment-reports/search",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def update_assessment_status(self, booking_id: str, status: str,
                               report_url: str = None, notes: str = None) -> Dict[str, Any]:
        """Update assessment report status."""
        data = {
            "booking_id": booking_id,
            "status": status
        }
        if report_url:
            data["report_url"] = report_url
        if notes:
            data["notes"] = notes

        response = self.session.post(
            f"{self.base_url}/api/assessment-reports/update",
            json=data
        )
        response.raise_for_status()
        return response.json()

# Example usage
if __name__ == "__main__":
    api = CenturyPropertyTaxAPI()

    # Check API health
    health = api.health_check()
    print(f"API Status: {health.get('status')}")

    # Search for assessments
    assessments = api.search_assessments(status="pending")
    print(f"Found {len(assessments.get('bookings', []))} pending assessments")

    # Update assessment status (example)
    # result = api.update_assessment_status(
    #     booking_id="CPT20250811_A1",
    #     status="ready",
    #     report_url="https://reports.example.com/report.pdf",
    #     notes="Assessment complete"
    # )
    # print(f"Update result: {result.get('message')}")
'''

    with open(examples_dir / "python_integration.py", 'w') as f:
        f.write(python_example)

    # JavaScript example
    js_example = '''/**
 * JavaScript Integration Example for Century Property Tax API
 *
 * This example demonstrates how to integrate with the API using JavaScript
 * and the fetch API or axios library.
 */

class CenturyPropertyTaxAPI {
    constructor(baseUrl = 'https://api.centuryproptax.com') {
        this.baseUrl = baseUrl;
    }

    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/health`);
        if (!response.ok) {
            throw new Error(`Health check failed: ${response.statusText}`);
        }
        return await response.json();
    }

    async searchAssessments({ bookingId, phone, status } = {}) {
        const params = new URLSearchParams();
        if (bookingId) params.append('booking_id', bookingId);
        if (phone) params.append('phone', phone);
        if (status) params.append('status', status);

        const response = await fetch(
            `${this.baseUrl}/api/assessment-reports/search?${params}`
        );
        if (!response.ok) {
            throw new Error(`Search failed: ${response.statusText}`);
        }
        return await response.json();
    }

    async updateAssessmentStatus(bookingId, status, { reportUrl, notes } = {}) {
        const data = { booking_id: bookingId, status };
        if (reportUrl) data.report_url = reportUrl;
        if (notes) data.notes = notes;

        const response = await fetch(
            `${this.baseUrl}/api/assessment-reports/update`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            }
        );
        if (!response.ok) {
            throw new Error(`Update failed: ${response.statusText}`);
        }
        return await response.json();
    }
}

// Example usage
async function example() {
    const api = new CenturyPropertyTaxAPI();

    try {
        // Check API health
        const health = await api.healthCheck();
        console.log(`API Status: ${health.status}`);

        // Search for pending assessments
        const assessments = await api.searchAssessments({ status: 'pending' });
        console.log(`Found ${assessments.bookings?.length || 0} pending assessments`);

        // Update assessment status (example)
        // const result = await api.updateAssessmentStatus(
        //     'CPT20250811_A1',
        //     'ready',
        //     {
        //         reportUrl: 'https://reports.example.com/report.pdf',
        //         notes: 'Assessment complete'
        //     }
        // );
        // console.log(`Update result: ${result.message}`);

    } catch (error) {
        console.error('API Error:', error.message);
    }
}

// Run example
example();
'''

    with open(examples_dir / "javascript_integration.js", 'w') as f:
        f.write(js_example)

    print("✅ Integration examples generated")

def main():
    """Main documentation generation function."""
    print("🚀 Generating Century Property Tax API Documentation...")

    # Create output directories
    docs_dir = Path("docs")
    static_dir = docs_dir / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    # Extract OpenAPI schema
    print("📥 Extracting OpenAPI schema...")
    schema = extract_openapi_schema()

    if not schema:
        print("❌ Failed to extract OpenAPI schema")
        return 1

    # Save OpenAPI JSON
    openapi_json_path = static_dir / "openapi.json"
    save_openapi_json(schema, openapi_json_path)

    # Generate markdown documentation
    print("📝 Generating markdown documentation...")
    generate_markdown_docs(schema, static_dir)

    # Generate integration examples
    print("🔧 Generating integration examples...")
    generate_integration_examples()

    print("✅ Documentation generation complete!")
    print(f"📁 Output directory: {static_dir}")
    print("📚 Available files:")
    print("  - openapi.json: OpenAPI schema")
    print("  - api-reference.md: Complete API reference")
    print("  - endpoints-summary.md: Endpoint summary table")
    print("  - examples/: Integration examples")

    return 0

if __name__ == "__main__":
    exit(main())