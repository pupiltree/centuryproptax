"""
Assessment Report Management API endpoints for authorized personnel.
Allows property tax staff to update assessment report status and upload report files.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import json

from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from services.persistence.database import get_db_session
from services.persistence.repositories import BookingRepository, CustomerRepository

router = APIRouter(prefix="/api/assessment-reports", tags=["Assessment Report Management"])


class ReportUpdateRequest(BaseModel):
    booking_id: str
    status: str  # pending, processing, ready, delivered
    report_url: Optional[str] = None
    notes: Optional[str] = None


class ReportSearchRequest(BaseModel):
    booking_id: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


@router.get("/", response_class=HTMLResponse)
async def assessment_report_management_page():
    """Assessment report management webpage for authorized personnel."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Century Property Tax - Assessment Report Management</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
                padding: 20px 30px;
                text-align: center;
            }
            .header h1 {
                font-size: 24px;
                margin-bottom: 5px;
            }
            .header p {
                opacity: 0.9;
                font-size: 14px;
            }
            .content {
                padding: 30px;
            }
            .section {
                margin-bottom: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                border-left: 4px solid #667eea;
            }
            .section h3 {
                color: #333;
                margin-bottom: 15px;
                font-size: 18px;
            }
            .form-group {
                margin-bottom: 15px;
            }
            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #555;
            }
            .form-control {
                width: 100%;
                padding: 10px;
                border: 2px solid #e1e5e9;
                border-radius: 5px;
                font-size: 14px;
                transition: border-color 0.3s;
            }
            .form-control:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            .btn {
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: transform 0.2s, box-shadow 0.2s;
                margin-right: 10px;
                margin-bottom: 10px;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .btn-secondary {
                background: #6c757d;
            }
            .result-area {
                margin-top: 20px;
                padding: 15px;
                background: white;
                border-radius: 5px;
                border: 1px solid #dee2e6;
                min-height: 100px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                white-space: pre-wrap;
                overflow-y: auto;
                max-height: 300px;
            }
            .status-badge {
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                text-transform: uppercase;
            }
            .status-pending {
                background: #fff3cd;
                color: #856404;
            }
            .status-processing {
                background: #cce5ff;
                color: #004085;
            }
            .status-ready {
                background: #d4edda;
                color: #155724;
            }
            .status-delivered {
                background: #e2e3e5;
                color: #383d41;
            }
            .grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }
            @media (max-width: 768px) {
                .grid {
                    grid-template-columns: 1fr;
                }
                .container {
                    margin: 10px;
                }
                .content {
                    padding: 20px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏢 Century Property Tax</h1>
                <p>Assessment Report Management System - Authorized Personnel Only</p>
            </div>
            
            <div class="content">
                <div class="grid">
                    <!-- Search Assessment Reports Section -->
                    <div class="section">
                        <h3>🔍 Search Assessment Reports</h3>
                        <form id="searchForm">
                            <div class="form-group">
                                <label for="searchBookingId">Assessment ID:</label>
                                <input type="text" id="searchBookingId" class="form-control"
                                       placeholder="e.g., CPT20250811_A1">
                            </div>
                            <div class="form-group">
                                <label for="searchPhone">Phone Number:</label>
                                <input type="text" id="searchPhone" class="form-control" 
                                       placeholder="e.g., 9876543210">
                            </div>
                            <div class="form-group">
                                <label for="searchStatus">Status Filter:</label>
                                <select id="searchStatus" class="form-control">
                                    <option value="">All Statuses</option>
                                    <option value="pending">Pending</option>
                                    <option value="processing">Processing</option>
                                    <option value="ready">Ready</option>
                                    <option value="delivered">Delivered</option>
                                </select>
                            </div>
                            <button type="button" class="btn" onclick="searchReports()">
                                🔍 Search Assessment Reports
                            </button>
                        </form>
                        <div id="searchResults" class="result-area">
                            Click "Search Assessment Reports" to find assessments...
                        </div>
                    </div>
                    
                    <!-- Update Assessment Report Section -->
                    <div class="section">
                        <h3>📝 Update Assessment Report Status</h3>
                        <form id="updateForm">
                            <div class="form-group">
                                <label for="updateBookingId">Assessment ID: <span style="color: red;">*</span></label>
                                <input type="text" id="updateBookingId" class="form-control" required
                                       placeholder="e.g., CPT20250811_A1">
                            </div>
                            <div class="form-group">
                                <label for="updateStatus">New Status: <span style="color: red;">*</span></label>
                                <select id="updateStatus" class="form-control" required>
                                    <option value="">Select Status</option>
                                    <option value="pending">📝 Pending</option>
                                    <option value="processing">⚗️ Processing</option>
                                    <option value="ready">✅ Ready</option>
                                    <option value="delivered">📦 Delivered</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="reportUrl">Assessment Report URL (if ready):</label>
                                <input type="url" id="reportUrl" class="form-control"
                                       placeholder="https://reports.centuryproptax.com/download/...">
                            </div>
                            <div class="form-group">
                                <label for="updateNotes">Notes:</label>
                                <textarea id="updateNotes" class="form-control" rows="3"
                                          placeholder="Optional notes about the report status..."></textarea>
                            </div>
                            <button type="button" class="btn" onclick="updateReport()">
                                💾 Update Assessment Report
                            </button>
                            <button type="button" class="btn btn-secondary" onclick="clearForm()">
                                🗑️ Clear Form
                            </button>
                        </form>
                        <div id="updateResults" class="result-area">
                            Fill the form above and click "Update Assessment Report"...
                        </div>
                    </div>
                </div>
                
                <!-- Quick Actions -->
                <div class="section">
                    <h3>⚡ Quick Actions</h3>
                    <button class="btn" onclick="loadPendingReports()">📋 Load Pending Assessments</button>
                    <button class="btn" onclick="loadProcessingReports()">⚗️ Load Processing Assessments</button>
                    <button class="btn" onclick="loadTodaysBookings()">📅 Today's Assessments</button>
                    <button class="btn btn-secondary" onclick="clearAllResults()">🗑️ Clear All Results</button>
                </div>
            </div>
        </div>
        
        <script>
            // API Base URL
            const API_BASE = '/api/assessment-reports';
            
            // Search Reports Function
            async function searchReports() {
                const bookingId = document.getElementById('searchBookingId').value.trim();
                const phone = document.getElementById('searchPhone').value.trim();
                const status = document.getElementById('searchStatus').value;
                
                const resultsDiv = document.getElementById('searchResults');
                resultsDiv.textContent = 'Searching...';
                
                try {
                    const params = new URLSearchParams();
                    if (bookingId) params.append('booking_id', bookingId);
                    if (phone) params.append('phone', phone);
                    if (status) params.append('status', status);
                    
                    const response = await fetch(`${API_BASE}/search?${params}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        displaySearchResults(data.bookings);
                    } else {
                        resultsDiv.textContent = `Error: ${data.message}`;
                    }
                } catch (error) {
                    resultsDiv.textContent = `Network error: ${error.message}`;
                }
            }
            
            // Display Search Results
            function displaySearchResults(bookings) {
                const resultsDiv = document.getElementById('searchResults');
                
                if (!bookings || bookings.length === 0) {
                    resultsDiv.textContent = 'No assessments found matching your criteria.';
                    return;
                }

                let html = `Found ${bookings.length} assessment(s):\\n\\n`;

                bookings.forEach((booking, index) => {
                    const statusClass = `status-${booking.status || 'pending'}`;
                    const statusBadge = `<span class="${statusClass}">${booking.status || 'pending'}</span>`;
                    
                    html += `${index + 1}. Assessment ID: ${booking.booking_id}\\n`;
                    html += `   Property Owner: ${booking.customer_name}\\n`;
                    html += `   Phone: ${booking.phone}\\n`;
                    html += `   Assessment: ${booking.test_name}\\n`;
                    html += `   Status: ${booking.status || 'pending'}\\n`;
                    html += `   Date: ${new Date(booking.created_at).toLocaleDateString()}\\n`;
                    if (booking.report_url) {
                        html += `   Report: ${booking.report_url}\\n`;
                    }
                    html += `\\n`;
                });
                
                resultsDiv.innerHTML = `<pre>${html}</pre>`;
            }
            
            // Update Report Function
            async function updateReport() {
                const bookingId = document.getElementById('updateBookingId').value.trim();
                const status = document.getElementById('updateStatus').value;
                const reportUrl = document.getElementById('reportUrl').value.trim();
                const notes = document.getElementById('updateNotes').value.trim();
                
                if (!bookingId || !status) {
                    alert('Please fill in all required fields (marked with *)');
                    return;
                }
                
                const resultsDiv = document.getElementById('updateResults');
                resultsDiv.textContent = 'Updating report...';
                
                try {
                    const response = await fetch(`${API_BASE}/update`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            booking_id: bookingId,
                            status: status,
                            report_url: reportUrl || null,
                            notes: notes || null
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        resultsDiv.innerHTML = `
                            <div style="color: green; font-weight: bold;">✅ SUCCESS</div>
                            <div>Booking ID: ${data.booking_id}</div>
                            <div>Status updated to: ${data.status}</div>
                            <div>Updated at: ${new Date().toLocaleString()}</div>
                            ${data.message ? `<div>Message: ${data.message}</div>` : ''}
                        `;
                        
                        // Auto-fill search form with updated booking ID
                        document.getElementById('searchBookingId').value = bookingId;
                    } else {
                        resultsDiv.innerHTML = `
                            <div style="color: red; font-weight: bold;">❌ ERROR</div>
                            <div>${data.message}</div>
                        `;
                    }
                } catch (error) {
                    resultsDiv.innerHTML = `
                        <div style="color: red; font-weight: bold;">❌ NETWORK ERROR</div>
                        <div>${error.message}</div>
                    `;
                }
            }
            
            // Clear Form
            function clearForm() {
                document.getElementById('updateForm').reset();
                document.getElementById('updateResults').textContent = 'Form cleared. Fill the form above and click "Update Assessment Report"...';
            }
            
            // Quick Action Functions
            async function loadPendingReports() {
                document.getElementById('searchStatus').value = 'pending';
                await searchReports();
            }
            
            async function loadProcessingReports() {
                document.getElementById('searchStatus').value = 'processing';
                await searchReports();
            }
            
            async function loadTodaysBookings() {
                // This would require a date filter in the API
                document.getElementById('searchResults').textContent = 'Today\\'s assessments feature coming soon...';
            }

            function clearAllResults() {
                document.getElementById('searchResults').textContent = 'Click "Search Assessment Reports" to find assessments...';
                document.getElementById('updateResults').textContent = 'Fill the form above and click "Update Assessment Report"...';
                document.getElementById('searchForm').reset();
            }
            
            // Auto-populate update form when clicking on search results
            document.getElementById('searchResults').addEventListener('click', function(e) {
                const text = e.target.textContent;
                const assessmentIdMatch = text.match(/Assessment ID: (\\S+)/);
                if (assessmentIdMatch) {
                    document.getElementById('updateBookingId').value = assessmentIdMatch[1];
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content


@router.get("/search")
async def search_assessment_reports(
    booking_id: Optional[str] = None,
    phone: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """Search for assessment bookings/reports with various filters."""
    try:
        async with get_db_session() as session:
            booking_repo = BookingRepository(session)
            customer_repo = CustomerRepository(session)
            
            bookings = []
            
            if booking_id:
                # Search by specific assessment ID
                booking = await booking_repo.get_by_booking_id(booking_id)
                if booking:
                    customer = await customer_repo.get_by_id(booking.customer_id)
                    bookings = [booking]

            elif phone:
                # Search by phone number
                clean_phone = phone.replace("+91", "").replace("-", "").replace(" ", "")
                customer = await customer_repo.get_by_phone(clean_phone)
                if customer:
                    bookings = await booking_repo.get_customer_bookings(customer.id, limit=20)

            else:
                # Get all assessment bookings with optional status filter
                bookings = await booking_repo.get_all_bookings(limit=50)
            
            # Filter by status if provided
            if status:
                bookings = [b for b in bookings if b.status == status]
            
            # Format response
            formatted_bookings = []
            for booking in bookings:
                customer = await customer_repo.get_by_id(booking.customer_id)
                
                formatted_bookings.append({
                    "booking_id": booking.booking_id,
                    "customer_name": customer.name,
                    "phone": customer.phone,
                    "test_name": f"Assessment {booking.test_id}",  # Would need to join with assessment catalog
                    "status": booking.status,
                    "created_at": booking.created_at.isoformat(),
                    "report_url": booking.notes if booking.notes and "http" in booking.notes else None,
                    "total_amount": float(booking.total_amount) if booking.total_amount else 0
                })
            
            return {
                "success": True,
                "bookings": formatted_bookings,
                "total_found": len(formatted_bookings),
                "message": f"Found {len(formatted_bookings)} assessment(s)"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Search error: {str(e)}",
            "bookings": []
        }


@router.post("/update")
async def update_assessment_report_status(request: ReportUpdateRequest) -> Dict[str, Any]:
    """Update assessment report status for a specific booking."""
    try:
        async with get_db_session() as session:
            booking_repo = BookingRepository(session)
            
            # Find the assessment booking
            booking = await booking_repo.get_by_booking_id(request.booking_id)

            if not booking:
                return {
                    "success": False,
                    "message": f"Assessment '{request.booking_id}' not found"
                }
            
            # Update booking status
            await booking_repo.update_booking_status(
                booking.id,
                status=request.status,
                notes=request.notes
            )
            
            # If assessment report URL provided, store it in notes (simple implementation)
            if request.report_url:
                notes_data = {
                    "report_url": request.report_url,
                    "updated_at": datetime.now().isoformat(),
                    "notes": request.notes
                }
                await booking_repo.update_booking_status(
                    booking.id,
                    notes=json.dumps(notes_data)
                )
            
            return {
                "success": True,
                "booking_id": request.booking_id,
                "status": request.status,
                "message": f"Assessment report status updated to '{request.status}'",
                "updated_at": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Update error: {str(e)}"
        }