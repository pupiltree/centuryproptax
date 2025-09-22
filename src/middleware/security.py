"""Security middleware for production deployment.

This module provides comprehensive security measures including:
- SSL/TLS enforcement and security headers
- CORS configuration for production
- Rate limiting and DDoS protection
- Authentication and authorization
- Content Security Policy (CSP)
"""

import time
import hashlib
import secrets
from typing import Dict, List, Optional, Set
from fastapi import FastAPI, Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from datetime import datetime, timedelta
import os
import ipaddress

logger = structlog.get_logger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware for production."""

    def __init__(
        self,
        app: FastAPI,
        enable_ssl_redirect: bool = True,
        enable_security_headers: bool = True,
        enable_rate_limiting: bool = True,
        rate_limit_requests: int = 1000,
        rate_limit_window: int = 60,  # seconds
        trusted_hosts: Optional[List[str]] = None,
        allowed_origins: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.enable_ssl_redirect = enable_ssl_redirect
        self.enable_security_headers = enable_security_headers
        self.enable_rate_limiting = enable_rate_limiting
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window
        self.trusted_hosts = trusted_hosts or [
            "docs.centuryproptax.com",
            "api.centuryproptax.com",
            "centuryproptax.com"
        ]
        self.allowed_origins = allowed_origins or [
            "https://docs.centuryproptax.com",
            "https://api.centuryproptax.com",
            "https://centuryproptax.com"
        ]

        # Rate limiting storage
        self.rate_limit_storage: Dict[str, List[float]] = {}
        self.blocked_ips: Set[str] = set()

        # Security configuration
        self.csp_policy = self._build_csp_policy()
        self.security_headers = self._build_security_headers()

    async def dispatch(self, request: Request, call_next):
        """Process request with security checks."""
        # SSL redirect check
        if self.enable_ssl_redirect and not self._is_secure_request(request):
            return self._redirect_to_https(request)

        # Host validation
        if not self._is_trusted_host(request):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid host header"}
            )

        # Rate limiting
        if self.enable_rate_limiting:
            rate_limit_check = self._check_rate_limit(request)
            if rate_limit_check:
                return rate_limit_check

        # DDoS protection
        ddos_check = self._check_ddos_protection(request)
        if ddos_check:
            return ddos_check

        # Process request
        response = await call_next(request)

        # Apply security headers
        if self.enable_security_headers:
            self._add_security_headers(response, request)

        return response

    def _is_secure_request(self, request: Request) -> bool:
        """Check if request is using HTTPS."""
        # Check various headers that indicate HTTPS
        if request.url.scheme == "https":
            return True

        # Check forwarded headers (for reverse proxy setups)
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto == "https":
            return True

        # Check if running in development
        if os.getenv("ENVIRONMENT") == "development":
            return True

        return False

    def _redirect_to_https(self, request: Request) -> Response:
        """Redirect HTTP to HTTPS."""
        https_url = request.url.replace(scheme="https")
        return Response(
            status_code=status.HTTP_301_MOVED_PERMANENTLY,
            headers={"Location": str(https_url)}
        )

    def _is_trusted_host(self, request: Request) -> bool:
        """Validate host header against trusted hosts."""
        host = request.headers.get("host", "").lower()

        # Remove port number if present
        host = host.split(':')[0]

        # Check against trusted hosts
        for trusted_host in self.trusted_hosts:
            if host == trusted_host or host.endswith(f".{trusted_host}"):
                return True

        # Allow localhost in development
        if os.getenv("ENVIRONMENT") == "development":
            if host in ["localhost", "127.0.0.1", "0.0.0.0"]:
                return True

        return False

    def _check_rate_limit(self, request: Request) -> Optional[Response]:
        """Check and enforce rate limiting."""
        client_ip = self._get_client_ip(request)

        # Skip rate limiting for trusted IPs
        if self._is_trusted_ip(client_ip):
            return None

        current_time = time.time()
        window_start = current_time - self.rate_limit_window

        # Clean old requests
        if client_ip in self.rate_limit_storage:
            self.rate_limit_storage[client_ip] = [
                req_time for req_time in self.rate_limit_storage[client_ip]
                if req_time > window_start
            ]
        else:
            self.rate_limit_storage[client_ip] = []

        # Check current request count
        request_count = len(self.rate_limit_storage[client_ip])

        if request_count >= self.rate_limit_requests:
            # Block IP temporarily
            self.blocked_ips.add(client_ip)
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": self.rate_limit_window
                },
                headers={
                    "Retry-After": str(self.rate_limit_window),
                    "X-RateLimit-Limit": str(self.rate_limit_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + self.rate_limit_window))
                }
            )

        # Add current request
        self.rate_limit_storage[client_ip].append(current_time)

        return None

    def _check_ddos_protection(self, request: Request) -> Optional[Response]:
        """Basic DDoS protection."""
        client_ip = self._get_client_ip(request)

        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "IP temporarily blocked"}
            )

        # Check for suspicious patterns
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_patterns = ["bot", "crawler", "spider", "scraper"]

        # Allow legitimate bots
        legitimate_bots = ["googlebot", "bingbot", "facebookexternalhit"]

        is_suspicious = any(pattern in user_agent for pattern in suspicious_patterns)
        is_legitimate = any(bot in user_agent for bot in legitimate_bots)

        if is_suspicious and not is_legitimate:
            logger.warning(f"Suspicious user agent from {client_ip}: {user_agent}")
            # Could implement additional checks here

        return None

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address handling proxies."""
        # Check X-Forwarded-For header (common with load balancers)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP (client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"

    def _is_trusted_ip(self, ip: str) -> bool:
        """Check if IP is in trusted range."""
        trusted_ranges = [
            "127.0.0.0/8",     # Loopback
            "10.0.0.0/8",      # Private
            "172.16.0.0/12",   # Private
            "192.168.0.0/16",  # Private
        ]

        try:
            ip_obj = ipaddress.ip_address(ip)
            for trusted_range in trusted_ranges:
                if ip_obj in ipaddress.ip_network(trusted_range):
                    return True
        except ValueError:
            pass

        return False

    def _build_csp_policy(self) -> str:
        """Build Content Security Policy."""
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Needed for Swagger UI
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]

        # Add CDN if configured
        cdn_url = os.getenv('CDN_URL')
        if cdn_url:
            cdn_domain = cdn_url.replace('https://', '').replace('http://', '')
            csp_directives.extend([
                f"script-src 'self' 'unsafe-inline' 'unsafe-eval' {cdn_domain}",
                f"style-src 'self' 'unsafe-inline' {cdn_domain}",
                f"img-src 'self' data: https: {cdn_domain}",
                f"font-src 'self' data: {cdn_domain}"
            ])

        return "; ".join(csp_directives)

    def _build_security_headers(self) -> Dict[str, str]:
        """Build security headers."""
        return {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Content-Security-Policy": self.csp_policy,
            "X-Security-Headers": "enabled"
        }

    def _add_security_headers(self, response: Response, request: Request):
        """Add security headers to response."""
        for header, value in self.security_headers.items():
            response.headers[header] = value

        # Add request-specific headers
        response.headers["X-Request-ID"] = self._generate_request_id()
        response.headers["X-Timestamp"] = str(int(time.time()))

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        return secrets.token_hex(16)

    def get_security_status(self) -> Dict:
        """Get current security status."""
        return {
            "ssl_redirect_enabled": self.enable_ssl_redirect,
            "security_headers_enabled": self.enable_security_headers,
            "rate_limiting_enabled": self.enable_rate_limiting,
            "rate_limit_requests": self.rate_limit_requests,
            "rate_limit_window": self.rate_limit_window,
            "trusted_hosts": self.trusted_hosts,
            "blocked_ips_count": len(self.blocked_ips),
            "active_rate_limits": len(self.rate_limit_storage),
            "csp_policy": self.csp_policy
        }


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for protected endpoints."""

    def __init__(self, app: FastAPI, protected_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.protected_paths = protected_paths or [
            "/admin",
            "/stats",
            "/metrics"
        ]
        self.api_keys = self._load_api_keys()

    async def dispatch(self, request: Request, call_next):
        """Check authentication for protected paths."""
        path = request.url.path

        # Check if path requires authentication
        if any(path.startswith(protected_path) for protected_path in self.protected_paths):
            auth_result = self._check_authentication(request)
            if auth_result:
                return auth_result

        return await call_next(request)

    def _check_authentication(self, request: Request) -> Optional[Response]:
        """Check request authentication."""
        # Check API key
        api_key = request.headers.get("X-API-Key")
        if api_key and api_key in self.api_keys:
            return None

        # Check basic auth (for admin interfaces)
        authorization = request.headers.get("Authorization")
        if authorization and self._validate_basic_auth(authorization):
            return None

        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Authentication required"},
            headers={"WWW-Authenticate": "Bearer"}
        )

    def _load_api_keys(self) -> Set[str]:
        """Load valid API keys."""
        # In production, load from secure storage
        api_keys = set()

        # Load from environment
        env_key = os.getenv("API_KEY")
        if env_key:
            api_keys.add(env_key)

        # Generate a default key if none configured (development only)
        if not api_keys and os.getenv("ENVIRONMENT") == "development":
            api_keys.add("dev-api-key-123")

        return api_keys

    def _validate_basic_auth(self, authorization: str) -> bool:
        """Validate basic authentication."""
        try:
            scheme, credentials = authorization.split(" ", 1)
            if scheme.lower() != "basic":
                return False

            # In production, validate against secure user store
            # For now, use environment variables
            admin_user = os.getenv("ADMIN_USERNAME", "admin")
            admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")

            import base64
            decoded = base64.b64decode(credentials).decode("utf-8")
            username, password = decoded.split(":", 1)

            return username == admin_user and password == admin_pass

        except Exception:
            return False


def setup_security_middleware(app: FastAPI):
    """Set up comprehensive security middleware."""
    # Environment-based configuration
    is_production = os.getenv("ENVIRONMENT") == "production"

    # CORS configuration
    allowed_origins = [
        "https://docs.centuryproptax.com",
        "https://api.centuryproptax.com",
        "https://centuryproptax.com"
    ]

    if not is_production:
        allowed_origins.extend([
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000"
        ])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time", "X-Request-ID"]
    )

    # Security middleware
    security_middleware = SecurityMiddleware(
        app=app,
        enable_ssl_redirect=is_production,
        enable_security_headers=True,
        enable_rate_limiting=True,
        rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "1000")),
        rate_limit_window=60
    )

    app.add_middleware(SecurityMiddleware)

    # Authentication middleware
    auth_middleware = AuthenticationMiddleware(app)
    app.add_middleware(AuthenticationMiddleware)

    logger.info("✅ Security middleware configured for production")

    return security_middleware, auth_middleware