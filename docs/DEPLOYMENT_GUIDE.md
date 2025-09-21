# Deployment Guide - Century Property Tax Application

This guide provides comprehensive deployment procedures for the Century Property Tax application with special focus on logging configuration across different environments.

## Overview

The application supports multiple deployment scenarios:
- **Development**: Local development with debug logging
- **Staging**: Production-like environment with verbose logging
- **Production**: Optimized performance with structured logging
- **Docker**: Containerized deployment with flexible logging options

## Pre-Deployment Checklist

### 1. Environment Variables
Ensure all required environment variables are configured:

```bash
# Core Application (Required)
WHATSAPP_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_ID=your_phone_id
GOOGLE_API_KEY=your_gemini_api_key
DATABASE_URL=your_database_url

# Logging Configuration (Recommended)
LOG_LEVEL=INFO                    # INFO for production, DEBUG for development
LOG_DIR=/var/log/centuryproptax  # Absolute path for production
LOG_FILE_ENABLED=true            # Enable file logging with rotation
```

### 2. Directory Structure
Create necessary directories with proper permissions:

```bash
# Production directories
sudo mkdir -p /var/log/centuryproptax
sudo mkdir -p /var/lib/centuryproptax
sudo mkdir -p /etc/centuryproptax

# Set proper permissions
sudo chown -R app:app /var/log/centuryproptax
sudo chown -R app:app /var/lib/centuryproptax
sudo chmod 755 /var/log/centuryproptax
sudo chmod 644 /etc/centuryproptax/.env
```

### 3. Dependencies
Install required system packages and Python dependencies:

```bash
# System packages (Ubuntu/Debian)
sudo apt update
sudo apt install -y python3-pip python3-venv nginx redis-server

# Python dependencies
pip install -r requirements.txt
```

## Environment-Specific Configurations

### Development Environment

#### Logging Configuration
```bash
# .env.development
LOG_LEVEL=DEBUG
LOG_DIR=./logs
LOG_FILE_ENABLED=true
DEBUG=true

# WhatsApp configuration for development
ALLOW_BUSINESS_ACCOUNT_REPLIES=true
```

#### Setup Steps
```bash
# 1. Clone repository
git clone https://github.com/your-org/centuryproptax.git
cd centuryproptax

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment
cp .env.example .env.development
# Edit .env.development with your settings

# 5. Initialize database
python scripts/init_database.py

# 6. Start development server
python src/main.py
```

#### Development Logging Features
- **DEBUG level logging**: Detailed function entry/exit traces
- **Local file logging**: Logs stored in `./logs/` directory
- **Console output**: Real-time log streaming to terminal
- **No log compression**: Immediate access to all log files

### Staging Environment

#### Logging Configuration
```bash
# .env.staging
LOG_LEVEL=INFO
LOG_DIR=/var/log/centuryproptax-staging
LOG_FILE_ENABLED=true
DEBUG=false

# Performance monitoring
ENABLE_PERFORMANCE_LOGGING=true
```

#### Setup Steps
```bash
# 1. Create application user
sudo useradd -r -s /bin/bash -d /var/lib/centuryproptax centuryproptax

# 2. Create directories
sudo mkdir -p /var/log/centuryproptax-staging
sudo mkdir -p /var/lib/centuryproptax-staging
sudo chown -R centuryproptax:centuryproptax /var/log/centuryproptax-staging
sudo chown -R centuryproptax:centuryproptax /var/lib/centuryproptax-staging

# 3. Deploy application
sudo -u centuryproptax git clone https://github.com/your-org/centuryproptax.git /var/lib/centuryproptax-staging
cd /var/lib/centuryproptax-staging

# 4. Configure environment
sudo -u centuryproptax cp .env.example .env.staging
# Edit .env.staging with staging credentials

# 5. Install dependencies
sudo -u centuryproptax python3 -m venv venv
sudo -u centuryproptax venv/bin/pip install -r requirements.txt

# 6. Create systemd service
sudo cp deployment/systemd/centuryproptax-staging.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable centuryproptax-staging
sudo systemctl start centuryproptax-staging
```

#### Staging Logging Features
- **INFO level logging**: Application flow and business events
- **Structured logging**: JSON format for log aggregation
- **Log rotation**: 100MB files, 20 backups (2GB total)
- **Performance metrics**: Request timing and resource usage

