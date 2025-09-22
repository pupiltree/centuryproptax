"""SEO optimization module for Century Property Tax Documentation Portal.

This module provides comprehensive SEO optimization including:
- Meta tags optimization
- Structured data implementation
- Sitemap generation
- Robot.txt configuration
- OpenGraph and Twitter Card metadata
"""

import os
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from datetime import datetime
import xml.etree.ElementTree as ET
import structlog

logger = structlog.get_logger(__name__)


class SEOManager:
    """Comprehensive SEO optimization manager."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('DOCS_BASE_URL', 'https://docs.centuryproptax.com')
        self.site_name = "Century Property Tax Documentation"
        self.site_description = "Comprehensive API documentation for Century Property Tax's intelligent assistant system"
        self.organization_name = "Century Property Tax"
        self.contact_email = "support@centuryproptax.com"

    def get_meta_tags(self, request: Request) -> Dict[str, str]:
        """Generate meta tags for a specific page."""
        path = request.url.path
        page_info = self._get_page_info(path)

        meta_tags = {
            # Basic meta tags
            'title': page_info['title'],
            'description': page_info['description'],
            'keywords': page_info['keywords'],
            'author': self.organization_name,
            'robots': 'index, follow',
            'viewport': 'width=device-width, initial-scale=1.0',

            # Open Graph meta tags
            'og:title': page_info['title'],
            'og:description': page_info['description'],
            'og:type': 'website',
            'og:url': str(request.url),
            'og:site_name': self.site_name,
            'og:image': f"{self.base_url}/static/og-image.png",
            'og:image:alt': f"{self.site_name} - {page_info['title']}",

            # Twitter Card meta tags
            'twitter:card': 'summary_large_image',
            'twitter:site': '@centuryproptax',
            'twitter:title': page_info['title'],
            'twitter:description': page_info['description'],
            'twitter:image': f"{self.base_url}/static/twitter-card.png",

            # Technical meta tags
            'canonical': str(request.url),
            'alternate': f"{self.base_url}/api/openapi.json",
            'dns-prefetch': 'https://fonts.googleapis.com',
            'preconnect': 'https://fonts.gstatic.com',

            # Schema.org structured data
            'application-ld-json': self._get_structured_data(page_info, str(request.url))
        }

        return meta_tags

    def _get_page_info(self, path: str) -> Dict[str, str]:
        """Get page-specific information for SEO."""
        page_configs = {
            '/': {
                'title': f"{self.site_name} - Home",
                'description': self.site_description,
                'keywords': 'API documentation, property tax, WhatsApp bot, FastAPI, OpenAPI'
            },
            '/documentation': {
                'title': f"{self.site_name} - API Documentation Portal",
                'description': "Interactive API documentation portal with comprehensive guides and examples",
                'keywords': 'API docs, interactive documentation, developer portal, REST API'
            },
            '/docs': {
                'title': f"{self.site_name} - Swagger UI",
                'description': "Interactive Swagger UI documentation for Century Property Tax API",
                'keywords': 'Swagger UI, OpenAPI, interactive API docs, REST endpoints'
            },
            '/redoc': {
                'title': f"{self.site_name} - ReDoc",
                'description': "Beautiful ReDoc documentation for Century Property Tax API",
                'keywords': 'ReDoc, API documentation, OpenAPI spec, developer docs'
            },
            '/health': {
                'title': f"{self.site_name} - System Health",
                'description': "Real-time system health and status monitoring",
                'keywords': 'system health, API status, monitoring, uptime'
            }
        }

        # Default configuration
        default_config = {
            'title': f"{self.site_name}",
            'description': self.site_description,
            'keywords': 'property tax, API, documentation, WhatsApp, automation'
        }

        return page_configs.get(path, default_config)

    def _get_structured_data(self, page_info: Dict[str, str], url: str) -> str:
        """Generate JSON-LD structured data."""
        structured_data = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": self.site_name,
            "description": page_info['description'],
            "url": url,
            "applicationCategory": "DeveloperApplication",
            "operatingSystem": "Web",
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD"
            },
            "publisher": {
                "@type": "Organization",
                "name": self.organization_name,
                "url": "https://centuryproptax.com",
                "contactPoint": {
                    "@type": "ContactPoint",
                    "email": self.contact_email,
                    "contactType": "customer service"
                }
            },
            "featureList": [
                "WhatsApp Business API Integration",
                "Property Assessment Management",
                "Document Processing",
                "Payment Integration",
                "Real-time Notifications",
                "Comprehensive API Documentation"
            ]
        }

        import json
        return json.dumps(structured_data, separators=(',', ':'))

    def generate_sitemap(self) -> str:
        """Generate XML sitemap for the documentation portal."""
        # Define pages to include in sitemap
        pages = [
            {
                'url': self.base_url,
                'lastmod': datetime.now().isoformat(),
                'changefreq': 'daily',
                'priority': '1.0'
            },
            {
                'url': f"{self.base_url}/documentation",
                'lastmod': datetime.now().isoformat(),
                'changefreq': 'weekly',
                'priority': '0.9'
            },
            {
                'url': f"{self.base_url}/docs",
                'lastmod': datetime.now().isoformat(),
                'changefreq': 'weekly',
                'priority': '0.8'
            },
            {
                'url': f"{self.base_url}/redoc",
                'lastmod': datetime.now().isoformat(),
                'changefreq': 'weekly',
                'priority': '0.8'
            },
            {
                'url': f"{self.base_url}/openapi.json",
                'lastmod': datetime.now().isoformat(),
                'changefreq': 'weekly',
                'priority': '0.7'
            }
        ]

        # Create XML sitemap
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

        for page in pages:
            url_elem = ET.SubElement(urlset, 'url')

            loc = ET.SubElement(url_elem, 'loc')
            loc.text = page['url']

            lastmod = ET.SubElement(url_elem, 'lastmod')
            lastmod.text = page['lastmod']

            changefreq = ET.SubElement(url_elem, 'changefreq')
            changefreq.text = page['changefreq']

            priority = ET.SubElement(url_elem, 'priority')
            priority.text = page['priority']

        # Convert to string with XML declaration
        ET.indent(urlset, space="  ")
        xml_str = ET.tostring(urlset, encoding='unicode')
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

    def generate_robots_txt(self) -> str:
        """Generate robots.txt file."""
        robots_content = f"""User-agent: *
