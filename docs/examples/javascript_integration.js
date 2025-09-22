/**
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
