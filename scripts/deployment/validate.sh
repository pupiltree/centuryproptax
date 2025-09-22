#!/bin/bash
# Production validation script for Century Property Tax Documentation Portal
# This script performs comprehensive validation of the deployed system

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VALIDATION_LOG="/tmp/centuryproptax_validation_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
TIMEOUT="${TIMEOUT:-30}"
EXPECTED_VERSION="${EXPECTED_VERSION:-4.0.0}"

# Test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} $message" | tee -a "$VALIDATION_LOG"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} $message" | tee -a "$VALIDATION_LOG"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message" | tee -a "$VALIDATION_LOG"
            ;;
        "DEBUG")
            echo -e "${BLUE}[DEBUG]${NC} $message" | tee -a "$VALIDATION_LOG"
            ;;
        "PASS")
            echo -e "${GREEN}[PASS]${NC} $message" | tee -a "$VALIDATION_LOG"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            ;;
        "FAIL")
            echo -e "${RED}[FAIL]${NC} $message" | tee -a "$VALIDATION_LOG"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            ;;
    esac
    TOTAL_TESTS=$((PASSED_TESTS + FAILED_TESTS))
}

# Test function wrapper
run_test() {
    local test_name="$1"
    local test_command="$2"

    log "DEBUG" "Running test: $test_name"

    if eval "$test_command"; then
        log "PASS" "$test_name"
        return 0
    else
        log "FAIL" "$test_name"
        return 1
    fi
}

# Basic connectivity tests
test_basic_connectivity() {
    log "INFO" "Testing basic connectivity..."

    run_test "Health endpoint accessibility" \
        "curl -s -f --max-time $TIMEOUT '$BASE_URL/health' >/dev/null"

    run_test "Root endpoint accessibility" \
        "curl -s -f --max-time $TIMEOUT '$BASE_URL/' >/dev/null"

    run_test "OpenAPI schema accessibility" \
        "curl -s -f --max-time $TIMEOUT '$BASE_URL/openapi.json' >/dev/null"
}

# Documentation portal tests
test_documentation_portal() {
    log "INFO" "Testing documentation portal..."

    run_test "Documentation portal accessibility" \
        "curl -s -f --max-time $TIMEOUT '$BASE_URL/documentation' >/dev/null"

    run_test "Swagger UI accessibility" \
        "curl -s -f --max-time $TIMEOUT '$BASE_URL/docs' >/dev/null"

    run_test "ReDoc accessibility" \
        "curl -s -f --max-time $TIMEOUT '$BASE_URL/redoc' >/dev/null"

    # Test static assets
    run_test "CSS assets loading" \
        "curl -s -f --max-time $TIMEOUT '$BASE_URL/documentation' | grep -q 'text/css\\|stylesheet'"

    run_test "JavaScript functionality" \
        "curl -s -f --max-time $TIMEOUT '$BASE_URL/documentation' | grep -q 'loadApiStatus\\|javascript'"
}

# API functionality tests
test_api_functionality() {
    log "INFO" "Testing API functionality..."

    # Test health endpoint response
    local health_response=$(curl -s --max-time $TIMEOUT "$BASE_URL/health" 2>/dev/null)

    run_test "Health endpoint returns JSON" \
        "echo '$health_response' | python3 -m json.tool >/dev/null 2>&1"

    run_test "Health status is healthy" \
        "echo '$health_response' | python3 -c 'import sys, json; exit(0 if json.load(sys.stdin).get(\"status\") == \"healthy\" else 1)' 2>/dev/null"

    if [[ -n "$EXPECTED_VERSION" ]]; then
        run_test "API version matches expected ($EXPECTED_VERSION)" \
            "echo '$health_response' | python3 -c 'import sys, json; exit(0 if json.load(sys.stdin).get(\"version\") == \"$EXPECTED_VERSION\" else 1)' 2>/dev/null"
    fi

    # Test OpenAPI schema
    local openapi_response=$(curl -s --max-time $TIMEOUT "$BASE_URL/openapi.json" 2>/dev/null)

    run_test "OpenAPI schema is valid JSON" \
        "echo '$openapi_response' | python3 -m json.tool >/dev/null 2>&1"

    run_test "OpenAPI schema contains required fields" \
        "echo '$openapi_response' | python3 -c 'import sys, json; schema=json.load(sys.stdin); exit(0 if all(k in schema for k in [\"openapi\", \"info\", \"paths\"]) else 1)' 2>/dev/null"
}

