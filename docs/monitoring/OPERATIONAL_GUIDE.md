# Century Property Tax - Production Monitoring Operational Guide

## Overview

This guide provides comprehensive operational procedures for managing the Century Property Tax production monitoring system. The monitoring system includes performance dashboards, business analytics, infrastructure health monitoring, and automated alerting.

## System Architecture

### Components
- **Performance Dashboard**: Real-time system metrics and response times
- **Business Analytics**: Privacy-compliant user engagement and conversion tracking
- **Infrastructure Monitoring**: Database, Redis, and external API health checks
- **Alert Management**: Multi-channel notifications with escalation procedures
- **Access Control**: Role-based authentication and authorization
- **Data Retention**: Automated cleanup and compliance policies

### Key URLs
- Dashboard Interface: `https://api.centuryproptax.com/monitoring/dashboard`
- Performance API: `https://api.centuryproptax.com/monitoring/performance`
- Business Analytics: `https://api.centuryproptax.com/monitoring/business`
- Infrastructure Health: `https://api.centuryproptax.com/monitoring/infrastructure`
- Alert Configuration: `https://api.centuryproptax.com/monitoring/alerts`

## Authentication and Access Control

### User Roles

#### Viewer
- **Permissions**: Read-only access to all dashboards
- **Use Case**: Business stakeholders, executives
- **Access**: View performance, business, and infrastructure metrics

#### Operator
- **Permissions**: View dashboards + acknowledge/suppress alerts
- **Use Case**: Operations team, on-call engineers
- **Access**: All viewer permissions + alert management

#### Admin
- **Permissions**: Full system management
- **Use Case**: DevOps engineers, system administrators
- **Access**: All permissions including user management and configuration

#### System
- **Permissions**: Programmatic access for automation
- **Use Case**: CI/CD pipelines, external monitoring tools
- **Access**: API-based monitoring data access

### Authentication Methods

#### JWT Tokens (Users)
```bash
# Login to get JWT token
curl -X POST https://api.centuryproptax.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "operator", "password": "your_password"}'

# Use token in Authorization header
curl -H "Authorization: Bearer <jwt_token>" \
  https://api.centuryproptax.com/monitoring/performance
```

#### API Keys (Programmatic Access)
```bash
# Use API key in Authorization header
curl -H "Authorization: Bearer cpt_monitor_<api_key>" \
  https://api.centuryproptax.com/monitoring/infrastructure
```

## Daily Operations

### Morning Health Check
1. **Access Dashboard**: Navigate to monitoring dashboard
2. **Review Overnight Alerts**: Check for any critical alerts
3. **Verify System Health**: Confirm all services are healthy
4. **Check Performance Metrics**: Review response times and error rates
5. **Business Metrics Review**: Check user engagement and conversion rates

### Performance Monitoring
- **Response Time Targets**: <2s average, <5s 95th percentile
- **Error Rate Targets**: <1% for critical endpoints
- **Availability Targets**: >99.9% uptime
- **Resource Usage**: CPU <70%, Memory <80%

### Business Analytics Review
- **Conversion Tracking**: Monitor property tax inquiry completion rates
- **User Engagement**: Track session duration and satisfaction scores
- **Peak Usage**: Identify traffic patterns and capacity planning needs
- **Privacy Compliance**: Ensure all data is properly anonymized

## Alert Management

### Alert Severity Levels

#### Critical (🔥)
- **Response Time**: Immediate (within 5 minutes)
- **Examples**: Database down, high error rate (>5%), system unavailable
- **Notifications**: Email, Slack, webhook, escalation to on-call
- **Actions**: Immediate investigation and resolution required

#### Warning (⚠️)
- **Response Time**: Within 15 minutes
- **Examples**: High response time, high memory usage, Redis issues
- **Notifications**: Email, Slack
- **Actions**: Monitor and investigate if persistent

#### Info (ℹ️)
- **Response Time**: Next business day
- **Examples**: SSL certificate expiring, disk space low
- **Notifications**: Email
- **Actions**: Schedule maintenance or updates

### Alert Response Procedures

