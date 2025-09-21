# DevOps Logging Runbook - Century Property Tax Application

This runbook provides comprehensive procedures for DevOps engineers to monitor, maintain, and troubleshoot the logging system in production environments.

## Table of Contents

1. [System Overview](#system-overview)
2. [Daily Operations](#daily-operations)
3. [Monitoring and Alerting](#monitoring-and-alerting)
4. [Maintenance Procedures](#maintenance-procedures)
5. [Incident Response](#incident-response)
6. [Performance Tuning](#performance-tuning)
7. [Backup and Recovery](#backup-and-recovery)
8. [Security Considerations](#security-considerations)

## System Overview

### Logging Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │────▶│  Log Rotation   │────▶│  Log Storage    │
│     Logs        │    │   (100MB/file)  │    │  (10 backups)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  Compression    │
                          │    (gzip)       │
                          └─────────────────┘
```

### Log File Locations
- **Production**: `/var/log/centuryproptax/`
- **Staging**: `/var/log/centuryproptax-staging/`
- **Development**: `./logs/`

### Configuration Files
- **Environment**: `/etc/centuryproptax/.env`
- **Systemd Service**: `/etc/systemd/system/centuryproptax.service`
- **Log Rotation**: Automatic via application (100MB limit)

## Daily Operations

### Morning Checklist

#### 1. Check Service Health
```bash
#!/bin/bash
# daily_health_check.sh

echo "=== Century Property Tax - Daily Health Check ==="
echo "Date: $(date)"
echo

# Check service status
echo "1. Service Status:"
systemctl is-active centuryproptax || echo "❌ Service is not active"
systemctl is-enabled centuryproptax || echo "❌ Service is not enabled"

# Check disk space
echo -e "\n2. Disk Space:"
df -h /var/log/centuryproptax/ | tail -1 | awk '{
    if ($5 > 80) print "❌ Log disk usage: " $5 " (> 80%)"
    else print "✅ Log disk usage: " $5
}'

# Check recent errors
echo -e "\n3. Recent Errors (last 24 hours):"
error_count=$(journalctl -u centuryproptax --since "24 hours ago" | grep -c "ERROR\|CRITICAL" || echo "0")
if [ "$error_count" -gt 10 ]; then
    echo "❌ High error count: $error_count errors"
else
    echo "✅ Error count: $error_count errors"
fi

# Check log file rotation
echo -e "\n4. Log Files:"
ls -lh /var/log/centuryproptax/ | grep app.log
compressed_count=$(ls /var/log/centuryproptax/app.log.*.gz 2>/dev/null | wc -l)
echo "Compressed backups: $compressed_count"

# Check memory usage
echo -e "\n5. Memory Usage:"
ps aux | grep centuryproptax | grep -v grep | awk '{
    if ($4 > 10) print "❌ High memory usage: " $4 "%"
    else print "✅ Memory usage: " $4 "%"
}'

echo -e "\n=== Health Check Complete ==="
```

#### 2. Log Analysis
```bash
#!/bin/bash
# daily_log_analysis.sh

LOG_DIR="/var/log/centuryproptax"
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

echo "=== Daily Log Analysis for $YESTERDAY ==="

# Error summary
echo "1. Error Summary:"
grep "$YESTERDAY" $LOG_DIR/app.log | jq -r 'select(.level == "error" or .level == "critical") | .event' | sort | uniq -c | sort -nr

# Top events
echo -e "\n2. Top Events:"
grep "$YESTERDAY" $LOG_DIR/app.log | jq -r '.event' | sort | uniq -c | sort -nr | head -10

# Performance metrics
echo -e "\n3. Performance Metrics:"
grep "$YESTERDAY" $LOG_DIR/app.log | jq -r 'select(.execution_time_ms) | .execution_time_ms' | awk '
{
    sum += $1
    count++
    if ($1 > max) max = $1
}
END {
    if (count > 0) {
        print "Average response time: " sum/count " ms"
        print "Max response time: " max " ms"
        print "Total requests: " count
    }
}'

# User activity
echo -e "\n4. User Activity:"
unique_users=$(grep "$YESTERDAY" $LOG_DIR/app.log | jq -r 'select(.user_id) | .user_id' | sort | uniq | wc -l)
echo "Unique active users: $unique_users"

echo -e "\n=== Analysis Complete ==="
```

### Evening Checklist

#### 1. Backup Verification
```bash
#!/bin/bash
# evening_backup_check.sh

echo "=== Evening Backup Verification ==="

# Check compressed log files
echo "1. Compressed Log Files:"
find /var/log/centuryproptax/ -name "*.gz" -mtime -1 -ls

# Verify backup integrity
echo -e "\n2. Backup Integrity:"
for file in /var/log/centuryproptax/app.log.*.gz; do
    if [ -f "$file" ]; then
        if gzip -t "$file" 2>/dev/null; then
            echo "✅ $file - OK"
        else
            echo "❌ $file - CORRUPTED"
        fi
    fi
done

# Check log rotation
echo -e "\n3. Log Rotation Status:"
current_size=$(stat -c%s /var/log/centuryproptax/app.log)
max_size=$((100 * 1024 * 1024))  # 100MB
usage_percent=$((current_size * 100 / max_size))
echo "Current log file: $(($current_size / 1024 / 1024))MB ($usage_percent%)"
```

## Monitoring and Alerting

### Key Metrics to Monitor

#### 1. Disk Space Monitoring
```bash
#!/bin/bash
# monitor_disk_space.sh

THRESHOLD=80
CURRENT=$(df /var/log/centuryproptax/ | tail -1 | awk '{print $5}' | sed 's/%//')

if [ "$CURRENT" -gt "$THRESHOLD" ]; then
    echo "ALERT: Log disk space at $CURRENT% (threshold: $THRESHOLD%)"
    # Send alert (email, Slack, PagerDuty, etc.)
    send_alert "disk_space_high" "Log disk usage: $CURRENT%"
fi
```

#### 2. Error Rate Monitoring
```bash
#!/bin/bash
# monitor_error_rate.sh

# Count errors in last hour
ERRORS=$(journalctl -u centuryproptax --since "1 hour ago" | grep -c "ERROR\|CRITICAL")
THRESHOLD=50

if [ "$ERRORS" -gt "$THRESHOLD" ]; then
    echo "ALERT: High error rate: $ERRORS errors in last hour"
    send_alert "high_error_rate" "Error count: $ERRORS in last hour"
fi
```

#### 3. Log File Growth Monitoring
```bash
#!/bin/bash
# monitor_log_growth.sh

LOG_FILE="/var/log/centuryproptax/app.log"
CURRENT_SIZE=$(stat -c%s "$LOG_FILE")
THRESHOLD=$((90 * 1024 * 1024))  # 90MB (near rotation threshold)

if [ "$CURRENT_SIZE" -gt "$THRESHOLD" ]; then
    echo "INFO: Log file nearing rotation threshold: $(($CURRENT_SIZE / 1024 / 1024))MB"
fi
```

### Automated Monitoring Setup

#### Systemd Timer for Daily Checks
```ini
# /etc/systemd/system/centuryproptax-health-check.timer
[Unit]
Description=Daily health check for Century Property Tax
Requires=centuryproptax-health-check.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/centuryproptax-health-check.service
[Unit]
Description=Century Property Tax Health Check
After=centuryproptax.service

[Service]
Type=oneshot
ExecStart=/opt/centuryproptax/scripts/daily_health_check.sh
User=centuryproptax
```

#### Nagios/Icinga Checks
```bash
# /usr/local/nagios/libexec/check_centuryproptax_logs

#!/bin/bash
# Nagios plugin for Century Property Tax logging

WARNING_THRESHOLD=20
CRITICAL_THRESHOLD=50

# Count errors in last hour
ERROR_COUNT=$(journalctl -u centuryproptax --since "1 hour ago" | grep -c "ERROR\|CRITICAL")

if [ "$ERROR_COUNT" -ge "$CRITICAL_THRESHOLD" ]; then
    echo "CRITICAL - $ERROR_COUNT errors in last hour"
    exit 2
elif [ "$ERROR_COUNT" -ge "$WARNING_THRESHOLD" ]; then
    echo "WARNING - $ERROR_COUNT errors in last hour"
    exit 1
else
    echo "OK - $ERROR_COUNT errors in last hour"
    exit 0
fi
```

## Maintenance Procedures

### Weekly Maintenance

#### 1. Log File Cleanup
```bash
#!/bin/bash
# weekly_log_cleanup.sh

LOG_DIR="/var/log/centuryproptax"

echo "=== Weekly Log Cleanup ==="

# Remove compressed logs older than 30 days
echo "1. Removing compressed logs older than 30 days:"
find "$LOG_DIR" -name "app.log.*.gz" -mtime +30 -print -delete

# Archive logs older than 7 days to backup location
echo -e "\n2. Archiving recent compressed logs:"
BACKUP_DIR="/backup/centuryproptax/logs/$(date +%Y/%m)"
mkdir -p "$BACKUP_DIR"

find "$LOG_DIR" -name "app.log.*.gz" -mtime +7 -mtime -30 -exec mv {} "$BACKUP_DIR/" \;

# Verify current log file integrity
echo -e "\n3. Verifying current log file:"
if [ -f "$LOG_DIR/app.log" ]; then
    echo "Current log file size: $(stat -c%s $LOG_DIR/app.log | numfmt --to=iec-i)"
    echo "Last modified: $(stat -c%y $LOG_DIR/app.log)"
else
    echo "❌ Current log file missing!"
fi

echo -e "\n=== Cleanup Complete ==="
```

#### 2. Performance Analysis
```bash
#!/bin/bash
# weekly_performance_analysis.sh

LOG_DIR="/var/log/centuryproptax"
WEEK_AGO=$(date -d "7 days ago" +%Y-%m-%d)

echo "=== Weekly Performance Analysis (since $WEEK_AGO) ==="

# Analyze response times
echo "1. Response Time Analysis:"
zcat "$LOG_DIR"/app.log.*.gz "$LOG_DIR/app.log" | \
grep -E "execution_time_ms.*$WEEK_AGO" | \
jq -r '.execution_time_ms' | \
awk '
{
    times[NR] = $1
    sum += $1
    if ($1 > max) max = $1
    if (min == "" || $1 < min) min = $1
}
END {
    if (NR > 0) {
        print "Total requests: " NR
        print "Average time: " sum/NR " ms"
        print "Min time: " min " ms"
        print "Max time: " max " ms"

        # Calculate percentiles
        n = asort(times)
        print "95th percentile: " times[int(n * 0.95)] " ms"
        print "99th percentile: " times[int(n * 0.99)] " ms"
    }
}'

# Analyze error patterns
echo -e "\n2. Error Pattern Analysis:"
zcat "$LOG_DIR"/app.log.*.gz "$LOG_DIR/app.log" | \
grep -E "(ERROR|CRITICAL).*$WEEK_AGO" | \
jq -r '.event' | sort | uniq -c | sort -nr | head -10

echo -e "\n=== Analysis Complete ==="
```

### Monthly Maintenance

#### 1. Capacity Planning
```bash
#!/bin/bash
# monthly_capacity_planning.sh

LOG_DIR="/var/log/centuryproptax"

echo "=== Monthly Capacity Planning ==="

# Calculate monthly log volume
MONTH_AGO=$(date -d "30 days ago" +%Y-%m-%d)
TOTAL_SIZE=$(find "$LOG_DIR" -name "*.log*" -newer "$(date -d "$MONTH_AGO" +%Y-%m-%d)" -exec stat -c%s {} \; | awk '{sum += $1} END {print sum}')

echo "1. Log Volume Analysis:"
echo "Total log volume (30 days): $(echo $TOTAL_SIZE | numfmt --to=iec-i)"
echo "Average daily volume: $(echo "scale=2; $TOTAL_SIZE / 30 / 1024 / 1024" | bc) MB"
echo "Projected yearly volume: $(echo "scale=2; $TOTAL_SIZE * 12 / 1024 / 1024 / 1024" | bc) GB"

# Disk space projections
CURRENT_USAGE=$(df /var/log/centuryproptax/ | tail -1 | awk '{print $3}')
TOTAL_SPACE=$(df /var/log/centuryproptax/ | tail -1 | awk '{print $2}')
USAGE_PERCENT=$(echo "scale=2; $CURRENT_USAGE * 100 / $TOTAL_SPACE" | bc)

echo -e "\n2. Disk Space Projections:"
echo "Current usage: $USAGE_PERCENT%"
echo "Estimated months until 80% capacity: $(echo "scale=0; (($TOTAL_SPACE * 0.8) - $CURRENT_USAGE) / ($TOTAL_SIZE / 30) / 30" | bc)"

echo -e "\n=== Planning Complete ==="
```

#### 2. Log Rotation Optimization
```bash
#!/bin/bash
# optimize_log_rotation.sh

echo "=== Log Rotation Optimization ==="

# Analyze rotation frequency
ROTATIONS=$(ls /var/log/centuryproptax/app.log.*.gz | wc -l)
echo "Current number of rotated files: $ROTATIONS"

# Calculate optimal rotation size based on volume
DAILY_VOLUME=$(find /var/log/centuryproptax/ -name "app.log" -mtime -1 -exec stat -c%s {} \;)
OPTIMAL_SIZE=$(echo "scale=0; $DAILY_VOLUME * 3" | bc)  # 3 days per file

echo "Daily log volume: $(echo $DAILY_VOLUME | numfmt --to=iec-i)"
echo "Suggested rotation size: $(echo $OPTIMAL_SIZE | numfmt --to=iec-i)"

if [ "$OPTIMAL_SIZE" -gt $((200 * 1024 * 1024)) ]; then
    echo "⚠️  Consider reducing log verbosity or increasing rotation frequency"
elif [ "$OPTIMAL_SIZE" -lt $((50 * 1024 * 1024)) ]; then
    echo "ℹ️  Could increase rotation size for fewer files"
fi

echo -e "\n=== Optimization Complete ==="
```

## Incident Response

### High Error Rate Incident

#### 1. Initial Response (5 minutes)
```bash
#!/bin/bash
# incident_high_errors.sh

echo "=== HIGH ERROR RATE INCIDENT RESPONSE ==="

# Get recent error summary
echo "1. Recent Error Summary (last 30 minutes):"
journalctl -u centuryproptax --since "30 minutes ago" | \
grep -E "(ERROR|CRITICAL)" | \
tail -20

# Check service status
echo -e "\n2. Service Status:"
systemctl status centuryproptax --lines=10

# Check resource usage
echo -e "\n3. Resource Usage:"
top -b -n 1 | grep centuryproptax
df -h /var/log/centuryproptax/

# Check recent deployments
echo -e "\n4. Recent Deployments:"
journalctl -u centuryproptax --since "2 hours ago" | grep -i "start\|restart\|deploy"
```

#### 2. Investigation (15 minutes)
```bash
#!/bin/bash
# investigate_errors.sh

LOG_FILE="/var/log/centuryproptax/app.log"

echo "=== ERROR INVESTIGATION ==="

# Top error events in last hour
echo "1. Top Error Events (last hour):"
tail -n 1000 "$LOG_FILE" | \
jq -r 'select(.timestamp > "'$(date -d "1 hour ago" --iso-8601)'") | select(.level == "error" or .level == "critical") | .event' | \
sort | uniq -c | sort -nr | head -10

# Error patterns by component
echo -e "\n2. Errors by Component:"
tail -n 1000 "$LOG_FILE" | \
jq -r 'select(.level == "error" or .level == "critical") | .component' | \
sort | uniq -c | sort -nr

# Recent stack traces
echo -e "\n3. Recent Stack Traces:"
tail -n 1000 "$LOG_FILE" | \
jq -r 'select(.stack_trace) | .stack_trace' | \
head -3

# Check for known error patterns
echo -e "\n4. Known Error Patterns:"
if grep -q "database.*connection" "$LOG_FILE"; then
    echo "❌ Database connection issues detected"
fi
if grep -q "rate.*limit" "$LOG_FILE"; then
    echo "❌ Rate limiting issues detected"
fi
if grep -q "timeout" "$LOG_FILE"; then
    echo "❌ Timeout issues detected"
fi
```

### Disk Space Critical Incident

#### 1. Emergency Response
```bash
#!/bin/bash
# emergency_disk_cleanup.sh

echo "=== EMERGENCY DISK CLEANUP ==="

LOG_DIR="/var/log/centuryproptax"

# Check current space
echo "1. Current Disk Usage:"
df -h "$LOG_DIR"

# Emergency cleanup: remove oldest compressed logs
echo -e "\n2. Emergency Cleanup:"
OLD_LOGS=$(find "$LOG_DIR" -name "app.log.*.gz" | sort | head -5)
if [ ! -z "$OLD_LOGS" ]; then
    echo "Removing oldest compressed logs:"
    echo "$OLD_LOGS"
    echo "$OLD_LOGS" | xargs rm -f

    echo "Space freed:"
    df -h "$LOG_DIR"
else
    echo "No compressed logs to remove"
fi

# If still critical, truncate current log
USAGE=$(df "$LOG_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$USAGE" -gt 95 ]; then
    echo -e "\n3. CRITICAL: Truncating current log file"
    tail -n 10000 "$LOG_DIR/app.log" > "$LOG_DIR/app.log.tmp"
    mv "$LOG_DIR/app.log.tmp" "$LOG_DIR/app.log"
    echo "Current log truncated to last 10,000 lines"
fi

echo -e "\n=== Emergency Cleanup Complete ==="
```

### Service Down Incident

#### 1. Quick Diagnostics
```bash
#!/bin/bash
# service_down_diagnostics.sh

echo "=== SERVICE DOWN DIAGNOSTICS ==="

# Check if process is running
echo "1. Process Status:"
if pgrep -f centuryproptax > /dev/null; then
    echo "✅ Process is running"
    ps aux | grep centuryproptax | grep -v grep
else
    echo "❌ Process is not running"
fi

# Check systemd status
echo -e "\n2. Systemd Status:"
systemctl status centuryproptax --lines=20

# Check recent logs
echo -e "\n3. Recent Logs:"
journalctl -u centuryproptax --since "10 minutes ago" --lines=20

# Check port binding
echo -e "\n4. Port Status:"
netstat -tlnp | grep :8000 || echo "Port 8000 not listening"

# Check log file for startup errors
echo -e "\n5. Application Logs:"
tail -n 20 /var/log/centuryproptax/app.log | grep -E "(ERROR|CRITICAL|started|failed)"
```

## Performance Tuning

### Log Level Optimization

#### Production Recommendations
```bash
# Environment settings for optimal production performance
LOG_LEVEL=WARNING           # Reduce verbosity
LOG_FILE_ENABLED=true      # Keep file logging for forensics
LOG_DIR=/var/log/centuryproptax
```

#### Performance Impact Analysis
```bash
#!/bin/bash
# analyze_log_performance.sh

echo "=== LOG PERFORMANCE ANALYSIS ==="

# Current log level impact
CURRENT_LEVEL=$(grep LOG_LEVEL /etc/centuryproptax/.env | cut -d= -f2)
echo "Current log level: $CURRENT_LEVEL"

# Estimate volume by level
LOG_FILE="/var/log/centuryproptax/app.log"

echo -e "\n1. Message Volume by Level (last 1000 entries):"
tail -n 1000 "$LOG_FILE" | jq -r '.level' | sort | uniq -c | sort -nr

# Estimate size impact
echo -e "\n2. Size Impact by Level:"
tail -n 1000 "$LOG_FILE" | jq -r 'select(.level == "debug") | length' | awk '{sum += $1; count++} END {if (count > 0) print "Average DEBUG message size: " sum/count " chars"}'
tail -n 1000 "$LOG_FILE" | jq -r 'select(.level == "info") | length' | awk '{sum += $1; count++} END {if (count > 0) print "Average INFO message size: " sum/count " chars"}'
```

### File I/O Optimization

#### 1. Monitor I/O Performance
```bash
#!/bin/bash
# monitor_log_io.sh

echo "=== LOG I/O MONITORING ==="

# Check I/O stats for log directory
LOG_DEVICE=$(df /var/log/centuryproptax/ | tail -1 | awk '{print $1}')
echo "Log device: $LOG_DEVICE"

# Monitor I/O for 30 seconds
echo "Monitoring I/O for 30 seconds..."
iostat -x 1 30 | grep -A 1 $(basename $LOG_DEVICE) | tail -20

# Check for I/O wait
echo -e "\nCurrent I/O wait:"
top -b -n 1 | grep "Cpu(s)" | awk '{print $10}' | sed 's/wa,//' | awk '{print "I/O wait: " $1}'
```

#### 2. Optimize Log Rotation
```bash
#!/bin/bash
# optimize_rotation.sh

LOG_DIR="/var/log/centuryproptax"

echo "=== LOG ROTATION OPTIMIZATION ==="

# Check current rotation efficiency
echo "1. Current Files:"
ls -lh "$LOG_DIR"/app.log*

# Calculate compression ratios
echo -e "\n2. Compression Efficiency:"
for file in "$LOG_DIR"/app.log.*.gz; do
    if [ -f "$file" ]; then
        compressed_size=$(stat -c%s "$file")
        uncompressed_size=$(gzip -l "$file" | tail -1 | awk '{print $2}')
        ratio=$(echo "scale=1; $compressed_size * 100 / $uncompressed_size" | bc)
        echo "$(basename $file): ${ratio}% of original size"
    fi
done
```

## Backup and Recovery

### Backup Procedures

#### 1. Daily Log Backup
```bash
#!/bin/bash
# daily_log_backup.sh

BACKUP_DIR="/backup/centuryproptax/logs"
LOG_DIR="/var/log/centuryproptax"
DATE=$(date +%Y%m%d)

echo "=== DAILY LOG BACKUP ==="

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup compressed logs
echo "1. Backing up compressed logs:"
cp "$LOG_DIR"/app.log.*.gz "$BACKUP_DIR/$DATE/" 2>/dev/null || echo "No compressed logs to backup"

# Backup current log (compress first)
echo "2. Backing up current log:"
gzip -c "$LOG_DIR/app.log" > "$BACKUP_DIR/$DATE/app.log.current.gz"

# Create metadata file
echo "3. Creating backup metadata:"
cat > "$BACKUP_DIR/$DATE/backup_info.txt" << EOF
Backup Date: $(date)
Source Directory: $LOG_DIR
Backup Type: Daily
Files Backed Up:
$(ls -la "$BACKUP_DIR/$DATE/")
Total Size: $(du -sh "$BACKUP_DIR/$DATE/" | cut -f1)
EOF

echo "✅ Backup completed: $BACKUP_DIR/$DATE"
```

#### 2. Weekly Archive
```bash
#!/bin/bash
# weekly_archive.sh

ARCHIVE_DIR="/archive/centuryproptax/logs"
BACKUP_DIR="/backup/centuryproptax/logs"
WEEK=$(date +%Y-W%U)

echo "=== WEEKLY LOG ARCHIVE ==="

# Create archive directory
mkdir -p "$ARCHIVE_DIR/$WEEK"

# Archive week's backups
echo "1. Archiving weekly backups:"
tar -czf "$ARCHIVE_DIR/$WEEK/logs-$WEEK.tar.gz" -C "$BACKUP_DIR" $(ls "$BACKUP_DIR" | sort | tail -7)

# Verify archive integrity
echo "2. Verifying archive:"
if tar -tzf "$ARCHIVE_DIR/$WEEK/logs-$WEEK.tar.gz" > /dev/null 2>&1; then
    echo "✅ Archive integrity verified"

    # Clean up old daily backups
    ls "$BACKUP_DIR" | sort | head -n -7 | xargs -I {} rm -rf "$BACKUP_DIR/{}"
    echo "✅ Old daily backups cleaned up"
else
    echo "❌ Archive verification failed"
    exit 1
fi

echo "✅ Weekly archive completed: $ARCHIVE_DIR/$WEEK"
```

### Recovery Procedures

#### 1. Point-in-Time Recovery
```bash
#!/bin/bash
# point_in_time_recovery.sh

TARGET_DATE="$1"
RECOVERY_DIR="/tmp/log_recovery"

if [ -z "$TARGET_DATE" ]; then
    echo "Usage: $0 YYYY-MM-DD"
    exit 1
fi

echo "=== POINT-IN-TIME LOG RECOVERY ==="
echo "Target date: $TARGET_DATE"

# Create recovery directory
mkdir -p "$RECOVERY_DIR"

# Find relevant backups
echo "1. Locating backups for $TARGET_DATE:"
BACKUP_FILES=$(find /backup/centuryproptax/logs/ -name "*$(echo $TARGET_DATE | sed 's/-//g')*")
ARCHIVE_FILES=$(find /archive/centuryproptax/logs/ -name "*.tar.gz" -newer "$(date -d "$TARGET_DATE" +%Y-%m-%d)")

# Restore from backups
echo "2. Restoring from backups:"
for file in $BACKUP_FILES; do
    cp -r "$file" "$RECOVERY_DIR/"
done

# Extract from archives if needed
echo "3. Extracting from archives:"
for file in $ARCHIVE_FILES; do
    tar -xzf "$file" -C "$RECOVERY_DIR/"
done

echo "✅ Recovery completed in: $RECOVERY_DIR"
echo "Files recovered:"
find "$RECOVERY_DIR" -name "*.log*" -o -name "*.gz"
```

#### 2. Emergency Log Recovery
```bash
#!/bin/bash
# emergency_recovery.sh

echo "=== EMERGENCY LOG RECOVERY ==="

LOG_DIR="/var/log/centuryproptax"
RECOVERY_DIR="/tmp/emergency_recovery"

# Create recovery environment
mkdir -p "$RECOVERY_DIR"

# Attempt to recover from systemd journal
echo "1. Recovering from systemd journal:"
journalctl -u centuryproptax --since "24 hours ago" > "$RECOVERY_DIR/systemd_recovery.log"

# Look for backup locations
echo "2. Searching for alternative log sources:"
find /var -name "*centuryproptax*log*" 2>/dev/null | head -10

# Attempt to recover deleted files (if filesystem supports it)
echo "3. Checking for recoverable deleted files:"
lsof | grep deleted | grep centuryproptax || echo "No deleted files found in use"

# Create minimal logging environment
echo "4. Setting up minimal logging:"
mkdir -p "$LOG_DIR"
touch "$LOG_DIR/app.log"
chown centuryproptax:centuryproptax "$LOG_DIR/app.log"
chmod 644 "$LOG_DIR/app.log"

echo "✅ Emergency recovery completed"
echo "Recovery files in: $RECOVERY_DIR"
echo "Minimal logging restored in: $LOG_DIR"
```

## Security Considerations

### Log Security Checklist

#### 1. File Permissions Audit
```bash
#!/bin/bash
# audit_log_permissions.sh

echo "=== LOG SECURITY AUDIT ==="

LOG_DIR="/var/log/centuryproptax"

# Check directory permissions
echo "1. Directory Permissions:"
ls -la "$LOG_DIR"

# Verify ownership
echo -e "\n2. File Ownership:"
find "$LOG_DIR" -not -user centuryproptax -ls

# Check for world-readable files
echo -e "\n3. World-Readable Files:"
find "$LOG_DIR" -perm /o+r -ls

# Check for suspicious access
echo -e "\n4. Recent Access (last 24 hours):"
find "$LOG_DIR" -atime -1 -ls
```

#### 2. Sensitive Data Detection
```bash
#!/bin/bash
# detect_sensitive_data.sh

LOG_FILE="/var/log/centuryproptax/app.log"

echo "=== SENSITIVE DATA DETECTION ==="

# Check for potential PII
echo "1. Checking for potential PII:"
grep -i "ssn\|social.*security\|credit.*card\|password" "$LOG_FILE" | wc -l | awk '{print "Potential PII instances: " $1}'

# Check for API keys
echo -e "\n2. Checking for API keys:"
grep -E "key.*[a-zA-Z0-9]{20,}" "$LOG_FILE" | wc -l | awk '{print "Potential API key instances: " $1}'

# Check for phone numbers
echo -e "\n3. Checking for phone numbers:"
grep -E "\b[0-9]{3}-[0-9]{3}-[0-9]{4}\b" "$LOG_FILE" | wc -l | awk '{print "Phone number instances: " $1}'

# Check for email addresses
echo -e "\n4. Checking for email addresses:"
grep -E "\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b" "$LOG_FILE" | wc -l | awk '{print "Email address instances: " $1}'
```

### Access Control

#### 1. Log Access Monitoring
```bash
#!/bin/bash
# monitor_log_access.sh

echo "=== LOG ACCESS MONITORING ==="

# Monitor file access with auditd (if available)
if command -v auditctl > /dev/null; then
    echo "1. Setting up audit rules:"
    auditctl -w /var/log/centuryproptax/ -p rwxa -k centuryproptax_logs
    echo "✅ Audit rules added"
else
    echo "⚠️  auditd not available"
fi

# Check recent access logs
echo -e "\n2. Recent Access (from auth.log):"
grep centuryproptax /var/log/auth.log | tail -10 || echo "No auth.log entries found"

# Monitor sudo access to logs
echo -e "\n3. Sudo Access to Logs:"
grep "COMMAND.*centuryproptax" /var/log/auth.log | tail -5 || echo "No sudo access logged"
```

This comprehensive DevOps runbook provides all necessary procedures for maintaining the Century Property Tax application's logging system in production environments. Regular execution of these procedures ensures optimal performance, security, and reliability.