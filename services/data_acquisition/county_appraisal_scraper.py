"""
County Appraisal District Scraper
Scrapes property tax information from major Texas county appraisal districts
"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import structlog
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from datetime import datetime

from .texas_comptroller_scraper import ScrapedDocument

logger = structlog.get_logger()

@dataclass
class CountyInfo:
    """Information about a county appraisal district"""
    name: str
    website: str
    population: int
    priority: int  # 1=highest, 5=lowest

class CountyAppraisalScraper:
    """Scrapes property tax information from Texas county appraisal districts"""

    # Major Texas counties by population and economic impact
    MAJOR_COUNTIES = [
        CountyInfo("Harris County", "https://hcad.org", 4700000, 1),
        CountyInfo("Dallas County", "https://dallascad.org", 2600000, 1),
        CountyInfo("Tarrant County", "https://tcad.org", 2100000, 1),
        CountyInfo("Bexar County", "https://bcad.org", 2000000, 1),
        CountyInfo("Travis County", "https://traviscad.org", 1300000, 2),
        CountyInfo("Collin County", "https://collincad.org", 1000000, 2),
        CountyInfo("Fort Bend County", "https://fbcad.org", 820000, 2),
        CountyInfo("Montgomery County", "https://mctx.org", 610000, 3),
        CountyInfo("Williamson County", "https://wcad.org", 590000, 3),
        CountyInfo("Hidalgo County", "https://hidalgocad.org", 870000, 3)
    ]

    def __init__(self, max_concurrent: int = 3, delay_between_requests: float = 2.0):
        self.max_concurrent = max_concurrent
        self.delay_between_requests = delay_between_requests
        self.session: Optional[aiohttp.ClientSession] = None
        self.scraped_urls = set()

    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=45)
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

    async def scrape_all_counties(self, priority_filter: int = 2) -> List[ScrapedDocument]:
        """Scrape property tax content from major counties"""
        documents = []

        # Filter counties by priority
        counties_to_scrape = [c for c in self.MAJOR_COUNTIES if c.priority <= priority_filter]

        logger.info(f"🏢 Scraping {len(counties_to_scrape)} county appraisal districts")

        for county in counties_to_scrape:
            logger.info(f"🏛️ Scraping {county.name}: {county.website}")

            try:
                county_docs = await self.scrape_county(county)
                documents.extend(county_docs)

                logger.info(f"✅ {county.name}: {len(county_docs)} documents collected")

                # Respectful delay between counties
                await asyncio.sleep(self.delay_between_requests * 2)

            except Exception as e:
                logger.error(f"❌ Failed to scrape {county.name}: {e}")
                continue

        logger.info(f"✅ County scraping complete: {len(documents)} total documents")
        return documents

    async def scrape_county(self, county: CountyInfo) -> List[ScrapedDocument]:
        """Scrape property tax content from a specific county"""
        documents = []

        try:
            # Get county website structure
            property_tax_urls = await self.find_property_tax_sections(county)

            if not property_tax_urls:
                logger.warning(f"⚠️ No property tax sections found for {county.name}")
                return documents

            # Scrape each property tax section
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def scrape_with_semaphore(url):
                async with semaphore:
                    await asyncio.sleep(self.delay_between_requests)
                    return await self.scrape_county_page(url, county)

            tasks = [scrape_with_semaphore(url) for url in property_tax_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, ScrapedDocument):
                    documents.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"❌ Error scraping county page: {result}")

        except Exception as e:
            logger.error(f"❌ Error scraping {county.name}: {e}")

        return documents

    async def find_property_tax_sections(self, county: CountyInfo) -> List[str]:
        """Find property tax related sections on county website"""
        try:
            async with self.session.get(county.website) as response:
                if response.status != 200:
                    logger.warning(f"⚠️ HTTP {response.status} for {county.website}")
                    return []

                html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')

            # Find navigation and links
            links = soup.find_all('a', href=True)
            property_tax_urls = []

            for link in links:
                href = link['href']
                link_text = link.get_text().strip().lower()

                # Look for property tax related links
                if self._is_county_property_tax_link(href, link_text):
                    full_url = urljoin(county.website, href)
                    if full_url not in property_tax_urls:
                        property_tax_urls.append(full_url)

            # Also try common property tax paths
            common_paths = [
                '/property-tax',
                '/exemptions',
                '/appeals',
                '/protest',
                '/forms',
                '/procedures',
                '/homestead',
                '/rendition'
            ]

            for path in common_paths:
                test_url = urljoin(county.website, path)
                try:
                    async with self.session.head(test_url) as response:
                        if response.status == 200 and test_url not in property_tax_urls:
                            property_tax_urls.append(test_url)
                except:
                    continue

            return property_tax_urls[:15]  # Limit to 15 URLs per county

        except Exception as e:
            logger.error(f"❌ Error finding property tax sections for {county.name}: {e}")
            return []

    async def scrape_county_page(self, url: str, county: CountyInfo) -> Optional[ScrapedDocument]:
        """Scrape a single county page"""
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
            title = self._extract_title(soup, county)
            content = self._extract_content(soup)
            document_type = self._classify_county_document_type(url, title, content)

            if not content.strip():
                logger.warning(f"⚠️ No content extracted from {url}")
                return None

            return ScrapedDocument(
                url=url,
                title=title,
                content=content,
                document_type=document_type,
                authority=f"{county.name} Appraisal District",
                jurisdiction=county.name.replace(" County", ""),
                citations=self._extract_county_citations(content)
            )

        except Exception as e:
            logger.error(f"❌ Error scraping county page {url}: {e}")
            return None

    def _is_county_property_tax_link(self, href: str, link_text: str) -> bool:
        """Check if a county link is property tax related"""
        href_lower = href.lower()
        text_lower = link_text.lower()

        # County-specific property tax keywords
        keywords = [
            'property tax', 'property-tax', 'exemption', 'appraisal',
            'assessment', 'protest', 'appeal', 'rendition', 'valuation',
            'homestead', 'tax rate', 'tax roll', 'notice', 'hearing',
            'agricultural', 'disability', 'veteran', 'senior', 'freeze'
        ]

        # Check for keywords
        for keyword in keywords:
            if keyword in href_lower or keyword in text_lower:
                return True

        # Exclude unwanted links
        exclude = [
            'mailto:', 'tel:', 'javascript:', '.jpg', '.png', '.gif',
            'facebook', 'twitter', 'linkedin', 'instagram', 'youtube',
            'calendar', 'news', 'employment', 'contact', 'about'
        ]

        if any(ex in href_lower for ex in exclude):
            return False

        return False

    def _extract_title(self, soup: BeautifulSoup, county: CountyInfo) -> str:
        """Extract page title with county context"""
        # Try multiple title selectors
        for selector in ['h1', 'title', '.page-title', '.content-title', '.main-title']:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if title and len(title) > 3:
                    return f"{county.name}: {title}"

        return f"{county.name}: Property Tax Information"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from county page"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', '.sidebar']):
            element.decompose()

        # Try to find main content area
        main_content = None
        for selector in ['.main-content', '.content', 'main', 'article', '.page-content', '.body-content']:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if not main_content:
            main_content = soup.find('body') or soup

        # Extract text while preserving structure
        text_parts = []
        for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div', 'td']):
            text = element.get_text().strip()
            if text and len(text) > 15:  # Filter out very short text
                # Clean up common county website artifacts
                if not any(artifact in text.lower() for artifact in ['skip to', 'javascript', 'cookie', 'accessibility']):
                    text_parts.append(text)

        return '\n\n'.join(text_parts)

    def _classify_county_document_type(self, url: str, title: str, content: str) -> str:
        """Classify county document type"""
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()

        if any(term in url_lower for term in ['form', 'pdf', 'download']):
            return 'form'
        elif any(term in url_lower or term in title_lower for term in ['exemption', 'homestead']):
            return 'exemption'
        elif any(term in url_lower or term in title_lower for term in ['protest', 'appeal', 'hearing']):
            return 'appeal'
        elif any(term in url_lower or term in title_lower for term in ['rate', 'tax rate', 'levy']):
            return 'tax_rate'
        elif any(term in title_lower for term in ['procedure', 'process', 'how to', 'step']):
            return 'procedure'
        elif any(term in title_lower for term in ['deadline', 'calendar', 'schedule']):
            return 'deadline'
        else:
            return 'general'

    def _extract_county_citations(self, content: str) -> List[str]:
        """Extract citations from county content"""
        citations = []

        # County-specific citation patterns
        patterns = [
            r'Property Tax Code\s+(?:Section|§)\s*(\d+(?:\.\d+)*)',
            r'Tax Code\s+(?:Section|§)\s*(\d+(?:\.\d+)*)',
            r'Local Government Code\s+(?:Section|§)\s*(\d+(?:\.\d+)*)',
            r'Chapter\s+(\d+)',
            r'Section\s+(\d+(?:\.\d+)*)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            citations.extend([f"§{match}" for match in matches])

        return list(set(citations))  # Remove duplicates

async def scrape_county_appraisal_data(priority_filter: int = 2) -> List[ScrapedDocument]:
    """Main function to scrape county appraisal data"""
    logger.info(f"🚀 Starting county appraisal scraping (priority ≤ {priority_filter})")

    async with CountyAppraisalScraper() as scraper:
        documents = await scraper.scrape_all_counties(priority_filter)

    logger.info(f"✅ County scraping completed: {len(documents)} documents collected")
    return documents

if __name__ == "__main__":
    # Test the scraper
    async def test_county_scraper():
        documents = await scrape_county_appraisal_data(priority_filter=1)  # Only top priority counties
        for doc in documents[:5]:  # Print first 5 for testing
            print(f"Title: {doc.title}")
            print(f"Authority: {doc.authority}")
            print(f"Type: {doc.document_type}")
            print(f"URL: {doc.url}")
            print(f"Content length: {len(doc.content)}")
            print("---")

    asyncio.run(test_county_scraper())