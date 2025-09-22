"""Monitoring and metrics middleware for production deployment.

This module provides comprehensive monitoring including:
- Prometheus metrics collection
- Performance tracking and analytics
- Health checks and system status
- Usage analytics and reporting
"""

import time
import psutil
from typing import Dict, Optional, List
from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import structlog
from datetime import datetime, timedelta
import os
import json

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'http_active_connections',
    'Number of active HTTP connections'
)

MEMORY_USAGE = Gauge(
    'process_memory_usage_bytes',
    'Process memory usage in bytes'
)

CPU_USAGE = Gauge(
    'process_cpu_usage_percent',
    'Process CPU usage percentage'
)

DOCUMENTATION_VIEWS = Counter(
    'documentation_page_views_total',
    'Total documentation page views',
    ['page', 'user_agent']
)

API_ENDPOINT_USAGE = Counter(
    'api_endpoint_usage_total',
    'API endpoint usage statistics',
    ['endpoint', 'method']
)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Comprehensive monitoring middleware."""

    def __init__(
        self,
        app: FastAPI,
        enable_detailed_metrics: bool = True,
        enable_usage_analytics: bool = True,
        track_user_agents: bool = True
    ):
        super().__init__(app)
        self.enable_detailed_metrics = enable_detailed_metrics
        self.enable_usage_analytics = enable_usage_analytics
        self.track_user_agents = track_user_agents

        # Internal metrics storage
        self.request_metrics: Dict[str, Dict] = {}
        self.system_metrics: Dict[str, float] = {}
        self.usage_analytics: Dict[str, Dict] = {}

        # Start system metrics collection
        self._update_system_metrics()

    async def dispatch(self, request: Request, call_next):
        """Process request with monitoring."""
        start_time = time.time()
        method = request.method
        path = request.url.path

        # Increment active connections
        ACTIVE_CONNECTIONS.inc()

        try:
            # Process request
            response = await call_next(request)

            # Record metrics
            duration = time.time() - start_time
            status_code = str(response.status_code)

            # Update Prometheus metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=self._normalize_endpoint(path),
                status=status_code
            ).inc()

            REQUEST_DURATION.labels(
                method=method,
                endpoint=self._normalize_endpoint(path)
            ).observe(duration)

            # Track documentation usage
            if self.enable_usage_analytics:
                self._track_documentation_usage(request, response)

            # Track API usage
            if path.startswith('/docs') or path.startswith('/redoc'):
                self._track_api_documentation_usage(request)

            # Add monitoring headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Request-ID"] = self._generate_request_id()

            return response

        except Exception as e:
            # Record error metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=self._normalize_endpoint(path),
                status="500"
            ).inc()
            raise

        finally:
            # Decrement active connections
            ACTIVE_CONNECTIONS.dec()

            # Update system metrics periodically
            if int(time.time()) % 30 == 0:  # Every 30 seconds
                self._update_system_metrics()

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics."""
        # Remove query parameters
        path = path.split('?')[0]

        # Normalize common patterns
        if path.startswith('/documentation'):
            return '/documentation'
        elif path.startswith('/docs'):
            return '/docs'
        elif path.startswith('/redoc'):
            return '/redoc'
        elif path == '/openapi.json':
            return '/openapi.json'
        elif path == '/health':
            return '/health'
        elif path == '/':
            return '/'
        else:
            return '/other'

    def _track_documentation_usage(self, request: Request, response: Response):
        """Track documentation page usage."""
        path = request.url.path
        user_agent = request.headers.get('user-agent', 'unknown')

        # Simplify user agent for metrics
        if self.track_user_agents:
            simplified_ua = self._simplify_user_agent(user_agent)
        else:
            simplified_ua = 'browser'

        # Track specific documentation pages
        if path.startswith('/documentation'):
            page = 'documentation_portal'
        elif path.startswith('/docs'):
            page = 'swagger_ui'
        elif path.startswith('/redoc'):
            page = 'redoc'
        elif path == '/openapi.json':
            page = 'openapi_schema'
        else:
            return

        DOCUMENTATION_VIEWS.labels(
            page=page,
            user_agent=simplified_ua
        ).inc()

        # Store detailed analytics
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        if current_hour not in self.usage_analytics:
            self.usage_analytics[current_hour] = {
                'documentation_portal': 0,
                'swagger_ui': 0,
                'redoc': 0,
                'openapi_schema': 0,
                'unique_visitors': set(),
                'user_agents': {}
            }

        self.usage_analytics[current_hour][page] += 1

        # Track unique visitors (simplified)
        visitor_id = self._get_visitor_id(request)
        self.usage_analytics[current_hour]['unique_visitors'].add(visitor_id)

        # Track user agents
        if simplified_ua not in self.usage_analytics[current_hour]['user_agents']:
            self.usage_analytics[current_hour]['user_agents'][simplified_ua] = 0
        self.usage_analytics[current_hour]['user_agents'][simplified_ua] += 1

    def _track_api_documentation_usage(self, request: Request):
        """Track API documentation endpoint usage."""
        path = request.url.path
        method = request.method

        API_ENDPOINT_USAGE.labels(
            endpoint=self._normalize_endpoint(path),
            method=method
        ).inc()

    def _simplify_user_agent(self, user_agent: str) -> str:
        """Simplify user agent string for metrics."""
        user_agent = user_agent.lower()

        if 'chrome' in user_agent:
            return 'chrome'
        elif 'firefox' in user_agent:
            return 'firefox'
        elif 'safari' in user_agent:
            return 'safari'
        elif 'edge' in user_agent:
            return 'edge'
        elif 'bot' in user_agent or 'crawler' in user_agent:
            return 'bot'
        elif 'postman' in user_agent:
            return 'postman'
        elif 'curl' in user_agent:
            return 'curl'
        else:
            return 'other'

    def _get_visitor_id(self, request: Request) -> str:
        """Generate simple visitor ID for analytics."""
        # Use IP + User-Agent hash for simple visitor identification
        ip = request.client.host if request.client else 'unknown'
        user_agent = request.headers.get('user-agent', '')

        import hashlib
        visitor_data = f"{ip}:{user_agent}"
        return hashlib.md5(visitor_data.encode()).hexdigest()[:8]

    def _update_system_metrics(self):
        """Update system metrics."""
        try:
            # Memory usage
            memory_info = psutil.virtual_memory()
            MEMORY_USAGE.set(memory_info.used)

            # CPU usage
            cpu_percent = psutil.cpu_percent()
            CPU_USAGE.set(cpu_percent)

            # Store for health endpoint
            self.system_metrics.update({
                'memory_used_bytes': memory_info.used,
                'memory_total_bytes': memory_info.total,
                'memory_percent': memory_info.percent,
                'cpu_percent': cpu_percent,
                'disk_usage_percent': psutil.disk_usage('/').percent
            })

        except Exception as e:
            logger.warning(f"Failed to update system metrics: {e}")

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        import uuid
        return str(uuid.uuid4())[:8]

    def get_usage_analytics(self, hours: int = 24) -> Dict:
        """Get usage analytics for the last N hours."""
        current_time = datetime.now()
        analytics_data = {
            'total_views': 0,
            'unique_visitors': set(),
            'page_views': {
                'documentation_portal': 0,
                'swagger_ui': 0,
                'redoc': 0,
                'openapi_schema': 0
            },
            'user_agents': {},
            'hourly_breakdown': {}
        }

        # Aggregate data from the last N hours
        for i in range(hours):
            hour_time = current_time - timedelta(hours=i)
            hour_key = hour_time.strftime('%Y-%m-%d-%H')

            if hour_key in self.usage_analytics:
                hour_data = self.usage_analytics[hour_key]
                analytics_data['hourly_breakdown'][hour_key] = {
                    'total_views': sum([
                        hour_data.get('documentation_portal', 0),
                        hour_data.get('swagger_ui', 0),
                        hour_data.get('redoc', 0),
                        hour_data.get('openapi_schema', 0)
                    ]),
                    'unique_visitors': len(hour_data.get('unique_visitors', set()))
                }

                # Aggregate totals
                for page in analytics_data['page_views']:
                    analytics_data['page_views'][page] += hour_data.get(page, 0)
                    analytics_data['total_views'] += hour_data.get(page, 0)

                # Aggregate unique visitors
                analytics_data['unique_visitors'].update(hour_data.get('unique_visitors', set()))

                # Aggregate user agents
                for ua, count in hour_data.get('user_agents', {}).items():
                    if ua not in analytics_data['user_agents']:
                        analytics_data['user_agents'][ua] = 0
                    analytics_data['user_agents'][ua] += count

        # Convert set to count for JSON serialization
        analytics_data['unique_visitors'] = len(analytics_data['unique_visitors'])

        return analytics_data

    def get_system_status(self) -> Dict:
        """Get current system status."""
        return {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': self.system_metrics,
            'monitoring_enabled': {
                'detailed_metrics': self.enable_detailed_metrics,
                'usage_analytics': self.enable_usage_analytics,
                'user_agent_tracking': self.track_user_agents
            }
        }


def setup_monitoring_middleware(app: FastAPI) -> MonitoringMiddleware:
    """Set up monitoring middleware."""
    monitoring = MonitoringMiddleware(
        app=app,
        enable_detailed_metrics=True,
        enable_usage_analytics=True,
        track_user_agents=True
    )

    app.add_middleware(MonitoringMiddleware)

    # Add metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # Add analytics endpoint
    @app.get("/analytics")
    async def analytics():
        """Usage analytics endpoint."""
        return monitoring.get_usage_analytics()

    # Add system status endpoint
    @app.get("/system-status")
    async def system_status():
        """System status endpoint."""
        return monitoring.get_system_status()

    logger.info("✅ Monitoring middleware configured with Prometheus metrics")

    return monitoring