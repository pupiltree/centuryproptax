"""
Data Collection Scheduler
Manages automated scraping and data updates for the property tax knowledge base
"""

import asyncio
import schedule
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog
from pathlib import Path
import json

from .texas_comptroller_scraper import scrape_texas_comptroller_data
from .county_appraisal_scraper import scrape_county_appraisal_data
from .document_processor import process_scraped_documents

logger = structlog.get_logger()

@dataclass
class ScheduledJob:
    """Represents a scheduled data collection job"""
    name: str
    function: Callable
    schedule_type: str  # 'daily', 'weekly', 'monthly'
    schedule_time: str  # Time in format "HH:MM" or day name for weekly
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class CollectionStats:
    """Statistics from a data collection run"""
    job_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    documents_collected: int = 0
    documents_processed: int = 0
    success: bool = False
    error_message: Optional[str] = None

class DataCollectionScheduler:
    """Schedules and manages automated data collection"""

    def __init__(self, storage_dir: str = "./data/collections"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.jobs: Dict[str, ScheduledJob] = {}
        self.collection_history: List[CollectionStats] = []
        self.running = False

        # Set up default jobs
        self._setup_default_jobs()

    def _setup_default_jobs(self):
        """Set up default data collection jobs"""
        # Texas Comptroller - weekly updates (Sunday 2 AM)
        self.add_job(
            name="texas_comptroller_weekly",
            function=self._run_comptroller_collection,
            schedule_type="weekly",
            schedule_time="sunday"
        )

        # County Appraisal - monthly updates (1st of month, 3 AM)
        self.add_job(
            name="county_appraisal_monthly",
            function=self._run_county_collection,
            schedule_type="monthly",
            schedule_time="01 03:00"
        )

        # Quick comptroller check - daily (6 AM)
        self.add_job(
            name="comptroller_daily_check",
            function=self._run_daily_comptroller_check,
            schedule_type="daily",
            schedule_time="06:00"
        )

    def add_job(self, name: str, function: Callable, schedule_type: str, schedule_time: str):
        """Add a scheduled job"""
        job = ScheduledJob(
            name=name,
            function=function,
            schedule_type=schedule_type,
            schedule_time=schedule_time
        )

        self.jobs[name] = job
        self._schedule_job(job)

        logger.info(f"📅 Added scheduled job: {name} ({schedule_type} at {schedule_time})")

    def _schedule_job(self, job: ScheduledJob):
        """Schedule a job with the schedule library"""
        if job.schedule_type == "daily":
            schedule.every().day.at(job.schedule_time).do(self._run_job_wrapper, job.name)
        elif job.schedule_type == "weekly":
            day = job.schedule_time.lower()
            getattr(schedule.every(), day).at("02:00").do(self._run_job_wrapper, job.name)
        elif job.schedule_type == "monthly":
            # For monthly, we'll check daily and run on the specified day
            schedule.every().day.at("03:00").do(self._check_monthly_job, job.name)

    def _run_job_wrapper(self, job_name: str):
        """Wrapper to run jobs asynchronously"""
        if job_name not in self.jobs:
            logger.error(f"❌ Job {job_name} not found")
            return

        job = self.jobs[job_name]
        if not job.enabled:
            logger.info(f"⏸️ Job {job_name} is disabled, skipping")
            return

        # Run the job asynchronously
        asyncio.create_task(self._run_job_async(job))

    async def _run_job_async(self, job: ScheduledJob):
        """Run a job asynchronously with error handling and retries"""
        stats = CollectionStats(
            job_name=job.name,
            start_time=datetime.now()
        )

        logger.info(f"🚀 Starting scheduled job: {job.name}")

        try:
            # Run the job function
            result = await job.function()

            if isinstance(result, dict):
                stats.documents_collected = result.get('collected', 0)
                stats.documents_processed = result.get('processed', 0)

            stats.success = True
            stats.end_time = datetime.now()

            job.last_run = datetime.now()
            job.retry_count = 0  # Reset retry count on success

            logger.info(f"✅ Job {job.name} completed successfully")

        except Exception as e:
            stats.success = False
            stats.error_message = str(e)
            stats.end_time = datetime.now()

            job.retry_count += 1

            logger.error(f"❌ Job {job.name} failed: {e}")

            # Schedule retry if within retry limit
            if job.retry_count <= job.max_retries:
                retry_delay = 2 ** job.retry_count  # Exponential backoff
                logger.info(f"🔄 Scheduling retry {job.retry_count}/{job.max_retries} in {retry_delay} minutes")

                asyncio.create_task(self._schedule_retry(job, retry_delay))
            else:
                logger.error(f"💥 Job {job.name} exceeded max retries, disabling")
                job.enabled = False

        # Save collection stats
        self.collection_history.append(stats)
        await self._save_collection_stats(stats)

    async def _schedule_retry(self, job: ScheduledJob, delay_minutes: int):
        """Schedule a job retry after a delay"""
        await asyncio.sleep(delay_minutes * 60)
        await self._run_job_async(job)

    def _check_monthly_job(self, job_name: str):
        """Check if it's time to run a monthly job"""
        if job_name not in self.jobs:
            return

        job = self.jobs[job_name]
        if not job.enabled:
            return

        now = datetime.now()

        # Parse monthly schedule (day and time)
        try:
            day_str, time_str = job.schedule_time.split(' ')
            target_day = int(day_str)

            # Check if today is the target day and we haven't run this month
            if (now.day == target_day and
                (job.last_run is None or job.last_run.month != now.month)):
                asyncio.create_task(self._run_job_async(job))

        except ValueError:
            logger.error(f"❌ Invalid monthly schedule format for {job_name}: {job.schedule_time}")

    async def _run_comptroller_collection(self) -> Dict[str, int]:
        """Run Texas Comptroller data collection"""
        logger.info("🏛️ Running Texas Comptroller collection")

        # Scrape documents
        scraped_docs = await scrape_texas_comptroller_data()

        # Process documents
        processed_docs = await process_scraped_documents(scraped_docs)

        # Save to storage
        await self._save_documents(processed_docs, "comptroller")

        return {
            'collected': len(scraped_docs),
            'processed': len(processed_docs)
        }

    async def _run_county_collection(self) -> Dict[str, int]:
        """Run county appraisal data collection"""
        logger.info("🏢 Running county appraisal collection")

        # Scrape documents (priority 2 counties for monthly)
        scraped_docs = await scrape_county_appraisal_data(priority_filter=2)

        # Process documents
        processed_docs = await process_scraped_documents(scraped_docs)

        # Save to storage
        await self._save_documents(processed_docs, "counties")

        return {
            'collected': len(scraped_docs),
            'processed': len(processed_docs)
        }

    async def _run_daily_comptroller_check(self) -> Dict[str, int]:
        """Run daily check for critical comptroller updates"""
        logger.info("🔍 Running daily comptroller check")

        # Only check critical sections for daily updates
        from .texas_comptroller_scraper import TexasComptrollerScraper

        async with TexasComptrollerScraper() as scraper:
            # Just check main property tax page for updates
            critical_urls = [
                "https://comptroller.texas.gov/taxes/property-tax/",
                "https://comptroller.texas.gov/taxes/property-tax/forms/"
            ]

            documents = []
            for url in critical_urls:
                doc = await scraper.scrape_page(url)
                if doc:
                    documents.append(doc)

        # Process any new documents
        processed_docs = await process_scraped_documents(documents)

        # Save to storage
        if processed_docs:
            await self._save_documents(processed_docs, "daily_updates")

        return {
            'collected': len(documents),
            'processed': len(processed_docs)
        }

    async def _save_documents(self, documents, collection_type: str):
        """Save processed documents to storage"""
        if not documents:
            return

        timestamp = datetime.now().isoformat()
        collection_dir = self.storage_dir / collection_type
        collection_dir.mkdir(exist_ok=True)

        filename = f"{collection_type}_{timestamp.replace(':', '-')}.json"
        filepath = collection_dir / filename

        # Convert documents to serializable format
        doc_data = []
        for doc in documents:
            doc_dict = {
                'original_doc': {
                    'url': doc.original_doc.url,
                    'title': doc.original_doc.title,
                    'content': doc.original_doc.content,
                    'document_type': doc.original_doc.document_type,
                    'authority': doc.original_doc.authority,
                    'jurisdiction': doc.original_doc.jurisdiction,
                    'effective_date': doc.original_doc.effective_date.isoformat() if doc.original_doc.effective_date else None,
                    'section_number': doc.original_doc.section_number,
                    'citations': doc.original_doc.citations,
                    'hash': doc.original_doc.hash
                },
                'cleaned_content': doc.cleaned_content,
                'chunks': doc.chunks,
                'metadata': doc.metadata,
                'quality_score': doc.quality_score,
                'processing_notes': doc.processing_notes
            }
            doc_data.append(doc_dict)

        # Save to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Saved {len(documents)} documents to {filepath}")

    async def _save_collection_stats(self, stats: CollectionStats):
        """Save collection statistics"""
        stats_file = self.storage_dir / "collection_stats.json"

        # Load existing stats
        existing_stats = []
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    existing_stats = json.load(f)
            except:
                pass

        # Add new stats
        stats_dict = {
            'job_name': stats.job_name,
            'start_time': stats.start_time.isoformat(),
            'end_time': stats.end_time.isoformat() if stats.end_time else None,
            'documents_collected': stats.documents_collected,
            'documents_processed': stats.documents_processed,
            'success': stats.success,
            'error_message': stats.error_message
        }

        existing_stats.append(stats_dict)

        # Keep only last 100 stats entries
        if len(existing_stats) > 100:
            existing_stats = existing_stats[-100:]

        # Save updated stats
        with open(stats_file, 'w') as f:
            json.dump(existing_stats, f, indent=2)

    async def start_scheduler(self):
        """Start the scheduler"""
        self.running = True
        logger.info("🕐 Data collection scheduler started")

        while self.running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("⏹️ Data collection scheduler stopped")

    def get_job_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs"""
        status = {}

        for name, job in self.jobs.items():
            status[name] = {
                'enabled': job.enabled,
                'schedule_type': job.schedule_type,
                'schedule_time': job.schedule_time,
                'last_run': job.last_run.isoformat() if job.last_run else None,
                'retry_count': job.retry_count,
                'max_retries': job.max_retries
            }

        return status

    def get_collection_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent collection history"""
        recent_stats = self.collection_history[-limit:] if limit else self.collection_history

        return [
            {
                'job_name': stats.job_name,
                'start_time': stats.start_time.isoformat(),
                'end_time': stats.end_time.isoformat() if stats.end_time else None,
                'documents_collected': stats.documents_collected,
                'documents_processed': stats.documents_processed,
                'success': stats.success,
                'error_message': stats.error_message
            }
            for stats in recent_stats
        ]

# Global scheduler instance
_scheduler_instance = None

def get_scheduler() -> DataCollectionScheduler:
    """Get the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = DataCollectionScheduler()
    return _scheduler_instance

async def start_data_collection_scheduler():
    """Start the data collection scheduler"""
    scheduler = get_scheduler()
    await scheduler.start_scheduler()

def stop_data_collection_scheduler():
    """Stop the data collection scheduler"""
    scheduler = get_scheduler()
    scheduler.stop_scheduler()

if __name__ == "__main__":
    # Test the scheduler
    async def test_scheduler():
        scheduler = DataCollectionScheduler()

        # Run a single collection manually
        result = await scheduler._run_daily_comptroller_check()
        print(f"Collection result: {result}")

        # Show job status
        status = scheduler.get_job_status()
        print(f"Job status: {json.dumps(status, indent=2)}")

    asyncio.run(test_scheduler())