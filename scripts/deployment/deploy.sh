#!/bin/bash
# Production deployment script for Century Property Tax Documentation Portal
# This script handles the complete deployment process with validation and rollback capabilities

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOYMENT_LOG="/tmp/centuryproptax_deployment_$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="/tmp/deployment_backup_$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Deployment configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.production.yml"
ENV_FILE="${PROJECT_ROOT}/.env.production"
HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-http://localhost:8000/health}"
DEPLOYMENT_TIMEOUT="${DEPLOYMENT_TIMEOUT:-300}"
ROLLBACK_ENABLED="${ROLLBACK_ENABLED:-true}"

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} $message" | tee -a "$DEPLOYMENT_LOG"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} $message" | tee -a "$DEPLOYMENT_LOG"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message" | tee -a "$DEPLOYMENT_LOG"
            ;;
        "DEBUG")
            echo -e "${BLUE}[DEBUG]${NC} $message" | tee -a "$DEPLOYMENT_LOG"
            ;;
    esac
}

# Error handling
handle_error() {
    local exit_code=$?
    log "ERROR" "Deployment failed with exit code $exit_code"

    if [[ "$ROLLBACK_ENABLED" == "true" ]]; then
        log "INFO" "Starting automatic rollback..."
        rollback_deployment
    fi

    log "ERROR" "Deployment failed. Check logs at: $DEPLOYMENT_LOG"
    exit $exit_code
}

# Set up error handling
trap handle_error ERR

# Pre-deployment validation
validate_prerequisites() {
    log "INFO" "Validating deployment prerequisites..."

    # Check if running as root or with docker permissions
    if ! docker ps >/dev/null 2>&1; then
        log "ERROR" "Docker not accessible. Check permissions or Docker installation."
        exit 1
    fi

    # Check if docker-compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        log "ERROR" "docker-compose not found. Please install docker-compose."
        exit 1
    fi

    # Check if required files exist
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        log "ERROR" "Docker compose file not found: $DOCKER_COMPOSE_FILE"
        exit 1
    fi

    if [[ ! -f "$ENV_FILE" ]]; then
        log "WARN" "Environment file not found: $ENV_FILE"
        log "INFO" "Creating environment file from example..."
        cp "$PROJECT_ROOT/.env.production.example" "$ENV_FILE"
        log "WARN" "Please update $ENV_FILE with your actual configuration values."
        exit 1
    fi

    # Check available disk space (minimum 2GB)
    local available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 2097152 ]]; then  # 2GB in KB
        log "ERROR" "Insufficient disk space. At least 2GB required."
        exit 1
    fi

    log "INFO" "Prerequisites validation passed"
}

# Create backup of current deployment
create_deployment_backup() {
    log "INFO" "Creating deployment backup..."

    mkdir -p "$BACKUP_DIR"

    # Backup docker volumes
    if docker volume ls -q | grep -q centuryproptax; then
        log "INFO" "Backing up Docker volumes..."
        docker run --rm -v centuryproptax_postgres-data:/source -v "$BACKUP_DIR":/backup alpine tar czf /backup/postgres-data.tar.gz -C /source .
        docker run --rm -v centuryproptax_redis-data:/source -v "$BACKUP_DIR":/backup alpine tar czf /backup/redis-data.tar.gz -C /source .
    fi

    # Backup current configuration
    if [[ -f "$ENV_FILE" ]]; then
        cp "$ENV_FILE" "$BACKUP_DIR/env.backup"
    fi

    log "INFO" "Backup created at: $BACKUP_DIR"
}

# Build and deploy containers
deploy_containers() {
    log "INFO" "Starting container deployment..."

    cd "$PROJECT_ROOT"

    # Pull latest images
    log "INFO" "Pulling latest images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" pull

    # Build application image
    log "INFO" "Building application image..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache app

    # Start services
    log "INFO" "Starting services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d

    log "INFO" "Containers deployed successfully"
}

