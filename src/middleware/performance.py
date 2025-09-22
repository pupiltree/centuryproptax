"""Performance optimization middleware for production deployment.

This module provides comprehensive performance optimization including:
- Static asset caching and compression
- CDN integration and cache headers
- Response optimization and minification
- Performance monitoring and metrics
"""

import time
import gzip
import mimetypes
from typing import Dict, Optional, Tuple
from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import StreamingResponse
import structlog
from datetime import datetime, timedelta
import hashlib
import os

logger = structlog.get_logger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Comprehensive performance optimization middleware."""

    def __init__(
        self,
        app: FastAPI,
        enable_compression: bool = True,
        enable_caching: bool = True,
        enable_cdn: bool = True,
        cdn_base_url: Optional[str] = None,
        max_age: int = 86400,  # 24 hours
        compression_min_size: int = 1024  # 1KB
    ):
        super().__init__(app)
        self.enable_compression = enable_compression
        self.enable_caching = enable_caching
        self.enable_cdn = enable_cdn
        self.cdn_base_url = cdn_base_url or os.getenv('CDN_URL')
        self.max_age = max_age
        self.compression_min_size = compression_min_size

        # Performance metrics
        self.request_times: Dict[str, float] = {}
        self.request_counts: Dict[str, int] = {}

    async def dispatch(self, request: Request, call_next):
        """Process request with performance optimizations."""
        start_time = time.time()

        # Track request metrics
        path = request.url.path
        self.request_counts[path] = self.request_counts.get(path, 0) + 1

        # Handle static file optimization
        if self._is_static_file(path):
            response = await self._handle_static_file(request, call_next)
        else:
            response = await call_next(request)

        # Apply performance optimizations
        response = await self._optimize_response(request, response)

        # Record timing
        process_time = time.time() - start_time
        self.request_times[path] = process_time
        response.headers["X-Process-Time"] = str(process_time)

        # Add performance headers
        self._add_performance_headers(response, request)

        return response

    def _is_static_file(self, path: str) -> bool:
        """Check if path is a static file."""
        static_extensions = {
            '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg',
            '.ico', '.woff', '.woff2', '.ttf', '.eot', '.pdf'
        }
        return any(path.endswith(ext) for ext in static_extensions)

    async def _handle_static_file(self, request: Request, call_next) -> Response:
        """Handle static file with caching and compression."""
        # Check if-modified-since header
        if_modified_since = request.headers.get('if-modified-since')
        if if_modified_since and self.enable_caching:
            # For simplicity, return 304 for documentation static files
            # In production, implement proper file timestamp checking
            if '/documentation/' in request.url.path:
                return Response(status_code=304)

        response = await call_next(request)

        # Apply static file optimizations
        if response.status_code == 200:
            response = await self._optimize_static_response(request, response)

        return response

    async def _optimize_static_response(self, request: Request, response: Response) -> Response:
        """Optimize static file response."""
        # Add caching headers
        if self.enable_caching:
            response.headers["Cache-Control"] = f"public, max-age={self.max_age}"
            response.headers["Expires"] = (
                datetime.utcnow() + timedelta(seconds=self.max_age)
            ).strftime('%a, %d %b %Y %H:%M:%S GMT')

            # Add ETag for cache validation
            if hasattr(response, 'body'):
                etag = hashlib.md5(response.body).hexdigest()
                response.headers["ETag"] = f'"{etag}"'

        # Add CDN headers if configured
        if self.enable_cdn and self.cdn_base_url:
            response.headers["X-CDN-Cache"] = "MISS"
            response.headers["X-CDN-URL"] = self.cdn_base_url

        return response

    async def _optimize_response(self, request: Request, response: Response) -> Response:
        """Apply general response optimizations."""
        # Compress response if applicable
        if self.enable_compression:
            response = await self._compress_response(request, response)

        # Add cache headers for API responses
        if request.url.path.startswith('/docs') or request.url.path.startswith('/redoc'):
            response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour
        elif request.url.path == '/openapi.json':
            response.headers["Cache-Control"] = "public, max-age=1800"  # 30 minutes

        return response

    async def _compress_response(self, request: Request, response: Response) -> Response:
        """Compress response if client supports it."""
        accept_encoding = request.headers.get('accept-encoding', '')

        if 'gzip' not in accept_encoding:
            return response

        # Check if response should be compressed
        content_type = response.headers.get('content-type', '')
        compressible_types = {
            'text/html', 'text/css', 'text/javascript', 'application/javascript',
            'application/json', 'text/xml', 'application/xml', 'text/plain'
        }

        should_compress = any(ct in content_type for ct in compressible_types)

        if not should_compress:
            return response

        # Compress if response is large enough
        if hasattr(response, 'body') and len(response.body) >= self.compression_min_size:
            compressed_body = gzip.compress(response.body)

            # Update response
            response.body = compressed_body
            response.headers["Content-Encoding"] = "gzip"
            response.headers["Content-Length"] = str(len(compressed_body))
            response.headers["Vary"] = "Accept-Encoding"

        return response

    def _add_performance_headers(self, response: Response, request: Request):
        """Add performance monitoring headers."""
        response.headers["X-Powered-By"] = "Century Property Tax API"
        response.headers["X-Performance-Optimized"] = "true"

        # Add cache status
        if self.enable_caching:
            response.headers["X-Cache-Status"] = "OPTIMIZED"

        # Add CDN information
        if self.enable_cdn and self.cdn_base_url:
            response.headers["X-CDN-Enabled"] = "true"

    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics."""
        return {
            "request_times": dict(list(self.request_times.items())[-50:]),  # Last 50
            "request_counts": dict(list(self.request_counts.items())[-50:]),  # Last 50
            "average_response_time": (
                sum(self.request_times.values()) / len(self.request_times)
                if self.request_times else 0
            ),
            "total_requests": sum(self.request_counts.values()),
            "optimization_enabled": {
                "compression": self.enable_compression,
                "caching": self.enable_caching,
                "cdn": self.enable_cdn
            }
        }


