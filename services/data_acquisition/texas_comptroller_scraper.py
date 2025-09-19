"""
Texas Comptroller Web Scraper
Scrapes property tax information from comptroller.texas.gov
"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import structlog
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from datetime import datetime
import hashlib

logger = structlog.get_logger()

@dataclass
class ScrapedDocument:
    """Represents a scraped document with metadata"""
    url: str
    title: str
    content: str
    document_type: str  # 'statute', 'regulation', 'procedure', 'form', 'faq'
    effective_date: Optional[datetime] = None
    authority: str = "Texas Comptroller"
    jurisdiction: str = "Texas"
    section_number: Optional[str] = None
    citations: List[str] = None
    hash: Optional[str] = None

    def __post_init__(self):
        if self.citations is None:
            self.citations = []
        if self.hash is None:
            self.hash = hashlib.md5(self.content.encode()).hexdigest()

class TexasComptrollerScraper:
    """Scrapes property tax information from Texas Comptroller website"""

    BASE_URL = "https://comptroller.texas.gov"
    PROPERTY_TAX_PATHS = [
        "/taxes/property-tax/",
        "/taxes/property-tax/property-tax-exemptions/",
        "/taxes/property-tax/rendition-and-appraisal/",
        "/taxes/property-tax/protest-and-appeals/",
        "/taxes/property-tax/forms/",
        "/taxes/property-tax/frequently-asked-questions/"
    ]

    def __init__(self, max_concurrent: int = 5, delay_between_requests: float = 1.0):
        self.max_concurrent = max_concurrent
        self.delay_between_requests = delay_between_requests
        self.session: Optional[aiohttp.ClientSession] = None
        self.scraped_urls = set()

    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; PropertyTaxBot/1.0; +https://centuryproptax.com/bot)'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def scrape_all_property_tax_content(self) -> List[ScrapedDocument]:
        """Scrape all property tax content from comptroller website"""
        documents = []

        for path in self.PROPERTY_TAX_PATHS:
            url = urljoin(self.BASE_URL, path)
            logger.info(f"🕷️ Scraping section: {url}")

            try:
                # Scrape main page
                doc = await self.scrape_page(url)
                if doc:
                    documents.append(doc)

                # Find and scrape linked pages
                linked_docs = await self.scrape_linked_pages(url)
                documents.extend(linked_docs)

                # Respectful delay
                await asyncio.sleep(self.delay_between_requests)

            except Exception as e:
                logger.error(f"❌ Failed to scrape {url}: {e}")
                continue

        logger.info(f"✅ Scraped {len(documents)} documents from Texas Comptroller")
        return documents

    async def scrape_page(self, url: str) -> Optional[ScrapedDocument]:
        """Scrape a single page"""
        if url in self.scraped_urls:
            return None

        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"⚠️ HTTP {response.status} for {url}")
                    return None

                html = await response.text()
                self.scraped_urls.add(url)

            soup = BeautifulSoup(html, 'html.parser')

            # Extract content
            title = self._extract_title(soup)
            content = self._extract_content(soup)
            document_type = self._classify_document_type(url, title, content)
            effective_date = self._extract_effective_date(content)
            section_number = self._extract_section_number(content)
            citations = self._extract_citations(content)

            if not content.strip():
                logger.warning(f"⚠️ No content extracted from {url}")
                return None

            return ScrapedDocument(
                url=url,
                title=title,
                content=content,
                document_type=document_type,
                effective_date=effective_date,
                section_number=section_number,
                citations=citations
            )

        except Exception as e:
            logger.error(f"❌ Error scraping {url}: {e}")
            return None

    async def scrape_linked_pages(self, base_url: str) -> List[ScrapedDocument]:
        """Find and scrape linked pages from a base page"""
        documents = []

        try:
            async with self.session.get(base_url) as response:
                if response.status != 200:
                    return documents

                html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')

            # Find relevant links
            links = soup.find_all('a', href=True)
            property_tax_links = []

            for link in links:
                href = link['href']
                full_url = urljoin(base_url, href)

                # Filter for property tax related links
                if self._is_property_tax_related(href, link.get_text()):
                    property_tax_links.append(full_url)

            # Scrape linked pages with concurrency control
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def scrape_with_semaphore(url):
                async with semaphore:
                    await asyncio.sleep(self.delay_between_requests)
                    return await self.scrape_page(url)

            tasks = [scrape_with_semaphore(url) for url in property_tax_links[:20]]  # Limit to 20 per section
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, ScrapedDocument):
                    documents.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"❌ Error in concurrent scraping: {result}")

        except Exception as e:
            logger.error(f"❌ Error finding linked pages for {base_url}: {e}")

        return documents

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        # Try multiple title selectors
        for selector in ['h1', 'title', '.page-title', '.content-title']:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        return "Untitled Document"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from page"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()

        # Try to find main content area
        main_content = None
        for selector in ['.main-content', '.content', 'main', 'article', '.page-content']:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if not main_content:
            main_content = soup.find('body') or soup

        # Extract text while preserving structure
        text_parts = []
        for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div']):
            text = element.get_text().strip()
            if text and len(text) > 10:  # Filter out very short text
                text_parts.append(text)

        return '\n\n'.join(text_parts)

    def _classify_document_type(self, url: str, title: str, content: str) -> str:
        """Classify the type of document"""
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()

        if any(term in url_lower for term in ['form', 'pdf']):
            return 'form'
        elif any(term in url_lower for term in ['faq', 'question']):
            return 'faq'
        elif any(term in title_lower for term in ['code', 'statute', 'section']):
            return 'statute'
        elif any(term in title_lower for term in ['regulation', 'rule', 'administrative']):
            return 'regulation'
        elif any(term in content_lower for term in ['procedure', 'process', 'step', 'how to']):
            return 'procedure'
        else:
            return 'general'

    def _extract_effective_date(self, content: str) -> Optional[datetime]:
        """Extract effective date from content"""
        # Look for date patterns
        date_patterns = [
            r'effective\s+(\w+\s+\d{1,2},\s+\d{4})',
            r'as\s+of\s+(\w+\s+\d{1,2},\s+\d{4})',
            r'updated\s+(\w+\s+\d{1,2},\s+\d{4})'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    return datetime.strptime(date_str, '%B %d, %Y')
                except ValueError:
                    continue

        return None

    def _extract_section_number(self, content: str) -> Optional[str]:
        """Extract section number from legal text"""
        # Look for section patterns
        section_patterns = [
            r'(?:Section|Sec\.?)\s+(\d+(?:\.\d+)*)',
            r'§\s*(\d+(?:\.\d+)*)',
            r'Chapter\s+(\d+)'
        ]

        for pattern in section_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_citations(self, content: str) -> List[str]:
        """Extract legal citations from content"""
        citations = []

        # Common citation patterns
        citation_patterns = [
            r'Tax Code\s+(?:Section|§)\s*(\d+(?:\.\d+)*)',
            r'(?:Texas|Tex\.)\s+Prop\.?\s+Code\s+(?:Section|§)\s*(\d+(?:\.\d+)*)',
            r'(?:Texas|Tex\.)\s+Tax\s+Code\s+(?:Section|§)\s*(\d+(?:\.\d+)*)'
        ]

        for pattern in citation_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            citations.extend(matches)

        return list(set(citations))  # Remove duplicates

    def _is_property_tax_related(self, href: str, link_text: str) -> bool:
        """Check if a link is property tax related"""
        href_lower = href.lower()
        text_lower = link_text.lower()

        # Property tax keywords
        keywords = [
            'property tax', 'property-tax', 'exemption', 'appraisal',
            'assessment', 'protest', 'appeal', 'rendition', 'valuation',
            'homestead', 'tax code', 'county', 'district'
        ]

        # Check if link contains property tax keywords
        for keyword in keywords:
            if keyword in href_lower or keyword in text_lower:
                return True

        # Must be on comptroller domain
        if not href.startswith('http') and not href.startswith('/'):
            return False

        # Exclude certain file types and sections
        exclude = ['mailto:', 'tel:', 'javascript:', '.jpg', '.png', '.gif', '#']
        if any(ex in href_lower for ex in exclude):
            return False

        return False

async def scrape_texas_comptroller_data() -> List[ScrapedDocument]:
    """Main function to scrape Texas Comptroller data"""
    logger.info("🚀 Starting Texas Comptroller scraping")

    async with TexasComptrollerScraper() as scraper:
        documents = await scraper.scrape_all_property_tax_content()

    logger.info(f"✅ Completed scraping: {len(documents)} documents collected")
    return documents

if __name__ == "__main__":
    # Test the scraper
    async def test_scraper():
        documents = await scrape_texas_comptroller_data()
        for doc in documents[:3]:  # Print first 3 for testing
            print(f"Title: {doc.title}")
            print(f"Type: {doc.document_type}")
            print(f"URL: {doc.url}")
            print(f"Content length: {len(doc.content)}")
            print("---")

    asyncio.run(test_scraper())