### Production Environment

#### Logging Configuration
```bash
# .env.production
LOG_LEVEL=WARNING
LOG_DIR=/var/log/centuryproptax
LOG_FILE_ENABLED=true
DEBUG=false

# Security settings
SECRET_KEY=your_production_secret_key
PROPERTY_DATA_ENCRYPTION_KEY=your_encryption_key

# Performance optimization
ENABLE_PERFORMANCE_LOGGING=false
LOG_SENSITIVE_DATA=false
```

#### Setup Steps
```bash
# 1. Create production user and directories
sudo useradd -r -s /bin/bash -d /var/lib/centuryproptax centuryproptax
sudo mkdir -p /var/log/centuryproptax
sudo mkdir -p /var/lib/centuryproptax
sudo mkdir -p /etc/centuryproptax

# 2. Set proper permissions
sudo chown -R centuryproptax:centuryproptax /var/log/centuryproptax
sudo chown -R centuryproptax:centuryproptax /var/lib/centuryproptax
sudo chmod 750 /var/log/centuryproptax
sudo chmod 700 /etc/centuryproptax

# 3. Deploy application
sudo -u centuryproptax git clone https://github.com/your-org/centuryproptax.git /var/lib/centuryproptax
cd /var/lib/centuryproptax

# 4. Configure production environment
sudo cp .env.example /etc/centuryproptax/.env
sudo chown centuryproptax:centuryproptax /etc/centuryproptax/.env
sudo chmod 600 /etc/centuryproptax/.env
# Edit /etc/centuryproptax/.env with production settings

# 5. Create symbolic link
sudo -u centuryproptax ln -s /etc/centuryproptax/.env /var/lib/centuryproptax/.env

# 6. Install dependencies and configure service
sudo -u centuryproptax python3 -m venv venv
sudo -u centuryproptax venv/bin/pip install -r requirements.txt

# 7. Configure systemd service
sudo cp deployment/systemd/centuryproptax.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable centuryproptax
sudo systemctl start centuryproptax

# 8. Configure nginx reverse proxy
sudo cp deployment/nginx/centuryproptax.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/centuryproptax.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Production Logging Features
- **WARNING+ level logging**: Errors and warnings only for performance
- **Structured JSON logs**: Optimized for log aggregation systems
- **Compressed rotation**: Automatic gzip compression to save disk space
- **Security compliance**: No sensitive data in logs
- **Log monitoring**: Integration with monitoring systems

## Docker Deployment

### Option 1: Console Logging Only (Recommended)
Ideal for container orchestration platforms like Kubernetes:

```dockerfile
# Dockerfile.production
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Configure for container logging
ENV LOG_FILE_ENABLED=false
ENV LOG_LEVEL=INFO