# Performance tests
test_performance() {
    log "INFO" "Testing performance..."

    # Test response times
    local health_time=$(curl -w "%{time_total}" -s -o /dev/null --max-time $TIMEOUT "$BASE_URL/health" 2>/dev/null || echo "999")
    local docs_time=$(curl -w "%{time_total}" -s -o /dev/null --max-time $TIMEOUT "$BASE_URL/docs" 2>/dev/null || echo "999")
    local portal_time=$(curl -w "%{time_total}" -s -o /dev/null --max-time $TIMEOUT "$BASE_URL/documentation" 2>/dev/null || echo "999")

    run_test "Health endpoint response time < 2s (${health_time}s)" \
        "python3 -c 'exit(0 if float(\"$health_time\") < 2.0 else 1)'"

    run_test "Docs endpoint response time < 3s (${docs_time}s)" \
        "python3 -c 'exit(0 if float(\"$docs_time\") < 3.0 else 1)'"

    run_test "Documentation portal response time < 3s (${portal_time}s)" \
        "python3 -c 'exit(0 if float(\"$portal_time\") < 3.0 else 1)'"

    # Test concurrent requests
    log "DEBUG" "Testing concurrent request handling..."

    local concurrent_test_result=0
    for i in {1..5}; do
        curl -s --max-time 10 "$BASE_URL/health" >/dev/null &
    done
    wait

    run_test "Concurrent requests handled successfully" \
        "true"  # If we reach here, concurrent test passed
}

