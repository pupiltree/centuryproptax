"""Role-based access control system for monitoring dashboards.

This module provides:
- User authentication and role management for monitoring access
- Granular permissions for different monitoring functionalities
- API key management for programmatic access
- Audit logging for monitoring access and actions
- Integration with existing authentication systems
"""

import asyncio
import hashlib
import secrets
import jwt
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import json
import structlog
from fastapi import HTTPException, status
import os

logger = structlog.get_logger(__name__)

class MonitoringRole(Enum):
    """Monitoring access roles with hierarchical permissions."""
    VIEWER = "viewer"          # Read-only access to dashboards
    OPERATOR = "operator"      # View + acknowledge alerts
    ADMIN = "admin"           # Full monitoring management
    SYSTEM = "system"         # Programmatic access for automation

class MonitoringPermission(Enum):
    """Granular monitoring permissions."""
    # Dashboard access
    VIEW_PERFORMANCE = "view_performance"
    VIEW_BUSINESS = "view_business"
    VIEW_INFRASTRUCTURE = "view_infrastructure"

    # Alert management
    VIEW_ALERTS = "view_alerts"
    ACKNOWLEDGE_ALERTS = "acknowledge_alerts"
    CONFIGURE_ALERTS = "configure_alerts"
    SUPPRESS_ALERTS = "suppress_alerts"

    # System management
    MANAGE_USERS = "manage_users"
    MANAGE_API_KEYS = "manage_api_keys"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    EXPORT_DATA = "export_data"

    # Administrative
    CONFIGURE_RETENTION = "configure_retention"
    MANAGE_INTEGRATIONS = "manage_integrations"

@dataclass
class MonitoringUser:
    """Monitoring system user."""
    username: str
    email: str
    role: MonitoringRole
    permissions: Set[MonitoringPermission]
    active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    api_keys: List[str] = None

    def __post_init__(self):
        if self.api_keys is None:
            self.api_keys = []

@dataclass
class APIKey:
    """API key for programmatic access."""
    key_id: str
    key_hash: str
    name: str
    permissions: Set[MonitoringPermission]
    created_by: str
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime] = None
    active: bool = True

@dataclass
class AuditLogEntry:
    """Audit log entry for monitoring access."""
    timestamp: datetime
    user: str
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: str
    user_agent: str
    success: bool