# Run application
CMD ["python", "src/main.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  centuryproptax:
    build: .
    environment:
      - LOG_LEVEL=INFO
      - LOG_FILE_ENABLED=false
      - WHATSAPP_TOKEN=${WHATSAPP_TOKEN}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
```

### Option 2: Persistent File Logging
For scenarios requiring log file persistence:

```dockerfile
# Dockerfile.with-logs
FROM python:3.11-slim

# Create app user and directories
RUN useradd -r -s /bin/bash -d /app app
RUN mkdir -p /app/logs && chown app:app /app/logs

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app
RUN chown -R app:app /app

# Configure logging
ENV LOG_LEVEL=INFO
ENV LOG_DIR=/app/logs
ENV LOG_FILE_ENABLED=true

# Create volume for logs
VOLUME ["/app/logs"]

# Switch to app user
USER app

# Run application
CMD ["python", "src/main.py"]
```

```yaml
# docker-compose.persistent-logs.yml
version: '3.8'
services:
  centuryproptax:
    build:
      context: .
      dockerfile: Dockerfile.with-logs
    environment:
      - LOG_LEVEL=INFO
      - LOG_FILE_ENABLED=true
      - LOG_DIR=/app/logs
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

### Kubernetes Deployment
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: centuryproptax
spec:
  replicas: 3
  selector:
    matchLabels:
      app: centuryproptax
  template:
    metadata:
      labels:
        app: centuryproptax
    spec:
      containers:
      - name: centuryproptax
        image: centuryproptax:latest
        env:
        - name: LOG_LEVEL
          value: "INFO"
        - name: LOG_FILE_ENABLED
          value: "false"  # Use Kubernetes logging
        - name: WHATSAPP_TOKEN
          valueFrom:
            secretKeyRef:
              name: centuryproptax-secrets
              key: whatsapp-token
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Post-Deployment Verification

### 1. Verify Application Startup
```bash
# Check service status
sudo systemctl status centuryproptax

# Check application logs for startup confirmation
sudo tail -f /var/log/centuryproptax/app.log

# Look for these messages:
# "Logging configured - Level: INFO"
# "Log directory: /var/log/centuryproptax"
# "File logging: enabled"
# "Application started successfully"
```

### 2. Test Logging Configuration
```bash
# Test log file creation
sudo -u centuryproptax python3 -c "
from src.core.logging import configure_logging, get_logger
configure_logging()
logger = get_logger('deployment_test')
logger.info('Deployment verification test', event='deployment_test')
print('Logging test completed')
"

# Verify log entry was created
sudo tail -n 1 /var/log/centuryproptax/app.log
```

### 3. Verify Log Rotation
```bash
# Check log rotation configuration
ls -la /var/log/centuryproptax/
# Should show app.log and possibly compressed backups

# Test log rotation trigger (if needed)
sudo logrotate -f /etc/logrotate.d/centuryproptax
```

### 4. Test Application Functionality
```bash
# Send test message via WhatsApp webhook
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "id": "test",
      "changes": [{
        "value": {
          "messaging_product": "whatsapp",
          "messages": [{
            "id": "test_msg_id",
            "from": "1234567890",
            "timestamp": "1234567890",
            "text": {"body": "test message"},
            "type": "text"
          }]
        }
      }]
    }]
  }'

# Check logs for message processing
sudo tail -f /var/log/centuryproptax/app.log | grep "test_msg_id"
```

## Monitoring and Maintenance

### Log Monitoring Commands
```bash
# Monitor real-time logs
sudo tail -f /var/log/centuryproptax/app.log

# Check log file sizes
sudo du -h /var/log/centuryproptax/

# Count error messages in last hour
sudo journalctl -u centuryproptax --since "1 hour ago" | grep -c ERROR

# View structured logs in readable format
sudo tail /var/log/centuryproptax/app.log | jq .
```

### Performance Monitoring
```bash
# Monitor application memory usage
ps aux | grep centuryproptax

# Check disk space for logs
df -h /var/log/

# Monitor log file growth rate
watch -n 5 'ls -lh /var/log/centuryproptax/app.log'
```

### Backup Procedures
```bash
# Backup logs before rotation
sudo tar -czf /backup/centuryproptax-logs-$(date +%Y%m%d).tar.gz /var/log/centuryproptax/

# Backup configuration
sudo cp /etc/centuryproptax/.env /backup/centuryproptax-config-$(date +%Y%m%d).env
```

## Troubleshooting Deployment Issues

### Common Deployment Problems

#### 1. Service Won't Start
```bash
# Check service status and logs
sudo systemctl status centuryproptax
sudo journalctl -u centuryproptax -f

# Common issues:
# - Missing environment variables
# - Database connection problems
# - Port already in use
# - Permission issues
```

#### 2. Log Files Not Created
```bash
# Check directory permissions
ls -la /var/log/centuryproptax/

# Test manual log creation
sudo -u centuryproptax touch /var/log/centuryproptax/test.log

# If this fails, fix permissions:
sudo chown -R centuryproptax:centuryproptax /var/log/centuryproptax/
sudo chmod 755 /var/log/centuryproptax/
```

#### 3. High Memory Usage
```bash
# Check for memory leaks in logging
sudo pmap $(pgrep -f centuryproptax) | tail

# Reduce log level if needed
echo "LOG_LEVEL=ERROR" | sudo tee -a /etc/centuryproptax/.env
sudo systemctl restart centuryproptax
```

### Rollback Procedures
```bash
# Quick rollback to previous version
sudo systemctl stop centuryproptax
sudo -u centuryproptax git checkout HEAD~1
sudo systemctl start centuryproptax

# Restore previous configuration
sudo cp /backup/centuryproptax-config-YYYYMMDD.env /etc/centuryproptax/.env
sudo systemctl restart centuryproptax
```

This deployment guide ensures consistent logging configuration across all environments while maintaining security and performance best practices.