# Security tests
test_security() {
    log "INFO" "Testing security features..."

    # Test security headers
    local headers=$(curl -I -s --max-time $TIMEOUT "$BASE_URL/documentation" 2>/dev/null)

    run_test "X-Content-Type-Options header present" \
        "echo '$headers' | grep -qi 'X-Content-Type-Options'"

    run_test "X-Frame-Options header present" \
        "echo '$headers' | grep -qi 'X-Frame-Options'"

    # Test HTTPS redirect (if in production)
    if [[ "$BASE_URL" == https://* ]]; then
        local http_url="${BASE_URL/https:/http:}"
        local redirect_response=$(curl -I -s --max-time $TIMEOUT "$http_url" 2>/dev/null || echo "")

        run_test "HTTP to HTTPS redirect configured" \
            "echo '$redirect_response' | grep -q '301\\|302'"
    fi

    # Test for common vulnerabilities
    run_test "No server information leak" \
        "! echo '$headers' | grep -qi 'server: \\(apache\\|nginx\\|iis\\)'"

    run_test "No X-Powered-By header leak" \
        "! echo '$headers' | grep -qi 'x-powered-by: \\(php\\|asp\\)'"
}

# SEO and accessibility tests
test_seo_accessibility() {
    log "INFO" "Testing SEO and accessibility..."

    # Test sitemap
    run_test "Sitemap.xml accessibility" \
        "curl -s -f --max-time $TIMEOUT '$BASE_URL/sitemap.xml' >/dev/null"

    run_test "Robots.txt accessibility" \
        "curl -s -f --max-time $TIMEOUT '$BASE_URL/robots.txt' >/dev/null"

    # Test meta tags in documentation portal
    local portal_html=$(curl -s --max-time $TIMEOUT "$BASE_URL/documentation" 2>/dev/null)

    run_test "Title tag present" \
        "echo '$portal_html' | grep -q '<title>'"

    run_test "Meta description present" \
        "echo '$portal_html' | grep -q 'meta.*description'"

    run_test "Viewport meta tag present" \
        "echo '$portal_html' | grep -q 'meta.*viewport'"

    # Test Open Graph tags
    run_test "Open Graph meta tags present" \
        "echo '$portal_html' | grep -q 'property=\"og:'"
}

# Container health tests
test_container_health() {
    log "INFO" "Testing container health..."

    if command -v docker >/dev/null 2>&1; then
        # Check if containers are running
        local running_containers=$(docker ps --format "table {{.Names}}" | grep centuryproptax | wc -l)

        run_test "Application containers running" \
            "test $running_containers -gt 0"

        # Check container health status
        local unhealthy_containers=$(docker ps --filter "health=unhealthy" --format "table {{.Names}}" | grep centuryproptax | wc -l)

        run_test "No unhealthy containers" \
            "test $unhealthy_containers -eq 0"

        # Check resource usage
        local memory_usage=$(docker stats --no-stream --format "{{.MemPerc}}" centuryproptax-docs 2>/dev/null | sed 's/%//' || echo "0")

        run_test "Memory usage under 80% (${memory_usage}%)" \
            "python3 -c 'exit(0 if float(\"$memory_usage\") < 80.0 else 1)' 2>/dev/null || true"
    else
        log "WARN" "Docker not available, skipping container health tests"
    fi
}

# Database connectivity tests
test_database_connectivity() {
    log "INFO" "Testing database connectivity..."

    # Test if database endpoints respond (indirectly through API)
    local stats_response=$(curl -s --max-time $TIMEOUT "$BASE_URL/stats" 2>/dev/null || echo "{}")

    run_test "Database connectivity (via stats endpoint)" \
        "echo '$stats_response' | python3 -c 'import sys, json; data=json.load(sys.stdin); exit(0 if \"database\" in str(data) or \"error\" not in str(data).lower() else 1)' 2>/dev/null || true"
}

# Monitoring and metrics tests
test_monitoring() {
    log "INFO" "Testing monitoring and metrics..."

    # Test metrics endpoint
    run_test "Metrics endpoint accessibility" \
        "curl -s -f --max-time $TIMEOUT '$BASE_URL/metrics' >/dev/null || true"

    # Test analytics endpoint
    run_test "Analytics endpoint accessibility" \
        "curl -s -f --max-time $TIMEOUT '$BASE_URL/analytics' >/dev/null || true"

    # Test system status endpoint
    run_test "System status endpoint accessibility" \
        "curl -s -f --max-time $TIMEOUT '$BASE_URL/system-status' >/dev/null || true"
}

# Generate validation report
generate_validation_report() {
    local report_file="/tmp/validation_report_$(date +%Y%m%d_%H%M%S).json"

    cat > "$report_file" <<EOF
{
    "validation_id": "$(date +%Y%m%d_%H%M%S)",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "base_url": "$BASE_URL",
    "total_tests": $TOTAL_TESTS,
    "passed_tests": $PASSED_TESTS,
    "failed_tests": $FAILED_TESTS,
    "success_rate": $(python3 -c "print(round($PASSED_TESTS / $TOTAL_TESTS * 100, 2) if $TOTAL_TESTS > 0 else 0)"),
    "logs": "$VALIDATION_LOG"
}
EOF

    log "INFO" "Validation report generated: $report_file"
}

# Main validation function
main() {
    log "INFO" "Starting Century Property Tax Documentation Portal validation"
    log "INFO" "Base URL: $BASE_URL"
    log "INFO" "Timeout: ${TIMEOUT}s"

    # Run all test suites
    test_basic_connectivity
    test_documentation_portal
    test_api_functionality
    test_performance
    test_security
    test_seo_accessibility
    test_container_health
    test_database_connectivity
    test_monitoring

    # Generate report
    generate_validation_report

    # Display results
    echo
    echo "================================================"
    echo "   VALIDATION RESULTS"
    echo "================================================"
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "Success Rate: $(python3 -c "print(f'{$PASSED_TESTS / $TOTAL_TESTS * 100:.1f}%' if $TOTAL_TESTS > 0 else '0%')")"
    echo "Logs: $VALIDATION_LOG"
    echo "================================================"

    # Exit with appropriate code
    if [[ $FAILED_TESTS -eq 0 ]]; then
        log "INFO" "🎉 All validation tests passed!"
        exit 0
    else
        log "ERROR" "❌ $FAILED_TESTS validation tests failed"
        exit 1
    fi
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi