#!/bin/bash
# Automated backup script for Century Property Tax Documentation Portal
# This script should be run via cron for regular backups

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/app/logs/backup_cron.log"
BACKUP_SCRIPT="/app/scripts/backup/backup_system.py"
NOTIFICATION_WEBHOOK="${BACKUP_NOTIFICATION_WEBHOOK:-}"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    local exit_code=$?
    log "ERROR: Backup failed with exit code $exit_code"

    # Send notification if webhook is configured
    if [[ -n "$NOTIFICATION_WEBHOOK" ]]; then
        curl -X POST "$NOTIFICATION_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"🚨 Century Property Tax backup failed with exit code $exit_code\"}" \
            2>/dev/null || true
    fi

    exit $exit_code
}

# Set up error handling
trap handle_error ERR

# Start backup
log "Starting automated backup process"

# Check if backup script exists
if [[ ! -f "$BACKUP_SCRIPT" ]]; then
    log "ERROR: Backup script not found at $BACKUP_SCRIPT"
    exit 1
fi

# Run health check first
log "Running backup system health check"
if ! python3 "$BACKUP_SCRIPT" health; then
    log "WARNING: Some health checks failed, but continuing with backup"
fi

# Create backup
log "Creating full system backup"
if python3 "$BACKUP_SCRIPT" backup; then
    log "Backup completed successfully"

    # Send success notification if webhook is configured
    if [[ -n "$NOTIFICATION_WEBHOOK" ]]; then
        curl -X POST "$NOTIFICATION_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"✅ Century Property Tax backup completed successfully\"}" \
            2>/dev/null || true
    fi
else
    log "ERROR: Backup failed"
    exit 1
fi

# List recent backups for verification
log "Recent backups:"
python3 "$BACKUP_SCRIPT" list | head -10 | tee -a "$LOG_FILE"

log "Backup process completed"