Allow: /

# Sitemap
Sitemap: {self.base_url}/sitemap.xml

# Crawl-delay for polite bots
Crawl-delay: 1

# Disallow admin areas
Disallow: /admin/
Disallow: /private/
Disallow: /*.json$

# Allow important documentation
Allow: /docs
Allow: /redoc
Allow: /documentation
Allow: /openapi.json

# Contact information
# For questions about this robots.txt file, contact: {self.contact_email}
"""
        return robots_content.strip()

    def get_canonical_url(self, request: Request) -> str:
        """Get canonical URL for the current page."""
        # Ensure HTTPS
        canonical_url = str(request.url).replace('http://', 'https://')

        # Remove query parameters for documentation pages
        if any(path in canonical_url for path in ['/docs', '/redoc', '/documentation']):
            canonical_url = canonical_url.split('?')[0]

        return canonical_url

    def generate_open_graph_image_url(self, title: str) -> str:
        """Generate dynamic Open Graph image URL."""
        # In production, this could generate dynamic images
        # For now, return static image
        return f"{self.base_url}/static/og-image.png"


def setup_seo_routes(app: FastAPI):
    """Set up SEO-related routes."""
    seo_manager = SEOManager()

    @app.get("/sitemap.xml", response_class=PlainTextResponse)
    async def sitemap():
        """Generate and serve sitemap.xml."""
        sitemap_content = seo_manager.generate_sitemap()
        return Response(
            content=sitemap_content,
            media_type="application/xml",
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Content-Type": "application/xml; charset=utf-8"
            }
        )

    @app.get("/robots.txt", response_class=PlainTextResponse)
    async def robots_txt():
        """Generate and serve robots.txt."""
        robots_content = seo_manager.generate_robots_txt()
        return Response(
            content=robots_content,
            media_type="text/plain",
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                "Content-Type": "text/plain; charset=utf-8"
            }
        )

    @app.get("/manifest.json")
    async def web_app_manifest():
        """Generate web app manifest for PWA features."""
        manifest = {
            "name": seo_manager.site_name,
            "short_name": "Century Tax Docs",
            "description": seo_manager.site_description,
            "start_url": "/",
            "display": "standalone",
            "theme_color": "#667eea",
            "background_color": "#f8fafc",
            "orientation": "portrait",
            "icons": [
                {
                    "src": "/static/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "/static/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ],
            "categories": ["developer", "documentation", "business"]
        }

        return Response(
            content=json.dumps(manifest, indent=2),
            media_type="application/json",
            headers={
                "Cache-Control": "public, max-age=86400"  # Cache for 24 hours
            }
        )

    logger.info("✅ SEO routes configured")

    return seo_manager


class SEOMiddleware:
    """SEO optimization middleware."""

    def __init__(self, app: FastAPI, seo_manager: SEOManager):
        self.app = app
        self.seo_manager = seo_manager

    async def __call__(self, scope, receive, send):
        """Add SEO headers to HTML responses."""
        if scope["type"] == "http":
            request = Request(scope, receive)

            # Only process GET requests for HTML content
            if request.method == "GET":
                response = await self.app(scope, receive, send)

                # Add canonical header for HTML responses
                if "text/html" in request.headers.get("accept", ""):
                    canonical_url = self.seo_manager.get_canonical_url(request)

                    # Add Link header for canonical URL
                    if hasattr(response, 'headers'):
                        response.headers["Link"] = f'<{canonical_url}>; rel="canonical"'

                return response

        return await self.app(scope, receive, send)


def enhance_documentation_html_with_seo(html_content: str, meta_tags: Dict[str, str]) -> str:
    """Enhance HTML content with SEO meta tags."""
    # This function would be used to inject meta tags into the documentation HTML
    # For the static HTML file, we'll update it directly

    head_additions = []

    # Basic meta tags
    for name, content in meta_tags.items():
        if name.startswith('og:'):
            head_additions.append(f'    <meta property="{name}" content="{content}">')
        elif name.startswith('twitter:'):
            head_additions.append(f'    <meta name="{name}" content="{content}">')
        elif name == 'canonical':
            head_additions.append(f'    <link rel="canonical" href="{content}">')
        elif name == 'application-ld-json':
            head_additions.append(f'    <script type="application/ld+json">{content}</script>')
        elif name in ['title', 'description', 'keywords', 'author', 'robots', 'viewport']:
            if name == 'title':
                # Replace existing title
                html_content = html_content.replace('<title>Century Property Tax - API Documentation</title>', f'<title>{content}</title>')
            else:
                head_additions.append(f'    <meta name="{name}" content="{content}">')

    # Add meta tags before closing head tag
    if head_additions:
        seo_meta = '\n'.join(head_additions)
        html_content = html_content.replace('</head>', f'{seo_meta}\n</head>')

    return html_content