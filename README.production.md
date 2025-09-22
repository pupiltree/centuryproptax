# Century Property Tax Documentation Portal - Production Deployment Guide

This guide provides comprehensive instructions for deploying the Century Property Tax Documentation Portal to production with security hardening, performance optimization, and operational excellence.

## Overview

The production deployment includes:

- **Containerized Deployment**: Docker-based deployment with Docker Compose
- **Security Hardening**: SSL/TLS, security headers, rate limiting, authentication
- **Performance Optimization**: CDN integration, caching, compression
- **Monitoring & Logging**: Prometheus metrics, Grafana dashboards, comprehensive logging
- **Backup & Recovery**: Automated backups with encryption and disaster recovery
- **SEO Optimization**: Meta tags, sitemaps, structured data

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Domain name configured (e.g., `docs.centuryproptax.com`)
- SSL certificates or Let's Encrypt setup
- Environment variables configured

### 1. Configuration

```bash
# Copy and configure environment file
cp .env.production.example .env.production

# Edit with your actual values
nano .env.production
```

### 2. Deploy

```bash
# Run deployment script
./scripts/deployment/deploy.sh
```

### 3. Validate

```bash
# Run validation tests
./scripts/deployment/validate.sh
```

## Detailed Configuration

### Environment Variables

Key environment variables to configure in `.env.production`:

```bash
# Application
ENVIRONMENT=production
BASE_URL=https://docs.centuryproptax.com
CDN_URL=https://cdn.centuryproptax.com

# Database
DATABASE_URL=postgresql://user:pass@db:5432/centuryproptax
POSTGRES_PASSWORD=your_secure_password

# Redis
REDIS_URL=redis://:password@redis:6379/0
REDIS_PASSWORD=your_secure_redis_password

# WhatsApp Business API
WA_ACCESS_TOKEN=your_whatsapp_token
WA_PHONE_NUMBER_ID=your_phone_number_id
WA_VERIFY_TOKEN=your_webhook_verify_token

# Payment (Razorpay)
RAZORPAY_KEY_ID=rzp_live_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret

# SSL/Security
ACME_EMAIL=admin@centuryproptax.com
JWT_SECRET_KEY=your_jwt_secret_minimum_32_chars

# Monitoring
GRAFANA_PASSWORD=your_grafana_password

# Backups
S3_BACKUP_BUCKET=centuryproptax-backups
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
BACKUP_ENCRYPTION_KEY=your_backup_encryption_key
```

### Domain Configuration

1. **DNS Setup**: Point your domain to the server IP
2. **SSL Certificates**: Configured automatically with Let's Encrypt
3. **CDN Setup**: Configure CDN for static assets (optional)

## Production Features

### Security

- **HTTPS Enforcement**: Automatic HTTP to HTTPS redirect
- **Security Headers**: Comprehensive security headers (HSTS, CSP, etc.)
- **Rate Limiting**: Configurable rate limits per IP
- **Authentication**: API key and basic auth for protected endpoints
- **CORS**: Production-safe CORS configuration

### Performance

- **Compression**: Gzip compression for text assets
- **Caching**: Smart caching strategies for different content types
- **CDN Integration**: Support for CDN integration
- **Static Optimization**: Optimized static asset delivery

### Monitoring

- **Health Checks**: Comprehensive health monitoring
- **Metrics**: Prometheus metrics collection
- **Dashboards**: Pre-configured Grafana dashboards
- **Alerting**: Alert rules for critical issues
- **Usage Analytics**: Documentation usage tracking

### Backup & Recovery

- **Automated Backups**: Daily encrypted backups
- **Cloud Storage**: S3-compatible backup storage
- **Disaster Recovery**: Automated restore procedures
- **Data Encryption**: Encrypted backup files

## Operations

### Deployment

```bash
# Deploy latest version
./scripts/deployment/deploy.sh

# Deploy with custom environment
ENVIRONMENT=staging ./scripts/deployment/deploy.sh

# Deploy without rollback
ROLLBACK_ENABLED=false ./scripts/deployment/deploy.sh
```