#### 1. Alert Acknowledgment
```bash
# Acknowledge alert via API
curl -X POST "https://api.centuryproptax.com/monitoring/alerts/high_error_rate/acknowledge" \
  -H "Authorization: Bearer <token>" \
  -d '{"acknowledged_by": "operator_name"}'
```

#### 2. Investigation Steps
1. **Check Dashboard**: Review all related metrics
2. **Verify Issue**: Confirm the alert is not a false positive
3. **Check Logs**: Review application and system logs
4. **Assess Impact**: Determine user impact and business criticality
5. **Begin Resolution**: Follow appropriate runbook procedures

#### 3. Escalation Process
- **Level 1**: Initial responder (15 minutes)
- **Level 2**: Senior engineer (30 minutes)
- **Level 3**: Engineering manager (60 minutes)
- **Level 4**: CTO/Executive team (24/7 for critical issues)

### Common Alert Scenarios

#### High Response Time
1. **Check Database**: Verify database performance and connections
2. **Review Traffic**: Look for traffic spikes or unusual patterns
3. **Check Resources**: Monitor CPU, memory, and disk usage
4. **Scale if Needed**: Increase server resources or replicas

#### High Error Rate
1. **Check Logs**: Review application error logs
2. **Database Issues**: Verify database connectivity and performance
3. **External APIs**: Check third-party service status
4. **Code Issues**: Look for recent deployments or changes

#### Database Connection Failure
1. **Immediate Action**: Check database service status
2. **Connection Pool**: Verify connection pool configuration
3. **Network Issues**: Test network connectivity
4. **Failover**: Execute database failover if needed

## Infrastructure Monitoring

### Database Health
- **Connection Pool**: Monitor active/idle connections
- **Query Performance**: Track slow queries and response times
- **Resource Usage**: Monitor CPU, memory, and disk I/O
- **Backup Status**: Verify backup completion and integrity

### Redis Health
- **Memory Usage**: Monitor memory consumption and eviction
- **Connection Count**: Track active connections
- **Response Time**: Monitor operation performance
- **Persistence**: Verify data persistence settings

### External API Dependencies
- **Response Times**: Monitor third-party API performance
- **Error Rates**: Track API failures and timeouts
- **Rate Limits**: Monitor API quota usage
- **Fallback Systems**: Verify fallback mechanisms

## Data Management and Compliance

### Data Retention Policies
- **Performance Metrics**: 30 days (anonymized after 7 days)
- **Business Analytics**: 90 days (immediately anonymized)
- **Infrastructure Logs**: 7 days
- **Audit Logs**: 365 days (anonymized after 90 days)
- **Alert History**: 30 days

### Privacy Compliance
- **Data Anonymization**: Automatic PII removal/hashing
- **User Consent**: Respect user privacy preferences
- **Data Export**: Support GDPR/CCPA data export requests
- **Data Deletion**: Honor right-to-be-forgotten requests

### Backup and Archival
- **Automated Archival**: Old data compressed and archived
- **Archive Location**: `/data/archives/` with retention policies
- **Backup Verification**: Regular backup integrity checks
- **Disaster Recovery**: Off-site backup storage

## Troubleshooting Guide

### Dashboard Not Loading
1. **Check Service Status**: Verify API service is running
2. **Authentication**: Ensure valid credentials/tokens
3. **Network**: Test connectivity to monitoring endpoints
4. **Browser Cache**: Clear cache and cookies
5. **Recent Changes**: Check for recent deployments

### Missing Metrics
1. **Middleware**: Verify monitoring middleware is active
2. **Database**: Check database connectivity and permissions
3. **Redis**: Verify Redis connection and data
4. **Collection**: Ensure metrics collection is enabled

### False Alerts
1. **Thresholds**: Review alert threshold configuration
2. **Data Quality**: Check for incomplete or corrupted metrics
3. **Timing**: Verify alert evaluation intervals
4. **Suppression**: Temporarily suppress problematic alerts

### Performance Issues
1. **Resource Usage**: Check system resource consumption
2. **Database Load**: Monitor database query performance
3. **Network**: Check network latency and bandwidth
4. **Scaling**: Consider horizontal or vertical scaling

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily
- [ ] Review overnight alerts and incidents
- [ ] Check system health dashboard
- [ ] Verify backup completion
- [ ] Monitor performance trends

#### Weekly
- [ ] Review alert configurations and thresholds
- [ ] Analyze performance trends and capacity
- [ ] Clean up old alerts and notifications
- [ ] Update runbook procedures

#### Monthly
- [ ] Review data retention and cleanup
- [ ] Audit user access and permissions
- [ ] Performance optimization review
- [ ] Update monitoring documentation

#### Quarterly
- [ ] Comprehensive security audit
- [ ] Disaster recovery testing
- [ ] Capacity planning review
- [ ] Training needs assessment

### System Updates
1. **Pre-Update**: Create monitoring system backup
2. **Staging**: Test updates in staging environment
3. **Maintenance Window**: Schedule during low-traffic periods
4. **Rollback Plan**: Prepare rollback procedures
5. **Post-Update**: Verify all monitoring functions

## Emergency Procedures

### System-Wide Outage
1. **Immediate**: Activate incident response team
2. **Communication**: Notify stakeholders via emergency channels
3. **Assessment**: Determine scope and impact
4. **Recovery**: Execute disaster recovery procedures
5. **Post-Mortem**: Conduct incident analysis

### Data Breach Response
1. **Containment**: Isolate affected systems
2. **Assessment**: Determine data exposure scope
3. **Notification**: Follow legal notification requirements
4. **Recovery**: Restore secure operations
5. **Prevention**: Implement additional security measures

### Key Contacts
- **Engineering On-Call**: +1-XXX-XXX-XXXX
- **DevOps Lead**: devops@centuryproptax.com
- **Security Team**: security@centuryproptax.com
- **Executive Escalation**: exec@centuryproptax.com

## Performance Tuning

### Optimization Strategies
1. **Database Indexing**: Optimize monitoring queries
2. **Caching**: Implement intelligent caching layers
3. **Data Aggregation**: Pre-aggregate commonly used metrics
4. **Query Optimization**: Minimize database load
5. **Resource Scaling**: Right-size monitoring infrastructure

### Monitoring Best Practices
1. **Meaningful Metrics**: Focus on actionable metrics
2. **Appropriate Thresholds**: Set realistic alert thresholds
3. **Reduce Noise**: Minimize false positive alerts
4. **Documentation**: Keep runbooks current
5. **Training**: Ensure team knowledge is up-to-date

## Integration with External Tools

### Prometheus
```yaml
# Scrape configuration
scrape_configs:
  - job_name: 'centuryproptax-monitoring'
    static_configs:
      - targets: ['api.centuryproptax.com:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Grafana
- Import dashboard configuration from `/monitoring/grafana/dashboards/`
- Configure data sources for Prometheus metrics
- Set up custom alerts and notifications

### PagerDuty
```json
{
  "integration_key": "your_pagerduty_key",
  "escalation_policy": "monitoring_escalation",
  "notification_channels": ["webhook"]
}
```

## Appendix

### Useful Commands
```bash
# Check monitoring service status
systemctl status centuryproptax-monitoring

# View recent logs
journalctl -u centuryproptax-monitoring -f

# Manual performance validation
python scripts/validate_monitoring_performance.py

# Data retention cleanup
python -m src.core.data_retention --cleanup

# User management
python -m src.core.monitoring_auth --create-user operator ops@company.com
```

### Environment Variables
```bash
# Authentication
MONITORING_SECRET=your_monitoring_secret
MONITORING_JWT_SECRET=your_jwt_secret

# Database
DATABASE_URL=postgresql://user:pass@localhost/centuryproptax
REDIS_URL=redis://localhost:6379

# Notifications
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=alerts@centuryproptax.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Storage
MONITORING_ARCHIVE_PATH=/data/archives
MONITORING_EXPORT_PATH=/data/exports
```

### Support Resources
- **Documentation**: https://docs.centuryproptax.com/monitoring/
- **Runbooks**: https://docs.centuryproptax.com/runbooks/
- **Status Page**: https://status.centuryproptax.com
- **Internal Wiki**: https://wiki.centuryproptax.com/monitoring/

---

**Last Updated**: $(date)
**Version**: 1.0
**Owner**: DevOps Team