class CDNManager:
    """Content Delivery Network integration manager."""

    def __init__(self, cdn_base_url: Optional[str] = None):
        self.cdn_base_url = cdn_base_url or os.getenv('CDN_URL')
        self.enabled = bool(self.cdn_base_url)

    def get_cdn_url(self, path: str) -> str:
        """Get CDN URL for a given path."""
        if not self.enabled:
            return path

        # Ensure path starts with /
        if not path.startswith('/'):
            path = '/' + path

        return f"{self.cdn_base_url}{path}"

    def should_use_cdn(self, path: str) -> bool:
        """Determine if path should use CDN."""
        if not self.enabled:
            return False

        # Use CDN for static assets
        static_patterns = [
            '/docs/static/',
            '/documentation/',
            '/favicon.ico',
            '.css',
            '.js',
            '.png',
            '.jpg',
            '.svg'
        ]

        return any(pattern in path for pattern in static_patterns)


class CacheManager:
    """Advanced caching manager with multiple strategies."""

    def __init__(self):
        self.cache_strategies = {
            'static': {'max_age': 86400, 'immutable': True},  # 24 hours
            'api': {'max_age': 3600, 'immutable': False},     # 1 hour
            'docs': {'max_age': 1800, 'immutable': False},    # 30 minutes
            'health': {'max_age': 60, 'immutable': False}     # 1 minute
        }

    def get_cache_headers(self, path: str) -> Dict[str, str]:
        """Get appropriate cache headers for path."""
        strategy = self._get_cache_strategy(path)
        cache_config = self.cache_strategies.get(strategy, self.cache_strategies['api'])

        headers = {
            "Cache-Control": f"public, max-age={cache_config['max_age']}"
        }

        if cache_config['immutable']:
            headers["Cache-Control"] += ", immutable"

        # Add expires header
        expires_time = datetime.utcnow() + timedelta(seconds=cache_config['max_age'])
        headers["Expires"] = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')

        return headers

    def _get_cache_strategy(self, path: str) -> str:
        """Determine cache strategy for path."""
        if any(ext in path for ext in ['.css', '.js', '.png', '.jpg', '.svg']):
            return 'static'
        elif path.startswith('/docs') or path.startswith('/redoc'):
            return 'docs'
        elif path == '/health':
            return 'health'
        else:
            return 'api'


# Global instances
cdn_manager = CDNManager()
cache_manager = CacheManager()


def setup_performance_middleware(app: FastAPI) -> PerformanceMiddleware:
    """Set up performance middleware with production configuration."""
    middleware = PerformanceMiddleware(
        app=app,
        enable_compression=True,
        enable_caching=True,
        enable_cdn=bool(os.getenv('CDN_URL')),
        cdn_base_url=os.getenv('CDN_URL'),
        max_age=86400,  # 24 hours for static assets
        compression_min_size=1024  # 1KB minimum for compression
    )

    app.add_middleware(PerformanceMiddleware)
    logger.info("✅ Performance optimization middleware configured")

    return middleware