class MonitoringAuthManager:
    """Role-based access control manager for monitoring."""

    def __init__(self, config_file: Optional[str] = None):
        self.users: Dict[str, MonitoringUser] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.audit_logs: List[AuditLogEntry] = []
        self.jwt_secret = os.getenv("MONITORING_JWT_SECRET", secrets.token_urlsafe(32))
        self.jwt_algorithm = "HS256"
        self.jwt_expiry_hours = 24

        # Role permission mappings
        self.role_permissions = {
            MonitoringRole.VIEWER: {
                MonitoringPermission.VIEW_PERFORMANCE,
                MonitoringPermission.VIEW_BUSINESS,
                MonitoringPermission.VIEW_INFRASTRUCTURE,
                MonitoringPermission.VIEW_ALERTS
            },
            MonitoringRole.OPERATOR: {
                MonitoringPermission.VIEW_PERFORMANCE,
                MonitoringPermission.VIEW_BUSINESS,
                MonitoringPermission.VIEW_INFRASTRUCTURE,
                MonitoringPermission.VIEW_ALERTS,
                MonitoringPermission.ACKNOWLEDGE_ALERTS,
                MonitoringPermission.SUPPRESS_ALERTS
            },
            MonitoringRole.ADMIN: set(MonitoringPermission),  # All permissions
            MonitoringRole.SYSTEM: {
                MonitoringPermission.VIEW_PERFORMANCE,
                MonitoringPermission.VIEW_BUSINESS,
                MonitoringPermission.VIEW_INFRASTRUCTURE,
                MonitoringPermission.VIEW_ALERTS,
                MonitoringPermission.ACKNOWLEDGE_ALERTS,
                MonitoringPermission.EXPORT_DATA
            }
        }

        # Load configuration
        if config_file:
            self.load_config(config_file)
        else:
            self.create_default_users()

    def create_default_users(self):
        """Create default monitoring users."""
        default_users = [
            MonitoringUser(
                username="admin",
                email="admin@centuryproptax.com",
                role=MonitoringRole.ADMIN,
                permissions=self.role_permissions[MonitoringRole.ADMIN],
                active=True,
                created_at=datetime.now()
            ),
            MonitoringUser(
                username="operator",
                email="ops@centuryproptax.com",
                role=MonitoringRole.OPERATOR,
                permissions=self.role_permissions[MonitoringRole.OPERATOR],
                active=True,
                created_at=datetime.now()
            ),
            MonitoringUser(
                username="viewer",
                email="viewer@centuryproptax.com",
                role=MonitoringRole.VIEWER,
                permissions=self.role_permissions[MonitoringRole.VIEWER],
                active=True,
                created_at=datetime.now()
            )
        ]

        for user in default_users:
            self.users[user.username] = user

        logger.info(f"✅ Created {len(default_users)} default monitoring users")

    def load_config(self, config_file: str):
        """Load authentication configuration from file."""
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)

                # Load users
                for user_data in config.get('users', []):
                    user = MonitoringUser(
                        username=user_data['username'],
                        email=user_data['email'],
                        role=MonitoringRole(user_data['role']),
                        permissions=set(MonitoringPermission(p) for p in user_data.get('permissions', [])),
                        active=user_data.get('active', True),
                        created_at=datetime.fromisoformat(user_data['created_at'])
                    )
                    self.users[user.username] = user

                # Load API keys
                for key_data in config.get('api_keys', []):
                    api_key = APIKey(
                        key_id=key_data['key_id'],
                        key_hash=key_data['key_hash'],
                        name=key_data['name'],
                        permissions=set(MonitoringPermission(p) for p in key_data['permissions']),
                        created_by=key_data['created_by'],
                        created_at=datetime.fromisoformat(key_data['created_at']),
                        expires_at=datetime.fromisoformat(key_data['expires_at']) if key_data.get('expires_at') else None,
                        active=key_data.get('active', True)
                    )
                    self.api_keys[api_key.key_id] = api_key

                logger.info(f"✅ Loaded monitoring auth config from {config_file}")
            else:
                logger.warning(f"Auth config file {config_file} not found, using defaults")
                self.create_default_users()

        except Exception as e:
            logger.error(f"Failed to load auth config from {config_file}: {e}")
            self.create_default_users()

    def create_user(self, username: str, email: str, role: MonitoringRole, active: bool = True) -> MonitoringUser:
        """Create a new monitoring user."""
        if username in self.users:
            raise ValueError(f"User {username} already exists")

        user = MonitoringUser(
            username=username,
            email=email,
            role=role,
            permissions=self.role_permissions[role].copy(),
            active=active,
            created_at=datetime.now()
        )

        self.users[username] = user
        self.log_action(username, "create_user", "user", {"created_user": username, "role": role.value})

        logger.info(f"✅ Created monitoring user: {username} with role {role.value}")
        return user

    def update_user_role(self, username: str, new_role: MonitoringRole, updated_by: str) -> bool:
        """Update user role and permissions."""
        if username not in self.users:
            return False

        user = self.users[username]
        old_role = user.role

        user.role = new_role
        user.permissions = self.role_permissions[new_role].copy()

        self.log_action(
            updated_by,
            "update_user_role",
            "user",
            {"username": username, "old_role": old_role.value, "new_role": new_role.value}
        )

        logger.info(f"✅ Updated user {username} role from {old_role.value} to {new_role.value}")
        return True

    def deactivate_user(self, username: str, deactivated_by: str) -> bool:
        """Deactivate a monitoring user."""
        if username not in self.users:
            return False

        self.users[username].active = False
        self.log_action(deactivated_by, "deactivate_user", "user", {"username": username})

        logger.info(f"✅ Deactivated monitoring user: {username}")
        return True

    def create_api_key(
        self,
        name: str,
        permissions: Set[MonitoringPermission],
        created_by: str,
        expires_in_days: Optional[int] = None
    ) -> tuple[str, APIKey]:
        """Create a new API key with specified permissions."""
        # Generate API key
        key_value = f"cpt_monitor_{secrets.token_urlsafe(32)}"
        key_id = secrets.token_urlsafe(16)
        key_hash = hashlib.sha256(key_value.encode()).hexdigest()

        # Set expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            permissions=permissions,
            created_by=created_by,
            created_at=datetime.now(),
            expires_at=expires_at
        )

        self.api_keys[key_id] = api_key

        # Add to user's API keys
        if created_by in self.users:
            self.users[created_by].api_keys.append(key_id)

        self.log_action(
            created_by,
            "create_api_key",
            "api_key",
            {"key_id": key_id, "name": name, "permissions": [p.value for p in permissions]}
        )

        logger.info(f"✅ Created API key: {name} for {created_by}")
        return key_value, api_key

    def revoke_api_key(self, key_id: str, revoked_by: str) -> bool:
        """Revoke an API key."""
        if key_id not in self.api_keys:
            return False

        self.api_keys[key_id].active = False
        self.log_action(revoked_by, "revoke_api_key", "api_key", {"key_id": key_id})

        logger.info(f"✅ Revoked API key: {key_id}")
        return True

    def authenticate_user(self, username: str, token: str) -> Optional[MonitoringUser]:
        """Authenticate user with JWT token."""
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            # Verify user exists and is active
            if username not in self.users:
                return None

            user = self.users[username]
            if not user.active:
                return None

            # Verify token payload
            if payload.get('username') != username:
                return None

            # Update last login
            user.last_login = datetime.now()

            return user

        except jwt.InvalidTokenError:
            return None

    def authenticate_api_key(self, api_key: str) -> Optional[APIKey]:
        """Authenticate API key."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        for key_obj in self.api_keys.values():
            if key_obj.key_hash == key_hash and key_obj.active:
                # Check expiration
                if key_obj.expires_at and datetime.now() > key_obj.expires_at:
                    key_obj.active = False
                    return None

                # Update last used
                key_obj.last_used = datetime.now()
                return key_obj

        return None

    def generate_jwt_token(self, username: str) -> str:
        """Generate JWT token for user."""
        if username not in self.users:
            raise ValueError(f"User {username} not found")

        user = self.users[username]
        if not user.active:
            raise ValueError(f"User {username} is not active")

        payload = {
            'username': username,
            'role': user.role.value,
            'iat': datetime.now(),
            'exp': datetime.now() + timedelta(hours=self.jwt_expiry_hours)
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token

    def has_permission(self, user_or_key: any, permission: MonitoringPermission) -> bool:
        """Check if user or API key has specific permission."""
        if isinstance(user_or_key, MonitoringUser):
            return permission in user_or_key.permissions
        elif isinstance(user_or_key, APIKey):
            return permission in user_or_key.permissions
        return False

    def require_permission(self, user_or_key: any, permission: MonitoringPermission):
        """Require specific permission or raise HTTP exception."""
        if not self.has_permission(user_or_key, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission.value}"
            )

    def log_action(
        self,
        user: str,
        action: str,
        resource: str,
        details: Dict[str, Any],
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        success: bool = True
    ):
        """Log audit action."""
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            user=user,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )

        self.audit_logs.append(entry)

        # Keep only last 1000 entries in memory
        if len(self.audit_logs) > 1000:
            self.audit_logs = self.audit_logs[-1000:]

    def get_audit_logs(
        self,
        user: Optional[str] = None,
        action: Optional[str] = None,
        hours: int = 24
    ) -> List[AuditLogEntry]:
        """Get audit logs with optional filtering."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        filtered_logs = [
            log for log in self.audit_logs
            if log.timestamp >= cutoff_time
        ]

        if user:
            filtered_logs = [log for log in filtered_logs if log.user == user]

        if action:
            filtered_logs = [log for log in filtered_logs if log.action == action]

        return sorted(filtered_logs, key=lambda x: x.timestamp, reverse=True)

    def get_user_summary(self) -> Dict[str, Any]:
        """Get summary of users and permissions."""
        return {
            "total_users": len(self.users),
            "active_users": len([u for u in self.users.values() if u.active]),
            "users_by_role": {
                role.value: len([u for u in self.users.values() if u.role == role])
                for role in MonitoringRole
            },
            "total_api_keys": len(self.api_keys),
            "active_api_keys": len([k for k in self.api_keys.values() if k.active])
        }

    def export_config(self) -> Dict[str, Any]:
        """Export configuration for backup."""
        return {
            "users": [
                {
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.value,
                    "permissions": [p.value for p in user.permissions],
                    "active": user.active,
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None
                }
                for user in self.users.values()
            ],
            "api_keys": [
                {
                    "key_id": key.key_id,
                    "key_hash": key.key_hash,
                    "name": key.name,
                    "permissions": [p.value for p in key.permissions],
                    "created_by": key.created_by,
                    "created_at": key.created_at.isoformat(),
                    "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                    "active": key.active
                }
                for key in self.api_keys.values()
            ]
        }


# Global authentication manager instance
auth_manager = MonitoringAuthManager()