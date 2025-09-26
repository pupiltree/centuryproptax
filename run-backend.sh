#!/bin/bash

# Krsnaa Diagnostics Backend Startup Script
# Automatically sets up and runs the backend server

set -e  # Exit on any error

echo "🚀 Krsnaa Diagnostics Backend Startup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Create logs directory if it doesn't exist
print_status "Creating logs directory..."
mkdir -p logs

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and install dependencies
print_status "Installing/updating dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt
print_success "Dependencies installed"

# Check if .env file exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_warning ".env not found. Copying from .env.example..."
        cp .env.example .env
        print_warning "Please configure your .env file with proper credentials"
    else
        print_error ".env file not found and no .env.example available"
        exit 1
    fi
fi

# Verify environment setup
print_status "Verifying environment configuration..."
python -c "
import os
required_vars = ['IG_TOKEN', 'IG_USER_ID', 'VERIFY_TOKEN', 'GOOGLE_API_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print(f'❌ Missing required environment variables: {missing_vars}')
    print('   Please configure your .env file')
    exit(1)
else:
    print('✅ Environment variables configured')
"

# Initialize database and test components
print_status "Initializing database and testing components..."
python -c "
import sys, asyncio
sys.path.append('.')

async def test_components():
    try:
        # Test database connection
        from services.persistence.database import get_database_manager
        db_manager = await get_database_manager()
        health = await db_manager.health_check()
        if health:
            print('✅ Database connection successful')
        else:
            print('❌ Database connection failed')
            return False
        
        # Seed test catalog if empty
        from services.persistence.seed_data import seed_test_catalog
        await seed_test_catalog()
        print('✅ Test catalog seeded')
        
        # Test main application
        from src.main import app
        print('✅ Main application loads successfully')
        
        from agents.core.property_tax_assistant_v3 import get_property_tax_assistant
        print('✅ Property tax assistant loads successfully')

        from services.messaging.modern_integrated_webhook_handler import IntegratedWebhookHandler
        print('✅ Modern webhook handler loads successfully')
        
        from integrations.google_sheets.lead_tracker import GoogleSheetsLeadTracker
        print('✅ Google Sheets integration loads successfully')
        
        print('✅ All components verified')
        return True
    except Exception as e:
        print(f'❌ Component verification failed: {e}')
        return False

result = asyncio.run(test_components())
if not result:
    exit(1)
"

print_success "All pre-flight checks passed!"

# Get port from environment or use default
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

print_status "Starting server on http://$HOST:$PORT"
print_status "Available endpoints:"
print_status "  • GET/POST /webhook - Instagram webhook (production)"
print_status "  • GET /health - Health check"
print_status "  • GET /stats - System statistics"
print_status "  • GET /test - Test Instagram API"
print_status "  • GET / - API info"

echo ""
print_success "🎯 Backend is starting up..."
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uvicorn src.main:app --host "$HOST" --port "$PORT" --reload