# Health check validation
validate_deployment() {
    log "INFO" "Validating deployment health..."

    local max_attempts=30
    local attempt=0
    local health_status="unknown"

    while [[ $attempt -lt $max_attempts ]]; do
        attempt=$((attempt + 1))

        log "DEBUG" "Health check attempt $attempt/$max_attempts"

        if health_response=$(curl -s -f "$HEALTH_CHECK_URL" 2>/dev/null); then
            health_status=$(echo "$health_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")

            if [[ "$health_status" == "healthy" ]]; then
                log "INFO" "Health check passed"
                return 0
            fi
        fi

        log "DEBUG" "Health check failed (status: $health_status), retrying in 10 seconds..."
        sleep 10
    done

    log "ERROR" "Health check failed after $max_attempts attempts"
    return 1
}

# Validate specific functionality
validate_functionality() {
    log "INFO" "Validating application functionality..."

    # Test documentation portal
    if curl -s -f "$HEALTH_CHECK_URL" | grep -q "healthy"; then
        log "INFO" "✅ API health check passed"
    else
        log "ERROR" "❌ API health check failed"
        return 1
    fi

    # Test documentation endpoints
    local base_url=$(echo "$HEALTH_CHECK_URL" | sed 's|/health||')

    if curl -s -f "$base_url/docs" >/dev/null; then
        log "INFO" "✅ Swagger UI accessible"
    else
        log "ERROR" "❌ Swagger UI not accessible"
        return 1
    fi

    if curl -s -f "$base_url/redoc" >/dev/null; then
        log "INFO" "✅ ReDoc accessible"
    else
        log "ERROR" "❌ ReDoc not accessible"
        return 1
    fi

    if curl -s -f "$base_url/documentation" >/dev/null; then
        log "INFO" "✅ Documentation portal accessible"
    else
        log "ERROR" "❌ Documentation portal not accessible"
        return 1
    fi

    if curl -s -f "$base_url/openapi.json" >/dev/null; then
        log "INFO" "✅ OpenAPI schema accessible"
    else
        log "ERROR" "❌ OpenAPI schema not accessible"
        return 1
    fi

    log "INFO" "All functionality tests passed"
}

# Performance validation
validate_performance() {
    log "INFO" "Validating deployment performance..."

    local base_url=$(echo "$HEALTH_CHECK_URL" | sed 's|/health||')

    # Test response times
    local health_time=$(curl -w "%{time_total}" -s -o /dev/null "$HEALTH_CHECK_URL")
    local docs_time=$(curl -w "%{time_total}" -s -o /dev/null "$base_url/docs")

    # Validate response times (should be under 2 seconds)
    if (( $(echo "$health_time < 2.0" | bc -l) )); then
        log "INFO" "✅ Health endpoint response time: ${health_time}s"
    else
        log "WARN" "⚠️ Health endpoint slow response: ${health_time}s"
    fi

    if (( $(echo "$docs_time < 3.0" | bc -l) )); then
        log "INFO" "✅ Docs endpoint response time: ${docs_time}s"
    else
        log "WARN" "⚠️ Docs endpoint slow response: ${docs_time}s"
    fi

    log "INFO" "Performance validation completed"
}

