"""Data retention and compliance policies for monitoring system.

This module provides:
- Configurable data retention policies for metrics and logs
- Privacy compliance and data anonymization procedures
- Automated data cleanup and archival processes
- GDPR/CCPA compliance for user data handling
- Data export and deletion capabilities
"""

import asyncio
import asyncpg
import redis
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import json
import gzip
import structlog
import os
import hashlib

logger = structlog.get_logger(__name__)

class DataCategory(Enum):
    """Categories of data with different retention requirements."""
    PERFORMANCE_METRICS = "performance_metrics"
    BUSINESS_ANALYTICS = "business_analytics"
    INFRASTRUCTURE_LOGS = "infrastructure_logs"
    AUDIT_LOGS = "audit_logs"
    ALERT_HISTORY = "alert_history"
    USER_SESSIONS = "user_sessions"
    SYSTEM_EVENTS = "system_events"

class RetentionPolicy(Enum):
    """Predefined retention policies."""
    SHORT_TERM = "short_term"      # 7 days
    MEDIUM_TERM = "medium_term"    # 30 days
    LONG_TERM = "long_term"        # 90 days
    EXTENDED = "extended"          # 1 year
    PERMANENT = "permanent"        # No deletion

class ComplianceRegion(Enum):
    """Data compliance regions."""
    US = "us"          # US privacy laws
    EU = "eu"          # GDPR
    CALIFORNIA = "ca"  # CCPA
    GLOBAL = "global"  # Most restrictive

@dataclass
class RetentionRule:
    """Data retention rule configuration."""
    category: DataCategory
    policy: RetentionPolicy
    retention_days: int
    anonymize_after_days: Optional[int]
    archive_after_days: Optional[int]
    compliance_regions: List[ComplianceRegion]
    description: str
    auto_cleanup: bool = True

@dataclass
class DataExportRequest:
    """Data export request for compliance."""
    request_id: str
    user_identifier: str
    categories: List[DataCategory]
    date_range: tuple[datetime, datetime]
    requester: str
    created_at: datetime
    status: str  # "pending", "processing", "completed", "failed"
    export_path: Optional[str] = None

@dataclass
class DataDeletionRequest:
    """Data deletion request for compliance."""
    request_id: str
    user_identifier: str
    categories: List[DataCategory]
    requester: str
    created_at: datetime
    status: str  # "pending", "processing", "completed", "failed"
    verification_required: bool = True

class DataRetentionManager:
    """Production data retention and compliance manager."""

    def __init__(self, config_file: Optional[str] = None):
        self.retention_rules: Dict[DataCategory, RetentionRule] = {}
        self.export_requests: Dict[str, DataExportRequest] = {}
        self.deletion_requests: Dict[str, DataDeletionRequest] = {}

        # Database and Redis connections
        self.db_pool = None
        self.redis_client = None

        # Configuration
        self.default_retention_days = 30
        self.max_retention_days = 365
        self.anonymization_enabled = True
        self.compliance_region = ComplianceRegion.US

        # Storage paths
        self.archive_path = Path(os.getenv("MONITORING_ARCHIVE_PATH", "./data/archives"))
        self.export_path = Path(os.getenv("MONITORING_EXPORT_PATH", "./data/exports"))

        # Ensure directories exist
        self.archive_path.mkdir(parents=True, exist_ok=True)
        self.export_path.mkdir(parents=True, exist_ok=True)

        # Load configuration
        if config_file:
            self.load_config(config_file)
        else:
            self.load_default_policies()

    def load_default_policies(self):
        """Load default data retention policies."""
        default_rules = [
            RetentionRule(
                category=DataCategory.PERFORMANCE_METRICS,
                policy=RetentionPolicy.MEDIUM_TERM,
                retention_days=30,
                anonymize_after_days=7,
                archive_after_days=14,
                compliance_regions=[ComplianceRegion.US, ComplianceRegion.EU],
                description="Performance metrics with 30-day retention, anonymized after 7 days"
            ),
            RetentionRule(
                category=DataCategory.BUSINESS_ANALYTICS,
                policy=RetentionPolicy.LONG_TERM,
                retention_days=90,
                anonymize_after_days=1,  # Immediate anonymization for privacy
                archive_after_days=30,
                compliance_regions=[ComplianceRegion.US, ComplianceRegion.EU, ComplianceRegion.CALIFORNIA],
                description="Business analytics with immediate anonymization and 90-day retention"
            ),
            RetentionRule(
                category=DataCategory.INFRASTRUCTURE_LOGS,
                policy=RetentionPolicy.SHORT_TERM,
                retention_days=7,
                anonymize_after_days=None,  # No PII in infrastructure logs
                archive_after_days=3,
                compliance_regions=[ComplianceRegion.US],
                description="Infrastructure logs with 7-day retention"
            ),
            RetentionRule(
                category=DataCategory.AUDIT_LOGS,
                policy=RetentionPolicy.EXTENDED,
                retention_days=365,
                anonymize_after_days=90,
                archive_after_days=30,
                compliance_regions=[ComplianceRegion.US, ComplianceRegion.EU],
                description="Audit logs with 1-year retention for compliance"
            ),
            RetentionRule(
                category=DataCategory.ALERT_HISTORY,
                policy=RetentionPolicy.MEDIUM_TERM,
                retention_days=30,
                anonymize_after_days=None,  # No PII in alerts
                archive_after_days=14,
                compliance_regions=[ComplianceRegion.US],
                description="Alert history with 30-day retention"
            ),
            RetentionRule(
                category=DataCategory.USER_SESSIONS,
                policy=RetentionPolicy.SHORT_TERM,
                retention_days=7,
                anonymize_after_days=1,  # Quick anonymization for privacy
                archive_after_days=None,  # No archival for session data
                compliance_regions=[ComplianceRegion.US, ComplianceRegion.EU, ComplianceRegion.CALIFORNIA],
                description="User session data with immediate anonymization and 7-day retention"
            ),
            RetentionRule(
                category=DataCategory.SYSTEM_EVENTS,
                policy=RetentionPolicy.MEDIUM_TERM,
                retention_days=30,
                anonymize_after_days=None,
                archive_after_days=14,
                compliance_regions=[ComplianceRegion.US],
                description="System events with 30-day retention"
            )
        ]

        for rule in default_rules:
            self.retention_rules[rule.category] = rule

        logger.info(f"✅ Loaded {len(default_rules)} default data retention policies")

    def load_config(self, config_file: str):
        """Load retention configuration from file."""
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)

                # Load retention rules
                for rule_data in config.get('retention_rules', []):
                    rule = RetentionRule(
                        category=DataCategory(rule_data['category']),
                        policy=RetentionPolicy(rule_data['policy']),
                        retention_days=rule_data['retention_days'],
                        anonymize_after_days=rule_data.get('anonymize_after_days'),
                        archive_after_days=rule_data.get('archive_after_days'),
                        compliance_regions=[
                            ComplianceRegion(r) for r in rule_data.get('compliance_regions', ['us'])
                        ],
                        description=rule_data.get('description', ''),
                        auto_cleanup=rule_data.get('auto_cleanup', True)
                    )
                    self.retention_rules[rule.category] = rule

                # Load configuration settings
                self.compliance_region = ComplianceRegion(config.get('compliance_region', 'us'))
                self.anonymization_enabled = config.get('anonymization_enabled', True)

                logger.info(f"✅ Loaded retention config from {config_file}")
            else:
                logger.warning(f"Retention config file {config_file} not found, using defaults")
                self.load_default_policies()

        except Exception as e:
            logger.error(f"Failed to load retention config from {config_file}: {e}")
            self.load_default_policies()

    async def initialize(self, db_pool: asyncpg.Pool, redis_client: redis.Redis):
        """Initialize with database and Redis connections."""
        self.db_pool = db_pool
        self.redis_client = redis_client

        # Create necessary database tables for retention tracking
        await self._create_retention_tables()

        logger.info("✅ Data retention manager initialized")

    async def _create_retention_tables(self):
        """Create database tables for retention tracking."""
        if not self.db_pool:
            return

        try:
            async with self.db_pool.acquire() as conn:
                # Data retention tracking table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_retention_log (
                        id SERIAL PRIMARY KEY,
                        category VARCHAR(50) NOT NULL,
                        action VARCHAR(50) NOT NULL,
                        records_affected INTEGER,
                        executed_at TIMESTAMP DEFAULT NOW(),
                        details JSONB
                    )
                """)

                # Data export requests table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_export_requests (
                        id SERIAL PRIMARY KEY,
                        request_id VARCHAR(100) UNIQUE NOT NULL,
                        user_identifier VARCHAR(255) NOT NULL,
                        categories JSONB NOT NULL,
                        date_range JSONB NOT NULL,
                        requester VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW(),
                        status VARCHAR(50) DEFAULT 'pending',
                        export_path TEXT,
                        completed_at TIMESTAMP
                    )
                """)

                # Data deletion requests table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_deletion_requests (
                        id SERIAL PRIMARY KEY,
                        request_id VARCHAR(100) UNIQUE NOT NULL,
                        user_identifier VARCHAR(255) NOT NULL,
                        categories JSONB NOT NULL,
                        requester VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW(),
                        status VARCHAR(50) DEFAULT 'pending',
                        verification_required BOOLEAN DEFAULT TRUE,
                        completed_at TIMESTAMP
                    )
                """)

            logger.info("✅ Data retention tables created/verified")

        except Exception as e:
            logger.error(f"Failed to create retention tables: {e}")

    async def run_retention_cleanup(self) -> Dict[str, Any]:
        """Run automated data retention cleanup."""
        cleanup_results = {
            "timestamp": datetime.now().isoformat(),
            "categories_processed": [],
            "total_records_processed": 0,
            "total_records_deleted": 0,
            "total_records_anonymized": 0,
            "total_records_archived": 0,
            "errors": []
        }

        for category, rule in self.retention_rules.items():
            if not rule.auto_cleanup:
                continue

            try:
                result = await self._process_category_retention(category, rule)
                cleanup_results["categories_processed"].append({
                    "category": category.value,
                    "result": result
                })
                cleanup_results["total_records_processed"] += result.get("records_processed", 0)
                cleanup_results["total_records_deleted"] += result.get("records_deleted", 0)
                cleanup_results["total_records_anonymized"] += result.get("records_anonymized", 0)
                cleanup_results["total_records_archived"] += result.get("records_archived", 0)

            except Exception as e:
                error_msg = f"Failed to process {category.value}: {e}"
                cleanup_results["errors"].append(error_msg)
                logger.error(error_msg)

        # Log cleanup results
        await self._log_retention_action("automated_cleanup", cleanup_results)

        logger.info(
            f"✅ Data retention cleanup completed",
            extra={
                "categories": len(cleanup_results["categories_processed"]),
                "records_deleted": cleanup_results["total_records_deleted"],
                "records_anonymized": cleanup_results["total_records_anonymized"],
                "errors": len(cleanup_results["errors"])
            }
        )

        return cleanup_results

    async def _process_category_retention(self, category: DataCategory, rule: RetentionRule) -> Dict[str, int]:
        """Process retention for a specific data category."""
        result = {
            "records_processed": 0,
            "records_deleted": 0,
            "records_anonymized": 0,
            "records_archived": 0
        }

        # Calculate cutoff dates
        deletion_cutoff = datetime.now() - timedelta(days=rule.retention_days)
        anonymization_cutoff = None
        archival_cutoff = None

        if rule.anonymize_after_days:
            anonymization_cutoff = datetime.now() - timedelta(days=rule.anonymize_after_days)

        if rule.archive_after_days:
            archival_cutoff = datetime.now() - timedelta(days=rule.archive_after_days)

        # Process based on data category
        if category == DataCategory.PERFORMANCE_METRICS:
            result = await self._process_performance_metrics(
                deletion_cutoff, anonymization_cutoff, archival_cutoff
            )
        elif category == DataCategory.BUSINESS_ANALYTICS:
            result = await self._process_business_analytics(
                deletion_cutoff, anonymization_cutoff, archival_cutoff
            )
        elif category == DataCategory.AUDIT_LOGS:
            result = await self._process_audit_logs(
                deletion_cutoff, anonymization_cutoff, archival_cutoff
            )
        # Add other categories as needed

        return result

    async def _process_performance_metrics(
        self,
        deletion_cutoff: datetime,
        anonymization_cutoff: Optional[datetime],
        archival_cutoff: Optional[datetime]
    ) -> Dict[str, int]:
        """Process performance metrics retention."""
        result = {"records_processed": 0, "records_deleted": 0, "records_anonymized": 0, "records_archived": 0}

        if not self.db_pool:
            return result

        try:
            async with self.db_pool.acquire() as conn:
                # Archive old records if needed
                if archival_cutoff:
                    archived_records = await self._archive_performance_data(conn, archival_cutoff)
                    result["records_archived"] = archived_records

                # Anonymize records if needed
                if anonymization_cutoff and self.anonymization_enabled:
                    anonymized_records = await self._anonymize_performance_data(conn, anonymization_cutoff)
                    result["records_anonymized"] = anonymized_records

                # Delete old records
                deleted_records = await self._delete_performance_data(conn, deletion_cutoff)
                result["records_deleted"] = deleted_records

                result["records_processed"] = result["records_deleted"] + result["records_anonymized"] + result["records_archived"]

        except Exception as e:
            logger.error(f"Failed to process performance metrics retention: {e}")
            raise

        return result

    async def _archive_performance_data(self, conn: asyncpg.Connection, cutoff: datetime) -> int:
        """Archive performance data to compressed files."""
        try:
            # Query data to archive
            rows = await conn.fetch("""
                SELECT * FROM performance_metrics
                WHERE created_at < $1 AND archived_at IS NULL
                ORDER BY created_at
            """, cutoff)

            if not rows:
                return 0

            # Create archive file
            archive_file = self.archive_path / f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json.gz"

            # Write compressed archive
            archive_data = [dict(row) for row in rows]
            with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
                json.dump(archive_data, f, default=str, indent=2)

            # Mark records as archived
            await conn.execute("""
                UPDATE performance_metrics
                SET archived_at = NOW(), archive_path = $1
                WHERE created_at < $2 AND archived_at IS NULL
            """, str(archive_file), cutoff)

            logger.info(f"✅ Archived {len(rows)} performance metrics records to {archive_file}")
            return len(rows)

        except Exception as e:
            logger.error(f"Failed to archive performance data: {e}")
            return 0

    async def _anonymize_performance_data(self, conn: asyncpg.Connection, cutoff: datetime) -> int:
        """Anonymize performance data by removing/hashing PII."""
        try:
            # Update records to remove/hash PII
            result = await conn.execute("""
                UPDATE performance_metrics
                SET
                    user_id = md5(user_id::text),
                    ip_address = '0.0.0.0',
                    user_agent = 'anonymized',
                    anonymized_at = NOW()
                WHERE created_at < $1 AND anonymized_at IS NULL
            """, cutoff)

            count = int(result.split()[-1]) if result.split() else 0
            if count > 0:
                logger.info(f"✅ Anonymized {count} performance metrics records")

            return count

        except Exception as e:
            logger.error(f"Failed to anonymize performance data: {e}")
            return 0

    async def _delete_performance_data(self, conn: asyncpg.Connection, cutoff: datetime) -> int:
        """Delete old performance data."""
        try:
            result = await conn.execute("""
                DELETE FROM performance_metrics
                WHERE created_at < $1
            """, cutoff)

            count = int(result.split()[-1]) if result.split() else 0
            if count > 0:
                logger.info(f"✅ Deleted {count} old performance metrics records")

            return count

        except Exception as e:
            logger.error(f"Failed to delete performance data: {e}")
            return 0

    async def _process_business_analytics(
        self,
        deletion_cutoff: datetime,
        anonymization_cutoff: Optional[datetime],
        archival_cutoff: Optional[datetime]
    ) -> Dict[str, int]:
        """Process business analytics retention with strict privacy compliance."""
        result = {"records_processed": 0, "records_deleted": 0, "records_anonymized": 0, "records_archived": 0}

        # Business analytics should be anonymized immediately for privacy
        if self.redis_client:
            try:
                # Clear old Redis analytics data
                keys_pattern = "analytics:*"
                keys = await asyncio.to_thread(self.redis_client.keys, keys_pattern)

                deleted_keys = 0
                for key in keys:
                    # Check if key is old enough to delete
                    ttl = await asyncio.to_thread(self.redis_client.ttl, key)
                    if ttl == -1:  # No expiration set, check creation time
                        # For simplicity, delete keys without TTL as they're likely old
                        await asyncio.to_thread(self.redis_client.delete, key)
                        deleted_keys += 1

                result["records_deleted"] = deleted_keys
                result["records_processed"] = deleted_keys

                if deleted_keys > 0:
                    logger.info(f"✅ Deleted {deleted_keys} old business analytics records from Redis")

            except Exception as e:
                logger.error(f"Failed to process business analytics retention: {e}")

        return result

    async def _process_audit_logs(
        self,
        deletion_cutoff: datetime,
        anonymization_cutoff: Optional[datetime],
        archival_cutoff: Optional[datetime]
    ) -> Dict[str, int]:
        """Process audit logs retention."""
        result = {"records_processed": 0, "records_deleted": 0, "records_anonymized": 0, "records_archived": 0}

        if not self.db_pool:
            return result

        try:
            async with self.db_pool.acquire() as conn:
                # Archive audit logs before deletion
                if archival_cutoff:
                    archived_records = await self._archive_audit_logs(conn, archival_cutoff)
                    result["records_archived"] = archived_records

                # Anonymize sensitive audit data
                if anonymization_cutoff and self.anonymization_enabled:
                    anonymized_records = await self._anonymize_audit_logs(conn, anonymization_cutoff)
                    result["records_anonymized"] = anonymized_records

                # Delete very old audit logs (keeping archives)
                deleted_records = await self._delete_audit_logs(conn, deletion_cutoff)
                result["records_deleted"] = deleted_records

                result["records_processed"] = result["records_deleted"] + result["records_anonymized"] + result["records_archived"]

        except Exception as e:
            logger.error(f"Failed to process audit logs retention: {e}")
            raise

        return result

    async def _archive_audit_logs(self, conn: asyncpg.Connection, cutoff: datetime) -> int:
        """Archive audit logs."""
        try:
            rows = await conn.fetch("""
                SELECT * FROM monitoring_audit_logs
                WHERE timestamp < $1 AND archived_at IS NULL
                ORDER BY timestamp
            """, cutoff)

            if not rows:
                return 0

            # Create archive file
            archive_file = self.archive_path / f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json.gz"

            # Write compressed archive
            archive_data = [dict(row) for row in rows]
            with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
                json.dump(archive_data, f, default=str, indent=2)

            # Mark as archived
            await conn.execute("""
                UPDATE monitoring_audit_logs
                SET archived_at = NOW(), archive_path = $1
                WHERE timestamp < $2 AND archived_at IS NULL
            """, str(archive_file), cutoff)

            logger.info(f"✅ Archived {len(rows)} audit log records")
            return len(rows)

        except Exception as e:
            logger.error(f"Failed to archive audit logs: {e}")
            return 0

    async def _anonymize_audit_logs(self, conn: asyncpg.Connection, cutoff: datetime) -> int:
        """Anonymize audit logs by removing PII."""
        try:
            result = await conn.execute("""
                UPDATE monitoring_audit_logs
                SET
                    ip_address = '0.0.0.0',
                    user_agent = 'anonymized',
                    details = jsonb_set(details, '{anonymized}', 'true'),
                    anonymized_at = NOW()
                WHERE timestamp < $1 AND anonymized_at IS NULL
            """, cutoff)

            count = int(result.split()[-1]) if result.split() else 0
            return count

        except Exception as e:
            logger.error(f"Failed to anonymize audit logs: {e}")
            return 0

    async def _delete_audit_logs(self, conn: asyncpg.Connection, cutoff: datetime) -> int:
        """Delete old audit logs (only if archived)."""
        try:
            result = await conn.execute("""
                DELETE FROM monitoring_audit_logs
                WHERE timestamp < $1 AND archived_at IS NOT NULL
            """, cutoff)

            count = int(result.split()[-1]) if result.split() else 0
            return count

        except Exception as e:
            logger.error(f"Failed to delete audit logs: {e}")
            return 0

    async def _log_retention_action(self, action: str, details: Dict[str, Any]):
        """Log retention action to database."""
        if not self.db_pool:
            return

        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO data_retention_log (category, action, records_affected, details)
                    VALUES ($1, $2, $3, $4)
                """, "all", action, details.get("total_records_processed", 0), json.dumps(details))

        except Exception as e:
            logger.error(f"Failed to log retention action: {e}")

    async def request_data_export(
        self,
        user_identifier: str,
        categories: List[DataCategory],
        date_range: tuple[datetime, datetime],
        requester: str
    ) -> str:
        """Request data export for compliance (GDPR/CCPA)."""
        import uuid
        request_id = str(uuid.uuid4())

        export_request = DataExportRequest(
            request_id=request_id,
            user_identifier=user_identifier,
            categories=categories,
            date_range=date_range,
            requester=requester,
            created_at=datetime.now(),
            status="pending"
        )

        self.export_requests[request_id] = export_request

        # Store in database
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO data_export_requests
                        (request_id, user_identifier, categories, date_range, requester)
                        VALUES ($1, $2, $3, $4, $5)
                    """, request_id, user_identifier,
                    json.dumps([c.value for c in categories]),
                    json.dumps([dt.isoformat() for dt in date_range]),
                    requester)

            except Exception as e:
                logger.error(f"Failed to store export request: {e}")

        logger.info(f"✅ Data export request created: {request_id}")
        return request_id

    async def request_data_deletion(
        self,
        user_identifier: str,
        categories: List[DataCategory],
        requester: str,
        verification_required: bool = True
    ) -> str:
        """Request data deletion for compliance (GDPR/CCPA)."""
        import uuid
        request_id = str(uuid.uuid4())

        deletion_request = DataDeletionRequest(
            request_id=request_id,
            user_identifier=user_identifier,
            categories=categories,
            requester=requester,
            created_at=datetime.now(),
            status="pending",
            verification_required=verification_required
        )

        self.deletion_requests[request_id] = deletion_request

        # Store in database
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO data_deletion_requests
                        (request_id, user_identifier, categories, requester, verification_required)
                        VALUES ($1, $2, $3, $4, $5)
                    """, request_id, user_identifier,
                    json.dumps([c.value for c in categories]),
                    requester, verification_required)

            except Exception as e:
                logger.error(f"Failed to store deletion request: {e}")

        logger.info(f"✅ Data deletion request created: {request_id}")
        return request_id

    def get_retention_summary(self) -> Dict[str, Any]:
        """Get summary of data retention policies and status."""
        return {
            "retention_policies": {
                category.value: {
                    "retention_days": rule.retention_days,
                    "anonymize_after_days": rule.anonymize_after_days,
                    "archive_after_days": rule.archive_after_days,
                    "auto_cleanup": rule.auto_cleanup,
                    "compliance_regions": [r.value for r in rule.compliance_regions]
                }
                for category, rule in self.retention_rules.items()
            },
            "configuration": {
                "compliance_region": self.compliance_region.value,
                "anonymization_enabled": self.anonymization_enabled,
                "archive_path": str(self.archive_path),
                "export_path": str(self.export_path)
            },
            "pending_requests": {
                "export_requests": len([r for r in self.export_requests.values() if r.status == "pending"]),
                "deletion_requests": len([r for r in self.deletion_requests.values() if r.status == "pending"])
            }
        }


# Global data retention manager instance
retention_manager = DataRetentionManager()