### Validation

```bash
# Full validation suite
./scripts/deployment/validate.sh

# Validate specific URL
BASE_URL=https://docs.centuryproptax.com ./scripts/deployment/validate.sh
```

### Monitoring

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics` (Prometheus format)
- **Analytics**: `GET /analytics` (Usage statistics)
- **System Status**: `GET /system-status`

### Backup Management

```bash
# Create manual backup
python3 scripts/backup/backup_system.py backup

# List available backups
python3 scripts/backup/backup_system.py list

# Restore from backup
python3 scripts/backup/backup_system.py restore --backup-id BACKUP_ID

# Health check
python3 scripts/backup/backup_system.py health
```

### Scheduled Tasks

Set up cron jobs for automated operations:

```bash
# Daily backups at 2 AM
0 2 * * * /app/scripts/backup/backup_cron.sh

# Weekly health checks
0 8 * * 1 /app/scripts/deployment/validate.sh
```

## Troubleshooting

### Common Issues

1. **Container Won't Start**
   ```bash
   # Check logs
   docker-compose -f docker-compose.production.yml logs app

   # Check configuration
   docker-compose -f docker-compose.production.yml config
   ```

2. **SSL Certificate Issues**
   ```bash
   # Check certificate status
   docker-compose -f docker-compose.production.yml logs traefik

   # Manually trigger certificate renewal
   docker-compose -f docker-compose.production.yml restart traefik
   ```

3. **Database Connection Issues**
   ```bash
   # Check database status
   docker-compose -f docker-compose.production.yml logs db

   # Test database connectivity
   curl http://localhost:8000/health
   ```

4. **Performance Issues**
   ```bash
   # Check system resources
   docker stats

   # Check application metrics
   curl http://localhost:8000/metrics
   ```

### Logs

- **Application Logs**: `/app/logs/app.log`
- **Deployment Logs**: `/tmp/centuryproptax_deployment_*.log`
- **Backup Logs**: `/app/logs/backup.log`
- **Validation Logs**: `/tmp/centuryproptax_validation_*.log`

### Support URLs

- **Documentation Portal**: https://docs.centuryproptax.com/documentation
- **API Documentation**: https://docs.centuryproptax.com/docs
- **Health Status**: https://docs.centuryproptax.com/health
- **Metrics**: https://docs.centuryproptax.com/metrics
- **Grafana Dashboard**: https://docs.centuryproptax.com:3000

## Security Considerations

### Production Checklist

- [ ] Environment variables configured securely
- [ ] SSL certificates properly configured
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] Authentication enabled for admin endpoints
- [ ] Backup encryption configured
- [ ] Monitoring and alerting set up
- [ ] Log rotation configured
- [ ] Database secured with strong passwords
- [ ] API keys rotated regularly

### Security Best Practices

1. **Environment Variables**: Never commit production secrets to version control
2. **SSL/TLS**: Use strong cipher suites and HSTS
3. **Rate Limiting**: Configure appropriate limits for your use case
4. **Monitoring**: Set up alerts for security events
5. **Backups**: Encrypt and test backup restoration regularly
6. **Updates**: Keep containers and dependencies updated

## Performance Tuning

### Optimization Settings

```bash
# Worker processes (adjust based on CPU cores)
WORKER_COUNT=4

# Connection limits
MAX_CONNECTIONS=1000

# Cache settings
CACHE_TTL=3600

# CDN configuration
CDN_URL=https://cdn.centuryproptax.com
```

### Monitoring Performance

- Monitor response times via `/metrics`
- Use Grafana dashboards for visualization
- Set up alerts for performance degradation
- Regular performance validation with validation script

## Support

For deployment support and troubleshooting:

- **Email**: support@centuryproptax.com
- **Documentation**: This README and inline code documentation
- **Logs**: Check deployment and application logs
- **Health Checks**: Use provided validation scripts

## License

Proprietary - Century Property Tax. All rights reserved.