# Rollback deployment
rollback_deployment() {
    log "WARN" "Starting deployment rollback..."

    if [[ ! -d "$BACKUP_DIR" ]]; then
        log "ERROR" "Backup directory not found. Cannot rollback."
        return 1
    fi

    cd "$PROJECT_ROOT"

    # Stop current containers
    log "INFO" "Stopping current containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" down

    # Restore volumes if backup exists
    if [[ -f "$BACKUP_DIR/postgres-data.tar.gz" ]]; then
        log "INFO" "Restoring PostgreSQL data..."
        docker run --rm -v centuryproptax_postgres-data:/target -v "$BACKUP_DIR":/backup alpine sh -c "cd /target && tar xzf /backup/postgres-data.tar.gz"
    fi

    if [[ -f "$BACKUP_DIR/redis-data.tar.gz" ]]; then
        log "INFO" "Restoring Redis data..."
        docker run --rm -v centuryproptax_redis-data:/target -v "$BACKUP_DIR":/backup alpine sh -c "cd /target && tar xzf /backup/redis-data.tar.gz"
    fi

    # Restore configuration
    if [[ -f "$BACKUP_DIR/env.backup" ]]; then
        cp "$BACKUP_DIR/env.backup" "$ENV_FILE"
    fi

    # Start previous version
    log "INFO" "Starting previous version..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d

    # Validate rollback
    if validate_deployment; then
        log "INFO" "Rollback completed successfully"
    else
        log "ERROR" "Rollback failed"
        return 1
    fi
}

# Cleanup old resources
cleanup_old_resources() {
    log "INFO" "Cleaning up old resources..."

    # Remove unused Docker images
    docker image prune -f >/dev/null 2>&1 || true

    # Remove old backup directories (keep last 5)
    find /tmp -name "deployment_backup_*" -type d -mtime +5 -exec rm -rf {} + 2>/dev/null || true

    log "INFO" "Cleanup completed"
}

# Send deployment notification
send_notification() {
    local status="$1"
    local webhook_url="${DEPLOYMENT_NOTIFICATION_WEBHOOK:-}"

    if [[ -n "$webhook_url" ]]; then
        local message
        if [[ "$status" == "success" ]]; then
            message="✅ Century Property Tax Documentation Portal deployed successfully"
        else
            message="🚨 Century Property Tax Documentation Portal deployment failed"
        fi

        curl -X POST "$webhook_url" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"$message\"}" \
            2>/dev/null || true
    fi
}

# Generate deployment report
generate_deployment_report() {
    local status="$1"
    local report_file="/tmp/deployment_report_$(date +%Y%m%d_%H%M%S).json"

    cat > "$report_file" <<EOF
{
    "deployment_id": "$(date +%Y%m%d_%H%M%S)",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "status": "$status",
    "environment": "$ENVIRONMENT",
    "health_check_url": "$HEALTH_CHECK_URL",
    "logs": "$DEPLOYMENT_LOG",
    "backup_location": "$BACKUP_DIR"
}
EOF

    log "INFO" "Deployment report generated: $report_file"
}

# Main deployment function
main() {
    log "INFO" "Starting Century Property Tax Documentation Portal deployment"
    log "INFO" "Environment: $ENVIRONMENT"
    log "INFO" "Deployment ID: $(date +%Y%m%d_%H%M%S)"

    # Deployment steps
    validate_prerequisites
    create_deployment_backup
    deploy_containers

    # Wait for services to start
    log "INFO" "Waiting for services to start..."
    sleep 30

    # Validation steps
    validate_deployment
    validate_functionality
    validate_performance

    # Cleanup
    cleanup_old_resources

    log "INFO" "🎉 Deployment completed successfully!"

    # Generate report and send notification
    generate_deployment_report "success"
    send_notification "success"

    # Display summary
    echo
    echo "================================================"
    echo "   DEPLOYMENT SUCCESSFUL"
    echo "================================================"
    echo "Environment: $ENVIRONMENT"
    echo "Health Check: $HEALTH_CHECK_URL"
    echo "Documentation: $(echo "$HEALTH_CHECK_URL" | sed 's|/health|/documentation|')"
    echo "Swagger UI: $(echo "$HEALTH_CHECK_URL" | sed 's|/health|/docs|')"
    echo "ReDoc: $(echo "$HEALTH_CHECK_URL" | sed 's|/health|/redoc|')"
    echo "Logs: $DEPLOYMENT_LOG"
    echo "Backup: $BACKUP_DIR"
    echo "================================================"
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi