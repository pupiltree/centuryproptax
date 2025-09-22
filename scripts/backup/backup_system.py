#!/usr/bin/env python3
"""Comprehensive backup and disaster recovery system for Century Property Tax Documentation Portal.

This script provides automated backup functionality including:
- Database backups with encryption
- Static file backups to cloud storage
- Configuration backups
- Automated restoration procedures
- Health checks and validation
"""

import os
import sys
import gzip
import shutil
import tarfile
import subprocess
import boto3
import psycopg2
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import json
import hashlib
from cryptography.fernet import Fernet
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BackupManager:
    """Comprehensive backup and disaster recovery manager."""

    def __init__(self):
        self.backup_dir = Path("/app/backups")
        self.backup_dir.mkdir(exist_ok=True)

        # Configuration from environment
        self.db_url = os.getenv('DATABASE_URL')
        self.redis_url = os.getenv('REDIS_URL')
        self.s3_bucket = os.getenv('S3_BACKUP_BUCKET')
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.backup_retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
        self.encryption_key = os.getenv('BACKUP_ENCRYPTION_KEY')

        # Initialize encryption
        if self.encryption_key:
            self.cipher = Fernet(self.encryption_key.encode())
        else:
            # Generate a new key if not provided
            self.encryption_key = Fernet.generate_key().decode()
            self.cipher = Fernet(self.encryption_key.encode())
            logger.warning("Generated new encryption key. Store this securely!")
            logger.warning(f"BACKUP_ENCRYPTION_KEY={self.encryption_key}")

        # Initialize AWS S3 client
        if self.aws_access_key and self.aws_secret_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key
            )
        else:
            self.s3_client = None
            logger.warning("AWS credentials not configured. S3 backups disabled.")

    def create_full_backup(self) -> Dict[str, str]:
        """Create a complete system backup."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_id = f"centuryproptax_backup_{timestamp}"

        logger.info(f"Starting full backup: {backup_id}")

        backup_manifest = {
            'backup_id': backup_id,
            'timestamp': timestamp,
            'components': {},
            'checksums': {},
            'size_bytes': 0
        }

        try:
            # 1. Database backup
            db_backup_file = self._backup_database(backup_id)
            if db_backup_file:
                backup_manifest['components']['database'] = str(db_backup_file)
                backup_manifest['checksums']['database'] = self._calculate_checksum(db_backup_file)
                backup_manifest['size_bytes'] += db_backup_file.stat().st_size

            # 2. Redis backup
            redis_backup_file = self._backup_redis(backup_id)
            if redis_backup_file:
                backup_manifest['components']['redis'] = str(redis_backup_file)
                backup_manifest['checksums']['redis'] = self._calculate_checksum(redis_backup_file)
                backup_manifest['size_bytes'] += redis_backup_file.stat().st_size

            # 3. Static files backup
            static_backup_file = self._backup_static_files(backup_id)
            if static_backup_file:
                backup_manifest['components']['static_files'] = str(static_backup_file)
                backup_manifest['checksums']['static_files'] = self._calculate_checksum(static_backup_file)
                backup_manifest['size_bytes'] += static_backup_file.stat().st_size

            # 4. Configuration backup
            config_backup_file = self._backup_configuration(backup_id)
            if config_backup_file:
                backup_manifest['components']['configuration'] = str(config_backup_file)
                backup_manifest['checksums']['configuration'] = self._calculate_checksum(config_backup_file)
                backup_manifest['size_bytes'] += config_backup_file.stat().st_size

            # 5. Application logs backup
            logs_backup_file = self._backup_logs(backup_id)
            if logs_backup_file:
                backup_manifest['components']['logs'] = str(logs_backup_file)
                backup_manifest['checksums']['logs'] = self._calculate_checksum(logs_backup_file)
                backup_manifest['size_bytes'] += logs_backup_file.stat().st_size

            # Save backup manifest
            manifest_file = self.backup_dir / f"{backup_id}_manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(backup_manifest, f, indent=2)

            # Upload to S3 if configured
            if self.s3_client:
                self._upload_to_s3(backup_id, backup_manifest)

            # Clean old backups
            self._cleanup_old_backups()

            logger.info(f"Full backup completed: {backup_id}")
            logger.info(f"Total size: {backup_manifest['size_bytes'] / 1024 / 1024:.2f} MB")

            return backup_manifest

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise

    def _backup_database(self, backup_id: str) -> Optional[Path]:
        """Backup PostgreSQL database."""
        if not self.db_url:
            logger.warning("Database URL not configured. Skipping database backup.")
            return None

        logger.info("Backing up database...")

        # Parse database URL
        from urllib.parse import urlparse
        parsed = urlparse(self.db_url)

        backup_file = self.backup_dir / f"{backup_id}_database.sql.gz"

        try:
            # Create database dump
            pg_dump_cmd = [
                'pg_dump',
                f'--host={parsed.hostname}',
                f'--port={parsed.port or 5432}',
                f'--username={parsed.username}',
                f'--dbname={parsed.path[1:]}',  # Remove leading slash
                '--no-password',
                '--verbose',
                '--clean',
                '--if-exists',
                '--create'
            ]

            # Set password via environment
            env = os.environ.copy()
            env['PGPASSWORD'] = parsed.password

            # Run pg_dump and compress
            with gzip.open(backup_file, 'wt') as f:
                result = subprocess.run(
                    pg_dump_cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    check=True,
                    text=True
                )

            # Encrypt the backup
            encrypted_file = self._encrypt_file(backup_file)
            backup_file.unlink()  # Remove unencrypted file

            logger.info(f"Database backup completed: {encrypted_file}")
            return encrypted_file

        except subprocess.CalledProcessError as e:
            logger.error(f"Database backup failed: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return None

    def _backup_redis(self, backup_id: str) -> Optional[Path]:
        """Backup Redis data."""
        if not self.redis_url:
            logger.warning("Redis URL not configured. Skipping Redis backup.")
            return None

        logger.info("Backing up Redis...")

        try:
            # Connect to Redis
            r = redis.from_url(self.redis_url)

            # Get all keys
            keys = r.keys('*')

            backup_data = {}
            for key in keys:
                key_str = key.decode('utf-8')
                key_type = r.type(key).decode('utf-8')

                if key_type == 'string':
                    backup_data[key_str] = {
                        'type': 'string',
                        'value': r.get(key).decode('utf-8')
                    }
                elif key_type == 'hash':
                    backup_data[key_str] = {
                        'type': 'hash',
                        'value': {k.decode('utf-8'): v.decode('utf-8') for k, v in r.hgetall(key).items()}
                    }
                elif key_type == 'list':
                    backup_data[key_str] = {
                        'type': 'list',
                        'value': [item.decode('utf-8') for item in r.lrange(key, 0, -1)]
                    }
                elif key_type == 'set':
                    backup_data[key_str] = {
                        'type': 'set',
                        'value': [item.decode('utf-8') for item in r.smembers(key)]
                    }
                elif key_type == 'zset':
                    backup_data[key_str] = {
                        'type': 'zset',
                        'value': [(member.decode('utf-8'), score) for member, score in r.zrange(key, 0, -1, withscores=True)]
                    }

            # Save to file
            backup_file = self.backup_dir / f"{backup_id}_redis.json.gz"

            with gzip.open(backup_file, 'wt') as f:
                json.dump(backup_data, f, indent=2)

            # Encrypt the backup
            encrypted_file = self._encrypt_file(backup_file)
            backup_file.unlink()  # Remove unencrypted file

            logger.info(f"Redis backup completed: {encrypted_file}")
            return encrypted_file

        except Exception as e:
            logger.error(f"Redis backup failed: {e}")
            return None

    def _backup_static_files(self, backup_id: str) -> Optional[Path]:
        """Backup static files and documentation."""
        logger.info("Backing up static files...")

        static_dirs = [
            '/app/docs/static',
            '/app/docs/examples',
            '/app/static'
        ]

        backup_file = self.backup_dir / f"{backup_id}_static.tar.gz"

        try:
            with tarfile.open(backup_file, 'w:gz') as tar:
                for static_dir in static_dirs:
                    if os.path.exists(static_dir):
                        tar.add(static_dir, arcname=os.path.basename(static_dir))

            # Encrypt the backup
            encrypted_file = self._encrypt_file(backup_file)
            backup_file.unlink()  # Remove unencrypted file

            logger.info(f"Static files backup completed: {encrypted_file}")
            return encrypted_file

        except Exception as e:
            logger.error(f"Static files backup failed: {e}")
            return None

    def _backup_configuration(self, backup_id: str) -> Optional[Path]:
        """Backup configuration files."""
        logger.info("Backing up configuration...")

        config_files = [
            '/app/.env.production',
            '/app/docker-compose.production.yml',
            '/app/monitoring/prometheus.yml',
            '/app/monitoring/alert_rules.yml'
        ]

        backup_file = self.backup_dir / f"{backup_id}_config.tar.gz"

        try:
            with tarfile.open(backup_file, 'w:gz') as tar:
                for config_file in config_files:
                    if os.path.exists(config_file):
                        tar.add(config_file, arcname=os.path.basename(config_file))

            # Encrypt the backup
            encrypted_file = self._encrypt_file(backup_file)
            backup_file.unlink()  # Remove unencrypted file

            logger.info(f"Configuration backup completed: {encrypted_file}")
            return encrypted_file

        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
            return None

    def _backup_logs(self, backup_id: str) -> Optional[Path]:
        """Backup application logs."""
        logger.info("Backing up logs...")

        logs_dir = '/app/logs'
        backup_file = self.backup_dir / f"{backup_id}_logs.tar.gz"

        try:
            if os.path.exists(logs_dir):
                with tarfile.open(backup_file, 'w:gz') as tar:
                    tar.add(logs_dir, arcname='logs')

                # Encrypt the backup
                encrypted_file = self._encrypt_file(backup_file)
                backup_file.unlink()  # Remove unencrypted file

                logger.info(f"Logs backup completed: {encrypted_file}")
                return encrypted_file
            else:
                logger.warning("Logs directory not found. Skipping logs backup.")
                return None

        except Exception as e:
            logger.error(f"Logs backup failed: {e}")
            return None

    def _encrypt_file(self, file_path: Path) -> Path:
        """Encrypt a backup file."""
        encrypted_file = file_path.with_suffix(file_path.suffix + '.enc')

        with open(file_path, 'rb') as infile:
            with open(encrypted_file, 'wb') as outfile:
                outfile.write(self.cipher.encrypt(infile.read()))

        return encrypted_file

    def _decrypt_file(self, encrypted_file: Path) -> Path:
        """Decrypt a backup file."""
        decrypted_file = encrypted_file.with_suffix('')

        with open(encrypted_file, 'rb') as infile:
            with open(decrypted_file, 'wb') as outfile:
                outfile.write(self.cipher.decrypt(infile.read()))

        return decrypted_file

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _upload_to_s3(self, backup_id: str, manifest: Dict):
        """Upload backup files to S3."""
        if not self.s3_client or not self.s3_bucket:
            return

        logger.info("Uploading backups to S3...")

        try:
            # Upload manifest
            manifest_file = self.backup_dir / f"{backup_id}_manifest.json"
            s3_key = f"backups/{backup_id}/manifest.json"
            self.s3_client.upload_file(str(manifest_file), self.s3_bucket, s3_key)

            # Upload all backup components
            for component, file_path in manifest['components'].items():
                s3_key = f"backups/{backup_id}/{os.path.basename(file_path)}"
                self.s3_client.upload_file(file_path, self.s3_bucket, s3_key)

            logger.info(f"Backup uploaded to S3: s3://{self.s3_bucket}/backups/{backup_id}/")

        except Exception as e:
            logger.error(f"S3 upload failed: {e}")

    def _cleanup_old_backups(self):
        """Remove old backup files based on retention policy."""
        logger.info(f"Cleaning up backups older than {self.backup_retention_days} days...")

        cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)

        for backup_file in self.backup_dir.glob("centuryproptax_backup_*"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                logger.info(f"Removed old backup: {backup_file}")

    def restore_from_backup(self, backup_id: str, components: Optional[List[str]] = None) -> bool:
        """Restore system from a backup."""
        logger.info(f"Starting restore from backup: {backup_id}")

        # Load backup manifest
        manifest_file = self.backup_dir / f"{backup_id}_manifest.json"
        if not manifest_file.exists():
            logger.error(f"Backup manifest not found: {manifest_file}")
            return False

        with open(manifest_file, 'r') as f:
            manifest = json.load(f)

        # Determine which components to restore
        if components is None:
            components = list(manifest['components'].keys())

        try:
            for component in components:
                if component not in manifest['components']:
                    logger.warning(f"Component '{component}' not found in backup")
                    continue

                logger.info(f"Restoring component: {component}")

                if component == 'database':
                    self._restore_database(manifest['components'][component])
                elif component == 'redis':
                    self._restore_redis(manifest['components'][component])
                elif component == 'static_files':
                    self._restore_static_files(manifest['components'][component])
                elif component == 'configuration':
                    self._restore_configuration(manifest['components'][component])
                elif component == 'logs':
                    self._restore_logs(manifest['components'][component])

            logger.info("Restore completed successfully")
            return True

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def _restore_database(self, encrypted_backup_file: str):
        """Restore database from backup."""
        logger.info("Restoring database...")

        encrypted_file = Path(encrypted_backup_file)

        # Decrypt the backup
        backup_file = self._decrypt_file(encrypted_file)

        try:
            # Parse database URL
            from urllib.parse import urlparse
            parsed = urlparse(self.db_url)

            # Restore database
            psql_cmd = [
                'psql',
                f'--host={parsed.hostname}',
                f'--port={parsed.port or 5432}',
                f'--username={parsed.username}',
                f'--dbname={parsed.path[1:]}',
                '--no-password'
            ]

            # Set password via environment
            env = os.environ.copy()
            env['PGPASSWORD'] = parsed.password

            # Run restore
            with gzip.open(backup_file, 'rt') as f:
                result = subprocess.run(
                    psql_cmd,
                    stdin=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    check=True,
                    text=True
                )

            logger.info("Database restore completed")

        finally:
            # Clean up decrypted file
            if backup_file.exists():
                backup_file.unlink()

    def list_backups(self) -> List[Dict]:
        """List all available backups."""
        backups = []

        for manifest_file in self.backup_dir.glob("*_manifest.json"):
            try:
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                backups.append({
                    'backup_id': manifest['backup_id'],
                    'timestamp': manifest['timestamp'],
                    'size_mb': manifest['size_bytes'] / 1024 / 1024,
                    'components': list(manifest['components'].keys())
                })
            except Exception as e:
                logger.warning(f"Failed to read manifest {manifest_file}: {e}")

        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)

    def health_check(self) -> Dict[str, bool]:
        """Perform backup system health check."""
        health = {
            'backup_directory_writable': False,
            'database_accessible': False,
            'redis_accessible': False,
            's3_accessible': False,
            'encryption_configured': False
        }

        # Check backup directory
        try:
            test_file = self.backup_dir / 'health_check_test'
            test_file.write_text('test')
            test_file.unlink()
            health['backup_directory_writable'] = True
        except Exception:
            pass

        # Check database
        if self.db_url:
            try:
                conn = psycopg2.connect(self.db_url)
                conn.close()
                health['database_accessible'] = True
            except Exception:
                pass

        # Check Redis
        if self.redis_url:
            try:
                r = redis.from_url(self.redis_url)
                r.ping()
                health['redis_accessible'] = True
            except Exception:
                pass

        # Check S3
        if self.s3_client and self.s3_bucket:
            try:
                self.s3_client.head_bucket(Bucket=self.s3_bucket)
                health['s3_accessible'] = True
            except Exception:
                pass

        # Check encryption
        health['encryption_configured'] = bool(self.encryption_key)

        return health


def main():
    """Main backup script entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Century Property Tax Backup System')
    parser.add_argument('action', choices=['backup', 'restore', 'list', 'health'])
    parser.add_argument('--backup-id', help='Backup ID for restore operation')
    parser.add_argument('--components', nargs='+', help='Components to restore')

    args = parser.parse_args()

    backup_manager = BackupManager()

    if args.action == 'backup':
        manifest = backup_manager.create_full_backup()
        print(f"Backup completed: {manifest['backup_id']}")

    elif args.action == 'restore':
        if not args.backup_id:
            print("Error: --backup-id required for restore")
            sys.exit(1)

        success = backup_manager.restore_from_backup(args.backup_id, args.components)
        if success:
            print("Restore completed successfully")
        else:
            print("Restore failed")
            sys.exit(1)

    elif args.action == 'list':
        backups = backup_manager.list_backups()
        if backups:
            print("Available backups:")
            for backup in backups:
                print(f"  {backup['backup_id']} ({backup['timestamp']}) - {backup['size_mb']:.2f} MB")
                print(f"    Components: {', '.join(backup['components'])}")
        else:
            print("No backups found")

    elif args.action == 'health':
        health = backup_manager.health_check()
        print("Backup system health:")
        for check, status in health.items():
            status_str = "✅ PASS" if status else "❌ FAIL"
            print(f"  {check}: {status_str}")


if __name__ == '__main__':
    main()